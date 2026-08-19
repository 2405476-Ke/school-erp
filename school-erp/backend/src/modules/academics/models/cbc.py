"""
CBC (Competency-Based Curriculum) Assessment System Models.

Models for competency-based assessments using 1-4 rubric scoring.

Structure:
- Learning Area (e.g., Mathematics Activities, Language Activities)
  - Strand (e.g., Measurement, Geometry, Number Sense)
    - Rubric Score (1-4: Below Expectation to Exceeding Expectation)

Assessment Types:
- Formative: Ongoing classroom assessments
- Summative: End-of-term comprehensive assessment
"""
from datetime import date
from typing import List
from uuid import UUID

from sqlalchemy import CheckConstraint, ForeignKey, Index, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column, relationship

from src.core.base import AuditableBase, TenantMixin


class CbcLearningArea(AuditableBase, TenantMixin):
    """
    Learning Area in CBC curriculum (e.g., Mathematics Activities, Language Activities).

    In Kenya CBC:
    - Grade 1-3: 7 learning areas
    - Grade 4-6: 7 learning areas
    - Grade 7-9: 7 learning areas (aligned with KICD framework)

    Each learning area contains multiple strands.
    """

    __tablename__ = "cbc_learning_areas"

    code: Mapped[str] = mapped_column(
        comment="Learning area code (MATH, ENG, SCI, etc.)"
    )
    name: Mapped[str] = mapped_column(comment="Full name of learning area")
    description: Mapped[str] = mapped_column(default="", nullable=True)
    is_active: Mapped[bool] = mapped_column(default=True)

    # Relationships
    strands: Mapped[List["CbcStrand"]] = relationship(
        "CbcStrand",
        back_populates="learning_area",
        cascade="all, delete-orphan",
    )

    # Constraints
    __table_args__ = (
        UniqueConstraint(
            "school_id",
            "code",
            name="uq_learning_area_school_code",
        ),
        Index("idx_learning_area_code", "code"),
    )


class CbcStrand(AuditableBase, TenantMixin):
    """
    Strand under a Learning Area (e.g., Measurement, Geometry under Mathematics).

    Each strand represents a specific competency area.
    Strands are assessed individually, then rolled up to Learning Area level.

    Example:
    Learning Area: Mathematics Activities
      - Strand: Number Sense
      - Strand: Measurement
      - Strand: Geometry
      - Strand: Data Handling
    """

    __tablename__ = "cbc_strands"

    learning_area_id: Mapped[UUID] = mapped_column(ForeignKey("cbc_learning_areas.id", ondelete="CASCADE"))
    code: Mapped[str] = mapped_column(comment="Strand code (e.g., MEAS, GEO)")
    name: Mapped[str] = mapped_column(comment="Strand name")
    description: Mapped[str] = mapped_column(default="", nullable=True)
    is_active: Mapped[bool] = mapped_column(default=True)

    # Relationships
    learning_area: Mapped["CbcLearningArea"] = relationship(
        "CbcLearningArea",
        back_populates="strands",
    )
    rubric_scores: Mapped[List["CbcRubricScore"]] = relationship(
        "CbcRubricScore",
        back_populates="strand",
        cascade="all, delete-orphan",
    )

    # Constraints
    __table_args__ = (
        UniqueConstraint(
            "school_id",
            "learning_area_id",
            "code",
            name="uq_strand_learning_area_code",
        ),
        Index("idx_strand_learning_area", "learning_area_id"),
    )


class CbcAssessment(AuditableBase, TenantMixin):
    """
    Assessment configuration (Formative or Summative).

    Formative: Continuous assessment during term
    Summative: End-of-term comprehensive assessment

    Each assessment is tied to a term and can have multiple rubric scores.
    """

    __tablename__ = "cbc_assessments"

    term_id: Mapped[UUID] = mapped_column(ForeignKey("terms.id", ondelete="RESTRICT"))
    assessment_type: Mapped[str] = mapped_column(
        comment="FORMATIVE or SUMMATIVE"
    )
    name: Mapped[str] = mapped_column(comment="e.g., 'End of Term 1 Summative'")
    assessment_date: Mapped[date]
    description: Mapped[str] = mapped_column(default="", nullable=True)
    is_active: Mapped[bool] = mapped_column(default=True)

    # Relationships
    rubric_scores: Mapped[List["CbcRubricScore"]] = relationship(
        "CbcRubricScore",
        back_populates="assessment",
        cascade="all, delete-orphan",
    )

    # Constraints
    __table_args__ = (
        CheckConstraint(
            "assessment_type IN ('FORMATIVE', 'SUMMATIVE')",
            name="ck_assessment_type",
        ),
        UniqueConstraint(
            "school_id",
            "term_id",
            "assessment_type",
            name="uq_assessment_term_type",
        ),
        Index("idx_assessment_term", "term_id"),
        Index("idx_assessment_type", "assessment_type"),
    )


class CbcRubricScore(AuditableBase, TenantMixin):
    """
    Individual rubric score: student's competency level on a strand (1-4 scale).

    SCORING RUBRIC (KICD Standard):
    - 4: Exceeding Expectation (E) - Demonstrates high level of competency
    - 3: Meeting Expectation (M) - Demonstrates expected level of competency
    - 2: Approaching Expectation (A) - Approaching expected level of competency
    - 1: Below Expectation (B) - Has not yet demonstrated expected competency

    REAL BUSINESS LOGIC:
    1. Teacher assesses student on a strand
    2. Assigns score (1, 2, 3, or 4)
    3. System validates strict integer
    4. Stores with teacher remarks (optional)
    5. Used in report generation to calculate mode (most frequent score)

    Unique Constraint: One score per student per strand per assessment
    """

    __tablename__ = "cbc_rubric_scores"

    student_id: Mapped[UUID] = mapped_column(ForeignKey("students.id", ondelete="CASCADE"))
    assessment_id: Mapped[UUID] = mapped_column(ForeignKey("cbc_assessments.id", ondelete="CASCADE"))
    strand_id: Mapped[UUID] = mapped_column(ForeignKey("cbc_strands.id", ondelete="RESTRICT"))
    score: Mapped[int] = mapped_column(
        comment="Competency level (1=Below, 2=Approaching, 3=Meeting, 4=Exceeding)"
    )
    teacher_remarks: Mapped[str] = mapped_column(default="", nullable=True)
    is_validated: Mapped[bool] = mapped_column(
        default=False,
        comment="True if reviewed by admin",
    )

    # Relationships
    assessment: Mapped["CbcAssessment"] = relationship(
        "CbcAssessment",
        back_populates="rubric_scores",
    )
    strand: Mapped["CbcStrand"] = relationship(
        "CbcStrand",
        back_populates="rubric_scores",
    )

    # Constraints
    __table_args__ = (
        CheckConstraint(
            "score >= 1 AND score <= 4",
            name="ck_rubric_score_range",
        ),
        UniqueConstraint(
            "school_id",
            "student_id",
            "assessment_id",
            "strand_id",
            name="uq_rubric_score_student_strand",
        ),
        Index("idx_rubric_score_student", "student_id"),
        Index("idx_rubric_score_assessment", "assessment_id"),
        Index("idx_rubric_score_strand", "strand_id"),
        Index("idx_rubric_score_score", "score"),
        # For aggregations
        Index(
            "idx_rubric_score_student_assessment",
            "student_id",
            "assessment_id",
        ),
    )
