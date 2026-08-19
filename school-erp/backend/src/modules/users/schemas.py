"""
Pydantic schemas for User request/response validation.
"""
from typing import List, Optional
from uuid import UUID

from pydantic import BaseModel, EmailStr, Field


class PermissionSchema(BaseModel):
    """Permission response schema."""

    id: UUID
    name: str
    module: str
    description: Optional[str] = None

    class Config:
        from_attributes = True


class RoleSchema(BaseModel):
    """Role response schema."""

    id: UUID
    name: str
    description: Optional[str] = None
    is_system_role: bool
    permissions: List[PermissionSchema] = []

    class Config:
        from_attributes = True


class UserLogin(BaseModel):
    """Login request schema."""

    email: EmailStr
    password: str = Field(..., min_length=1)


class UserCreate(BaseModel):
    """User creation schema."""

    username: str = Field(..., min_length=3, max_length=100)
    email: EmailStr
    phone_number: Optional[str] = None
    password: str = Field(..., min_length=12)
    user_type: str = Field(..., description="SUPERADMIN, ADMIN, STAFF, TEACHER, PARENT, STUDENT")
    role_ids: Optional[List[UUID]] = None


class UserUpdate(BaseModel):
    """User update schema (partial)."""

    username: Optional[str] = None
    email: Optional[EmailStr] = None
    phone_number: Optional[str] = None
    is_active: Optional[bool] = None
    role_ids: Optional[List[UUID]] = None


class UserChangePassword(BaseModel):
    """Change password request schema."""

    old_password: str
    new_password: str = Field(..., min_length=12)
    confirm_password: str


class UserSchema(BaseModel):
    """User response schema."""

    id: UUID
    school_id: UUID
    username: str
    email: Optional[str]
    phone_number: Optional[str]
    user_type: str
    is_active: bool
    last_login: Optional[str] = None
    roles: List[RoleSchema] = []
    scopes: List[str] = []
    created_at: str
    updated_at: str

    class Config:
        from_attributes = True


class Token(BaseModel):
    """Token response schema."""

    access_token: str
    token_type: str = "bearer"
    expires_in: Optional[int] = None
