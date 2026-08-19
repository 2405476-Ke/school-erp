"""
Pydantic v2 schemas for Chart of Accounts, General Ledger, and financial reporting.
Strict validation with custom validators for business rules.
"""
from datetime import date, datetime
from decimal import Decimal
from typing import List, Optional
from uuid import UUID

from pydantic import BaseModel, Field, ConfigDict, field_validator, model_validator

from src.modules.finance.models.ledger import AccountTypeEnum, PeriodStatusEnum, JournalStatusEnum


# ============================================================================
# ACCOUNT TYPE & CATEGORY SCHEMAS
# ============================================================================


class AccountTypeResponse(BaseModel):
    """Account type response."""
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    name: str
    normal_balance: str  # DEBIT or CREDIT


class AccountCategoryResponse(BaseModel):
    """Account category response."""
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    account_type_id: UUID
    name: str
    description: Optional[str] = None


# ============================================================================
# ACCOUNT SCHEMAS
# ============================================================================


class AccountCreate(BaseModel):
    """Create account request."""

    code: str = Field(..., min_length=4, max_length=20, pattern=r"^\d+$")
    name: str = Field(..., min_length=1, max_length=150)
    description: Optional[str] = Field(None, max_length=500)
    is_control_account: bool = False
    is_header: bool = False
    category_id: UUID
    parent_id: Optional[UUID] = None

    @model_validator(mode="after")
    def validate_headers_and_control(self):
        """Headers and control accounts cannot both be true."""
        if self.is_header and self.is_control_account:
            raise ValueError("Account cannot be both header and control account")
        return self


class AccountUpdate(BaseModel):
    """Update account request."""

    name: Optional[str] = Field(None, min_length=1, max_length=150)
    description: Optional[str] = Field(None, max_length=500)
    is_active: Optional[bool] = None


class AccountResponse(BaseModel):
    """Account response."""
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    school_id: UUID
    code: str
    name: str
    description: Optional[str] = None
    is_control_account: bool
    is_header: bool
    is_active: bool
    category_id: UUID
    parent_id: Optional[UUID] = None
    created_at: datetime
    updated_at: datetime


class AccountTreeResponse(AccountResponse):
    """Hierarchical account tree response."""

    children: List["AccountTreeResponse"] = []


AccountTreeResponse.model_rebuild()


# ============================================================================
# COST CENTER SCHEMAS
# ============================================================================


class CostCenterCreate(BaseModel):
    """Create cost center request."""

    code: str = Field(..., min_length=1, max_length=20)
    name: str = Field(..., min_length=1, max_length=100)
    description: Optional[str] = None
    is_active: bool = True


class CostCenterUpdate(BaseModel):
    """Update cost center request."""

    name: Optional[str] = Field(None, min_length=1, max_length=100)
    description: Optional[str] = None
    is_active: Optional[bool] = None


class CostCenterResponse(BaseModel):
    """Cost center response."""
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    school_id: UUID
    code: str
    name: str
    description: Optional[str] = None
    is_active: bool
    created_at: datetime
    updated_at: datetime


# ============================================================================
# FINANCIAL YEAR & PERIOD SCHEMAS
# ============================================================================


class FinancialYearCreate(BaseModel):
    """Create financial year request."""

    year_name: str = Field(..., min_length=4, max_length=20)
    start_date: date
    end_date: date

    @model_validator(mode="after")
    def validate_dates(self):
        """Start date must be before end date."""
        if self.start_date >= self.end_date:
            raise ValueError("start_date must be before end_date")
        return self


class FinancialYearResponse(BaseModel):
    """Financial year response."""
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    school_id: UUID
    year_name: str
    start_date: date
    end_date: date
    status: str
    created_at: datetime
    updated_at: datetime


class AccountingPeriodCreate(BaseModel):
    """Create accounting period request."""

    financial_year_id: UUID
    period_name: str = Field(..., min_length=1, max_length=50)
    period_number: Optional[int] = Field(None, ge=1, le=12)
    start_date: date
    end_date: date

    @model_validator(mode="after")
    def validate_dates(self):
        """Start date must be before end date."""
        if self.start_date >= self.end_date:
            raise ValueError("start_date must be before end_date")
        return self


class AccountingPeriodResponse(BaseModel):
    """Accounting period response."""
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    school_id: UUID
    financial_year_id: UUID
    period_name: str
    period_number: Optional[int] = None
    start_date: date
    end_date: date
    status: str
    created_at: datetime
    updated_at: datetime


# ============================================================================
# JOURNAL LINE SCHEMAS
# ============================================================================


class JournalLineCreate(BaseModel):
    """Create journal line request."""

    account_id: UUID
    cost_center_id: Optional[UUID] = None
    description: Optional[str] = Field(None, max_length=255)
    debit: Decimal = Field(default=Decimal("0.0000"), decimal_places=4, ge=0)
    credit: Decimal = Field(default=Decimal("0.0000"), decimal_places=4, ge=0)

    @model_validator(mode="after")
    def validate_debit_credit(self):
        """Each line must have debit OR credit, not both, not neither."""
        if self.debit == Decimal("0.0000") and self.credit == Decimal("0.0000"):
            raise ValueError("Line must have either debit or credit (not zero)")
        if self.debit > Decimal("0.0000") and self.credit > Decimal("0.0000"):
            raise ValueError("Line cannot have both debit and credit")
        return self


class JournalLineResponse(BaseModel):
    """Journal line response."""
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    journal_id: UUID
    account_id: UUID
    cost_center_id: Optional[UUID] = None
    debit: Decimal
    credit: Decimal
    description: Optional[str] = None
    created_at: datetime
    updated_at: datetime


# ============================================================================
# JOURNAL ENTRY SCHEMAS
# ============================================================================


class JournalEntryCreate(BaseModel):
    """Create journal entry request (draft)."""

    transaction_date: date
    description: str = Field(..., min_length=1, max_length=500)
    lines: List[JournalLineCreate] = Field(..., min_length=1)

    @model_validator(mode="after")
    def validate_balanced(self):
        """Journal must be balanced (total debit = total credit)."""
        total_debit = sum((line.debit for line in self.lines), Decimal("0.0000"))
        total_credit = sum((line.credit for line in self.lines), Decimal("0.0000"))

        if total_debit != total_credit:
            raise ValueError(
                f"Journal is unbalanced: total debit={total_debit}, total credit={total_credit}"
            )
        return self


class JournalEntryResponse(BaseModel):
    """Journal entry response."""
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    school_id: UUID
    reference: str
    transaction_date: date
    description: str
    status: str
    period_id: UUID
    posted_by_id: Optional[UUID] = None
    posted_at: Optional[datetime] = None
    reversed_by_id: Optional[UUID] = None
    reverses_id: Optional[UUID] = None
    lines: List[JournalLineResponse] = []
    created_at: datetime
    updated_at: datetime


class JournalEntryPostRequest(BaseModel):
    """Request to post a journal entry."""

    user_id: UUID


class JournalEntryReverseRequest(BaseModel):
    """Request to reverse a journal entry."""

    user_id: UUID
    reason: str = Field(..., min_length=1, max_length=500)


# ============================================================================
# ACCOUNT BALANCE SCHEMAS
# ============================================================================


class AccountBalanceResponse(BaseModel):
    """Account balance response."""
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    school_id: UUID
    period_id: UUID
    account_id: UUID
    cost_center_id: Optional[UUID] = None
    opening_balance: Decimal
    debit_movement: Decimal
    credit_movement: Decimal
    closing_balance: Decimal
    created_at: datetime
    updated_at: datetime


# ============================================================================
# REPORTING SCHEMAS
# ============================================================================


class TrialBalanceLine(BaseModel):
    """Trial balance line."""

    account_code: str
    account_name: str
    debit: Decimal = Field(decimal_places=4)
    credit: Decimal = Field(decimal_places=4)


class TrialBalanceReport(BaseModel):
    """Trial balance report."""

    period_id: UUID
    period_name: str
    report_date: datetime
    lines: List[TrialBalanceLine]
    total_debit: Decimal = Field(decimal_places=4)
    total_credit: Decimal = Field(decimal_places=4)
    is_balanced: bool


class LedgerLine(BaseModel):
    """General ledger line."""

    transaction_date: date
    reference: str
    description: str
    debit: Decimal = Field(decimal_places=4)
    credit: Decimal = Field(decimal_places=4)
    running_balance: Decimal = Field(decimal_places=4)


class GeneralLedgerReport(BaseModel):
    """General ledger report for an account."""

    account_code: str
    account_name: str
    period_id: UUID
    from_date: date
    to_date: date
    opening_balance: Decimal = Field(decimal_places=4)
    lines: List[LedgerLine]
    closing_balance: Decimal = Field(decimal_places=4)
