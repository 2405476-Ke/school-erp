"""
Fee management repositories: Data access layer for FeeVoteHead, FeeStructure, FeeInvoice, FeeReceipt.
Typed queries with proper eager loading and transaction safety.
"""
from datetime import date
from decimal import Decimal
from typing import List, Optional, Tuple
from uuid import UUID

from sqlalchemy import and_, func, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from src.modules.finance.models.fees import (
    FeeInvoice,
    FeeInvoiceItem,
    FeeInvoiceStatusEnum,
    FeeReceipt,
    FeeReceiptAllocation,
    FeeStructure,
    FeeStructureItem,
    FeeVoteHead,
    PaymentMethodEnum,
    StudentFeeAccount,
)
from src.shared.base_repository import BaseRepository


class FeeVoteHeadRepository(BaseRepository[FeeVoteHead]):
    """Repository for fee vote head data access."""

    def __init__(self, db: AsyncSession):
        super().__init__(FeeVoteHead, db)

    async def get_by_name(self, school_id: UUID, name: str) -> Optional[FeeVoteHead]:
        """Fetch vote head by name within school."""
        query = (
            select(self.model)
            .where(
                and_(
                    self.model.school_id == school_id,
                    self.model.name == name,
                    self.model.is_deleted == False,
                )
            )
        )
        result = await self.db.execute(query)
        return result.scalar_one_or_none()

    async def get_active_by_priority(self, school_id: UUID) -> List[FeeVoteHead]:
        """Fetch all active vote heads ordered by priority (for payment allocation)."""
        query = (
            select(self.model)
            .where(
                and_(
                    self.model.school_id == school_id,
                    self.model.is_active == True,
                    self.model.is_deleted == False,
                )
            )
            .order_by(self.model.priority.asc())
        )
        result = await self.db.execute(query)
        return result.scalars().all()


class FeeStructureRepository(BaseRepository[FeeStructure]):
    """Repository for fee structure data access."""

    def __init__(self, db: AsyncSession):
        super().__init__(FeeStructure, db)

    async def get_for_term(
        self,
        school_id: UUID,
        academic_year_id: UUID,
        term_id: UUID,
        boarding_type: str,
        curriculum_type: str,
    ) -> Optional[FeeStructure]:
        """
        Fetch fee structure for specific term, boarding type, and curriculum.
        Tries exact match first, then falls back to 'ALL' wildcards.
        """
        # Exact match
        query = (
            select(self.model)
            .where(
                and_(
                    self.model.school_id == school_id,
                    self.model.academic_year_id == academic_year_id,
                    self.model.term_id == term_id,
                    self.model.boarding_type == boarding_type,
                    self.model.curriculum_type == curriculum_type,
                    self.model.is_active == True,
                    self.model.is_deleted == False,
                )
            )
            .options(selectinload(FeeStructure.items).selectinload(FeeStructureItem.vote_head))
        )
        result = await self.db.execute(query)
        structure = result.scalar_one_or_none()

        if structure:
            return structure

        # Fallback 1: Try boarding_type=ALL, exact curriculum
        query = (
            select(self.model)
            .where(
                and_(
                    self.model.school_id == school_id,
                    self.model.academic_year_id == academic_year_id,
                    self.model.term_id == term_id,
                    self.model.boarding_type == "ALL",
                    self.model.curriculum_type == curriculum_type,
                    self.model.is_active == True,
                    self.model.is_deleted == False,
                )
            )
            .options(selectinload(FeeStructure.items).selectinload(FeeStructureItem.vote_head))
        )
        result = await self.db.execute(query)
        structure = result.scalar_one_or_none()

        if structure:
            return structure

        # Fallback 2: Try curriculum_type=ALL, exact boarding
        query = (
            select(self.model)
            .where(
                and_(
                    self.model.school_id == school_id,
                    self.model.academic_year_id == academic_year_id,
                    self.model.term_id == term_id,
                    self.model.boarding_type == boarding_type,
                    self.model.curriculum_type == "ALL",
                    self.model.is_active == True,
                    self.model.is_deleted == False,
                )
            )
            .options(selectinload(FeeStructure.items).selectinload(FeeStructureItem.vote_head))
        )
        result = await self.db.execute(query)
        structure = result.scalar_one_or_none()

        if structure:
            return structure

        # Fallback 3: Both ALL
        query = (
            select(self.model)
            .where(
                and_(
                    self.model.school_id == school_id,
                    self.model.academic_year_id == academic_year_id,
                    self.model.term_id == term_id,
                    self.model.boarding_type == "ALL",
                    self.model.curriculum_type == "ALL",
                    self.model.is_active == True,
                    self.model.is_deleted == False,
                )
            )
            .options(selectinload(FeeStructure.items).selectinload(FeeStructureItem.vote_head))
        )
        result = await self.db.execute(query)
        return result.scalar_one_or_none()


class FeeInvoiceRepository(BaseRepository[FeeInvoice]):
    """Repository for fee invoice data access."""

    def __init__(self, db: AsyncSession):
        super().__init__(FeeInvoice, db)

    async def get_by_number(self, school_id: UUID, invoice_number: str) -> Optional[FeeInvoice]:
        """Fetch invoice by number."""
        query = (
            select(self.model)
            .where(
                and_(
                    self.model.school_id == school_id,
                    self.model.invoice_number == invoice_number,
                    self.model.is_deleted == False,
                )
            )
            .options(selectinload(FeeInvoice.items).selectinload(FeeInvoiceItem.vote_head))
        )
        result = await self.db.execute(query)
        return result.scalar_one_or_none()

    async def get_unpaid_for_student(self, student_id: UUID) -> List[FeeInvoice]:
        """Fetch all unpaid/partial invoices for a student, ordered by invoice date."""
        query = (
            select(self.model)
            .where(
                and_(
                    self.model.student_id == student_id,
                    self.model.status.in_([
                        FeeInvoiceStatusEnum.UNPAID.value,
                        FeeInvoiceStatusEnum.PARTIAL.value,
                    ]),
                    self.model.is_deleted == False,
                )
            )
            .options(selectinload(FeeInvoice.items).selectinload(FeeInvoiceItem.vote_head))
            .order_by(self.model.invoice_date.asc())
        )
        result = await self.db.execute(query)
        return result.scalars().all()

    async def get_for_student_term(
        self, student_id: UUID, term_id: UUID
    ) -> Optional[FeeInvoice]:
        """Fetch invoice for a specific student + term."""
        query = (
            select(self.model)
            .where(
                and_(
                    self.model.student_id == student_id,
                    self.model.term_id == term_id,
                    self.model.is_deleted == False,
                )
            )
            .options(selectinload(FeeInvoice.items).selectinload(FeeInvoiceItem.vote_head))
        )
        result = await self.db.execute(query)
        return result.scalar_one_or_none()

    async def get_for_term(
        self, school_id: UUID, term_id: UUID, status: Optional[str] = None
    ) -> List[FeeInvoice]:
        """Fetch invoices for a term, optionally filtered by status."""
        filters = [
            self.model.school_id == school_id,
            self.model.term_id == term_id,
            self.model.is_deleted == False,
        ]
        if status:
            filters.append(self.model.status == status)

        query = (
            select(self.model)
            .where(and_(*filters))
            .options(selectinload(FeeInvoice.items))
            .order_by(self.model.invoice_date.desc())
        )
        result = await self.db.execute(query)
        return result.scalars().all()


class FeeReceiptRepository(BaseRepository[FeeReceipt]):
    """Repository for fee receipt data access."""

    def __init__(self, db: AsyncSession):
        super().__init__(FeeReceipt, db)

    async def get_by_number(self, school_id: UUID, receipt_number: str) -> Optional[FeeReceipt]:
        """Fetch receipt by number."""
        query = (
            select(self.model)
            .where(
                and_(
                    self.model.school_id == school_id,
                    self.model.receipt_number == receipt_number,
                    self.model.is_deleted == False,
                )
            )
            .options(selectinload(FeeReceipt.allocations))
        )
        result = await self.db.execute(query)
        return result.scalar_one_or_none()

    async def get_for_student(
        self, student_id: UUID, posted_only: bool = False
    ) -> List[FeeReceipt]:
        """Fetch receipts for a student."""
        filters = [
            self.model.student_id == student_id,
            self.model.is_deleted == False,
        ]
        if posted_only:
            filters.append(self.model.is_posted == True)

        query = (
            select(self.model)
            .where(and_(*filters))
            .options(selectinload(FeeReceipt.allocations))
            .order_by(self.model.receipt_date.desc())
        )
        result = await self.db.execute(query)
        return result.scalars().all()

    async def get_unposted(self, school_id: UUID) -> List[FeeReceipt]:
        """Fetch all unposted receipts (ready for GL posting)."""
        query = (
            select(self.model)
            .where(
                and_(
                    self.model.school_id == school_id,
                    self.model.is_posted == False,
                    self.model.is_deleted == False,
                )
            )
            .options(selectinload(FeeReceipt.allocations))
            .order_by(self.model.created_at.asc())
        )
        result = await self.db.execute(query)
        return result.scalars().all()


class FeeReceiptAllocationRepository(BaseRepository[FeeReceiptAllocation]):
    """Repository for receipt allocation data access."""

    def __init__(self, db: AsyncSession):
        super().__init__(FeeReceiptAllocation, db)

    async def get_for_receipt(self, receipt_id: UUID) -> List[FeeReceiptAllocation]:
        """Fetch all allocations for a receipt."""
        query = (
            select(self.model)
            .where(self.model.receipt_id == receipt_id)
            .options(
                selectinload(FeeReceiptAllocation.invoice_item),
                selectinload(FeeReceiptAllocation.vote_head),
            )
        )
        result = await self.db.execute(query)
        return result.scalars().all()


class StudentFeeAccountRepository(BaseRepository[StudentFeeAccount]):
    """Repository for student fee account (running balance) data access."""

    def __init__(self, db: AsyncSession):
        super().__init__(StudentFeeAccount, db)

    async def get_for_student(self, student_id: UUID) -> Optional[StudentFeeAccount]:
        """Fetch fee account for student."""
        query = select(self.model).where(
            and_(
                self.model.student_id == student_id,
                self.model.is_deleted == False,
            )
        )
        result = await self.db.execute(query)
        return result.scalar_one_or_none()

    async def get_or_create_for_student(
        self, school_id: UUID, student_id: UUID
    ) -> StudentFeeAccount:
        """Get existing fee account or create new one."""
        account = await self.get_for_student(student_id)
        if account:
            return account

        # Create new account
        new_account = StudentFeeAccount(
            school_id=school_id,
            student_id=student_id,
            running_balance=Decimal("0.0000"),
        )
        self.db.add(new_account)
        await self.db.flush()
        return new_account
