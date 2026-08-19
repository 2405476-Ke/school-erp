"""
Academics Core Routers: CRUD endpoints for academic structure.

Endpoints for:
- Academic Years
- Terms
- Class Levels
- Streams
- Subjects
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
from src.modules.academics.models.core import (
    AcademicYear,
    ClassLevel,
    ClassLevelSubject,
    Stream,
    Subject,
    Term,
)
from src.modules.academics.schemas.core import (
    AcademicYearCreate,
    AcademicYearDetailResponse,
    AcademicYearResponse,
    AcademicYearUpdate,
    ClassLevelCreate,
    ClassLevelDetailResponse,
    ClassLevelResponse,
    ClassLevelSummaryResponse,
    ClassLevelUpdate,
    ClassStreamSummary,
    StreamCreate,
    StreamResponse,
    StreamUpdate,
    SubjectCreate,
    SubjectResponse,
    SubjectUpdate,
    TermCreate,
    TermResponse,
    TermUpdate,
)

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/academics", tags=["Academics"])


# ============================================================================
# ACADEMIC YEARS
# ============================================================================


@router.post("/academic-years", response_model=APIResponse)
async def create_academic_year(
    request: AcademicYearCreate,
    db: AsyncSession = Depends(get_db),
    school_id: UUID = Depends(lambda: UUID("00000000-0000-0000-0000-000000000000")),  # Placeholder
) -> APIResponse:
    """
    Create an academic year.

    Example:
    {
        "year": 2024,
        "start_date": "2024-01-15",
        "end_date": "2024-12-20",
        "is_current": true
    }
    """
    try:
        # Verify year is unique for school
        existing_query = select(AcademicYear).where(
            and_(
                AcademicYear.school_id == school_id,
                AcademicYear.year == request.year,
            )
        )
        existing = await db.scalar(existing_query)

        if existing:
            return APIResponse.error(
                error=f"Academic year {request.year} already exists for school",
                message="Duplicate academic year",
                status_code=400,
            )

        # If marking as current, unset other years
        if request.is_current:
            update_query = select(AcademicYear).where(
                and_(
                    AcademicYear.school_id == school_id,
                    AcademicYear.is_current == True,
                )
            )
            current_years = (await db.execute(update_query)).scalars().all()
            for year in current_years:
                year.is_current = False

        # Create year
        academic_year = AcademicYear(
            school_id=school_id,
            year=request.year,
            start_date=request.start_date,
            end_date=request.end_date,
            is_current=request.is_current,
            is_active=True,
        )
        db.add(academic_year)
        await db.commit()

        response = AcademicYearResponse(
            id=academic_year.id,
            year=academic_year.year,
            start_date=academic_year.start_date,
            end_date=academic_year.end_date,
            is_current=academic_year.is_current,
            is_active=academic_year.is_active,
            created_at=academic_year.created_at.isoformat(),
        )

        return APIResponse.success(
            data=response,
            message=f"Academic year {request.year} created",
            status_code=201,
        )

    except Exception as e:
        logger.error(f"Error creating academic year: {e}")
        return APIResponse.error(
            error=str(e),
            message="Failed to create academic year",
            status_code=500,
        )


@router.get("/academic-years", response_model=APIResponse)
async def list_academic_years(
    db: AsyncSession = Depends(get_db),
    school_id: UUID = Depends(lambda: UUID("00000000-0000-0000-0000-000000000000")),
    active_only: bool = Query(False, description="Only active academic years"),
) -> APIResponse:
    """List all academic years for school."""
    try:
        query = select(AcademicYear).where(
            AcademicYear.school_id == school_id
        )

        if active_only:
            query = query.where(AcademicYear.is_active == True)

        query = query.order_by(AcademicYear.year.desc())

        result = await db.execute(query)
        years = result.scalars().all()

        responses = [
            AcademicYearResponse(
                id=year.id,
                year=year.year,
                start_date=year.start_date,
                end_date=year.end_date,
                is_current=year.is_current,
                is_active=year.is_active,
                created_at=year.created_at.isoformat(),
            )
            for year in years
        ]

        return APIResponse.success(
            data=responses,
            message=f"Found {len(responses)} academic years",
            status_code=200,
        )

    except Exception as e:
        logger.error(f"Error listing academic years: {e}")
        return APIResponse.error(
            error=str(e),
            message="Failed to list academic years",
            status_code=500,
        )


@router.get("/academic-years/{academic_year_id}", response_model=APIResponse)
async def get_academic_year(
    academic_year_id: UUID,
    db: AsyncSession = Depends(get_db),
    school_id: UUID = Depends(lambda: UUID("00000000-0000-0000-0000-000000000000")),
) -> APIResponse:
    """Get academic year with nested terms."""
    try:
        query = select(AcademicYear).where(
            and_(
                AcademicYear.id == academic_year_id,
                AcademicYear.school_id == school_id,
            )
        ).options(selectinload(AcademicYear.terms))

        year = await db.scalar(query)

        if not year:
            return APIResponse.error(
                error="Not found",
                message="Academic year not found",
                status_code=404,
            )

        term_responses = [
            TermResponse(
                id=term.id,
                academic_year_id=term.academic_year_id,
                term_number=term.term_number,
                name=term.name,
                start_date=term.start_date,
                end_date=term.end_date,
                is_active=term.is_active,
                created_at=term.created_at.isoformat(),
            )
            for term in year.terms
        ]

        response = AcademicYearDetailResponse(
            id=year.id,
            year=year.year,
            start_date=year.start_date,
            end_date=year.end_date,
            is_current=year.is_current,
            is_active=year.is_active,
            created_at=year.created_at.isoformat(),
            terms=term_responses,
        )

        return APIResponse.success(
            data=response,
            message="Academic year retrieved",
            status_code=200,
        )

    except Exception as e:
        logger.error(f"Error getting academic year: {e}")
        return APIResponse.error(
            error=str(e),
            message="Failed to retrieve academic year",
            status_code=500,
        )


# ============================================================================
# TERMS
# ============================================================================


@router.post("/terms", response_model=APIResponse)
async def create_term(
    request: TermCreate,
    db: AsyncSession = Depends(get_db),
    school_id: UUID = Depends(lambda: UUID("00000000-0000-0000-0000-000000000000")),
) -> APIResponse:
    """Create a term."""
    try:
        # Verify academic year exists
        year_query = select(AcademicYear).where(
            and_(
                AcademicYear.id == request.academic_year_id,
                AcademicYear.school_id == school_id,
            )
        )
        academic_year = await db.scalar(year_query)

        if not academic_year:
            return APIResponse.error(
                error="Academic year not found",
                message="Invalid academic year",
                status_code=404,
            )

        # Check for duplicate term number
        existing_query = select(Term).where(
            and_(
                Term.school_id == school_id,
                Term.academic_year_id == request.academic_year_id,
                Term.term_number == request.term_number,
            )
        )
        existing = await db.scalar(existing_query)

        if existing:
            return APIResponse.error(
                error="Term already exists",
                message=f"Term {request.term_number} already created for this academic year",
                status_code=400,
            )

        # Create term
        term = Term(
            school_id=school_id,
            academic_year_id=request.academic_year_id,
            term_number=request.term_number,
            name=request.name,
            start_date=request.start_date,
            end_date=request.end_date,
            is_active=True,
        )
        db.add(term)
        await db.commit()

        response = TermResponse(
            id=term.id,
            academic_year_id=term.academic_year_id,
            term_number=term.term_number,
            name=term.name,
            start_date=term.start_date,
            end_date=term.end_date,
            is_active=term.is_active,
            created_at=term.created_at.isoformat(),
        )

        return APIResponse.success(
            data=response,
            message=f"Term {request.name} created",
            status_code=201,
        )

    except Exception as e:
        logger.error(f"Error creating term: {e}")
        return APIResponse.error(
            error=str(e),
            message="Failed to create term",
            status_code=500,
        )


@router.get("/terms", response_model=APIResponse)
async def list_terms(
    db: AsyncSession = Depends(get_db),
    school_id: UUID = Depends(lambda: UUID("00000000-0000-0000-0000-000000000000")),
    academic_year_id: UUID = Query(None, description="Filter by academic year"),
) -> APIResponse:
    """List all terms."""
    try:
        query = select(Term).where(Term.school_id == school_id)

        if academic_year_id:
            query = query.where(Term.academic_year_id == academic_year_id)

        query = query.order_by(Term.academic_year_id.desc(), Term.term_number)

        result = await db.execute(query)
        terms = result.scalars().all()

        responses = [
            TermResponse(
                id=term.id,
                academic_year_id=term.academic_year_id,
                term_number=term.term_number,
                name=term.name,
                start_date=term.start_date,
                end_date=term.end_date,
                is_active=term.is_active,
                created_at=term.created_at.isoformat(),
            )
            for term in terms
        ]

        return APIResponse.success(
            data=responses,
            message=f"Found {len(responses)} terms",
            status_code=200,
        )

    except Exception as e:
        logger.error(f"Error listing terms: {e}")
        return APIResponse.error(
            error=str(e),
            message="Failed to list terms",
            status_code=500,
        )


# ============================================================================
# SUBJECTS
# ============================================================================


@router.post("/subjects", response_model=APIResponse)
async def create_subject(
    request: SubjectCreate,
    db: AsyncSession = Depends(get_db),
    school_id: UUID = Depends(lambda: UUID("00000000-0000-0000-0000-000000000000")),
) -> APIResponse:
    """Create a subject."""
    try:
        # Check for duplicate code
        existing_query = select(Subject).where(
            and_(
                Subject.school_id == school_id,
                Subject.subject_code == request.subject_code,
            )
        )
        existing = await db.scalar(existing_query)

        if existing:
            return APIResponse.error(
                error="Subject code already exists",
                message=f"Subject {request.subject_code} already created",
                status_code=400,
            )

        # Create subject
        subject = Subject(
            school_id=school_id,
            subject_code=request.subject_code,
            name=request.name,
            description=request.description,
            is_compulsory=request.is_compulsory,
            is_active=True,
        )
        db.add(subject)
        await db.commit()

        response = SubjectResponse(
            id=subject.id,
            subject_code=subject.subject_code,
            name=subject.name,
            description=subject.description,
            is_compulsory=subject.is_compulsory,
            is_active=subject.is_active,
            created_at=subject.created_at.isoformat(),
        )

        return APIResponse.success(
            data=response,
            message=f"Subject {request.name} created",
            status_code=201,
        )

    except Exception as e:
        logger.error(f"Error creating subject: {e}")
        return APIResponse.error(
            error=str(e),
            message="Failed to create subject",
            status_code=500,
        )


@router.get("/subjects", response_model=APIResponse)
async def list_subjects(
    db: AsyncSession = Depends(get_db),
    school_id: UUID = Depends(lambda: UUID("00000000-0000-0000-0000-000000000000")),
    is_compulsory: bool = Query(None, description="Filter by compulsory/elective"),
) -> APIResponse:
    """List all subjects."""
    try:
        query = select(Subject).where(
            and_(
                Subject.school_id == school_id,
                Subject.is_active == True,
            )
        )

        if is_compulsory is not None:
            query = query.where(Subject.is_compulsory == is_compulsory)

        query = query.order_by(Subject.name)

        result = await db.execute(query)
        subjects = result.scalars().all()

        responses = [
            SubjectResponse(
                id=subject.id,
                subject_code=subject.subject_code,
                name=subject.name,
                description=subject.description,
                is_compulsory=subject.is_compulsory,
                is_active=subject.is_active,
                created_at=subject.created_at.isoformat(),
            )
            for subject in subjects
        ]

        return APIResponse.success(
            data=responses,
            message=f"Found {len(responses)} subjects",
            status_code=200,
        )

    except Exception as e:
        logger.error(f"Error listing subjects: {e}")
        return APIResponse.error(
            error=str(e),
            message="Failed to list subjects",
            status_code=500,
        )


# ============================================================================
# CLASS LEVELS
# ============================================================================


@router.post("/class-levels", response_model=APIResponse)
async def create_class_level(
    request: ClassLevelCreate,
    db: AsyncSession = Depends(get_db),
    school_id: UUID = Depends(lambda: UUID("00000000-0000-0000-0000-000000000000")),
) -> APIResponse:
    """Create a class level."""
    try:
        # Verify academic year exists
        year_query = select(AcademicYear).where(
            and_(
                AcademicYear.id == request.academic_year_id,
                AcademicYear.school_id == school_id,
            )
        )
        academic_year = await db.scalar(year_query)

        if not academic_year:
            return APIResponse.error(
                error="Academic year not found",
                message="Invalid academic year",
                status_code=404,
            )

        # Check for duplicate code
        existing_query = select(ClassLevel).where(
            and_(
                ClassLevel.school_id == school_id,
                ClassLevel.academic_year_id == request.academic_year_id,
                ClassLevel.level_code == request.level_code,
            )
        )
        existing = await db.scalar(existing_query)

        if existing:
            return APIResponse.error(
                error="Class level code already exists",
                message=f"Class {request.level_code} already created",
                status_code=400,
            )

        # Create class level
        class_level = ClassLevel(
            school_id=school_id,
            academic_year_id=request.academic_year_id,
            name=request.name,
            level_code=request.level_code,
            curriculum_type=request.curriculum_type,
            is_active=True,
        )
        db.add(class_level)
        await db.commit()

        response = ClassLevelResponse(
            id=class_level.id,
            academic_year_id=class_level.academic_year_id,
            name=class_level.name,
            level_code=class_level.level_code,
            curriculum_type=class_level.curriculum_type,
            is_active=class_level.is_active,
            created_at=class_level.created_at.isoformat(),
        )

        return APIResponse.success(
            data=response,
            message=f"Class level {request.name} created",
            status_code=201,
        )

    except Exception as e:
        logger.error(f"Error creating class level: {e}")
        return APIResponse.error(
            error=str(e),
            message="Failed to create class level",
            status_code=500,
        )


@router.get("/class-levels", response_model=APIResponse)
async def list_class_levels(
    db: AsyncSession = Depends(get_db),
    school_id: UUID = Depends(lambda: UUID("00000000-0000-0000-0000-000000000000")),
    academic_year_id: UUID = Query(None, description="Filter by academic year"),
) -> APIResponse:
    """List all class levels."""
    try:
        query = select(ClassLevel).where(
            and_(
                ClassLevel.school_id == school_id,
                ClassLevel.is_active == True,
            )
        )

        if academic_year_id:
            query = query.where(ClassLevel.academic_year_id == academic_year_id)

        query = query.options(
            selectinload(ClassLevel.streams),
        ).order_by(ClassLevel.level_code)

        result = await db.execute(query)
        class_levels = result.scalars().all()

        responses = []
        for cl in class_levels:
            stream_responses = [
                ClassStreamSummary(
                    id=stream.id,
                    name=stream.name,
                    stream_code=stream.stream_code,
                    current_enrollment=stream.current_enrollment,
                    max_capacity=stream.max_capacity,
                    available_capacity=stream.available_capacity,
                    form_tutor_id=stream.form_tutor_id,
                )
                for stream in cl.streams
            ]

            total_enrollment = sum(s.current_enrollment for s in cl.streams)
            total_capacity = sum(s.max_capacity for s in cl.streams)

            response = ClassLevelSummaryResponse(
                id=cl.id,
                name=cl.name,
                level_code=cl.level_code,
                curriculum_type=cl.curriculum_type,
                streams=stream_responses,
                total_enrollment=total_enrollment,
                total_capacity=total_capacity,
            )
            responses.append(response)

        return APIResponse.success(
            data=responses,
            message=f"Found {len(responses)} class levels",
            status_code=200,
        )

    except Exception as e:
        logger.error(f"Error listing class levels: {e}")
        return APIResponse.error(
            error=str(e),
            message="Failed to list class levels",
            status_code=500,
        )


@router.post("/streams", response_model=APIResponse)
async def create_stream(
    request: StreamCreate,
    db: AsyncSession = Depends(get_db),
    school_id: UUID = Depends(lambda: UUID("00000000-0000-0000-0000-000000000000")),
) -> APIResponse:
    """Create a stream (section) within a class level."""
    try:
        # Verify class level exists
        class_query = select(ClassLevel).where(
            and_(
                ClassLevel.id == request.class_level_id,
                ClassLevel.school_id == school_id,
            )
        )
        class_level = await db.scalar(class_query)

        if not class_level:
            return APIResponse.error(
                error="Class level not found",
                message="Invalid class level",
                status_code=404,
            )

        # Check for duplicate code
        existing_query = select(Stream).where(
            and_(
                Stream.school_id == school_id,
                Stream.class_level_id == request.class_level_id,
                Stream.stream_code == request.stream_code,
            )
        )
        existing = await db.scalar(existing_query)

        if existing:
            return APIResponse.error(
                error="Stream code already exists",
                message=f"Stream {request.stream_code} already created",
                status_code=400,
            )

        # Create stream
        stream = Stream(
            school_id=school_id,
            class_level_id=request.class_level_id,
            name=request.name,
            stream_code=request.stream_code,
            max_capacity=request.max_capacity,
            current_enrollment=0,
            form_tutor_id=request.form_tutor_id,
            is_active=True,
        )
        db.add(stream)
        await db.commit()

        response = StreamResponse(
            id=stream.id,
            class_level_id=stream.class_level_id,
            name=stream.name,
            stream_code=stream.stream_code,
            max_capacity=stream.max_capacity,
            current_enrollment=stream.current_enrollment,
            form_tutor_id=stream.form_tutor_id,
            is_active=stream.is_active,
            created_at=stream.created_at.isoformat(),
        )

        return APIResponse.success(
            data=response,
            message=f"Stream {request.name} created",
            status_code=201,
        )

    except Exception as e:
        logger.error(f"Error creating stream: {e}")
        return APIResponse.error(
            error=str(e),
            message="Failed to create stream",
            status_code=500,
        )
