"""
CBC Report Card Service: Generate competency-based termly reports.

COMPLEX ALGORITHM:
generate_cbc_report(student_id, term_id, school_id, db):
1. Fetch all CbcRubricScore for student in term across all assessments
2. Group by Learning Area → Strands
3. For each Learning Area:
   - Collect all strand scores
   - Calculate Mode (most frequent score across strands)
   - Calculate Average
4. Format according to KICD guidelines
5. Return nested CbcReportCard response

KICD Format Requirements:
- Learning Area level aggregation
- Mode-based competency determination
- Clear level descriptions (Exceeding, Meeting, Approaching, Below)
- Teacher remarks collection
"""
import logging
from collections import Counter
from datetime import datetime
from statistics import mode, StatisticsError
from uuid import UUID, uuid4

from sqlalchemy import and_, func, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from src.core.exceptions import NotFoundError
from src.modules.academics.models.cbc import (
    CbcAssessment,
    CbcLearningArea,
    CbcRubricScore,
    CbcStrand,
)
from src.modules.academics.models.core import ClassLevel, Stream, StudentClassEnrollment, Term
from src.modules.academics.schemas.cbc import (
    CbcReportCard,
    LearningAreaPerformance,
    StrandPerformance,
)
from src.modules.students.models import Student

logger = logging.getLogger(__name__)

# Score level mapping
SCORE_LEVELS = {
    1: "Below Expectation",
    2: "Approaching Expectation",
    3: "Meeting Expectation",
    4: "Exceeding Expectation",
}


class ReportCardServiceCbc:
    """
    Service for generating CBC report cards with KICD-compliant formatting.

    Handles:
    - Fetching rubric scores
    - Grouping by learning area and strand
    - Computing mode (most frequent score)
    - Building nested response
    """

    def __init__(self, db: AsyncSession):
        """Initialize CBC report card service."""
        self.db = db

    async def generate_cbc_report(
        self,
        school_id: UUID,
        student_id: UUID,
        term_id: UUID,
    ) -> CbcReportCard:
        """
        Generate a CBC report card for a student in a term.

        REAL COMPLEX ALGORITHM:

        1. FETCH CONTEXT
           - Verify student exists
           - Verify term exists
           - Fetch student's enrollment for this term
           - Get class level and stream

        2. FETCH ALL ASSESSMENTS IN TERM
           - Query CbcAssessment WHERE term_id, is_active=True
           - Get assessment details (type, date, name)

        3. FETCH ALL RUBRIC SCORES
           - Query CbcRubricScore WHERE student_id + assessment_id in term
           - Join with Strand → LearningArea
           - Result: [(score, strand_id, strand_name, la_id, la_code, la_name), ...]

        4. GROUP BY LEARNING AREA
           - For each learning area:
             * Collect all strand records
             * For each strand:
               - Get all scores for that strand
               - Calculate mode (most frequent score)
               - Collect remarks
               - Create StrandPerformance

        5. CALCULATE LEARNING AREA AGGREGATES
           - mode_score = mode of all strand modes (or median if no clear mode)
           - average_score = mean of all strand scores
           - total_strands_assessed = count

        6. CALCULATE REPORT SUMMARY
           - Count LA where mode >= 3 (Meeting/Exceeding)
           - Count LA where mode == 2 (Approaching)
           - Count LA where mode == 1 (Below)

        7. BUILD RESPONSE
           - Return deeply nested CbcReportCard with all calculated fields
           - KICD-compliant format

        Args:
            school_id: School context
            student_id: Student ID
            term_id: Term ID

        Returns:
            CbcReportCard (complete report)

        Raises:
            NotFoundError: If student, term, or scores not found
        """
        logger.info(
            f"Generating CBC report: student={student_id}, term={term_id}, school={school_id}"
        )

        # ====================================================================
        # 1. FETCH CONTEXT
        # ====================================================================

        # Verify student exists
        student_query = select(Student).where(
            and_(
                Student.id == student_id,
                Student.school_id == school_id,
                Student.is_deleted == False,
            )
        )
        student = await self.db.scalar(student_query)

        if not student:
            raise NotFoundError(f"Student {student_id} not found")

        logger.debug(f"Student verified: {student.first_name} {student.last_name}")

        # Verify term exists
        term_query = select(Term).where(
            and_(
                Term.id == term_id,
                Term.school_id == school_id,
                Term.is_active == True,
            )
        ).options(selectinload(Term.academic_year))

        term = await self.db.scalar(term_query)

        if not term:
            raise NotFoundError(f"Term {term_id} not found or inactive")

        academic_year = term.academic_year
        logger.debug(f"Term verified: {term.name} ({academic_year.year})")

        # Fetch student's enrollment for this term
        enrollment_query = select(StudentClassEnrollment).where(
            and_(
                StudentClassEnrollment.student_id == student_id,
                StudentClassEnrollment.term_id == term_id,
                StudentClassEnrollment.school_id == school_id,
            )
        ).options(
            selectinload(StudentClassEnrollment.class_level),
            selectinload(StudentClassEnrollment.stream),
        )

        enrollment = await self.db.scalar(enrollment_query)

        if not enrollment:
            raise NotFoundError(f"Student not enrolled in this term")

        class_level = enrollment.class_level
        stream = enrollment.stream

        logger.debug(f"Enrollment verified: {class_level.name} {stream.name}")

        # ====================================================================
        # 2. FETCH ALL ASSESSMENTS IN TERM
        # ====================================================================

        assessments_query = select(CbcAssessment).where(
            and_(
                CbcAssessment.term_id == term_id,
                CbcAssessment.school_id == school_id,
                CbcAssessment.is_active == True,
            )
        ).order_by(CbcAssessment.assessment_date.desc())

        result = await self.db.execute(assessments_query)
        assessments = result.scalars().all()

        if not assessments:
            raise NotFoundError(f"No assessments found for term {term_id}")

        logger.debug(f"Found {len(assessments)} assessments")

        # ====================================================================
        # 3. FETCH ALL RUBRIC SCORES FOR STUDENT IN TERM
        # ====================================================================

        # Complex join to get: score, strand details, learning area details
        scores_query = select(
            CbcRubricScore.id,
            CbcRubricScore.score,
            CbcRubricScore.teacher_remarks,
            CbcRubricScore.assessment_id,
            CbcRubricScore.created_at,
            CbcStrand.id.label("strand_id"),
            CbcStrand.code.label("strand_code"),
            CbcStrand.name.label("strand_name"),
            CbcLearningArea.id.label("learning_area_id"),
            CbcLearningArea.code.label("learning_area_code"),
            CbcLearningArea.name.label("learning_area_name"),
        ).join(
            CbcRubricScore,
            CbcRubricScore.strand_id == CbcStrand.id,
        ).join(
            CbcAssessment,
            CbcRubricScore.assessment_id == CbcAssessment.id,
        ).join(
            CbcLearningArea,
            CbcStrand.learning_area_id == CbcLearningArea.id,
        ).where(
            and_(
                CbcRubricScore.student_id == student_id,
                CbcRubricScore.school_id == school_id,
                CbcAssessment.term_id == term_id,
            )
        ).order_by(
            CbcLearningArea.name,
            CbcStrand.name,
            CbcAssessment.assessment_date.desc(),
        )

        result = await self.db.execute(scores_query)
        score_rows = result.all()

        if not score_rows:
            raise NotFoundError(
                f"No rubric scores found for student {student_id} in term {term_id}"
            )

        logger.debug(f"Fetched {len(score_rows)} rubric score records")

        # ====================================================================
        # 4. GROUP BY LEARNING AREA → STRANDS
        # ====================================================================

        # Structure: {learning_area_id: {strand_id: [scores]}}
        learning_areas_dict = {}

        for row in score_rows:
            la_id = row.learning_area_id
            strand_id = row.strand_id
            score = row.score

            if la_id not in learning_areas_dict:
                learning_areas_dict[la_id] = {
                    "la_code": row.learning_area_code,
                    "la_name": row.learning_area_name,
                    "strands": {},
                }

            if strand_id not in learning_areas_dict[la_id]["strands"]:
                learning_areas_dict[la_id]["strands"][strand_id] = {
                    "strand_code": row.strand_code,
                    "strand_name": row.strand_name,
                    "scores": [],
                    "remarks": row.teacher_remarks or "",
                }

            learning_areas_dict[la_id]["strands"][strand_id]["scores"].append(score)

        logger.debug(f"Grouped into {len(learning_areas_dict)} learning areas")

        # ====================================================================
        # 5. CALCULATE AGGREGATES & BUILD RESPONSE DATA
        # ====================================================================

        learning_areas_list = []
        meeting_expectation_count = 0
        approaching_count = 0
        below_count = 0

        for la_id, la_data in learning_areas_dict.items():
            strands_list = []
            all_strand_scores = []

            for strand_id, strand_data in la_data["strands"].items():
                strand_scores = strand_data["scores"]
                all_strand_scores.extend(strand_scores)

                # Calculate mode for this strand
                try:
                    strand_mode = mode(strand_scores)
                except StatisticsError:
                    # If no clear mode, use median or mean
                    strand_mode = int(sum(strand_scores) / len(strand_scores))

                strand_perf = StrandPerformance(
                    strand_id=strand_id,
                    strand_code=strand_data["strand_code"],
                    strand_name=strand_data["strand_name"],
                    score=strand_mode,
                    score_level=SCORE_LEVELS[strand_mode],
                    teacher_remarks=strand_data["remarks"] if strand_data["remarks"] else None,
                )
                strands_list.append(strand_perf)

            # Calculate learning area mode (most common score across strands)
            try:
                la_mode = mode(all_strand_scores)
            except StatisticsError:
                # If no clear mode, use mean rounded
                la_mode = round(sum(all_strand_scores) / len(all_strand_scores))

            # Ensure mode is in valid range
            la_mode = max(1, min(4, la_mode))

            # Calculate average
            la_average = sum(all_strand_scores) / len(all_strand_scores)

            # Update summary counts
            if la_mode >= 3:
                meeting_expectation_count += 1
            elif la_mode == 2:
                approaching_count += 1
            else:
                below_count += 1

            la_perf = LearningAreaPerformance(
                learning_area_id=la_id,
                learning_area_code=la_data["la_code"],
                learning_area_name=la_data["la_name"],
                strands=strands_list,
                mode_score=la_mode,
                mode_level=SCORE_LEVELS[la_mode],
                average_score=round(la_average, 2),
                total_strands_assessed=len(strands_list),
            )
            learning_areas_list.append(la_perf)

        # Sort by learning area name
        learning_areas_list.sort(key=lambda x: x.learning_area_name)

        logger.debug(
            f"Aggregates: meeting={meeting_expectation_count}, "
            f"approaching={approaching_count}, below={below_count}"
        )

        # ====================================================================
        # 6. DETERMINE ASSESSMENT DETAILS
        # ====================================================================

        # Use most recent assessment in term
        latest_assessment = assessments[0]
        assessment_type = latest_assessment.assessment_type
        assessment_name = latest_assessment.name
        assessment_date = latest_assessment.assessment_date.isoformat()

        # ====================================================================
        # 7. BUILD RESPONSE
        # ====================================================================

        report_card = CbcReportCard(
            report_id=str(uuid4()),
            student_id=student_id,
            student_name=f"{student.first_name} {student.last_name}",
            student_admission_number=student.admission_number,
            term_id=term_id,
            term_name=term.name,
            term_number=term.term_number,
            academic_year=academic_year.year,
            assessment_type=assessment_type,
            assessment_name=assessment_name,
            assessment_date=assessment_date,
            class_level_name=class_level.name,
            stream_name=stream.name,
            learning_areas=learning_areas_list,
            total_learning_areas=len(learning_areas_list),
            learning_areas_meeting_expectation=meeting_expectation_count,
            learning_areas_approaching=approaching_count,
            learning_areas_below=below_count,
            generated_at=datetime.now().isoformat(),
        )

        logger.info(
            f"CBC report generated: {report_card.student_name} "
            f"({report_card.stream_name}), "
            f"{meeting_expectation_count} LA meeting expectation"
        )

        return report_card

    async def get_learning_area_performance_summary(
        self,
        school_id: UUID,
        term_id: UUID,
    ) -> dict:
        """
        Get summary of learning area performance for entire class/school.

        Used for analytics and trend tracking.

        Args:
            school_id: School context
            term_id: Term ID

        Returns:
            Dictionary with:
            - total_students_assessed
            - learning_areas
            - average_mode_by_la
            - percentage_meeting_expectation
        """
        # Count unique students assessed
        students_query = select(func.count(func.distinct(CbcRubricScore.student_id))).join(
            CbcAssessment,
            CbcRubricScore.assessment_id == CbcAssessment.id,
        ).where(
            and_(
                CbcRubricScore.school_id == school_id,
                CbcAssessment.term_id == term_id,
            )
        )

        total_students = await self.db.scalar(students_query) or 0

        # Average score per learning area
        la_avg_query = select(
            CbcLearningArea.name,
            func.avg(CbcRubricScore.score).label("avg_score"),
        ).join(
            CbcStrand,
            CbcRubricScore.strand_id == CbcStrand.id,
        ).join(
            CbcLearningArea,
            CbcStrand.learning_area_id == CbcLearningArea.id,
        ).join(
            CbcAssessment,
            CbcRubricScore.assessment_id == CbcAssessment.id,
        ).where(
            and_(
                CbcRubricScore.school_id == school_id,
                CbcAssessment.term_id == term_id,
            )
        ).group_by(CbcLearningArea.name).order_by(CbcLearningArea.name)

        result = await self.db.execute(la_avg_query)
        la_performance = {row[0]: float(round(row[1], 2)) for row in result}

        return {
            "total_students_assessed": total_students,
            "learning_area_performance": la_performance,
            "generated_at": datetime.now().isoformat(),
        }
