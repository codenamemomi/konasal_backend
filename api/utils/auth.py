import re
from fastapi import HTTPException, status
from email_validator import validate_email, EmailNotValidError
from jose import jwt
from core.config.settings import settings
from datetime import datetime, timedelta
from api.utils.token import serializer, pwd



def hash_passsword(password:str) -> str:
    return pwd.hash(password)

def validate_password(password:str) -> bool:
    if len(password) < 8:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Password must be at least 8 characters long")
    if not re.search(r"[A-Z]", password):
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Password must contain at least one uppercase letter")
    if not re.search(r"[a-z]", password):
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Password must contain at least one lowercase letter")
    if not re.search(r"[0-9]", password):
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Password must contain at least one digit")
    if not re.search(r"[!@#$%^&*(),.?\":{}|<>]", password):
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Password must contain at least one special character")
    return True

def verify_password(plain_password:str, hashed_password:str) -> bool:
    return pwd.verify(plain_password, hashed_password)

def validate_email_format(email:str) -> bool:
    try:
        valid = validate_email(email)
        return valid.email
    except EmailNotValidError as e:
        raise HTTPException(status_code=400, detail=f'Invalid email format: {str(e)}')
    
def create_access_token(data: dict, expires_delta: timedelta = None) -> str:
    to_encode = data.copy()
    expire = datetime.utcnow() + (expires_delta or timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES))
    to_encode.update({"exp": expire})
    return jwt.encode(to_encode, settings.SECRET_KEY, algorithm=settings.ALGORITHM)