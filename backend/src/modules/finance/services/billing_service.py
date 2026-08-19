"""
Billing Service: Generates invoices for a term.
Handles the termly billing run: loops through active students and creates invoices.
"""
import secrets
from datetime import date, datetime, timezone
from decimal import Decimal
from uuid import UUID

from sqlalchemy import and_, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from src.modules.finance.models.fees import (
    FeeInvoice,
    FeeInvoiceItem,
    FeeInvoiceStatusEnum,
    FeeStructure,
)
from src.modules.finance.repositories.fees_repo import (
    FeeInvoiceRepository,
    FeeStructureRepository,
)
from src.modules.academic.models import Term
from src.modules.students.models import Student
from src.shared.exceptions import ValidationError, NotFoundError


class BillingService:
    """
    Service for termly billing operations.
    Generates invoices for all active students in a term.
    """

    def __init__(self, db: AsyncSession):
        self.db = db
        self.invoice_repo = FeeInvoiceRepository(db)
        self.fee_structure_repo = FeeStructureRepository(db)

    async def run_termly_billing(
        self, school_id: UUID, academic_year_id: UUID, term_id: UUID, created_by_id: UUID
    ) -> dict:
        """
        Run termly billing: generate invoices for all active students.

        Process:
        1. Fetch term to validate it exists
        2. Fetch all active students in the school
        3. For each student:
           - Determine boarding type (DAY/BOARDING from student.boarding_status)
           - Determine curriculum type (8-4-4/CBC from student.curriculum_type)
           - Find matching FeeStructure
           - Create FeeInvoice if not already exists
           - Create FeeInvoiceItems for each structure item

        Args:
            school_id: School context
            academic_year_id: Academic year for billing
            term_id: Term for billing
            created_by_id: User running billing

        Returns:
            Dict with: invoices_created, students_processed, total_billed, errors

        Raises:
            ValidationError: If term not found or invalid
        """
        # 1. Validate term exists
        term_query = select(Term).where(
            and_(
                Term.id == term_id,
                Term.academic_year_id == academic_year_id,
            )
        )
        term_result = await self.db.execute(term_query)
        term = term_result.scalar_one_or_none()

        if not term:
            raise NotFoundError(f"Term {term_id} not found in academic year {academic_year_id}")

        # 2. Fetch all active students in school
        students_query = (
            select(Student)
            .where(
                and_(
                    Student.school_id == school_id,
                    Student.is_active == True,
                    Student.is_deleted == False,
                )
            )
        )
        students_result = await self.db.execute(students_query)
        students = students_result.scalars().all()

        if not students:
            return {
                "invoices_created": 0,
                "students_processed": 0,
                "total_billed": Decimal("0.0000"),
                "errors": [],
                "timestamp": datetime.now(timezone.utc),
            }

        # 3. Process each student
        invoices_created = 0
        total_billed = Decimal("0.0000")
        errors = []

        for student in students:
            try:
                # Check if invoice already exists for this term
                existing = await self.invoice_repo.get_for_student_term(student.id, term_id)
                if existing:
                    continue  # Skip if already billed

                # Determine boarding type
                boarding_type = student.boarding_status if student.boarding_status else "DAY"

                # Determine curriculum type
                curriculum_type = student.curriculum_type if student.curriculum_type else "8-4-4"

                # Find matching FeeStructure
                fee_structure = await self.fee_structure_repo.get_for_term(
                    school_id,
                    academic_year_id,
                    term_id,
                    boarding_type,
                    curriculum_type,
                )

                if not fee_structure:
                    errors.append({
                        "student_id": str(student.id),
                        "admission_number": student.admission_number,
                        "reason": f"No fee structure found for {boarding_type}/{curriculum_type}",
                    })
                    continue

                # Create invoice
                invoice_number = await self._generate_invoice_number(school_id, term_id)

                invoice = FeeInvoice(
                    school_id=school_id,
                    student_id=student.id,
                    term_id=term_id,
                    fee_structure_id=fee_structure.id,
                    invoice_number=invoice_number,
                    invoice_date=date.today(),
                    total_amount=fee_structure.total_amount,
                    amount_paid=Decimal("0.0000"),
                    status=FeeInvoiceStatusEnum.UNPAID.value,
                    created_by_id=created_by_id,
                )
                self.db.add(invoice)
                await self.db.flush()

                # Create invoice items (one per vote head)
                for fee_item in fee_structure.items:
                    invoice_item = FeeInvoiceItem(
                        invoice_id=invoice.id,
                        vote_head_id=fee_item.vote_head_id,
                        amount=fee_item.amount,
                        amount_paid=Decimal("0.0000"),
                    )
                    self.db.add(invoice_item)

                await self.db.flush()

                invoices_created += 1
                total_billed += fee_structure.total_amount

            except Exception as e:
                errors.append({
                    "student_id": str(student.id),
                    "admission_number": student.admission_number,
                    "reason": str(e),
                })
                await self.db.rollback()
                continue

        # Commit all invoices
        await self.db.commit()

        return {
            "invoices_created": invoices_created,
            "students_processed": len(students),
            "total_billed": total_billed,
            "errors": errors,
            "timestamp": datetime.now(timezone.utc),
        }

    async def _generate_invoice_number(self, school_id: UUID, term_id: UUID) -> str:
        """
        Generate a unique invoice number.
        Format: INV-YYYYMMDD-XXXXXX (random suffix for uniqueness)
        """
        today = date.today()
        date_part = today.strftime("%Y%m%d")

        while True:
            random_part = secrets.token_hex(3).upper()
            invoice_number = f"INV-{date_part}-{random_part}"

            # Check if exists
            existing = await self.invoice_repo.get_by_number(school_id, invoice_number)
            if not existing:
                return invoice_number
