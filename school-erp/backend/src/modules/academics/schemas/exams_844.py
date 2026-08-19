"""
8-4-4 Examination System Schemas: Pydantic v2 models for API requests/responses.

Schemas for:
- Exam management
- Grading system configuration
- Exam results input
- Report card generation
"""
from datetime import datetime
from decimal import Decimal
from typing import List, Optional
from uuid import UUID

from pydantic import BaseModel, Field


# ============================================================================
# GRADING SYSTEM SCHEMAS
# ============================================================================


class GradingSystemCreate(BaseModel):
    """Create grading system entry."""

    min_mark: Decimal = Field(..., ge=0, le=100, description="Minimum mark for this grade")
    max_mark: Decimal = Field(..., ge=0, le=100, description="Maximum mark for this grade")
    grade: str = Field(..., min_length=1, max_length=5, description="A, A-, B+, etc.")
    points: int = Field(..., ge=1, le=12, description="Points value (1-12)")
    description: Optional[str] = None


class GradingSystemResponse(BaseModel):
    """Grading system entry response."""

    id: UUID
    min_mark: Decimal
    max_mark: Decimal
    grade: str
    points: int
    description: Optional[str]
    created_at: str


# ============================================================================
# EXAM SCHEMAS
# ============================================================================


class ExamCreate(BaseModel):
    """Create exam request."""

    term_id: UUID
    exam_type: str = Field(..., description="EOT, MID, MOCK, FINAL")
    name: str = Field(..., min_length=1, max_length=100)
    exam_date: datetime
    description: Optional[str] = None


class ExamUpdate(BaseModel):
    """Update exam request."""

    name: Optional[str] = None
    exam_date: Optional[datetime] = None
    description: Optional[str] = None
    is_active: Optional[bool] = None


class ExamResponse(BaseModel):
    """Exam response."""

    id: UUID
    term_id: UUID
    exam_type: str
    name: str
    exam_date: str  # ISO format
    description: Optional[str]
    is_active: bool
    created_at: str


class ExamDetailResponse(ExamResponse):
    """Exam response with result count."""

    result_count: int = 0


# ============================================================================
# EXAM RESULT SCHEMAS
# ============================================================================


class ExamResult844Input(BaseModel):
    """Single exam result for batch input."""

    student_id: UUID
    subject_id: UUID
    mark_score: Decimal = Field(..., ge=0, le=100)
    remarks: Optional[str] = None


class ExamResult844BatchInput(BaseModel):
    """Batch input of exam results."""

    exam_id: UUID
    results: List[ExamResult844Input] = Field(..., min_items=1)


class ExamResult844Response(BaseModel):
    """Exam result response."""

    id: UUID
    student_id: UUID
    exam_id: UUID
    subject_id: UUID
    mark_score: Decimal
    grade: str
    points: int
    remarks: Optional[str]
    is_validated: bool
    created_at: str


# ============================================================================
# REPORT CARD SCHEMAS
# ============================================================================


class SubjectResultSummary(BaseModel):
    """Result for a single subject in report card."""

    subject_id: UUID
    subject_name: str
    subject_code: str
    mark_score: Decimal
    grade: str
    points: int
    is_compulsory: bool


class ReportCardAggregates(BaseModel):
    """Aggregate statistics for report card."""

    total_subjects: int
    total_marks: Decimal  # Sum of all marks
    mean_mark: Decimal  # Average mark across subjects
    mean_grade: str  # Most common grade (mode) - represented as string
    mean_points: Decimal  # Average points


class StudentRanking(BaseModel):
    """Student's position in rankings."""

    stream_rank: int  # Position in own stream
    stream_total: int  # Total students in stream
    class_rank: int  # Position in entire class level
    class_total: int  # Total students in class level
    stream_rank_percentage: Decimal  # Top X% in stream
    class_rank_percentage: Decimal  # Top X% in class


class ReportCard844Response(BaseModel):
    """Complete report card for student in 8-4-4 system."""

    # Identifiers
    report_card_id: str  # Generated ID for this report card
    student_id: UUID
    student_name: str
    student_admission_number: str
    exam_id: UUID
    exam_name: str
    exam_type: str
    exam_date: str

    # Academic context
    academic_year: int
    term_number: int
    term_name: str
    class_level_name: str
    stream_name: str

    # Subject results (sorted by performance or by name)
    results: List[SubjectResultSummary]

    # Aggregates
    aggregates: ReportCardAggregates

    # Rankings
    rankings: StudentRanking

    # Metadata
    generated_at: str
    remarks: Optional[str] = None


# ============================================================================
# BULK UPLOAD SCHEMAS
# ============================================================================


class ExamMarksBulkUploadRequest(BaseModel):
    """Request to upload marks in bulk."""

    exam_id: UUID
    results: List[ExamResult844Input] = Field(
        ...,
        description="List of student marks",
        min_items=1,
        max_items=500,
    )


class BulkUploadResult(BaseModel):
    """Result of bulk upload."""

    total_submitted: int
    total_processed: int
    total_skipped: int
    total_errors: int
    errors: List[dict] = []


class ExamResultsBatch(BaseModel):
    """Response after batch input."""

    exam_id: UUID
    results_created: int
    results_updated: int
    failed: List[dict] = []


# ============================================================================
# FILTER/QUERY SCHEMAS
# ============================================================================


class ExamResultFilter(BaseModel):
    """Filter for querying exam results."""

    exam_id: Optional[UUID] = None
    student_id: Optional[UUID] = None
    subject_id: Optional[UUID] = None
    grade: Optional[str] = None
    min_mark: Optional[Decimal] = None
    max_mark: Optional[Decimal] = None


class ReportCardQuery(BaseModel):
    """Query parameters for report card."""

    student_id: UUID
    exam_id: UUID
    term_id: Optional[UUID] = None
    show_rankings: bool = True
