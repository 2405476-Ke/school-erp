"""Gate security services."""

from .gate_service import (
    GateService,
    ForbiddenExitError,
)

__all__ = [
    "GateService",
    "ForbiddenExitError",
]
