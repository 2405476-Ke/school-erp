"""
Academics Schemas: Pydantic v2 models for API requests/responses.

Schemas for AcademicYear, Term, ClassLevel, Stream, Subject, and Enrollments.
All use nested relationships for complete API responses.
"""
from datetime import date
from decimal import Decimal
from typing import List, Optional
from uuid import UUID

from pydantic import BaseModel, Field


# ============================================================================
# ACADEMIC YEAR SCHEMAS
# ============================================================================


class AcademicYearCreate(BaseModel):
    """Create academic year request."""
    year: int = Field(..., ge=2000, le=2100, description="Academic year (e.g., 2024)")
    start_date: date
    end_date: date
    is_current: bool = False


class AcademicYearUpdate(BaseModel):
    """Update academic year request."""
    is_current: Optional[bool] = None
    is_active: Optional[bool] = None
    end_date: Optional[date] = None


class AcademicYearResponse(BaseModel):
    """Academic year response."""
    id: UUID
    year: int
    start_date: date
    end_date: date
    is_current: bool
    is_active: bool
    created_at: str


class AcademicYearDetailResponse(AcademicYearResponse):
    """Academic year with nested terms."""
    terms: List["TermResponse"] = []


# ============================================================================
# TERM SCHEMAS
# ============================================================================


class TermCreate(BaseModel):
    """Create term request."""
    academic_year_id: UUID
    term_number: int = Field(..., ge=1, le=3, description="Term 1, 2, or 3")
    name: str = Field(..., min_length=1, max_length=50)
    start_date: date
    end_date: date


class TermUpdate(BaseModel):
    """Update term request."""
    is_active: Optional[bool] = None
    end_date: Optional[date] = None


class TermResponse(BaseModel):
    """Term response."""
    id: UUID
    academic_year_id: UUID
    term_number: int
    name: str
    start_date: date
    end_date: date
    is_active: bool
    created_at: str


# ============================================================================
# SUBJECT SCHEMAS
# ============================================================================


class SubjectCreate(BaseModel):
    """Create subject request."""
    subject_code: str = Field(..., min_length=1, max_length=20, description="MATH, ENG, etc.")
    name: str = Field(..., min_length=1, max_length=100)
    description: Optional[str] = None
    is_compulsory: bool = True


class SubjectUpdate(BaseModel):
    """Update subject request."""
    name: Optional[str] = None
    description: Optional[str] = None
    is_compulsory: Optional[bool] = None
    is_active: Optional[bool] = None


class SubjectResponse(BaseModel):
    """Subject response."""
    id: UUID
    subject_code: str
    name: str
    description: Optional[str]
    is_compulsory: bool
    is_active: bool
    created_at: str


# ============================================================================
# STREAM SCHEMAS
# ============================================================================


class StreamCreate(BaseModel):
    """Create stream request."""
    class_level_id: UUID
    name: str = Field(..., min_length=1, max_length=50)
    stream_code: str = Field(..., min_length=1, max_length=10, description="A, B, C, etc.")
    max_capacity: int = Field(default=50, ge=1, le=100)
    form_tutor_id: Optional[UUID] = None


class StreamUpdate(BaseModel):
    """Update stream request."""
    name: Optional[str] = None
    max_capacity: Optional[int] = None
    form_tutor_id: Optional[UUID] = None
    is_active: Optional[bool] = None


class StreamResponse(BaseModel):
    """Stream response."""
    id: UUID
    class_level_id: UUID
    name: str
    stream_code: str
    max_capacity: int
    current_enrollment: int
    form_tutor_id: Optional[UUID]
    is_active: bool
    created_at: str

    @property
    def available_capacity(self) -> int:
        """Available capacity."""
        return self.max_capacity - self.current_enrollment


# ============================================================================
# CLASS LEVEL SCHEMAS
# ============================================================================


class ClassLevelCreate(BaseModel):
    """Create class level request."""
    academic_year_id: UUID
    name: str = Field(..., min_length=1, max_length=50, description="Form 1, Grade 9")
    level_code: str = Field(..., min_length=1, max_length=10, description="F1, G9")
    curriculum_type: str = Field(..., description="8-4-4 or CBC")


class ClassLevelUpdate(BaseModel):
    """Update class level request."""
    is_active: Optional[bool] = None


class ClassLevelResponse(BaseModel):
    """Class level response."""
    id: UUID
    academic_year_id: UUID
    name: str
    level_code: str
    curriculum_type: str
    is_active: bool
    created_at: str


class ClassLevelDetailResponse(ClassLevelResponse):
    """Class level with nested streams and subjects."""
    streams: List[StreamResponse] = []
    subjects: List[SubjectResponse] = []
    enrollment_count: int = 0  # Total students in this class


# ============================================================================
# STUDENT CLASS ENROLLMENT SCHEMAS
# ============================================================================


class StudentClassEnrollmentCreate(BaseModel):
    """Create student enrollment request."""
    student_id: UUID
    stream_id: UUID
    term_id: UUID
    enrollment_date: date = Field(default_factory=date.today)


class StudentClassEnrollmentUpdate(BaseModel):
    """Update enrollment request."""
    stream_id: Optional[UUID] = None
    is_active: Optional[bool] = None


class StudentClassEnrollmentResponse(BaseModel):
    """Student enrollment response."""
    id: UUID
    student_id: UUID
    class_level_id: UUID
    stream_id: UUID
    academic_year_id: UUID
    term_id: UUID
    enrollment_date: date
    is_active: bool
    created_at: str


class StudentEnrollmentDetailResponse(BaseModel):
    """Student enrollment with full details."""
    id: UUID
    student_id: UUID
    enrollment_date: date
    is_active: bool

    # Nested objects
    class_level: ClassLevelResponse
    stream: StreamResponse
    academic_year: AcademicYearResponse
    term: TermResponse

    # Selected subjects
    subject_selections: List["StudentSubjectSelectionResponse"] = []


# ============================================================================
# STUDENT SUBJECT SELECTION SCHEMAS
# ============================================================================


class StudentSubjectSelectionCreate(BaseModel):
    """Create subject selection request."""
    enrollment_id: UUID
    subject_id: UUID
    is_compulsory: bool = True


class StudentSubjectSelectionResponse(BaseModel):
    """Subject selection response."""
    id: UUID
    enrollment_id: UUID
    subject_id: UUID
    is_compulsory: bool
    selection_date: date
    created_at: str


class StudentSubjectSelectionDetailResponse(StudentSubjectSelectionResponse):
    """Subject selection with nested subject."""
    subject: SubjectResponse


# ============================================================================
# BULK/CONVENIENCE SCHEMAS
# ============================================================================


class EnrollmentRequest(BaseModel):
    """Request to enroll a student in class and auto-assign compulsory subjects."""
    student_id: UUID
    stream_id: UUID
    term_id: UUID


class EnrollmentResponse(BaseModel):
    """Response after student enrollment."""
    success: bool
    message: str
    enrollment_id: Optional[UUID] = None
    subjects_assigned: int = 0


class ClassStreamSummary(BaseModel):
    """Summary of a stream (used in class listing)."""
    id: UUID
    name: str
    stream_code: str
    current_enrollment: int
    max_capacity: int
    available_capacity: int
    form_tutor_id: Optional[UUID]


class ClassLevelSummaryResponse(BaseModel):
    """Summary of class level with all streams."""
    id: UUID
    name: str
    level_code: str
    curriculum_type: str
    streams: List[ClassStreamSummary]
    total_enrollment: int
    total_capacity: int


class StudentEnrollmentListResponse(BaseModel):
    """List of student enrollments."""
    id: UUID
    class_level_id: UUID
    class_level_name: str
    stream_id: UUID
    stream_name: str
    academic_year_id: UUID
    academic_year: int
    term_id: UUID
    term_name: str
    term_number: int
    enrollment_date: date
    is_active: bool
    subject_count: int  # Number of subjects selected


class StudentTranscriptSummary(BaseModel):
    """Student's enrollment history (transcript)."""
    student_id: UUID
    enrollments: List[StudentEnrollmentListResponse]


# Update forward references
AcademicYearDetailResponse.model_rebuild()
StudentEnrollmentDetailResponse.model_rebuild()
StudentSubjectSelectionDetailResponse.model_rebuild()
