"""
SQLAlchemy ORM models for HR and Payroll System.

Models:
- Staff: Employee records with KRA PIN, TSC Number, employment type
- PayrollRun: Monthly payroll batches with status tracking
- PayrollEntry: Individual staff salary records for a payroll run
- PayrollAllowance: Additional allowances (e.g., hardship, responsibility)
- PayrollDeduction: Additional deductions (e.g., HELB, SACCO, loans)
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

from src.core.models import AuditableBase, TenantMixin


class EmploymentType(str, Enum):
    """Employment type classification."""
    BOM = "BOM"  # Board of Management (contract/non-tenured)
    TSC = "TSC"  # Teachers Service Commission (tenured)


class PayrollStatus(str, Enum):
    """Payroll run status."""
    DRAFT = "DRAFT"
    APPROVED = "APPROVED"
    PROCESSED = "PROCESSED"
    PAID = "PAID"
    CANCELLED = "CANCELLED"


class Staff(AuditableBase, TenantMixin):
    """
    Staff member (employee) record.
    
    Attributes:
        school_id: Tenant identifier (FK to schools)
        user_id: Link to User account (optional, for login)
        first_name: Employee first name
        last_name: Employee last name
        email: Work email
        phone: Phone number
        employee_number: Unique per school
        employment_type: BOM or TSC
        kra_pin: KRA Personal Identification Number (required for tax)
        tsc_number: TSC Number (for TSC-employed staff)
        bank_account: Bank account number for salary
        bank_name: Bank name
        id_number: National ID
        basic_pay: Base monthly salary (Decimal)
        is_active: Active/inactive status
    """
    __tablename__ = "staff"
    
    user_id: Mapped[UUID | None] = mapped_column(
        ForeignKey("users.id", ondelete="SET NULL"),
        nullable=True,
    )
    first_name: Mapped[str] = mapped_column(String(100))
    last_name: Mapped[str] = mapped_column(String(100))
    email: Mapped[str | None] = mapped_column(String(255), nullable=True)
    phone: Mapped[str | None] = mapped_column(String(20), nullable=True)
    employee_number: Mapped[str] = mapped_column(String(50))
    employment_type: Mapped[EmploymentType] = mapped_column(SQLEnum(EmploymentType))
    kra_pin: Mapped[str] = mapped_column(String(20), comment="KRA Personal Identification Number")
    tsc_number: Mapped[str | None] = mapped_column(String(20), nullable=True, comment="TSC Number for TSC staff")
    bank_account: Mapped[str | None] = mapped_column(String(50), nullable=True)
    bank_name: Mapped[str | None] = mapped_column(String(100), nullable=True)
    id_number: Mapped[str | None] = mapped_column(String(20), nullable=True)
    basic_pay: Mapped[Decimal] = mapped_column(
        Numeric(15, 2),
        comment="Monthly basic salary",
    )
    is_active: Mapped[bool] = mapped_column(default=True)
    
    # Relationships
    payroll_entries: Mapped[list["PayrollEntry"]] = relationship(
        back_populates="staff",
        cascade="all, delete-orphan",
        lazy="select",
    )
    allowances: Mapped[list["PayrollAllowance"]] = relationship(
        back_populates="staff",
        cascade="all, delete-orphan",
        lazy="select",
    )
    deductions: Mapped[list["PayrollDeduction"]] = relationship(
        back_populates="staff",
        cascade="all, delete-orphan",
        lazy="select",
    )
    
    __table_args__ = (
        UniqueConstraint("school_id", "employee_number", name="uq_staff_employee_number"),
        UniqueConstraint("school_id", "kra_pin", name="uq_staff_kra_pin"),
        CheckConstraint("basic_pay > 0", name="ck_staff_basic_pay_positive"),
        Index("idx_staff_school_active", "school_id", "is_active"),
        Index("idx_staff_employment_type", "employment_type"),
    )


class PayrollRun(AuditableBase, TenantMixin):
    """
    Monthly payroll batch processing record.
    
    Attributes:
        school_id: Tenant identifier
        period_month: Month (1-12)
        period_year: Year (e.g., 2024)
        status: DRAFT, APPROVED, PROCESSED, PAID, CANCELLED
        description: Optional notes about this run
        processed_by: User ID who processed
        processed_at: Timestamp of processing
        approved_by: User ID who approved
        approved_at: Timestamp of approval
        total_gross_pay: Sum of all gross salaries in run
        total_net_pay: Sum of all net salaries in run
        total_paye_deducted: Sum of PAYE deductions
        total_nssf_deducted: Sum of NSSF deductions
        total_sha_deducted: Sum of SHA/NHIF deductions
    """
    __tablename__ = "payroll_runs"
    
    period_month: Mapped[int] = mapped_column(comment="Month 1-12")
    period_year: Mapped[int] = mapped_column(comment="Year e.g. 2024")
    status: Mapped[PayrollStatus] = mapped_column(SQLEnum(PayrollStatus), default=PayrollStatus.DRAFT)
    description: Mapped[str | None] = mapped_column(Text, nullable=True)
    processed_by: Mapped[UUID | None] = mapped_column(
        ForeignKey("users.id", ondelete="SET NULL"),
        nullable=True,
    )
    processed_at: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)
    approved_by: Mapped[UUID | None] = mapped_column(
        ForeignKey("users.id", ondelete="SET NULL"),
        nullable=True,
    )
    approved_at: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)
    total_gross_pay: Mapped[Decimal] = mapped_column(Numeric(15, 2), default=Decimal("0.00"))
    total_net_pay: Mapped[Decimal] = mapped_column(Numeric(15, 2), default=Decimal("0.00"))
    total_paye_deducted: Mapped[Decimal] = mapped_column(Numeric(15, 2), default=Decimal("0.00"))
    total_nssf_deducted: Mapped[Decimal] = mapped_column(Numeric(15, 2), default=Decimal("0.00"))
    total_sha_deducted: Mapped[Decimal] = mapped_column(Numeric(15, 2), default=Decimal("0.00"))
    total_housing_levy_deducted: Mapped[Decimal] = mapped_column(Numeric(15, 2), default=Decimal("0.00"))
    
    # Relationships
    entries: Mapped[list["PayrollEntry"]] = relationship(
        back_populates="payroll_run",
        cascade="all, delete-orphan",
        lazy="select",
    )
    
    __table_args__ = (
        UniqueConstraint("school_id", "period_month", "period_year", name="uq_payroll_run_period"),
        CheckConstraint("period_month >= 1 AND period_month <= 12", name="ck_payroll_run_month"),
        CheckConstraint("period_year >= 2000", name="ck_payroll_run_year"),
        Index("idx_payroll_run_status", "status"),
        Index("idx_payroll_run_period", "period_year", "period_month"),
    )


class PayrollEntry(AuditableBase, TenantMixin):
    """
    Individual staff salary record for a payroll run.
    
    CRITICAL: This stores the complete salary breakdown for one staff member
    in one payroll period. All amounts are calculated per statutory requirements.
    
    Attributes:
        school_id: Tenant identifier
        payroll_run_id: FK to PayrollRun
        staff_id: FK to Staff
        basic_pay: Basic monthly salary (copied from Staff at run time)
        total_allowances: Sum of all allowances (PayrollAllowance records)
        gross_pay: basic_pay + total_allowances
        nssf_tier1: NSSF Tier 1 deduction (6% of pensionable, capped at 7,000)
        nssf_tier2: NSSF Tier 2 deduction (6% of pensionable, capped at 29,000)
        sha_nhif: SHA/NHIF deduction (2.75% of gross)
        housing_levy: Housing Levy deduction (1.5% of gross)
        taxable_pay: Gross - NSSF (Tier 1 + Tier 2)
        paye: PAYE tax calculated on taxable_pay, minus personal relief
        total_statutory_deductions: NSSF + SHA + Housing Levy + PAYE
        total_other_deductions: Sum of PayrollDeduction records
        net_pay: Gross - All deductions
        is_locked: Whether this entry can be edited
    """
    __tablename__ = "payroll_entries"
    
    payroll_run_id: Mapped[UUID] = mapped_column(ForeignKey("payroll_runs.id", ondelete="CASCADE"))
    staff_id: Mapped[UUID] = mapped_column(ForeignKey("staff.id", ondelete="RESTRICT"))
    
    # Income components
    basic_pay: Mapped[Decimal] = mapped_column(Numeric(15, 2))
    total_allowances: Mapped[Decimal] = mapped_column(Numeric(15, 2), default=Decimal("0.00"))
    gross_pay: Mapped[Decimal] = mapped_column(Numeric(15, 2), comment="basic_pay + allowances")
    
    # Statutory deductions
    nssf_tier1: Mapped[Decimal] = mapped_column(Numeric(15, 2), default=Decimal("0.00"), comment="6% pensionable, capped 7,000")
    nssf_tier2: Mapped[Decimal] = mapped_column(Numeric(15, 2), default=Decimal("0.00"), comment="6% pensionable, capped 29,000")
    sha_nhif: Mapped[Decimal] = mapped_column(Numeric(15, 2), default=Decimal("0.00"), comment="2.75% of gross")
    housing_levy: Mapped[Decimal] = mapped_column(Numeric(15, 2), default=Decimal("0.00"), comment="1.5% of gross")
    taxable_pay: Mapped[Decimal] = mapped_column(Numeric(15, 2), comment="Gross - NSSF tiers")
    paye: Mapped[Decimal] = mapped_column(Numeric(15, 2), comment="PAYE after KRA bands and personal relief")
    total_statutory_deductions: Mapped[Decimal] = mapped_column(
        Numeric(15, 2),
        default=Decimal("0.00"),
        comment="NSSF + SHA + Housing + PAYE",
    )
    
    # Other deductions
    total_other_deductions: Mapped[Decimal] = mapped_column(Numeric(15, 2), default=Decimal("0.00"))
    
    # Net pay
    net_pay: Mapped[Decimal] = mapped_column(Numeric(15, 2), comment="Gross - All deductions")
    
    # Lock status
    is_locked: Mapped[bool] = mapped_column(default=False, comment="Cannot edit if locked")
    
    # Relationships
    payroll_run: Mapped["PayrollRun"] = relationship(back_populates="entries")
    staff: Mapped["Staff"] = relationship(back_populates="payroll_entries")
    allowance_lines: Mapped[list["PayrollAllowance"]] = relationship(
        back_populates="payroll_entry",
        cascade="all, delete-orphan",
        lazy="select",
    )
    deduction_lines: Mapped[list["PayrollDeduction"]] = relationship(
        back_populates="payroll_entry",
        cascade="all, delete-orphan",
        lazy="select",
    )
    
    __table_args__ = (
        UniqueConstraint("school_id", "payroll_run_id", "staff_id", name="uq_payroll_entry_staff_run"),
        CheckConstraint("basic_pay >= 0", name="ck_payroll_entry_basic_pay"),
        CheckConstraint("gross_pay >= 0", name="ck_payroll_entry_gross_pay"),
        CheckConstraint("net_pay >= 0", name="ck_payroll_entry_net_pay"),
        Index("idx_payroll_entry_run", "payroll_run_id"),
        Index("idx_payroll_entry_staff", "staff_id"),
    )


class PayrollAllowance(AuditableBase, TenantMixin):
    """
    Additional allowances for a staff member in a payroll run.
    
    Examples:
    - Hardship allowance
    - Responsibility allowance
    - Housing allowance
    - Transport allowance
    
    Attributes:
        school_id: Tenant identifier
        payroll_entry_id: FK to PayrollEntry
        staff_id: FK to Staff (denormalized for query efficiency)
        allowance_type: Name of allowance (e.g., "Hardship")
        amount: Amount in KES
        description: Optional notes
    """
    __tablename__ = "payroll_allowances"
    
    payroll_entry_id: Mapped[UUID] = mapped_column(ForeignKey("payroll_entries.id", ondelete="CASCADE"))
    staff_id: Mapped[UUID] = mapped_column(ForeignKey("staff.id", ondelete="CASCADE"))
    allowance_type: Mapped[str] = mapped_column(String(100))
    amount: Mapped[Decimal] = mapped_column(Numeric(15, 2))
    description: Mapped[str | None] = mapped_column(Text, nullable=True)
    
    # Relationships
    payroll_entry: Mapped["PayrollEntry"] = relationship(back_populates="allowance_lines")
    staff: Mapped["Staff"] = relationship(back_populates="allowances")
    
    __table_args__ = (
        CheckConstraint("amount >= 0", name="ck_payroll_allowance_amount"),
        Index("idx_payroll_allowance_entry", "payroll_entry_id"),
        Index("idx_payroll_allowance_staff", "staff_id"),
    )


class PayrollDeduction(AuditableBase, TenantMixin):
    """
    Additional deductions for a staff member in a payroll run.
    
    Examples:
    - HELB loan repayment
    - SACCO savings
    - Staff loan
    - Insurance premium
    - Union dues
    
    Attributes:
        school_id: Tenant identifier
        payroll_entry_id: FK to PayrollEntry
        staff_id: FK to Staff (denormalized)
        deduction_type: Type of deduction (e.g., "HELB")
        amount: Amount in KES
        description: Optional notes
    """
    __tablename__ = "payroll_deductions"
    
    payroll_entry_id: Mapped[UUID] = mapped_column(ForeignKey("payroll_entries.id", ondelete="CASCADE"))
    staff_id: Mapped[UUID] = mapped_column(ForeignKey("staff.id", ondelete="CASCADE"))
    deduction_type: Mapped[str] = mapped_column(String(100))
    amount: Mapped[Decimal] = mapped_column(Numeric(15, 2))
    description: Mapped[str | None] = mapped_column(Text, nullable=True)
    
    # Relationships
    payroll_entry: Mapped["PayrollEntry"] = relationship(back_populates="deduction_lines")
    staff: Mapped["Staff"] = relationship(back_populates="deductions")
    
    __table_args__ = (
        CheckConstraint("amount >= 0", name="ck_payroll_deduction_amount"),
        Index("idx_payroll_deduction_entry", "payroll_entry_id"),
        Index("idx_payroll_deduction_staff", "staff_id"),
    )
