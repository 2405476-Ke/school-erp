"""
Fee management routers: FastAPI endpoints for billing and receipts.
Full validation, error handling, and GL integration.
"""
from datetime import date, datetime
from typing import List, Optional
from uuid import UUID

from fastapi import APIRouter, Depends, Query, HTTPException
from sqlalchemy import and_, select
from sqlalchemy.ext.asyncio import AsyncSession

from src.core.database import get_db
from src.core.security import get_current_user
from src.modules.finance.repositories.fees_repo import (
    FeeStructureRepository,
    FeeVoteHeadRepository,
    FeeInvoiceRepository,
    FeeReceiptRepository,
    StudentFeeAccountRepository,
)
from src.modules.finance.services.billing_service import BillingService
from src.modules.finance.services.receipt_service import ReceiptService
from src.modules.finance.schemas.fees import (
    BillingRunRequest,
    BillingRunResponse,
    FeeInvoiceResponse,
    FeeReceiptCreate,
    FeeReceiptResponse,
    FeeStructureCreate,
    FeeStructureResponse,
    FeeVoteHeadCreate,
    FeeVoteHeadResponse,
    FeeVoteHeadUpdate,
    ReceiptPostRequest,
    StudentFeeStatement,
    StudentFeeStatementLine,
)
from src.modules.users.models import User
from src.shared.exceptions import NotFoundError, ValidationError
from src.shared.response import APIResponse

router = APIRouter(prefix="/finance", tags=["finance"])


# ============================================================================
# FEE VOTE HEADS
# ============================================================================


@router.post("/fee-vote-heads", response_model=APIResponse[FeeVoteHeadResponse])
async def create_fee_vote_head(
    school_id: UUID,
    data: FeeVoteHeadCreate,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Create a new fee vote head (budget line item)."""
    if current_user.school_id != school_id:
        raise HTTPException(status_code=403, detail="Not authorized for this school")

    repo = FeeVoteHeadRepository(db)

    # Check name uniqueness
    existing = await repo.get_by_name(school_id, data.name)
    if existing:
        raise HTTPException(
            status_code=409,
            detail=f"Vote head '{data.name}' already exists",
        )

    vote_head = await repo.create({
        "school_id": school_id,
        "name": data.name,
        "description": data.description,
        "account_id": data.account_id,
        "priority": data.priority,
        "is_restricted": data.is_restricted,
        "allow_arrears_carry": data.allow_arrears_carry,
        "is_active": data.is_active,
    })

    return APIResponse.success(
        FeeVoteHeadResponse.model_validate(vote_head),
        message="Vote head created",
    )


@router.get("/fee-vote-heads", response_model=APIResponse[List[FeeVoteHeadResponse]])
async def list_fee_vote_heads(
    school_id: UUID,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """List all fee vote heads for a school."""
    if current_user.school_id != school_id:
        raise HTTPException(status_code=403, detail="Not authorized for this school")

    repo = FeeVoteHeadRepository(db)
    vote_heads = await repo.get_active_by_priority(school_id)

    return APIResponse.success(
        [FeeVoteHeadResponse.model_validate(vh) for vh in vote_heads],
        message=f"Retrieved {len(vote_heads)} vote heads",
    )


@router.put("/fee-vote-heads/{vote_head_id}", response_model=APIResponse[FeeVoteHeadResponse])
async def update_fee_vote_head(
    school_id: UUID,
    vote_head_id: UUID,
    data: FeeVoteHeadUpdate,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Update a fee vote head."""
    if current_user.school_id != school_id:
        raise HTTPException(status_code=403, detail="Not authorized for this school")

    repo = FeeVoteHeadRepository(db)
    vote_head = await repo.get_by_id(vote_head_id)

    if not vote_head or vote_head.school_id != school_id:
        raise HTTPException(status_code=404, detail="Vote head not found")

    updated = await repo.update(vote_head_id, data.model_dump(exclude_unset=True))

    return APIResponse.success(
        FeeVoteHeadResponse.model_validate(updated),
        message="Vote head updated",
    )


# ============================================================================
# FEE STRUCTURES
# ============================================================================


@router.post("/fee-structures", response_model=APIResponse[FeeStructureResponse])
async def create_fee_structure(
    school_id: UUID,
    data: FeeStructureCreate,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Create a new fee structure."""
    if current_user.school_id != school_id:
        raise HTTPException(status_code=403, detail="Not authorized for this school")

    repo = FeeStructureRepository(db)

    # Check uniqueness
    existing = await repo.get_for_term(
        school_id,
        data.academic_year_id,
        data.term_id,
        data.boarding_type,
        data.curriculum_type,
    )
    if existing:
        raise HTTPException(
            status_code=409,
            detail=f"Fee structure already exists for {data.boarding_type}/{data.curriculum_type}",
        )

    # Calculate total
    total_amount = sum((item.amount for item in data.items))

    # Create structure
    fee_structure = await repo.create({
        "school_id": school_id,
        "academic_year_id": data.academic_year_id,
        "term_id": data.term_id,
        "boarding_type": data.boarding_type,
        "curriculum_type": data.curriculum_type,
        "total_amount": total_amount,
        "is_active": data.is_active,
    })
    await db.flush()

    # Create items
    from src.modules.finance.models.fees import FeeStructureItem

    for item_data in data.items:
        item = FeeStructureItem(
            fee_structure_id=fee_structure.id,
            vote_head_id=item_data.vote_head_id,
            amount=item_data.amount,
        )
        db.add(item)

    await db.commit()

    # Reload with items
    fee_structure = await repo.get_by_id(fee_structure.id)

    return APIResponse.success(
        FeeStructureResponse.model_validate(fee_structure),
        message="Fee structure created",
    )


@router.get("/fee-structures/{structure_id}", response_model=APIResponse[FeeStructureResponse])
async def get_fee_structure(
    school_id: UUID,
    structure_id: UUID,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Fetch a fee structure."""
    if current_user.school_id != school_id:
        raise HTTPException(status_code=403, detail="Not authorized for this school")

    repo = FeeStructureRepository(db)
    structure = await repo.get_by_id(structure_id)

    if not structure or structure.school_id != school_id:
        raise HTTPException(status_code=404, detail="Fee structure not found")

    return APIResponse.success(
        FeeStructureResponse.model_validate(structure),
        message="Fee structure retrieved",
    )


# ============================================================================
# BILLING (Termly Invoice Generation)
# ============================================================================


@router.post("/billing/run-termly-billing", response_model=APIResponse[BillingRunResponse])
async def run_termly_billing(
    school_id: UUID,
    data: BillingRunRequest,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """
    Run termly billing: generate invoices for all active students.

    Process:
    1. Fetch term to validate
    2. Get all active students
    3. For each student:
       - Determine boarding/curriculum type
       - Find matching FeeStructure
       - Create FeeInvoice if not exists
       - Create FeeInvoiceItems for each structure item

    Returns: Count of invoices created, students processed, total billed, any errors
    """
    if current_user.school_id != school_id:
        raise HTTPException(status_code=403, detail="Not authorized for this school")

    service = BillingService(db)

    try:
        result = await service.run_termly_billing(
            school_id,
            data.academic_year_id,
            data.term_id,
            current_user.id,
        )

        return APIResponse.success(
            BillingRunResponse(
                invoices_created=result["invoices_created"],
                students_processed=result["students_processed"],
                total_billed=result["total_billed"],
                timestamp=result["timestamp"],
            ),
            message="Billing run completed",
            meta={
                "errors": result["errors"],
            },
        )

    except ValidationError as e:
        raise HTTPException(status_code=400, detail=str(e.detail))
    except NotFoundError as e:
        raise HTTPException(status_code=404, detail=str(e.detail))


# ============================================================================
# STUDENT FEE STATEMENTS
# ============================================================================


@router.get("/students/{student_id}/fee-statement", response_model=APIResponse[StudentFeeStatement])
async def get_student_fee_statement(
    school_id: UUID,
    student_id: UUID,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """
    Get a student's fee statement: all invoices and running balance.

    Shows:
    - Total arrears (running_balance from StudentFeeAccount)
    - List of invoices with amounts paid, outstanding
    - Total owing
    """
    if current_user.school_id != school_id:
        raise HTTPException(status_code=403, detail="Not authorized for this school")

    # Get student
    from src.modules.students.models import Student

    student_query = select(Student).where(
        and_(
            Student.id == student_id,
            Student.school_id == school_id,
            Student.is_deleted == False,
        )
    )
    student_result = await db.execute(student_query)
    student = student_result.scalar_one_or_none()

    if not student:
        raise HTTPException(status_code=404, detail="Student not found")

    # Get fee account
    student_account_repo = StudentFeeAccountRepository(db)
    student_account = await student_account_repo.get_for_student(student_id)
    total_arrears = student_account.running_balance if student_account else 0

    # Get all invoices
    invoice_repo = FeeInvoiceRepository(db)
    invoices = await invoice_repo.get_unpaid_for_student(student_id)

    # Get term names
    from src.modules.academic.models import Term

    terms_query = select(Term)
    terms_result = await db.execute(terms_query)
    terms_dict = {term.id: term for term in terms_result.scalars().all()}

    statement_lines = []
    total_owing = 0

    for invoice in invoices:
        term = terms_dict.get(invoice.term_id)
        term_name = term.term_name if term else "Unknown"
        outstanding = invoice.total_amount - invoice.amount_paid

        statement_lines.append(
            StudentFeeStatementLine(
                invoice_number=invoice.invoice_number,
                invoice_date=invoice.invoice_date,
                term_name=term_name,
                total_amount=invoice.total_amount,
                amount_paid=invoice.amount_paid,
                status=invoice.status,
                outstanding=outstanding,
            )
        )
        total_owing += outstanding

    return APIResponse.success(
        StudentFeeStatement(
            student_id=student_id,
            student_name=f"{student.first_name} {student.last_name}",
            total_arrears=total_arrears,
            invoices=statement_lines,
            total_owing=total_owing,
        ),
        message="Fee statement retrieved",
    )


# ============================================================================
# FEE RECEIPTS
# ============================================================================


@router.post("/receipts", response_model=APIResponse[FeeReceiptResponse])
async def create_fee_receipt(
    school_id: UUID,
    data: FeeReceiptCreate,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """
    Create a new fee receipt (UNPOSTED).

    The receipt is created but not yet allocated to invoices or posted to GL.
    Call POST /receipts/{receipt_id}/allocate to allocate and post GL.
    """
    if current_user.school_id != school_id:
        raise HTTPException(status_code=403, detail="Not authorized for this school")

    service = ReceiptService(db)

    try:
        receipt = await service.create_receipt(
            school_id,
            data.student_id,
            data.receipt_date,
            data.amount,
            data.payment_method,
            data.reference_number,
            current_user.id,
        )

        return APIResponse.success(
            FeeReceiptResponse.model_validate(receipt),
            message="Receipt created (UNPOSTED)",
        )

    except ValidationError as e:
        raise HTTPException(status_code=400, detail=str(e.detail))
    except NotFoundError as e:
        raise HTTPException(status_code=404, detail=str(e.detail))


@router.get("/receipts/{receipt_id}", response_model=APIResponse[FeeReceiptResponse])
async def get_fee_receipt(
    school_id: UUID,
    receipt_id: UUID,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Fetch a fee receipt."""
    if current_user.school_id != school_id:
        raise HTTPException(status_code=403, detail="Not authorized for this school")

    repo = FeeReceiptRepository(db)
    receipt = await repo.get_by_id(receipt_id)

    if not receipt or receipt.school_id != school_id:
        raise HTTPException(status_code=404, detail="Receipt not found")

    return APIResponse.success(
        FeeReceiptResponse.model_validate(receipt),
        message="Receipt retrieved",
    )


@router.post(
    "/receipts/{receipt_id}/allocate",
    response_model=APIResponse[FeeReceiptResponse],
)
async def allocate_fee_receipt(
    school_id: UUID,
    receipt_id: UUID,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """
    Allocate a receipt to invoices and post to General Ledger.

    CRITICAL OPERATION:
    1. Fetch unpaid invoices for student
    2. Process payment allocation by priority
    3. Create GL journal entry (DR Bank, CR Revenue)
    4. Post journal atomically
    5. Update student fee account balance
    6. Mark receipt as POSTED

    This is the heart of the fee billing system.

    Raises:
        ValidationError: If receipt already posted or student has no invoices
        Exception: If GL posting fails (entire operation rolls back)
    """
    if current_user.school_id != school_id:
        raise HTTPException(status_code=403, detail="Not authorized for this school")

    service = ReceiptService(db)

    try:
        receipt = await service.allocate_payment(
            school_id,
            receipt_id,
            current_user.id,
        )

        return APIResponse.success(
            FeeReceiptResponse.model_validate(receipt),
            message="Receipt allocated and posted to GL",
        )

    except ValidationError as e:
        raise HTTPException(status_code=400, detail=str(e.detail))
    except NotFoundError as e:
        raise HTTPException(status_code=404, detail=str(e.detail))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Allocation failed: {str(e)}")


@router.get("/receipts", response_model=APIResponse[List[FeeReceiptResponse]])
async def list_fee_receipts(
    school_id: UUID,
    student_id: Optional[UUID] = Query(None),
    posted_only: bool = Query(False),
    skip: int = Query(0, ge=0),
    limit: int = Query(50, ge=1, le=500),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """
    List fee receipts with optional filtering.

    Args:
        student_id: Filter by student (optional)
        posted_only: Filter to only posted receipts (optional)
        skip: Pagination offset
        limit: Pagination limit
    """
    if current_user.school_id != school_id:
        raise HTTPException(status_code=403, detail="Not authorized for this school")

    if student_id:
        repo = FeeReceiptRepository(db)
        receipts = await repo.get_for_student(student_id, posted_only=posted_only)
        receipts = receipts[skip : skip + limit]

    else:
        # List all receipts for school
        from src.modules.finance.models.fees import FeeReceipt

        filters = [
            FeeReceipt.school_id == school_id,
            FeeReceipt.is_deleted == False,
        ]
        if posted_only:
            filters.append(FeeReceipt.is_posted == True)

        query = (
            select(FeeReceipt)
            .where(and_(*filters))
            .order_by(FeeReceipt.receipt_date.desc())
            .offset(skip)
            .limit(limit)
        )
        result = await db.execute(query)
        receipts = result.scalars().all()

    return APIResponse.success(
        [FeeReceiptResponse.model_validate(r) for r in receipts],
        message=f"Retrieved {len(receipts)} receipts",
    )
