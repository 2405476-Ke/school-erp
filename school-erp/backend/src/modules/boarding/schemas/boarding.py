"""
Pydantic v2 schemas for Boarding and Discipline System.

Schemas for:
- Hostel CRUD operations
- Dormitory CRUD operations
- Bed allocation and management
- Leave pass requests and approvals
- Disciplinary incident and action tracking
"""

from datetime import datetime, date
from decimal import Decimal
from uuid import UUID

from pydantic import BaseModel, Field, field_validator


# ============================================================================
# HOSTEL SCHEMAS
# ============================================================================


class DormitoryCreate(BaseModel):
    """Create dormitory request."""
    name: str = Field(..., min_length=1, max_length=100, description="Wing/unit name")
    capacity: int = Field(..., gt=0, description="Number of beds")


class DormitoryResponse(BaseModel):
    """Dormitory response model."""
    id: UUID
    name: str
    capacity: int
    current_occupancy: int
    is_active: bool
    created_at: datetime


class HostelCreate(BaseModel):
    """Create hostel request."""
    name: str = Field(..., min_length=1, max_length=100, description="Hostel name")
    code: str = Field(..., min_length=1, max_length=10, description="Hostel code")
    capacity: int = Field(..., gt=0, description="Total bed capacity")
    description: str | None = Field(None, max_length=500)
    matron_staff_id: UUID | None = None


class HostelResponse(BaseModel):
    """Hostel response model."""
    id: UUID
    name: str
    code: str
    capacity: int
    current_occupancy: int
    description: str | None
    is_active: bool
    created_at: datetime


class HostelDetailResponse(BaseModel):
    """Hostel detail with dormitories."""
    id: UUID
    name: str
    code: str
    capacity: int
    current_occupancy: int
    description: str | None
    is_active: bool
    dormitories: list[DormitoryResponse] = []
    occupancy_rate: float = Field(description="Percentage of beds occupied")
    created_at: datetime


# ============================================================================
# BED SCHEMAS
# ============================================================================


class BedCreate(BaseModel):
    """Create bed request."""
    dormitory_id: UUID
    bed_number: str = Field(..., min_length=1, max_length=20, description="Bed identifier (e.g., A-01)")


class BedResponse(BaseModel):
    """Bed response model."""
    id: UUID
    dormitory_id: UUID
    bed_number: str
    is_occupied: bool
    is_active: bool
    created_at: datetime


class BedDetailResponse(BaseModel):
    """Bed detail with current allocation."""
    id: UUID
    dormitory_id: UUID
    bed_number: str
    is_occupied: bool
    is_active: bool
    current_occupant_name: str | None = Field(None, description="Current student name if occupied")
    current_occupant_id: UUID | None = Field(None, description="Current student ID if occupied")
    allocation_start_date: date | None = None
    created_at: datetime


# ============================================================================
# BED ALLOCATION SCHEMAS
# ============================================================================


class BedAllocationRequest(BaseModel):
    """Request to allocate bed to student."""
    student_id: UUID
    bed_id: UUID
    start_date: date = Field(..., description="Allocation start date")
    end_date: date | None = Field(None, description="Allocation end date (null if ongoing)")
    
    @field_validator("end_date")
    @classmethod
    def validate_dates(cls, v: date | None, info) -> date | None:
        """Ensure end_date >= start_date if provided."""
        if v is not None and "start_date" in info.data:
            if v < info.data["start_date"]:
                raise ValueError("end_date must be >= start_date")
        return v


class BedAllocationResponse(BaseModel):
    """Bed allocation response."""
    id: UUID
    student_id: UUID
    student_name: str
    bed_id: UUID
    bed_number: str
    dormitory_name: str
    hostel_name: str
    start_date: date
    end_date: date | None
    is_active: bool
    created_at: datetime


class BedAllocationDetail(BaseModel):
    """Detailed bed allocation."""
    id: UUID
    student_id: UUID
    student_name: str
    student_admission_number: str
    bed_id: UUID
    bed_number: str
    dormitory_id: UUID
    dormitory_name: str
    hostel_id: UUID
    hostel_name: str
    start_date: date
    end_date: date | None
    is_active: bool
    duration_days: int = Field(description="Number of days allocated")
    created_at: datetime


class AllocateBedResponse(BaseModel):
    """Response from allocate bed operation."""
    success: bool
    allocation_id: UUID
    student_name: str
    bed_number: str
    bed_location: str = Field(description="Hostel - Dormitory - Bed format")
    start_date: date
    message: str


# ============================================================================
# LEAVE PASS SCHEMAS
# ============================================================================


class RequestLeavePassRequest(BaseModel):
    """Request to leave school (exeat pass)."""
    student_id: UUID
    exeat_type: str = Field(..., description="DAY_OUT/OVERNIGHT/WEEKEND/HOLIDAY/MEDICAL/BEREAVEMENT/SPECIAL")
    reason: str = Field(..., min_length=10, description="Detailed reason for leave")
    expected_return_time: datetime = Field(..., description="When student will return")
    destination: str | None = Field(None, max_length=255, description="Where student is going")
    contact_person_name: str | None = Field(None, max_length=100, description="Emergency contact name")
    contact_person_phone: str | None = Field(None, max_length=20, description="Emergency contact phone")


class LeavePassResponse(BaseModel):
    """Leave pass response."""
    id: UUID
    student_id: UUID
    student_name: str
    student_admission_number: str
    exeat_type: str
    reason: str
    status: str
    requested_date: datetime
    expected_return_time: datetime | None
    approved_by: str | None = Field(None, description="Name of approver")
    approved_date: datetime | None
    destination: str | None
    contact_person_name: str | None
    contact_person_phone: str | None


class ApproveLeavePassRequest(BaseModel):
    """Request to approve leave pass."""
    leave_pass_id: UUID
    approved: bool = Field(..., description="True to approve, False to reject")
    approval_reason: str | None = Field(None, description="Reason for approval/rejection")


class ApproveLeavePassResponse(BaseModel):
    """Response from approve leave pass."""
    leave_pass_id: UUID
    student_name: str
    status: str
    approved_date: datetime
    message: str


class RecordDepartureRequest(BaseModel):
    """Record student departure from school."""
    leave_pass_id: UUID
    departure_time: datetime = Field(..., description="Time of departure")


class RecordDepartureResponse(BaseModel):
    """Response from record departure."""
    leave_pass_id: UUID
    student_name: str
    status: str
    departure_time: datetime
    expected_return_time: datetime
    message: str


class RecordReturnRequest(BaseModel):
    """Record student return to school."""
    leave_pass_id: UUID
    actual_return_time: datetime = Field(..., description="Time of return")


class RecordReturnResponse(BaseModel):
    """Response from record return."""
    leave_pass_id: UUID
    student_name: str
    status: str
    actual_return_time: datetime
    days_away: int
    message: str


class VerifyGateExitRequest(BaseModel):
    """Request to verify student can exit (called by Gate/Security)."""
    student_id: UUID
    current_time: datetime = Field(..., description="Current date/time at gate")


class VerifyGateExitResponse(BaseModel):
    """Response for gate exit verification."""
    allowed: bool
    student_name: str
    leave_pass_id: UUID | None
    exeat_type: str | None
    expected_return_time: datetime | None
    destination: str | None
    message: str


class LeavePassListResponse(BaseModel):
    """List of leave passes with statistics."""
    total_requests: int
    approved_count: int
    pending_count: int
    rejected_count: int
    currently_away: int
    passes: list[LeavePassResponse]


# ============================================================================
# DISCIPLINARY SCHEMAS
# ============================================================================


class ReportDisciplinaryIncidentRequest(BaseModel):
    """Report disciplinary incident."""
    student_id: UUID
    category: str = Field(..., description="ACADEMIC/CONDUCT/CURFEW/SUBSTANCE/SAFETY/PROPERTY/UNIFORM/OTHER")
    description: str = Field(..., min_length=20, description="Detailed description")
    incident_date: date = Field(..., description="When incident occurred")
    location: str | None = Field(None, max_length=255, description="Where incident occurred")
    witnesses: str | None = Field(None, description="Names of witnesses")
    severity: int = Field(..., ge=1, le=5, description="1-5, 1=minor, 5=critical")


class DisciplinaryIncidentResponse(BaseModel):
    """Disciplinary incident response."""
    id: UUID
    student_id: UUID
    student_name: str
    student_admission_number: str
    category: str
    description: str
    incident_date: date
    reported_date: datetime
    location: str | None
    severity: int
    reported_by: str | None = Field(None, description="Staff name who reported")
    actions_count: int = Field(description="Number of actions taken")


class DisciplinaryIncidentDetailResponse(BaseModel):
    """Disciplinary incident with actions."""
    id: UUID
    student_id: UUID
    student_name: str
    student_admission_number: str
    category: str
    description: str
    incident_date: date
    reported_date: datetime
    location: str | None
    witnesses: str | None
    severity: int
    reported_by: str | None
    actions: list["DisciplinaryActionResponse"] = []


class IssueDisciplinaryActionRequest(BaseModel):
    """Issue disciplinary action in response to incident."""
    incident_id: UUID
    action_type: str = Field(..., description="WARNING/DETENTION/SUSPENSION/EXPULSION/COMMUNITY_SERVICE/FINE/RESTRICTION/COUNSELING")
    description: str = Field(..., min_length=10, description="Details of action")
    start_date: date = Field(..., description="When action starts")
    end_date: date | None = Field(None, description="When action ends (null if permanent)")
    reason: str = Field(..., min_length=20, description="Justification for action")
    
    @field_validator("end_date")
    @classmethod
    def validate_dates(cls, v: date | None, info) -> date | None:
        """Ensure end_date >= start_date if provided."""
        if v is not None and "start_date" in info.data:
            if v < info.data["start_date"]:
                raise ValueError("end_date must be >= start_date")
        return v


class DisciplinaryActionResponse(BaseModel):
    """Disciplinary action response."""
    id: UUID
    incident_id: UUID
    action_type: str
    description: str
    start_date: date
    end_date: date | None
    issued_date: datetime
    duration_days: int | None = Field(description="Days of action duration")
    issued_by: str | None = Field(None, description="Staff name who issued")
    reason: str


class IssueDisciplinaryActionResponse(BaseModel):
    """Response from issue disciplinary action."""
    action_id: UUID
    incident_id: UUID
    student_name: str
    action_type: str
    start_date: date
    end_date: date | None
    message: str


class StudentDisciplinaryRecordResponse(BaseModel):
    """Complete disciplinary record for student."""
    student_id: UUID
    student_name: str
    student_admission_number: str
    total_incidents: int
    incidents_by_category: dict[str, int]
    active_actions: list[DisciplinaryActionResponse]
    recent_incidents: list[DisciplinaryIncidentResponse]


# Update forward references
DisciplinaryIncidentDetailResponse.model_rebuild()
