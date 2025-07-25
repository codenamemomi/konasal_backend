from uuid import UUID
from enum import Enum
from datetime import date
from typing import Optional, Literal

from pydantic import (
    BaseModel,
    EmailStr,
    Field,
    model_validator,
    field_serializer
)

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
    phone_number: Optional[str] = None
    date_of_birth: Optional[date] = None
    gender: Optional[GenderEnum] = None

    @model_validator(mode="before")
    def passwords_match(cls, values):
        if values.get("password") != values.get("password_verify"):
            raise ValueError("Passwords do not match")
        return values

class UserResponse(BaseModel):
    id: UUID
    email: EmailStr
    is_verified: bool
    first_name: str
    last_name: str
    phone_number: Optional[str] = None
    date_of_birth: Optional[date] = None
    gender: Optional[GenderEnum] = None

    @field_serializer("date_of_birth", mode="plain")
    def format_birth_date(cls, dob: Optional[date]) -> Optional[str]:
        return dob.strftime("%d-%m") if dob else None

    class Config:
        orm_mode = True

class UserUpdate(BaseModel):
    email: Optional[EmailStr] = None
    first_name: Optional[str] = Field(None, min_length=2, max_length=20)
    last_name: Optional[str] = Field(None, min_length=2, max_length=20)
    phone_number: Optional[str] = None
    date_of_birth: Optional[date] = None
    gender: Optional[GenderEnum] = None

class LoginRequest(BaseModel):
    email: EmailStr
    password: str

class UserInfo(BaseModel):
    id: str
    first_name: str
    last_name: str
    email: EmailStr
    phone_number: Optional[str] = None
    date_of_birth: Optional[date] = None
    gender: Optional[GenderEnum] = None
    is_verified: bool

    @field_serializer("date_of_birth", mode="plain")
    def format_birth_date(cls, dob: Optional[date]) -> Optional[str]:
        return dob.strftime("%d-%m") if dob else None

class LoginResponse(BaseModel):
    message: str
    access_token: str
    token_type: Literal["bearer"]
    user: UserInfo

class Token(BaseModel):
    access_token: str
    token_type: str = "bearer"

class LogoutRequest(BaseModel):
    access_token: str

class PasswordResetRequest(BaseModel):
    email: EmailStr

class PasswordResetVerify(BaseModel):
    token: str
    new_password: str
    new_password_verify: str

    @model_validator(mode="before")
    def passwords_match(cls, values):
        if values["new_password"] != values["new_password_verify"]:
            raise ValueError("Passwords do not match")
        return values

class TokenVerifyRequest(BaseModel):
    token: str

class ResendVerificationRequest(BaseModel):
    email: EmailStr
