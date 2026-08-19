"""
Custom exception hierarchy for the ERP system.
"""
from fastapi import HTTPException, status


class ERPException(HTTPException):
    """Base ERP exception."""

    def __init__(self, status_code: int, detail: str):
        super().__init__(status_code=status_code, detail=detail)


class NotFoundError(ERPException):
    """404 Not Found."""

    def __init__(self, detail: str = "Resource not found"):
        super().__init__(status.HTTP_404_NOT_FOUND, detail)


class ValidationError(ERPException):
    """400 Bad Request."""

    def __init__(self, detail: str = "Validation failed"):
        super().__init__(status.HTTP_400_BAD_REQUEST, detail)


class DuplicateEntryError(ERPException):
    """409 Conflict."""

    def __init__(self, detail: str = "Entry already exists"):
        super().__init__(status.HTTP_409_CONFLICT, detail)


class UnauthorizedError(ERPException):
    """401 Unauthorized."""

    def __init__(self, detail: str = "Authentication required"):
        super().__init__(status.HTTP_401_UNAUTHORIZED, detail)


class ForbiddenError(ERPException):
    """403 Forbidden."""

    def __init__(self, detail: str = "Permission denied"):
        super().__init__(status.HTTP_403_FORBIDDEN, detail)


class InsufficientFundsError(ERPException):
    """400 Insufficient Funds."""

    def __init__(self, detail: str = "Insufficient funds"):
        super().__init__(status.HTTP_400_BAD_REQUEST, detail)
