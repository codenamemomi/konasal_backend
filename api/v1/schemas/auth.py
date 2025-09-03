from pydantic import BaseModel, EmailStr, Field, model_validator, field_serializer
from typing import Optional, Literal, Union
from datetime import date
from enum import Enum
import uuid

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
        password = values.get("password")
        password_verify = values.get("password_verify")
        if str(password) != str(password_verify):
            raise ValueError(f"Passwords do not match: {password!r} vs {password_verify!r}")
        return values

class UserResponse(BaseModel):
    id: Union[str, uuid.UUID]  # Accept multiple types including UUID
    email: EmailStr
    is_verified: bool
    first_name: str
    last_name: str
    phone_number: Optional[str] = None
    date_of_birth: Optional[date] = None
    gender: Optional[GenderEnum] = None
    profile_picture: Optional[str] = None

    @field_serializer("date_of_birth")
    def format_birth_date(self, dob: Optional[date], _info) -> Optional[str]:
        return dob.strftime("%d-%m") if dob else None

    @field_serializer("id")  # Add serializer for ID
    def serialize_id(self, id_value: Union[int, str, uuid.UUID], _info) -> str:
        return str(id_value)  # Convert UUID to string for JSON serialization

    class Config:
        from_attributes = True

class UserUpdate(BaseModel):
    email: Optional[EmailStr] = None
    first_name: Optional[str] = Field(None, min_length=2, max_length=20)
    last_name: Optional[str] = Field(None, min_length=2, max_length=20)
    phone_number: Optional[str] = None
    date_of_birth: Optional[date] = None
    gender: Optional[GenderEnum] = None

class UserInfo(BaseModel):
    id: str  # Keep as string
    first_name: str
    last_name: str
    email: EmailStr
    phone_number: Optional[str] = None
    date_of_birth: Optional[date] = None
    gender: Optional[GenderEnum] = None
    is_verified: bool
    profile_picture: Optional[str] = None

    @field_serializer("date_of_birth")
    def format_birth_date(self, dob: Optional[date], _info) -> Optional[str]:
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
    email: EmailStr
    token: str

class ResendVerificationRequest(BaseModel):
    email: EmailStr

class LoginRequest(BaseModel):
    email: EmailStr
    password: str