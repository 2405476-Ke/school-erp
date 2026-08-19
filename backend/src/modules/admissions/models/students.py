"""
SQLAlchemy ORM models for Student Admissions and Lifecycle Management.

Models:
- StudentProspect: Application records (KCPE/KPSEA marks, status)
- Student: Main student profile (admission_number, UPI/NEMIS, demographics)
- ParentGuardian: Parent/Guardian records
- StudentParentRelationship: M:N association between Student and ParentGuardian
- StudentClearance: Exit clearance tracking
- StudentTransfer: Inter-school transfer records
"""

from decimal import Decimal
from datetime import datetime, date
from uuid import UUID
from enum import Enum

from sqlalchemy import (
    CheckConstraint,
    ForeignKey,
    Index,
    UniqueConstraint,
    String,
    Integer,
    Boolean,
    Date,
    DateTime,
    Text,
    Numeric,
    Enum as SQLEnum,
)
from sqlalchemy.orm import Mapped, mapped_column, relationship

from src.core.models import AuditableBase, TenantMixin


class ProspectStatus(str, Enum):
    """Application status for StudentProspect."""
    PENDING = "PENDING"
    ADMITTED = "ADMITTED"
    REJECTED = "REJECTED"


class Gender(str, Enum):
    """Gender classification."""
    MALE = "MALE"
    FEMALE = "FEMALE"
    OTHER = "OTHER"


class BoardingStatus(str, Enum):
    """Student boarding status."""
    BOARDING = "BOARDING"
    DAY = "DAY"


class StudentActiveStatus(str, Enum):
    """Student active status."""
    ACTIVE = "ACTIVE"
    SUSPENDED = "SUSPENDED"
    WITHDRAWN = "WITHDRAWN"
    GRADUATED = "GRADUATED"


class ClearanceStatus(str, Enum):
    """Student clearance status."""
    PENDING = "PENDING"
    CLEARED = "CLEARED"
    PARTIALLY_CLEARED = "PARTIALLY_CLEARED"


class RelationshipType(str, Enum):
    """Relationship to student."""
    MOTHER = "MOTHER"
    FATHER = "FATHER"
    GUARDIAN = "GUARDIAN"
    OTHER = "OTHER"


class StudentProspect(AuditableBase, TenantMixin):
    """
    Application record for prospective student.
    
    Attributes:
        school_id: Tenant identifier
        first_name: Applicant first name
        last_name: Applicant last name
        email: Email address
        phone: Phone number
        gender: MALE/FEMALE/OTHER
        date_of_birth: Date of birth
        kcpe_marks: Marks scored in KCPE (0-500)
        kcpe_year: Year of KCPE exam
        kpsea_marks: Marks scored in KPSEA (0-500, if applicable)
        kpsea_year: Year of KPSEA exam
        status: PENDING/ADMITTED/REJECTED
        application_date: Date of application
        notes: Additional application notes
    """
    __tablename__ = "student_prospects"
    
    first_name: Mapped[str] = mapped_column(String(100))
    last_name: Mapped[str] = mapped_column(String(100))
    email: Mapped[str | None] = mapped_column(String(255), nullable=True)
    phone: Mapped[str | None] = mapped_column(String(20), nullable=True)
    gender: Mapped[Gender] = mapped_column(SQLEnum(Gender))
    date_of_birth: Mapped[date] = mapped_column(Date)
    kcpe_marks: Mapped[Decimal] = mapped_column(Numeric(6, 2), comment="Out of 500")
    kcpe_year: Mapped[int] = mapped_column(Integer, comment="Year of KCPE exam")
    kpsea_marks: Mapped[Decimal | None] = mapped_column(Numeric(6, 2), nullable=True, comment="Out of 500")
    kpsea_year: Mapped[int | None] = mapped_column(Integer, nullable=True)
    status: Mapped[ProspectStatus] = mapped_column(SQLEnum(ProspectStatus), default=ProspectStatus.PENDING)
    application_date: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    notes: Mapped[str | None] = mapped_column(Text, nullable=True)
    
    # Relationships
    student: Mapped["Student | None"] = relationship(
        back_populates="prospect",
        uselist=False,
        foreign_keys="Student.prospect_id",
    )
    
    __table_args__ = (
        CheckConstraint("kcpe_marks >= 0 AND kcpe_marks <= 500", name="ck_prospect_kcpe_marks"),
        CheckConstraint("kpsea_marks IS NULL OR (kpsea_marks >= 0 AND kpsea_marks <= 500)", name="ck_prospect_kpsea_marks"),
        CheckConstraint("kcpe_year >= 2000", name="ck_prospect_kcpe_year"),
        Index("idx_prospect_school_status", "school_id", "status"),
        Index("idx_prospect_kcpe_marks", "kcpe_marks"),
    )


class Student(AuditableBase, TenantMixin):
    """
    Main student profile record.
    
    This is the primary student record. Created either via admission from prospect
    or via direct enrollment. Linked to all downstream modules (academics, finance, library).
    
    Attributes:
        school_id: Tenant identifier
        prospect_id: FK to StudentProspect (optional, if admitted from prospect)
        admission_number: Unique sequential number (e.g., ADM-2024-001)
        upi_nemis_number: UPI/NEMIS number from MoE
        first_name: Student first name
        last_name: Student last name
        email: Student email
        phone: Student phone
        gender: MALE/FEMALE/OTHER
        date_of_birth: Date of birth
        boarding_status: BOARDING/DAY
        active_status: ACTIVE/SUSPENDED/WITHDRAWN/GRADUATED
        admission_date: Date admitted to school
        is_active: Soft delete flag
    """
    __tablename__ = "students"
    
    prospect_id: Mapped[UUID | None] = mapped_column(
        ForeignKey("student_prospects.id", ondelete="SET NULL"),
        nullable=True,
    )
    admission_number: Mapped[str] = mapped_column(String(50), comment="Sequential admission number")
    upi_nemis_number: Mapped[str | None] = mapped_column(String(50), nullable=True, comment="UPI from MoE")
    first_name: Mapped[str] = mapped_column(String(100))
    last_name: Mapped[str] = mapped_column(String(100))
    email: Mapped[str | None] = mapped_column(String(255), nullable=True)
    phone: Mapped[str | None] = mapped_column(String(20), nullable=True)
    gender: Mapped[Gender] = mapped_column(SQLEnum(Gender))
    date_of_birth: Mapped[date] = mapped_column(Date)
    boarding_status: Mapped[BoardingStatus] = mapped_column(SQLEnum(BoardingStatus))
    active_status: Mapped[StudentActiveStatus] = mapped_column(
        SQLEnum(StudentActiveStatus),
        default=StudentActiveStatus.ACTIVE,
    )
    admission_date: Mapped[date] = mapped_column(Date)
    is_active: Mapped[bool] = mapped_column(default=True, comment="Soft delete flag")
    
    # Relationships
    prospect: Mapped["StudentProspect | None"] = relationship(
        back_populates="student",
        foreign_keys=[prospect_id],
    )
    parent_relationships: Mapped[list["StudentParentRelationship"]] = relationship(
        back_populates="student",
        cascade="all, delete-orphan",
        lazy="select",
    )
    class_enrollments: Mapped[list["StudentClassEnrollment"]] = relationship(
        back_populates="student",
        cascade="all, delete-orphan",
        lazy="select",
    )
    fee_account: Mapped["FeeAccount | None"] = relationship(
        back_populates="student",
        uselist=False,
        cascade="all, delete-orphan",
    )
    clearances: Mapped[list["StudentClearance"]] = relationship(
        back_populates="student",
        cascade="all, delete-orphan",
        lazy="select",
    )
    transfers: Mapped[list["StudentTransfer"]] = relationship(
        back_populates="student",
        cascade="all, delete-orphan",
        lazy="select",
    )
    
    __table_args__ = (
        UniqueConstraint("school_id", "admission_number", name="uq_student_admission_number"),
        UniqueConstraint("school_id", "upi_nemis_number", name="uq_student_upi_nemis"),
        Index("idx_student_school_active", "school_id", "is_active"),
        Index("idx_student_gender", "gender"),
        Index("idx_student_admission_date", "admission_date"),
    )


class ParentGuardian(AuditableBase, TenantMixin):
    """
    Parent or guardian record.
    
    Can be associated with multiple students via StudentParentRelationship.
    
    Attributes:
        school_id: Tenant identifier
        first_name: Parent first name
        last_name: Parent last name
        email: Email
        phone: Phone number
        id_number: National ID
        occupation: Occupation/profession
        address: Residential address
        is_active: Active/inactive
    """
    __tablename__ = "parent_guardians"
    
    first_name: Mapped[str] = mapped_column(String(100))
    last_name: Mapped[str] = mapped_column(String(100))
    email: Mapped[str | None] = mapped_column(String(255), nullable=True)
    phone: Mapped[str | None] = mapped_column(String(20), nullable=True)
    id_number: Mapped[str | None] = mapped_column(String(20), nullable=True)
    occupation: Mapped[str | None] = mapped_column(String(100), nullable=True)
    address: Mapped[str | None] = mapped_column(Text, nullable=True)
    is_active: Mapped[bool] = mapped_column(default=True)
    
    # Relationships
    student_relationships: Mapped[list["StudentParentRelationship"]] = relationship(
        back_populates="parent_guardian",
        cascade="all, delete-orphan",
        lazy="select",
    )
    
    __table_args__ = (
        UniqueConstraint("school_id", "id_number", name="uq_parent_id_number"),
        Index("idx_parent_school_active", "school_id", "is_active"),
    )


class StudentParentRelationship(AuditableBase, TenantMixin):
    """
    M:N association between Student and ParentGuardian.
    
    Attributes:
        school_id: Tenant identifier
        student_id: FK to Student
        parent_guardian_id: FK to ParentGuardian
        relationship_type: MOTHER/FATHER/GUARDIAN/OTHER
        is_primary: Primary contact (only one per student)
        emergency_contact: Is emergency contact
    """
    __tablename__ = "student_parent_relationships"
    
    student_id: Mapped[UUID] = mapped_column(ForeignKey("students.id", ondelete="CASCADE"))
    parent_guardian_id: Mapped[UUID] = mapped_column(ForeignKey("parent_guardians.id", ondelete="CASCADE"))
    relationship_type: Mapped[RelationshipType] = mapped_column(SQLEnum(RelationshipType))
    is_primary: Mapped[bool] = mapped_column(default=False, comment="Primary contact for student")
    emergency_contact: Mapped[bool] = mapped_column(default=False)
    
    # Relationships
    student: Mapped["Student"] = relationship(back_populates="parent_relationships")
    parent_guardian: Mapped["ParentGuardian"] = relationship(back_populates="student_relationships")
    
    __table_args__ = (
        UniqueConstraint("school_id", "student_id", "parent_guardian_id", name="uq_student_parent_relationship"),
        Index("idx_student_parent_student", "student_id"),
        Index("idx_student_parent_parent", "parent_guardian_id"),
    )


class StudentClearance(AuditableBase, TenantMixin):
    """
    Student exit clearance record.
    
    Tracks clearance status when student is leaving (graduation, transfer, withdrawal).
    Must check: unpaid fees, unreturned library books, unreturned sports gear.
    
    Attributes:
        school_id: Tenant identifier
        student_id: FK to Student
        status: PENDING/CLEARED/PARTIALLY_CLEARED
        initiated_date: When clearance was initiated
        cleared_date: When fully cleared (null if not cleared)
        has_fee_balance: Whether student has unpaid fees
        has_library_books: Whether student has unreturned library books
        has_sports_gear: Whether student has unreturned sports gear
        remarks: Additional notes
    """
    __tablename__ = "student_clearances"
    
    student_id: Mapped[UUID] = mapped_column(ForeignKey("students.id", ondelete="CASCADE"))
    status: Mapped[ClearanceStatus] = mapped_column(SQLEnum(ClearanceStatus), default=ClearanceStatus.PENDING)
    initiated_date: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    cleared_date: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)
    has_fee_balance: Mapped[bool] = mapped_column(default=False)
    has_library_books: Mapped[bool] = mapped_column(default=False)
    has_sports_gear: Mapped[bool] = mapped_column(default=False)
    remarks: Mapped[str | None] = mapped_column(Text, nullable=True)
    
    # Relationships
    student: Mapped["Student"] = relationship(back_populates="clearances")
    
    __table_args__ = (
        Index("idx_clearance_student", "student_id"),
        Index("idx_clearance_status", "status"),
    )


class StudentTransfer(AuditableBase, TenantMixin):
    """
    Inter-school transfer record.
    
    Tracks when student transfers from/to another school.
    
    Attributes:
        school_id: Current school (tenant)
        student_id: FK to Student
        transfer_from_school: Name of previous school (if incoming transfer)
        transfer_to_school: Name of new school (if outgoing transfer)
        transfer_date: Date of transfer
        reason: Reason for transfer
        status: INITIATED/APPROVED/COMPLETED/REJECTED
    """
    __tablename__ = "student_transfers"
    
    student_id: Mapped[UUID] = mapped_column(ForeignKey("students.id", ondelete="CASCADE"))
    transfer_from_school: Mapped[str | None] = mapped_column(String(255), nullable=True)
    transfer_to_school: Mapped[str | None] = mapped_column(String(255), nullable=True)
    transfer_date: Mapped[date] = mapped_column(Date)
    reason: Mapped[str | None] = mapped_column(Text, nullable=True)
    status: Mapped[str] = mapped_column(String(50), default="INITIATED")
    
    # Relationships
    student: Mapped["Student"] = relationship(back_populates="transfers")
    
    __table_args__ = (
        Index("idx_transfer_student", "student_id"),
        Index("idx_transfer_status", "status"),
    )


# Forward reference declarations (for cross-module imports)
# These are populated by actual imports in the services
StudentClassEnrollment = None
FeeAccount = None
