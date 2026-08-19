"""
Pydantic v2 schemas for fee management.
FeeStructure, FeeInvoice, FeeReceipt request/response schemas with validation.
"""
from datetime import date, datetime
from decimal import Decimal
from typing import List, Optional
from uuid import UUID

from pydantic import BaseModel, Field, ConfigDict, field_validator, model_validator


# ============================================================================
# FEE VOTE HEAD SCHEMAS
# ============================================================================


class FeeVoteHeadCreate(BaseModel):
    """Create fee vote head request."""

    name: str = Field(..., min_length=1, max_length=100)
    description: Optional[str] = Field(None, max_length=500)
    account_id: UUID
    priority: int = Field(default=1, ge=1, le=100)
    is_restricted: bool = False
    allow_arrears_carry: bool = True
    is_active: bool = True


class FeeVoteHeadUpdate(BaseModel):
    """Update fee vote head request."""

    name: Optional[str] = Field(None, min_length=1, max_length=100)
    description: Optional[str] = Field(None, max_length=500)
    priority: Optional[int] = Field(None, ge=1, le=100)
    is_active: Optional[bool] = None


class FeeVoteHeadResponse(BaseModel):
    """Fee vote head response."""
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    school_id: UUID
    name: str
    description: Optional[str] = None
    account_id: UUID
    priority: int
    is_restricted: bool
    allow_arrears_carry: bool
    is_active: bool
    created_at: datetime
    updated_at: datetime


# ============================================================================
# FEE STRUCTURE SCHEMAS
# ============================================================================


class FeeStructureItemCreate(BaseModel):
    """Create fee structure item (line item)."""

    vote_head_id: UUID
    amount: Decimal = Field(..., decimal_places=4, ge=0)


class FeeStructureCreate(BaseModel):
    """Create fee structure request."""

    academic_year_id: UUID
    term_id: UUID
    boarding_type: str = Field(..., regex="^(DAY|BOARDING|ALL)$")
    curriculum_type: str = Field(..., regex="^(8-4-4|CBC|ALL)$")
    items: List[FeeStructureItemCreate] = Field(..., min_length=1)
    is_active: bool = True

    @model_validator(mode="after")
    def validate_total_positive(self):
        """Total amount must be > 0."""
        total = sum(item.amount for item in self.items)
        if total <= Decimal("0"):
            raise ValueError("Fee structure total must be greater than 0")
        return self


class FeeStructureItemResponse(BaseModel):
    """Fee structure item response."""
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    fee_structure_id: UUID
    vote_head_id: UUID
    amount: Decimal
    created_at: datetime
    updated_at: datetime


class FeeStructureResponse(BaseModel):
    """Fee structure response."""
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    school_id: UUID
    academic_year_id: UUID
    term_id: UUID
    boarding_type: str
    curriculum_type: str
    total_amount: Decimal
    is_active: bool
    items: List[FeeStructureItemResponse] = []
    created_at: datetime
    updated_at: datetime


# ============================================================================
# FEE INVOICE SCHEMAS
# ============================================================================


class FeeInvoiceItemResponse(BaseModel):
    """Fee invoice item response."""
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    invoice_id: UUID
    vote_head_id: UUID
    amount: Decimal
    amount_paid: Decimal
    created_at: datetime
    updated_at: datetime


class FeeInvoiceResponse(BaseModel):
    """Fee invoice response."""
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    school_id: UUID
    student_id: UUID
    term_id: UUID
    fee_structure_id: Optional[UUID] = None
    invoice_number: str
    invoice_date: date
    total_amount: Decimal
    amount_paid: Decimal
    status: str
    items: List[FeeInvoiceItemResponse] = []
    created_at: datetime
    updated_at: datetime

    @property
    def amount_outstanding(self) -> Decimal:
        """Calculate outstanding balance."""
        return self.total_amount - self.amount_paid


class StudentFeeStatementLine(BaseModel):
    """Single line in student fee statement."""

    invoice_number: str
    invoice_date: date
    term_name: str
    total_amount: Decimal
    amount_paid: Decimal
    status: str
    outstanding: Decimal


class StudentFeeStatement(BaseModel):
    """Student fee statement (summary + detail)."""

    student_id: UUID
    student_name: str
    total_arrears: Decimal
    invoices: List[StudentFeeStatementLine]
    total_owing: Decimal

    @property
    def total_paid(self) -> Decimal:
        """Sum of amounts paid."""
        return sum(inv.amount_paid for inv in self.invoices)


# ============================================================================
# FEE RECEIPT SCHEMAS
# ============================================================================


class FeeReceiptAllocationResponse(BaseModel):
    """Receipt allocation response."""
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    receipt_id: UUID
    invoice_item_id: Optional[UUID] = None
    vote_head_id: UUID
    allocated_amount: Decimal
    created_at: datetime
    updated_at: datetime


class FeeReceiptCreate(BaseModel):
    """Create fee receipt request."""

    student_id: UUID
    receipt_date: date
    amount: Decimal = Field(..., decimal_places=4, gt=0)
    payment_method: str = Field(..., regex="^(MPESA|BANK|CASH|CHEQUE|BURSARY)$")
    reference_number: Optional[str] = Field(None, max_length=100)


class FeeReceiptResponse(BaseModel):
    """Fee receipt response."""
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    school_id: UUID
    student_id: UUID
    receipt_number: str
    receipt_date: date
    amount: Decimal
    payment_method: str
    reference_number: Optional[str] = None
    is_posted: bool
    posted_at: Optional[datetime] = None
    allocations: List[FeeReceiptAllocationResponse] = []
    created_at: datetime
    updated_at: datetime


class ReceiptPostRequest(BaseModel):
    """Request to post a receipt to the GL."""

    user_id: UUID


# ============================================================================
# BILLING SERVICE SCHEMAS
# ============================================================================


class BillingRunRequest(BaseModel):
    """Request to run termly billing."""

    academic_year_id: UUID
    term_id: UUID


class BillingRunResponse(BaseModel):
    """Response from billing run."""

    invoices_created: int
    students_processed: int
    total_billed: Decimal
    timestamp: datetime
