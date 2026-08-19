"""
Periods Routers: FastAPI endpoints for accounting period management.

Endpoints for:
- Close accounting period
- Reopen accounting period
- Get period details
- List periods
"""
from typing import List, Optional
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy import and_, select
from sqlalchemy.ext.asyncio import AsyncSession

from src.core.database import get_db
from src.core.security import get_current_user
from src.modules.finance.models.ledger import AccountingPeriod
from src.modules.finance.services.period_service import PeriodService
from src.modules.finance.schemas.reporting import PeriodCloseRequest, PeriodCloseResponse
from src.modules.users.models import User
from src.shared.exceptions import NotFoundError, ValidationError
from src.shared.response import APIResponse

router = APIRouter(prefix="/finance/periods", tags=["finance-periods"])


# ============================================================================
# PERIOD MANAGEMENT
# ============================================================================


@router.get("/{period_id}", response_model=APIResponse[dict])
async def get_period(
    school_id: UUID,
    period_id: UUID,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Fetch a specific accounting period."""
    if current_user.school_id != school_id:
        raise HTTPException(status_code=403, detail="Not authorized for this school")

    period_query = select(AccountingPeriod).where(
        and_(
            AccountingPeriod.id == period_id,
            AccountingPeriod.school_id == school_id,
        )
    )
    result = await db.execute(period_query)
    period = result.scalar_one_or_none()

    if not period:
        raise HTTPException(status_code=404, detail="Period not found")

    return APIResponse.success(
        {
            "id": str(period.id),
            "period_name": period.period_name,
            "start_date": period.start_date.isoformat(),
            "end_date": period.end_date.isoformat(),
            "status": period.status,
            "financial_year_id": str(period.financial_year_id),
        },
        message="Period retrieved",
    )


@router.get("", response_model=APIResponse[List[dict]])
async def list_periods(
    school_id: UUID,
    financial_year_id: Optional[UUID] = Query(None),
    status: Optional[str] = Query(None),  # OPEN, CLOSED, FUTURE
    skip: int = Query(0, ge=0),
    limit: int = Query(50, ge=1, le=500),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """
    List accounting periods for a school.

    Optional filters by financial year and status.
    """
    if current_user.school_id != school_id:
        raise HTTPException(status_code=403, detail="Not authorized for this school")

    filters = [
        AccountingPeriod.school_id == school_id,
        AccountingPeriod.is_deleted == False,
    ]

    if financial_year_id:
        filters.append(AccountingPeriod.financial_year_id == financial_year_id)

    if status:
        filters.append(AccountingPeriod.status == status)

    query = (
        select(AccountingPeriod)
        .where(and_(*filters))
        .order_by(AccountingPeriod.start_date)
        .offset(skip)
        .limit(limit)
    )

    result = await db.execute(query)
    periods = result.scalars().all()

    periods_data = [
        {
            "id": str(p.id),
            "period_name": p.period_name,
            "start_date": p.start_date.isoformat(),
            "end_date": p.end_date.isoformat(),
            "status": p.status,
            "financial_year_id": str(p.financial_year_id),
        }
        for p in periods
    ]

    return APIResponse.success(
        periods_data,
        message=f"Retrieved {len(periods_data)} periods",
    )


# ============================================================================
# PERIOD CLOSE OPERATIONS (CRITICAL)
# ============================================================================


@router.post("/{period_id}/close", response_model=APIResponse[PeriodCloseResponse])
async def close_period(
    school_id: UUID,
    period_id: UUID,
    request: PeriodCloseRequest,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """
    Close an accounting period (CRITICAL OPERATION).

    This is a critical financial operation that:
    1. Verifies no DRAFT journals remain
    2. Generates and verifies trial balance
    3. Locks the period (no future posts allowed)
    4. Rolls forward closing balances to next period as opening balances
    5. Calculates and records retained earnings

    After closure:
    - Period is READ-ONLY
    - New journals cannot be posted to this period
    - Next period can be opened for transactions

    Args:
        period_id: Period to close
        request: PeriodCloseRequest (closing_note)

    Returns:
        PeriodCloseResponse with closure details

    Raises:
        ValidationError: If DRAFT journals exist or period already closed
        BadRequest: If trial balance not balanced
    """
    if current_user.school_id != school_id:
        raise HTTPException(status_code=403, detail="Not authorized for this school")

    service = PeriodService(db)

    try:
        result = await service.close_accounting_period(
            school_id,
            period_id,
            current_user.id,
            request.closing_note,
        )

        return APIResponse.success(
            PeriodCloseResponse(
                period_id=result["period_id"],
                period_name=result["period_name"],
                closed_at=result["closed_at"],
                closed_by_id=result["closed_by_id"],
                retained_earnings_account_id=result["retained_earnings_account_id"],
                retained_earnings_amount=result["retained_earnings_amount"],
                opening_balances_created=result["opening_balances_created"],
                message=result["message"],
            ),
            message="Period closed successfully",
        )

    except ValidationError as e:
        raise HTTPException(status_code=400, detail=str(e.detail))
    except NotFoundError as e:
        raise HTTPException(status_code=404, detail=str(e.detail))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Period close failed: {str(e)}")


@router.post("/{period_id}/reopen", response_model=APIResponse[dict])
async def reopen_period(
    school_id: UUID,
    period_id: UUID,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """
    Reopen a closed period (for corrections).

    CAUTION: Can only reopen if next period is not yet closed.
    Used to correct errors discovered after period closure.

    Args:
        period_id: Period to reopen

    Returns:
        Confirmation of reopen

    Raises:
        ValidationError: If period not closed or next period is closed
    """
    if current_user.school_id != school_id:
        raise HTTPException(status_code=403, detail="Not authorized for this school")

    service = PeriodService(db)

    try:
        result = await service.reopen_accounting_period(
            school_id, period_id, current_user.id
        )

        return APIResponse.success(
            result,
            message=result["message"],
        )

    except ValidationError as e:
        raise HTTPException(status_code=400, detail=str(e.detail))
    except NotFoundError as e:
        raise HTTPException(status_code=404, detail=str(e.detail))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Period reopen failed: {str(e)}")
