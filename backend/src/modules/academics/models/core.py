"""
Academics Module: Core models for curriculum, classes, subjects, and enrollments.

Models:
- AcademicYear: School calendar (e.g., 2024)
- Term: Term within academic year (Term 1, 2, 3)
- Curriculum: Enum (8-4-4, CBC)
- ClassLevel: Grade/Form (e.g., Form 1, Grade 9)
- Stream: Section within class (North, South)
- Subject: Course (Mathematics, English, etc.)
- StudentClassEnrollment: Student → ClassLevel + Stream mapping
- StudentSubjectSelection: Student → Subject mapping (electives)
"""
from datetime import date
from decimal import Decimal
from enum import Enum
from typing import List, Optional
from uuid import UUID

from sqlalchemy import (
    Boolean,
    CheckConstraint,
    Date,
    Enum as SQLEnum,
    ForeignKey,
    Index,
    Integer,
    Numeric,
    String,
    Text,
    UniqueConstraint,
)
from sqlalchemy.dialects.postgresql import UUID as PG_UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from src.shared.base_model import AuditableBase, TenantMixin


class CurriculumEnum(str, Enum):
    """Curriculum types in Kenya."""
    OLD_8_4_4 = "8-4-4"
    CBC = "CBC"  # Competency-Based Curriculum


class AcademicYear(AuditableBase, TenantMixin):
    """
    Academic year calendar.
    Represents a school year (e.g., 2024, 2025).
    """
    __tablename__ = "academic_years"

    year: Mapped[int] = mapped_column(Integer, nullable=False)  # e.g., 2024
    start_date: Mapped[date] = mapped_column(Date, nullable=False)
    end_date: Mapped[date] = mapped_column(Date, nullable=False)

    is_current: Mapped[bool] = mapped_column(default=False, nullable=False, index=True)
    is_active: Mapped[bool] = mapped_column(default=True, nullable=False, index=True)

    # Relationships
    terms: Mapped[List["Term"]] = relationship(
        back_populates="academic_year",
        cascade="all, delete-orphan",
    )
    class_levels: Mapped[List["ClassLevel"]] = relationship(
        back_populates="academic_year",
    )
    enrollments: Mapped[List["StudentClassEnrollment"]] = relationship(
        back_populates="academic_year",
    )

    __table_args__ = (
        UniqueConstraint("school_id", "year", name="uq_academic_year_school_year"),
        CheckConstraint("start_date < end_date", name="ck_academic_year_dates"),
    )

    def __repr__(self) -> str:
        return f"<AcademicYear {self.year}>"


class Term(AuditableBase, TenantMixin):
    """
    Academic term (Term 1, Term 2, Term 3).
    Each term belongs to an academic year.
    """
    __tablename__ = "terms"

    academic_year_id: Mapped[UUID] = mapped_column(
        PG_UUID(as_uuid=True),
        ForeignKey("academic_years.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )

    term_number: Mapped[int] = mapped_column(Integer, nullable=False)  # 1, 2, 3
    name: Mapped[str] = mapped_column(String(50), nullable=False)  # "Term 1", "Term 2"

    start_date: Mapped[date] = mapped_column(Date, nullable=False)
    end_date: Mapped[date] = mapped_column(Date, nullable=False)

    is_active: Mapped[bool] = mapped_column(default=True, nullable=False, index=True)

    # Relationships
    academic_year: Mapped[AcademicYear] = relationship(back_populates="terms")
    enrollments: Mapped[List["StudentClassEnrollment"]] = relationship(
        back_populates="term",
    )
    assessments: Mapped[List["Assessment"]] = relationship(
        back_populates="term",
    )

    __table_args__ = (
        UniqueConstraint(
            "school_id", "academic_year_id", "term_number",
            name="uq_term_school_academic_year_number"
        ),
        CheckConstraint("term_number IN (1, 2, 3)", name="ck_term_number"),
        CheckConstraint("start_date < end_date", name="ck_term_dates"),
    )

    def __repr__(self) -> str:
        return f"<Term {self.name} ({self.academic_year.year})>"


class ClassLevel(AuditableBase, TenantMixin):
    """
    Class/Grade level (Form 1, Form 2, Grade 9, etc.).
    Linked to academic year and curriculum type.
    """
    __tablename__ = "class_levels"

    academic_year_id: Mapped[UUID] = mapped_column(
        PG_UUID(as_uuid=True),
        ForeignKey("academic_years.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )

    name: Mapped[str] = mapped_column(String(50), nullable=False)  # "Form 1", "Grade 9"
    level_code: Mapped[str] = mapped_column(
        String(10), nullable=False
    )  # "F1", "G9", "F2"

    curriculum_type: Mapped[str] = mapped_column(
        SQLEnum(CurriculumEnum, values_callable=lambda x: [e.value for e in x]),
        nullable=False,
    )

    is_active: Mapped[bool] = mapped_column(default=True, nullable=False, index=True)

    # Relationships
    academic_year: Mapped[AcademicYear] = relationship(back_populates="class_levels")
    streams: Mapped[List["Stream"]] = relationship(
        back_populates="class_level",
        cascade="all, delete-orphan",
    )
    subjects: Mapped[List["Subject"]] = relationship(
        secondary="class_level_subjects",
        back_populates="class_levels",
    )
    enrollments: Mapped[List["StudentClassEnrollment"]] = relationship(
        back_populates="class_level",
    )

    __table_args__ = (
        UniqueConstraint(
            "school_id", "academic_year_id", "level_code",
            name="uq_class_level_school_year_code"
        ),
    )

    def __repr__(self) -> str:
        return f"<ClassLevel {self.name} ({self.curriculum_type})>"


class Stream(AuditableBase, TenantMixin):
    """
    Stream/Section within a class (North, South, East, West).
    Multiple streams per class level to manage capacity.
    """
    __tablename__ = "streams"

    class_level_id: Mapped[UUID] = mapped_column(
        PG_UUID(as_uuid=True),
        ForeignKey("class_levels.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )

    name: Mapped[str] = mapped_column(String(50), nullable=False)  # "North", "South"
    stream_code: Mapped[str] = mapped_column(String(10), nullable=False)  # "A", "B"

    max_capacity: Mapped[int] = mapped_column(Integer, default=50, nullable=False)
    current_enrollment: Mapped[int] = mapped_column(Integer, default=0, nullable=False)

    form_tutor_id: Mapped[Optional[UUID]] = mapped_column(
        PG_UUID(as_uuid=True),
        nullable=True,
    )  # Teacher assigned as form tutor

    is_active: Mapped[bool] = mapped_column(default=True, nullable=False, index=True)

    # Relationships
    class_level: Mapped[ClassLevel] = relationship(back_populates="streams")
    enrollments: Mapped[List["StudentClassEnrollment"]] = relationship(
        back_populates="stream",
    )

    __table_args__ = (
        UniqueConstraint(
            "school_id", "class_level_id", "stream_code",
            name="uq_stream_school_class_code"
        ),
        CheckConstraint("current_enrollment <= max_capacity", name="ck_stream_capacity"),
    )

    def __repr__(self) -> str:
        return f"<Stream {self.name}>"

    @property
    def available_capacity(self) -> int:
        """Calculate available capacity in stream."""
        return self.max_capacity - self.current_enrollment


class Subject(AuditableBase, TenantMixin):
    """
    Subject/Course (Mathematics, English, History, etc.).
    Can be compulsory or elective.
    """
    __tablename__ = "subjects"

    subject_code: Mapped[str] = mapped_column(
        String(20), nullable=False, unique=True
    )  # "MATH", "ENG"
    name: Mapped[str] = mapped_column(String(100), nullable=False)
    description: Mapped[Optional[str]] = mapped_column(Text)

    is_compulsory: Mapped[bool] = mapped_column(
        default=True, nullable=False
    )  # True: must take, False: elective
    is_active: Mapped[bool] = mapped_column(default=True, nullable=False, index=True)

    # Relationships
    class_levels: Mapped[List[ClassLevel]] = relationship(
        secondary="class_level_subjects",
        back_populates="subjects",
    )
    student_selections: Mapped[List["StudentSubjectSelection"]] = relationship(
        back_populates="subject",
        cascade="all, delete-orphan",
    )
    class_teacher_assignments: Mapped[List["ClassTeacherAssignment"]] = relationship(
        back_populates="subject",
    )
    assessments: Mapped[List["Assessment"]] = relationship(
        back_populates="subject",
    )

    __table_args__ = (
        UniqueConstraint("school_id", "subject_code", name="uq_subject_school_code"),
    )

    def __repr__(self) -> str:
        return f"<Subject {self.name}>"


class ClassLevelSubject(AuditableBase):
    """
    Association table: which subjects are offered in which class levels.
    """
    __tablename__ = "class_level_subjects"

    class_level_id: Mapped[UUID] = mapped_column(
        PG_UUID(as_uuid=True),
        ForeignKey("class_levels.id", ondelete="CASCADE"),
        nullable=False,
    )
    subject_id: Mapped[UUID] = mapped_column(
        PG_UUID(as_uuid=True),
        ForeignKey("subjects.id", ondelete="CASCADE"),
        nullable=False,
    )

    __table_args__ = (
        UniqueConstraint(
            "class_level_id", "subject_id",
            name="uq_class_level_subject"
        ),
    )


class StudentClassEnrollment(AuditableBase, TenantMixin):
    """
    Student enrollment in a class for a specific term.
    Maps: Student → ClassLevel + Stream + AcademicYear + Term
    """
    __tablename__ = "student_class_enrollments"

    student_id: Mapped[UUID] = mapped_column(
        PG_UUID(as_uuid=True),
        ForeignKey("students.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )

    class_level_id: Mapped[UUID] = mapped_column(
        PG_UUID(as_uuid=True),
        ForeignKey("class_levels.id", ondelete="CASCADE"),
        nullable=False,
    )

    stream_id: Mapped[UUID] = mapped_column(
        PG_UUID(as_uuid=True),
        ForeignKey("streams.id", ondelete="CASCADE"),
        nullable=False,
    )

    academic_year_id: Mapped[UUID] = mapped_column(
        PG_UUID(as_uuid=True),
        ForeignKey("academic_years.id", ondelete="CASCADE"),
        nullable=False,
    )

    term_id: Mapped[UUID] = mapped_column(
        PG_UUID(as_uuid=True),
        ForeignKey("terms.id", ondelete="CASCADE"),
        nullable=False,
    )

    enrollment_date: Mapped[date] = mapped_column(Date, nullable=False)
    is_active: Mapped[bool] = mapped_column(default=True, nullable=False, index=True)

    # Relationships (lazy load to avoid N+1)
    student: Mapped["Student"] = relationship()
    class_level: Mapped[ClassLevel] = relationship(back_populates="enrollments")
    stream: Mapped[Stream] = relationship(back_populates="enrollments")
    academic_year: Mapped[AcademicYear] = relationship(back_populates="enrollments")
    term: Mapped[Term] = relationship(back_populates="enrollments")

    subject_selections: Mapped[List["StudentSubjectSelection"]] = relationship(
        back_populates="enrollment",
        cascade="all, delete-orphan",
    )

    __table_args__ = (
        UniqueConstraint(
            "school_id", "student_id", "academic_year_id", "term_id",
            name="uq_enrollment_student_year_term"
        ),
        Index("idx_enrollment_class_term", "class_level_id", "term_id"),
    )

    def __repr__(self) -> str:
        return f"<StudentClassEnrollment {self.student_id} → {self.class_level.name}>"


class StudentSubjectSelection(AuditableBase, TenantMixin):
    """
    Student selection of a subject for their enrollment.
    Used for compulsory (auto-assigned) and elective (student-selected) subjects.
    """
    __tablename__ = "student_subject_selections"

    enrollment_id: Mapped[UUID] = mapped_column(
        PG_UUID(as_uuid=True),
        ForeignKey("student_class_enrollments.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )

    subject_id: Mapped[UUID] = mapped_column(
        PG_UUID(as_uuid=True),
        ForeignKey("subjects.id", ondelete="CASCADE"),
        nullable=False,
    )

    is_compulsory: Mapped[bool] = mapped_column(
        default=True, nullable=False
    )  # True: auto-assigned, False: student-selected
    selection_date: Mapped[date] = mapped_column(Date, nullable=False)

    # Relationships
    enrollment: Mapped[StudentClassEnrollment] = relationship(
        back_populates="subject_selections"
    )
    subject: Mapped[Subject] = relationship(back_populates="student_selections")

    __table_args__ = (
        UniqueConstraint(
            "school_id", "enrollment_id", "subject_id",
            name="uq_subject_selection_enrollment_subject"
        ),
    )

    def __repr__(self) -> str:
        return f"<StudentSubjectSelection {self.subject.name}>"


# ============================================================================
# PLACEHOLDER: Assessment, ClassTeacherAssignment, AttendanceRecord
# These will be implemented in PHASE 3 PART 2
# ============================================================================

class Assessment(AuditableBase, TenantMixin):
    """
    Assessment/Test/Exam record.
    To be fully implemented in PHASE 3 PART 2.
    """
    __tablename__ = "assessments"

    term_id: Mapped[UUID] = mapped_column(
        PG_UUID(as_uuid=True),
        ForeignKey("terms.id", ondelete="CASCADE"),
        nullable=False,
    )

    subject_id: Mapped[UUID] = mapped_column(
        PG_UUID(as_uuid=True),
        ForeignKey("subjects.id", ondelete="CASCADE"),
        nullable=False,
    )

    assessment_type: Mapped[str] = mapped_column(
        String(50), nullable=False
    )  # "EXAM", "CAT", "ASSIGNMENT"

    name: Mapped[str] = mapped_column(String(100), nullable=False)
    max_score: Mapped[Decimal] = mapped_column(Numeric(5, 2), nullable=False)

    # Relationships
    term: Mapped[Term] = relationship(back_populates="assessments")
    subject: Mapped[Subject] = relationship(back_populates="assessments")

    __table_args__ = (
        Index("idx_assessment_term_subject", "term_id", "subject_id"),
    )


class ClassTeacherAssignment(AuditableBase, TenantMixin):
    """
    Assign teacher to teach a subject in a class.
    To be fully implemented in PHASE 3 PART 2.
    """
    __tablename__ = "class_teacher_assignments"

    class_level_id: Mapped[UUID] = mapped_column(
        PG_UUID(as_uuid=True),
        ForeignKey("class_levels.id", ondelete="CASCADE"),
        nullable=False,
    )

    subject_id: Mapped[UUID] = mapped_column(
        PG_UUID(as_uuid=True),
        ForeignKey("subjects.id", ondelete="CASCADE"),
        nullable=False,
    )

    teacher_id: Mapped[UUID] = mapped_column(
        PG_UUID(as_uuid=True),
        nullable=False,
    )

    # Relationships
    subject: Mapped[Subject] = relationship(back_populates="class_teacher_assignments")

    __table_args__ = (
        UniqueConstraint(
            "school_id", "class_level_id", "subject_id",
            name="uq_class_teacher_assignment"
        ),
    )
