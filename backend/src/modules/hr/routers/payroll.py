"""
Routers for HR and Payroll System.

Endpoints for:
- Staff management (CRUD)
- Payroll run processing and approval
- KRA P10 report generation
"""

import logging
from uuid import UUID
from datetime import datetime

from fastapi import APIRouter, Depends, Query
from sqlalchemy import and_, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from src.core.database import get_db
from src.core.exceptions import NotFoundError, ValidationError
from src.core.response import APIResponse
from src.modules.hr.models.hr_payroll import (
    Staff,
    PayrollRun,
    PayrollEntry,
    EmploymentType,
    PayrollStatus,
)
from src.modules.hr.schemas.hr_payroll import (
    StaffCreate,
    StaffUpdate,
    StaffResponse,
    PayrollRunCreate,
    PayrollRunResponse,
    PayrollRunDetailResponse,
    PayrollRunProcessRequest,
    PayrollRunApproveInput,
    PayrollEntryDetailResponse,
    P10Report,
    P10ReportLine,
)
from src.modules.hr.services.payroll_run_service import PayrollRunService

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/hr", tags=["HR & Payroll"])


# ============================================================================
# STAFF MANAGEMENT
# ============================================================================


@router.post("/staff", response_model=APIResponse)
async def create_staff(
    request: StaffCreate,
    db: AsyncSession = Depends(get_db),
    school_id: UUID = Depends(lambda: UUID("00000000-0000-0000-0000-000000000000")),
) -> APIResponse:
    """
    Create a new staff member.
    
    Example:
    {
        "first_name": "John",
        "last_name": "Doe",
        "employee_number": "EMP001",
        "employment_type": "BOM",
        "kra_pin": "A001234567A",
        "basic_pay": 50000
    }
    """
    try:
        # Check for duplicate employee number
        existing_query = select(Staff).where(
            and_(
                Staff.school_id == school_id,
                Staff.employee_number == request.employee_number,
            )
        )
        existing = await db.scalar(existing_query)

        if existing:
            return APIResponse.error(
                error="Employee number already exists",
                message=f"Employee number {request.employee_number} already registered",
                status_code=400,
            )

        # Check for duplicate KRA PIN
        existing_kra_query = select(Staff).where(
            and_(
                Staff.school_id == school_id,
                Staff.kra_pin == request.kra_pin,
            )
        )
        existing_kra = await db.scalar(existing_kra_query)

        if existing_kra:
            return APIResponse.error(
                error="KRA PIN already exists",
                message=f"KRA PIN {request.kra_pin} already registered",
                status_code=400,
            )

        # Create staff
        staff = Staff(
            school_id=school_id,
            first_name=request.first_name,
            last_name=request.last_name,
            email=request.email,
            phone=request.phone,
            employee_number=request.employee_number,
            employment_type=request.employment_type,
            kra_pin=request.kra_pin,
            tsc_number=request.tsc_number,
            bank_account=request.bank_account,
            bank_name=request.bank_name,
            id_number=request.id_number,
            basic_pay=request.basic_pay,
            is_active=True,
        )
        db.add(staff)
        await db.commit()

        response = StaffResponse(
            id=staff.id,
            employee_number=staff.employee_number,
            first_name=staff.first_name,
            last_name=staff.last_name,
            email=staff.email,
            phone=staff.phone,
            employment_type=staff.employment_type.value,
            kra_pin=staff.kra_pin,
            tsc_number=staff.tsc_number,
            bank_account=staff.bank_account,
            bank_name=staff.bank_name,
            basic_pay=staff.basic_pay,
            is_active=staff.is_active,
            created_at=staff.created_at.isoformat(),
        )

        return APIResponse.success(
            data=response,
            message=f"Staff {staff.first_name} {staff.last_name} created",
            status_code=201,
        )

    except Exception as e:
        logger.error(f"Error creating staff: {e}")
        return APIResponse.error(
            error=str(e),
            message="Failed to create staff",
            status_code=500,
        )


@router.get("/staff/{staff_id}", response_model=APIResponse)
async def get_staff(
    staff_id: UUID,
    db: AsyncSession = Depends(get_db),
    school_id: UUID = Depends(lambda: UUID("00000000-0000-0000-0000-000000000000")),
) -> APIResponse:
    """Get staff details."""
    try:
        query = select(Staff).where(
            and_(
                Staff.id == staff_id,
                Staff.school_id == school_id,
            )
        )
        staff = await db.scalar(query)

        if not staff:
            return APIResponse.error(
                error="Staff not found",
                message="Invalid staff ID",
                status_code=404,
            )

        response = StaffResponse(
            id=staff.id,
            employee_number=staff.employee_number,
            first_name=staff.first_name,
            last_name=staff.last_name,
            email=staff.email,
            phone=staff.phone,
            employment_type=staff.employment_type.value,
            kra_pin=staff.kra_pin,
            tsc_number=staff.tsc_number,
            bank_account=staff.bank_account,
            bank_name=staff.bank_name,
            basic_pay=staff.basic_pay,
            is_active=staff.is_active,
            created_at=staff.created_at.isoformat(),
        )

        return APIResponse.success(
            data=response,
            message="Staff retrieved",
            status_code=200,
        )

    except Exception as e:
        logger.error(f"Error retrieving staff: {e}")
        return APIResponse.error(
            error=str(e),
            message="Failed to retrieve staff",
            status_code=500,
        )


@router.get("/staff", response_model=APIResponse)
async def list_staff(
    db: AsyncSession = Depends(get_db),
    school_id: UUID = Depends(lambda: UUID("00000000-0000-0000-0000-000000000000")),
    is_active: bool = Query(True, description="Filter by active status"),
) -> APIResponse:
    """List all staff."""
    try:
        query = select(Staff).where(
            and_(
                Staff.school_id == school_id,
                Staff.is_active == is_active,
            )
        ).order_by(Staff.employee_number)

        result = await db.execute(query)
        staff_list = result.scalars().all()

        responses = [
            StaffResponse(
                id=staff.id,
                employee_number=staff.employee_number,
                first_name=staff.first_name,
                last_name=staff.last_name,
                email=staff.email,
                phone=staff.phone,
                employment_type=staff.employment_type.value,
                kra_pin=staff.kra_pin,
                tsc_number=staff.tsc_number,
                bank_account=staff.bank_account,
                bank_name=staff.bank_name,
                basic_pay=staff.basic_pay,
                is_active=staff.is_active,
                created_at=staff.created_at.isoformat(),
            )
            for staff in staff_list
        ]

        return APIResponse.success(
            data=responses,
            message=f"Found {len(responses)} staff members",
            status_code=200,
        )

    except Exception as e:
        logger.error(f"Error listing staff: {e}")
        return APIResponse.error(
            error=str(e),
            message="Failed to list staff",
            status_code=500,
        )


# ============================================================================
# PAYROLL RUN MANAGEMENT
# ============================================================================


@router.post("/payroll/runs", response_model=APIResponse)
async def create_payroll_run(
    request: PayrollRunCreate,
    db: AsyncSession = Depends(get_db),
    school_id: UUID = Depends(lambda: UUID("00000000-0000-0000-0000-000000000000")),
) -> APIResponse:
    """
    Create a new payroll run for a month/year.
    
    Example:
    {
        "period_month": 1,
        "period_year": 2024,
        "description": "January 2024 payroll"
    }
    """
    try:
        # Check for duplicate run
        existing_query = select(PayrollRun).where(
            and_(
                PayrollRun.school_id == school_id,
                PayrollRun.period_month == request.period_month,
                PayrollRun.period_year == request.period_year,
            )
        )
        existing = await db.scalar(existing_query)

        if existing:
            return APIResponse.error(
                error="Payroll run already exists",
                message=f"Payroll run for {request.period_month}/{request.period_year} already exists",
                status_code=400,
            )

        # Create payroll run
        payroll_run = PayrollRun(
            school_id=school_id,
            period_month=request.period_month,
            period_year=request.period_year,
            status=PayrollStatus.DRAFT,
            description=request.description,
        )
        db.add(payroll_run)
        await db.commit()

        response = PayrollRunResponse(
            id=payroll_run.id,
            period_month=payroll_run.period_month,
            period_year=payroll_run.period_year,
            status=payroll_run.status.value,
            description=payroll_run.description,
            processed_by=payroll_run.processed_by,
            processed_at=payroll_run.processed_at.isoformat() if payroll_run.processed_at else None,
            approved_by=payroll_run.approved_by,
            approved_at=payroll_run.approved_at.isoformat() if payroll_run.approved_at else None,
            total_gross_pay=payroll_run.total_gross_pay,
            total_net_pay=payroll_run.total_net_pay,
            total_paye_deducted=payroll_run.total_paye_deducted,
            total_nssf_deducted=payroll_run.total_nssf_deducted,
            total_sha_deducted=payroll_run.total_sha_deducted,
            total_housing_levy_deducted=payroll_run.total_housing_levy_deducted,
            created_at=payroll_run.created_at.isoformat(),
        )

        return APIResponse.success(
            data=response,
            message=f"Payroll run created for {request.period_month}/{request.period_year}",
            status_code=201,
        )

    except Exception as e:
        logger.error(f"Error creating payroll run: {e}")
        return APIResponse.error(
            error=str(e),
            message="Failed to create payroll run",
            status_code=500,
        )


@router.post("/payroll/runs/{run_id}/process", response_model=APIResponse)
async def process_payroll_run(
    run_id: UUID,
    request: PayrollRunProcessRequest,
    db: AsyncSession = Depends(get_db),
    school_id: UUID = Depends(lambda: UUID("00000000-0000-0000-0000-000000000000")),
) -> APIResponse:
    """
    CRITICAL ENDPOINT: Process payroll run.
    
    This calculates all salary deductions for all staff and creates payroll entries.
    
    ALGORITHM (see PayrollRunService.process_payroll_run):
    1. Fetch all active staff
    2. For each staff:
       - Calculate taxes using TaxEngine.calculate_taxes()
       - Create PayrollEntry with full salary breakdown
       - Include all statutory deductions (NSSF, PAYE, SHA, Housing)
    3. Update run totals
    4. Change status to PROCESSED
    
    Example:
    {
        "processed_by": "550e8400-e29b-41d4-a716-446655440000"
    }
    """
    try:
        service = PayrollRunService(db)
        result = await service.process_payroll_run(
            school_id=school_id,
            run_id=run_id,
            processed_by=request.processed_by,
        )

        return APIResponse.success(
            data=result,
            message="Payroll run processed successfully",
            status_code=200,
        )

    except NotFoundError as e:
        logger.warning(f"Payroll run not found: {e}")
        return APIResponse.error(
            error=str(e),
            message="Payroll run not found",
            status_code=404,
        )

    except ValidationError as e:
        logger.warning(f"Payroll run validation error: {e}")
        return APIResponse.error(
            error=str(e),
            message="Cannot process payroll run",
            status_code=400,
        )

    except Exception as e:
        logger.error(f"Error processing payroll run: {e}", exc_info=True)
        return APIResponse.error(
            error=str(e),
            message="Failed to process payroll run",
            status_code=500,
        )


@router.post("/payroll/runs/{run_id}/approve", response_model=APIResponse)
async def approve_payroll_run(
    run_id: UUID,
    request: PayrollRunApproveInput,
    db: AsyncSession = Depends(get_db),
    school_id: UUID = Depends(lambda: UUID("00000000-0000-0000-0000-000000000000")),
) -> APIResponse:
    """
    CRITICAL ENDPOINT: Approve payroll run and post GL entries.
    
    This MUST integrate with General Ledger:
    1. Locks all payroll entries (no further edits)
    2. Posts journal entries to GL:
       - DR Salary Expense (Total Gross)
       - CR Net Salary Payable
       - CR PAYE Control
       - CR NSSF Control
       - CR SHA Control
       - CR Housing Levy Control
    3. Changes status to APPROVED
    
    CRITICAL: GL posting must be atomic (all-or-nothing). If GL posting fails,
    entire approval is rolled back.
    
    Example:
    {
        "approved_by": "550e8400-e29b-41d4-a716-446655440000"
    }
    """
    try:
        service = PayrollRunService(db)
        result = await service.approve_payroll_run(
            school_id=school_id,
            run_id=run_id,
            approved_by=request.approved_by,
        )

        return APIResponse.success(
            data=result,
            message="Payroll run approved and GL entries posted",
            status_code=200,
        )

    except NotFoundError as e:
        logger.warning(f"Payroll run not found: {e}")
        return APIResponse.error(
            error=str(e),
            message="Payroll run not found",
            status_code=404,
        )

    except ValidationError as e:
        logger.warning(f"Payroll run approval error: {e}")
        return APIResponse.error(
            error=str(e),
            message="Cannot approve payroll run",
            status_code=400,
        )

    except Exception as e:
        logger.error(f"Error approving payroll run: {e}", exc_info=True)
        return APIResponse.error(
            error=str(e),
            message="Failed to approve payroll run",
            status_code=500,
        )


@router.get("/payroll/runs/{run_id}", response_model=APIResponse)
async def get_payroll_run(
    run_id: UUID,
    db: AsyncSession = Depends(get_db),
    school_id: UUID = Depends(lambda: UUID("00000000-0000-0000-0000-000000000000")),
) -> APIResponse:
    """Get detailed payroll run with all entries."""
    try:
        service = PayrollRunService(db)
        payroll_run = await service.get_payroll_run(school_id, run_id)

        # Build detailed response
        entry_responses = []
        for entry in payroll_run.entries:
            allowance_lines = [
                {
                    "id": str(a.id),
                    "allowance_type": a.allowance_type,
                    "amount": str(a.amount),
                    "description": a.description,
                }
                for a in entry.allowance_lines
            ]

            deduction_lines = [
                {
                    "id": str(d.id),
                    "deduction_type": d.deduction_type,
                    "amount": str(d.amount),
                    "description": d.description,
                }
                for d in entry.deduction_lines
            ]

            entry_response = PayrollEntryDetailResponse(
                id=entry.id,
                payroll_run_id=entry.payroll_run_id,
                staff_id=entry.staff_id,
                employee_number=entry.staff.employee_number,
                staff_name=f"{entry.staff.first_name} {entry.staff.last_name}",
                basic_pay=entry.basic_pay,
                total_allowances=entry.total_allowances,
                gross_pay=entry.gross_pay,
                nssf_tier1=entry.nssf_tier1,
                nssf_tier2=entry.nssf_tier2,
                sha_nhif=entry.sha_nhif,
                housing_levy=entry.housing_levy,
                taxable_pay=entry.taxable_pay,
                paye=entry.paye,
                total_statutory_deductions=entry.total_statutory_deductions,
                total_other_deductions=entry.total_other_deductions,
                net_pay=entry.net_pay,
                allowance_lines=allowance_lines,
                deduction_lines=deduction_lines,
                is_locked=entry.is_locked,
            )
            entry_responses.append(entry_response)

        response = PayrollRunDetailResponse(
            id=payroll_run.id,
            period_month=payroll_run.period_month,
            period_year=payroll_run.period_year,
            status=payroll_run.status.value,
            description=payroll_run.description,
            processed_by=payroll_run.processed_by,
            processed_at=payroll_run.processed_at.isoformat() if payroll_run.processed_at else None,
            approved_by=payroll_run.approved_by,
            approved_at=payroll_run.approved_at.isoformat() if payroll_run.approved_at else None,
            total_gross_pay=payroll_run.total_gross_pay,
            total_net_pay=payroll_run.total_net_pay,
            total_paye_deducted=payroll_run.total_paye_deducted,
            total_nssf_deducted=payroll_run.total_nssf_deducted,
            total_sha_deducted=payroll_run.total_sha_deducted,
            total_housing_levy_deducted=payroll_run.total_housing_levy_deducted,
            entries=entry_responses,
            entry_count=len(entry_responses),
            created_at=payroll_run.created_at.isoformat(),
        )

        return APIResponse.success(
            data=response,
            message="Payroll run retrieved",
            status_code=200,
        )

    except NotFoundError as e:
        return APIResponse.error(
            error=str(e),
            message="Payroll run not found",
            status_code=404,
        )

    except Exception as e:
        logger.error(f"Error retrieving payroll run: {e}")
        return APIResponse.error(
            error=str(e),
            message="Failed to retrieve payroll run",
            status_code=500,
        )


# ============================================================================
# REPORTS
# ============================================================================


@router.get("/payroll/runs/{run_id}/reports/p10", response_model=APIResponse)
async def get_p10_report(
    run_id: UUID,
    db: AsyncSession = Depends(get_db),
    school_id: UUID = Depends(lambda: UUID("00000000-0000-0000-0000-000000000000")),
) -> APIResponse:
    """
    Generate KRA P10 report for payroll run.
    
    P10 Report:
    - Employee details (names, KRA PIN, TSC Number, ID Number)
    - Gross salary and allowances
    - PAYE tax deducted
    - Other statutory deductions (NSSF, SHA, Housing)
    - Net pay
    
    Can be exported to CSV/Excel for KRA submission.
    
    Example Response:
    {
        "success": true,
        "data": {
            "payroll_run_id": "550e8400-e29b-41d4-a716-446655440000",
            "period_month": 1,
            "period_year": 2024,
            "generated_at": "2024-02-15T14:30:00",
            "total_employees": 45,
            "total_gross_pay": "2250000.00",
            "total_paye": "285000.00",
            "total_nssf": "135000.00",
            "lines": [
                {
                    "employee_number": "EMP001",
                    "first_name": "John",
                    "last_name": "Doe",
                    "kra_pin": "A001234567A",
                    "gross_pay": "50000.00",
                    "paye_tax": "5285.00",
                    "net_pay": "42715.00"
                }
            ]
        }
    }
    """
    try:
        service = PayrollRunService(db)
        p10_lines = await service.get_p10_report_data(school_id, run_id)

        # Fetch run for totals
        run_query = select(PayrollRun).where(
            and_(
                PayrollRun.id == run_id,
                PayrollRun.school_id == school_id,
            )
        )
        payroll_run = await db.scalar(run_query)

        if not payroll_run:
            return APIResponse.error(
                error="Payroll run not found",
                message="Invalid payroll run ID",
                status_code=404,
            )

        # Convert lines to response objects
        p10_report_lines = [
            P10ReportLine(
                employee_number=line["employee_number"],
                first_name=line["first_name"],
                last_name=line["last_name"],
                kra_pin=line["kra_pin"],
                tsc_number=line["tsc_number"],
                id_number=line["id_number"],
                basic_pay=line["basic_pay"],
                allowances=line["allowances"],
                gross_pay=line["gross_pay"],
                nssf_deduction=line["nssf_deduction"],
                sha_deduction=line["sha_deduction"],
                housing_levy=line["housing_levy"],
                paye_tax=line["paye_tax"],
                net_pay=line["net_pay"],
            )
            for line in p10_lines
        ]

        report = P10Report(
            payroll_run_id=payroll_run.id,
            period_month=payroll_run.period_month,
            period_year=payroll_run.period_year,
            generated_at=datetime.utcnow().isoformat(),
            total_employees=len(p10_report_lines),
            total_gross_pay=payroll_run.total_gross_pay,
            total_paye=payroll_run.total_paye_deducted,
            total_nssf=payroll_run.total_nssf_deducted,
            lines=p10_report_lines,
        )

        return APIResponse.success(
            data=report,
            message="P10 report generated",
            status_code=200,
        )

    except NotFoundError as e:
        return APIResponse.error(
            error=str(e),
            message="Payroll run or entries not found",
            status_code=404,
        )

    except Exception as e:
        logger.error(f"Error generating P10 report: {e}")
        return APIResponse.error(
            error=str(e),
            message="Failed to generate P10 report",
            status_code=500,
        )
