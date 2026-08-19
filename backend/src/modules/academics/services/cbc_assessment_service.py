"""
CBC Assessment Service: Record and validate rubric scores.

CRITICAL VALIDATION:
- Score must be strictly an integer (not float, not string)
- Score must be between 1 and 4 inclusive
- Unique constraint: one score per student per strand per assessment
- Supports idempotency: update if duplicate, create if new

Scoring Rubric (KICD Standard):
- 4: Exceeding Expectation (E)
- 3: Meeting Expectation (M)
- 2: Approaching Expectation (A)
- 1: Below Expectation (B)
"""
import logging
from uuid import UUID

from sqlalchemy import and_, select
from sqlalchemy.ext.asyncio import AsyncSession

from src.core.exceptions import NotFoundError, ValidationError
from src.modules.academics.models.cbc import CbcAssessment, CbcRubricScore, CbcStrand
from src.modules.students.models import Student

logger = logging.getLogger(__name__)

# Score level mapping
SCORE_LEVELS = {
    1: "Below Expectation",
    2: "Approaching Expectation",
    3: "Meeting Expectation",
    4: "Exceeding Expectation",
}

SCORE_CODES = {
    1: "B",
    2: "A",
    3: "M",
    4: "E",
}


class CbcAssessmentService:
    """
    Service for recording and managing CBC rubric scores.

    CRITICAL ALGORITHM for record_strand_score():
    1. Validate score is strictly integer (not float/string)
    2. Validate score is in range [1, 4]
    3. Verify student exists
    4. Verify assessment exists
    5. Verify strand exists
    6. Check for existing score (idempotent update)
    7. Create or update score
    8. Commit atomically
    """

    def __init__(self, db: AsyncSession):
        """Initialize assessment service."""
        self.db = db

    async def record_strand_score(
        self,
        school_id: UUID,
        student_id: UUID,
        assessment_id: UUID,
        strand_id: UUID,
        score: int,
        teacher_remarks: str = None,
    ) -> CbcRubricScore:
        """
        Record a rubric score for a student on a strand.

        REAL VALIDATION & ALGORITHM:
        1. Validate score type and range
           - Must be int, not float/string/None
           - Must be 1, 2, 3, or 4 (STRICTLY)
           - Reject: 1.5, "2", 0, 5, etc.
        2. Verify entities exist
           - Student: must be active
           - Assessment: must exist
           - Strand: must exist
        3. Idempotent operation
           - Check if score already exists (unique constraint)
           - If exists: UPDATE with new score & remarks
           - If not: CREATE new entry
        4. Commit atomically

        Args:
            school_id: School context
            student_id: Student ID
            assessment_id: Assessment ID
            strand_id: Strand ID
            score: Rubric score (1, 2, 3, or 4) - MUST BE INT
            teacher_remarks: Optional teacher notes

        Returns:
            CbcRubricScore (created or updated)

        Raises:
            ValidationError: If score invalid or outside [1, 4]
            NotFoundError: If student, assessment, or strand not found
        """
        logger.info(
            f"Recording rubric score: student={student_id}, strand={strand_id}, "
            f"assessment={assessment_id}, score={score}"
        )

        # 1. VALIDATE SCORE - STRICT TYPE & RANGE CHECKING
        # This is CRITICAL: must reject floats, strings, None, and out-of-range values
        
        if not isinstance(score, int) or isinstance(score, bool):
            # Note: bool is subclass of int in Python, so explicitly reject
            raise ValidationError(
                f"Score must be an integer, got {type(score).__name__}: {score}"
            )

        if score < 1 or score > 4:
            raise ValidationError(
                f"Score must be between 1 and 4, got {score}. "
                f"Valid values: 1=Below Expectation, 2=Approaching, 3=Meeting, 4=Exceeding"
            )

        logger.debug(f"Score validated: {score} ({SCORE_LEVELS[score]})")

        # 2. VERIFY STUDENT EXISTS & IS ACTIVE
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
            raise ValidationError(
                f"Student {student.first_name} {student.last_name} is not active"
            )

        logger.debug(f"Student verified: {student.first_name} {student.last_name}")

        # 3. VERIFY ASSESSMENT EXISTS & IS ACTIVE
        assessment_query = select(CbcAssessment).where(
            and_(
                CbcAssessment.id == assessment_id,
                CbcAssessment.school_id == school_id,
                CbcAssessment.is_active == True,
            )
        )
        assessment = await self.db.scalar(assessment_query)

        if not assessment:
            raise NotFoundError(f"Assessment {assessment_id} not found or inactive")

        logger.debug(f"Assessment verified: {assessment.name} ({assessment.assessment_type})")

        # 4. VERIFY STRAND EXISTS & IS ACTIVE
        strand_query = select(CbcStrand).where(
            and_(
                CbcStrand.id == strand_id,
                CbcStrand.school_id == school_id,
                CbcStrand.is_active == True,
            )
        )
        strand = await self.db.scalar(strand_query)

        if not strand:
            raise NotFoundError(f"Strand {strand_id} not found or inactive")

        logger.debug(f"Strand verified: {strand.name}")

        # 5. CHECK FOR EXISTING SCORE (IDEMPOTENT)
        existing_query = select(CbcRubricScore).where(
            and_(
                CbcRubricScore.school_id == school_id,
                CbcRubricScore.student_id == student_id,
                CbcRubricScore.assessment_id == assessment_id,
                CbcRubricScore.strand_id == strand_id,
            )
        )
        existing_score = await self.db.scalar(existing_query)

        if existing_score:
            # 5a. UPDATE existing score
            existing_score.score = score
            if teacher_remarks:
                existing_score.teacher_remarks = teacher_remarks
            
            logger.info(
                f"Rubric score updated: {student.admission_number} on "
                f"{strand.name} = {score} ({SCORE_LEVELS[score]})"
            )

            await self.db.commit()
            return existing_score

        else:
            # 5b. CREATE new score
            rubric_score = CbcRubricScore(
                school_id=school_id,
                student_id=student_id,
                assessment_id=assessment_id,
                strand_id=strand_id,
                score=score,
                teacher_remarks=teacher_remarks or "",
                is_validated=False,
            )
            self.db.add(rubric_score)

            logger.info(
                f"Rubric score created: {student.admission_number} on "
                f"{strand.name} = {score} ({SCORE_LEVELS[score]})"
            )

            await self.db.commit()
            return rubric_score

    async def get_student_strand_scores(
        self,
        school_id: UUID,
        student_id: UUID,
        assessment_id: UUID,
    ) -> list[CbcRubricScore]:
        """
        Get all strand scores for a student in an assessment.

        Args:
            school_id: School context
            student_id: Student ID
            assessment_id: Assessment ID

        Returns:
            List of CbcRubricScore
        """
        query = select(CbcRubricScore).where(
            and_(
                CbcRubricScore.school_id == school_id,
                CbcRubricScore.student_id == student_id,
                CbcRubricScore.assessment_id == assessment_id,
            )
        ).order_by(CbcRubricScore.created_at)

        result = await self.db.execute(query)
        return result.scalars().all()

    async def get_strand_scores_by_assessment(
        self,
        school_id: UUID,
        assessment_id: UUID,
        strand_id: UUID = None,
    ) -> list[CbcRubricScore]:
        """
        Get all rubric scores for an assessment (optionally filtered by strand).

        Args:
            school_id: School context
            assessment_id: Assessment ID
            strand_id: Optional strand filter

        Returns:
            List of CbcRubricScore
        """
        query = select(CbcRubricScore).where(
            and_(
                CbcRubricScore.school_id == school_id,
                CbcRubricScore.assessment_id == assessment_id,
            )
        )

        if strand_id:
            query = query.where(CbcRubricScore.strand_id == strand_id)

        query = query.order_by(
            CbcRubricScore.strand_id,
            CbcRubricScore.student_id,
        )

        result = await self.db.execute(query)
        return result.scalars().all()

    @staticmethod
    def get_score_level(score: int) -> str:
        """
        Get textual representation of score.

        Args:
            score: Score value (1-4)

        Returns:
            Level description
        """
        return SCORE_LEVELS.get(score, "Unknown")

    @staticmethod
    def get_score_code(score: int) -> str:
        """
        Get letter code of score (B, A, M, E).

        Args:
            score: Score value (1-4)

        Returns:
            Single letter code
        """
        return SCORE_CODES.get(score, "?")
