"""
Standardized API response wrapper for consistent JSON structure across all endpoints.
"""
from typing import Any, Generic, Optional, TypeVar

from pydantic import BaseModel

T = TypeVar("T")


class APIResponse(BaseModel, Generic[T]):
    """
    Standardized response wrapper for all API endpoints.
    All responses return {success, message, data, meta}.
    """

    success: bool
    message: str
    data: Optional[T] = None
    meta: Optional[dict[str, Any]] = None

    @classmethod
    def success(
        cls,
        data: Optional[T] = None,
        message: str = "Success",
        meta: Optional[dict[str, Any]] = None,
    ) -> "APIResponse[T]":
        """Construct a success response."""
        return cls(success=True, message=message, data=data, meta=meta)

    @classmethod
    def error(cls, message: str, meta: Optional[dict[str, Any]] = None) -> "APIResponse[None]":
        """Construct an error response."""
        return cls(success=False, message=message, data=None, meta=meta)
