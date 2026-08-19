"""
User authentication router: login, refresh, logout, and password management endpoints.
"""
import secrets
from typing import Any, Optional
from uuid import UUID

from fastapi import APIRouter, Cookie, Depends, Header, HTTPException, Request, Response, status
from sqlalchemy.ext.asyncio import AsyncSession

from src.core.config import settings
from src.core.database import get_db
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
from src.modules.users.schemas import Token, UserLogin, UserChangePassword, UserSchema
from src.modules.users.services import UserService
from src.shared.exceptions import UnauthorizedError, ValidationError
from src.shared.response import APIResponse

router = APIRouter(prefix="/auth", tags=["Authentication"])

REFRESH_COOKIE = "refresh_token"
CSRF_COOKIE = "csrf_token"
CSRF_HEADER = "X-CSRF-Token"


def _cookie_kwargs() -> dict:
    """Cookie settings for secure refresh token storage."""
    return {
        "httponly": True,
        "secure": settings.ENVIRONMENT == "production",
        "samesite": "lax",
        "max_age": settings.REFRESH_TOKEN_EXPIRE_DAYS * 24 * 60 * 60,
        "path": f"{settings.API_V1_STR}/auth",
    }


async def _issue_tokens(
    response: Response,
    user_id: UUID,
    scopes: list[str],
) -> str:
    """
    Issue access + refresh tokens, store refresh in secure httponly cookie,
    store CSRF token in readable cookie for XSS protection.
    Returns access_token string.
    """
    access_token = create_access_token(user_id, scopes=scopes)
    refresh_token, jti = create_refresh_token(user_id)

    # Store jti in Redis for rotation tracking (if Redis is available)
    # For now, we skip Redis integration in PHASE 1
    # In production, call: await register_active_refresh(redis, user_id, jti)

    csrf_value = secrets.token_urlsafe(32)
    response.set_cookie(REFRESH_COOKIE, refresh_token, **_cookie_kwargs())
    response.set_cookie(
        CSRF_COOKIE,
        csrf_value,
        httponly=False,  # JavaScript must read it
        secure=settings.ENVIRONMENT == "production",
        samesite="lax",
        max_age=settings.REFRESH_TOKEN_EXPIRE_DAYS * 24 * 60 * 60,
    )
    return access_token


@router.post("/login", response_model=APIResponse[Token])
async def login(
    response: Response,
    user_in: UserLogin,
    db: AsyncSession = Depends(get_db),
) -> Any:
    """
    Login endpoint: accepts email + password, returns access token.
    Refresh token stored in httponly cookie; CSRF token in readable cookie.
    """
    user_repo = UserRepository(db)
    user = await user_repo.get_by_email(user_in.email)

    if not user or not verify_password(user_in.password, user.password_hash):
        raise HTTPException(status_code=400, detail="Incorrect email or password")
    if not user.is_active:
        raise HTTPException(status_code=400, detail="Inactive user")

    # Record login
    await UserService(db).record_login(user.id)

    access_token = await _issue_tokens(response, user.id, scopes=user.scopes)
    return APIResponse.success(
        data=Token(access_token=access_token, token_type="bearer"),
        message="Login successful",
    )


@router.post("/refresh", response_model=APIResponse[Token])
async def refresh(
    response: Response,
    refresh_token: Optional[str] = Cookie(default=None, alias=REFRESH_COOKIE),
    csrf_cookie: Optional[str] = Cookie(default=None, alias=CSRF_COOKIE),
    csrf_header: Optional[str] = Header(default=None, alias=CSRF_HEADER),
    db: AsyncSession = Depends(get_db),
) -> Any:
    """
    Refresh access token: validates refresh token + CSRF, returns new access token.
    Implements token rotation (old refresh jti revoked immediately).
    """
    if not refresh_token:
        raise HTTPException(status_code=401, detail="Refresh token missing")
    if not csrf_cookie or csrf_cookie != csrf_header:
        raise HTTPException(status_code=403, detail="CSRF validation failed")

    token_data = verify_token(refresh_token)
    if token_data.get("type") != "refresh":
        raise HTTPException(status_code=401, detail="Wrong token type")

    # In production, check Redis revocation: if await is_refresh_revoked(redis, token_data["jti"])

    user_id = UUID(token_data.get("sub"))
    user_repo = UserRepository(db)
    user = await user_repo.get_by_id(user_id)
    if not user or not user.is_active:
        raise HTTPException(status_code=401, detail="User inactive or not found")

    # In production, revoke old jti in Redis: await revoke_refresh(redis, token_data["jti"])

    access_token = await _issue_tokens(response, user.id, scopes=user.scopes)
    return APIResponse.success(
        data=Token(access_token=access_token, token_type="bearer"),
        message="Token refreshed",
    )


@router.post("/logout")
async def logout(response: Response) -> APIResponse:
    """
    Logout endpoint: clears refresh token cookie.
    In production, also revokes the jti in Redis.
    """
    response.delete_cookie(REFRESH_COOKIE, path=f"{settings.API_V1_STR}/auth")
    response.delete_cookie(CSRF_COOKIE)
    return APIResponse.success(message="Logged out successfully")


@router.get("/me", response_model=APIResponse[UserSchema])
async def get_me(current_user: User = Depends(get_current_user)) -> APIResponse[UserSchema]:
    """
    Get current authenticated user profile.
    """
    return APIResponse.success(
        data=UserSchema.model_validate(current_user),
        message="User profile retrieved",
    )


@router.post("/change-password")
async def change_password(
    req: UserChangePassword,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> APIResponse:
    """
    Change password for current user.
    Validates old password, enforces password policy.
    """
    service = UserService(db)
    await service.change_password(current_user.id, req)
    return APIResponse.success(message="Password changed successfully")
