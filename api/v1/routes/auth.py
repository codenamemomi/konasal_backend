from fastapi import FastAPI, HTTPException, Depends, APIRouter, Request, status, Cookie, Response
from sqlalchemy.orm import Session
from starlette.responses import JSONResponse
from itsdangerous import URLSafeTimedSerializer, BadSignature, SignatureExpired
from sqlalchemy import select
from pydantic import EmailStr
import random
from fastapi import BackgroundTasks


from core.config.settings import settings
from api.utils import email_utils
from api.v1.schemas.auth import UserCreate, UserResponse, LoginRequest, Token, PasswordResetRequest, PasswordResetVerify, ResendVerificationRequest, TokenVerifyRequest
from api.v1.services import auth as user_service
from api.db.session import get_db
from api.utils.auth import create_access_token, validate_password, validate_email_format, verify_password 
from api.v1.models.user import User
from api.utils.token import oauth2_scheme
from api.utils.token import serializer

auth = APIRouter(prefix="/auth", tags=["Auth"])


@auth.post("/signup", response_model=UserResponse)
async def signup(user_data: UserCreate, background_tasks: BackgroundTasks, db: Session = Depends(get_db)):
    validate_password(user_data.password)
    validate_email_format(user_data.email)

    existing_user = await user_service.get_user_by_email(user_data.email, db)
    if existing_user:
        raise HTTPException(status_code=400, detail="Email already registered")

    if len(user_data.password) < 8:
        raise HTTPException(status_code=400, detail="Password must be at least 8 characters long")

    hashed_password = user_service.hash_password(user_data.password)
    user_data.password = hashed_password

    try:
        await user_service.create_user(db, user_data)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))

    token = str(random.randint(10000, 99999))
    await user_service.store_token(user_data.email, token)

    # Email content
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

    background_tasks.add_task(
        email_utils.send_email_reminder,
        to_email=user_data.email,
        subject=subject,
        content=html_content
    )

    return JSONResponse(status_code=200, content={"message": "Verification code sent to your email"})


@auth.post("/verify-email")
async def verify_email(data: TokenVerifyRequest, db: Session = Depends(get_db)):
    email = await user_service.verify_token(data.token)
    if not email:
        raise HTTPException(status_code=400, detail="Invalid or expired token")

    user = await user_service.get_user_by_email(email, db)
    if not user:
        raise HTTPException(status_code=404, detail="User not found")

    if user.is_verified:
        return {"msg": "Email already verified"}

    await user_service.verify_user_email(user, db)
    await user_service.delete_token(data.token)

    return {"msg": "Email verified successfully"}


@auth.post("/resend-verification")
async def resend_verification_email(
    payload: ResendVerificationRequest,
    background_tasks: BackgroundTasks,
    db: Session = Depends(get_db)
):
    email = payload.email
    user = await user_service.get_user_by_email(email, db)
    if not user:
        raise HTTPException(status_code=404, detail="User not found")

    if user.is_verified:
        return JSONResponse(status_code=200, content={"message": "Email already verified"})

    token = str(random.randint(10000, 99999))
    await user_service.store_token(user.email, token)

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

    background_tasks.add_task(
        email_utils.send_email_reminder,
        to_email=user.email,
        subject="Your Verification Code",
        content=html_content
    )

    return JSONResponse(status_code=200, content={"message": "Verification email resent"})


@auth.post("/login")
async def login(response: Response, user_data: LoginRequest, db: Session = Depends(get_db)):
    stmt = select(User).where(User.email == user_data.email)
    result = await db.execute(stmt)
    user = result.scalar_one_or_none()

    if not user:
        raise HTTPException(status_code=401, detail="Invalid credentials")

    if not verify_password(user_data.password, user.password_hash):
        raise HTTPException(status_code=401, detail="Invalid credentials")

    if not user.is_verified:
        raise HTTPException(status_code=403, detail="Please verify your email before logging in")

    access_token = create_access_token(data={"sub": str(user.id)})

    

    response = JSONResponse(
        status_code=200,
        content={
            "message": "Login successful",
            "access_token": access_token,
            "token_type": "bearer",
            "user": {
                "id": str(user.id),
                "first_name": user.first_name,
                "last_name": user.last_name,
                "email": user.email,
                "gender": user.gender,
                "is_verified": user.is_verified
            }
        }
    )
    response.set_cookie(
        key="access_token",
        value=access_token,
        httponly=True,
        secure=False,
        samesite="lax",
        max_age=settings.ACCESS_TOKEN_EXPIRE_MINUTES * 60,
    )    
    return response


@auth.post("/logout")
async def logout(response: Response, request: Request):
    token = request.cookies.get("access_token")
    if not token:
        raise HTTPException(status_code=401, detail="please login first")
    
    await user_service.blacklist_token(token)
    response.delete_cookie("access_token")
    return {"detail": "Logged out successfully"}


@auth.post("/forgot-password")
async def forgot_password(data: PasswordResetRequest, db: Session = Depends(get_db)):
    user = user_service.get_user_by_email(data.email, db)
    if not user:
        raise HTTPException(status_code=404, detail="User not found")

    token = str(random.randint(10000, 99999))
    await user_service.store_token(data.email, token)

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

    try:
        email_utils.send_email_reminder(
            to_email=data.email,
            subject=subject,
            content=html_content
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to send email: {str(e)}")

    return {"msg": "Password reset token sent to your email"}


@auth.post("/reset-password")
async def reset_password(data: PasswordResetVerify, db: Session = Depends(get_db)):
    email = await user_service.verify_token(data.token)
    if not email:
        raise HTTPException(status_code=400, detail="Invalid or expired token")

    user = await user_service.get_user_by_email(email, db)
    if not user:
        raise HTTPException(status_code=404, detail="User not found")

    await user_service.update_user_password(user, data.new_password, db)
    await user_service.delete_token(data.token)

    return {"msg": "Password reset successfully"}







# @auth.post("/signup", response_model=UserResponse)
# async def signup(user_data: UserCreate, db: Session = Depends(get_db)):
#     validate_password(user_data.password)
#     validate_email_format(user_data.email)

#     existing_user = await user_service.get_user_by_email(user_data.email, db)
#     if existing_user:
#         raise HTTPException(status_code=400, detail="Email already registered")

#     if len(user_data.password) < 8:
#         raise HTTPException(status_code=400, detail="Password must be at least 8 characters long")

#     hashed_password = user_service.hash_password(user_data.password)
#     user_data.password = hashed_password

#     try:
#         await user_service.create_user(db, user_data)
#     except ValueError as e:
#         raise HTTPException(status_code=400, detail=str(e))

#     token = str(random.randint(100000, 999999))

#     await user_service.store_token(user_data.email, token, expiry=600)

#     try:
#         email_utils.send_email_reminder(
#             to_email=user_data.email,
#             subject="Verify your email",
#             content=f"Your verification code is: {token}"
#         )
#     except Exception:
#         raise HTTPException(status_code=500, detail="Failed to send verification email")

#     return JSONResponse(status_code=200, content={"message": "Verification code sent to email"})



# @auth.post("/verify")
# async def verify_email(data: EmailVerificationRequest, db: Session = Depends(get_db)):
#     stored_email = await user_service.verify_token(data.token)

#     if stored_email != data.email:
#         raise HTTPException(status_code=400, detail="Invalid or expired token")

#     try:
#         await user_service.verify_user_email(data.email, db)
#     except ValueError:
#         raise HTTPException(status_code=400, detail="Email not found")

#     await user_service.delete_token(data.token)

#     return JSONResponse(status_code=200, content={"message": "Email verified successfully"})