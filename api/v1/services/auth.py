# api/v1/services/user_service.py
from fastapi import Depends, Request, HTTPException, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from jose import JWTError, jwt
from typing import Optional
from datetime import datetime
import redis.asyncio as redis
import logging
import uuid

from api.db.session import get_db
from api.v1.models.user import User
from core.config.settings import settings
from api.v1.schemas.auth import UserCreate
from api.utils.auth import verify_password, hash_passsword  # Use your auth.py

r = redis.Redis(
    host=settings.REDIS_HOST,
    port=settings.REDIS_PORT,
    password=settings.REDIS_PASSWORD,
    db=settings.REDIS_DB,
    decode_responses=settings.REDIS_RESPONSE,
    ssl=False
)

logger = logging.getLogger(__name__)

# --- Core User Logic ---
async def get_user_by_email(email: str, db: AsyncSession) -> Optional[User]:
    stmt = select(User).where(User.email == email)
    result = await db.execute(stmt)
    return result.scalar_one_or_none()

async def get_current_user(request: Request, db: AsyncSession = Depends(get_db)) -> User:
    # First try to get token from Authorization header
    auth_header = request.headers.get("Authorization")
    print(f"DEBUG: Authorization header: {auth_header}")  # Debug log
    
    if auth_header and auth_header.startswith("Bearer "):
        token = auth_header.split(" ")[1]
        print(f"DEBUG: Using Authorization header token: {token[:20]}...")  # Debug log (show first 20 chars)
    else:
        # Fall back to cookie
        token = request.cookies.get("access_token")
        print(f"DEBUG: Using cookie token: {token}")  # Debug log
    
    if not token:
        print("DEBUG: No token found in headers or cookies")  # Debug log
        raise HTTPException(status_code=401, detail="Missing authentication token")

    if await is_token_blacklisted(token):
        print("DEBUG: Token is blacklisted")  # Debug log
        raise HTTPException(status_code=401, detail="Token has been revoked")

    try:
        payload = jwt.decode(token, settings.SECRET_KEY, algorithms=[settings.ALGORITHM])
        user_id_str: str = payload.get("sub")
        print(f"DEBUG: Decoded user ID from token: {user_id_str}")  # Debug log
        
        if not user_id_str:
            print("DEBUG: No user ID in token payload")  # Debug log
            raise HTTPException(status_code=401, detail="Invalid token")
    except JWTError as e:
        print(f"DEBUG: JWT decoding error: {e}")  # Debug log
        raise HTTPException(status_code=401, detail="Could not validate token")

    # Convert string ID back to UUID for database query
    try:
        user_id_uuid = uuid.UUID(user_id_str)
        print(f"DEBUG: Converted to UUID: {user_id_uuid}")  # Debug log
    except ValueError as e:
        print(f"DEBUG: UUID conversion error: {e}")  # Debug log
        raise HTTPException(status_code=401, detail="Invalid user ID format")

    stmt = select(User).where(User.id == user_id_uuid)
    result = await db.execute(stmt)
    user = result.scalar_one_or_none()

    if user is None:
        print(f"DEBUG: User not found with ID: {user_id_uuid}")  # Debug log
        raise HTTPException(status_code=404, detail="User not found")

    print(f"DEBUG: User found: {user.email}")  # Debug log
    return user

async def create_user(db: AsyncSession, user_data: UserCreate):
    existing_user = await get_user_by_email(user_data.email, db)
    if existing_user:
        raise ValueError("Email already registered")

    # Hash password using your api/utils/auth.py
    hashed_password = hash_passsword(user_data.password)

    db_user = User(
        email=user_data.email,
        password_hash=hashed_password,
        first_name=user_data.first_name,
        last_name=user_data.last_name,
        phone_number=user_data.phone_number,
        date_of_birth=user_data.date_of_birth,
        gender=user_data.gender,
        is_verified=False
    )
    db.add(db_user)
    await db.commit()
    await db.refresh(db_user)
    return db_user

async def store_verification_token(email: str, token: str):
    async with r as redis:
        await redis.setex(f"verification_token:{email}", 600, token)

async def verify_user_email(db: AsyncSession, email: str, token: str) -> User:
    async with r as redis:
        stored_token = await redis.get(f"verification_token:{email}")
        if not stored_token or stored_token != token:
            raise ValueError("Invalid or expired verification token")

        user = await get_user_by_email(email, db)
        if not user:
            raise ValueError("User not found")

        user.is_verified = True
        db.add(user)
        await db.commit()
        await db.refresh(user)

        await redis.delete(f"verification_token:{email}")
        return user

# --- Token Blacklisting & Password Reset Token ---
async def blacklist_token(token: str):
    try:
        payload = jwt.decode(token, settings.SECRET_KEY, algorithms=[settings.ALGORITHM])
        exp = payload.get("exp")
        if exp:
            ttl = int(exp - datetime.utcnow().timestamp())
            if ttl > 0:
                async with r as redis:
                    await redis.setex(token, ttl, "blacklisted")
    except Exception as e:
        logger.error(f"Error blacklisting token: {e}")

async def is_token_blacklisted(token: str) -> bool:
    async with r as redis:
        result = await redis.get(token)
        return result == "blacklisted"

async def store_reset_token(email: str, token: str, expiry: int = 600):
    async with r as redis:
        key = f"reset_token:{token}"
        await redis.setex(key, expiry, email)

async def verify_token(token: str) -> Optional[str]:
    async with r as redis:
        key = f"reset_token:{token}"
        email = await redis.get(key)
        return email

async def delete_token(token: str):
    async with r as redis:
        key = f"reset_token:{token}"
        await redis.delete(key)

# --- Update Password ---
async def update_user_password(user: User, new_password: str, db: AsyncSession):
    user.password_hash = hash_passsword(new_password)
    db.add(user)
    await db.commit()
    await db.refresh(user)