"""
Reporting Routers: FastAPI endpoints for financial reports.

Endpoints for:
- Trial Balance Report
- Income Statement Report
- Balance Sheet Report
- General Ledger Report
"""
from datetime import date
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.ext.asyncio import AsyncSession

from src.core.database import get_db
from src.core.security import get_current_user
from src.modules.finance.services.reporting_service import ReportingService
from src.modules.users.models import User
from src.shared.exceptions import NotFoundError, ValidationError
from src.shared.response import APIResponse
from src.modules.finance.schemas.reporting import (
    TrialBalanceReport,
    IncomeStatementReport,
    BalanceSheetReport,
    GeneralLedgerReport,
)

router = APIRouter(prefix="/finance/reports", tags=["finance-reports"])


@router.get("/trial-balance", response_model=APIResponse[TrialBalanceReport])
async def get_trial_balance(
    school_id: UUID,
    period_id: UUID,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """
    Generate trial balance for a period.

    Trial balance shows all accounts with their closing balances.
    Verifies that Total Debits = Total Credits.

    Args:
        period_id: Accounting period

    Returns:
        TrialBalanceReport with all accounts and verification
    """
    if current_user.school_id != school_id:
        raise HTTPException(status_code=403, detail="Not authorized for this school")

    service = ReportingService(db)

    try:
        report = await service.generate_trial_balance(
            school_id, period_id, current_user.id
        )

        return APIResponse.success(
            report,
            message="Trial balance generated",
            meta={"is_balanced": report.is_balanced},
        )

    except NotFoundError as e:
        raise HTTPException(status_code=404, detail=str(e.detail))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Report generation failed: {str(e)}")


@router.get("/income-statement", response_model=APIResponse[IncomeStatementReport])
async def get_income_statement(
    school_id: UUID,
    from_date: date = Query(...),
    to_date: date = Query(...),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """
    Generate income statement for a period.

    Income statement shows Revenue - Expenses = Net Surplus/Deficit.

    Args:
        from_date: Start date
        to_date: End date

    Returns:
        IncomeStatementReport with revenue, expenses, net
    """
    if current_user.school_id != school_id:
        raise HTTPException(status_code=403, detail="Not authorized for this school")

    if from_date > to_date:
        raise HTTPException(
            status_code=400,
            detail="from_date must be before to_date",
        )

    service = ReportingService(db)

    try:
        report = await service.generate_income_statement(
            school_id, from_date, to_date, current_user.id
        )

        return APIResponse.success(
            report,
            message="Income statement generated",
            meta={
                "total_revenue": float(report.total_revenue),
                "total_expenses": float(report.total_expenses),
                "net_result": float(report.net_surplus_deficit),
            },
        )

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Report generation failed: {str(e)}")


@router.get("/balance-sheet", response_model=APIResponse[BalanceSheetReport])
async def get_balance_sheet(
    school_id: UUID,
    as_at_date: date = Query(...),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """
    Generate balance sheet as of a date.

    Balance sheet shows Assets = Liabilities + Equity.
    Includes retained earnings from income statement.

    Args:
        as_at_date: Date for balance sheet (usually period end)

    Returns:
        BalanceSheetReport with all sections and verification
    """
    if current_user.school_id != school_id:
        raise HTTPException(status_code=403, detail="Not authorized for this school")

    service = ReportingService(db)

    try:
        report = await service.generate_balance_sheet(
            school_id, as_at_date, current_user.id
        )

        return APIResponse.success(
            report,
            message="Balance sheet generated",
            meta={
                "is_balanced": report.is_balanced,
                "total_assets": float(report.total_assets),
                "total_liabilities_equity": float(report.total_liabilities + report.total_equity),
            },
        )

    except NotFoundError as e:
        raise HTTPException(status_code=404, detail=str(e.detail))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Report generation failed: {str(e)}")


@router.get("/general-ledger/{account_id}", response_model=APIResponse[GeneralLedgerReport])
async def get_general_ledger(
    school_id: UUID,
    account_id: UUID,
    from_date: date = Query(...),
    to_date: date = Query(...),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """
    Generate general ledger for a specific account.

    Shows detailed transaction history with running balance.

    Args:
        account_id: GL account to report on
        from_date: Start date
        to_date: End date

    Returns:
        GeneralLedgerReport with all transactions and running balance
    """
    if current_user.school_id != school_id:
        raise HTTPException(status_code=403, detail="Not authorized for this school")

    if from_date > to_date:
        raise HTTPException(
            status_code=400,
            detail="from_date must be before to_date",
        )

    service = ReportingService(db)

    try:
        report = await service.generate_general_ledger(
            school_id, account_id, from_date, to_date, current_user.id
        )

        return APIResponse.success(
            report,
            message="General ledger generated",
            meta={
                "transaction_count": len(report.lines),
                "total_debits": float(report.total_debits),
                "total_credits": float(report.total_credits),
                "closing_balance": float(report.closing_balance),
            },
        )

    except NotFoundError as e:
        raise HTTPException(status_code=404, detail=str(e.detail))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Report generation failed: {str(e)}")
