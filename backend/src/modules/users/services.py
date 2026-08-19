"""
User service: business logic for user management, authentication, and authorization.
"""
from datetime import datetime, timedelta, timezone
from typing import List, Optional
from uuid import UUID

from sqlalchemy.ext.asyncio import AsyncSession

from src.core.config import settings
from src.core.security import hash_password, verify_password
from src.modules.users.models import User, Role
from src.modules.users.repository import UserRepository, RoleRepository, PermissionRepository
from src.modules.users.schemas import UserCreate, UserUpdate, UserChangePassword, UserSchema
from src.shared.exceptions import (
    NotFoundError,
    ValidationError,
    DuplicateEntryError,
    UnauthorizedError,
)


class UserService:
    """Business logic for user management."""

    def __init__(self, db: AsyncSession):
        self.db = db
        self.user_repo = UserRepository(db)
        self.role_repo = RoleRepository(db)

    async def create_user(self, school_id: UUID, user_in: UserCreate) -> UserSchema:
        """
        Create new user with password hashing and role assignment.
        Validates password policy and ensures email/username uniqueness.
        """
        # Password policy validation
        self._validate_password(user_in.password)

        # Check email uniqueness
        if await self.user_repo.exists_email(user_in.email):
            raise DuplicateEntryError(f"Email '{user_in.email}' already exists")

        # Check username uniqueness within school
        if await self.user_repo.exists_username(school_id, user_in.username):
            raise DuplicateEntryError(f"Username '{user_in.username}' already exists in school")

        # Fetch roles if specified
        roles: List[Role] = []
        if user_in.role_ids:
            for role_id in user_in.role_ids:
                role = await self.role_repo.get_by_id(role_id)
                if not role or role.school_id != school_id:
                    raise NotFoundError(f"Role {role_id} not found in school")
                roles.append(role)

        # Create user
        user = await self.user_repo.create(
            {
                "school_id": school_id,
                "username": user_in.username,
                "email": user_in.email,
                "phone_number": user_in.phone_number,
                "password_hash": hash_password(user_in.password),
                "user_type": user_in.user_type,
                "is_active": True,
                "roles": roles,
            }
        )
        await self.db.commit()

        # Reload with relations
        user = await self.user_repo.get_by_id(user.id)
        return UserSchema.model_validate(user)

    async def update_user(self, user_id: UUID, user_in: UserUpdate) -> UserSchema:
        """Update user (partial update, only non-null fields)."""
        user = await self.user_repo.get_by_id(user_id)
        if not user:
            raise NotFoundError(f"User {user_id} not found")

        update_data = {}
        if user_in.username is not None:
            update_data["username"] = user_in.username
        if user_in.email is not None:
            update_data["email"] = user_in.email
        if user_in.phone_number is not None:
            update_data["phone_number"] = user_in.phone_number
        if user_in.is_active is not None:
            update_data["is_active"] = user_in.is_active

        if update_data:
            await self.user_repo.update(user_id, update_data)

        # Update roles if specified
        if user_in.role_ids is not None:
            roles = []
            for role_id in user_in.role_ids:
                role = await self.role_repo.get_by_id(role_id)
                if not role:
                    raise NotFoundError(f"Role {role_id} not found")
                roles.append(role)
            user.roles = roles

        await self.db.commit()

        # Reload with relations
        user = await self.user_repo.get_by_id(user_id)
        return UserSchema.model_validate(user)

    async def change_password(self, user_id: UUID, req: UserChangePassword) -> None:
        """Change user password with validation."""
        user = await self.user_repo.get_by_id(user_id)
        if not user:
            raise NotFoundError(f"User {user_id} not found")

        # Verify old password
        if not verify_password(req.old_password, user.password_hash):
            raise UnauthorizedError("Incorrect current password")

        # Validate new password
        if req.new_password != req.confirm_password:
            raise ValidationError("New passwords do not match")
        self._validate_password(req.new_password)

        # Update password
        await self.user_repo.update(
            user_id,
            {"password_hash": hash_password(req.new_password)},
        )
        await self.db.commit()

    async def get_user(self, user_id: UUID) -> UserSchema:
        """Fetch user by ID."""
        user = await self.user_repo.get_by_id(user_id)
        if not user:
            raise NotFoundError(f"User {user_id} not found")
        return UserSchema.model_validate(user)

    async def get_users_by_school(
        self, school_id: UUID, skip: int = 0, limit: int = 100
    ) -> tuple[List[UserSchema], int]:
        """Fetch paginated users in a school."""
        users, total = await self.user_repo.get_by_school(school_id, skip, limit)
        return [UserSchema.model_validate(u) for u in users], total

    async def deactivate_user(self, user_id: UUID) -> None:
        """Deactivate user (soft-delete or is_active=False)."""
        user = await self.user_repo.get_by_id(user_id)
        if not user:
            raise NotFoundError(f"User {user_id} not found")
        await self.user_repo.update(user_id, {"is_active": False})
        await self.db.commit()

    async def record_login(self, user_id: UUID) -> None:
        """Update last_login timestamp."""
        await self.user_repo.update(
            user_id,
            {"last_login": datetime.now(timezone.utc)},
        )
        await self.db.commit()

    def _validate_password(self, password: str) -> None:
        """
        Validate password meets policy requirements:
        - Minimum length (PASSWORD_MIN_LENGTH)
        - At least 3 of 4 character classes (upper, lower, digit, symbol)
        """
        if len(password) < settings.PASSWORD_MIN_LENGTH:
            raise ValidationError(
                f"Password must be at least {settings.PASSWORD_MIN_LENGTH} characters"
            )

        # Check character class diversity
        has_upper = any(c.isupper() for c in password)
        has_lower = any(c.islower() for c in password)
        has_digit = any(c.isdigit() for c in password)
        has_symbol = any(not c.isalnum() for c in password)

        classes_met = sum([has_upper, has_lower, has_digit, has_symbol])
        if classes_met < 3:
            raise ValidationError(
                "Password must contain at least 3 of: uppercase, lowercase, digit, symbol"
            )
