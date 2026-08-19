"""
Gate Security FastAPI Routers.

Endpoints for security guards to manage visitors and scan students.
"""

import logging
from uuid import UUID

from fastapi import APIRouter, Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession

from src.core.database import get_db
from src.core.exceptions import NotFoundError, ValidationError, ForbiddenError
from src.core.response import APIResponse
from src.modules.security.schemas.gate import (
    CreateVisitorRequest,
    VisitorResponse,
    VisitorLogResponse,
    CheckOutVisitorRequest,
    ScanStudentExitRequest,
    ScanStudentEntryRequest,
    StudentGateEventResponse,
    StudentExitClearanceResponse,
    StudentUnauthorizedExitAlert,
    StudentEntryLoggingResponse,
    GateSuspicionResponse,
    GateAuditReportResponse,
)
from src.modules.security.services.gate_service import (
    GateService,
    ForbiddenExitError,
)

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/security/gate", tags=["Gate Security & Visitors"])


# ============================================================================
# VISITOR MANAGEMENT
# ============================================================================


@router.post("/visitor/check-in", response_model=APIResponse)
async def check_in_visitor(
    request: CreateVisitorRequest,
    db: AsyncSession = Depends(get_db),
    school_id: UUID = Depends(lambda: UUID("00000000-0000-0000-0000-000000000000")),
) -> APIResponse:
    """
    Check in visitor and issue gate pass.
    
    Security guards use this endpoint when a visitor arrives at the gate.
    Generates gate pass ticket for visitor tracking.
    """
    try:
        service = GateService(db)
        result = await service.log_visitor_entry(
            school_id=school_id,
            first_name=request.first_name,
            last_name=request.last_name,
            national_id=request.national_id,
            phone=request.phone,
            email=request.email,
            visitor_type=request.visitor_type,
            purpose=request.purpose,
            host_staff_id=request.host_staff_id,
            vehicle_registration=request.vehicle_registration,
            vehicle_description=request.vehicle_description,
        )
        
        return APIResponse.success(
            data=result,
            message="Visitor checked in successfully",
            status_code=201,
        )
    
    except ForbiddenError as e:
        logger.warning(f"Visitor denied entry (blacklist): {str(e)}")
        return APIResponse.error(
            error=str(e),
            message="Visitor denied entry - blacklisted",
            status_code=403,
        )
    
    except ValidationError as e:
        return APIResponse.error(
            error=str(e),
            message="Visitor check-in validation failed",
            status_code=400,
        )
    
    except Exception as e:
        logger.error(f"Error checking in visitor: {e}", exc_info=True)
        return APIResponse.error(
            error=str(e),
            message="Failed to check in visitor",
            status_code=500,
        )


@router.post("/visitor/{gate_pass_number}/check-out", response_model=APIResponse)
async def check_out_visitor(
    gate_pass_number: str,
    request: CheckOutVisitorRequest,
    db: AsyncSession = Depends(get_db),
    school_id: UUID = Depends(lambda: UUID("00000000-0000-0000-0000-000000000000")),
) -> APIResponse:
    """Check out visitor using gate pass number."""
    try:
        service = GateService(db)
        result = await service.checkout_visitor(
            school_id=school_id,
            gate_pass_number=gate_pass_number,
            security_notes=request.security_notes,
        )
        
        return APIResponse.success(
            data=result,
            message="Visitor checked out successfully",
            status_code=200,
        )
    
    except NotFoundError as e:
        return APIResponse.error(
            error=str(e),
            message="Gate pass not found",
            status_code=404,
        )
    
    except ValidationError as e:
        return APIResponse.error(
            error=str(e),
            message="Check-out validation failed",
            status_code=400,
        )
    
    except Exception as e:
        logger.error(f"Error checking out visitor: {e}")
        return APIResponse.error(
            error=str(e),
            message="Failed to check out visitor",
            status_code=500,
        )


@router.post("/visitor/{national_id}/blacklist", response_model=APIResponse)
async def blacklist_visitor(
    national_id: str,
    reason: str = Query(..., min_length=5, max_length=500),
    db: AsyncSession = Depends(get_db),
    school_id: UUID = Depends(lambda: UUID("00000000-0000-0000-0000-000000000000")),
) -> APIResponse:
    """Blacklist a visitor from campus."""
    try:
        service = GateService(db)
        result = await service.blacklist_visitor(
            school_id=school_id,
            national_id=national_id,
            reason=reason,
        )
        
        return APIResponse.success(
            data=result,
            message="Visitor blacklisted successfully",
            status_code=200,
        )
    
    except NotFoundError as e:
        return APIResponse.error(
            error=str(e),
            message="Visitor not found",
            status_code=404,
        )
    
    except Exception as e:
        logger.error(f"Error blacklisting visitor: {e}")
        return APIResponse.error(
            error=str(e),
            message="Failed to blacklist visitor",
            status_code=500,
        )


# ============================================================================
# STUDENT GATE SCANNING (CRITICAL SECURITY)
# ============================================================================


@router.post("/scan-student-exit", response_model=APIResponse)
async def scan_student_exit(
    request: ScanStudentExitRequest,
    db: AsyncSession = Depends(get_db),
    school_id: UUID = Depends(lambda: UUID("00000000-0000-0000-0000-000000000000")),
) -> APIResponse:
    """
    CRITICAL SECURITY ENDPOINT: Scan student ID for exit.
    
    This endpoint verifies if a student has an approved leave pass
    from the Boarding Master. If authorized, logs the exit event
    and returns clearance. If unauthorized, denies access and
    triggers a high-priority alert.
    
    Workflow:
    1. Guard scans student ID (or enters manually)
    2. System queries Boarding module for active leave pass
    3. If APPROVED leave pass with valid time:
       → Return CLEAR TO EXIT with pass details
    4. If NO leave pass or EXPIRED:
       → Return DENIED, log unauthorized attempt
       → Trigger alert to Boarding Master
    """
    try:
        service = GateService(db)
        result = await service.scan_student_exit(
            school_id=school_id,
            student_id=request.student_id,
            guard_user_id=request.guard_user_id,
        )
        
        return APIResponse.success(
            data=result,
            message="Student exit authorized - gate opens",
            status_code=200,
        )
    
    except ForbiddenExitError as e:
        # Unauthorized exit attempt
        logger.warning(f"UNAUTHORIZED EXIT: {str(e)}")
        
        return APIResponse.error(
            error=str(e.reason),
            message="EXIT DENIED - No approved leave pass",
            status_code=403,
        )
    
    except NotFoundError as e:
        return APIResponse.error(
            error=str(e),
            message="Student not found",
            status_code=404,
        )
    
    except Exception as e:
        logger.error(f"Error scanning student exit: {e}", exc_info=True)
        return APIResponse.error(
            error=str(e),
            message="Failed to scan student exit",
            status_code=500,
        )


@router.post("/scan-student-entry", response_model=APIResponse)
async def scan_student_entry(
    request: ScanStudentEntryRequest,
    db: AsyncSession = Depends(get_db),
    school_id: UUID = Depends(lambda: UUID("00000000-0000-0000-0000-000000000000")),
) -> APIResponse:
    """
    Scan student ID for entry/return to campus.
    
    Logs the student's return and updates their leave pass status
    to RETURNED for audit purposes.
    """
    try:
        service = GateService(db)
        result = await service.scan_student_entry(
            school_id=school_id,
            student_id=request.student_id,
            guard_user_id=request.guard_user_id,
        )
        
        return APIResponse.success(
            data=result,
            message="Student entry logged successfully",
            status_code=200,
        )
    
    except NotFoundError as e:
        return APIResponse.error(
            error=str(e),
            message="Student not found",
            status_code=404,
        )
    
    except Exception as e:
        logger.error(f"Error scanning student entry: {e}")
        return APIResponse.error(
            error=str(e),
            message="Failed to scan student entry",
            status_code=500,
        )


# ============================================================================
# AUDIT & REPORTING
# ============================================================================


@router.get("/student/{student_id}/history", response_model=APIResponse)
async def get_student_gate_history(
    student_id: UUID,
    days: int = Query(30, ge=1, le=365, description="Days of history to retrieve"),
    db: AsyncSession = Depends(get_db),
    school_id: UUID = Depends(lambda: UUID("00000000-0000-0000-0000-000000000000")),
) -> APIResponse:
    """Get student's recent gate entry/exit history."""
    try:
        service = GateService(db)
        events = await service.get_student_gate_history(
            school_id=school_id,
            student_id=student_id,
            days_back=days,
        )
        
        return APIResponse.success(
            data=events,
            message=f"Found {len(events)} gate events",
            status_code=200,
        )
    
    except Exception as e:
        logger.error(f"Error getting gate history: {e}")
        return APIResponse.error(
            error=str(e),
            message="Failed to retrieve history",
            status_code=500,
        )


@router.get("/audit-report", response_model=APIResponse)
async def get_gate_audit_report(
    days: int = Query(1, ge=1, le=30, description="Days to include in report"),
    db: AsyncSession = Depends(get_db),
    school_id: UUID = Depends(lambda: UUID("00000000-0000-0000-0000-000000000000")),
) -> APIResponse:
    """
    Get gate security audit report.
    
    Shows statistics on:
    - Total student exits/entries
    - Authorized vs unauthorized exits
    - Visitor check-ins/check-outs
    - Security incidents and alerts
    """
    try:
        service = GateService(db)
        report = await service.get_gate_audit_report(
            school_id=school_id,
            days_back=days,
        )
        
        return APIResponse.success(
            data=report,
            message=f"Gate audit report for {report['period']}",
            status_code=200,
        )
    
    except Exception as e:
        logger.error(f"Error generating audit report: {e}")
        return APIResponse.error(
            error=str(e),
            message="Failed to generate report",
            status_code=500,
        )


# ============================================================================
# HEALTH CHECK
# ============================================================================


@router.get("/health", response_model=APIResponse)
async def gate_system_health() -> APIResponse:
    """Check gate system health and connectivity."""
    logger.info("Gate system health check")
    
    return APIResponse.success(
        data={
            "status": "OPERATIONAL",
            "timestamp": __import__("datetime").datetime.utcnow().isoformat(),
        },
        message="Gate security system operational",
        status_code=200,
    )
