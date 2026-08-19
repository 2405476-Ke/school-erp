"""
CBC (Competency-Based Curriculum) Assessment Schemas: Pydantic v2 models.

Schemas for:
- Learning Areas and Strands
- Assessment management
- Rubric score input
- CBC report generation
"""
from datetime import date
from typing import List, Optional
from uuid import UUID

from pydantic import BaseModel, Field


# ============================================================================
# LEARNING AREA & STRAND SCHEMAS
# ============================================================================


class CbcLearningAreaCreate(BaseModel):
    """Create learning area request."""

    code: str = Field(..., min_length=1, max_length=20, description="MATH, ENG, SCI, etc.")
    name: str = Field(..., min_length=1, max_length=100)
    description: Optional[str] = None


class CbcLearningAreaResponse(BaseModel):
    """Learning area response."""

    id: UUID
    code: str
    name: str
    description: Optional[str]
    is_active: bool
    created_at: str


class CbcLearningAreaDetailResponse(CbcLearningAreaResponse):
    """Learning area with nested strands."""

    strands: List["CbcStrandResponse"] = []


class CbcStrandCreate(BaseModel):
    """Create strand request."""

    learning_area_id: UUID
    code: str = Field(..., min_length=1, max_length=20, description="MEAS, GEO, etc.")
    name: str = Field(..., min_length=1, max_length=100)
    description: Optional[str] = None


class CbcStrandResponse(BaseModel):
    """Strand response."""

    id: UUID
    learning_area_id: UUID
    code: str
    name: str
    description: Optional[str]
    is_active: bool
    created_at: str


# ============================================================================
# ASSESSMENT SCHEMAS
# ============================================================================


class CbcAssessmentCreate(BaseModel):
    """Create assessment request."""

    term_id: UUID
    assessment_type: str = Field(..., description="FORMATIVE or SUMMATIVE")
    name: str = Field(..., min_length=1, max_length=100)
    assessment_date: date
    description: Optional[str] = None


class CbcAssessmentResponse(BaseModel):
    """Assessment response."""

    id: UUID
    term_id: UUID
    assessment_type: str
    name: str
    assessment_date: str
    description: Optional[str]
    is_active: bool
    created_at: str


# ============================================================================
# RUBRIC SCORE SCHEMAS
# ============================================================================


class RubricScoreInput(BaseModel):
    """Single rubric score for batch input."""

    student_id: UUID
    strand_id: UUID
    score: int = Field(..., ge=1, le=4, description="1=Below, 2=Approaching, 3=Meeting, 4=Exceeding")
    teacher_remarks: Optional[str] = None


class CbcRubricScoreBatchInput(BaseModel):
    """Batch rubric score input."""

    assessment_id: UUID
    scores: List[RubricScoreInput] = Field(..., min_items=1)


class CbcRubricScoreResponse(BaseModel):
    """Rubric score response."""

    id: UUID
    student_id: UUID
    assessment_id: UUID
    strand_id: UUID
    score: int
    teacher_remarks: Optional[str]
    is_validated: bool
    created_at: str


# ============================================================================
# CBC REPORT CARD SCHEMAS
# ============================================================================


class StrandPerformance(BaseModel):
    """Performance on a single strand."""

    strand_id: UUID
    strand_code: str
    strand_name: str
    score: int  # 1-4
    score_level: str  # "Below", "Approaching", "Meeting", "Exceeding"
    teacher_remarks: Optional[str]


class LearningAreaPerformance(BaseModel):
    """Performance in a learning area (aggregated from strands)."""

    learning_area_id: UUID
    learning_area_code: str
    learning_area_name: str
    strands: List[StrandPerformance]
    # Calculated fields
    mode_score: int  # Most frequent score across strands (1-4)
    mode_level: str  # "Below", "Approaching", "Meeting", "Exceeding"
    average_score: float  # Mean of all strand scores
    total_strands_assessed: int


class CbcReportCard(BaseModel):
    """CBC Report Card (KICD-compliant format)."""

    # Identifiers
    report_id: str
    student_id: UUID
    student_name: str
    student_admission_number: str
    term_id: UUID
    term_name: str
    term_number: int
    academic_year: int
    assessment_type: str  # FORMATIVE or SUMMATIVE
    assessment_name: str
    assessment_date: str

    # Academic context
    class_level_name: str
    stream_name: str

    # Learning areas with nested strands
    learning_areas: List[LearningAreaPerformance]

    # Overall summary
    total_learning_areas: int
    learning_areas_meeting_expectation: int  # Count where mode_score >= 3
    learning_areas_approaching: int  # Count where mode_score == 2
    learning_areas_below: int  # Count where mode_score == 1

    # Metadata
    generated_at: str
    teacher_remarks: Optional[str] = None


# ============================================================================
# HELPER SCHEMAS
# ============================================================================


class ScoreLevelMapping(BaseModel):
    """Mapping of score to level."""

    score: int
    level: str
    description: str


class CbcBulkUploadResult(BaseModel):
    """Result of bulk rubric score upload."""

    assessment_id: UUID
    total_submitted: int
    total_processed: int
    total_skipped: int
    total_errors: int
    errors: List[dict] = []


# Update forward references
CbcLearningAreaDetailResponse.model_rebuild()
