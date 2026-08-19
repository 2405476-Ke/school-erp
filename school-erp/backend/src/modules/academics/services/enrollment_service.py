"""
Enrollment Service: Business logic for student class enrollment.

Implements:
- enroll_student_in_class()
- Auto-assignment of compulsory subjects
- Stream capacity management
- Subject selection logic
"""
import logging
from datetime import date
from uuid import UUID

from sqlalchemy import and_, select
from sqlalchemy.ext.asyncio import AsyncSession

from src.core.exceptions import NotFoundError, ValidationError
from src.modules.academics.models.core import (
    ClassLevel,
    ClassLevelSubject,
    Stream,
    StudentClassEnrollment,
    StudentSubjectSelection,
    Subject,
    Term,
)
from src.modules.students.models import Student

logger = logging.getLogger(__name__)


class EnrollmentService:
    """
    Service for student enrollment in classes and subjects.

    Business Logic:
    1. Verify student is active
    2. Verify stream exists and has capacity
    3. Check for duplicate enrollment (student already in class/term)
    4. Create StudentClassEnrollment
    5. Auto-assign compulsory subjects for that ClassLevel
    6. Update stream current_enrollment
    7. Atomic: all or nothing
    """

    def __init__(self, db: AsyncSession):
        """Initialize enrollment service with database session."""
        self.db = db

    async def enroll_student_in_class(
        self,
        school_id: UUID,
        student_id: UUID,
        stream_id: UUID,
        term_id: UUID,
        enrollment_date: date = None,
    ) -> tuple[StudentClassEnrollment, int]:
        """
        Enroll a student in a class stream for a term.

        REAL BUSINESS LOGIC:
        1. Fetch and verify student
           - Must exist
           - Must be active
           - Must belong to school
        2. Fetch and verify stream
           - Must exist
           - Must have capacity
           - Get associated ClassLevel
        3. Fetch and verify term
           - Must exist
           - Must be active
           - Get associated AcademicYear
        4. Check for duplicate enrollment
           - Student cannot already be enrolled in same term/class combo
        5. Create StudentClassEnrollment
           - Link student → class + stream + term
           - Set enrollment_date
           - Mark is_active=True
        6. Get all compulsory subjects for ClassLevel
           - Query ClassLevelSubject where Subject.is_compulsory=True
        7. Auto-assign compulsory subjects
           - Create StudentSubjectSelection for each compulsory subject
           - Set is_compulsory=True for each
           - Set selection_date
        8. Update Stream.current_enrollment
           - Increment by 1
           - Verify still <= max_capacity
        9. Commit atomically
           - If any step fails, rollback everything

        Args:
            school_id: School context
            student_id: Student to enroll
            stream_id: Stream to enroll into
            term_id: Term for enrollment
            enrollment_date: Date of enrollment (default: today)

        Returns:
            Tuple of (StudentClassEnrollment, number_of_subjects_assigned)

        Raises:
            NotFoundError: If student, stream, or term not found
            ValidationError: If student inactive, stream full, or duplicate enrollment
        """
        if enrollment_date is None:
            enrollment_date = date.today()

        logger.info(
            f"Enrolling student {student_id} in stream {stream_id}, "
            f"term {term_id} (school {school_id})"
        )

        # 1. Fetch and verify student
        student_query = select(Student).where(
            and_(
                Student.id == student_id,
                Student.school_id == school_id,
                Student.is_deleted == False,
            )
        )
        student = await self.db.scalar(student_query)

        if not student:
            raise NotFoundError(f"Student {student_id} not found or inactive")

        if not student.is_active:
            raise ValidationError(f"Student {student.first_name} {student.last_name} is not active")

        logger.info(f"Student verified: {student.first_name} {student.last_name}")

        # 2. Fetch and verify stream
        stream_query = select(Stream).where(
            and_(
                Stream.id == stream_id,
                Stream.school_id == school_id,
            )
        ).options(selectinload=lambda: Stream.class_level)

        stream = await self.db.scalar(stream_query)

        if not stream:
            raise NotFoundError(f"Stream {stream_id} not found")

        if not stream.is_active:
            raise ValidationError(f"Stream {stream.name} is not active")

        # Check stream capacity
        if stream.current_enrollment >= stream.max_capacity:
            raise ValidationError(
                f"Stream {stream.name} is at full capacity "
                f"({stream.current_enrollment}/{stream.max_capacity})"
            )

        class_level = stream.class_level
        logger.info(f"Stream verified: {stream.name} ({stream.current_enrollment}/{stream.max_capacity})")

        # 3. Fetch and verify term
        term_query = select(Term).where(
            and_(
                Term.id == term_id,
                Term.school_id == school_id,
                Term.is_active == True,
            )
        ).options(selectinload=lambda: Term.academic_year)

        term = await self.db.scalar(term_query)

        if not term:
            raise NotFoundError(f"Term {term_id} not found or inactive")

        academic_year = term.academic_year
        logger.info(f"Term verified: {term.name} ({academic_year.year})")

        # 4. Check for duplicate enrollment
        duplicate_query = select(StudentClassEnrollment).where(
            and_(
                StudentClassEnrollment.student_id == student_id,
                StudentClassEnrollment.academic_year_id == academic_year.id,
                StudentClassEnrollment.term_id == term_id,
                StudentClassEnrollment.school_id == school_id,
            )
        )
        existing_enrollment = await self.db.scalar(duplicate_query)

        if existing_enrollment:
            raise ValidationError(
                f"Student is already enrolled in {term.name} {academic_year.year}"
            )

        # 5. Create StudentClassEnrollment
        enrollment = StudentClassEnrollment(
            school_id=school_id,
            student_id=student_id,
            class_level_id=class_level.id,
            stream_id=stream_id,
            academic_year_id=academic_year.id,
            term_id=term_id,
            enrollment_date=enrollment_date,
            is_active=True,
        )
        self.db.add(enrollment)
        await self.db.flush()  # Get enrollment.id before creating selections

        logger.info(f"StudentClassEnrollment created: {enrollment.id}")

        # 6. Get all compulsory subjects for ClassLevel
        compulsory_subjects_query = select(Subject).join(
            ClassLevelSubject,
            Subject.id == ClassLevelSubject.subject_id,
        ).where(
            and_(
                ClassLevelSubject.class_level_id == class_level.id,
                Subject.is_compulsory == True,
                Subject.is_active == True,
                Subject.school_id == school_id,
            )
        )

        compulsory_subjects = (await self.db.execute(compulsory_subjects_query)).scalars().all()

        logger.info(f"Found {len(compulsory_subjects)} compulsory subjects for {class_level.name}")

        # 7. Auto-assign compulsory subjects
        subject_count = 0
        for subject in compulsory_subjects:
            subject_selection = StudentSubjectSelection(
                school_id=school_id,
                enrollment_id=enrollment.id,
                subject_id=subject.id,
                is_compulsory=True,
                selection_date=enrollment_date,
            )
            self.db.add(subject_selection)
            subject_count += 1

            logger.debug(f"Auto-assigned subject: {subject.name}")

        await self.db.flush()
        logger.info(f"Assigned {subject_count} compulsory subjects")

        # 8. Update Stream.current_enrollment
        stream.current_enrollment += 1

        # Verify still within capacity (should never happen due to check above, but safety)
        if stream.current_enrollment > stream.max_capacity:
            raise ValidationError(
                f"Stream capacity exceeded (race condition detected)"
            )

        logger.info(
            f"Stream updated: {stream.name} "
            f"({stream.current_enrollment}/{stream.max_capacity})"
        )

        # 9. Commit atomically
        await self.db.commit()

        logger.info(
            f"Student {student_id} successfully enrolled: "
            f"{class_level.name}/{stream.name}, "
            f"{subject_count} subjects assigned"
        )

        return enrollment, subject_count

    async def get_student_enrollment_by_term(
        self,
        school_id: UUID,
        student_id: UUID,
        term_id: UUID,
    ) -> StudentClassEnrollment:
        """
        Get student's enrollment for a specific term.

        Args:
            school_id: School context
            student_id: Student ID
            term_id: Term ID

        Returns:
            StudentClassEnrollment or None

        Raises:
            NotFoundError: If enrollment not found
        """
        query = select(StudentClassEnrollment).where(
            and_(
                StudentClassEnrollment.school_id == school_id,
                StudentClassEnrollment.student_id == student_id,
                StudentClassEnrollment.term_id == term_id,
                StudentClassEnrollment.is_active == True,
            )
        ).options(
            selectinload(StudentClassEnrollment.class_level),
            selectinload(StudentClassEnrollment.stream),
            selectinload(StudentClassEnrollment.term),
            selectinload(StudentClassEnrollment.academic_year),
        )

        enrollment = await self.db.scalar(query)

        if not enrollment:
            raise NotFoundError(f"Enrollment not found for student in term")

        return enrollment

    async def get_student_enrollments(
        self,
        school_id: UUID,
        student_id: UUID,
        academic_year_id: UUID = None,
        active_only: bool = True,
    ) -> list[StudentClassEnrollment]:
        """
        Get all enrollments for a student (transcript).

        Args:
            school_id: School context
            student_id: Student ID
            academic_year_id: Optional filter by academic year
            active_only: Only return active enrollments

        Returns:
            List of StudentClassEnrollment records
        """
        query = select(StudentClassEnrollment).where(
            and_(
                StudentClassEnrollment.school_id == school_id,
                StudentClassEnrollment.student_id == student_id,
            )
        )

        if academic_year_id:
            query = query.where(StudentClassEnrollment.academic_year_id == academic_year_id)

        if active_only:
            query = query.where(StudentClassEnrollment.is_active == True)

        query = query.order_by(
            StudentClassEnrollment.academic_year_id.desc(),
            StudentClassEnrollment.created_at.desc(),
        ).options(
            selectinload(StudentClassEnrollment.class_level),
            selectinload(StudentClassEnrollment.stream),
            selectinload(StudentClassEnrollment.term),
            selectinload(StudentClassEnrollment.academic_year),
            selectinload(StudentClassEnrollment.subject_selections).selectinload(
                StudentSubjectSelection.subject
            ),
        )

        result = await self.db.execute(query)
        return result.scalars().all()

    async def get_class_enrollment(
        self,
        school_id: UUID,
        class_level_id: UUID,
        term_id: UUID,
    ) -> list[StudentClassEnrollment]:
        """
        Get all students enrolled in a class for a term.

        Args:
            school_id: School context
            class_level_id: Class level ID
            term_id: Term ID

        Returns:
            List of StudentClassEnrollment records
        """
        query = select(StudentClassEnrollment).where(
            and_(
                StudentClassEnrollment.school_id == school_id,
                StudentClassEnrollment.class_level_id == class_level_id,
                StudentClassEnrollment.term_id == term_id,
                StudentClassEnrollment.is_active == True,
            )
        ).order_by(
            StudentClassEnrollment.stream_id,
            StudentClassEnrollment.student_id,
        ).options(
            selectinload(StudentClassEnrollment.student),
            selectinload(StudentClassEnrollment.stream),
        )

        result = await self.db.execute(query)
        return result.scalars().all()

    async def get_stream_enrollment(
        self,
        school_id: UUID,
        stream_id: UUID,
        term_id: UUID,
    ) -> list[StudentClassEnrollment]:
        """
        Get all students enrolled in a specific stream for a term.

        Args:
            school_id: School context
            stream_id: Stream ID
            term_id: Term ID

        Returns:
            List of StudentClassEnrollment records
        """
        query = select(StudentClassEnrollment).where(
            and_(
                StudentClassEnrollment.school_id == school_id,
                StudentClassEnrollment.stream_id == stream_id,
                StudentClassEnrollment.term_id == term_id,
                StudentClassEnrollment.is_active == True,
            )
        ).order_by(StudentClassEnrollment.created_at).options(
            selectinload(StudentClassEnrollment.student),
        )

        result = await self.db.execute(query)
        return result.scalars().all()

    async def update_subject_selection(
        self,
        school_id: UUID,
        enrollment_id: UUID,
        subject_id: UUID,
        add: bool = True,
    ) -> StudentSubjectSelection:
        """
        Add or remove a subject selection for student (for electives).

        Can only add/remove ELECTIVE (is_compulsory=False) subjects.
        Compulsory subjects cannot be removed.

        Args:
            school_id: School context
            enrollment_id: Enrollment ID
            subject_id: Subject to add/remove
            add: True to add, False to remove

        Returns:
            Updated StudentSubjectSelection or raises error

        Raises:
            NotFoundError: If enrollment or subject not found
            ValidationError: If trying to remove compulsory subject
        """
        # Fetch enrollment
        enrollment_query = select(StudentClassEnrollment).where(
            and_(
                StudentClassEnrollment.id == enrollment_id,
                StudentClassEnrollment.school_id == school_id,
            )
        )
        enrollment = await self.db.scalar(enrollment_query)

        if not enrollment:
            raise NotFoundError(f"Enrollment {enrollment_id} not found")

        # Fetch subject
        subject_query = select(Subject).where(
            and_(
                Subject.id == subject_id,
                Subject.school_id == school_id,
            )
        )
        subject = await self.db.scalar(subject_query)

        if not subject:
            raise NotFoundError(f"Subject {subject_id} not found")

        if add:
            # Add subject (must be elective)
            if subject.is_compulsory:
                raise ValidationError(f"Cannot manually add compulsory subject {subject.name}")

            # Check if already selected
            existing_query = select(StudentSubjectSelection).where(
                and_(
                    StudentSubjectSelection.enrollment_id == enrollment_id,
                    StudentSubjectSelection.subject_id == subject_id,
                )
            )
            existing = await self.db.scalar(existing_query)

            if existing:
                raise ValidationError(f"Subject {subject.name} already selected")

            # Create selection
            selection = StudentSubjectSelection(
                school_id=school_id,
                enrollment_id=enrollment_id,
                subject_id=subject_id,
                is_compulsory=False,
                selection_date=date.today(),
            )
            self.db.add(selection)

            logger.info(f"Subject {subject.name} added to enrollment")

            await self.db.commit()
            return selection

        else:
            # Remove subject (must be elective)
            selection_query = select(StudentSubjectSelection).where(
                and_(
                    StudentSubjectSelection.enrollment_id == enrollment_id,
                    StudentSubjectSelection.subject_id == subject_id,
                )
            )
            selection = await self.db.scalar(selection_query)

            if not selection:
                raise NotFoundError(f"Subject {subject.name} not currently selected")

            if selection.is_compulsory:
                raise ValidationError(
                    f"Cannot remove compulsory subject {subject.name}"
                )

            # Delete selection
            await self.db.delete(selection)
            await self.db.commit()

            logger.info(f"Subject {subject.name} removed from enrollment")
            return selection
