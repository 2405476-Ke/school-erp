"""
Application configuration using Pydantic v2 Settings.
Loads from .env file with typed validation and defaults.
"""
from typing import Any, List, Optional, Union
from uuid import UUID

from pydantic import AnyHttpUrl, Field, PostgresDsn, ValidationInfo, field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Global application settings loaded from environment variables."""

    # ========== Application ==========
    PROJECT_NAME: str = "Kenya Secondary School ERP"
    ENVIRONMENT: str = Field(default="development", description="Environment: development, staging, production")
    API_V1_STR: str = "/api/v1"
    DEBUG: bool = False

    # ========== CORS ==========
    BACKEND_CORS_ORIGINS: List[AnyHttpUrl] = Field(default_factory=list)

    @field_validator("BACKEND_CORS_ORIGINS", mode="before")
    @classmethod
    def assemble_cors_origins(cls, v: Union[str, List[str]]) -> Union[List[str], str]:
        if isinstance(v, str) and not v.startswith("["):
            return [i.strip() for i in v.split(",")]
        if isinstance(v, (list, str)):
            return v
        raise ValueError(v)

    # ========== Security & JWT ==========
    SECRET_KEY: str = Field(..., description="JWT signing secret (generate: openssl rand -hex 32)")
    ENCRYPTION_KEY: str = Field(..., description="Fernet key for PII columns (generate: python -c \"from cryptography.fernet import Fernet;print(Fernet.generate_key().decode())\")")
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 30
    REFRESH_TOKEN_EXPIRE_DAYS: int = 7
    PASSWORD_MIN_LENGTH: int = 12
    LOGIN_MAX_ATTEMPTS: int = 5
    LOGIN_LOCKOUT_MINUTES: int = 15

    # ========== Database ==========
    POSTGRES_SERVER: str = Field(..., description="PostgreSQL server hostname")
    POSTGRES_USER: str = Field(..., description="PostgreSQL user")
    POSTGRES_PASSWORD: str = Field(..., description="PostgreSQL password")
    POSTGRES_DB: str = Field(..., description="PostgreSQL database name")
    POSTGRES_PORT: int = 5432
    DATABASE_URL: Optional[PostgresDsn] = None

    @field_validator("DATABASE_URL", mode="before")
    @classmethod
    def assemble_db_connection(cls, v: Optional[str], info: ValidationInfo) -> Any:
        """Build DATABASE_URL from individual postgres credentials if not provided."""
        if isinstance(v, str):
            return v
        data = info.data
        return PostgresDsn.build(
            scheme="postgresql+asyncpg",
            username=data.get("POSTGRES_USER"),
            password=data.get("POSTGRES_PASSWORD"),
            host=data.get("POSTGRES_SERVER"),
            port=int(data.get("POSTGRES_PORT", 5432)),
            path=data.get("POSTGRES_DB") or "",
        )

    # ========== Redis & Celery ==========
    REDIS_HOST: str = "localhost"
    REDIS_PORT: int = 6379
    REDIS_DB: int = 0
    REDIS_URL: str = Field(default="redis://localhost:6379/0")
    CELERY_BROKER_URL: str = Field(default="redis://localhost:6379/0")
    CELERY_RESULT_BACKEND: str = Field(default="redis://localhost:6379/1")
    CACHE_URL: str = Field(default="redis://localhost:6379/2")

    # ========== M-Pesa Daraja API ==========
    MPESA_ENVIRONMENT: str = "sandbox"
    MPESA_BASE_URL: str = Field(default="https://sandbox.safaricom.co.ke", description="Daraja API base URL")
    MPESA_CONSUMER_KEY: str = Field(..., description="Daraja API consumer key")
    MPESA_CONSUMER_SECRET: str = Field(..., description="Daraja API consumer secret")
    MPESA_PASSKEY: str = Field(..., description="M-Pesa STK Push passkey")
    MPESA_SHORTCODE: str = Field(default="174379", description="M-Pesa business shortcode")
    MPESA_CALLBACK_URL: AnyHttpUrl = Field(..., description="Callback URL for STK Push responses")
    MPESA_EXPRESS_CALLBACK_URL: AnyHttpUrl = Field(..., description="Callback URL for STK Push responses")
    MPESA_C2B_VALIDATION_URL: Optional[AnyHttpUrl] = None
    MPESA_C2B_CONFIRMATION_URL: Optional[AnyHttpUrl] = None
    MPESA_CALLBACK_ALLOWED_IPS: List[str] = Field(
        default_factory=lambda: ["196.201.214.200", "196.201.214.206", "196.201.213.114"],
        description="Comma-separated Safaricom IPs allowed for callbacks",
    )

    # ========== Africa's Talking SMS Gateway ==========
    SMS_PROVIDER: str = "africastalking"
    AT_USERNAME: str = Field(..., description="Africa's Talking username")
    AT_API_KEY: str = Field(..., description="Africa's Talking API key")
    SENDER_ID: str = Field(default="SCHOOL", description="SMS sender ID")

    # ========== KRA & Statutory ==========
    KRA_EMPLOYER_PIN: Optional[str] = None
    KRA_P10_ENDPOINT: Optional[AnyHttpUrl] = None

    model_config = SettingsConfigDict(
        env_file=".env",
        case_sensitive=True,
        extra="ignore",
    )


settings = Settings()
