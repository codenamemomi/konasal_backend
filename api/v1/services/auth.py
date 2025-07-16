from fastapi import Depends, Request
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from passlib.context import CryptContext
from typing import Optional
import redis.asyncio as redis
import datetime
import logging
from passlib.hash import bcrypt

from api.db.session import get_db
from api.v1.models.user import User
from fastapi import HTTPException, status
from jose import JWTError, jwt
from core.config.settings import settings
from api.utils.token import oauth2_scheme
from api.v1.schemas.auth import UserCreate


r = redis.Redis(
    host=settings.REDIS_HOST,
    port=settings.REDIS_PORT,
    password=settings.REDIS_PASSWORD,
    db=settings.REDIS_DB,
    decode_responses=settings.REDIS_RESPONSE
)


logger = logging.getLogger(__name__)

def hash_password(password: str) -> str:
    return bcrypt.hash(password)

def verify_password(password: str, hashed: str) -> bool:
    return bcrypt.verify(password, hashed)


async def get_user_by_email(email: str, db: AsyncSession):
    stmt = select(User).where(User.email == email)
    result = await db.execute(stmt)
    return result.scalar_one_or_none()

async def get_current_user(request: Request, db: AsyncSession = Depends(get_db)):
    token = request.cookies.get("access_token")

    if not token:
        raise HTTPException(status_code=401, detail="Missing authentication token")

    if await is_token_blacklisted(token):
        raise HTTPException(status_code=401, detail="Token has been revoked")

    try:
        payload = jwt.decode(token, settings.SECRET_KEY, algorithms=[settings.ALGORITHM])
        user_id: str = payload.get("sub")
        if not user_id:
            raise HTTPException(status_code=401, detail="Invalid token")
    except JWTError:
        raise HTTPException(status_code=401, detail="Could not validate token")

    stmt = select(User).where(User.id == user_id)
    result = await db.execute(stmt)
    user = result.scalar_one_or_none()

    if user is None:
        raise HTTPException(status_code=404, detail="User not found")

    return user

async def create_user(db: AsyncSession, schemas: UserCreate) -> User:
    result = await db.execute(select(User).where(User.email == schemas.email))
    existing_user = result.scalar_one_or_none()

    if existing_user:
        raise ValueError("Email already registered")

    new_user = User(
        email=schemas.email,
        password_hash=schemas.password,
        first_name=schemas.first_name,
        last_name=schemas.last_name,
        role="attendee",
        is_verified=False
    )
    db.add(new_user)
    await db.commit()
    await db.refresh(new_user)
    return new_user

async def verify_user_email(user: User, db: AsyncSession):
    if not user:
        raise ValueError("User not found")

    user.is_verified = True
    db.add(user)
    await db.commit()
    await db.refresh(user)
    return user

async def blacklist_token(token: str):
    try:
        payload = jwt.decode(token, settings.SECRET_KEY, algorithms=[settings.ALGORITHM])
        exp = payload.get("exp")
        if exp:
            ttl = int(exp - datetime.utcnow().timestamp())
            if ttl > 0:
                await r.setex(token, ttl, "blacklisted")
    except Exception as e:
        logger.error(f"Error blacklisting token: {e}")

async def is_token_blacklisted(token: str) -> bool:
    result = await r.get(token)
    return result == "blacklisted"

async def store_token(email: str, token: str, expiry: int = 600):
    key = f"reset_token:{token}"
    await r.set(key, email, ex=expiry)

async def verify_token(token: str) -> str | None:
    key = f"reset_token:{token}"
    email = await r.get(key)
    return email if email else None

async def delete_token(token: str):
    key = f"reset_token:{token}"
    await r.delete(key)

async def update_user_password(user, new_password: str, db):
    user.password_hash = hash_password(new_password)
    db.add(user)
    await db.commit()
    await db.refresh(user)
