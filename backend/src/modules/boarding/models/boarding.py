"""
SQLAlchemy ORM models for Boarding and Discipline System.

Models:
- Hostel: Residential houses (e.g., Serengeti House)
- Dormitory: Wings/units within hostels
- Bed: Physical bed allocations
- BedAllocation: Student-to-bed mapping with dates
- StudentLeavePass: Exeat passes with security tracking
- DisciplinaryIncident: Infraction records
- DisciplinaryAction: Disciplinary measures taken
"""

from datetime import datetime, date, time
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
    Time,
    Text,
    Enum as SQLEnum,
)
from sqlalchemy.orm import Mapped, mapped_column, relationship

from src.core.models import AuditableBase, TenantMixin


class ExeatType(str, Enum):
    """Type of leave/exeat pass."""
    DAY_OUT = "DAY_OUT"  # Same day return
    OVERNIGHT = "OVERNIGHT"  # Single night out
    WEEKEND = "WEEKEND"  # Weekend leave
    HOLIDAY = "HOLIDAY"  # Holiday break
    MEDICAL = "MEDICAL"  # Medical appointment/emergency
    BEREAVEMENT = "BEREAVEMENT"  # Family emergency
    SPECIAL = "SPECIAL"  # Special circumstances


class LeavePassStatus(str, Enum):
    """Status of leave pass."""
    REQUESTED = "REQUESTED"
    APPROVED = "APPROVED"
    REJECTED = "REJECTED"
    DEPARTED = "DEPARTED"
    RETURNED = "RETURNED"
    EXTENDED = "EXTENDED"
    EXPIRED = "EXPIRED"


class DisciplinaryCategory(str, Enum):
    """Category of disciplinary infraction."""
    ACADEMIC = "ACADEMIC"  # Late assignment, poor performance
    CONDUCT = "CONDUCT"  # Disrespect, rudeness
    CURFEW = "CURFEW"  # Breaking curfew rules
    SUBSTANCE = "SUBSTANCE"  # Drugs, alcohol
    SAFETY = "SAFETY"  # Fighting, weapons
    PROPERTY = "PROPERTY"  # Theft, vandalism
    UNIFORM = "UNIFORM"  # Uniform violations
    OTHER = "OTHER"


class DisciplinaryActionType(str, Enum):
    """Type of disciplinary action."""
    WARNING = "WARNING"
    DETENTION = "DETENTION"
    SUSPENSION = "SUSPENSION"
    EXPULSION = "EXPULSION"
    COMMUNITY_SERVICE = "COMMUNITY_SERVICE"
    FINE = "FINE"
    RESTRICTION = "RESTRICTION"  # Restricted movement/activities
    COUNSELING = "COUNSELING"


class Hostel(AuditableBase, TenantMixin):
    """
    Residential hostel/house.
    
    Attributes:
        school_id: Tenant identifier
        name: Hostel name (e.g., Serengeti House)
        code: Hostel code (e.g., SER)
        capacity: Total bed capacity
        current_occupancy: Current number of occupied beds
        matron_staff_id: FK to Staff (hostel matron/administrator)
        description: Additional details
        is_active: Active/inactive status
    """
    __tablename__ = "hostels"
    
    name: Mapped[str] = mapped_column(String(100))
    code: Mapped[str] = mapped_column(String(10))
    capacity: Mapped[int] = mapped_column(Integer)
    current_occupancy: Mapped[int] = mapped_column(Integer, default=0)
    matron_staff_id: Mapped[UUID | None] = mapped_column(
        ForeignKey("staff.id", ondelete="SET NULL"),
        nullable=True,
    )
    description: Mapped[str | None] = mapped_column(Text, nullable=True)
    is_active: Mapped[bool] = mapped_column(default=True)
    
    # Relationships
    dormitories: Mapped[list["Dormitory"]] = relationship(
        back_populates="hostel",
        cascade="all, delete-orphan",
        lazy="select",
    )
    
    __table_args__ = (
        UniqueConstraint("school_id", "name", name="uq_hostel_name"),
        UniqueConstraint("school_id", "code", name="uq_hostel_code"),
        CheckConstraint("capacity > 0", name="ck_hostel_capacity_positive"),
        CheckConstraint("current_occupancy >= 0 AND current_occupancy <= capacity", name="ck_hostel_occupancy_valid"),
        Index("idx_hostel_school_active", "school_id", "is_active"),
    )


class Dormitory(AuditableBase, TenantMixin):
    """
    Dormitory/wing within hostel.
    
    Attributes:
        school_id: Tenant identifier
        hostel_id: FK to Hostel
        name: Dormitory name (e.g., Wing A)
        capacity: Bed capacity in this dormitory
        current_occupancy: Currently occupied beds
        is_active: Active/inactive
    """
    __tablename__ = "dormitories"
    
    hostel_id: Mapped[UUID] = mapped_column(ForeignKey("hostels.id", ondelete="CASCADE"))
    name: Mapped[str] = mapped_column(String(100))
    capacity: Mapped[int] = mapped_column(Integer)
    current_occupancy: Mapped[int] = mapped_column(Integer, default=0)
    is_active: Mapped[bool] = mapped_column(default=True)
    
    # Relationships
    hostel: Mapped["Hostel"] = relationship(back_populates="dormitories")
    beds: Mapped[list["Bed"]] = relationship(
        back_populates="dormitory",
        cascade="all, delete-orphan",
        lazy="select",
    )
    
    __table_args__ = (
        UniqueConstraint("school_id", "hostel_id", "name", name="uq_dormitory_name"),
        CheckConstraint("capacity > 0", name="ck_dormitory_capacity_positive"),
        CheckConstraint("current_occupancy >= 0 AND current_occupancy <= capacity", name="ck_dormitory_occupancy_valid"),
        Index("idx_dormitory_hostel", "hostel_id"),
    )


class Bed(AuditableBase, TenantMixin):
    """
    Physical bed in dormitory.
    
    Attributes:
        school_id: Tenant identifier
        dormitory_id: FK to Dormitory
        bed_number: Bed identifier (e.g., "A-01")
        is_occupied: Whether bed is currently occupied
        is_active: Bed is available for allocation
    """
    __tablename__ = "beds"
    
    dormitory_id: Mapped[UUID] = mapped_column(ForeignKey("dormitories.id", ondelete="CASCADE"))
    bed_number: Mapped[str] = mapped_column(String(20))
    is_occupied: Mapped[bool] = mapped_column(default=False)
    is_active: Mapped[bool] = mapped_column(default=True, comment="Bed is available for allocation")
    
    # Relationships
    dormitory: Mapped["Dormitory"] = relationship(back_populates="beds")
    allocations: Mapped[list["BedAllocation"]] = relationship(
        back_populates="bed",
        cascade="all, delete-orphan",
        lazy="select",
    )
    
    __table_args__ = (
        UniqueConstraint("school_id", "dormitory_id", "bed_number", name="uq_bed_number"),
        Index("idx_bed_dormitory", "dormitory_id"),
        Index("idx_bed_occupied", "is_occupied"),
    )


class BedAllocation(AuditableBase, TenantMixin):
    """
    Allocation of bed to student.
    
    CRITICAL: Tracks which student occupies which bed for what period.
    
    Attributes:
        school_id: Tenant identifier
        student_id: FK to Student
        bed_id: FK to Bed
        start_date: Allocation start date
        end_date: Allocation end date (null if ongoing)
        is_active: Currently active allocation
    """
    __tablename__ = "bed_allocations"
    
    student_id: Mapped[UUID] = mapped_column(ForeignKey("students.id", ondelete="CASCADE"))
    bed_id: Mapped[UUID] = mapped_column(ForeignKey("beds.id", ondelete="RESTRICT"))
    start_date: Mapped[date] = mapped_column(Date)
    end_date: Mapped[date | None] = mapped_column(Date, nullable=True, comment="Null if ongoing")
    is_active: Mapped[bool] = mapped_column(default=True)
    
    # Relationships
    student: Mapped["Student"] = relationship()
    bed: Mapped["Bed"] = relationship(back_populates="allocations")
    
    __table_args__ = (
        UniqueConstraint("school_id", "student_id", "start_date", name="uq_bed_allocation_student_date"),
        CheckConstraint("end_date IS NULL OR end_date >= start_date", name="ck_bed_allocation_dates_valid"),
        Index("idx_bed_allocation_student", "student_id"),
        Index("idx_bed_allocation_bed", "bed_id"),
        Index("idx_bed_allocation_active", "is_active"),
    )


class StudentLeavePass(AuditableBase, TenantMixin):
    """
    Leave/exeat pass for student departure from school.
    
    CRITICAL SECURITY: Enforces who can leave compound and when.
    Gate/Security module calls verify_gate_exit() before allowing departure.
    
    Attributes:
        school_id: Tenant identifier
        student_id: FK to Student
        exeat_type: DAY_OUT/OVERNIGHT/WEEKEND/HOLIDAY/MEDICAL/BEREAVEMENT/SPECIAL
        reason: Reason for leave
        departure_time: When student left (null until departure)
        expected_return_time: When student is expected back
        actual_return_time: When student actually returned (null if not returned)
        status: REQUESTED/APPROVED/REJECTED/DEPARTED/RETURNED/EXTENDED/EXPIRED
        requested_date: When pass was requested
        approved_by: User ID who approved (null if not approved)
        approved_date: When approved (null if not approved)
        destination: Where student is going
        contact_person_name: Emergency contact while away
        contact_person_phone: Emergency contact phone
    """
    __tablename__ = "student_leave_passes"
    
    student_id: Mapped[UUID] = mapped_column(ForeignKey("students.id", ondelete="CASCADE"))
    exeat_type: Mapped[ExeatType] = mapped_column(SQLEnum(ExeatType))
    reason: Mapped[str] = mapped_column(Text)
    departure_time: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)
    expected_return_time: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)
    actual_return_time: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)
    status: Mapped[LeavePassStatus] = mapped_column(SQLEnum(LeavePassStatus), default=LeavePassStatus.REQUESTED)
    requested_date: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    approved_by: Mapped[UUID | None] = mapped_column(
        ForeignKey("users.id", ondelete="SET NULL"),
        nullable=True,
    )
    approved_date: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)
    destination: Mapped[str | None] = mapped_column(String(255), nullable=True)
    contact_person_name: Mapped[str | None] = mapped_column(String(100), nullable=True)
    contact_person_phone: Mapped[str | None] = mapped_column(String(20), nullable=True)
    
    # Relationships
    student: Mapped["Student"] = relationship()
    
    __table_args__ = (
        Index("idx_leave_pass_student", "student_id"),
        Index("idx_leave_pass_status", "status"),
        Index("idx_leave_pass_departure", "departure_time"),
    )


class DisciplinaryIncident(AuditableBase, TenantMixin):
    """
    Disciplinary infraction record.
    
    Attributes:
        school_id: Tenant identifier
        student_id: FK to Student
        category: ACADEMIC/CONDUCT/CURFEW/SUBSTANCE/SAFETY/PROPERTY/UNIFORM/OTHER
        description: Detailed description of incident
        incident_date: When the incident occurred
        reported_by_staff_id: FK to Staff who reported
        reported_date: When reported (auto-set to now)
        location: Where incident occurred
        witnesses: Names of witnesses
        severity: 1-5 (1=minor, 5=critical)
    """
    __tablename__ = "disciplinary_incidents"
    
    student_id: Mapped[UUID] = mapped_column(ForeignKey("students.id", ondelete="CASCADE"))
    category: Mapped[DisciplinaryCategory] = mapped_column(SQLEnum(DisciplinaryCategory))
    description: Mapped[str] = mapped_column(Text)
    incident_date: Mapped[date] = mapped_column(Date)
    reported_by_staff_id: Mapped[UUID | None] = mapped_column(
        ForeignKey("staff.id", ondelete="SET NULL"),
        nullable=True,
    )
    reported_date: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    location: Mapped[str | None] = mapped_column(String(255), nullable=True)
    witnesses: Mapped[str | None] = mapped_column(Text, nullable=True)
    severity: Mapped[int] = mapped_column(Integer, comment="1-5, 1=minor, 5=critical")
    
    # Relationships
    student: Mapped["Student"] = relationship()
    disciplinary_actions: Mapped[list["DisciplinaryAction"]] = relationship(
        back_populates="incident",
        cascade="all, delete-orphan",
        lazy="select",
    )
    
    __table_args__ = (
        CheckConstraint("severity >= 1 AND severity <= 5", name="ck_incident_severity"),
        Index("idx_incident_student", "student_id"),
        Index("idx_incident_category", "category"),
        Index("idx_incident_date", "incident_date"),
    )


class DisciplinaryAction(AuditableBase, TenantMixin):
    """
    Disciplinary action taken in response to incident.
    
    Attributes:
        school_id: Tenant identifier
        incident_id: FK to DisciplinaryIncident
        action_type: WARNING/DETENTION/SUSPENSION/EXPULSION/COMMUNITY_SERVICE/FINE/RESTRICTION/COUNSELING
        description: Details of action
        start_date: When action starts
        end_date: When action ends (null if permanent)
        issued_by_staff_id: FK to Staff who issued action
        issued_date: When action was issued
        reason: Justification for action
    """
    __tablename__ = "disciplinary_actions"
    
    incident_id: Mapped[UUID] = mapped_column(ForeignKey("disciplinary_incidents.id", ondelete="CASCADE"))
    action_type: Mapped[DisciplinaryActionType] = mapped_column(SQLEnum(DisciplinaryActionType))
    description: Mapped[str] = mapped_column(Text)
    start_date: Mapped[date] = mapped_column(Date)
    end_date: Mapped[date | None] = mapped_column(Date, nullable=True)
    issued_by_staff_id: Mapped[UUID | None] = mapped_column(
        ForeignKey("staff.id", ondelete="SET NULL"),
        nullable=True,
    )
    issued_date: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    reason: Mapped[str] = mapped_column(Text)
    
    # Relationships
    incident: Mapped["DisciplinaryIncident"] = relationship(back_populates="disciplinary_actions")
    
    __table_args__ = (
        CheckConstraint("end_date IS NULL OR end_date >= start_date", name="ck_action_dates_valid"),
        Index("idx_action_incident", "incident_id"),
        Index("idx_action_type", "action_type"),
    )


# Forward references for cross-module imports
Student = None
