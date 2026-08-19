"""
Grading Service for 8-4-4 System: Convert marks to grades and points.

CRITICAL ALGORITHM:
1. Take raw mark (0-100)
2. Query school's GradingSystem table
3. Find row where min_mark <= mark <= max_mark
4. Return grade and points
5. Fall back to Kenyan standard if no custom grading defined

Kenyan Standard (8-4-4):
A (12): 80-100
A- (11): 75-79
B+ (10): 70-74
B (9): 65-69
B- (8): 60-64
C (7): 50-59
D (6): 40-49
D- (5): 30-39
E (4): 20-29
F (1): 0-19
"""
import logging
from decimal import Decimal
from typing import NamedTuple
from uuid import UUID

from sqlalchemy import and_, select
from sqlalchemy.ext.asyncio import AsyncSession

from src.core.exceptions import ValidationError
from src.modules.academics.models.exams_844 import GradingSystem

logger = logging.getLogger(__name__)


class GradeResult(NamedTuple):
    """Result of grade calculation."""

    grade: str
    points: int


class GradingService844:
    """
    Service for grade and point calculation in 8-4-4 system.

    ALGORITHM:
    calculate_grade_and_points(mark, school_id, db):
        1. Validate mark is between 0-100
        2. Query GradingSystem table for school_id
        3. If empty: use KENYAN_STANDARD
        4. Find row where min_mark <= mark <= max_mark
        5. Return GradeResult(grade, points)
    """

    # Kenyan Standard Grading Scale for 8-4-4
    KENYAN_STANDARD = [
        {"min_mark": Decimal("80"), "max_mark": Decimal("100"), "grade": "A", "points": 12},
        {"min_mark": Decimal("75"), "max_mark": Decimal("79"), "grade": "A-", "points": 11},
        {"min_mark": Decimal("70"), "max_mark": Decimal("74"), "grade": "B+", "points": 10},
        {"min_mark": Decimal("65"), "max_mark": Decimal("69"), "grade": "B", "points": 9},
        {"min_mark": Decimal("60"), "max_mark": Decimal("64"), "grade": "B-", "points": 8},
        {"min_mark": Decimal("50"), "max_mark": Decimal("59"), "grade": "C", "points": 7},
        {"min_mark": Decimal("40"), "max_mark": Decimal("49"), "grade": "D", "points": 6},
        {"min_mark": Decimal("30"), "max_mark": Decimal("39"), "grade": "D-", "points": 5},
        {"min_mark": Decimal("20"), "max_mark": Decimal("29"), "grade": "E", "points": 4},
        {"min_mark": Decimal("0"), "max_mark": Decimal("19"), "grade": "F", "points": 1},
    ]

    def __init__(self, db: AsyncSession):
        """Initialize grading service."""
        self.db = db

    async def calculate_grade_and_points(
        self,
        mark: Decimal,
        school_id: UUID,
    ) -> GradeResult:
        """
        Calculate grade and points for a raw mark.

        REAL ALGORITHM:
        1. Validate mark (0-100)
        2. Query school's custom GradingSystem entries
        3. If none exist: use KENYAN_STANDARD fallback
        4. Find matching row: min_mark <= mark <= max_mark
        5. Return grade and points

        Args:
            mark: Raw mark (0-100)
            school_id: School context

        Returns:
            GradeResult(grade, points)

        Raises:
            ValidationError: If mark invalid or no matching grade found
        """
        # 1. Validate mark
        mark = Decimal(str(mark))  # Ensure it's Decimal

        if mark < 0 or mark > 100:
            raise ValidationError(f"Mark {mark} is out of range (0-100)")

        logger.debug(f"Calculating grade for mark {mark} (school {school_id})")

        # 2. Query school's custom grading system
        grading_query = select(GradingSystem).where(
            GradingSystem.school_id == school_id,
        ).order_by(GradingSystem.min_mark.desc())

        result = await self.db.execute(grading_query)
        custom_grades = result.scalars().all()

        # 3. Use custom grading system if available, otherwise use standard
        grading_scale = [
            {
                "min_mark": g.min_mark,
                "max_mark": g.max_mark,
                "grade": g.grade,
                "points": g.points,
            }
            for g in custom_grades
        ]

        if not grading_scale:
            logger.debug(f"No custom grading system for school {school_id}, using Kenyan standard")
            grading_scale = self.KENYAN_STANDARD

        # 4. Find matching grade entry: min_mark <= mark <= max_mark
        for grade_entry in grading_scale:
            if grade_entry["min_mark"] <= mark <= grade_entry["max_mark"]:
                result_grade = GradeResult(
                    grade=grade_entry["grade"],
                    points=grade_entry["points"],
                )

                logger.debug(
                    f"Mark {mark} → Grade {result_grade.grade} "
                    f"({result_grade.points} points)"
                )

                return result_grade

        # 5. Should never reach here if grading system is properly configured
        logger.error(f"No matching grade found for mark {mark}")
        raise ValidationError(
            f"No matching grade found for mark {mark}. "
            f"Grading system may be misconfigured."
        )

    async def initialize_school_grading_system(
        self,
        school_id: UUID,
    ) -> int:
        """
        Initialize school's grading system with Kenyan standard if not already set.

        Useful for onboarding new schools.

        Args:
            school_id: School to initialize

        Returns:
            Number of grading entries created

        Raises:
            ValidationError: If school already has grading system
        """
        # Check if school already has grading entries
        check_query = select(GradingSystem).where(
            GradingSystem.school_id == school_id,
        )

        existing = await self.db.scalar(check_query)

        if existing:
            raise ValidationError(
                f"School {school_id} already has a grading system configured"
            )

        logger.info(f"Initializing grading system for school {school_id}")

        # Create entries from Kenyan standard
        count = 0
        for grade_entry in self.KENYAN_STANDARD:
            grading = GradingSystem(
                school_id=school_id,
                min_mark=grade_entry["min_mark"],
                max_mark=grade_entry["max_mark"],
                grade=grade_entry["grade"],
                points=grade_entry["points"],
                description=f"{grade_entry['grade']} Grade: {grade_entry['min_mark']}-{grade_entry['max_mark']} marks ({grade_entry['points']} points)",
            )
            self.db.add(grading)
            count += 1

        await self.db.commit()

        logger.info(f"Grading system initialized: {count} entries created for school {school_id}")
        return count

    async def get_grading_system(
        self,
        school_id: UUID,
    ) -> list[dict]:
        """
        Get all grading entries for a school.

        Args:
            school_id: School context

        Returns:
            List of grading entries ordered by mark range
        """
        query = select(GradingSystem).where(
            GradingSystem.school_id == school_id,
        ).order_by(GradingSystem.min_mark.desc())

        result = await self.db.execute(query)
        entries = result.scalars().all()

        if not entries:
            logger.debug(f"No custom grading system for school {school_id}")
            return [
                {
                    "min_mark": float(e["min_mark"]),
                    "max_mark": float(e["max_mark"]),
                    "grade": e["grade"],
                    "points": e["points"],
                }
                for e in self.KENYAN_STANDARD
            ]

        return [
            {
                "id": str(e.id),
                "min_mark": float(e.min_mark),
                "max_mark": float(e.max_mark),
                "grade": e.grade,
                "points": e.points,
                "description": e.description,
            }
            for e in entries
        ]

    async def validate_grading_entry(
        self,
        min_mark: Decimal,
        max_mark: Decimal,
        points: int,
    ) -> bool:
        """
        Validate a grading entry for consistency.

        Args:
            min_mark: Minimum mark
            max_mark: Maximum mark
            points: Points value

        Returns:
            True if valid, raises ValidationError otherwise
        """
        if min_mark < 0 or max_mark > 100:
            raise ValidationError("Marks must be between 0 and 100")

        if min_mark > max_mark:
            raise ValidationError("min_mark must be <= max_mark")

        if points < 1 or points > 12:
            raise ValidationError("Points must be between 1 and 12")

        return True
