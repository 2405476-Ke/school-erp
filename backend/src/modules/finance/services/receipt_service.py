"""
Receipt Service: Processes fee payments and allocates them to invoices.
CRITICAL ENGINE: Implements double-entry accounting with GL posting.

The payment allocation algorithm:
1. Find unpaid invoices (ordered by date, oldest first - "fifo" by term)
2. Clear arrears (past debts) FIRST
3. Distribute remainder across current term's vote heads by priority
4. Create GL journal entries atomically
5. If journal fails, receipt and allocation rollback
"""
import secrets
from datetime import date, datetime, timezone
from decimal import Decimal
from typing import List, Optional, Tuple
from uuid import UUID

from sqlalchemy import and_, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from src.modules.finance.models.fees import (
    FeeInvoice,
    FeeInvoiceItem,
    FeeInvoiceStatusEnum,
    FeeReceipt,
    FeeReceiptAllocation,
    StudentFeeAccount,
)
from src.modules.finance.repositories.fees_repo import (
    FeeInvoiceRepository,
    FeeReceiptAllocationRepository,
    FeeReceiptRepository,
    StudentFeeAccountRepository,
)
from src.modules.finance.services.journal_service import JournalService
from src.modules.finance.schemas.ledger import JournalEntryCreate, JournalLineCreate
from src.shared.exceptions import ValidationError, NotFoundError


class ReceiptService:
    """
    Service for receipt creation and payment allocation.
    Integrates with JournalService for GL posting.
    All operations are atomic - if journal fails, receipt rolls back.
    """

    def __init__(self, db: AsyncSession):
        self.db = db
        self.receipt_repo = FeeReceiptRepository(db)
        self.invoice_repo = FeeInvoiceRepository(db)
        self.allocation_repo = FeeReceiptAllocationRepository(db)
        self.student_account_repo = StudentFeeAccountRepository(db)
        self.journal_service = JournalService(db)

    async def create_receipt(
        self,
        school_id: UUID,
        student_id: UUID,
        receipt_date: date,
        amount: Decimal,
        payment_method: str,
        reference_number: Optional[str],
        created_by_id: UUID,
    ) -> FeeReceipt:
        """
        Create a new fee receipt (UNPOSTED).

        The receipt is created but NOT automatically posted to GL.
        Call allocate_payment() afterward to allocate to invoices and post GL.

        Args:
            school_id: School context
            student_id: Student paying
            receipt_date: Date of payment
            amount: Amount received (must be > 0)
            payment_method: MPESA, BANK, CASH, CHEQUE, BURSARY
            reference_number: Optional (M-Pesa code, cheque number, etc.)
            created_by_id: User creating receipt

        Returns:
            Created FeeReceipt (is_posted=False, no allocations yet)

        Raises:
            ValidationError: If amount <= 0 or student not found
        """
        if amount <= Decimal("0"):
            raise ValidationError("Receipt amount must be greater than 0")

        # Verify student exists
        from src.modules.students.models import Student

        student_query = select(Student).where(
            and_(
                Student.id == student_id,
                Student.school_id == school_id,
                Student.is_deleted == False,
            )
        )
        student_result = await self.db.execute(student_query)
        student = student_result.scalar_one_or_none()

        if not student:
            raise NotFoundError(f"Student {student_id} not found")

        # Generate receipt number
        receipt_number = await self._generate_receipt_number(school_id)

        # Create receipt (UNPOSTED)
        receipt = FeeReceipt(
            school_id=school_id,
            student_id=student_id,
            receipt_number=receipt_number,
            receipt_date=receipt_date,
            amount=amount,
            payment_method=payment_method,
            reference_number=reference_number,
            is_posted=False,
            created_by_id=created_by_id,
        )
        self.db.add(receipt)
        await self.db.flush()

        return receipt

    async def allocate_payment(
        self,
        school_id: UUID,
        receipt_id: UUID,
        user_id: UUID,
    ) -> FeeReceipt:
        """
        CRITICAL ALGORITHM: Allocate a receipt to invoices and post to GL.

        This is the heart of the fee billing system.

        Process:
        1. Fetch receipt with student
        2. Get all unpaid invoices for student (ordered by date, oldest first)
        3. Process each invoice:
           - Calculate unpaid amount (total - amount_paid)
           - Allocate as much as possible from receipt balance
           - Update invoice status (UNPAID→PAID or PAID→PARTIAL)
           - Create allocation records
           - Track which items were paid
        4. Create GL journal entry:
           - DR Bank/Mpesa (or cash account based on payment_method)
           - CR StudentReceivables (all allocated items at once)
        5. Post journal atomically (if fails, entire transaction rolls back)
        6. Update student_fee_accounts.running_balance (reduce by total paid)
        7. Mark receipt is_posted=True

        Args:
            school_id: School context
            receipt_id: Receipt to allocate
            user_id: User authorizing allocation

        Returns:
            Updated FeeReceipt (is_posted=True, with allocations)

        Raises:
            NotFoundError: If receipt not found
            ValidationError: If receipt already posted
        """
        # 1. Fetch receipt
        receipt = await self.receipt_repo.get_by_id(receipt_id)
        if not receipt or receipt.school_id != school_id:
            raise NotFoundError(f"Receipt {receipt_id} not found")

        if receipt.is_posted:
            raise ValidationError(f"Receipt {receipt.receipt_number} is already posted")

        # 2. Get all unpaid invoices for student (FIFO: oldest term first)
        unpaid_invoices = await self.invoice_repo.get_unpaid_for_student(receipt.student_id)

        if not unpaid_invoices:
            raise ValidationError(
                f"Student {receipt.student_id} has no unpaid invoices"
            )

        # 3. Process allocations
        remaining_amount = receipt.amount
        allocations: List[FeeReceiptAllocation] = []
        invoices_to_update: List[Tuple[FeeInvoice, Decimal]] = []

        for invoice in unpaid_invoices:
            unpaid_amount = invoice.total_amount - invoice.amount_paid

            if remaining_amount <= Decimal("0"):
                break  # No more money to allocate

            if remaining_amount >= unpaid_amount:
                # Can pay invoice in full
                allocation_for_invoice = remaining_amount
                remaining_amount -= unpaid_amount

                # Mark invoice as PAID
                invoice.status = FeeInvoiceStatusEnum.PAID.value
                invoice.amount_paid = invoice.total_amount

                # Create allocations for each item
                for item in invoice.items:
                    allocation = FeeReceiptAllocation(
                        school_id=school_id,
                        receipt_id=receipt_id,
                        invoice_item_id=item.id,
                        vote_head_id=item.vote_head_id,
                        allocated_amount=item.amount,
                    )
                    allocations.append(allocation)
                    item.amount_paid = item.amount

                invoices_to_update.append((invoice, unpaid_amount))

            else:
                # Can only partially pay invoice
                # Distribute remaining amount across items by priority
                allocated_by_priority = await self._allocate_by_priority(
                    school_id,
                    receipt_id,
                    invoice,
                    remaining_amount,
                )
                allocations.extend(allocated_by_priority)

                # Update invoice with partial payment
                total_allocated = sum(
                    (alloc.allocated_amount for alloc in allocated_by_priority),
                    Decimal("0.0000"),
                )
                invoice.amount_paid += total_allocated
                invoice.status = FeeInvoiceStatusEnum.PARTIAL.value

                # Update items
                for item in invoice.items:
                    item_allocations = [
                        a for a in allocated_by_priority if a.invoice_item_id == item.id
                    ]
                    for alloc in item_allocations:
                        item.amount_paid += alloc.allocated_amount

                invoices_to_update.append((invoice, total_allocated))
                remaining_amount = Decimal("0")

        # 4. Create GL journal entry
        # Collect all vote heads and amounts allocated
        vote_head_totals = {}
        for alloc in allocations:
            if alloc.vote_head_id not in vote_head_totals:
                vote_head_totals[alloc.vote_head_id] = Decimal("0.0000")
            vote_head_totals[alloc.vote_head_id] += alloc.allocated_amount

        # Get bank/cash account based on payment method
        bank_account_id = await self._get_bank_account_for_method(
            school_id, receipt.payment_method
        )

        # Build journal lines
        journal_lines = [
            JournalLineCreate(
                account_id=bank_account_id,
                cost_center_id=None,
                description=f"Fee receipt {receipt.receipt_number} - {receipt.payment_method}",
                debit=sum(
                    (alloc.allocated_amount for alloc in allocations),
                    Decimal("0.0000"),
                ),
                credit=Decimal("0.0000"),
            )
        ]

        # CR each vote head's revenue account (account_id from FeeVoteHead)
        for vote_head_id, allocated_amount in vote_head_totals.items():
            vote_head_query = select(FeeVoteHead).where(FeeVoteHead.id == vote_head_id)
            vote_head_result = await self.db.execute(vote_head_query)
            vote_head = vote_head_result.scalar_one_or_none()

            if not vote_head:
                raise NotFoundError(f"Vote head {vote_head_id} not found")

            journal_lines.append(
                JournalLineCreate(
                    account_id=vote_head.account_id,
                    cost_center_id=None,
                    description=f"Fee revenue - {vote_head.name}",
                    debit=Decimal("0.0000"),
                    credit=allocated_amount,
                )
            )

        # Create journal entry (DRAFT)
        total_allocated = sum(
            (alloc.allocated_amount for alloc in allocations),
            Decimal("0.0000"),
        )

        journal_data = JournalEntryCreate(
            transaction_date=receipt.receipt_date,
            description=f"Fee receipt {receipt.receipt_number} from student {receipt.student_id}",
            lines=journal_lines,
        )

        try:
            # Create draft journal
            draft_journal = await self.journal_service.create_draft(
                school_id, journal_data, user_id
            )

            # Post journal immediately
            posted_journal = await self.journal_service.post_journal(
                school_id, draft_journal.id, user_id
            )

            # Update receipt
            receipt.is_posted = True
            receipt.posted_by_id = user_id
            receipt.posted_at = datetime.now(timezone.utc)
            receipt.journal_entry_id = posted_journal.id

        except Exception as e:
            # Journal posting failed - rollback everything
            await self.db.rollback()
            raise ValidationError(
                f"Failed to post GL journal for receipt {receipt.receipt_number}: {str(e)}"
            )

        # 5. Add all allocations to session
        for alloc in allocations:
            self.db.add(alloc)

        # 6. Update student fee account
        student_account = await self.student_account_repo.get_or_create_for_student(
            school_id, receipt.student_id
        )
        student_account.running_balance = max(
            Decimal("0.0000"),
            student_account.running_balance - total_allocated,
        )
        student_account.last_updated_at = datetime.now(timezone.utc)

        # Commit everything
        await self.db.commit()

        # Reload receipt with allocations
        receipt = await self.receipt_repo.get_by_id(receipt_id)
        return receipt

    async def _allocate_by_priority(
        self,
        school_id: UUID,
        receipt_id: UUID,
        invoice: FeeInvoice,
        remaining_amount: Decimal,
    ) -> List[FeeReceiptAllocation]:
        """
        Allocate remaining amount across invoice items by vote head priority.

        Process:
        1. Sort items by vote_head.priority (lower = paid first)
        2. Allocate remaining_amount to each item in priority order
        3. Create allocation records

        Args:
            school_id: School context
            receipt_id: Receipt being allocated
            invoice: Invoice to allocate from
            remaining_amount: Amount left to allocate

        Returns:
            List of allocation records created
        """
        allocations = []

        # Sort items by vote head priority
        sorted_items = sorted(
            invoice.items,
            key=lambda item: item.vote_head.priority if item.vote_head else 999,
        )

        for item in sorted_items:
            if remaining_amount <= Decimal("0"):
                break

            item_unpaid = item.amount - item.amount_paid

            if remaining_amount >= item_unpaid:
                # Pay item in full
                allocation = FeeReceiptAllocation(
                    school_id=school_id,
                    receipt_id=receipt_id,
                    invoice_item_id=item.id,
                    vote_head_id=item.vote_head_id,
                    allocated_amount=item_unpaid,
                )
                allocations.append(allocation)
                item.amount_paid = item.amount
                remaining_amount -= item_unpaid

            else:
                # Partial payment to item
                allocation = FeeReceiptAllocation(
                    school_id=school_id,
                    receipt_id=receipt_id,
                    invoice_item_id=item.id,
                    vote_head_id=item.vote_head_id,
                    allocated_amount=remaining_amount,
                )
                allocations.append(allocation)
                item.amount_paid += remaining_amount
                remaining_amount = Decimal("0")

        return allocations

    async def _get_bank_account_for_method(
        self, school_id: UUID, payment_method: str
    ) -> UUID:
        """
        Get the GL bank/cash account for a payment method.

        For now, returns a placeholder. In production, this would:
        - MPESA → M-Pesa Suspense Account (1105)
        - BANK → Bank Account (1110)
        - CASH → Cash in Hand (1100)
        - CHEQUE → Cheques in Transit (1120)
        - BURSARY → Bursary Account (special)

        This should be configurable per school.
        """
        # For this implementation, we'll use a hard-coded account
        # In production, fetch from school settings
        account_query = (
            select("Account")
            .where(
                and_(
                    "Account.school_id" == school_id,
                    "Account.code".in_(["1100", "1110"]),  # Cash or Bank
                )
            )
            .limit(1)
        )
        # Note: This is simplified; actual code would fetch from Account model
        # For now, raise error if account not configured
        from src.modules.finance.models.ledger import Account

        account_query = (
            select(Account)
            .where(
                and_(
                    Account.school_id == school_id,
                    Account.code.in_(["1100", "1110"]),
                )
            )
            .limit(1)
        )
        result = await self.db.execute(account_query)
        account = result.scalar_one_or_none()

        if not account:
            raise ValidationError(
                f"No bank/cash account configured for payment method {payment_method}"
            )

        return account.id

    async def _generate_receipt_number(self, school_id: UUID) -> str:
        """
        Generate a unique receipt number.
        Format: RCP-YYYYMMDD-XXXXXX (random suffix)
        """
        today = date.today()
        date_part = today.strftime("%Y%m%d")

        while True:
            random_part = secrets.token_hex(3).upper()
            receipt_number = f"RCP-{date_part}-{random_part}"

            existing = await self.receipt_repo.get_by_number(school_id, receipt_number)
            if not existing:
                return receipt_number


# Import at end to avoid circular imports
from src.modules.finance.models.fees import FeeVoteHead
