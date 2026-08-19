"""
Finance module: Fee Management models.
FeeStructure, FeeVoteHead, FeeInvoice, FeeReceipt, StudentFeeAccount.
All amounts in DECIMAL(15,4) for KES precision.
"""
from datetime import datetime, timezone
from decimal import Decimal
from enum import Enum
from typing import List, Optional
from uuid import UUID

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
)
from sqlalchemy.dialects.postgresql import UUID as PG_UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from src.shared.base_model import AuditableBase, TenantMixin, GUID, FK_UUID, SCHOOL_ID


class PaymentMethodEnum(str, Enum):
    """Payment methods for fee receipts."""
    MPESA = "MPESA"
    BANK = "BANK"
    CASH = "CASH"
    CHEQUE = "CHEQUE"
    BURSARY = "BURSARY"


class FeeInvoiceStatusEnum(str, Enum):
    """Fee invoice status."""
    UNPAID = "UNPAID"
    PARTIAL = "PARTIAL"
    PAID = "PAID"
    VOID = "VOID"


class FeeVoteHead(AuditableBase, TenantMixin):
    """
    Fee vote head (budget line item).
    Maps to a GL revenue account and has priority for payment allocation.
    """
    __tablename__ = "fee_vote_heads"

    name: Mapped[str] = mapped_column(String(100), nullable=False)  # e.g., "Tuition", "Boarding"
    description: Mapped[Optional[str]] = mapped_column(Text)
    
    account_id: Mapped[UUID] = mapped_column(
        PG_UUID(as_uuid=True), ForeignKey("accounts.id"), nullable=False
    )
    
    priority: Mapped[int] = mapped_column(default=1, nullable=False, index=True)
    # Lower priority number = paid first (1 = tuition, 2 = boarding, 3 = activity, etc.)
    
    is_restricted: Mapped[bool] = mapped_column(default=False, nullable=False)
    # True = MOE capitation funds, cannot be re-appropriated
    
    allow_arrears_carry: Mapped[bool] = mapped_column(default=True, nullable=False)
    # If False, unpaid balances at term end are written off
    
    is_active: Mapped[bool] = mapped_column(default=True, nullable=False, index=True)

    account: Mapped["Account"] = relationship()
    fee_structure_items: Mapped[List["FeeStructureItem"]] = relationship(
        back_populates="vote_head",
        cascade="all, delete-orphan",
    )
    invoice_items: Mapped[List["FeeInvoiceItem"]] = relationship(
        back_populates="vote_head",
    )
    receipt_allocations: Mapped[List["FeeReceiptAllocation"]] = relationship(
        back_populates="vote_head",
    )

    __table_args__ = (
        UniqueConstraint("school_id", "name", name="uq_fee_vote_head_school_name"),
    )


class FeeStructure(AuditableBase, TenantMixin):
    """
    Fee structure: amount breakdown by vote head for a specific term and boarding type.
    Per academic_year + term + boarding_type + curriculum_type.
    """
    __tablename__ = "fee_structures"

    academic_year_id: Mapped[UUID] = mapped_column(
        PG_UUID(as_uuid=True), ForeignKey("academic_years.id", ondelete="CASCADE"), nullable=False
    )
    term_id: Mapped[UUID] = mapped_column(
        PG_UUID(as_uuid=True), ForeignKey("terms.id", ondelete="CASCADE"), nullable=False
    )
    
    boarding_type: Mapped[str] = mapped_column(
        String(20), nullable=False, index=True
    )  # DAY, BOARDING, or ALL
    curriculum_type: Mapped[str] = mapped_column(
        String(20), nullable=False, index=True
    )  # 8-4-4, CBC, or ALL
    
    total_amount: Mapped[Decimal] = mapped_column(
        Numeric(15, 4), default=Decimal("0.0000"), nullable=False
    )
    
    is_active: Mapped[bool] = mapped_column(default=True, nullable=False, index=True)

    academic_year: Mapped["AcademicYear"] = relationship()
    term: Mapped["Term"] = relationship()
    items: Mapped[List["FeeStructureItem"]] = relationship(
        back_populates="fee_structure",
        cascade="all, delete-orphan",
        lazy="selectin",
    )
    invoices: Mapped[List["FeeInvoice"]] = relationship(
        back_populates="fee_structure",
    )

    __table_args__ = (
        UniqueConstraint(
            "school_id", "academic_year_id", "term_id", "boarding_type", "curriculum_type",
            name="uq_fee_structure_unique"
        ),
        CheckConstraint("boarding_type IN ('DAY', 'BOARDING', 'ALL')", name="ck_boarding_type"),
        CheckConstraint("curriculum_type IN ('8-4-4', 'CBC', 'ALL')", name="ck_curriculum_type"),
    )


class FeeStructureItem(AuditableBase):
    """Individual line item in a fee structure."""
    __tablename__ = "fee_structure_items"

    fee_structure_id: Mapped[UUID] = mapped_column(
        PG_UUID(as_uuid=True), ForeignKey("fee_structures.id", ondelete="CASCADE"), nullable=False
    )
    vote_head_id: Mapped[UUID] = mapped_column(
        PG_UUID(as_uuid=True), ForeignKey("fee_vote_heads.id"), nullable=False
    )
    
    amount: Mapped[Decimal] = mapped_column(Numeric(15, 4), nullable=False)

    fee_structure: Mapped[FeeStructure] = relationship(back_populates="items")
    vote_head: Mapped[FeeVoteHead] = relationship(back_populates="fee_structure_items")

    __table_args__ = (
        UniqueConstraint(
            "fee_structure_id", "vote_head_id",
            name="uq_fee_structure_item_unique"
        ),
    )


class StudentFeeAccount(AuditableBase, TenantMixin):
    """
    Student fee account: tracks cumulative balance.
    Positive balance = arrears (student owes money)
    Negative balance = prepayment (student credit)
    """
    __tablename__ = "student_fee_accounts"

    student_id: Mapped[UUID] = mapped_column(
        PG_UUID(as_uuid=True), ForeignKey("students.id", ondelete="CASCADE"), nullable=False, unique=True
    )
    
    running_balance: Mapped[Decimal] = mapped_column(
        Numeric(15, 4), default=Decimal("0.0000"), nullable=False
    )
    last_updated_at: Mapped[DateTime] = mapped_column(
        DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), nullable=False
    )

    student: Mapped["Student"] = relationship()

    __table_args__ = (
        CheckConstraint("running_balance >= 0", name="ck_running_balance_positive"),
    )


class FeeInvoice(AuditableBase, TenantMixin):
    """
    Fee invoice: billing document for a student for a specific term.
    Status transitions: UNPAID → PARTIAL → PAID (or VOID)
    """
    __tablename__ = "fee_invoices"

    student_id: Mapped[UUID] = mapped_column(
        PG_UUID(as_uuid=True), ForeignKey("students.id", ondelete="CASCADE"), nullable=False, index=True
    )
    term_id: Mapped[UUID] = mapped_column(
        PG_UUID(as_uuid=True), ForeignKey("terms.id", ondelete="CASCADE"), nullable=False
    )
    fee_structure_id: Mapped[Optional[UUID]] = mapped_column(
        PG_UUID(as_uuid=True), ForeignKey("fee_structures.id"), nullable=True
    )
    
    invoice_number: Mapped[str] = mapped_column(String(50), nullable=False, unique=True, index=True)
    invoice_date: Mapped[Date] = mapped_column(Date, nullable=False)
    
    total_amount: Mapped[Decimal] = mapped_column(
        Numeric(15, 4), nullable=False
    )
    amount_paid: Mapped[Decimal] = mapped_column(
        Numeric(15, 4), default=Decimal("0.0000"), nullable=False
    )
    
    status: Mapped[str] = mapped_column(
        SQLEnum(FeeInvoiceStatusEnum, values_callable=lambda x: [e.value for e in x]),
        default=FeeInvoiceStatusEnum.UNPAID.value,
        nullable=False,
        index=True,
    )

    journal_entry_id: Mapped[Optional[UUID]] = mapped_column(
        PG_UUID(as_uuid=True), ForeignKey("journal_entries.id"), nullable=True
    )

    student: Mapped["Student"] = relationship()
    term: Mapped["Term"] = relationship()
    fee_structure: Mapped[Optional[FeeStructure]] = relationship(back_populates="invoices")
    items: Mapped[List["FeeInvoiceItem"]] = relationship(
        back_populates="invoice",
        cascade="all, delete-orphan",
        lazy="selectin",
    )
    allocations: Mapped[List["FeeReceiptAllocation"]] = relationship(
        back_populates="invoice_item",
    )

    __table_args__ = (
        UniqueConstraint(
            "school_id", "student_id", "term_id",
            name="uq_fee_invoice_student_term"
        ),
        Index("ix_fee_invoice_student_status", "student_id", "status"),
    )


class FeeInvoiceItem(AuditableBase):
    """Individual line item in a fee invoice (per vote head)."""
    __tablename__ = "fee_invoice_items"

    invoice_id: Mapped[UUID] = mapped_column(
        PG_UUID(as_uuid=True), ForeignKey("fee_invoices.id", ondelete="CASCADE"), nullable=False
    )
    vote_head_id: Mapped[UUID] = mapped_column(
        PG_UUID(as_uuid=True), ForeignKey("fee_vote_heads.id"), nullable=False
    )
    
    amount: Mapped[Decimal] = mapped_column(Numeric(15, 4), nullable=False)
    amount_paid: Mapped[Decimal] = mapped_column(
        Numeric(15, 4), default=Decimal("0.0000"), nullable=False
    )

    invoice: Mapped[FeeInvoice] = relationship(back_populates="items")
    vote_head: Mapped[FeeVoteHead] = relationship(back_populates="invoice_items")
    allocations: Mapped[List["FeeReceiptAllocation"]] = relationship(
        back_populates="invoice_item",
        cascade="all, delete-orphan",
    )

    __table_args__ = (
        UniqueConstraint(
            "invoice_id", "vote_head_id",
            name="uq_fee_invoice_item_unique"
        ),
    )


class FeeReceipt(AuditableBase, TenantMixin):
    """
    Fee receipt: payment record from student.
    Links to journal entry for GL posting (DR Bank, CR StudentReceivables).
    """
    __tablename__ = "fee_receipts"

    student_id: Mapped[UUID] = mapped_column(
        PG_UUID(as_uuid=True), ForeignKey("students.id", ondelete="CASCADE"), nullable=False, index=True
    )
    
    receipt_number: Mapped[str] = mapped_column(String(50), nullable=False, index=True)
    receipt_date: Mapped[Date] = mapped_column(Date, nullable=False)
    
    amount: Mapped[Decimal] = mapped_column(Numeric(15, 4), nullable=False)
    
    payment_method: Mapped[str] = mapped_column(
        SQLEnum(PaymentMethodEnum, values_callable=lambda x: [e.value for e in x]),
        nullable=False
    )
    
    reference_number: Mapped[Optional[str]] = mapped_column(
        String(100)
    )  # M-Pesa code, Cheque number, etc.
    
    is_posted: Mapped[bool] = mapped_column(default=False, nullable=False, index=True)
    
    journal_entry_id: Mapped[Optional[UUID]] = mapped_column(
        PG_UUID(as_uuid=True), ForeignKey("journal_entries.id"), nullable=True
    )
    
    posted_by_id: Mapped[Optional[UUID]] = mapped_column(PG_UUID(as_uuid=True), nullable=True)
    posted_at: Mapped[Optional[DateTime]] = mapped_column(DateTime(timezone=True), nullable=True)

    student: Mapped["Student"] = relationship()
    allocations: Mapped[List["FeeReceiptAllocation"]] = relationship(
        back_populates="receipt",
        cascade="all, delete-orphan",
    )
    journal_entry: Mapped[Optional["JournalEntry"]] = relationship()

    __table_args__ = (
        UniqueConstraint("school_id", "receipt_number", name="uq_fee_receipt_school_number"),
        Index("ix_fee_receipt_student_date", "student_id", "receipt_date"),
    )


class FeeReceiptAllocation(AuditableBase, TenantMixin):
    """
    Allocation of a receipt to specific invoice items.
    Links receipt → invoice_item, records amount allocated.
    """
    __tablename__ = "fee_receipt_allocations"

    receipt_id: Mapped[UUID] = mapped_column(
        PG_UUID(as_uuid=True), ForeignKey("fee_receipts.id", ondelete="CASCADE"), nullable=False
    )
    
    invoice_item_id: Mapped[Optional[UUID]] = mapped_column(
        PG_UUID(as_uuid=True), ForeignKey("fee_invoice_items.id"), nullable=True
    )  # NULL if pre-paying/allocating to generic vote head
    
    vote_head_id: Mapped[UUID] = mapped_column(
        PG_UUID(as_uuid=True), ForeignKey("fee_vote_heads.id"), nullable=False
    )
    
    allocated_amount: Mapped[Decimal] = mapped_column(
        Numeric(15, 4), nullable=False
    )

    receipt: Mapped[FeeReceipt] = relationship(back_populates="allocations")
    invoice_item: Mapped[Optional[FeeInvoiceItem]] = relationship(back_populates="allocations")
    vote_head: Mapped[FeeVoteHead] = relationship(back_populates="receipt_allocations")

    __table_args__ = (
        Index("ix_allocation_receipt_item", "receipt_id", "invoice_item_id"),
    )


# Import after definitions to avoid circular imports
from src.modules.academic.models import (
    AcademicYear,
    Term,
)
from src.modules.students.models import (
    Student,
)
from src.modules.finance.models.ledger import (
    Account,
    JournalEntry,
)
