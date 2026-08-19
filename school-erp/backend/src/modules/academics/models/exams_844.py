"""
8-4-4 Examination System Models: Kenyan traditional grading system.

Models for:
- Exam: Exam configurations (End of Term, Mid-Term, etc.)
- GradingSystem: Grading scale (mark ranges → grades → points)
- ExamResult844: Individual student exam results with calculated grades
"""
from datetime import datetime
from decimal import Decimal
from typing import List
from uuid import UUID

from sqlalchemy import CheckConstraint, ForeignKey, Index, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column, relationship

from src.core.base import AuditableBase, TenantMixin


class Exam(AuditableBase, TenantMixin):
    """
    Exam configuration (e.g., "End of Term 1", "Mid-Term").

    Represents a specific examination sitting (e.g., all students take EOT1 exam).
    Links to Term to know when the exam was held.

    REAL USAGE:
    - End of Term 1 exam for 2024, held in April
    - Mid-Term exam for 2024 Term 2, held in July
    - Mock exam for Form 4 in October
    """

    __tablename__ = "exams"

    term_id: Mapped[UUID] = mapped_column(ForeignKey("terms.id", ondelete="RESTRICT"))
    exam_type: Mapped[str] = mapped_column(comment="EOT (End of Term), MID, MOCK, FINAL")
    name: Mapped[str] = mapped_column(comment="e.g., 'End of Term 1 2024'")
    exam_date: Mapped[datetime]
    description: Mapped[str] = mapped_column(default="", nullable=True)
    is_active: Mapped[bool] = mapped_column(default=True)

    # Relationships
    term: Mapped["Term"] = relationship("Term", back_populates="exams")
    results: Mapped[List["ExamResult844"]] = relationship(
        "ExamResult844",
        back_populates="exam",
        cascade="all, delete-orphan",
    )

    # Constraints
    __table_args__ = (
        UniqueConstraint(
            "school_id",
            "term_id",
            "exam_type",
            name="uq_exam_school_term_type",
        ),
        Index("idx_exam_term", "term_id"),
        Index("idx_exam_type", "exam_type"),
    )


class GradingSystem(AuditableBase, TenantMixin):
    """
    Grading scale: mark ranges → grades → points.

    Allows schools to define their own grading systems (e.g., strict vs. lenient).
    Defaults to Kenyan standard (80-100=A, 75-79=A-, etc.) if not defined.

    EXAMPLE DATA:
    - min_mark=80, max_mark=100, grade='A', points=12
    - min_mark=75, max_mark=79, grade='A-', points=11
    - min_mark=70, max_mark=74, grade='B+', points=10
    ...
    - min_mark=0, max_mark=19, grade='F', points=1 (or 0)

    USAGE:
    When calculating grade for a student with 85 marks:
    1. Query GradingSystem where school_id=X AND min_mark <= 85 AND max_mark >= 85
    2. Return grade='A', points=12
    """

    __tablename__ = "grading_systems"

    min_mark: Mapped[Decimal] = mapped_column(comment="Minimum mark for this grade (inclusive)")
    max_mark: Mapped[Decimal] = mapped_column(comment="Maximum mark for this grade (inclusive)")
    grade: Mapped[str] = mapped_column(comment="Grade letter (A, A-, B+, B, B-, C, D, D-, E, F)")
    points: Mapped[int] = mapped_column(comment="Points value (12, 11, 10, ...)")
    description: Mapped[str] = mapped_column(default="", nullable=True)

    # Constraints
    __table_args__ = (
        CheckConstraint("min_mark >= 0 AND max_mark <= 100", name="ck_grade_mark_range"),
        CheckConstraint("min_mark <= max_mark", name="ck_grade_min_le_max"),
        CheckConstraint("points > 0", name="ck_grade_points_positive"),
        UniqueConstraint(
            "school_id",
            "min_mark",
            "max_mark",
            name="uq_grade_school_range",
        ),
        Index("idx_grading_mark_range", "min_mark", "max_mark"),
        Index("idx_grading_grade", "grade"),
    )


class ExamResult844(AuditableBase, TenantMixin):
    """
    Individual exam result: student's mark + calculated grade & points.

    Stores the raw mark (0-100) along with automatically calculated:
    - Grade: A, A-, B+, B, B-, C, D, D-, E, F
    - Points: 12, 11, 10, 9, 8, 7, 6, 5, 4, 1

    REAL BUSINESS LOGIC:
    1. Teacher enters raw mark_score (0-100)
    2. System queries GradingSystem table
    3. Finds row where min_mark <= mark_score <= max_mark
    4. Extracts grade and points
    5. Stores all three (mark, grade, points)

    USAGE:
    - Input marks via bulk endpoint (POST /academics/844/marks/batch)
    - Each POST includes: student_id, subject_id, exam_id, mark_score
    - System calculates grade & points and stores
    - Used in report card generation
    - Included in aggregations for mean calculations
    """

    __tablename__ = "exam_results_844"

    student_id: Mapped[UUID] = mapped_column(ForeignKey("students.id", ondelete="CASCADE"))
    exam_id: Mapped[UUID] = mapped_column(ForeignKey("exams.id", ondelete="CASCADE"))
    subject_id: Mapped[UUID] = mapped_column(ForeignKey("subjects.id", ondelete="RESTRICT"))
    mark_score: Mapped[Decimal] = mapped_column(comment="Raw mark (0-100)")
    grade: Mapped[str] = mapped_column(comment="Calculated grade (A, A-, B+, etc.)")
    points: Mapped[int] = mapped_column(comment="Calculated points (12, 11, 10, etc.)")
    remarks: Mapped[str] = mapped_column(default="", nullable=True)
    is_validated: Mapped[bool] = mapped_column(
        default=False,
        comment="True if mark has been reviewed/approved by admin",
    )

    # Relationships
    exam: Mapped["Exam"] = relationship("Exam", back_populates="results")

    # Constraints
    __table_args__ = (
        CheckConstraint(
            "mark_score >= 0 AND mark_score <= 100",
            name="ck_exam_result_mark_range",
        ),
        UniqueConstraint(
            "school_id",
            "student_id",
            "exam_id",
            "subject_id",
            name="uq_exam_result_student_subject",
        ),
        Index("idx_exam_result_student", "student_id"),
        Index("idx_exam_result_exam", "exam_id"),
        Index("idx_exam_result_subject", "subject_id"),
        Index("idx_exam_result_grade", "grade"),
        Index("idx_exam_result_mark", "mark_score"),
        # For aggregations
        Index(
            "idx_exam_result_student_exam",
            "student_id",
            "exam_id",
        ),
    )
