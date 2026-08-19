"""
User repository: database access layer for user queries and operations.
"""
from typing import Optional
from uuid import UUID

from sqlalchemy import select, and_
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from src.modules.users.models import User, Role, Permission
from src.shared.base_repository import BaseRepository


class UserRepository(BaseRepository[User]):
    """Repository for User data access."""

    def __init__(self, db: AsyncSession):
        super().__init__(User, db)

    async def get_by_id(self, id: UUID) -> Optional[User]:
        """Fetch user by ID with roles and permissions eagerly loaded."""
        query = (
            select(self.model)
            .where(
                and_(
                    self.model.id == id,
                    self.model.is_deleted == False,
                )
            )
            .options(
                selectinload(User.roles).selectinload(Role.permissions)
            )
        )
        result = await self.db.execute(query)
        return result.unique().scalar_one_or_none()

    async def get_by_email(self, email: str) -> Optional[User]:
        """Fetch user by email with roles eagerly loaded."""
        query = (
            select(self.model)
            .where(
                and_(
                    self.model.email == email,
                    self.model.is_deleted == False,
                )
            )
            .options(
                selectinload(User.roles).selectinload(Role.permissions)
            )
        )
        result = await self.db.execute(query)
        return result.unique().scalar_one_or_none()

    async def get_by_username(self, school_id: UUID, username: str) -> Optional[User]:
        """Fetch user by username within a specific school."""
        query = (
            select(self.model)
            .where(
                and_(
                    self.model.school_id == school_id,
                    self.model.username == username,
                    self.model.is_deleted == False,
                )
            )
            .options(
                selectinload(User.roles).selectinload(Role.permissions)
            )
        )
        result = await self.db.execute(query)
        return result.unique().scalar_one_or_none()

    async def get_by_school(self, school_id: UUID, skip: int = 0, limit: int = 100) -> tuple[list[User], int]:
        """Fetch all users in a school with pagination."""
        from sqlalchemy import func

        # Count total
        count_query = select(func.count(User.id)).where(
            and_(
                User.school_id == school_id,
                User.is_deleted == False,
            )
        )
        count_result = await self.db.execute(count_query)
        total = count_result.scalar() or 0

        # Fetch paginated
        query = (
            select(User)
            .where(
                and_(
                    User.school_id == school_id,
                    User.is_deleted == False,
                )
            )
            .options(
                selectinload(User.roles).selectinload(Role.permissions)
            )
            .offset(skip)
            .limit(limit)
        )
        result = await self.db.execute(query)
        users = result.unique().scalars().all()
        return users, total

    async def exists_email(self, email: str) -> bool:
        """Check if email already exists."""
        query = select(self.model).where(
            and_(
                self.model.email == email,
                self.model.is_deleted == False,
            )
        )
        result = await self.db.execute(query)
        return result.scalar_one_or_none() is not None

    async def exists_username(self, school_id: UUID, username: str) -> bool:
        """Check if username exists in school."""
        query = select(self.model).where(
            and_(
                self.model.school_id == school_id,
                self.model.username == username,
                self.model.is_deleted == False,
            )
        )
        result = await self.db.execute(query)
        return result.scalar_one_or_none() is not None


class RoleRepository(BaseRepository[Role]):
    """Repository for Role data access."""

    def __init__(self, db: AsyncSession):
        super().__init__(Role, db)

    async def get_by_id(self, id: UUID) -> Optional[Role]:
        """Fetch role by ID with permissions eagerly loaded."""
        query = (
            select(self.model)
            .where(
                and_(
                    self.model.id == id,
                    self.model.is_deleted == False,
                )
            )
            .options(selectinload(Role.permissions))
        )
        result = await self.db.execute(query)
        return result.scalar_one_or_none()

    async def get_by_name(self, school_id: UUID, name: str) -> Optional[Role]:
        """Fetch role by name within a school."""
        query = (
            select(self.model)
            .where(
                and_(
                    self.model.school_id == school_id,
                    self.model.name == name,
                    self.model.is_deleted == False,
                )
            )
            .options(selectinload(Role.permissions))
        )
        result = await self.db.execute(query)
        return result.scalar_one_or_none()

    async def get_by_school(self, school_id: UUID) -> list[Role]:
        """Fetch all roles in a school."""
        query = (
            select(self.model)
            .where(
                and_(
                    self.model.school_id == school_id,
                    self.model.is_deleted == False,
                )
            )
            .options(selectinload(Role.permissions))
        )
        result = await self.db.execute(query)
        return result.scalars().all()


class PermissionRepository(BaseRepository[Permission]):
    """Repository for Permission data access."""

    def __init__(self, db: AsyncSession):
        super().__init__(Permission, db)

    async def get_by_name(self, name: str) -> Optional[Permission]:
        """Fetch permission by name."""
        query = select(self.model).where(
            and_(
                self.model.name == name,
                self.model.is_deleted == False,
            )
        )
        result = await self.db.execute(query)
        return result.scalar_one_or_none()

    async def get_all_by_module(self, module: str) -> list[Permission]:
        """Fetch all permissions in a module."""
        query = select(self.model).where(
            and_(
                self.model.module == module,
                self.model.is_deleted == False,
            )
        )
        result = await self.db.execute(query)
        return result.scalars().all()
