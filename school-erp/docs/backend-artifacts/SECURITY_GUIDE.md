# Kenya School ERP - Security Implementation Guide

This guide outlines the production-ready security implementation for the Kenya School ERP system, focusing on Authentication, Authorization, Kenya Data Protection Act (KDPA) compliance, Rate Limiting, and Input Validation.

## 1. JWT Authentication System

The system uses JSON Web Tokens (JWT) for stateless authentication. Access tokens are short-lived (30 minutes), while refresh tokens are long-lived (7 days), stored in HttpOnly, Secure, SameSite=Lax cookies, and **rotated on every refresh**. Each refresh JWT carries a unique `jti` tracked in a Redis revocation store so previous refresh tokens cannot be reused after logout, rotation, or forced revocation.

### `src/core/security.py`

```python
import secrets
from datetime import datetime, timedelta, timezone
from typing import Any, Union
from uuid import UUID

from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from jose import JWTError, jwt
from passlib.context import CryptContext
from pydantic import ValidationError
from redis.asyncio import Redis
from sqlalchemy.ext.asyncio import AsyncSession

from src.core.config import settings
from src.core.database import get_db
from src.core.redis import get_redis
from src.modules.users.repository import UserRepository
from src.modules.users.models import User
from src.schemas.token import TokenPayload

# bcrypt cost factor 12 = ~250ms hashing on modern CPUs.
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto", bcrypt__rounds=12)
oauth2_scheme = OAuth2PasswordBearer(tokenUrl=f"{settings.API_V1_STR}/auth/login")

REFRESH_REVOKED_PREFIX = "auth:refresh:revoked:"
REFRESH_ACTIVE_PREFIX = "auth:refresh:active:"


def verify_password(plain_password: str, hashed_password: str) -> bool:
    return pwd_context.verify(plain_password, hashed_password)


def hash_password(password: str) -> str:
    return pwd_context.hash(password)


def _now() -> datetime:
    return datetime.now(timezone.utc)


def create_access_token(subject: Union[str, UUID], scopes: list[str] | None = None) -> str:
    payload = {
        "sub": str(subject),
        "type": "access",
        "scopes": scopes or [],
        "iat": _now(),
        "exp": _now() + timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES),
        "jti": secrets.token_urlsafe(16),
    }
    return jwt.encode(payload, settings.SECRET_KEY, algorithm=settings.ALGORITHM)


def create_refresh_token(subject: Union[str, UUID]) -> tuple[str, str]:
    """Returns (token, jti) so the caller can store the jti in Redis for rotation checks."""
    jti = secrets.token_urlsafe(24)
    payload = {
        "sub": str(subject),
        "type": "refresh",
        "iat": _now(),
        "exp": _now() + timedelta(days=settings.REFRESH_TOKEN_EXPIRE_DAYS),
        "jti": jti,
    }
    return jwt.encode(payload, settings.SECRET_KEY, algorithm=settings.ALGORITHM), jti


def verify_token(token: str) -> TokenPayload:
    try:
        payload = jwt.decode(token, settings.SECRET_KEY, algorithms=[settings.ALGORITHM])
        return TokenPayload(**payload)
    except (JWTError, ValidationError) as exc:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Could not validate credentials",
            headers={"WWW-Authenticate": "Bearer"},
        ) from exc


async def get_current_user(
    db: AsyncSession = Depends(get_db),
    token: str = Depends(oauth2_scheme),
) -> User:
    token_data = verify_token(token)
    if token_data.type != "access":
        raise HTTPException(status_code=401, detail="Wrong token type")

    user = await UserRepository(db).get_by_id(UUID(token_data.sub))
    if not user or not user.is_active:
        raise HTTPException(status_code=401, detail="User inactive or not found")
    return user


async def register_active_refresh(redis: Redis, user_id: UUID, jti: str) -> None:
    ttl = settings.REFRESH_TOKEN_EXPIRE_DAYS * 24 * 3600
    await redis.setex(f"{REFRESH_ACTIVE_PREFIX}{user_id}:{jti}", ttl, "1")


async def revoke_refresh(redis: Redis, jti: str) -> None:
    await redis.setex(
        f"{REFRESH_REVOKED_PREFIX}{jti}",
        settings.REFRESH_TOKEN_EXPIRE_DAYS * 24 * 3600,
        "1",
    )


async def is_refresh_revoked(redis: Redis, jti: str) -> bool:
    return bool(await redis.get(f"{REFRESH_REVOKED_PREFIX}{jti}"))
```

### Auth Router (`src/api/v1/endpoints/auth.py`)

```python
import secrets
from typing import Any
from uuid import UUID

from fastapi import APIRouter, Cookie, Depends, Header, HTTPException, Request, Response, status
from redis.asyncio import Redis
from sqlalchemy.ext.asyncio import AsyncSession

from src.core.config import settings
from src.core.database import get_db
from src.core.redis import get_redis
from src.core.security import (
    create_access_token,
    create_refresh_token,
    get_current_user,
    hash_password,
    is_refresh_revoked,
    register_active_refresh,
    revoke_refresh,
    verify_password,
    verify_token,
)
from src.modules.users.models import User
from src.modules.users.repository import UserRepository
from src.modules.users.password_policy import assert_password_meets_policy
from src.schemas.token import Token
from src.schemas.user import UserChangePassword, UserLogin

router = APIRouter(prefix="/auth", tags=["Authentication"])

REFRESH_COOKIE = "refresh_token"
CSRF_COOKIE = "csrf_token"
CSRF_HEADER = "X-CSRF-Token"


def _cookie_kwargs() -> dict:
    return {
        "httponly": True,
        "secure": settings.ENVIRONMENT == "production",
        "samesite": "lax",
        "max_age": settings.REFRESH_TOKEN_EXPIRE_DAYS * 24 * 60 * 60,
        "path": "/api/v1/auth",
    }


async def _issue_tokens(
    response: Response, redis: Redis, user_id: UUID, scopes: list[str],
) -> str:
    access_token = create_access_token(user_id, scopes=scopes)
    refresh_token, jti = create_refresh_token(user_id)
    await register_active_refresh(redis, user_id, jti)

    csrf_value = secrets.token_urlsafe(32)
    response.set_cookie(REFRESH_COOKIE, refresh_token, **_cookie_kwargs())
    response.set_cookie(
        CSRF_COOKIE,
        csrf_value,
        httponly=False,
        secure=settings.ENVIRONMENT == "production",
        samesite="lax",
        max_age=settings.REFRESH_TOKEN_EXPIRE_DAYS * 24 * 60 * 60,
    )
    return access_token


@router.post("/login", response_model=Token)
async def login(
    response: Response,
    request: Request,
    user_in: UserLogin,
    db: AsyncSession = Depends(get_db),
    redis: Redis = Depends(get_redis),
) -> Any:
    users = UserRepository(db)
    user = await users.get_by_email(user_in.email)

    # Brute-force lockout tracked in Redis; keep window short-term.
    lockout_key = f"auth:lockout:{user_in.email}"
    attempts = int(await redis.get(lockout_key) or 0)
    if attempts >= settings.LOGIN_MAX_ATTEMPTS:
        raise HTTPException(status_code=429, detail="Too many failed attempts. Try later.")

    if not user or not verify_password(user_in.password, user.password_hash):
        await redis.setex(lockout_key, settings.LOGIN_LOCKOUT_MINUTES * 60, attempts + 1)
        raise HTTPException(status_code=400, detail="Incorrect email or password")
    if not user.is_active:
        raise HTTPException(status_code=400, detail="Inactive user")

    await redis.delete(lockout_key)
    access_token = await _issue_tokens(response, redis, user.id, scopes=user.scopes)
    return {"access_token": access_token, "token_type": "bearer"}


@router.post("/refresh", response_model=Token)
async def refresh(
    response: Response,
    refresh_token: str | None = Cookie(default=None, alias=REFRESH_COOKIE),
    csrf_cookie: str | None = Cookie(default=None, alias=CSRF_COOKIE),
    csrf_header: str | None = Header(default=None, alias=CSRF_HEADER),
    db: AsyncSession = Depends(get_db),
    redis: Redis = Depends(get_redis),
) -> Any:
    if not refresh_token:
        raise HTTPException(status_code=401, detail="Refresh token missing")
    if not csrf_cookie or csrf_cookie != csrf_header:
        raise HTTPException(status_code=403, detail="CSRF validation failed")

    token_data = verify_token(refresh_token)
    if token_data.type != "refresh":
        raise HTTPException(status_code=401, detail="Wrong token type")
    if await is_refresh_revoked(redis, token_data.jti):
        raise HTTPException(status_code=401, detail="Refresh token revoked")

    await revoke_refresh(redis, token_data.jti)  # rotate: old jti dies immediately.

    user = await UserRepository(db).get_by_id(UUID(token_data.sub))
    if not user or not user.is_active:
        raise HTTPException(status_code=401, detail="User inactive or not found")

    access_token = await _issue_tokens(response, redis, user.id, scopes=user.scopes)
    return {"access_token": access_token, "token_type": "bearer"}


@router.post("/logout")
async def logout(
    response: Response,
    refresh_token: str | None = Cookie(default=None, alias=REFRESH_COOKIE),
    redis: Redis = Depends(get_redis),
) -> dict:
    if refresh_token:
        try:
            data = verify_token(refresh_token)
            await revoke_refresh(redis, data.jti)
        except HTTPException:
            pass
    response.delete_cookie(REFRESH_COOKIE, path="/api/v1/auth")
    response.delete_cookie(CSRF_COOKIE)
    return {"message": "Logged out"}


@router.post("/change-password")
async def change_password(
    payload: UserChangePassword,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> dict:
    if not verify_password(payload.current_password, current_user.password_hash):
        raise HTTPException(status_code=400, detail="Incorrect current password")
    assert_password_meets_policy(payload.new_password)
    await UserRepository(db).update_password(current_user, hash_password(payload.new_password))
    return {"message": "Password updated"}
```

### Password policy (`src/modules/users/password_policy.py`)

```python
import re
from fastapi import HTTPException
from src.core.config import settings

# Load a common-password blocklist at import time; keep it short in-repo, fetch fuller list from S3 in prod.
COMMON_PASSWORDS = {"password", "12345678", "qwerty123", "letmein", "school123"}

_UPPER = re.compile(r"[A-Z]")
_LOWER = re.compile(r"[a-z]")
_DIGIT = re.compile(r"\d")
_SYMBOL = re.compile(r"[^\w\s]")


def assert_password_meets_policy(candidate: str) -> None:
    if len(candidate) < settings.PASSWORD_MIN_LENGTH:
        raise HTTPException(400, f"Password must be at least {settings.PASSWORD_MIN_LENGTH} chars.")
    if candidate.lower() in COMMON_PASSWORDS:
        raise HTTPException(400, "Password is on the common-password blocklist.")
    checks = [_UPPER, _LOWER, _DIGIT, _SYMBOL]
    if sum(bool(rx.search(candidate)) for rx in checks) < 3:
        raise HTTPException(400, "Password must mix upper, lower, digit and symbol characters.")
```

## 2. Role-Based Access Control (RBAC)

### `src/core/permissions.py`

```python
from enum import Enum
from typing import List, Dict

class Permission(str, Enum):
    # Finance
    FINANCE_VIEW = "finance:view"
    FINANCE_CREATE = "finance:create"
    FINANCE_APPROVE = "finance:approve"
    FINANCE_CLOSE_PERIOD = "finance:close_period"
    JOURNAL_POST = "journal:post"
    JOURNAL_REVERSE = "journal:reverse"
    
    # Payroll
    PAYROLL_VIEW = "payroll:view"
    PAYROLL_RUN = "payroll:run"
    PAYROLL_APPROVE = "payroll:approve"
    
    # Students
    STUDENTS_VIEW = "students:view"
    STUDENTS_MANAGE = "students:manage"
    
    # Operations
    GATE_OFFICER = "gate:manage"
    VISITOR_LOG = "visitor:log"
    
    # Procurement
    PROCUREMENT_REQUISITION = "procurement:requisition"
    PROCUREMENT_APPROVE_TIER1 = "procurement:approve_tier1"
    PROCUREMENT_APPROVE_TIER2 = "procurement:approve_tier2"
    PROCUREMENT_APPROVE_BOM = "procurement:approve_bom"
    
    # Inventory
    INVENTORY_VIEW = "inventory:view"
    INVENTORY_MANAGE = "inventory:manage"
    
    # HR
    HR_VIEW = "hr:view"
    HR_MANAGE = "hr:manage"
    
    # Reports
    REPORTS_FINANCIAL = "reports:financial"
    REPORTS_ACADEMIC = "reports:academic"
    REPORTS_EXECUTIVE = "reports:executive"
    
    # Admin
    SYSTEM_ADMIN = "system:admin"
    AUDIT_LOG_VIEW = "audit_log:view"

class Role(str, Enum):
    PRINCIPAL = "PRINCIPAL"
    DEPUTY_PRINCIPAL_ADMIN = "DEPUTY_PRINCIPAL_ADMIN"
    DEPUTY_PRINCIPAL_ACADEMICS = "DEPUTY_PRINCIPAL_ACADEMICS"
    BURSAR = "BURSAR"
    ACCOUNTS_CLERK = "ACCOUNTS_CLERK"
    HOD = "HOD"
    TEACHER = "TEACHER"
    CLASS_TEACHER = "CLASS_TEACHER"
    BOARDING_MASTER = "BOARDING_MASTER"
    GATE_OFFICER = "GATE_OFFICER"
    STOREKEEPER = "STOREKEEPER"
    NURSE = "NURSE"
    PARENT = "PARENT"
    STUDENT = "STUDENT"

ROLE_PERMISSIONS: Dict[Role, List[Permission]] = {
    Role.PRINCIPAL: [
        Permission.REPORTS_EXECUTIVE, Permission.REPORTS_FINANCIAL, Permission.REPORTS_ACADEMIC,
        Permission.FINANCE_APPROVE, Permission.FINANCE_CLOSE_PERIOD, Permission.JOURNAL_REVERSE,
        Permission.PAYROLL_APPROVE, Permission.PROCUREMENT_APPROVE_BOM,
        Permission.STUDENTS_MANAGE, Permission.HR_MANAGE, Permission.AUDIT_LOG_VIEW,
    ],
    Role.DEPUTY_PRINCIPAL_ADMIN: [
        Permission.REPORTS_EXECUTIVE, Permission.STUDENTS_MANAGE, Permission.GATE_OFFICER,
        Permission.HR_VIEW,
    ],
    Role.DEPUTY_PRINCIPAL_ACADEMICS: [
        Permission.REPORTS_ACADEMIC, Permission.STUDENTS_MANAGE, Permission.HR_VIEW,
    ],
    Role.BURSAR: [
        Permission.FINANCE_VIEW, Permission.FINANCE_CREATE, Permission.JOURNAL_POST,
        Permission.PAYROLL_RUN, Permission.REPORTS_FINANCIAL, Permission.PROCUREMENT_APPROVE_TIER1,
    ],
    Role.ACCOUNTS_CLERK: [
        Permission.FINANCE_VIEW, Permission.FINANCE_CREATE, Permission.JOURNAL_POST,
    ],
    Role.HOD: [
        Permission.REPORTS_ACADEMIC, Permission.PROCUREMENT_REQUISITION,
    ],
    Role.CLASS_TEACHER: [
        Permission.REPORTS_ACADEMIC, Permission.STUDENTS_VIEW,
    ],
    Role.TEACHER: [Permission.STUDENTS_VIEW],
    Role.BOARDING_MASTER: [Permission.STUDENTS_MANAGE, Permission.GATE_OFFICER],
    Role.GATE_OFFICER: [Permission.GATE_OFFICER, Permission.VISITOR_LOG],
    Role.STOREKEEPER: [Permission.INVENTORY_VIEW, Permission.INVENTORY_MANAGE],
    Role.NURSE: [Permission.STUDENTS_VIEW],
    Role.PARENT: [],
    Role.STUDENT: [],
}


def require_permission(required_permission: Permission):
    async def permission_checker(current_user: "User" = Depends(get_current_user)) -> "User":
        user_role = Role(current_user.role)
        allowed = ROLE_PERMISSIONS.get(user_role, [])
        if Permission.SYSTEM_ADMIN in allowed or required_permission in allowed:
            return current_user
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail=f"Not enough permissions. Required: {required_permission.value}",
        )

    return permission_checker
```

### Audit Log Middleware (`src/middleware/audit.py`)

Audit logging never blocks the request loop. The middleware captures request metadata and enqueues a Celery task that writes the audit row asynchronously. The Postgres trigger in `DATABASE_SCHEMA.md` provides the fine-grained row-level record; this middleware provides HTTP-level `who called what` visibility.

```python
import hashlib
from starlette.middleware.base import BaseHTTPMiddleware
from fastapi import Request, Response

from src.tasks.audit import record_http_audit


class AuditLogMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next) -> Response:
        payload_hash: str | None = None
        if request.method in {"POST", "PUT", "PATCH", "DELETE"}:
            body = await request.body()
            payload_hash = hashlib.sha256(body).hexdigest() if body else None
            # Restore body for downstream handlers.
            async def _replay() -> bytes:
                return body
            request._body = body

        response = await call_next(request)

        record_http_audit.delay(
            user_id=str(getattr(request.state, "user_id", "")) or None,
            school_id=str(getattr(request.state, "school_id", "")) or None,
            method=request.method,
            endpoint=str(request.url.path),
            payload_hash=payload_hash,
            status_code=response.status_code,
            ip_address=request.client.host if request.client else None,
            user_agent=request.headers.get("user-agent"),
        )
        return response
```

## 3. Kenya Data Protection Act Compliance

### Encrypted SQLAlchemy Type (`src/core/encryption.py`)

> **Key rotation.** `settings.ENCRYPTION_KEY` may be a colon-separated list `active:previous`; the active key encrypts writes and either key decrypts reads. Rotate keys via `MultiFernet`, then re-encrypt column values in a background task before dropping the previous key.

```python
from cryptography.fernet import Fernet, MultiFernet
from sqlalchemy.types import String, TypeDecorator
from src.core.config import settings

_keys = [Fernet(k.encode()) for k in settings.ENCRYPTION_KEY.split(":") if k]
if not _keys:
    raise RuntimeError("ENCRYPTION_KEY must be set")
fernet = MultiFernet(_keys)


class EncryptedString(TypeDecorator):
    """Symmetric encryption for KDPA-sensitive columns (KRA PIN, bank account, medical notes)."""

    impl = String
    cache_ok = True

    def process_bind_param(self, value, dialect):
        if value is None:
            return None
        return fernet.encrypt(value.encode("utf-8")).decode("utf-8")

    def process_result_value(self, value, dialect):
        if value is None:
            return None
        return fernet.decrypt(value.encode("utf-8")).decode("utf-8")
```

### Data Retention & Export Services

```python
# src/services/data_privacy.py
from uuid import UUID
from celery import shared_task
from sqlalchemy.ext.asyncio import AsyncSession

from src.modules.students.repository import StudentRepository


class DataRetentionService:
    """Anonymise or delete student records older than KDPA-mandated retention (7 years post-clearance)."""

    @staticmethod
    @shared_task(name="purge_expired_data")
    def purge_expired_data() -> None:
        # Enqueues chunked async job that runs on the worker's own event loop.
        from src.tasks.retention import anonymise_expired
        anonymise_expired.delay()


class DataSubjectService:
    """KDPA right to portability — export all personal data held for a data subject."""

    @staticmethod
    async def export_student_data(db: AsyncSession, student_id: UUID) -> dict:
        repo = StudentRepository(db)
        student = await repo.get_full_profile(student_id)
        if student is None:
            return {}
        return {
            "profile": student.to_dict(),
            "financials": [tx.to_dict() for tx in student.transactions],
            "medical": [med.to_dict() for med in student.medical_records],
            "consent_status": student.consent.status if student.consent else None,
        }
```

## 4. API Rate Limiting

### `src/core/rate_limit.py`

```python
from slowapi import Limiter, _rate_limit_exceeded_handler
from slowapi.util import get_remote_address
from slowapi.errors import RateLimitExceeded
from fastapi import Request

limiter = Limiter(key_func=get_remote_address)

def rate_limit_config(app):
    app.state.limiter = limiter
    app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)

# Usage in Router:
# @router.post("/login")
# @limiter.limit("10/minute")
# def login_access_token(request: Request, ...):
```

## 5. Input Validation & SQL Injection Prevention

- **ORM Usage**: All database interactions use SQLAlchemy 2.0 async ORM, so queries are parameterised.
- **Pydantic v2 Validation**: Strict type checking and per-field sanitisation.

```python
# src/schemas/validators.py
from decimal import Decimal
from pydantic import BaseModel, field_validator


class SecureBaseModel(BaseModel):
    @field_validator("*", mode="before")
    @classmethod
    def escape_xss(cls, value):
        if isinstance(value, str):
            return value.replace("<", "&lt;").replace(">", "&gt;")
        return value


class CreateBursary(SecureBaseModel):
    amount: Decimal
    description: str

    @field_validator("amount")
    @classmethod
    def amount_must_be_positive(cls, value: Decimal) -> Decimal:
        if value <= 0:
            raise ValueError("Amount must be positive")
        return value
```
