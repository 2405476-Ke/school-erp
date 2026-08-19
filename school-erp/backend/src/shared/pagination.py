"""
Pagination schemas for offset-based and cursor-based pagination.
"""
from typing import Generic, List, Optional, TypeVar

from pydantic import BaseModel

T = TypeVar("T")


class OffsetPagination(BaseModel, Generic[T]):
    """Offset-based pagination response."""

    items: List[T]
    total: int
    page: int
    size: int
    pages: int

    @classmethod
    def create(cls, items: List[T], total: int, page: int, size: int) -> "OffsetPagination[T]":
        """Construct pagination metadata."""
        pages = (total + size - 1) // size  # Ceiling division
        return cls(items=items, total=total, page=page, size=size, pages=pages)


class CursorPagination(BaseModel, Generic[T]):
    """Cursor-based pagination response."""

    items: List[T]
    next_cursor: Optional[str] = None
    has_next: bool = False
