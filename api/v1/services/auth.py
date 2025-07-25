from fastapi import Depends, Request, HTTPException, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from passlib.hash import bcrypt
from jose import JWTError, jwt
from typing import Optional
from datetime import datetime
import redis.asyncio as redis
import logging

from api.db.session import get_db
from api.v1.models.user import User
from core.config.settings import settings
from api.v1.schemas.auth import UserCreate


r = redis.Redis(
    host=settings.REDIS_HOST,
    port=settings.REDIS_PORT,
    password=settings.REDIS_PASSWORD,
    db=settings.REDIS_DB,
    decode_responses=settings.REDIS_RESPONSE,
    ssl=True
)

logger = logging.getLogger(__name__)


# --- Password Utilities ---
def hash_password(password: str) -> str:
    return bcrypt.hash(password)

def verify_password(password: str, hashed: str) -> bool:
    return bcrypt.verify(password, hashed)


# --- Core User Logic ---
async def get_user_by_email(email: str, db: AsyncSession) -> Optional[User]:
    stmt = select(User).where(User.email == email)
    result = await db.execute(stmt)
    return result.scalar_one_or_none()


async def get_current_user(request: Request, db: AsyncSession = Depends(get_db)) -> User:
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
    existing_user = await get_user_by_email(schemas.email, db)
    if existing_user:
        raise ValueError("Email already registered")

    new_user = User(
        email=schemas.email,
        password_hash=hash_password(schemas.password),
        first_name=schemas.first_name,
        last_name=schemas.last_name,
        gender=schemas.gender,
        phone_number=schemas.phone_number,
        date_of_birth=schemas.date_of_birth,
        is_verified=False
    )
    db.add(new_user)
    await db.commit()
    await db.refresh(new_user)
    return new_user


async def verify_user_email(user: User, db: AsyncSession) -> User:
    if not user:
        raise ValueError("User not found")

    user.is_verified = True
    db.add(user)
    await db.commit()
    await db.refresh(user)
    return user


# --- Token Blacklisting & Password Reset Token ---
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


async def verify_token(token: str) -> Optional[str]:
    key = f"reset_token:{token}"
    email = await r.get(key)
    return email


async def delete_token(token: str):
    key = f"reset_token:{token}"
    await r.delete(key)


# --- Update Password ---
async def update_user_password(user: User, new_password: str, db: AsyncSession):
    user.password_hash = hash_password(new_password)
    db.add(user)
    await db.commit()
    await db.refresh(user)
