"""Security & Gate Management Module.

Handles:
- Visitor management and blacklist control
- Student exit/entry verification against Boarding module leave passes
- Security incident tracking and alerts
- Gate audit trail and reporting
"""

from .models import (
    Visitor,
    VisitorLog,
    StudentGateEvent,
    GateSuspicion,
    VisitorType,
    StudentEventType,
    VisitorStatus,
)
from .schemas import (
    CreateVisitorRequest,
    StudentExitClearanceResponse,
    StudentUnauthorizedExitAlert,
)
from .services import (
    GateService,
    ForbiddenExitError,
)
from .routers import gate_router

__all__ = [
    # Models
    "Visitor",
    "VisitorLog",
    "StudentGateEvent",
    "GateSuspicion",
    "VisitorType",
    "StudentEventType",
    "VisitorStatus",
    # Services
    "GateService",
    "ForbiddenExitError",
    # Routers
    "gate_router",
]
