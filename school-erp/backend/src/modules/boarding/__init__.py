"""Boarding module initialization."""

from src.modules.boarding.models.boarding import (
    Hostel,
    Dormitory,
    Bed,
    BedAllocation,
    StudentLeavePass,
    DisciplinaryIncident,
    DisciplinaryAction,
    ExeatType,
    LeavePassStatus,
    DisciplinaryCategory,
    DisciplinaryActionType,
)
from src.modules.boarding.services.bed_allocation_service import BedAllocationService
from src.modules.boarding.services.exeat_service import ExeatService
from src.modules.boarding.services.discipline_service import DisciplinaryService

__all__ = [
    # Models
    "Hostel",
    "Dormitory",
    "Bed",
    "BedAllocation",
    "StudentLeavePass",
    "DisciplinaryIncident",
    "DisciplinaryAction",
    "ExeatType",
    "LeavePassStatus",
    "DisciplinaryCategory",
    "DisciplinaryActionType",
    # Services
    "BedAllocationService",
    "ExeatService",
    "DisciplinaryService",
]
