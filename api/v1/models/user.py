from sqlalchemy import Column, String, Boolean, Date
from sqlalchemy.types import Enum as SQLAlchemyEnum
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship
from datetime import date
from enum import Enum
import uuid
from api.v1.models.base_class import BaseModel

class GenderEnum(str, Enum):
    MALE = "MALE"
    FEMALE = "FEMALE"
    OTHER = "OTHER"

class User(BaseModel):
    __tablename__ = "users"

    # Make sure you're NOT overriding the id field from BaseModel
    # Remove this line if it exists:
    # id = Column(Integer, primary_key=True)
    
    first_name = Column(String, nullable=False)
    last_name = Column(String, nullable=False)
    email = Column(String, nullable=False, unique=True)
    date_of_birth = Column(Date, nullable=True)
    gender = Column(SQLAlchemyEnum(GenderEnum), nullable=True)
    phone_number = Column(String, nullable=True)
    password_hash = Column(String, nullable=False)
    is_verified = Column(Boolean, default=False)
    profile_picture = Column(String, nullable=True)

    enrollments = relationship("Enrollment", back_populates="user")
    payments = relationship("Payment", back_populates="user")