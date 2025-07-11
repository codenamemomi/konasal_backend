from fastapi import Depends
from fastapi.security import OAuth2PasswordBearer
from itsdangerous import URLSafeTimedSerializer
from core.config.settings import settings
from passlib.context import CryptContext


oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/api/v1/user/login")
serializer = URLSafeTimedSerializer(settings.SECRET_KEY)
pwd= CryptContext(schemes=["bcrypt"], deprecated="auto")


