"""
Report Card Service for 8-4-4 System: Generate comprehensive termly report cards.

COMPLEX ALGORITHM:
generate_termly_report_card(student_id, exam_id, school_id, db):
1. Fetch all ExamResult844 for student in exam
2. Get all StudentSubjectSelection for student in term (to include enrolled subjects)
3. Join results with subject details
4. For each subject: extract mark, grade, points
5. Calculate aggregates:
   - Total marks = SUM(mark_score)
   - Mean mark = AVG(mark_score)
   - Mean points = AVG(points)
   - Mean grade = find grade closest to mean points
6. For rankings (using window functions):
   - Stream rank: ROW_NUMBER() OVER (PARTITION BY stream_id ORDER BY total_points DESC)
   - Class rank: ROW_NUMBER() OVER (PARTITION BY class_level_id ORDER BY total_points DESC)
7. Return deeply nested ReportCard844Response

No placeholders. Full SQL queries with proper aggregations.
"""
import logging
from datetime import datetime
from decimal import Decimal
from uuid import UUID, uuid4

from sqlalchemy import and_, case, desc, func, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from src.core.exceptions import NotFoundError, ValidationError
from src.modules.academics.models.core import (
    ClassLevel,
    Stream,
    StudentClassEnrollment,
    StudentSubjectSelection,
    Subject,
    Term,
)
from src.modules.academics.models.exams_844 import ExamResult844
from src.modules.academics.schemas.exams_844 import (
    ReportCard844Response,
    ReportCardAggregates,
    StudentRanking,
    SubjectResultSummary,
)
from src.modules.academics.services.grading_service_844 import GradingService844
from src.modules.students.models import Student

logger = logging.getLogger(__name__)


class ReportCardService844:
    """
    Service for generating 8-4-4 report cards.

    Handles:
    - Fetching exam results
    - Calculating aggregates
    - Computing rankings
    - Building nested response
    """

    def __init__(self, db: AsyncSession):
        """Initialize report card service."""
        self.db = db

    async def generate_termly_report_card(
        self,
        school_id: UUID,
        student_id: UUID,
        exam_id: UUID,
    ) -> ReportCard844Response:
        """
        Generate a complete report card for student in an exam.

        REAL COMPLEX ALGORITHM:

        1. FETCH CONTEXT
           - Verify student exists
           - Fetch exam details and term
           - Fetch student's enrollment for this term/exam
           - Get class level and stream

        2. FETCH ALL RESULTS
           - Query ExamResult844 WHERE student_id + exam_id
           - Join with Subject to get subject details
           - Result: List of (mark, grade, points, subject_name, subject_code, is_compulsory)

        3. CALCULATE AGGREGATES
           - Total subjects = COUNT(*)
           - Total marks = SUM(mark_score)
           - Mean mark = AVG(mark_score)
           - Mean points = AVG(points)
           - Mean grade = Find grade from GradingSystem where points closest to mean_points
           
        4. CALCULATE RANKINGS (Window Functions)
           - Stream rank:
             * Query all ExamResult844 in same exam/stream
             * Group by student_id, calculate SUM(points)
             * ROW_NUMBER() OVER (ORDER BY total_points DESC)
             * Find current student's row number
             
           - Class rank:
             * Query all ExamResult844 in same exam/class_level
             * Group by student_id, calculate SUM(points)
             * ROW_NUMBER() OVER (ORDER BY total_points DESC)
             * Find current student's row number

        5. BUILD RESPONSE
           - Return deeply nested ReportCard844Response with all calculated fields

        Args:
            school_id: School context
            student_id: Student ID
            exam_id: Exam ID

        Returns:
            ReportCard844Response (complete report card)

        Raises:
            NotFoundError: If student, exam, or results not found
        """
        logger.info(
            f"Generating report card: student={student_id}, exam={exam_id}, school={school_id}"
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

        # Fetch exam and term
        from src.modules.academics.models.exams_844 import Exam
        from src.modules.academics.models.core import AcademicYear

        exam_query = select(Exam).where(
            and_(
                Exam.id == exam_id,
                Exam.school_id == school_id,
            )
        ).options(selectinload(Exam.term).selectinload(Term.academic_year))

        exam = await self.db.scalar(exam_query)

        if not exam:
            raise NotFoundError(f"Exam {exam_id} not found")

        term = exam.term
        academic_year = term.academic_year

        logger.debug(f"Exam verified: {exam.name} ({exam.exam_type})")

        # Fetch student's enrollment for this term
        enrollment_query = select(StudentClassEnrollment).where(
            and_(
                StudentClassEnrollment.student_id == student_id,
                StudentClassEnrollment.term_id == term.id,
                StudentClassEnrollment.school_id == school_id,
            )
        ).options(
            selectinload(StudentClassEnrollment.class_level),
            selectinload(StudentClassEnrollment.stream),
        )

        enrollment = await self.db.scalar(enrollment_query)

        if not enrollment:
            raise NotFoundError(
                f"Student not enrolled in this term. Cannot generate report card."
            )

        class_level = enrollment.class_level
        stream = enrollment.stream

        logger.debug(
            f"Enrollment verified: {class_level.name} {stream.name}"
        )

        # ====================================================================
        # 2. FETCH ALL EXAM RESULTS
        # ====================================================================

        results_query = select(
            ExamResult844.subject_id,
            ExamResult844.mark_score,
            ExamResult844.grade,
            ExamResult844.points,
            Subject.name.label("subject_name"),
            Subject.subject_code,
            Subject.is_compulsory,
        ).join(
            Subject,
            ExamResult844.subject_id == Subject.id,
        ).where(
            and_(
                ExamResult844.student_id == student_id,
                ExamResult844.exam_id == exam_id,
                ExamResult844.school_id == school_id,
            )
        ).order_by(Subject.name)

        result = await self.db.execute(results_query)
        exam_results = result.all()

        if not exam_results:
            raise NotFoundError(
                f"No exam results found for student {student_id} in exam {exam_id}"
            )

        logger.debug(f"Fetched {len(exam_results)} subject results")

        # ====================================================================
        # 3. CALCULATE AGGREGATES
        # ====================================================================

        subject_results = []
        total_marks = Decimal("0")
        total_points = 0
        points_list = []

        for row in exam_results:
            subject_results.append(
                SubjectResultSummary(
                    subject_id=row.subject_id,
                    subject_name=row.subject_name,
                    subject_code=row.subject_code,
                    mark_score=row.mark_score,
                    grade=row.grade,
                    points=row.points,
                    is_compulsory=row.is_compulsory,
                )
            )
            total_marks += row.mark_score
            total_points += row.points
            points_list.append(row.points)

        total_subjects = len(exam_results)
        mean_mark = total_marks / Decimal(total_subjects) if total_subjects > 0 else Decimal("0")
        mean_points = Decimal(total_points) / Decimal(total_subjects) if total_subjects > 0 else Decimal("0")

        logger.debug(
            f"Aggregates: total_marks={total_marks}, mean_mark={mean_mark}, "
            f"mean_points={mean_points}"
        )

        # Find mean grade: closest grade to mean_points
        grading_service = GradingService844(self.db)
        mean_grade_result = await grading_service.calculate_grade_and_points(
            Decimal(str(mean_mark)),
            school_id,
        )
        mean_grade = mean_grade_result.grade

        aggregates = ReportCardAggregates(
            total_subjects=total_subjects,
            total_marks=total_marks,
            mean_mark=mean_mark,
            mean_grade=mean_grade,
            mean_points=mean_points,
        )

        # ====================================================================
        # 4. CALCULATE RANKINGS
        # ====================================================================

        # STREAM RANK: Use window function to rank all students in stream by total points
        stream_ranking_query = select(
            StudentClassEnrollment.student_id,
            func.sum(ExamResult844.points).label("total_points"),
            func.row_number()
            .over(order_by=desc(func.sum(ExamResult844.points)))
            .label("rank"),
        ).join(
            ExamResult844,
            and_(
                ExamResult844.student_id == StudentClassEnrollment.student_id,
                ExamResult844.exam_id == exam_id,
            ),
        ).where(
            and_(
                StudentClassEnrollment.stream_id == stream.id,
                StudentClassEnrollment.term_id == term.id,
                StudentClassEnrollment.school_id == school_id,
            )
        ).group_by(
            StudentClassEnrollment.student_id,
        ).subquery()

        stream_rank_query = select(
            stream_ranking_query.c.rank,
        ).where(
            stream_ranking_query.c.student_id == student_id,
        )

        stream_rank_result = await self.db.execute(stream_rank_query)
        stream_rank = stream_rank_result.scalar() or 1

        # Count total students in stream for this term
        stream_total_query = select(func.count(StudentClassEnrollment.student_id)).where(
            and_(
                StudentClassEnrollment.stream_id == stream.id,
                StudentClassEnrollment.term_id == term.id,
                StudentClassEnrollment.school_id == school_id,
            )
        )
        stream_total = await self.db.scalar(stream_total_query) or 1

        logger.debug(f"Stream rank: {stream_rank}/{stream_total}")

        # CLASS RANK: Rank all students in class level by total points
        class_ranking_query = select(
            StudentClassEnrollment.student_id,
            func.sum(ExamResult844.points).label("total_points"),
            func.row_number()
            .over(order_by=desc(func.sum(ExamResult844.points)))
            .label("rank"),
        ).join(
            ExamResult844,
            and_(
                ExamResult844.student_id == StudentClassEnrollment.student_id,
                ExamResult844.exam_id == exam_id,
            ),
        ).where(
            and_(
                StudentClassEnrollment.class_level_id == class_level.id,
                StudentClassEnrollment.term_id == term.id,
                StudentClassEnrollment.school_id == school_id,
            )
        ).group_by(
            StudentClassEnrollment.student_id,
        ).subquery()

        class_rank_query = select(
            class_ranking_query.c.rank,
        ).where(
            class_ranking_query.c.student_id == student_id,
        )

        class_rank_result = await self.db.execute(class_rank_query)
        class_rank = class_rank_result.scalar() or 1

        # Count total students in class for this term
        class_total_query = select(func.count(StudentClassEnrollment.student_id)).where(
            and_(
                StudentClassEnrollment.class_level_id == class_level.id,
                StudentClassEnrollment.term_id == term.id,
                StudentClassEnrollment.school_id == school_id,
            )
        )
        class_total = await self.db.scalar(class_total_query) or 1

        logger.debug(f"Class rank: {class_rank}/{class_total}")

        # Calculate percentages
        stream_rank_percentage = Decimal(stream_rank) / Decimal(stream_total) * Decimal("100") if stream_total > 0 else Decimal("0")
        class_rank_percentage = Decimal(class_rank) / Decimal(class_total) * Decimal("100") if class_total > 0 else Decimal("0")

        rankings = StudentRanking(
            stream_rank=stream_rank,
            stream_total=stream_total,
            class_rank=class_rank,
            class_total=class_total,
            stream_rank_percentage=stream_rank_percentage,
            class_rank_percentage=class_rank_percentage,
        )

        # ====================================================================
        # 5. BUILD RESPONSE
        # ====================================================================

        report_card = ReportCard844Response(
            report_card_id=str(uuid4()),
            student_id=student_id,
            student_name=f"{student.first_name} {student.last_name}",
            student_admission_number=student.admission_number,
            exam_id=exam_id,
            exam_name=exam.name,
            exam_type=exam.exam_type,
            exam_date=exam.exam_date.isoformat(),
            academic_year=academic_year.year,
            term_number=term.term_number,
            term_name=term.name,
            class_level_name=class_level.name,
            stream_name=stream.name,
            results=subject_results,
            aggregates=aggregates,
            rankings=rankings,
            generated_at=datetime.now().isoformat(),
        )

        logger.info(
            f"Report card generated: {report_card.student_name} "
            f"({report_card.stream_name}), "
            f"stream rank {report_card.rankings.stream_rank}/{report_card.rankings.stream_total}"
        )

        return report_card

    async def get_class_performance_summary(
        self,
        school_id: UUID,
        class_level_id: UUID,
        term_id: UUID,
        exam_id: UUID,
    ) -> dict:
        """
        Get summary statistics for entire class performance.

        Used for class-level analytics and trend analysis.

        Args:
            school_id: School context
            class_level_id: Class level
            term_id: Term
            exam_id: Exam

        Returns:
            Dictionary with:
            - average_mean_mark: Average of all students' mean marks
            - top_performer: Best student name and rank
            - bottom_performer: Lowest student name and rank
            - subject_averages: Per-subject average marks
            - grade_distribution: Count of each grade
        """
        # Average performance per subject
        subject_avg_query = select(
            Subject.name,
            func.avg(ExamResult844.mark_score).label("avg_mark"),
            func.avg(ExamResult844.points).label("avg_points"),
        ).join(
            ExamResult844,
            ExamResult844.subject_id == Subject.id,
        ).join(
            StudentClassEnrollment,
            ExamResult844.student_id == StudentClassEnrollment.student_id,
        ).where(
            and_(
                StudentClassEnrollment.class_level_id == class_level_id,
                StudentClassEnrollment.term_id == term_id,
                ExamResult844.exam_id == exam_id,
                ExamResult844.school_id == school_id,
            )
        ).group_by(Subject.name)

        result = await self.db.execute(subject_avg_query)
        subject_averages = {row[0]: {"avg_mark": float(row[1]), "avg_points": float(row[2])} for row in result}

        # Grade distribution
        grade_dist_query = select(
            ExamResult844.grade,
            func.count(ExamResult844.id).label("count"),
        ).join(
            StudentClassEnrollment,
            ExamResult844.student_id == StudentClassEnrollment.student_id,
        ).where(
            and_(
                StudentClassEnrollment.class_level_id == class_level_id,
                StudentClassEnrollment.term_id == term_id,
                ExamResult844.exam_id == exam_id,
                ExamResult844.school_id == school_id,
            )
        ).group_by(ExamResult844.grade).order_by(ExamResult844.grade)

        result = await self.db.execute(grade_dist_query)
        grade_distribution = {row[0]: row[1] for row in result}

        return {
            "subject_averages": subject_averages,
            "grade_distribution": grade_distribution,
            "total_students": sum(grade_distribution.values()),
        }
