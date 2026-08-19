"""
FastAPI routers for Boarding Management.

Endpoints for:
- Hostel and dormitory management
- Bed allocation and occupancy tracking
- Student leave pass (exeat) management
"""

import logging
from uuid import UUID
from datetime import datetime, date

from fastapi import APIRouter, Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession

from src.core.database import get_db
from src.core.exceptions import NotFoundError, ValidationError
from src.core.response import APIResponse
from src.modules.boarding.models.boarding import (
    Hostel,
    Dormitory,
    Bed,
)
from src.modules.boarding.schemas.boarding import (
    HostelCreate,
    HostelResponse,
    HostelDetailResponse,
    DormitoryCreate,
    DormitoryResponse,
    BedCreate,
    BedResponse,
    BedDetailResponse,
    BedAllocationRequest,
    BedAllocationResponse,
    AllocateBedResponse,
    RequestLeavePassRequest,
    LeavePassResponse,
    ApproveLeavePassRequest,
    ApproveLeavePassResponse,
    RecordDepartureRequest,
    RecordDepartureResponse,
    RecordReturnRequest,
    RecordReturnResponse,
    VerifyGateExitRequest,
    VerifyGateExitResponse,
    LeavePassListResponse,
)
from src.modules.boarding.services.bed_allocation_service import BedAllocationService
from src.modules.boarding.services.exeat_service import ExeatService

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/boarding", tags=["Boarding Management"])


# ============================================================================
# HOSTEL MANAGEMENT
# ============================================================================


@router.post("/hostels", response_model=APIResponse)
async def create_hostel(
    request: HostelCreate,
    db: AsyncSession = Depends(get_db),
    school_id: UUID = Depends(lambda: UUID("00000000-0000-0000-0000-000000000000")),
) -> APIResponse:
    """Create new hostel."""
    try:
        hostel = Hostel(
            school_id=school_id,
            name=request.name,
            code=request.code,
            capacity=request.capacity,
            description=request.description,
            matron_staff_id=request.matron_staff_id,
            is_active=True,
        )
        
        db.add(hostel)
        await db.commit()
        
        response = HostelResponse(
            id=hostel.id,
            name=hostel.name,
            code=hostel.code,
            capacity=hostel.capacity,
            current_occupancy=0,
            description=hostel.description,
            is_active=hostel.is_active,
            created_at=hostel.created_at,
        )
        
        return APIResponse.success(
            data=response,
            message=f"Hostel {request.name} created successfully",
            status_code=201,
        )
    
    except Exception as e:
        logger.error(f"Error creating hostel: {e}")
        return APIResponse.error(
            error=str(e),
            message="Failed to create hostel",
            status_code=500,
        )


@router.get("/hostels", response_model=APIResponse)
async def list_hostels(
    db: AsyncSession = Depends(get_db),
    school_id: UUID = Depends(lambda: UUID("00000000-0000-0000-0000-000000000000")),
) -> APIResponse:
    """List all hostels."""
    try:
        from sqlalchemy import select
        
        query = select(Hostel).where(Hostel.school_id == school_id)
        result = await db.execute(query)
        hostels = result.scalars().all()
        
        responses = [
            HostelResponse(
                id=h.id,
                name=h.name,
                code=h.code,
                capacity=h.capacity,
                current_occupancy=h.current_occupancy,
                description=h.description,
                is_active=h.is_active,
                created_at=h.created_at,
            )
            for h in hostels
        ]
        
        return APIResponse.success(
            data=responses,
            message=f"Found {len(responses)} hostels",
            status_code=200,
        )
    
    except Exception as e:
        logger.error(f"Error listing hostels: {e}")
        return APIResponse.error(
            error=str(e),
            message="Failed to list hostels",
            status_code=500,
        )


@router.get("/hostels/{hostel_id}", response_model=APIResponse)
async def get_hostel(
    hostel_id: UUID,
    db: AsyncSession = Depends(get_db),
    school_id: UUID = Depends(lambda: UUID("00000000-0000-0000-0000-000000000000")),
) -> APIResponse:
    """Get hostel detail with dormitories."""
    try:
        from sqlalchemy import select
        from sqlalchemy.orm import selectinload
        
        query = select(Hostel).where(
            Hostel.id == hostel_id,
            Hostel.school_id == school_id,
        ).options(selectinload(Hostel.dormitories))
        
        hostel = await db.scalar(query)
        
        if not hostel:
            return APIResponse.error(
                error="Not found",
                message="Hostel not found",
                status_code=404,
            )
        
        dormitories = [
            DormitoryResponse(
                id=d.id,
                name=d.name,
                capacity=d.capacity,
                current_occupancy=d.current_occupancy,
                is_active=d.is_active,
                created_at=d.created_at,
            )
            for d in hostel.dormitories
        ]
        
        occupancy_rate = (
            (hostel.current_occupancy / hostel.capacity * 100)
            if hostel.capacity > 0
            else 0
        )
        
        response = HostelDetailResponse(
            id=hostel.id,
            name=hostel.name,
            code=hostel.code,
            capacity=hostel.capacity,
            current_occupancy=hostel.current_occupancy,
            description=hostel.description,
            is_active=hostel.is_active,
            dormitories=dormitories,
            occupancy_rate=round(occupancy_rate, 2),
            created_at=hostel.created_at,
        )
        
        return APIResponse.success(
            data=response,
            message="Hostel retrieved",
            status_code=200,
        )
    
    except Exception as e:
        logger.error(f"Error retrieving hostel: {e}")
        return APIResponse.error(
            error=str(e),
            message="Failed to retrieve hostel",
            status_code=500,
        )


# ============================================================================
# DORMITORY MANAGEMENT
# ============================================================================


@router.post("/dormitories", response_model=APIResponse)
async def create_dormitory(
    hostel_id: UUID,
    request: DormitoryCreate,
    db: AsyncSession = Depends(get_db),
    school_id: UUID = Depends(lambda: UUID("00000000-0000-0000-0000-000000000000")),
) -> APIResponse:
    """Create dormitory (wing) in hostel."""
    try:
        dormitory = Dormitory(
            school_id=school_id,
            hostel_id=hostel_id,
            name=request.name,
            capacity=request.capacity,
            is_active=True,
        )
        
        db.add(dormitory)
        await db.commit()
        
        response = DormitoryResponse(
            id=dormitory.id,
            name=dormitory.name,
            capacity=dormitory.capacity,
            current_occupancy=0,
            is_active=dormitory.is_active,
            created_at=dormitory.created_at,
        )
        
        return APIResponse.success(
            data=response,
            message=f"Dormitory {request.name} created",
            status_code=201,
        )
    
    except Exception as e:
        logger.error(f"Error creating dormitory: {e}")
        return APIResponse.error(
            error=str(e),
            message="Failed to create dormitory",
            status_code=500,
        )


# ============================================================================
# BED MANAGEMENT
# ============================================================================


@router.post("/beds", response_model=APIResponse)
async def create_bed(
    request: BedCreate,
    db: AsyncSession = Depends(get_db),
    school_id: UUID = Depends(lambda: UUID("00000000-0000-0000-0000-000000000000")),
) -> APIResponse:
    """Create bed in dormitory."""
    try:
        bed = Bed(
            school_id=school_id,
            dormitory_id=request.dormitory_id,
            bed_number=request.bed_number,
            is_occupied=False,
            is_active=True,
        )
        
        db.add(bed)
        await db.commit()
        
        response = BedResponse(
            id=bed.id,
            dormitory_id=bed.dormitory_id,
            bed_number=bed.bed_number,
            is_occupied=bed.is_occupied,
            is_active=bed.is_active,
            created_at=bed.created_at,
        )
        
        return APIResponse.success(
            data=response,
            message=f"Bed {request.bed_number} created",
            status_code=201,
        )
    
    except Exception as e:
        logger.error(f"Error creating bed: {e}")
        return APIResponse.error(
            error=str(e),
            message="Failed to create bed",
            status_code=500,
        )


@router.get("/beds/{bed_id}", response_model=APIResponse)
async def get_bed_detail(
    bed_id: UUID,
    db: AsyncSession = Depends(get_db),
    school_id: UUID = Depends(lambda: UUID("00000000-0000-0000-0000-000000000000")),
) -> APIResponse:
    """Get bed status and current occupant."""
    try:
        service = BedAllocationService(db)
        bed_status = await service.get_bed_status(school_id, bed_id)
        
        return APIResponse.success(
            data=bed_status,
            message="Bed status retrieved",
            status_code=200,
        )
    
    except NotFoundError as e:
        return APIResponse.error(
            error=str(e),
            message="Bed not found",
            status_code=404,
        )
    
    except Exception as e:
        logger.error(f"Error retrieving bed: {e}")
        return APIResponse.error(
            error=str(e),
            message="Failed to retrieve bed",
            status_code=500,
        )


# ============================================================================
# BED ALLOCATION (CRITICAL)
# ============================================================================


@router.post("/allocate-bed", response_model=APIResponse)
async def allocate_bed(
    request: BedAllocationRequest,
    db: AsyncSession = Depends(get_db),
    school_id: UUID = Depends(lambda: UUID("00000000-0000-0000-0000-000000000000")),
) -> APIResponse:
    """
    CRITICAL ENDPOINT: Allocate bed to student.
    
    STRICT VALIDATION:
    - Student must have boarding_status = BOARDING
    - Bed must be unoccupied
    - Atomic operation: allocation and occupancy updated together
    """
    try:
        service = BedAllocationService(db)
        result = await service.allocate_bed(
            school_id=school_id,
            student_id=request.student_id,
            bed_id=request.bed_id,
            start_date=request.start_date,
            end_date=request.end_date,
        )
        
        response = AllocateBedResponse(
            success=True,
            allocation_id=result["allocation_id"],
            student_name=result["student_name"],
            bed_number=result["bed_number"],
            bed_location=result["location"],
            start_date=result["start_date"],
            message=result["message"],
        )
        
        return APIResponse.success(
            data=response,
            message="Bed allocated successfully",
            status_code=201,
        )
    
    except NotFoundError as e:
        return APIResponse.error(
            error=str(e),
            message="Resource not found",
            status_code=404,
        )
    
    except ValidationError as e:
        return APIResponse.error(
            error=str(e),
            message="Bed allocation failed",
            status_code=400,
        )
    
    except Exception as e:
        logger.error(f"Error allocating bed: {e}", exc_info=True)
        return APIResponse.error(
            error=str(e),
            message="Failed to allocate bed",
            status_code=500,
        )


@router.get("/hostel/{hostel_id}/occupancy", response_model=APIResponse)
async def get_hostel_occupancy(
    hostel_id: UUID,
    db: AsyncSession = Depends(get_db),
    school_id: UUID = Depends(lambda: UUID("00000000-0000-0000-0000-000000000000")),
) -> APIResponse:
    """Get hostel occupancy statistics."""
    try:
        service = BedAllocationService(db)
        occupancy = await service.get_hostel_occupancy(school_id, hostel_id)
        
        return APIResponse.success(
            data=occupancy,
            message="Occupancy retrieved",
            status_code=200,
        )
    
    except NotFoundError as e:
        return APIResponse.error(
            error=str(e),
            message="Hostel not found",
            status_code=404,
        )
    
    except Exception as e:
        logger.error(f"Error retrieving occupancy: {e}")
        return APIResponse.error(
            error=str(e),
            message="Failed to retrieve occupancy",
            status_code=500,
        )


# ============================================================================
# LEAVE PASS MANAGEMENT (EXEAT) - SECURITY CRITICAL
# ============================================================================


@router.post("/leave-pass/request", response_model=APIResponse)
async def request_leave_pass(
    request: RequestLeavePassRequest,
    db: AsyncSession = Depends(get_db),
    school_id: UUID = Depends(lambda: UUID("00000000-0000-0000-0000-000000000000")),
) -> APIResponse:
    """
    Student requests leave pass (exeat).
    
    Initiates approval workflow. Must be approved before departure.
    """
    try:
        service = ExeatService(db)
        result = await service.request_leave_pass(
            school_id=school_id,
            student_id=request.student_id,
            exeat_type=request.exeat_type,
            reason=request.reason,
            expected_return_time=request.expected_return_time,
            destination=request.destination,
            contact_person_name=request.contact_person_name,
            contact_person_phone=request.contact_person_phone,
        )
        
        return APIResponse.success(
            data=result,
            message="Leave pass request submitted",
            status_code=201,
        )
    
    except NotFoundError as e:
        return APIResponse.error(
            error=str(e),
            message="Student not found",
            status_code=404,
        )
    
    except ValidationError as e:
        return APIResponse.error(
            error=str(e),
            message="Request validation failed",
            status_code=400,
        )
    
    except Exception as e:
        logger.error(f"Error requesting leave pass: {e}")
        return APIResponse.error(
            error=str(e),
            message="Failed to request leave pass",
            status_code=500,
        )


@router.post("/leave-pass/approve", response_model=APIResponse)
async def approve_leave_pass(
    request: ApproveLeavePassRequest,
    approver_user_id: UUID = Depends(lambda: UUID("00000000-0000-0000-0000-000000000000")),
    db: AsyncSession = Depends(get_db),
    school_id: UUID = Depends(lambda: UUID("00000000-0000-0000-0000-000000000000")),
) -> APIResponse:
    """
    CRITICAL SECURITY: Approve/reject leave pass.
    
    Only Boarding Master, Deputy Principal, or Principal can approve.
    Rejected passes are NOT eligible for gate exit.
    """
    try:
        service = ExeatService(db)
        result = await service.approve_leave_pass(
            school_id=school_id,
            leave_pass_id=request.leave_pass_id,
            approved_by_user_id=approver_user_id,
            approved=request.approved,
            approval_reason=request.approval_reason,
        )
        
        return APIResponse.success(
            data=result,
            message="Leave pass processed",
            status_code=200,
        )
    
    except NotFoundError as e:
        return APIResponse.error(
            error=str(e),
            message="Resource not found",
            status_code=404,
        )
    
    except ValidationError as e:
        return APIResponse.error(
            error=str(e),
            message="Approval failed",
            status_code=400,
        )
    
    except Exception as e:
        logger.error(f"Error approving leave pass: {e}")
        return APIResponse.error(
            error=str(e),
            message="Failed to approve leave pass",
            status_code=500,
        )


@router.post("/leave-pass/record-departure", response_model=APIResponse)
async def record_departure(
    request: RecordDepartureRequest,
    db: AsyncSession = Depends(get_db),
    school_id: UUID = Depends(lambda: UUID("00000000-0000-0000-0000-000000000000")),
) -> APIResponse:
    """Record student departure from school (at gate)."""
    try:
        service = ExeatService(db)
        result = await service.record_departure(
            school_id=school_id,
            leave_pass_id=request.leave_pass_id,
            departure_time=request.departure_time,
        )
        
        return APIResponse.success(
            data=result,
            message="Departure recorded",
            status_code=200,
        )
    
    except NotFoundError as e:
        return APIResponse.error(
            error=str(e),
            message="Leave pass not found",
            status_code=404,
        )
    
    except ValidationError as e:
        return APIResponse.error(
            error=str(e),
            message="Departure recording failed",
            status_code=400,
        )
    
    except Exception as e:
        logger.error(f"Error recording departure: {e}")
        return APIResponse.error(
            error=str(e),
            message="Failed to record departure",
            status_code=500,
        )


@router.post("/leave-pass/record-return", response_model=APIResponse)
async def record_return(
    request: RecordReturnRequest,
    db: AsyncSession = Depends(get_db),
    school_id: UUID = Depends(lambda: UUID("00000000-0000-0000-0000-000000000000")),
) -> APIResponse:
    """Record student return to school (at gate)."""
    try:
        service = ExeatService(db)
        result = await service.record_return(
            school_id=school_id,
            leave_pass_id=request.leave_pass_id,
            actual_return_time=request.actual_return_time,
        )
        
        return APIResponse.success(
            data=result,
            message="Return recorded",
            status_code=200,
        )
    
    except NotFoundError as e:
        return APIResponse.error(
            error=str(e),
            message="Leave pass not found",
            status_code=404,
        )
    
    except ValidationError as e:
        return APIResponse.error(
            error=str(e),
            message="Return recording failed",
            status_code=400,
        )
    
    except Exception as e:
        logger.error(f"Error recording return: {e}")
        return APIResponse.error(
            error=str(e),
            message="Failed to record return",
            status_code=500,
        )


@router.post("/gate/verify-exit", response_model=APIResponse)
async def verify_gate_exit(
    request: VerifyGateExitRequest,
    db: AsyncSession = Depends(get_db),
    school_id: UUID = Depends(lambda: UUID("00000000-0000-0000-0000-000000000000")),
) -> APIResponse:
    """
    CRITICAL SECURITY: Verify student can exit at gate.
    
    Called by Gate/Security module BEFORE allowing departure.
    Returns True ONLY if student has APPROVED leave pass for current time.
    
    Example usage:
    - Gate guard scans student ID
    - Calls this endpoint with student_id and current_time
    - If allowed=True: allow exit, record departure
    - If allowed=False: deny exit, alert security
    """
    try:
        service = ExeatService(db)
        result = await service.verify_gate_exit(
            school_id=school_id,
            student_id=request.student_id,
            current_time=request.current_time,
        )
        
        return APIResponse.success(
            data=result,
            message="Gate verification complete",
            status_code=200,
        )
    
    except Exception as e:
        logger.error(f"Error verifying gate exit: {e}")
        return APIResponse.error(
            error=str(e),
            message="Failed to verify exit",
            status_code=500,
        )


@router.get("/leave-passes/currently-away", response_model=APIResponse)
async def get_students_away(
    db: AsyncSession = Depends(get_db),
    school_id: UUID = Depends(lambda: UUID("00000000-0000-0000-0000-000000000000")),
) -> APIResponse:
    """Get list of students currently away on approved leave."""
    try:
        service = ExeatService(db)
        away_students = await service.get_students_away_now(school_id)
        
        return APIResponse.success(
            data=away_students,
            message=f"Found {len(away_students)} students away",
            status_code=200,
        )
    
    except Exception as e:
        logger.error(f"Error getting away students: {e}")
        return APIResponse.error(
            error=str(e),
            message="Failed to get students away",
            status_code=500,
        )
