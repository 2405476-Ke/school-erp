"""
Financial Reporting Schemas (Pydantic v2)

Schemas for:
- Trial Balance Report
- Income Statement Report
- Balance Sheet Report
- Period Close Report
"""
from datetime import date, datetime
from decimal import Decimal
from typing import List, Optional
from uuid import UUID

from pydantic import BaseModel, Field


# ============================================================================
# TRIAL BALANCE
# ============================================================================


class TrialBalanceRow(BaseModel):
    """Single row in a trial balance report."""

    account_id: UUID
    account_code: str
    account_name: str
    account_type: str  # ASSET, LIABILITY, EQUITY, REVENUE, EXPENSE
    parent_code: Optional[str] = None
    is_header: bool = False
    opening_balance: Decimal = Decimal("0.0000")
    debit_movement: Decimal = Decimal("0.0000")
    credit_movement: Decimal = Decimal("0.0000")
    closing_balance: Decimal = Decimal("0.0000")

    class Config:
        json_encoders = {
            Decimal: lambda v: float(v),
        }


class TrialBalanceReport(BaseModel):
    """Complete trial balance for a period."""

    period_id: UUID
    period_name: str
    accounting_date: date
    rows: List[TrialBalanceRow]
    total_debits: Decimal = Decimal("0.0000")
    total_credits: Decimal = Decimal("0.0000")
    is_balanced: bool  # True if total_debits == total_credits
    generated_at: datetime
    generated_by_id: Optional[UUID] = None

    class Config:
        json_encoders = {
            Decimal: lambda v: float(v),
        }


# ============================================================================
# INCOME STATEMENT
# ============================================================================


class IncomeStatementLine(BaseModel):
    """Single line item in income statement."""

    account_code: str
    account_name: str
    amount: Decimal = Decimal("0.0000")
    percentage_of_revenue: Optional[Decimal] = None

    class Config:
        json_encoders = {
            Decimal: lambda v: float(v),
        }


class IncomeStatementCategory(BaseModel):
    """Category of income statement (Revenue, Expenses, etc.)."""

    category_name: str  # "Revenue", "Expenses", "Other Income", "Other Expenses"
    category_type: str  # "REVENUE", "EXPENSE", "OTHER_INCOME", "OTHER_EXPENSE"
    lines: List[IncomeStatementLine]
    subtotal: Decimal = Decimal("0.0000")

    class Config:
        json_encoders = {
            Decimal: lambda v: float(v),
        }


class IncomeStatementReport(BaseModel):
    """Complete income statement for a period."""

    from_date: date
    to_date: date
    categories: List[IncomeStatementCategory]
    total_revenue: Decimal = Decimal("0.0000")
    total_expenses: Decimal = Decimal("0.0000")
    net_surplus_deficit: Decimal = Decimal("0.0000")  # Revenue - Expenses
    generated_at: datetime
    generated_by_id: Optional[UUID] = None

    class Config:
        json_encoders = {
            Decimal: lambda v: float(v),
        }


# ============================================================================
# BALANCE SHEET
# ============================================================================


class BalanceSheetLine(BaseModel):
    """Single line item on balance sheet."""

    account_code: str
    account_name: str
    amount: Decimal = Decimal("0.0000")

    class Config:
        json_encoders = {
            Decimal: lambda v: float(v),
        }


class BalanceSheetSection(BaseModel):
    """Section of balance sheet (Assets, Liabilities, Equity)."""

    section_name: str  # "Assets", "Liabilities", "Equity"
    section_type: str  # "ASSET", "LIABILITY", "EQUITY"
    lines: List[BalanceSheetLine]
    subtotal: Decimal = Decimal("0.0000")

    class Config:
        json_encoders = {
            Decimal: lambda v: float(v),
        }


class BalanceSheetReport(BaseModel):
    """Complete balance sheet as at a date."""

    as_at_date: date
    assets: BalanceSheetSection
    liabilities: BalanceSheetSection
    equity: BalanceSheetSection
    total_assets: Decimal = Decimal("0.0000")
    total_liabilities: Decimal = Decimal("0.0000")
    total_equity: Decimal = Decimal("0.0000")
    is_balanced: bool  # True if Assets == Liabilities + Equity
    generated_at: datetime
    generated_by_id: Optional[UUID] = None

    class Config:
        json_encoders = {
            Decimal: lambda v: float(v),
        }


# ============================================================================
# PERIOD CLOSE
# ============================================================================


class PeriodCloseRequest(BaseModel):
    """Request to close an accounting period."""

    period_id: UUID
    closing_note: Optional[str] = None


class PeriodCloseResponse(BaseModel):
    """Result of period close operation."""

    period_id: UUID
    period_name: str
    closed_at: datetime
    closed_by_id: UUID
    retained_earnings_account_id: UUID
    retained_earnings_amount: Decimal
    opening_balances_created: int
    message: str

    class Config:
        json_encoders = {
            Decimal: lambda v: float(v),
        }


# ============================================================================
# GENERAL LEDGER REPORT
# ============================================================================


class GeneralLedgerLine(BaseModel):
    """Single line in general ledger report."""

    transaction_date: date
    journal_reference: str
    description: str
    debit: Decimal = Decimal("0.0000")
    credit: Decimal = Decimal("0.0000")
    balance: Decimal = Decimal("0.0000")

    class Config:
        json_encoders = {
            Decimal: lambda v: float(v),
        }


class GeneralLedgerReport(BaseModel):
    """General ledger for a specific account over a period."""

    account_code: str
    account_name: str
    from_date: date
    to_date: date
    opening_balance: Decimal = Decimal("0.0000")
    lines: List[GeneralLedgerLine]
    closing_balance: Decimal = Decimal("0.0000")
    total_debits: Decimal = Decimal("0.0000")
    total_credits: Decimal = Decimal("0.0000")
    generated_at: datetime

    class Config:
        json_encoders = {
            Decimal: lambda v: float(v),
        }
