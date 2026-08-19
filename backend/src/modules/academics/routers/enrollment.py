"""
Academics Enrollment Routers: Endpoints for student enrollment and subject selection.

Endpoints for:
- Enroll student in class
- Get enrollment status
- Add/remove elective subjects
- Class roll call
- Student transcript
"""
import logging
from uuid import UUID

from fastapi import APIRouter, Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession

from src.core.database import get_db
from src.core.exceptions import NotFoundError, ValidationError
from src.core.response import APIResponse
from src.modules.academics.schemas.core import (
    ClassLevelResponse,
    EnrollmentRequest,
    EnrollmentResponse,
    StreamResponse,
    StudentClassEnrollmentResponse,
    StudentEnrollmentDetailResponse,
    StudentEnrollmentListResponse,
    StudentSubjectSelectionDetailResponse,
    StudentTranscriptSummary,
    TermResponse,
)
from src.modules.academics.services.enrollment_service import EnrollmentService

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/academics", tags=["Academics - Enrollment"])


# ============================================================================
# STUDENT ENROLLMENT
# ============================================================================


@router.post("/enrollments", response_model=APIResponse)
async def enroll_student_in_class(
    request: EnrollmentRequest,
    db: AsyncSession = Depends(get_db),
    school_id: UUID = Depends(lambda: UUID("00000000-0000-0000-0000-000000000000")),
) -> APIResponse:
    """
    Enroll a student in a class/stream for a term.

    REAL BUSINESS LOGIC:
    1. Verify student is active
    2. Verify stream has capacity
    3. Create StudentClassEnrollment
    4. Auto-assign all compulsory subjects
    5. Update stream current_enrollment
    6. Atomic: all-or-nothing

    Example Request:
    {
        "student_id": "550e8400-e29b-41d4-a716-446655440000",
        "stream_id": "660e8400-e29b-41d4-a716-446655440001",
        "term_id": "770e8400-e29b-41d4-a716-446655440002"
    }

    Response:
    {
        "success": true,
        "data": {
            "success": true,
            "message": "Student enrolled successfully",
            "enrollment_id": "880e8400-e29b-41d4-a716-446655440003",
            "subjects_assigned": 8
        }
    }
    """
    try:
        logger.info(
            f"Enrollment request: student={request.student_id}, "
            f"stream={request.stream_id}, term={request.term_id}"
        )

        service = EnrollmentService(db)

        # Enroll student (real business logic in service)
        enrollment, subject_count = await service.enroll_student_in_class(
            school_id=school_id,
            student_id=request.student_id,
            stream_id=request.stream_id,
            term_id=request.term_id,
        )

        response = EnrollmentResponse(
            success=True,
            message="Student enrolled successfully",
            enrollment_id=enrollment.id,
            subjects_assigned=subject_count,
        )

        return APIResponse.success(
            data=response,
            message=f"Student enrolled with {subject_count} subjects",
            status_code=201,
        )

    except NotFoundError as e:
        logger.warning(f"Enrollment not found error: {e}")
        return APIResponse.error(
            error=str(e),
            message="Student, stream, or term not found",
            status_code=404,
        )

    except ValidationError as e:
        logger.warning(f"Enrollment validation error: {e}")
        return APIResponse.error(
            error=str(e),
            message="Enrollment validation failed",
            status_code=400,
        )

    except Exception as e:
        logger.error(f"Enrollment error: {e}", exc_info=True)
        return APIResponse.error(
            error=str(e),
            message="Failed to enroll student",
            status_code=500,
        )


@router.get("/enrollments/{enrollment_id}", response_model=APIResponse)
async def get_enrollment(
    enrollment_id: UUID,
    db: AsyncSession = Depends(get_db),
    school_id: UUID = Depends(lambda: UUID("00000000-0000-0000-0000-000000000000")),
) -> APIResponse:
    """
    Get student enrollment with full details.

    Includes:
    - Class level details
    - Stream details
    - Term details
    - Academic year
    - Selected subjects (compulsory + electives)
    """
    try:
        service = EnrollmentService(db)

        # This endpoint would require fetching by ID, not by term
        # So we need to implement a helper method in the service
        # For now, returning a placeholder that would be implemented

        from sqlalchemy import select, and_
        from src.modules.academics.models.core import (
            StudentClassEnrollment,
        )
        from sqlalchemy.orm import selectinload

        query = select(StudentClassEnrollment).where(
            and_(
                StudentClassEnrollment.id == enrollment_id,
                StudentClassEnrollment.school_id == school_id,
            )
        ).options(
            selectinload(StudentClassEnrollment.class_level),
            selectinload(StudentClassEnrollment.stream),
            selectinload(StudentClassEnrollment.term),
            selectinload(StudentClassEnrollment.academic_year),
            selectinload(StudentClassEnrollment.subject_selections).selectinload(
                lambda: StudentClassEnrollment.subject_selections[0].subject
            ),
        )

        enrollment = await db.scalar(query)

        if not enrollment:
            return APIResponse.error(
                error="Not found",
                message="Enrollment not found",
                status_code=404,
            )

        # Build response
        class_level_response = ClassLevelResponse(
            id=enrollment.class_level.id,
            academic_year_id=enrollment.class_level.academic_year_id,
            name=enrollment.class_level.name,
            level_code=enrollment.class_level.level_code,
            curriculum_type=enrollment.class_level.curriculum_type,
            is_active=enrollment.class_level.is_active,
            created_at=enrollment.class_level.created_at.isoformat(),
        )

        stream_response = StreamResponse(
            id=enrollment.stream.id,
            class_level_id=enrollment.stream.class_level_id,
            name=enrollment.stream.name,
            stream_code=enrollment.stream.stream_code,
            max_capacity=enrollment.stream.max_capacity,
            current_enrollment=enrollment.stream.current_enrollment,
            form_tutor_id=enrollment.stream.form_tutor_id,
            is_active=enrollment.stream.is_active,
            created_at=enrollment.stream.created_at.isoformat(),
        )

        term_response = TermResponse(
            id=enrollment.term.id,
            academic_year_id=enrollment.term.academic_year_id,
            term_number=enrollment.term.term_number,
            name=enrollment.term.name,
            start_date=enrollment.term.start_date,
            end_date=enrollment.term.end_date,
            is_active=enrollment.term.is_active,
            created_at=enrollment.term.created_at.isoformat(),
        )

        subject_responses = [
            StudentSubjectSelectionDetailResponse(
                id=selection.id,
                enrollment_id=selection.enrollment_id,
                subject_id=selection.subject_id,
                is_compulsory=selection.is_compulsory,
                selection_date=selection.selection_date,
                created_at=selection.created_at.isoformat(),
                subject=__dict__,  # Would be properly built in real code
            )
            for selection in enrollment.subject_selections
        ]

        response = StudentEnrollmentDetailResponse(
            id=enrollment.id,
            student_id=enrollment.student_id,
            enrollment_date=enrollment.enrollment_date,
            is_active=enrollment.is_active,
            class_level=class_level_response,
            stream=stream_response,
            academic_year={
                "id": enrollment.academic_year.id,
                "year": enrollment.academic_year.year,
            },
            term=term_response,
            subject_selections=subject_responses,
        )

        return APIResponse.success(
            data=response,
            message="Enrollment retrieved",
            status_code=200,
        )

    except Exception as e:
        logger.error(f"Error getting enrollment: {e}")
        return APIResponse.error(
            error=str(e),
            message="Failed to retrieve enrollment",
            status_code=500,
        )


@router.get("/students/{student_id}/enrollments", response_model=APIResponse)
async def get_student_enrollments(
    student_id: UUID,
    db: AsyncSession = Depends(get_db),
    school_id: UUID = Depends(lambda: UUID("00000000-0000-0000-0000-000000000000")),
    academic_year_id: UUID = Query(None, description="Filter by academic year"),
) -> APIResponse:
    """
    Get student's enrollment history (transcript).

    Shows all terms the student has been enrolled, with class levels and streams.
    Can be filtered by academic year.
    """
    try:
        service = EnrollmentService(db)

        enrollments = await service.get_student_enrollments(
            school_id=school_id,
            student_id=student_id,
            academic_year_id=academic_year_id,
            active_only=False,  # Include all enrollments
        )

        enrollment_responses = []
        for enrollment in enrollments:
            subject_count = len(enrollment.subject_selections)

            response = StudentEnrollmentListResponse(
                id=enrollment.id,
                class_level_id=enrollment.class_level.id,
                class_level_name=enrollment.class_level.name,
                stream_id=enrollment.stream.id,
                stream_name=enrollment.stream.name,
                academic_year_id=enrollment.academic_year.id,
                academic_year=enrollment.academic_year.year,
                term_id=enrollment.term.id,
                term_name=enrollment.term.name,
                term_number=enrollment.term.term_number,
                enrollment_date=enrollment.enrollment_date,
                is_active=enrollment.is_active,
                subject_count=subject_count,
            )
            enrollment_responses.append(response)

        transcript = StudentTranscriptSummary(
            student_id=student_id,
            enrollments=enrollment_responses,
        )

        return APIResponse.success(
            data=transcript,
            message=f"Found {len(enrollment_responses)} enrollments",
            status_code=200,
        )

    except Exception as e:
        logger.error(f"Error getting student enrollments: {e}")
        return APIResponse.error(
            error=str(e),
            message="Failed to retrieve student enrollments",
            status_code=500,
        )


# ============================================================================
# SUBJECT SELECTION
# ============================================================================


@router.post("/enrollments/{enrollment_id}/subjects/{subject_id}", response_model=APIResponse)
async def add_subject_to_enrollment(
    enrollment_id: UUID,
    subject_id: UUID,
    db: AsyncSession = Depends(get_db),
    school_id: UUID = Depends(lambda: UUID("00000000-0000-0000-0000-000000000000")),
) -> APIResponse:
    """
    Add an elective subject to student's enrollment.

    Only elective (is_compulsory=False) subjects can be added.
    Compulsory subjects are auto-assigned during enrollment.

    Example:
    POST /api/v1/academics/enrollments/{enrollment_id}/subjects/{subject_id}
    """
    try:
        service = EnrollmentService(db)

        # Add subject (will validate it's elective)
        selection = await service.update_subject_selection(
            school_id=school_id,
            enrollment_id=enrollment_id,
            subject_id=subject_id,
            add=True,
        )

        response = StudentSubjectSelectionDetailResponse(
            id=selection.id,
            enrollment_id=selection.enrollment_id,
            subject_id=selection.subject_id,
            is_compulsory=selection.is_compulsory,
            selection_date=selection.selection_date,
            created_at=selection.created_at.isoformat(),
            subject={},  # Would be populated in real code
        )

        return APIResponse.success(
            data=response,
            message="Subject added to enrollment",
            status_code=201,
        )

    except NotFoundError as e:
        logger.warning(f"Subject selection not found: {e}")
        return APIResponse.error(
            error=str(e),
            message="Enrollment or subject not found",
            status_code=404,
        )

    except ValidationError as e:
        logger.warning(f"Subject selection validation error: {e}")
        return APIResponse.error(
            error=str(e),
            message="Cannot add subject",
            status_code=400,
        )

    except Exception as e:
        logger.error(f"Error adding subject: {e}")
        return APIResponse.error(
            error=str(e),
            message="Failed to add subject",
            status_code=500,
        )


@router.delete("/enrollments/{enrollment_id}/subjects/{subject_id}", response_model=APIResponse)
async def remove_subject_from_enrollment(
    enrollment_id: UUID,
    subject_id: UUID,
    db: AsyncSession = Depends(get_db),
    school_id: UUID = Depends(lambda: UUID("00000000-0000-0000-0000-000000000000")),
) -> APIResponse:
    """
    Remove an elective subject from student's enrollment.

    Only elective subjects can be removed.
    Compulsory subjects cannot be removed.

    Example:
    DELETE /api/v1/academics/enrollments/{enrollment_id}/subjects/{subject_id}
    """
    try:
        service = EnrollmentService(db)

        # Remove subject (will validate it's elective)
        await service.update_subject_selection(
            school_id=school_id,
            enrollment_id=enrollment_id,
            subject_id=subject_id,
            add=False,
        )

        return APIResponse.success(
            data={"removed": True},
            message="Subject removed from enrollment",
            status_code=200,
        )

    except NotFoundError as e:
        logger.warning(f"Subject not found for removal: {e}")
        return APIResponse.error(
            error=str(e),
            message="Enrollment or subject not found",
            status_code=404,
        )

    except ValidationError as e:
        logger.warning(f"Subject removal validation error: {e}")
        return APIResponse.error(
            error=str(e),
            message="Cannot remove subject",
            status_code=400,
        )

    except Exception as e:
        logger.error(f"Error removing subject: {e}")
        return APIResponse.error(
            error=str(e),
            message="Failed to remove subject",
            status_code=500,
        )


# ============================================================================
# CLASS ROLL CALL / CLASS LISTS
# ============================================================================


@router.get("/class-levels/{class_level_id}/streams/{stream_id}/roll-call", response_model=APIResponse)
async def get_stream_roll_call(
    class_level_id: UUID,
    stream_id: UUID,
    db: AsyncSession = Depends(get_db),
    school_id: UUID = Depends(lambda: UUID("00000000-0000-0000-0000-000000000000")),
    term_id: UUID = Query(None, description="Term ID (defaults to current term)"),
) -> APIResponse:
    """
    Get roll call for a stream (list of all students in stream).

    Returns:
    - Student names
    - Admission numbers
    - Contact information
    - Subjects enrolled

    Used for attendance tracking, exam invigilation, etc.
    """
    try:
        service = EnrollmentService(db)

        if term_id is None:
            # Would default to current term in real implementation
            return APIResponse.error(
                error="term_id required",
                message="Please specify term_id",
                status_code=400,
            )

        enrollments = await service.get_stream_enrollment(
            school_id=school_id,
            stream_id=stream_id,
            term_id=term_id,
        )

        roll_call = []
        for enrollment in enrollments:
            subject_names = [s.subject.name for s in enrollment.subject_selections]

            roll_call.append({
                "enrollment_id": str(enrollment.id),
                "student_id": str(enrollment.student_id),
                "student_name": f"{enrollment.student.first_name} {enrollment.student.last_name}",
                "admission_number": enrollment.student.admission_number,
                "phone": enrollment.student.phone_number,
                "subjects": subject_names,
            })

        return APIResponse.success(
            data={
                "class_level_id": str(class_level_id),
                "stream_id": str(stream_id),
                "term_id": str(term_id),
                "total_students": len(roll_call),
                "students": roll_call,
            },
            message=f"Roll call retrieved: {len(roll_call)} students",
            status_code=200,
        )

    except Exception as e:
        logger.error(f"Error getting roll call: {e}")
        return APIResponse.error(
            error=str(e),
            message="Failed to retrieve roll call",
            status_code=500,
        )
