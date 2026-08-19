"""
Ledger routers: FastAPI endpoints for Chart of Accounts, Financial Periods, and General Ledger.
Full validation, error handling, and proper HTTP status codes.
"""
from typing import List, Optional
from uuid import UUID

from fastapi import APIRouter, Depends, Query, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession

from src.core.database import get_db
from src.core.security import get_current_user
from src.modules.finance.repositories.ledger_repo import (
    AccountRepository,
    AccountingPeriodRepository,
    CostCenterRepository,
    FinancialYearRepository,
    JournalEntryRepository,
    AccountBalanceRepository,
)
from src.modules.finance.services.journal_service import JournalService
from src.modules.finance.schemas.ledger import (
    AccountCreate,
    AccountResponse,
    AccountTreeResponse,
    AccountUpdate,
    AccountingPeriodCreate,
    AccountingPeriodResponse,
    CostCenterCreate,
    CostCenterResponse,
    CostCenterUpdate,
    FinancialYearCreate,
    FinancialYearResponse,
    JournalEntryCreate,
    JournalEntryPostRequest,
    JournalEntryResponse,
    JournalEntryReverseRequest,
    AccountBalanceResponse,
    TrialBalanceReport,
    GeneralLedgerReport,
)
from src.modules.users.models import User
from src.shared.exceptions import NotFoundError, ValidationError
from src.shared.response import APIResponse

router = APIRouter(prefix="/finance", tags=["finance"])


# ============================================================================
# FINANCIAL YEARS
# ============================================================================


@router.post("/financial-years", response_model=APIResponse[FinancialYearResponse])
async def create_financial_year(
    school_id: UUID,
    data: FinancialYearCreate,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Create a new financial year."""
    if current_user.school_id != school_id:
        raise HTTPException(status_code=403, detail="Not authorized for this school")

    repo = FinancialYearRepository(db)

    # Check uniqueness
    existing = await repo.get_year_by_name(school_id, data.year_name)
    if existing:
        raise HTTPException(
            status_code=409,
            detail=f"Financial year '{data.year_name}' already exists",
        )

    year_obj = await repo.create({
        "school_id": school_id,
        "year_name": data.year_name,
        "start_date": data.start_date,
        "end_date": data.end_date,
        "status": "OPEN",
    })

    return APIResponse.success(
        FinancialYearResponse.model_validate(year_obj),
        message="Financial year created",
    )


@router.get("/financial-years/{year_id}", response_model=APIResponse[FinancialYearResponse])
async def get_financial_year(
    school_id: UUID,
    year_id: UUID,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Fetch a financial year."""
    if current_user.school_id != school_id:
        raise HTTPException(status_code=403, detail="Not authorized for this school")

    repo = FinancialYearRepository(db)
    year_obj = await repo.get_by_id(year_id)

    if not year_obj or year_obj.school_id != school_id:
        raise HTTPException(status_code=404, detail="Financial year not found")

    return APIResponse.success(
        FinancialYearResponse.model_validate(year_obj),
        message="Financial year retrieved",
    )


# ============================================================================
# ACCOUNTING PERIODS
# ============================================================================


@router.post(
    "/financial-years/{year_id}/periods",
    response_model=APIResponse[AccountingPeriodResponse],
)
async def create_accounting_period(
    school_id: UUID,
    year_id: UUID,
    data: AccountingPeriodCreate,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Create an accounting period."""
    if current_user.school_id != school_id:
        raise HTTPException(status_code=403, detail="Not authorized for this school")

    year_repo = FinancialYearRepository(db)
    year_obj = await year_repo.get_by_id(year_id)

    if not year_obj or year_obj.school_id != school_id:
        raise HTTPException(status_code=404, detail="Financial year not found")

    period_repo = AccountingPeriodRepository(db)
    period_obj = await period_repo.create({
        "school_id": school_id,
        "financial_year_id": year_id,
        "period_name": data.period_name,
        "period_number": data.period_number,
        "start_date": data.start_date,
        "end_date": data.end_date,
        "status": "FUTURE",
    })

    return APIResponse.success(
        AccountingPeriodResponse.model_validate(period_obj),
        message="Accounting period created",
    )


@router.get(
    "/periods/{period_id}",
    response_model=APIResponse[AccountingPeriodResponse],
)
async def get_accounting_period(
    school_id: UUID,
    period_id: UUID,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Fetch an accounting period."""
    if current_user.school_id != school_id:
        raise HTTPException(status_code=403, detail="Not authorized for this school")

    repo = AccountingPeriodRepository(db)
    period_obj = await repo.get_by_id(period_id)

    if not period_obj or period_obj.school_id != school_id:
        raise HTTPException(status_code=404, detail="Period not found")

    return APIResponse.success(
        AccountingPeriodResponse.model_validate(period_obj),
        message="Period retrieved",
    )


# ============================================================================
# CHART OF ACCOUNTS
# ============================================================================


@router.post("/accounts", response_model=APIResponse[AccountResponse])
async def create_account(
    school_id: UUID,
    data: AccountCreate,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Create a new account in the Chart of Accounts."""
    if current_user.school_id != school_id:
        raise HTTPException(status_code=403, detail="Not authorized for this school")

    account_repo = AccountRepository(db)

    # Check code uniqueness
    existing = await account_repo.get_by_code(school_id, data.code)
    if existing:
        raise HTTPException(
            status_code=409,
            detail=f"Account code '{data.code}' already exists in this school",
        )

    # Validate category exists
    from sqlalchemy import select
    from src.modules.finance.models.ledger import AccountCategory
    cat_query = select(AccountCategory).where(AccountCategory.id == data.category_id)
    cat_result = await db.execute(cat_query)
    category = cat_result.scalar_one_or_none()

    if not category:
        raise HTTPException(status_code=404, detail="Category not found")

    # Validate parent if provided
    if data.parent_id:
        parent = await account_repo.get_by_id(data.parent_id)
        if not parent or parent.school_id != school_id:
            raise HTTPException(status_code=404, detail="Parent account not found")

    account_obj = await account_repo.create({
        "school_id": school_id,
        "code": data.code,
        "name": data.name,
        "description": data.description,
        "is_control_account": data.is_control_account,
        "is_header": data.is_header,
        "is_active": True,
        "category_id": data.category_id,
        "parent_id": data.parent_id,
    })

    return APIResponse.success(
        AccountResponse.model_validate(account_obj),
        message="Account created",
    )


@router.get("/accounts/{account_id}", response_model=APIResponse[AccountResponse])
async def get_account(
    school_id: UUID,
    account_id: UUID,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Fetch an account."""
    if current_user.school_id != school_id:
        raise HTTPException(status_code=403, detail="Not authorized for this school")

    repo = AccountRepository(db)
    account_obj = await repo.get_by_id(account_id)

    if not account_obj or account_obj.school_id != school_id:
        raise HTTPException(status_code=404, detail="Account not found")

    return APIResponse.success(
        AccountResponse.model_validate(account_obj),
        message="Account retrieved",
    )


@router.put("/accounts/{account_id}", response_model=APIResponse[AccountResponse])
async def update_account(
    school_id: UUID,
    account_id: UUID,
    data: AccountUpdate,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Update an account."""
    if current_user.school_id != school_id:
        raise HTTPException(status_code=403, detail="Not authorized for this school")

    repo = AccountRepository(db)
    account_obj = await repo.get_by_id(account_id)

    if not account_obj or account_obj.school_id != school_id:
        raise HTTPException(status_code=404, detail="Account not found")

    # Validate no updates if account has posted lines
    has_posted = await repo.has_posted_lines(account_id)
    if has_posted and (data.is_active is False):
        raise HTTPException(
            status_code=400,
            detail="Cannot deactivate account with posted journal lines",
        )

    update_obj = await repo.update(account_id, data.model_dump(exclude_unset=True))

    return APIResponse.success(
        AccountResponse.model_validate(update_obj),
        message="Account updated",
    )


@router.get("/accounts/tree", response_model=APIResponse[List[AccountTreeResponse]])
async def get_accounts_tree(
    school_id: UUID,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Get full Chart of Accounts as hierarchical tree."""
    if current_user.school_id != school_id:
        raise HTTPException(status_code=403, detail="Not authorized for this school")

    repo = AccountRepository(db)
    roots = await repo.get_tree_roots(school_id)

    def build_tree(account) -> AccountTreeResponse:
        """Recursively build tree structure."""
        return AccountTreeResponse(
            **{
                **AccountResponse.model_validate(account).model_dump(),
                "children": [build_tree(child) for child in account.children],
            }
        )

    tree = [build_tree(root) for root in roots]

    return APIResponse.success(
        tree,
        message="Chart of Accounts retrieved",
    )


# ============================================================================
# COST CENTERS
# ============================================================================


@router.post("/cost-centers", response_model=APIResponse[CostCenterResponse])
async def create_cost_center(
    school_id: UUID,
    data: CostCenterCreate,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Create a new cost center."""
    if current_user.school_id != school_id:
        raise HTTPException(status_code=403, detail="Not authorized for this school")

    repo = CostCenterRepository(db)

    existing = await repo.get_by_code(school_id, data.code)
    if existing:
        raise HTTPException(
            status_code=409,
            detail=f"Cost center code '{data.code}' already exists",
        )

    cc_obj = await repo.create({
        "school_id": school_id,
        "code": data.code,
        "name": data.name,
        "description": data.description,
        "is_active": data.is_active,
    })

    return APIResponse.success(
        CostCenterResponse.model_validate(cc_obj),
        message="Cost center created",
    )


@router.get("/cost-centers", response_model=APIResponse[List[CostCenterResponse]])
async def list_cost_centers(
    school_id: UUID,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """List all cost centers for a school."""
    if current_user.school_id != school_id:
        raise HTTPException(status_code=403, detail="Not authorized for this school")

    repo = CostCenterRepository(db)
    cost_centers = await repo.get_active(school_id)

    return APIResponse.success(
        [CostCenterResponse.model_validate(cc) for cc in cost_centers],
        message=f"Retrieved {len(cost_centers)} cost centers",
    )


# ============================================================================
# JOURNAL ENTRIES (CORE LEDGER)
# ============================================================================


@router.post("/journal-entries", response_model=APIResponse[JournalEntryResponse])
async def create_journal_entry(
    school_id: UUID,
    data: JournalEntryCreate,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """
    Create a new draft journal entry.

    The journal is created in DRAFT status and can be edited until posted.
    All business rules are validated: balance, period, account validity.
    """
    if current_user.school_id != school_id:
        raise HTTPException(status_code=403, detail="Not authorized for this school")

    service = JournalService(db)

    try:
        journal = await service.create_draft(school_id, data, current_user.id)
        return APIResponse.success(journal, message="Journal entry created (DRAFT)")
    except ValidationError as e:
        raise HTTPException(status_code=400, detail=str(e.detail))
    except NotFoundError as e:
        raise HTTPException(status_code=404, detail=str(e.detail))


@router.get("/journal-entries/{journal_id}", response_model=APIResponse[JournalEntryResponse])
async def get_journal_entry(
    school_id: UUID,
    journal_id: UUID,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Fetch a journal entry with all lines."""
    if current_user.school_id != school_id:
        raise HTTPException(status_code=403, detail="Not authorized for this school")

    service = JournalService(db)

    try:
        journal = await service.get_journal(school_id, journal_id)
        return APIResponse.success(journal, message="Journal entry retrieved")
    except NotFoundError as e:
        raise HTTPException(status_code=404, detail=str(e.detail))


@router.post(
    "/journal-entries/{journal_id}/post",
    response_model=APIResponse[JournalEntryResponse],
)
async def post_journal_entry(
    school_id: UUID,
    journal_id: UUID,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """
    Post a journal entry to the general ledger.

    This is the critical operation that:
    1. Validates period is still open
    2. Re-checks balance (defense in depth)
    3. Atomically updates AccountBalance records (with pessimistic locking)
    4. Marks journal as POSTED

    Once posted, the journal cannot be edited (only reversed).
    """
    if current_user.school_id != school_id:
        raise HTTPException(status_code=403, detail="Not authorized for this school")

    service = JournalService(db)

    try:
        journal = await service.post_journal(school_id, journal_id, current_user.id)
        return APIResponse.success(journal, message="Journal entry posted")
    except ValidationError as e:
        raise HTTPException(status_code=400, detail=str(e.detail))
    except NotFoundError as e:
        raise HTTPException(status_code=404, detail=str(e.detail))


@router.post(
    "/journal-entries/{journal_id}/reverse",
    response_model=APIResponse[JournalEntryResponse],
)
async def reverse_journal_entry(
    school_id: UUID,
    journal_id: UUID,
    data: JournalEntryReverseRequest,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """
    Reverse a posted journal entry.

    Creates a new POSTED journal with debits/credits swapped.
    Original journal is marked as REVERSED.
    Reversal can only happen in an OPEN period.
    """
    if current_user.school_id != school_id:
        raise HTTPException(status_code=403, detail="Not authorized for this school")

    service = JournalService(db)

    try:
        reversal = await service.reverse_journal(
            school_id, journal_id, current_user.id, data.reason
        )
        return APIResponse.success(
            reversal, message="Journal entry reversed (reversal posted)"
        )
    except ValidationError as e:
        raise HTTPException(status_code=400, detail=str(e.detail))
    except NotFoundError as e:
        raise HTTPException(status_code=404, detail=str(e.detail))


@router.get("/journal-entries", response_model=APIResponse)
async def list_journal_entries(
    school_id: UUID,
    period_id: Optional[UUID] = Query(None),
    status: Optional[str] = Query(None, regex="^(DRAFT|POSTED|REVERSED)$"),
    skip: int = Query(0, ge=0),
    limit: int = Query(50, ge=1, le=500),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """List journal entries with optional filtering."""
    if current_user.school_id != school_id:
        raise HTTPException(status_code=403, detail="Not authorized for this school")

    service = JournalService(db)
    journals, total = await service.list_journals(
        school_id, period_id=period_id, status=status, skip=skip, limit=limit
    )

    return APIResponse.success(
        [j.model_dump() for j in journals],
        message=f"Retrieved {len(journals)} journals",
        meta={"total": total, "skip": skip, "limit": limit},
    )


# ============================================================================
# ACCOUNT BALANCES
# ============================================================================


@router.get(
    "/accounts/{account_id}/balance/{period_id}",
    response_model=APIResponse[AccountBalanceResponse],
)
async def get_account_balance(
    school_id: UUID,
    account_id: UUID,
    period_id: UUID,
    cost_center_id: Optional[UUID] = Query(None),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Get account balance for a specific period (and optional cost center)."""
    if current_user.school_id != school_id:
        raise HTTPException(status_code=403, detail="Not authorized for this school")

    repo = AccountBalanceRepository(db)
    balance = await repo.get_for_account_period(account_id, period_id, cost_center_id)

    if not balance or balance.school_id != school_id:
        raise HTTPException(status_code=404, detail="Balance not found")

    return APIResponse.success(
        AccountBalanceResponse.model_validate(balance),
        message="Account balance retrieved",
    )


@router.get(
    "/periods/{period_id}/balances",
    response_model=APIResponse[List[AccountBalanceResponse]],
)
async def get_period_balances(
    school_id: UUID,
    period_id: UUID,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Get all account balances in a period."""
    if current_user.school_id != school_id:
        raise HTTPException(status_code=403, detail="Not authorized for this school")

    repo = AccountBalanceRepository(db)
    balances = await repo.get_by_period(school_id, period_id)

    return APIResponse.success(
        [AccountBalanceResponse.model_validate(b) for b in balances],
        message=f"Retrieved {len(balances)} balances",
    )
