"""
Base SQLAlchemy model with UUID primary keys, audit fields, and multi-tenancy support.
"""
from datetime import datetime, timezone
from typing import Annotated, Optional
from uuid import UUID, uuid4

from sqlalchemy import Boolean, DateTime
from sqlalchemy.dialects.postgresql import UUID as PG_UUID
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column


def _utcnow() -> datetime:
    """Return current UTC datetime."""
    return datetime.now(timezone.utc)


# Type alias for UUID primary key columns
GUID = Annotated[UUID, mapped_column(PG_UUID(as_uuid=True), primary_key=True, default=uuid4)]

# Type alias for UUID foreign key columns
FK_UUID = Annotated[UUID, mapped_column(PG_UUID(as_uuid=True))]

# Type alias for school_id (tenant ID)
SCHOOL_ID = Annotated[UUID, mapped_column(PG_UUID(as_uuid=True), nullable=False, index=True)]


class Base(DeclarativeBase):
    """SQLAlchemy declarative base for all models."""

    pass


class AuditableBase(Base):
    """
    Base class for all auditable domain entities.
    Provides UUID primary key, created/updated timestamps, soft delete flag, and creator tracking.
    """

    __abstract__ = True

    id: Mapped[GUID]
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=_utcnow, nullable=False
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=_utcnow, onupdate=_utcnow, nullable=False
    )
    created_by: Mapped[Optional[UUID]] = mapped_column(PG_UUID(as_uuid=True), nullable=True)
    is_deleted: Mapped[bool] = mapped_column(Boolean, default=False, index=True, nullable=False)


class TenantMixin:
    """
    Mixin for tenant-scoped tables.
    Every row belongs to a school (school_id).
    Enforced at the database level via foreign key and index.
    """

    school_id: Mapped[SCHOOL_ID]
