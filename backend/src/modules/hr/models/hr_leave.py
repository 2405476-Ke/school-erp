"""
SQLAlchemy ORM models for HR Leave Management and Biometric Attendance.

Models:
- LeaveRequest: Staff leave applications with two-tier approval workflow
- LeaveBalance: Annual leave entitlements and usage tracking per staff
- AttendanceRecord: Daily biometric clock-in/out records for staff
"""

from decimal import Decimal
from datetime import datetime, date
from uuid import UUID
from enum import Enum

from sqlalchemy import (
    ForeignKey,
    Index,
    UniqueConstraint,
    Numeric,
    String,
    Integer,
    Boolean,
    Date,
    DateTime,
    Text,
    Enum as SQLEnum,
)
from sqlalchemy.orm import Mapped, mapped_column, relationship

from src.shared.base_model import AuditableBase, TenantMixin


class LeaveType(str, Enum):
    """Types of leave available to staff."""
    ANNUAL = "ANNUAL"
    SICK = "SICK"
    COMPASSIONATE = "COMPASSIONATE"
    MATERNITY = "MATERNITY"
    PATERNITY = "PATERNITY"


class LeaveStatus(str, Enum):
    """Leave request approval workflow statuses."""
    PENDING = "PENDING"
    APPROVED_TIER1 = "APPROVED_TIER1"   # Deputy Principal approved
    APPROVED = "APPROVED"               # Principal fully approved
    REJECTED = "REJECTED"
    CANCELLED = "CANCELLED"


class LeaveRequest(AuditableBase, TenantMixin):
    """
    Staff leave application record with two-tier approval workflow.

    Tier 1 approval: Deputy Principal
    Tier 2 approval: Principal (final approval, deducts from LeaveBalance)

    Attributes:
        school_id: Tenant identifier (FK to schools)
        staff_id: FK to Staff
        leave_type: ANNUAL, SICK, COMPASSIONATE, MATERNITY, or PATERNITY
        from_date: First day of leave
        to_date: Last day of leave
        reason: Staff's stated reason for the leave
        status: Workflow status (PENDING -> APPROVED_TIER1 -> APPROVED)
        tier1_approved_by_id: Deputy Principal who approved at Tier 1
        tier1_approved_at: Timestamp of Tier 1 approval
        tier2_approved_by_id: Principal who gave final approval
        tier2_approved_at: Timestamp of final approval
        rejection_reason: Reason recorded when leave is rejected
    """
    __tablename__ = "leave_requests"

    staff_id: Mapped[UUID] = mapped_column(
        ForeignKey("staff.id", ondelete="RESTRICT"),
        nullable=False,
    )
    leave_type: Mapped[str] = mapped_column(
        SQLEnum(LeaveType, name="leavetype"),
        nullable=False,
    )
    from_date: Mapped[date] = mapped_column(Date, nullable=False)
    to_date: Mapped[date] = mapped_column(Date, nullable=False)
    reason: Mapped[str] = mapped_column(Text, nullable=False)
    status: Mapped[str] = mapped_column(
        SQLEnum(LeaveStatus, name="leavestatus"),
        default=LeaveStatus.PENDING,
        nullable=False,
    )
    tier1_approved_by_id: Mapped[UUID | None] = mapped_column(
        ForeignKey("users.id", ondelete="SET NULL"),
        nullable=True,
    )
    tier1_approved_at: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)
    tier2_approved_by_id: Mapped[UUID | None] = mapped_column(
        ForeignKey("users.id", ondelete="SET NULL"),
        nullable=True,
    )
    tier2_approved_at: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)
    rejection_reason: Mapped[str | None] = mapped_column(Text, nullable=True)

    # Relationships
    staff: Mapped["Staff"] = relationship(
        "Staff",
        foreign_keys=[staff_id],
        lazy="select",
    )

    __table_args__ = (
        Index("idx_leave_request_staff", "staff_id"),
        Index("idx_leave_request_school_status", "school_id", "status"),
        Index("idx_leave_request_dates", "from_date", "to_date"),
    )


class LeaveBalance(AuditableBase, TenantMixin):
    """
    Annual leave entitlement and usage tracking per staff member.

    Attributes:
        school_id: Tenant identifier
        staff_id: FK to Staff
        year: Calendar year (e.g., 2024)
        leave_type: Type of leave this balance applies to
        entitled_days: Total days granted for the year
        used_days: Days consumed (incremented on final approval)
    """
    __tablename__ = "leave_balances"

    staff_id: Mapped[UUID] = mapped_column(
        ForeignKey("staff.id", ondelete="RESTRICT"),
        nullable=False,
    )
    year: Mapped[int] = mapped_column(Integer, nullable=False, comment="Calendar year")
    leave_type: Mapped[str] = mapped_column(
        SQLEnum(LeaveType, name="leavetype"),
        nullable=False,
    )
    entitled_days: Mapped[Decimal] = mapped_column(
        Numeric(5, 1),
        nullable=False,
        comment="Total days entitled for the year",
    )
    used_days: Mapped[Decimal] = mapped_column(
        Numeric(5, 1),
        default=Decimal("0.0"),
        nullable=False,
        comment="Days consumed so far",
    )

    # Relationships
    staff: Mapped["Staff"] = relationship(
        "Staff",
        foreign_keys=[staff_id],
        lazy="select",
    )

    __table_args__ = (
        UniqueConstraint(
            "school_id", "staff_id", "year", "leave_type",
            name="uq_leave_balance_staff_year_type",
        ),
        Index("idx_leave_balance_staff_year", "staff_id", "year"),
    )


class AttendanceRecord(AuditableBase, TenantMixin):
    """
    Daily biometric attendance record for a staff member.

    Attributes:
        school_id: Tenant identifier
        staff_id: FK to Staff
        attendance_date: The calendar date of this record
        clock_in: DateTime when the staff member clocked in
        clock_out: DateTime when the staff member clocked out
        source: Origin of the record (default: BIOMETRIC)
        biometric_device_id: Identifier of the device that logged the event
        is_present: False if staff was absent for the day
        notes: Optional remarks (e.g., approved late-in reason)
    """
    __tablename__ = "staff_attendance"

    staff_id: Mapped[UUID] = mapped_column(
        ForeignKey("staff.id", ondelete="RESTRICT"),
        nullable=False,
    )
    attendance_date: Mapped[date] = mapped_column(Date, nullable=False)
    clock_in: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)
    clock_out: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)
    source: Mapped[str] = mapped_column(
        String(30),
        default="BIOMETRIC",
        nullable=False,
        comment="BIOMETRIC | MANUAL | SYSTEM",
    )
    biometric_device_id: Mapped[str | None] = mapped_column(String(50), nullable=True)
    is_present: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    notes: Mapped[str | None] = mapped_column(Text, nullable=True)

    # Relationships
    staff: Mapped["Staff"] = relationship(
        "Staff",
        foreign_keys=[staff_id],
        lazy="select",
    )

    __table_args__ = (
        UniqueConstraint(
            "school_id", "staff_id", "attendance_date",
            name="uq_attendance_staff_date",
        ),
        Index("idx_attendance_staff_date", "staff_id", "attendance_date"),
        Index("idx_attendance_school_date", "school_id", "attendance_date"),
    )