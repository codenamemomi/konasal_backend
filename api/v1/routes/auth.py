# api/v1/routes/auth.py
from fastapi import FastAPI, HTTPException, Depends, APIRouter, Request, status, Cookie, Response, BackgroundTasks
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from pydantic import EmailStr, BaseModel
from starlette.responses import JSONResponse
import random

from core.config.settings import settings
from api.utils.email_utils import send_email_reminder
from api.utils.auth import validate_password, validate_email_format, verify_password, create_access_token
from api.v1.schemas.auth import UserCreate, UserResponse, LoginRequest, Token, PasswordResetRequest, PasswordResetVerify, ResendVerificationRequest, TokenVerifyRequest, LoginResponse, UserInfo
from api.v1.services import auth as user_service
from api.db.session import get_db
from api.v1.models.user import User
from api.utils.token import oauth2_scheme

auth = APIRouter(prefix="/auth", tags=["Auth"])

class MessageResponse(BaseModel):
    message: str

@auth.post("/signup", response_model=MessageResponse)
async def signup(user_data: UserCreate, background_tasks: BackgroundTasks, db: AsyncSession = Depends(get_db)):
    print(f"Signup request: {user_data.dict()}")  # Debug
    try:
        validate_password(user_data.password)
        validate_email_format(user_data.email)

        existing_user = await user_service.get_user_by_email(user_data.email, db)
        if existing_user:
            raise HTTPException(status_code=400, detail="Email already registered")

        await user_service.create_user(db, user_data)

        token = str(random.randint(10000, 99999))
        await user_service.store_verification_token(user_data.email, token)

        subject = "Verify Your Email Address"
        html_content = f"""
        <html>
            <body>
                <h2>Email Verification</h2>
                <p>Use the following verification code to activate your account:</p>
                <h3 style="color: #007BFF;">{token}</h3>
                <p>This code is valid for 10 minutes.</p>
            </body>
        </html>
        """

        # Only try to send email if configured, but always store the token
        from api.utils.email_utils import is_email_configured
        if is_email_configured():
            background_tasks.add_task(
                send_email_reminder,
                to_email=user_data.email,
                subject=subject,
                content=html_content
            )
            return {"message": "Verification code sent to your email"}
        else:
            # For development, return the token directly
            print(f"Development mode: Verification token for {user_data.email}: {token}")
            return {"message": f"Verification code: {token} (email not configured)"}
            
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    
@auth.post("/verify-email", response_model=MessageResponse)
async def verify_email(data: TokenVerifyRequest, db: AsyncSession = Depends(get_db)):
    try:
        user = await user_service.verify_user_email(db, data.email, data.token)
        return {"message": "Email verified successfully"}
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))

@auth.post("/resend-verification", response_model=MessageResponse)
async def resend_verification_email(payload: ResendVerificationRequest, background_tasks: BackgroundTasks, db: AsyncSession = Depends(get_db)):
    email = payload.email
    user = await user_service.get_user_by_email(email, db)
    if not user:
        raise HTTPException(status_code=404, detail="User not found")

    if user.is_verified:
        return {"message": "Email already verified"}

    token = str(random.randint(10000, 99999))
    await user_service.store_verification_token(user.email, token)

    html_content = f"""
    <html>
        <body>
            <h2>Verify Your Email</h2>
            <p>Use the following verification code to verify your email address:</p>
            <h3 style="font-size: 24px; color: #007BFF;">{token}</h3>
            <p>If you didn't request this, you can safely ignore it.</p>
        </body>
    </html>
    """

    from api.utils.email_utils import is_email_configured
    if is_email_configured():
        background_tasks.add_task(
            send_email_reminder,
            to_email=user.email,
            subject="Your Verification Code",
            content=html_content
        )
        return {"message": "Verification email resent"}
    else:
        print(f"Development mode: Resent verification token for {email}: {token}")
        return {"message": f"Verification code: {token} (email not configured)"}
    
@auth.post("/login", response_model=LoginResponse)
async def login(response: Response, user_data: LoginRequest, db: AsyncSession = Depends(get_db)):
    stmt = select(User).where(User.email == user_data.email)
    result = await db.execute(stmt)
    user = result.scalar_one_or_none()

    if not user or not verify_password(user_data.password, user.password_hash):
        raise HTTPException(status_code=401, detail="Invalid email or password")

    if not user.is_verified:
        raise HTTPException(status_code=403, detail="Please verify your email before logging in")

    access_token = create_access_token(data={"sub": str(user.id)})

    # Set cookie with proper settings for cross-origin
    response.set_cookie(
        key="access_token",
        value=access_token,
        httponly=True,
        secure=False,  # False for HTTP in development
        samesite="none",  # Changed to "none" for cross-origin
        max_age=settings.ACCESS_TOKEN_EXPIRE_MINUTES * 60,
        path="/",
        domain=None  # Allow all domains
    )

    # Also store in response for frontend to use as fallback
    return {
        "message": "Login successful",
        "access_token": access_token,  # Still return in response
        "token_type": "bearer",
        "user": {
            "id": str(user.id),
            "first_name": user.first_name,
            "last_name": user.last_name,
            "email": user.email,
            "date_of_birth": user.date_of_birth,
            "gender": user.gender,
            "phone_number": user.phone_number,
            "is_verified": user.is_verified,
            "profile_picture": user.profile_picture
        }
    }

@auth.post("/logout", response_model=MessageResponse)
async def logout(response: Response, request: Request):
    token = request.cookies.get("access_token")
    if not token:
        raise HTTPException(status_code=401, detail="Not authenticated")

    await user_service.blacklist_token(token)
    response.delete_cookie("access_token")
    return {"message": "Logged out successfully"}

@auth.post("/forgot-password", response_model=MessageResponse)
async def forgot_password(data: PasswordResetRequest, background_tasks: BackgroundTasks, db: AsyncSession = Depends(get_db)):
    user = await user_service.get_user_by_email(data.email, db)
    if not user:
        raise HTTPException(status_code=404, detail="User not found")

    token = str(random.randint(10000, 99999))
    await user_service.store_reset_token(data.email, token)  # Use store_reset_token

    subject = "Password Reset Request"
    html_content = f"""
    <html>
        <body>
            <h2>Password Reset</h2>
            <p>You requested to reset your password. Use the token below to proceed:</p>
            <h3 style="color: #007BFF;">{token}</h3>
            <p>This token is valid for 10 minutes.</p>
            <p>If you did not request this, please ignore this email.</p>
        </body>
    </html>
    """

    background_tasks.add_task(
        send_email_reminder,
        to_email=data.email,
        subject=subject,
        content=html_content
    )

    return {"message": "Password reset token sent to your email"}

@auth.post("/reset-password", response_model=MessageResponse)
async def reset_password(data: PasswordResetVerify, db: AsyncSession = Depends(get_db)):
    email = await user_service.verify_token(data.token)
    if not email:
        raise HTTPException(status_code=400, detail="Invalid or expired token")

    user = await user_service.get_user_by_email(email, db)
    if not user:
        raise HTTPException(status_code=404, detail="User not found")

    await user_service.update_user_password(user, data.new_password, db)
    await user_service.delete_token(data.token)

    return {"message": "Password reset successfully"}

