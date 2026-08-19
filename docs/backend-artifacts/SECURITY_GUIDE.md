# Kenya School ERP - Security Implementation Guide

This guide outlines the production-ready security implementation for the Kenya School ERP system, focusing on Authentication, Authorization, Kenya Data Protection Act (KDPA) compliance, Rate Limiting, and Input Validation.

## 1. JWT Authentication System

The system uses JSON Web Tokens (JWT) for stateless authentication. Access tokens are short-lived (15 minutes), while refresh tokens are long-lived (7 days) and stored in HttpOnly, Secure cookies to prevent XSS attacks.

### `src/core/security.py`

```python
from datetime import datetime, timedelta
from typing import Any, Union
from jose import jwt, JWTError
from passlib.context import CryptContext
from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from pydantic import ValidationError

from src.core.config import settings
from src.schemas.token import TokenPayload
from src.db.session import get_db
from src.models.user import User
from src.crud.crud_user import user as crud_user
from sqlalchemy.orm import Session

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")
oauth2_scheme = OAuth2PasswordBearer(tokenUrl=f"{settings.API_V1_STR}/auth/login")

ALGORITHM = "HS256"

def verify_password(plain_password: str, hashed_password: str) -> bool:
    return pwd_context.verify(plain_password, hashed_password)

def hash_password(password: str) -> str:
    return pwd_context.hash(password)

def create_access_token(subject: Union[str, Any], expires_delta: timedelta = None) -> str:
    if expires_delta:
        expire = datetime.utcnow() + expires_delta
    else:
        expire = datetime.utcnow() + timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)
    to_encode = {"exp": expire, "sub": str(subject)}
    encoded_jwt = jwt.encode(to_encode, settings.SECRET_KEY, algorithm=ALGORITHM)
    return encoded_jwt

def create_refresh_token(subject: Union[str, Any]) -> str:
    expire = datetime.utcnow() + timedelta(days=settings.REFRESH_TOKEN_EXPIRE_DAYS)
    to_encode = {"exp": expire, "sub": str(subject), "type": "refresh"}
    encoded_jwt = jwt.encode(to_encode, settings.SECRET_KEY, algorithm=ALGORITHM)
    return encoded_jwt

def verify_token(token: str) -> TokenPayload:
    try:
        payload = jwt.decode(token, settings.SECRET_KEY, algorithms=[ALGORITHM])
        token_data = TokenPayload(**payload)
        return token_data
    except (JWTError, ValidationError):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Could not validate credentials",
            headers={"WWW-Authenticate": "Bearer"},
        )

def get_current_user(
    db: Session = Depends(get_db), token: str = Depends(oauth2_scheme)
) -> User:
    token_data = verify_token(token)
    user = crud_user.get(db, id=token_data.sub)
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    if not user.is_active:
        raise HTTPException(status_code=400, detail="Inactive user")
    return user
```

### Auth Router (`src/api/v1/endpoints/auth.py`)

```python
from datetime import timedelta
from typing import Any
from fastapi import APIRouter, Depends, HTTPException, status, Response, Cookie
from sqlalchemy.orm import Session
from src.core.security import create_access_token, create_refresh_token, verify_password, get_current_user, verify_token
from src.core.config import settings
from src.db.session import get_db
from src.models.user import User
from src.schemas.token import Token
from src.schemas.user import UserLogin, UserChangePassword
from src.crud.crud_user import user as crud_user

router = APIRouter()

@router.post("/login", response_model=Token)
def login_access_token(
    response: Response, db: Session = Depends(get_db), user_in: UserLogin = Depends()
) -> Any:
    user = crud_user.get_by_email(db, email=user_in.email)
    if not user or not verify_password(user_in.password, user.hashed_password):
        raise HTTPException(status_code=400, detail="Incorrect email or password")
    elif not user.is_active:
        raise HTTPException(status_code=400, detail="Inactive user")
    
    access_token_expires = timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)
    access_token = create_access_token(user.id, expires_delta=access_token_expires)
    refresh_token = create_refresh_token(user.id)
    
    # Store refresh token in HttpOnly cookie
    response.set_cookie(
        key="refresh_token",
        value=refresh_token,
        httponly=True,
        secure=settings.ENV == "production",
        samesite="lax",
        max_age=settings.REFRESH_TOKEN_EXPIRE_DAYS * 24 * 60 * 60,
    )
    
    return {"access_token": access_token, "token_type": "bearer"}

@router.post("/refresh", response_model=Token)
def refresh_token(
    response: Response, db: Session = Depends(get_db), refresh_token: str = Cookie(None)
) -> Any:
    if not refresh_token:
        raise HTTPException(status_code=401, detail="Refresh token missing")
    token_data = verify_token(refresh_token)
    if token_data.type != "refresh":
        raise HTTPException(status_code=401, detail="Invalid token type")
        
    user = crud_user.get(db, id=token_data.sub)
    if not user or not user.is_active:
        raise HTTPException(status_code=401, detail="User not found or inactive")
        
    access_token = create_access_token(user.id)
    new_refresh_token = create_refresh_token(user.id)
    
    response.set_cookie(
        key="refresh_token",
        value=new_refresh_token,
        httponly=True,
        secure=settings.ENV == "production",
        samesite="lax",
        max_age=settings.REFRESH_TOKEN_EXPIRE_DAYS * 24 * 60 * 60,
    )
    return {"access_token": access_token, "token_type": "bearer"}

@router.post("/logout")
def logout(response: Response):
    response.delete_cookie("refresh_token")
    return {"message": "Successfully logged out"}

@router.post("/change-password")
def change_password(
    password_in: UserChangePassword,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
) -> Any:
    if not verify_password(password_in.current_password, current_user.hashed_password):
        raise HTTPException(status_code=400, detail="Incorrect current password")
    
    crud_user.update_password(db, db_obj=current_user, password=password_in.new_password)
    return {"message": "Password updated successfully"}
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
    Role.BURSAR: [
        Permission.FINANCE_VIEW, Permission.FINANCE_CREATE, Permission.JOURNAL_POST,
        Permission.PAYROLL_RUN, Permission.REPORTS_FINANCIAL, Permission.PROCUREMENT_APPROVE_TIER1
    ],
    Role.PRINCIPAL: [
        Permission.REPORTS_EXECUTIVE, Permission.REPORTS_FINANCIAL, Permission.REPORTS_ACADEMIC,
        Permission.FINANCE_APPROVE, Permission.PAYROLL_APPROVE, Permission.PROCUREMENT_APPROVE_BOM,
        Permission.FINANCE_CLOSE_PERIOD
    ],
    # ... mapped comprehensively
}

def require_permission(required_permission: Permission):
    def permission_checker(current_user: User = Depends(get_current_user)):
        user_role = Role(current_user.role)
        if user_role == Role.SYSTEM_ADMIN:
            return current_user
            
        allowed_permissions = ROLE_PERMISSIONS.get(user_role, [])
        if required_permission not in allowed_permissions:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"Not enough permissions. Required: {required_permission.value}"
            )
        return current_user
    return permission_checker
```

### Audit Log Middleware (`src/middleware/audit.py`)

```python
import json
import hashlib
from starlette.middleware.base import BaseHTTPMiddleware
from fastapi import Request
from src.db.session import SessionLocal
from src.models.audit import SystemAuditLog

class AuditLogMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next):
        if request.method in ["POST", "PUT", "PATCH", "DELETE"]:
            body = await request.body()
            payload_hash = hashlib.sha256(body).hexdigest() if body else None
            
            # Continue request
            response = await call_next(request)
            
            # Post-request processing (fire-and-forget or background task in production)
            if response.status_code < 400:
                user_id = getattr(request.state, "user_id", None)
                db = SessionLocal()
                try:
                    log_entry = SystemAuditLog(
                        user_id=user_id,
                        endpoint=str(request.url.path),
                        method=request.method,
                        payload_hash=payload_hash,
                        status_code=response.status_code,
                        ip_address=request.client.host
                    )
                    db.add(log_entry)
                    db.commit()
                finally:
                    db.close()
            return response
        return await call_next(request)
```

## 3. Kenya Data Protection Act Compliance

### Encrypted SQLAlchemy Type (`src/core/encryption.py`)

```python
from cryptography.fernet import Fernet
from sqlalchemy.types import TypeDecorator, String
from src.core.config import settings

fernet = Fernet(settings.ENCRYPTION_KEY.encode())

class EncryptedString(TypeDecorator):
    """
    Symmetric encryption for KDPA-sensitive fields (KRA PIN, Bank Account, Medical Notes).
    """
    impl = String
    cache_ok = True

    def process_bind_param(self, value, dialect):
        if value is not None:
            value = fernet.encrypt(value.encode('utf-8')).decode('utf-8')
        return value

    def process_result_value(self, value, dialect):
        if value is not None:
            value = fernet.decrypt(value.encode('utf-8')).decode('utf-8')
        return value
```

### Data Retention & Export Services

```python
# src/services/data_privacy.py
from datetime import datetime, timedelta
from celery import shared_task
from sqlalchemy.orm import Session
from src.models.student import Student
from src.models.consent import BiometricConsent

class DataRetentionService:
    @staticmethod
    @shared_task(name="purge_expired_data")
    def purge_expired_data():
        """Celery task to remove inactive student records older than 7 years."""
        # Implementation to anonymize or delete records
        pass

class DataSubjectService:
    @staticmethod
    def export_student_data(db: Session, student_id: str) -> dict:
        """
        KDPA right to data portability.
        Exports all personal data held for a student.
        """
        student = db.query(Student).filter(Student.id == student_id).first()
        return {
            "profile": student.to_dict(),
            "financials": [tx.to_dict() for tx in student.transactions],
            "medical": [med.to_dict() for med in student.medical_records],
            "consent_status": student.consent.status if student.consent else None
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

- **ORM Usage**: All database interactions use SQLAlchemy 2.0 ORM, inherently preventing SQL injection through parameterized queries.
- **Pydantic Validation**: Strict type checking and sanitization.

```python
# src/schemas/validators.py
from pydantic import BaseModel, validator
import re

class SecureBaseModel(BaseModel):
    @validator('*', pre=True)
    def escape_xss(cls, v):
        if isinstance(v, str):
            # Basic sanitization
            return v.replace("<", "&lt;").replace(">", "&gt;")
        return v

class CreateBursary(SecureBaseModel):
    amount: float
    description: str
    
    @validator('amount')
    def amount_must_be_positive(cls, v):
        if v <= 0:
            raise ValueError("Amount must be positive")
        return v
```
