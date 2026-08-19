"""
Security: JWT token handling, password hashing, and authentication dependencies.
"""
import secrets
from datetime import datetime, timedelta, timezone
from typing import Optional, Union
from uuid import UUID

from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from jose import JWTError, jwt
from passlib.context import CryptContext
from pydantic import ValidationError
from sqlalchemy.ext.asyncio import AsyncSession

from src.core.config import settings
from src.core.database import get_db

# bcrypt cost factor 12 = ~250ms hashing on modern CPUs
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto", bcrypt__rounds=12)
oauth2_scheme = OAuth2PasswordBearer(tokenUrl=f"{settings.API_V1_STR}/auth/login")

REFRESH_REVOKED_PREFIX = "auth:refresh:revoked:"
REFRESH_ACTIVE_PREFIX = "auth:refresh:active:"


def verify_password(plain_password: str, hashed_password: str) -> bool:
    """Verify plain password against bcrypt hash."""
    return pwd_context.verify(plain_password, hashed_password)


def hash_password(password: str) -> str:
    """Hash password using bcrypt."""
    return pwd_context.hash(password)


def _now() -> datetime:
    """Current UTC datetime."""
    return datetime.now(timezone.utc)


def create_access_token(subject: Union[str, UUID], scopes: Optional[list[str]] = None) -> str:
    """
    Create short-lived access token (expires in ACCESS_TOKEN_EXPIRE_MINUTES).
    """
    payload = {
        "sub": str(subject),
        "type": "access",
        "scopes": scopes or [],
        "iat": _now().timestamp(),
        "exp": (_now() + timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)).timestamp(),
        "jti": secrets.token_urlsafe(16),
    }
    return jwt.encode(payload, settings.SECRET_KEY, algorithm=settings.ALGORITHM)


def create_refresh_token(subject: Union[str, UUID]) -> tuple[str, str]:
    """
    Create long-lived refresh token (expires in REFRESH_TOKEN_EXPIRE_DAYS).
    Returns (token, jti) so caller can store jti in Redis for rotation tracking.
    """
    jti = secrets.token_urlsafe(24)
    payload = {
        "sub": str(subject),
        "type": "refresh",
        "iat": _now().timestamp(),
        "exp": (_now() + timedelta(days=settings.REFRESH_TOKEN_EXPIRE_DAYS)).timestamp(),
        "jti": jti,
    }
    return jwt.encode(payload, settings.SECRET_KEY, algorithm=settings.ALGORITHM), jti


def verify_token(token: str) -> dict:
    """
    Verify and decode JWT token.
    Returns payload dict with 'sub', 'type', 'jti', 'exp', etc.
    """
    try:
        payload = jwt.decode(token, settings.SECRET_KEY, algorithms=[settings.ALGORITHM])
        return payload
    except (JWTError, ValidationError) as exc:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Could not validate credentials",
            headers={"WWW-Authenticate": "Bearer"},
        ) from exc


async def get_current_user(
    token: str = Depends(oauth2_scheme),
    db: AsyncSession = Depends(get_db),
):
    """
    Dependency to extract current user from access token.
    Validates token type is 'access' and user exists and is active.
    """
    from src.modules.users.repository import UserRepository

    token_data = verify_token(token)
    if token_data.get("type") != "access":
        raise HTTPException(status_code=401, detail="Wrong token type")

    try:
        user_id = UUID(token_data.get("sub"))
    except (ValueError, TypeError):
        raise HTTPException(status_code=401, detail="Invalid user ID in token")

    user_repo = UserRepository(db)
    user = await user_repo.get_by_id(user_id)
    if not user or not user.is_active:
        raise HTTPException(status_code=401, detail="User inactive or not found")

    return user


async def is_refresh_revoked(jti: str) -> bool:
    """Check if refresh token JTI has been revoked (cached in Redis)."""
    # TODO: Implement Redis caching for refresh token revocation
    # For now, assume no tokens are revoked (return False)
    return False


async def revoke_refresh(jti: str) -> None:
    """Revoke refresh token by JTI (store in Redis with expiry)."""
    # TODO: Implement Redis caching for refresh token revocation
    pass


async def register_active_refresh(jti: str, expires_in_seconds: int) -> None:
    """Register active refresh token in Redis (for rotation tracking)."""
    # TODO: Implement Redis caching for active refresh tokens
    pass
