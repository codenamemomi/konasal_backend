from sqlalchemy import Column, String, Boolean, Date
from sqlalchemy.types import Enum as SQLAlchemyEnum
from sqlalchemy.orm import relationship
from datetime import date
from enum import Enum

from api.v1.models.base_class import BaseModel


class GenderEnum(str, Enum):
    MALE = "MALE"
    FEMALE = "FEMALE"


class User(BaseModel):
    __tablename__ = "users"

    first_name = Column(String, nullable=False)
    last_name = Column(String, nullable=False)
    email = Column(String, nullable=False, unique=True)
    date_of_birth = Column(Date, nullable=True)
    gender = Column(SQLAlchemyEnum(GenderEnum), nullable=True)
    password_hash = Column(String, nullable=False)
    is_verified = Column(Boolean, default=False)




fake_user_db = {}