"""
Routers for 8-4-4 Examination System: Manage exams, input marks, generate reports.

Endpoints for:
- Grading system configuration
- Exam management (CRUD)
- Bulk mark input
- Report card generation
- Performance analytics
"""
import logging
from uuid import UUID

from fastapi import APIRouter, Depends, Query
from sqlalchemy import and_, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from src.core.database import get_db
from src.core.exceptions import NotFoundError, ValidationError
from src.core.response import APIResponse
from src.modules.academics.models.exams_844 import Exam, ExamResult844, GradingSystem
from src.modules.academics.schemas.exams_844 import (
    ExamCreate,
    ExamDetailResponse,
    ExamResponse,
    ExamResult844BatchInput,
    ExamResult844Response,
    GradingSystemCreate,
    GradingSystemResponse,
    ReportCard844Response,
)
from src.modules.academics.services.grading_service_844 import GradingService844
from src.modules.academics.services.report_card_844_service import ReportCardService844

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/academics/844", tags=["Academics - 8-4-4 Exams"])


# ============================================================================
# GRADING SYSTEM MANAGEMENT
# ============================================================================


@router.post("/grading-system/initialize", response_model=APIResponse)
async def initialize_school_grading_system(
    db: AsyncSession = Depends(get_db),
    school_id: UUID = Depends(lambda: UUID("00000000-0000-0000-0000-000000000000")),
) -> APIResponse:
    """
    Initialize school with Kenyan standard grading system.

    Creates 10 grading entries (A, A-, B+, B, B-, C, D, D-, E, F) with standard ranges.

    Example Response:
    {
        "success": true,
        "data": {
            "grading_entries_created": 10,
            "school_id": "550e8400-e29b-41d4-a716-446655440000"
        }
    }
    """
    try:
        grading_service = GradingService844(db)
        count = await grading_service.initialize_school_grading_system(school_id)

        return APIResponse.success(
            data={
                "grading_entries_created": count,
                "school_id": str(school_id),
            },
            message=f"Grading system initialized with {count} entries",
            status_code=201,
        )

    except ValidationError as e:
        logger.warning(f"Grading system initialization error: {e}")
        return APIResponse.error(
            error=str(e),
            message="Grading system already initialized",
            status_code=409,
        )

    except Exception as e:
        logger.error(f"Error initializing grading system: {e}")
        return APIResponse.error(
            error=str(e),
            message="Failed to initialize grading system",
            status_code=500,
        )


@router.post("/grading-system/entries", response_model=APIResponse)
async def create_grading_entry(
    request: GradingSystemCreate,
    db: AsyncSession = Depends(get_db),
    school_id: UUID = Depends(lambda: UUID("00000000-0000-0000-0000-000000000000")),
) -> APIResponse:
    """
    Create custom grading entry for school.

    Example:
    {
        "min_mark": 80,
        "max_mark": 100,
        "grade": "A",
        "points": 12,
        "description": "Excellent performance"
    }
    """
    try:
        grading_service = GradingService844(db)

        # Validate entry
        await grading_service.validate_grading_entry(
            request.min_mark,
            request.max_mark,
            request.points,
        )

        # Check for overlap with existing entries
        overlap_query = select(GradingSystem).where(
            and_(
                GradingSystem.school_id == school_id,
                GradingSystem.min_mark <= request.max_mark,
                GradingSystem.max_mark >= request.min_mark,
            )
        )
        overlaps = (await db.execute(overlap_query)).scalars().all()

        if overlaps:
            return APIResponse.error(
                error="Mark range overlaps with existing entry",
                message=f"Grading entry overlaps with {len(overlaps)} existing entries",
                status_code=400,
            )

        # Create entry
        grading = GradingSystem(
            school_id=school_id,
            min_mark=request.min_mark,
            max_mark=request.max_mark,
            grade=request.grade,
            points=request.points,
            description=request.description,
        )
        db.add(grading)
        await db.commit()

        response = GradingSystemResponse(
            id=grading.id,
            min_mark=grading.min_mark,
            max_mark=grading.max_mark,
            grade=grading.grade,
            points=grading.points,
            description=grading.description,
            created_at=grading.created_at.isoformat(),
        )

        return APIResponse.success(
            data=response,
            message=f"Grading entry {request.grade} created",
            status_code=201,
        )

    except ValidationError as e:
        logger.warning(f"Grading entry validation error: {e}")
        return APIResponse.error(
            error=str(e),
            message="Invalid grading entry",
            status_code=400,
        )

    except Exception as e:
        logger.error(f"Error creating grading entry: {e}")
        return APIResponse.error(
            error=str(e),
            message="Failed to create grading entry",
            status_code=500,
        )


@router.get("/grading-system", response_model=APIResponse)
async def get_grading_system(
    db: AsyncSession = Depends(get_db),
    school_id: UUID = Depends(lambda: UUID("00000000-0000-0000-0000-000000000000")),
) -> APIResponse:
    """Get school's grading system (all entries)."""
    try:
        grading_service = GradingService844(db)
        entries = await grading_service.get_grading_system(school_id)

        return APIResponse.success(
            data=entries,
            message=f"Grading system retrieved ({len(entries)} entries)",
            status_code=200,
        )

    except Exception as e:
        logger.error(f"Error getting grading system: {e}")
        return APIResponse.error(
            error=str(e),
            message="Failed to retrieve grading system",
            status_code=500,
        )


# ============================================================================
# EXAM MANAGEMENT
# ============================================================================


@router.post("/exams", response_model=APIResponse)
async def create_exam(
    request: ExamCreate,
    db: AsyncSession = Depends(get_db),
    school_id: UUID = Depends(lambda: UUID("00000000-0000-0000-0000-000000000000")),
) -> APIResponse:
    """
    Create an examination sitting.

    Example:
    {
        "term_id": "550e8400-e29b-41d4-a716-446655440000",
        "exam_type": "EOT",
        "name": "End of Term 1 2024",
        "exam_date": "2024-04-15T00:00:00",
        "description": "End of Term Examination"
    }
    """
    try:
        # Verify term exists
        from src.modules.academics.models.core import Term

        term_query = select(Term).where(
            and_(
                Term.id == request.term_id,
                Term.school_id == school_id,
            )
        )
        term = await db.scalar(term_query)

        if not term:
            return APIResponse.error(
                error="Term not found",
                message="Invalid term ID",
                status_code=404,
            )

        # Check for duplicate exam (same term + type)
        existing_query = select(Exam).where(
            and_(
                Exam.school_id == school_id,
                Exam.term_id == request.term_id,
                Exam.exam_type == request.exam_type,
            )
        )
        existing = await db.scalar(existing_query)

        if existing:
            return APIResponse.error(
                error="Exam already exists",
                message=f"Exam {request.exam_type} already created for this term",
                status_code=400,
            )

        # Create exam
        exam = Exam(
            school_id=school_id,
            term_id=request.term_id,
            exam_type=request.exam_type,
            name=request.name,
            exam_date=request.exam_date,
            description=request.description,
            is_active=True,
        )
        db.add(exam)
        await db.commit()

        response = ExamResponse(
            id=exam.id,
            term_id=exam.term_id,
            exam_type=exam.exam_type,
            name=exam.name,
            exam_date=exam.exam_date.isoformat(),
            description=exam.description,
            is_active=exam.is_active,
            created_at=exam.created_at.isoformat(),
        )

        return APIResponse.success(
            data=response,
            message=f"Exam {request.name} created",
            status_code=201,
        )

    except Exception as e:
        logger.error(f"Error creating exam: {e}")
        return APIResponse.error(
            error=str(e),
            message="Failed to create exam",
            status_code=500,
        )


@router.get("/exams", response_model=APIResponse)
async def list_exams(
    db: AsyncSession = Depends(get_db),
    school_id: UUID = Depends(lambda: UUID("00000000-0000-0000-0000-000000000000")),
    term_id: UUID = Query(None, description="Filter by term"),
) -> APIResponse:
    """List all exams."""
    try:
        query = select(Exam).where(
            and_(
                Exam.school_id == school_id,
                Exam.is_active == True,
            )
        )

        if term_id:
            query = query.where(Exam.term_id == term_id)

        query = query.order_by(Exam.exam_date.desc())

        result = await db.execute(query)
        exams = result.scalars().all()

        responses = [
            ExamResponse(
                id=exam.id,
                term_id=exam.term_id,
                exam_type=exam.exam_type,
                name=exam.name,
                exam_date=exam.exam_date.isoformat(),
                description=exam.description,
                is_active=exam.is_active,
                created_at=exam.created_at.isoformat(),
            )
            for exam in exams
        ]

        return APIResponse.success(
            data=responses,
            message=f"Found {len(responses)} exams",
            status_code=200,
        )

    except Exception as e:
        logger.error(f"Error listing exams: {e}")
        return APIResponse.error(
            error=str(e),
            message="Failed to list exams",
            status_code=500,
        )


# ============================================================================
# MARK INPUT (BATCH)
# ============================================================================


@router.post("/marks/batch", response_model=APIResponse)
async def batch_input_marks(
    request: ExamResult844BatchInput,
    db: AsyncSession = Depends(get_db),
    school_id: UUID = Depends(lambda: UUID("00000000-0000-0000-0000-000000000000")),
) -> APIResponse:
    """
    Bulk input exam marks for students.

    REAL ALGORITHM:
    1. Verify exam exists
    2. For each student mark:
       - Verify student exists
       - Verify subject exists
       - Check for duplicate mark (unique constraint)
       - Calculate grade and points using GradingService
       - Create ExamResult844
    3. Commit atomically
    4. Return results with errors

    Example Request:
    {
        "exam_id": "550e8400-e29b-41d4-a716-446655440000",
        "results": [
            {
                "student_id": "660e8400-e29b-41d4-a716-446655440001",
                "subject_id": "770e8400-e29b-41d4-a716-446655440002",
                "mark_score": 85,
                "remarks": "Good performance"
            },
            {
                "student_id": "660e8400-e29b-41d4-a716-446655440001",
                "subject_id": "770e8400-e29b-41d4-a716-446655440003",
                "mark_score": 72,
                "remarks": "Average"
            }
        ]
    }
    """
    try:
        grading_service = GradingService844(db)
        from src.modules.students.models import Student
        from src.modules.academics.models.core import Subject

        # Verify exam exists
        exam_query = select(Exam).where(
            and_(
                Exam.id == request.exam_id,
                Exam.school_id == school_id,
            )
        )
        exam = await db.scalar(exam_query)

        if not exam:
            return APIResponse.error(
                error="Exam not found",
                message="Invalid exam ID",
                status_code=404,
            )

        logger.info(f"Processing {len(request.results)} marks for exam {exam.name}")

        created_count = 0
        updated_count = 0
        failed_count = 0
        errors = []

        for idx, mark_input in enumerate(request.results):
            try:
                # Verify student
                student_query = select(Student).where(
                    and_(
                        Student.id == mark_input.student_id,
                        Student.school_id == school_id,
                    )
                )
                student = await db.scalar(student_query)

                if not student:
                    errors.append({
                        "index": idx,
                        "student_id": str(mark_input.student_id),
                        "error": "Student not found",
                    })
                    failed_count += 1
                    continue

                # Verify subject
                subject_query = select(Subject).where(
                    and_(
                        Subject.id == mark_input.subject_id,
                        Subject.school_id == school_id,
                    )
                )
                subject = await db.scalar(subject_query)

                if not subject:
                    errors.append({
                        "index": idx,
                        "subject_id": str(mark_input.subject_id),
                        "error": "Subject not found",
                    })
                    failed_count += 1
                    continue

                # Calculate grade and points
                grade_result = await grading_service.calculate_grade_and_points(
                    mark_input.mark_score,
                    school_id,
                )

                # Check for existing result (unique constraint)
                existing_query = select(ExamResult844).where(
                    and_(
                        ExamResult844.school_id == school_id,
                        ExamResult844.student_id == mark_input.student_id,
                        ExamResult844.exam_id == request.exam_id,
                        ExamResult844.subject_id == mark_input.subject_id,
                    )
                )
                existing_result = await db.scalar(existing_query)

                if existing_result:
                    # Update existing result
                    existing_result.mark_score = mark_input.mark_score
                    existing_result.grade = grade_result.grade
                    existing_result.points = grade_result.points
                    existing_result.remarks = mark_input.remarks or existing_result.remarks
                    updated_count += 1
                else:
                    # Create new result
                    result = ExamResult844(
                        school_id=school_id,
                        student_id=mark_input.student_id,
                        exam_id=request.exam_id,
                        subject_id=mark_input.subject_id,
                        mark_score=mark_input.mark_score,
                        grade=grade_result.grade,
                        points=grade_result.points,
                        remarks=mark_input.remarks,
                        is_validated=False,
                    )
                    db.add(result)
                    created_count += 1

            except ValidationError as e:
                logger.warning(f"Validation error for mark at index {idx}: {e}")
                errors.append({
                    "index": idx,
                    "student_id": str(mark_input.student_id),
                    "subject_id": str(mark_input.subject_id),
                    "error": str(e),
                })
                failed_count += 1

            except Exception as e:
                logger.error(f"Error processing mark at index {idx}: {e}")
                errors.append({
                    "index": idx,
                    "student_id": str(mark_input.student_id),
                    "subject_id": str(mark_input.subject_id),
                    "error": str(e),
                })
                failed_count += 1

        # Commit all changes atomically
        await db.commit()

        logger.info(
            f"Batch mark input complete: created={created_count}, "
            f"updated={updated_count}, failed={failed_count}"
        )

        return APIResponse.success(
            data={
                "exam_id": str(request.exam_id),
                "total_submitted": len(request.results),
                "created": created_count,
                "updated": updated_count,
                "failed": failed_count,
                "errors": errors if errors else None,
            },
            message=f"Marks processed: {created_count} created, {updated_count} updated",
            status_code=201 if failed_count == 0 else 207,
        )

    except Exception as e:
        logger.error(f"Error in batch mark input: {e}", exc_info=True)
        return APIResponse.error(
            error=str(e),
            message="Batch mark input failed",
            status_code=500,
        )


# ============================================================================
# REPORT CARDS
# ============================================================================


@router.get("/report-cards/{student_id}", response_model=APIResponse)
async def get_report_card(
    student_id: UUID,
    exam_id: UUID = Query(..., description="Exam ID"),
    db: AsyncSession = Depends(get_db),
    school_id: UUID = Depends(lambda: UUID("00000000-0000-0000-0000-000000000000")),
) -> APIResponse:
    """
    Generate report card for student in specific exam.

    COMPLEX ALGORITHM:
    - Fetches all exam results
    - Calculates aggregates (total, mean, grade distribution)
    - Computes stream rank and class rank using window functions
    - Returns deeply nested response

    Example Response:
    {
        "success": true,
        "data": {
            "report_card_id": "880e8400-e29b-41d4-a716-446655440003",
            "student_id": "550e8400-e29b-41d4-a716-446655440000",
            "student_name": "John Doe",
            "exam_name": "End of Term 1 2024",
            "results": [
                {
                    "subject_name": "Mathematics",
                    "mark_score": 85,
                    "grade": "A",
                    "points": 12
                }
            ],
            "aggregates": {
                "total_subjects": 8,
                "total_marks": 650,
                "mean_mark": 81.25,
                "mean_grade": "A",
                "mean_points": 11.5
            },
            "rankings": {
                "stream_rank": 2,
                "stream_total": 45,
                "class_rank": 5,
                "class_total": 120
            }
        }
    }
    """
    try:
        report_service = ReportCardService844(db)
        report_card = await report_service.generate_termly_report_card(
            school_id=school_id,
            student_id=student_id,
            exam_id=exam_id,
        )

        return APIResponse.success(
            data=report_card,
            message=f"Report card generated for {report_card.student_name}",
            status_code=200,
        )

    except NotFoundError as e:
        logger.warning(f"Report card generation not found: {e}")
        return APIResponse.error(
            error=str(e),
            message="Student, exam, or results not found",
            status_code=404,
        )

    except Exception as e:
        logger.error(f"Error generating report card: {e}", exc_info=True)
        return APIResponse.error(
            error=str(e),
            message="Failed to generate report card",
            status_code=500,
        )


@router.get("/class-performance/{class_level_id}", response_model=APIResponse)
async def get_class_performance(
    class_level_id: UUID,
    exam_id: UUID = Query(..., description="Exam ID"),
    term_id: UUID = Query(..., description="Term ID"),
    db: AsyncSession = Depends(get_db),
    school_id: UUID = Depends(lambda: UUID("00000000-0000-0000-0000-000000000000")),
) -> APIResponse:
    """
    Get class-level performance summary.

    Returns:
    - Average performance per subject
    - Grade distribution
    - Top and bottom performers
    """
    try:
        report_service = ReportCardService844(db)
        summary = await report_service.get_class_performance_summary(
            school_id=school_id,
            class_level_id=class_level_id,
            term_id=term_id,
            exam_id=exam_id,
        )

        return APIResponse.success(
            data=summary,
            message="Class performance summary retrieved",
            status_code=200,
        )

    except Exception as e:
        logger.error(f"Error getting class performance: {e}")
        return APIResponse.error(
            error=str(e),
            message="Failed to retrieve class performance",
            status_code=500,
        )
