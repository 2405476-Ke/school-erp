"""
FastAPI routers for Admissions and Student Lifecycle.

Endpoints for:
- Student prospect management
- Student admission (critical integration endpoint)
- Student profile management
- Student clearance
- Student transfer
"""

import logging
from uuid import UUID
from decimal import Decimal

from fastapi import APIRouter, Depends, Query
from sqlalchemy import and_, select, func
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from src.core.database import get_db
from src.core.exceptions import NotFoundError, ValidationError
from src.core.response import APIResponse
from src.modules.admissions.models.students import (
    StudentProspect,
    Student,
    ParentGuardian,
    StudentParentRelationship,
    StudentClearance,
    StudentTransfer,
    ProspectStatus,
    Gender,
    BoardingStatus,
    StudentActiveStatus,
)
from src.modules.admissions.schemas.students import (
    StudentProspectCreate,
    StudentProspectResponse,
    StudentProspectDetailResponse,
    StudentCreate,
    StudentUpdate,
    StudentResponse,
    StudentDetailResponse,
    AdmitStudentRequest,
    AdmitStudentResponse,
    ParentGuardianCreate,
    ParentGuardianResponse,
    StudentParentRelationshipCreate,
    StudentParentRelationshipResponse,
    StudentClearanceResponse,
    InitiateClearanceRequest,
    InitiateClearanceResponse,
    StudentTransferCreate,
    StudentTransferResponse,
    ProspectListResponse,
    AdmissionStatistics,
)
from src.modules.admissions.services.admission_service import AdmissionService
from src.modules.admissions.services.clearance_service import ClearanceService

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/admissions", tags=["Admissions & Student Lifecycle"])


# ============================================================================
# STUDENT PROSPECT MANAGEMENT
# ============================================================================


@router.post("/prospects", response_model=APIResponse)
async def create_prospect(
    request: StudentProspectCreate,
    db: AsyncSession = Depends(get_db),
    school_id: UUID = Depends(lambda: UUID("00000000-0000-0000-0000-000000000000")),
) -> APIResponse:
    """
    Create a new prospective student application.
    
    Example:
    {
        "first_name": "Jane",
        "last_name": "Kamau",
        "gender": "FEMALE",
        "date_of_birth": "2008-06-15",
        "kcpe_marks": 385,
        "kcpe_year": 2024,
        "email": "jane@example.com",
        "phone": "+254712345678"
    }
    """
    try:
        prospect = StudentProspect(
            school_id=school_id,
            first_name=request.first_name,
            last_name=request.last_name,
            email=request.email,
            phone=request.phone,
            gender=request.gender,
            date_of_birth=request.date_of_birth,
            kcpe_marks=request.kcpe_marks,
            kcpe_year=request.kcpe_year,
            kpsea_marks=request.kpsea_marks,
            kpsea_year=request.kpsea_year,
            notes=request.notes,
            status=ProspectStatus.PENDING,
        )
        
        db.add(prospect)
        await db.commit()
        
        response = StudentProspectResponse(
            id=prospect.id,
            first_name=prospect.first_name,
            last_name=prospect.last_name,
            email=prospect.email,
            phone=prospect.phone,
            gender=prospect.gender.value,
            date_of_birth=prospect.date_of_birth.isoformat(),
            kcpe_marks=prospect.kcpe_marks,
            kcpe_year=prospect.kcpe_year,
            kpsea_marks=prospect.kpsea_marks,
            kpsea_year=prospect.kpsea_year,
            status=prospect.status.value,
            application_date=prospect.application_date.isoformat(),
            notes=prospect.notes,
            created_at=prospect.created_at.isoformat(),
        )
        
        return APIResponse.success(
            data=response,
            message=f"Application created for {request.first_name} {request.last_name}",
            status_code=201,
        )
    
    except Exception as e:
        logger.error(f"Error creating prospect: {e}")
        return APIResponse.error(
            error=str(e),
            message="Failed to create prospect application",
            status_code=500,
        )


@router.get("/prospects", response_model=APIResponse)
async def list_prospects(
    db: AsyncSession = Depends(get_db),
    school_id: UUID = Depends(lambda: UUID("00000000-0000-0000-0000-000000000000")),
    status: str = Query(None, description="PENDING, ADMITTED, REJECTED"),
    year: int = Query(None, description="KCPE year"),
) -> APIResponse:
    """List prospects with filters."""
    try:
        service = AdmissionService(db)
        prospects = await service.list_prospects(school_id, status, year)
        
        # Calculate statistics
        pending_count = sum(1 for p in prospects if p.status == ProspectStatus.PENDING)
        admitted_count = sum(1 for p in prospects if p.status == ProspectStatus.ADMITTED)
        rejected_count = sum(1 for p in prospects if p.status == ProspectStatus.REJECTED)
        
        prospect_responses = [
            StudentProspectResponse(
                id=p.id,
                first_name=p.first_name,
                last_name=p.last_name,
                email=p.email,
                phone=p.phone,
                gender=p.gender.value,
                date_of_birth=p.date_of_birth.isoformat(),
                kcpe_marks=p.kcpe_marks,
                kcpe_year=p.kcpe_year,
                kpsea_marks=p.kpsea_marks,
                kpsea_year=p.kpsea_year,
                status=p.status.value,
                application_date=p.application_date.isoformat(),
                notes=p.notes,
                created_at=p.created_at.isoformat(),
            )
            for p in prospects
        ]
        
        response = ProspectListResponse(
            total=len(prospects),
            pending=pending_count,
            admitted=admitted_count,
            rejected=rejected_count,
            prospects=prospect_responses,
        )
        
        return APIResponse.success(
            data=response,
            message=f"Found {len(prospects)} prospects",
            status_code=200,
        )
    
    except Exception as e:
        logger.error(f"Error listing prospects: {e}")
        return APIResponse.error(
            error=str(e),
            message="Failed to list prospects",
            status_code=500,
        )


@router.get("/prospects/{prospect_id}", response_model=APIResponse)
async def get_prospect(
    prospect_id: UUID,
    db: AsyncSession = Depends(get_db),
    school_id: UUID = Depends(lambda: UUID("00000000-0000-0000-0000-000000000000")),
) -> APIResponse:
    """Get prospect details."""
    try:
        service = AdmissionService(db)
        prospect = await service.get_prospect(school_id, prospect_id)
        
        # Compute admission score (average of KCPE and KPSEA if available)
        admission_score = prospect.kcpe_marks
        if prospect.kpsea_marks:
            admission_score = (prospect.kcpe_marks + prospect.kpsea_marks) / 2
        
        response = StudentProspectDetailResponse(
            id=prospect.id,
            first_name=prospect.first_name,
            last_name=prospect.last_name,
            email=prospect.email,
            phone=prospect.phone,
            gender=prospect.gender.value,
            date_of_birth=prospect.date_of_birth.isoformat(),
            kcpe_marks=prospect.kcpe_marks,
            kcpe_year=prospect.kcpe_year,
            kpsea_marks=prospect.kpsea_marks,
            kpsea_year=prospect.kpsea_year,
            status=prospect.status.value,
            application_date=prospect.application_date.isoformat(),
            notes=prospect.notes,
            admission_score=admission_score,
            created_at=prospect.created_at.isoformat(),
        )
        
        return APIResponse.success(
            data=response,
            message="Prospect retrieved",
            status_code=200,
        )
    
    except NotFoundError as e:
        return APIResponse.error(
            error=str(e),
            message="Prospect not found",
            status_code=404,
        )
    
    except Exception as e:
        logger.error(f"Error retrieving prospect: {e}")
        return APIResponse.error(
            error=str(e),
            message="Failed to retrieve prospect",
            status_code=500,
        )


# ============================================================================
# STUDENT ADMISSION (CRITICAL INTEGRATION)
# ============================================================================


@router.post("/admit", response_model=APIResponse)
async def admit_student(
    request: AdmitStudentRequest,
    db: AsyncSession = Depends(get_db),
    school_id: UUID = Depends(lambda: UUID("00000000-0000-0000-0000-000000000000")),
) -> APIResponse:
    """
    CRITICAL ENDPOINT: Admit student from prospect.
    
    This endpoint performs the COMPLETE student onboarding:
    1. Creates Student record
    2. Creates StudentClassEnrollment (via Academics service)
    3. Initializes FeeAccount (via Finance service)
    4. Generates initial invoice (via Finance service)
    
    All in a SINGLE ATOMIC TRANSACTION.
    
    INTEGRATION POINTS:
    - Academics: Creates enrollment, assigns compulsory subjects
    - Finance: Creates fee account and first invoice, posts GL
    
    Example:
    {
        "prospect_id": "550e8400-e29b-41d4-a716-446655440000",
        "class_level_id": "660e8400-e29b-41d4-a716-446655440001",
        "stream_id": "770e8400-e29b-41d4-a716-446655440002",
        "boarding_status": "BOARDING"
    }
    
    Response:
    {
        "success": true,
        "data": {
            "student_id": "880e8400-e29b-41d4-a716-446655440003",
            "admission_number": "ADM-2024-001",
            "class_level": "Form 1",
            "stream": "A",
            "enrollment_id": "990e8400-e29b-41d4-a716-446655440004",
            "fee_account_id": "aa0e8400-e29b-41d4-a716-446655440005",
            "initial_invoice_id": "bb0e8400-e29b-41d4-a716-446655440006",
            "message": "Student Jane Kamau successfully admitted..."
        }
    }
    """
    try:
        # Import services (would normally be injected)
        from src.modules.academics.services.enrollment_service import EnrollmentService
        from src.modules.finance.services.fee_account_service import FeeAccountService
        from src.modules.finance.services.billing_service import BillingService
        
        # Initialize services
        admission_service = AdmissionService(db)
        enrollment_service = EnrollmentService(db)
        fee_account_service = FeeAccountService(db)
        billing_service = BillingService(db)
        
        # Call critical admission algorithm
        result = await admission_service.admit_student(
            school_id=school_id,
            prospect_id=request.prospect_id,
            class_level_id=request.class_level_id,
            stream_id=request.stream_id,
            boarding_status=request.boarding_status.value,
            enrollment_service=enrollment_service,
            fee_account_service=fee_account_service,
            billing_service=billing_service,
        )
        
        response = AdmitStudentResponse(
            success=True,
            student_id=UUID(result["student_id"]),
            admission_number=result["admission_number"],
            class_enrollment_id=UUID(result["enrollment_id"]),
            fee_account_id=UUID(result["fee_account_id"]),
            initial_invoice_id=UUID(result["initial_invoice_id"]) if result.get("initial_invoice_id") else None,
            message=result["message"],
        )
        
        return APIResponse.success(
            data=response,
            message="Student admitted successfully",
            status_code=201,
        )
    
    except NotFoundError as e:
        logger.warning(f"Admission error (not found): {e}")
        return APIResponse.error(
            error=str(e),
            message="Required resource not found",
            status_code=404,
        )
    
    except ValidationError as e:
        logger.warning(f"Admission validation error: {e}")
        return APIResponse.error(
            error=str(e),
            message="Admission validation failed",
            status_code=400,
        )
    
    except Exception as e:
        logger.error(f"Error admitting student: {e}", exc_info=True)
        return APIResponse.error(
            error=str(e),
            message="Failed to admit student",
            status_code=500,
        )


# ============================================================================
# STUDENT PROFILE MANAGEMENT
# ============================================================================


@router.get("/students/{student_id}", response_model=APIResponse)
async def get_student(
    student_id: UUID,
    db: AsyncSession = Depends(get_db),
    school_id: UUID = Depends(lambda: UUID("00000000-0000-0000-0000-000000000000")),
) -> APIResponse:
    """Get student profile with all relationships."""
    try:
        service = AdmissionService(db)
        student = await service.get_student(school_id, student_id)
        
        # Build response
        parent_relationships = []
        for rel in student.parent_relationships:
            parent_name = f"{rel.parent_guardian.first_name} {rel.parent_guardian.last_name}"
            parent_relationships.append(
                StudentParentRelationshipResponse(
                    id=rel.id,
                    student_id=rel.student_id,
                    parent_guardian_id=rel.parent_guardian_id,
                    parent_name=parent_name,
                    relationship_type=rel.relationship_type.value,
                    is_primary=rel.is_primary,
                    emergency_contact=rel.emergency_contact,
                    created_at=rel.created_at.isoformat(),
                )
            )
        
        # Get current class
        current_class = None
        if student.class_enrollments:
            latest_enrollment = sorted(
                student.class_enrollments,
                key=lambda e: e.enrollment_date,
                reverse=True,
            )[0]
            current_class = latest_enrollment.class_level.name if latest_enrollment.class_level else None
        
        # Get fee balance
        fee_balance = None
        if student.fee_account:
            fee_balance = student.fee_account.balance
        
        # Check for pending clearance
        has_pending_clearance_query = select(StudentClearance).where(
            and_(
                StudentClearance.student_id == student_id,
                StudentClearance.status != "CLEARED",
            )
        )
        has_pending_clearance_result = await db.scalar(has_pending_clearance_query)
        has_pending_clearance = has_pending_clearance_result is not None
        
        response = StudentDetailResponse(
            id=student.id,
            admission_number=student.admission_number,
            upi_nemis_number=student.upi_nemis_number,
            first_name=student.first_name,
            last_name=student.last_name,
            email=student.email,
            phone=student.phone,
            gender=student.gender.value,
            date_of_birth=student.date_of_birth.isoformat(),
            boarding_status=student.boarding_status.value,
            active_status=student.active_status.value,
            admission_date=student.admission_date.isoformat(),
            is_active=student.is_active,
            parent_relationships=parent_relationships,
            class_enrollments_count=len(student.class_enrollments),
            current_class=current_class,
            fee_account_balance=fee_balance,
            has_pending_clearance=has_pending_clearance,
            created_at=student.created_at.isoformat(),
        )
        
        return APIResponse.success(
            data=response,
            message="Student retrieved",
            status_code=200,
        )
    
    except NotFoundError as e:
        return APIResponse.error(
            error=str(e),
            message="Student not found",
            status_code=404,
        )
    
    except Exception as e:
        logger.error(f"Error retrieving student: {e}")
        return APIResponse.error(
            error=str(e),
            message="Failed to retrieve student",
            status_code=500,
        )


@router.get("/students", response_model=APIResponse)
async def list_students(
    db: AsyncSession = Depends(get_db),
    school_id: UUID = Depends(lambda: UUID("00000000-0000-0000-0000-000000000000")),
    active_only: bool = Query(True),
    boarding_status: str = Query(None),
) -> APIResponse:
    """List students with filters."""
    try:
        service = AdmissionService(db)
        students = await service.list_students(school_id, active_only, boarding_status)
        
        responses = [
            StudentResponse(
                id=s.id,
                admission_number=s.admission_number,
                upi_nemis_number=s.upi_nemis_number,
                first_name=s.first_name,
                last_name=s.last_name,
                email=s.email,
                phone=s.phone,
                gender=s.gender.value,
                date_of_birth=s.date_of_birth.isoformat(),
                boarding_status=s.boarding_status.value,
                active_status=s.active_status.value,
                admission_date=s.admission_date.isoformat(),
                is_active=s.is_active,
                created_at=s.created_at.isoformat(),
            )
            for s in students
        ]
        
        return APIResponse.success(
            data=responses,
            message=f"Found {len(responses)} students",
            status_code=200,
        )
    
    except Exception as e:
        logger.error(f"Error listing students: {e}")
        return APIResponse.error(
            error=str(e),
            message="Failed to list students",
            status_code=500,
        )


@router.patch("/students/{student_id}", response_model=APIResponse)
async def update_student(
    student_id: UUID,
    request: StudentUpdate,
    db: AsyncSession = Depends(get_db),
    school_id: UUID = Depends(lambda: UUID("00000000-0000-0000-0000-000000000000")),
) -> APIResponse:
    """Update student record."""
    try:
        service = AdmissionService(db)
        student = await service.get_student(school_id, student_id)
        
        # Update fields
        if request.email:
            student.email = request.email
        if request.phone:
            student.phone = request.phone
        if request.boarding_status:
            student.boarding_status = request.boarding_status
        if request.active_status:
            student.active_status = StudentActiveStatus(request.active_status)
        
        await db.commit()
        
        return APIResponse.success(
            data={"student_id": str(student_id)},
            message="Student updated",
            status_code=200,
        )
    
    except NotFoundError as e:
        return APIResponse.error(
            error=str(e),
            message="Student not found",
            status_code=404,
        )
    
    except Exception as e:
        logger.error(f"Error updating student: {e}")
        return APIResponse.error(
            error=str(e),
            message="Failed to update student",
            status_code=500,
        )


# ============================================================================
# STUDENT CLEARANCE
# ============================================================================


@router.post("/clearance/initiate", response_model=APIResponse)
async def initiate_clearance(
    request: InitiateClearanceRequest,
    db: AsyncSession = Depends(get_db),
    school_id: UUID = Depends(lambda: UUID("00000000-0000-0000-0000-000000000000")),
) -> APIResponse:
    """
    CRITICAL ENDPOINT: Initiate student clearance.
    
    Checks:
    1. Finance: Unpaid fees
    2. Library: Unreturned books
    3. Sports: Unreturned gear
    
    Returns clearance status and required actions.
    """
    try:
        from src.modules.finance.services.fee_account_service import FeeAccountService
        # Import library and sports services if available
        
        service = ClearanceService(db)
        fee_service = FeeAccountService(db)
        
        result = await service.initiate_clearance(
            school_id=school_id,
            student_id=request.student_id,
            fee_service=fee_service,
            library_service=None,  # Optional
            sports_service=None,   # Optional
        )
        
        response = InitiateClearanceResponse(
            clearance_id=UUID(result["clearance_id"]),
            student_id=UUID(result["student_id"]),
            status=result["status"],
            has_fee_balance=result["has_fee_balance"],
            has_library_books=result["has_library_books"],
            has_sports_gear=result["has_sports_gear"],
            clearance_required=result["clearance_required"],
            message=result["message"],
        )
        
        return APIResponse.success(
            data=response,
            message="Clearance initiated",
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
            message="Clearance initiation failed",
            status_code=400,
        )
    
    except Exception as e:
        logger.error(f"Error initiating clearance: {e}", exc_info=True)
        return APIResponse.error(
            error=str(e),
            message="Failed to initiate clearance",
            status_code=500,
        )


@router.get("/clearance/{clearance_id}", response_model=APIResponse)
async def get_clearance(
    clearance_id: UUID,
    db: AsyncSession = Depends(get_db),
    school_id: UUID = Depends(lambda: UUID("00000000-0000-0000-0000-000000000000")),
) -> APIResponse:
    """Get clearance record."""
    try:
        service = ClearanceService(db)
        clearance = await service.get_clearance(school_id, clearance_id)
        
        response = StudentClearanceResponse(
            id=clearance.id,
            student_id=clearance.student_id,
            student_name=f"{clearance.student.first_name} {clearance.student.last_name}",
            status=clearance.status.value,
            initiated_date=clearance.initiated_date.isoformat(),
            cleared_date=clearance.cleared_date.isoformat() if clearance.cleared_date else None,
            has_fee_balance=clearance.has_fee_balance,
            has_library_books=clearance.has_library_books,
            has_sports_gear=clearance.has_sports_gear,
            remarks=clearance.remarks,
            created_at=clearance.created_at.isoformat(),
        )
        
        return APIResponse.success(
            data=response,
            message="Clearance retrieved",
            status_code=200,
        )
    
    except NotFoundError as e:
        return APIResponse.error(
            error=str(e),
            message="Clearance not found",
            status_code=404,
        )
    
    except Exception as e:
        logger.error(f"Error retrieving clearance: {e}")
        return APIResponse.error(
            error=str(e),
            message="Failed to retrieve clearance",
            status_code=500,
        )
