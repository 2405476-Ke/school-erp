"""
Pydantic v2 schemas for Admissions and Student Lifecycle.

Schemas for:
- StudentProspect (application management)
- Student (main profile)
- ParentGuardian and StudentParentRelationship
- StudentClearance and StudentTransfer
"""

from decimal import Decimal
from datetime import datetime, date
from uuid import UUID
from typing import Optional

from pydantic import BaseModel, Field, field_validator

from src.modules.admissions.models.students import (
    ProspectStatus,
    Gender,
    BoardingStatus,
    StudentActiveStatus,
    ClearanceStatus,
    RelationshipType,
)


# ============================================================================
# STUDENT PROSPECT SCHEMAS
# ============================================================================


class StudentProspectCreate(BaseModel):
    """Create a new prospect application."""
    first_name: str = Field(..., min_length=1, max_length=100)
    last_name: str = Field(..., min_length=1, max_length=100)
    email: Optional[str] = Field(None, max_length=255)
    phone: Optional[str] = Field(None, max_length=20)
    gender: Gender
    date_of_birth: date
    kcpe_marks: Decimal = Field(..., ge=0, le=500, decimal_places=2)
    kcpe_year: int = Field(..., ge=2000, le=2100)
    kpsea_marks: Optional[Decimal] = Field(None, ge=0, le=500, decimal_places=2)
    kpsea_year: Optional[int] = Field(None, ge=2000, le=2100)
    notes: Optional[str] = None


class StudentProspectResponse(BaseModel):
    """Student prospect response."""
    id: UUID
    first_name: str
    last_name: str
    email: Optional[str]
    phone: Optional[str]
    gender: str
    date_of_birth: str
    kcpe_marks: Decimal
    kcpe_year: int
    kpsea_marks: Optional[Decimal]
    kpsea_year: Optional[int]
    status: str
    application_date: str
    notes: Optional[str]
    created_at: str


class StudentProspectDetailResponse(BaseModel):
    """Detailed prospect with computed fields."""
    id: UUID
    first_name: str
    last_name: str
    email: Optional[str]
    phone: Optional[str]
    gender: str
    date_of_birth: str
    kcpe_marks: Decimal
    kcpe_year: int
    kpsea_marks: Optional[Decimal]
    kpsea_year: Optional[int]
    status: str
    application_date: str
    notes: Optional[str]
    admission_score: Decimal  # Computed: average of kcpe and kpsea
    created_at: str


# ============================================================================
# PARENT GUARDIAN SCHEMAS
# ============================================================================


class ParentGuardianCreate(BaseModel):
    """Create parent/guardian record."""
    first_name: str = Field(..., min_length=1, max_length=100)
    last_name: str = Field(..., min_length=1, max_length=100)
    email: Optional[str] = Field(None, max_length=255)
    phone: Optional[str] = Field(None, max_length=20)
    id_number: Optional[str] = Field(None, max_length=20)
    occupation: Optional[str] = Field(None, max_length=100)
    address: Optional[str] = None


class ParentGuardianResponse(BaseModel):
    """Parent/guardian response."""
    id: UUID
    first_name: str
    last_name: str
    email: Optional[str]
    phone: Optional[str]
    id_number: Optional[str]
    occupation: Optional[str]
    address: Optional[str]
    is_active: bool
    created_at: str


# ============================================================================
# STUDENT PARENT RELATIONSHIP SCHEMAS
# ============================================================================


class StudentParentRelationshipCreate(BaseModel):
    """Create student-parent relationship."""
    parent_guardian_id: UUID
    relationship_type: RelationshipType
    is_primary: bool = False
    emergency_contact: bool = False


class StudentParentRelationshipResponse(BaseModel):
    """Student-parent relationship response."""
    id: UUID
    student_id: UUID
    parent_guardian_id: UUID
    parent_name: str  # Computed
    relationship_type: str
    is_primary: bool
    emergency_contact: bool
    created_at: str


# ============================================================================
# STUDENT SCHEMAS
# ============================================================================


class StudentCreate(BaseModel):
    """Create student directly (not from prospect)."""
    first_name: str = Field(..., min_length=1, max_length=100)
    last_name: str = Field(..., min_length=1, max_length=100)
    email: Optional[str] = Field(None, max_length=255)
    phone: Optional[str] = Field(None, max_length=20)
    gender: Gender
    date_of_birth: date
    boarding_status: BoardingStatus
    admission_date: date
    upi_nemis_number: Optional[str] = None


class StudentUpdate(BaseModel):
    """Update student record."""
    email: Optional[str] = Field(None, max_length=255)
    phone: Optional[str] = Field(None, max_length=20)
    boarding_status: Optional[BoardingStatus] = None
    active_status: Optional[StudentActiveStatus] = None


class StudentResponse(BaseModel):
    """Student response."""
    id: UUID
    admission_number: str
    upi_nemis_number: Optional[str]
    first_name: str
    last_name: str
    email: Optional[str]
    phone: Optional[str]
    gender: str
    date_of_birth: str
    boarding_status: str
    active_status: str
    admission_date: str
    is_active: bool
    created_at: str


class StudentDetailResponse(BaseModel):
    """Detailed student profile with relationships."""
    id: UUID
    admission_number: str
    upi_nemis_number: Optional[str]
    first_name: str
    last_name: str
    email: Optional[str]
    phone: Optional[str]
    gender: str
    date_of_birth: str
    boarding_status: str
    active_status: str
    admission_date: str
    is_active: bool
    
    # Relationships
    parent_relationships: list[StudentParentRelationshipResponse] = []
    class_enrollments_count: int = 0
    current_class: Optional[str] = None
    
    # Finance
    fee_account_balance: Optional[Decimal] = None
    
    # Status
    has_pending_clearance: bool = False
    
    created_at: str


# ============================================================================
# ADMISSION SCHEMAS
# ============================================================================


class AdmitStudentRequest(BaseModel):
    """Request to admit student from prospect."""
    prospect_id: UUID = Field(..., description="Student prospect ID")
    class_level_id: UUID = Field(..., description="Class level to enroll into")
    stream_id: Optional[UUID] = None
    boarding_status: BoardingStatus


class AdmitStudentResponse(BaseModel):
    """Response to admission request."""
    success: bool
    student_id: UUID
    admission_number: str
    class_enrollment_id: UUID
    fee_account_id: UUID
    initial_invoice_id: Optional[UUID]
    message: str


# ============================================================================
# STUDENT CLEARANCE SCHEMAS
# ============================================================================


class StudentClearanceResponse(BaseModel):
    """Student clearance record."""
    id: UUID
    student_id: UUID
    student_name: str
    status: str
    initiated_date: str
    cleared_date: Optional[str]
    has_fee_balance: bool
    has_library_books: bool
    has_sports_gear: bool
    remarks: Optional[str]
    created_at: str


class InitiateClearanceRequest(BaseModel):
    """Request to initiate student clearance."""
    student_id: UUID = Field(..., description="Student ID")


class InitiateClearanceResponse(BaseModel):
    """Response to clearance initiation."""
    clearance_id: UUID
    student_id: UUID
    status: str
    has_fee_balance: bool
    has_library_books: bool
    has_sports_gear: bool
    clearance_required: bool  # True if any balance or items exist
    message: str


# ============================================================================
# STUDENT TRANSFER SCHEMAS
# ============================================================================


class StudentTransferCreate(BaseModel):
    """Create student transfer record."""
    student_id: UUID
    transfer_to_school: str
    transfer_date: date
    reason: Optional[str] = None


class StudentTransferResponse(BaseModel):
    """Student transfer response."""
    id: UUID
    student_id: UUID
    transfer_from_school: Optional[str]
    transfer_to_school: Optional[str]
    transfer_date: str
    reason: Optional[str]
    status: str
    created_at: str


# ============================================================================
# BULK OPERATIONS
# ============================================================================


class ProspectListResponse(BaseModel):
    """List of prospects."""
    total: int
    pending: int
    admitted: int
    rejected: int
    prospects: list[StudentProspectResponse]


class AdmissionStatistics(BaseModel):
    """Admission statistics for period."""
    period: str  # e.g., "2024-01"
    total_prospects: int
    total_admitted: int
    total_rejected: int
    admission_rate: Decimal
    average_kcpe_marks: Decimal
    average_kpsea_marks: Optional[Decimal]
