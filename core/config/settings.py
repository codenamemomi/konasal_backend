from pydantic_settings import BaseSettings, SettingsConfigDict
from pydantic import AnyHttpUrl, field_validator
from typing import List, Optional, Union

class Settings(BaseSettings):
    ENVIRONMENT: str = "development"
    DEBUG: bool = True

    PROJECT_NAME: str = "Konosal API"
    VERSION: str = "1.0.0"

    # Database settings
    POSTGRES_SERVER: str
    POSTGRES_USER: str
    POSTGRES_PASSWORD: str
    POSTGRES_DB: str
    POSTGRES_PORT: str = "5432"

    SECRET_KEY: str
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 30

    BACKEND_CORS_ORIGINS: List[str] = ["http://127.0.0.1:5500"]  # Updated

    EMAIL_HOST: Optional[str] = None
    EMAIL_PORT: Optional[int] = None
    EMAIL_USERNAME: Optional[str] = None  # Changed from EMAILS_FROM_EMAIL
    EMAIL_PASSWORD: Optional[str] = None
    EMAIL_FROM: Optional[str] = None  # Changed from MAIL_FROM
    EMAIL_USE_SSL: bool = True  # New setting to specify SSL usage
    
    
    # Remove or keep these for backward compatibility
    EMAILS_FROM_EMAIL: Optional[str] = None  # Keep for compatibility
    MAIL_FROM: Optional[str] = None  # Keep for compatibility
    MAIL_FROM_NAME: Optional[str] = None

    VERIFICATION_BASE_URL: Optional[str] = None

    REDIS_HOST: str 
    REDIS_PORT: int
    REDIS_DB: int
    REDIS_PASSWORD: str = ""
    REDIS_RESPONSE: bool = True
    REDIS_URL: str

    CELERY_BROKER_URL: str
    CELERY_RESULT_BACKEND: str
    
    SENDGRID_API_KEY: str
    
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=True,
    )

    @field_validator("BACKEND_CORS_ORIGINS", mode="before")
    @classmethod
    def assemble_cors_origins(cls, v: Union[str, List[str]]) -> List[str]:
        if isinstance(v, str):
            return [i.strip() for i in v.split(",")]
        return v

    @property
    def SQLALCHEMY_DATABASE_URI(self) -> str:
        return f"postgresql+asyncpg://{self.POSTGRES_USER}:{self.POSTGRES_PASSWORD}@{self.POSTGRES_SERVER}:{self.POSTGRES_PORT}/{self.POSTGRES_DB}"

settings = Settings()