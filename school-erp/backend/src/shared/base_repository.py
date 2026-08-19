"""
Generic CRUD repository base class for reusable data access patterns.
"""
from typing import Any, Generic, Optional, Type, TypeVar

from sqlalchemy import select, update
from sqlalchemy.ext.asyncio import AsyncSession

from src.shared.base_model import AuditableBase

ModelType = TypeVar("ModelType", bound=AuditableBase)


class BaseRepository(Generic[ModelType]):
    """
    Generic async repository for CRUD operations on AuditableBase models.
    Soft-deletes by default (filters is_deleted=False).
    """

    def __init__(self, model: Type[ModelType], db: AsyncSession):
        self.model = model
        self.db = db

    async def get_by_id(self, id: Any) -> Optional[ModelType]:
        """Fetch single record by ID, excluding soft-deleted records."""
        query = select(self.model).where(
            self.model.id == id,
            self.model.is_deleted == False,
        )
        result = await self.db.execute(query)
        return result.scalar_one_or_none()

    async def get_all(self, skip: int = 0, limit: int = 100) -> list[ModelType]:
        """Fetch multiple records with offset/limit, excluding soft-deleted."""
        query = (
            select(self.model)
            .where(self.model.is_deleted == False)
            .offset(skip)
            .limit(limit)
        )
        result = await self.db.execute(query)
        return result.scalars().all()

    async def get_all_with_count(self, skip: int = 0, limit: int = 100) -> tuple[list[ModelType], int]:
        """Fetch records with total count."""
        from sqlalchemy import func

        # Get total count
        count_query = select(func.count(self.model.id)).where(self.model.is_deleted == False)
        count_result = await self.db.execute(count_query)
        total = count_result.scalar()

        # Get paginated records
        records = await self.get_all(skip, limit)
        return records, total

    async def create(self, obj_in: dict[str, Any]) -> ModelType:
        """Create and flush new record."""
        db_obj = self.model(**obj_in)
        self.db.add(db_obj)
        await self.db.flush()
        return db_obj

    async def update(self, id: Any, obj_in: dict[str, Any]) -> Optional[ModelType]:
        """Update record by ID and return updated object."""
        query = (
            update(self.model)
            .where(self.model.id == id)
            .values(**obj_in, updated_at=select(func.now()))
            .returning(self.model)
        )
        result = await self.db.execute(query)
        return result.scalar_one_or_none()

    async def soft_delete(self, id: Any) -> bool:
        """Soft-delete record by ID."""
        from sqlalchemy import func

        query = (
            update(self.model)
            .where(self.model.id == id)
            .values(is_deleted=True, updated_at=select(func.now()))
        )
        result = await self.db.execute(query)
        return result.rowcount > 0

    async def hard_delete(self, id: Any) -> bool:
        """Permanently delete record (use with caution)."""
        query = self.model.__table__.delete().where(self.model.id == id)
        result = await self.db.execute(query)
        return result.rowcount > 0
