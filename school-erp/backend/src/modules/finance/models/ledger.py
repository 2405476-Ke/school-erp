"""
Finance module: SQLAlchemy models for Chart of Accounts, General Ledger, and accounting infrastructure.
Double-entry accounting system with strict business rule enforcement at the database level.
"""
from datetime import datetime, timezone
from decimal import Decimal
from enum import Enum
from typing import List, Optional
from uuid import UUID, uuid4

from sqlalchemy import (
    Boolean,
    CheckConstraint,
    Date,
    DateTime,
    Enum as SQLEnum,
    ForeignKey,
    Index,
    Numeric,
    String,
    Text,
    UniqueConstraint,
    ForeignKeyConstraint,
)
from sqlalchemy.dialects.postgresql import UUID as PG_UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from src.shared.base_model import AuditableBase, TenantMixin, GUID, FK_UUID, SCHOOL_ID


# ============================================================================
# ENUMERATIONS
# ============================================================================


class AccountTypeEnum(str, Enum):
    """Standard accounting account types (IAS 1)."""
    ASSET = "ASSET"
    LIABILITY = "LIABILITY"
    EQUITY = "EQUITY"
    REVENUE = "REVENUE"
    EXPENSE = "EXPENSE"


class PeriodStatusEnum(str, Enum):
    """Period lifecycle states."""
    FUTURE = "FUTURE"
    OPEN = "OPEN"
    CLOSED = "CLOSED"


class JournalStatusEnum(str, Enum):
    """Journal entry lifecycle states."""
    DRAFT = "DRAFT"
    POSTED = "POSTED"
    REVERSED = "REVERSED"


# ============================================================================
# FINANCIAL YEARS & PERIODS
# ============================================================================


class FinancialYear(AuditableBase, TenantMixin):
    """Financial year container for a school."""
    __tablename__ = "financial_years"

    year_name: Mapped[str] = mapped_column(String(20), nullable=False)  # e.g., "2025"
    start_date: Mapped[Date] = mapped_column(Date, nullable=False)
    end_date: Mapped[Date] = mapped_column(Date, nullable=False)
    status: Mapped[str] = mapped_column(String(20), default="OPEN", nullable=False)

    periods: Mapped[List["AccountingPeriod"]] = relationship(
        back_populates="financial_year",
        cascade="all, delete-orphan",
        lazy="selectin",
    )

    __table_args__ = (
        UniqueConstraint("school_id", "year_name", name="uq_financial_year_school_name"),
        CheckConstraint("start_date < end_date", name="ck_financial_year_dates"),
    )


class AccountingPeriod(AuditableBase, TenantMixin):
    """Accounting period (e.g., monthly, quarterly) within a financial year."""
    __tablename__ = "accounting_periods"

    financial_year_id: Mapped[UUID] = mapped_column(
        PG_UUID(as_uuid=True), ForeignKey("financial_years.id", ondelete="CASCADE"), nullable=False
    )
    period_name: Mapped[str] = mapped_column(String(50), nullable=False)  # e.g., "January 2025"
    period_number: Mapped[Optional[int]] = mapped_column(nullable=True)  # 1-12 for month, etc.
    start_date: Mapped[Date] = mapped_column(Date, nullable=False)
    end_date: Mapped[Date] = mapped_column(Date, nullable=False)
    status: Mapped[str] = mapped_column(
        SQLEnum(PeriodStatusEnum, values_callable=lambda x: [e.value for e in x]),
        default=PeriodStatusEnum.FUTURE.value,
        nullable=False,
        index=True,
    )

    financial_year: Mapped[FinancialYear] = relationship(back_populates="periods")
    journal_entries: Mapped[List["JournalEntry"]] = relationship(
        back_populates="period",
        cascade="all, delete-orphan",
    )
    account_balances: Mapped[List["AccountBalance"]] = relationship(
        back_populates="period",
        cascade="all, delete-orphan",
    )

    __table_args__ = (
        UniqueConstraint("school_id", "financial_year_id", "period_number", name="uq_period_school_year_num"),
        CheckConstraint("start_date < end_date", name="ck_accounting_period_dates"),
    )


# ============================================================================
# CHART OF ACCOUNTS
# ============================================================================


class AccountType(AuditableBase):
    """Account types (system-wide, not tenant-scoped)."""
    __tablename__ = "account_types"

    name: Mapped[str] = mapped_column(
        SQLEnum(AccountTypeEnum, values_callable=lambda x: [e.value for e in x]),
        unique=True,
        nullable=False,
    )
    normal_balance: Mapped[str] = mapped_column(
        String(10), nullable=False
    )  # DEBIT or CREDIT (normal balance side)

    categories: Mapped[List["AccountCategory"]] = relationship(
        back_populates="account_type",
        cascade="all, delete-orphan",
    )

    __table_args__ = (
        CheckConstraint("normal_balance IN ('DEBIT', 'CREDIT')", name="ck_account_type_balance"),
    )


class AccountCategory(AuditableBase):
    """Category grouping within account types (system-wide)."""
    __tablename__ = "account_categories"

    account_type_id: Mapped[UUID] = mapped_column(
        PG_UUID(as_uuid=True), ForeignKey("account_types.id", ondelete="CASCADE"), nullable=False
    )
    name: Mapped[str] = mapped_column(String(100), nullable=False)  # e.g., "Current Assets"
    description: Mapped[Optional[str]] = mapped_column(Text)

    account_type: Mapped[AccountType] = relationship(back_populates="categories")
    accounts: Mapped[List["Account"]] = relationship(
        back_populates="category",
        cascade="all, delete-orphan",
    )


class Account(AuditableBase, TenantMixin):
    """Chart of Accounts entry (hierarchical)."""
    __tablename__ = "accounts"

    code: Mapped[str] = mapped_column(String(20), nullable=False, index=True)
    name: Mapped[str] = mapped_column(String(150), nullable=False)
    description: Mapped[Optional[str]] = mapped_column(Text)
    is_control_account: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    is_header: Mapped[bool] = mapped_column(
        Boolean, default=False, nullable=False
    )  # Header accounts cannot have postings
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False, index=True)

    category_id: Mapped[UUID] = mapped_column(
        PG_UUID(as_uuid=True), ForeignKey("account_categories.id"), nullable=False
    )
    parent_id: Mapped[Optional[UUID]] = mapped_column(
        PG_UUID(as_uuid=True), ForeignKey("accounts.id"), nullable=True
    )

    category: Mapped[AccountCategory] = relationship(back_populates="accounts")
    parent: Mapped[Optional["Account"]] = relationship(
        "Account",
        back_populates="children",
        remote_side=[id],
    )
    children: Mapped[List["Account"]] = relationship(
        back_populates="parent",
        cascade="all, delete-orphan",
    )
    balances: Mapped[List["AccountBalance"]] = relationship(
        back_populates="account",
        cascade="all, delete-orphan",
    )
    journal_lines: Mapped[List["JournalLine"]] = relationship(
        back_populates="account",
        lazy="selectin",
    )

    __table_args__ = (
        UniqueConstraint("school_id", "code", name="uq_account_school_code"),
        CheckConstraint("code ~ '^[0-9]{4,}$'", name="ck_account_code_numeric"),
        Index("ix_accounts_school_type", "school_id", "is_active"),
    )


class CostCenter(AuditableBase, TenantMixin):
    """Cost centers for allocation and responsibility tracking."""
    __tablename__ = "cost_centers"

    code: Mapped[str] = mapped_column(String(20), nullable=False, index=True)
    name: Mapped[str] = mapped_column(String(100), nullable=False)
    description: Mapped[Optional[str]] = mapped_column(Text)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)

    journal_lines: Mapped[List["JournalLine"]] = relationship(
        back_populates="cost_center",
    )
    balances: Mapped[List["AccountBalance"]] = relationship(
        back_populates="cost_center",
    )

    __table_args__ = (
        UniqueConstraint("school_id", "code", name="uq_cost_center_school_code"),
    )


# ============================================================================
# GENERAL LEDGER
# ============================================================================


class JournalEntry(AuditableBase, TenantMixin):
    """Journal entry (batch of double-entry transactions)."""
    __tablename__ = "journal_entries"

    reference: Mapped[str] = mapped_column(
        String(50), nullable=False, index=True
    )  # e.g., "JRN-202501-A1B2C3"
    transaction_date: Mapped[Date] = mapped_column(Date, nullable=False, index=True)
    description: Mapped[str] = mapped_column(Text, nullable=False)
    status: Mapped[str] = mapped_column(
        SQLEnum(JournalStatusEnum, values_callable=lambda x: [e.value for e in x]),
        default=JournalStatusEnum.DRAFT.value,
        nullable=False,
        index=True,
    )

    period_id: Mapped[UUID] = mapped_column(
        PG_UUID(as_uuid=True), ForeignKey("accounting_periods.id", ondelete="RESTRICT"), nullable=False
    )
    posted_by_id: Mapped[Optional[UUID]] = mapped_column(PG_UUID(as_uuid=True), nullable=True)
    posted_at: Mapped[Optional[DateTime]] = mapped_column(DateTime(timezone=True), nullable=True)

    # Reversal tracking
    reversed_by_id: Mapped[Optional[UUID]] = mapped_column(PG_UUID(as_uuid=True), nullable=True)
    reverses_id: Mapped[Optional[UUID]] = mapped_column(
        PG_UUID(as_uuid=True), ForeignKey("journal_entries.id"), nullable=True
    )

    period: Mapped[AccountingPeriod] = relationship(back_populates="journal_entries")
    lines: Mapped[List["JournalLine"]] = relationship(
        back_populates="journal",
        cascade="all, delete-orphan",
        lazy="selectin",
    )

    __table_args__ = (
        UniqueConstraint("school_id", "reference", name="uq_journal_school_reference"),
        Index("ix_journal_period_status", "period_id", "status"),
    )


class JournalLine(AuditableBase):
    """Individual debit/credit line in a journal entry."""
    __tablename__ = "journal_lines"

    journal_id: Mapped[UUID] = mapped_column(
        PG_UUID(as_uuid=True), ForeignKey("journal_entries.id", ondelete="CASCADE"), nullable=False
    )
    account_id: Mapped[UUID] = mapped_column(
        PG_UUID(as_uuid=True), ForeignKey("accounts.id", ondelete="RESTRICT"), nullable=False
    )
    cost_center_id: Mapped[Optional[UUID]] = mapped_column(
        PG_UUID(as_uuid=True), ForeignKey("cost_centers.id", ondelete="SET NULL"), nullable=True
    )

    debit: Mapped[Decimal] = mapped_column(
        Numeric(15, 4), default=Decimal("0.0000"), nullable=False
    )
    credit: Mapped[Decimal] = mapped_column(
        Numeric(15, 4), default=Decimal("0.0000"), nullable=False
    )
    description: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)

    journal: Mapped[JournalEntry] = relationship(back_populates="lines")
    account: Mapped[Account] = relationship(back_populates="journal_lines")
    cost_center: Mapped[Optional[CostCenter]] = relationship(back_populates="journal_lines")

    __table_args__ = (
        CheckConstraint("debit >= 0", name="ck_journal_line_debit_positive"),
        CheckConstraint("credit >= 0", name="ck_journal_line_credit_positive"),
        CheckConstraint("NOT (debit > 0 AND credit > 0)", name="ck_journal_line_not_both"),
        Index("ix_journal_line_journal_account", "journal_id", "account_id"),
    )


class PeriodClosure(AuditableBase, TenantMixin):
    """Audit trail for period close operations."""
    __tablename__ = "period_closures"

    period_id: Mapped[UUID] = mapped_column(
        PG_UUID(as_uuid=True), ForeignKey("accounting_periods.id"), nullable=False
    )
    closed_by_id: Mapped[Optional[UUID]] = mapped_column(PG_UUID(as_uuid=True), nullable=True)
    closed_at: Mapped[DateTime] = mapped_column(
        DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), nullable=False
    )
    retained_earnings_account_id: Mapped[Optional[UUID]] = mapped_column(
        PG_UUID(as_uuid=True), ForeignKey("accounts.id"), nullable=True
    )


# ============================================================================
# ACCOUNT BALANCES (Materialized Running Balances)
# ============================================================================


class AccountBalance(AuditableBase, TenantMixin):
    """Materialized balance per period, account, and optional cost center."""
    __tablename__ = "account_balances"

    period_id: Mapped[UUID] = mapped_column(
        PG_UUID(as_uuid=True), ForeignKey("accounting_periods.id", ondelete="CASCADE"), nullable=False
    )
    account_id: Mapped[UUID] = mapped_column(
        PG_UUID(as_uuid=True), ForeignKey("accounts.id", ondelete="CASCADE"), nullable=False
    )
    cost_center_id: Mapped[Optional[UUID]] = mapped_column(
        PG_UUID(as_uuid=True), ForeignKey("cost_centers.id", ondelete="SET NULL"), nullable=True
    )

    opening_balance: Mapped[Decimal] = mapped_column(
        Numeric(15, 4), default=Decimal("0.0000"), nullable=False
    )
    debit_movement: Mapped[Decimal] = mapped_column(
        Numeric(15, 4), default=Decimal("0.0000"), nullable=False
    )
    credit_movement: Mapped[Decimal] = mapped_column(
        Numeric(15, 4), default=Decimal("0.0000"), nullable=False
    )
    closing_balance: Mapped[Decimal] = mapped_column(
        Numeric(15, 4), default=Decimal("0.0000"), nullable=False
    )

    period: Mapped[AccountingPeriod] = relationship(back_populates="account_balances")
    account: Mapped[Account] = relationship(back_populates="balances")
    cost_center: Mapped[Optional[CostCenter]] = relationship(back_populates="balances")

    __table_args__ = (
        UniqueConstraint(
            "school_id", "period_id", "account_id", "cost_center_id",
            name="uq_account_balance_school_period_account_cc"
        ),
        Index("ix_account_balance_period_account", "period_id", "account_id"),
    )
