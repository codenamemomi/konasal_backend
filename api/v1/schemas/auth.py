from uuid import UUID
from enum import Enum
from datetime import date
from pydantic import BaseModel, EmailStr, Field, model_validator, field_validator
from typing import Optional


class GenderEnum(str, Enum):
    MALE = "MALE"
    FEMALE = "FEMALE"
    OTHER = "OTHER"


class UserCreate(BaseModel):
    email: EmailStr
    password: str
    password_verify: str
    first_name: str
    last_name: str
    date_of_birth: Optional[date] = None
    gender: Optional[GenderEnum] = None

    @model_validator(mode="before")
    def passwords_match(cls, values):
        password = values.get("password")
        password_verify = values.get("password_verify")
        if password != password_verify:
            raise ValueError("passwords do not match")
        return values



class UserResponse(BaseModel):
    id: UUID
    email: EmailStr
    is_verified: bool
    first_name: str
    last_name: str
    date_of_birth: Optional[date] = None
    gender: Optional[GenderEnum] = None

    class Config:
        orm_mode = True


class UserUpdate(BaseModel):
    email: Optional[EmailStr] = None
    first_name: Optional[str] = Field(None, min_length=2, max_length=20)
    last_name: Optional[str] = Field(None, min_length=2, max_length=20)
    date_of_birth: Optional[date] = None
    gender: Optional[GenderEnum] = None


class LoginRequest(BaseModel):
    email: EmailStr
    password: str

class Token(BaseModel):
    access_token: str
    token_type: str = "bearer"

class LogoutRequest(BaseModel):
    access_token: str

class PasswordResetRequest(BaseModel):
    email: EmailStr


class TokenVerifyRequest(BaseModel):
    token: str
class PasswordResetVerify(BaseModel):
    token: str
    new_password: str
    new_password_verify: str

    @model_validator(mode="before")
    def passwords_match(cls, values):
        if values["new_password"] != values["new_password_verify"]:
            raise ValueError("Passwords do not match")
        return values
    

class ResendVerificationRequest(BaseModel):
    email: EmailStr


# class EmailVerificationRequest(BaseModel):
#     email: str
#     token: str