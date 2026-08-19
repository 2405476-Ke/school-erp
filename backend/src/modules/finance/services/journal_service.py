"""
Journal Service: Core double-entry accounting engine.
Implements business rules for journal posting, reversal, and balance management.
All operations are fully atomic with comprehensive validation.
"""
import secrets
from datetime import datetime, timezone
from decimal import Decimal
from typing import List, Optional
from uuid import UUID

from sqlalchemy import and_, func, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from src.modules.finance.models.ledger import (
    Account,
    AccountBalance,
    AccountingPeriod,
    JournalEntry,
    JournalLine,
    JournalStatusEnum,
    PeriodStatusEnum,
)
from src.modules.finance.repositories.ledger_repo import (
    AccountBalanceRepository,
    AccountRepository,
    AccountingPeriodRepository,
    JournalEntryRepository,
    JournalLineRepository,
)
from src.modules.finance.schemas.ledger import (
    JournalEntryCreate,
    JournalEntryResponse,
    JournalLineCreate,
)
from src.shared.exceptions import (
    ValidationError,
    UnauthorizedError,
    NotFoundError,
    DuplicateEntryError,
)


class JournalService:
    """
    Core service for double-entry accounting journal management.
    Ensures all business rules: balance, no control/header posting, period validation, atomicity.
    """

    def __init__(self, db: AsyncSession):
        self.db = db
        self.period_repo = AccountingPeriodRepository(db)
        self.account_repo = AccountRepository(db)
        self.journal_repo = JournalEntryRepository(db)
        self.journal_line_repo = JournalLineRepository(db)
        self.balance_repo = AccountBalanceRepository(db)

    async def create_draft(
        self, school_id: UUID, data: JournalEntryCreate, user_id: UUID
    ) -> JournalEntryResponse:
        """
        Create a new draft journal entry.

        Validates:
        1. Transaction date falls in an OPEN period
        2. All referenced accounts exist, are active, and not headers/control
        3. Journal is balanced (debits = credits)

        Args:
            school_id: School context
            data: Journal entry creation schema
            user_id: User creating the entry

        Returns:
            Fully populated JournalEntryResponse

        Raises:
            ValidationError: If any validation fails
        """
        # 1. Validate period is open for the transaction date
        period = await self.period_repo.get_open_period_for_date(school_id, data.transaction_date)
        if not period:
            raise ValidationError(
                f"No open accounting period found for date {data.transaction_date}"
            )

        # 2. Validate all accounts
        account_ids = [line.account_id for line in data.lines]
        accounts_query = select(Account).where(Account.id.in_(account_ids))
        accounts_result = await self.db.execute(accounts_query)
        accounts_dict = {acc.id: acc for acc in accounts_result.scalars().all()}

        for line in data.lines:
            acc = accounts_dict.get(line.account_id)
            if not acc:
                raise NotFoundError(f"Account {line.account_id} not found")
            if acc.school_id != school_id:
                raise ValidationError(
                    f"Account {line.account_id} does not belong to this school"
                )
            if not acc.is_active:
                raise ValidationError(
                    f"Account {acc.code} ({acc.name}) is not active"
                )
            if acc.is_header:
                raise ValidationError(
                    f"Cannot post to header account {acc.code} ({acc.name})"
                )
            if acc.is_control_account:
                raise ValidationError(
                    f"Cannot manually post to control account {acc.code} ({acc.name})"
                )

        # 3. Re-check balanced (defense in depth)
        total_debit = sum((line.debit for line in data.lines), Decimal("0.0000"))
        total_credit = sum((line.credit for line in data.lines), Decimal("0.0000"))
        if total_debit != total_credit:
            raise ValidationError(
                f"Journal is unbalanced: debit={total_debit}, credit={total_credit}"
            )

        # 4. Generate unique reference
        reference = await self._generate_reference(school_id, data.transaction_date)

        # 5. Create journal entry
        journal = JournalEntry(
            school_id=school_id,
            reference=reference,
            transaction_date=data.transaction_date,
            description=data.description,
            period_id=period.id,
            status=JournalStatusEnum.DRAFT.value,
            created_by_id=user_id,
        )
        self.db.add(journal)
        await self.db.flush()

        # 6. Create journal lines
        for line_data in data.lines:
            line = JournalLine(
                journal_id=journal.id,
                account_id=line_data.account_id,
                cost_center_id=line_data.cost_center_id,
                description=line_data.description,
                debit=line_data.debit,
                credit=line_data.credit,
            )
            self.db.add(line)

        await self.db.commit()

        # 7. Reload with relations for response
        journal = await self.journal_repo.get_with_lines(journal.id)
        return JournalEntryResponse.model_validate(journal)

    async def post_journal(self, school_id: UUID, journal_id: UUID, user_id: UUID) -> JournalEntryResponse:
        """
        Post (commit) a draft journal entry to the general ledger.

        This is the CRITICAL operation that updates running balances.

        Validates:
        1. Journal exists and belongs to school
        2. Journal is in DRAFT status
        3. Period is still OPEN
        4. Journal is balanced (defense in depth)
        5. All referenced accounts exist and are valid

        Updates:
        1. Sets journal status to POSTED
        2. Updates AccountBalance records (create if needed, update movements)
        3. Sets posted_by_id and posted_at

        This operation is ATOMIC - all changes commit together or all rollback.

        Args:
            school_id: School context
            journal_id: Journal to post
            user_id: User posting the entry

        Returns:
            Updated JournalEntryResponse

        Raises:
            NotFoundError: If journal not found
            ValidationError: If journal cannot be posted (status, period, balance, etc.)
        """
        # 1. Fetch journal with lines, using pessimistic lock
        journal_query = (
            select(JournalEntry)
            .where(
                and_(
                    JournalEntry.id == journal_id,
                    JournalEntry.school_id == school_id,
                )
            )
            .options(selectinload(JournalEntry.lines).selectinload(JournalLine.account))
            .with_for_update()
        )
        result = await self.db.execute(journal_query)
        journal = result.scalar_one_or_none()

        if not journal:
            raise NotFoundError(f"Journal {journal_id} not found in this school")

        # 2. Validate journal status
        if journal.status != JournalStatusEnum.DRAFT.value:
            raise ValidationError(
                f"Cannot post journal with status {journal.status}. Only DRAFT can be posted."
            )

        # 3. Validate journal has lines
        if not journal.lines:
            raise ValidationError("Cannot post journal without lines")

        # 4. Validate period is still OPEN
        period_query = select(AccountingPeriod).where(
            AccountingPeriod.id == journal.period_id
        ).with_for_update()
        period_result = await self.db.execute(period_query)
        period = period_result.scalar_one_or_none()

        if not period:
            raise NotFoundError(f"Period {journal.period_id} not found")
        if period.status != PeriodStatusEnum.OPEN.value:
            raise ValidationError(
                f"Cannot post journal to {period.status} period. Only OPEN periods accept posts."
            )

        # 5. Re-validate balance (defense in depth)
        total_debit = sum((line.debit for line in journal.lines), Decimal("0.0000"))
        total_credit = sum((line.credit for line in journal.lines), Decimal("0.0000"))

        if total_debit != total_credit:
            raise ValidationError(
                f"Journal {journal.reference} is unbalanced (Dr={total_debit}, Cr={total_credit}). "
                f"This should not happen; data integrity issue detected."
            )

        # 6. Process each line: update or create AccountBalance
        for line in journal.lines:
            # Get existing balance record or create new one
            balance_query = (
                select(AccountBalance)
                .where(
                    and_(
                        AccountBalance.school_id == school_id,
                        AccountBalance.account_id == line.account_id,
                        AccountBalance.period_id == journal.period_id,
                        AccountBalance.cost_center_id == line.cost_center_id,
                    )
                )
                .with_for_update()
            )
            balance_result = await self.db.execute(balance_query)
            balance = balance_result.scalar_one_or_none()

            if not balance:
                # Create new balance record
                balance = AccountBalance(
                    school_id=school_id,
                    account_id=line.account_id,
                    period_id=journal.period_id,
                    cost_center_id=line.cost_center_id,
                    opening_balance=Decimal("0.0000"),
                    debit_movement=Decimal("0.0000"),
                    credit_movement=Decimal("0.0000"),
                    closing_balance=Decimal("0.0000"),
                )
                self.db.add(balance)
                await self.db.flush()

            # Update movements
            balance.debit_movement += line.debit
            balance.credit_movement += line.credit

            # Calculate closing balance (depends on account type)
            account = line.account
            if account.category.account_type.normal_balance == "DEBIT":
                # Assets, Expenses: balance = opening + debits - credits
                balance.closing_balance = (
                    balance.opening_balance + balance.debit_movement - balance.credit_movement
                )
            else:
                # Liabilities, Equity, Revenue: balance = opening - debits + credits
                balance.closing_balance = (
                    balance.opening_balance - balance.debit_movement + balance.credit_movement
                )

        # 7. Update journal status
        journal.status = JournalStatusEnum.POSTED.value
        journal.posted_by_id = user_id
        journal.posted_at = datetime.now(timezone.utc)

        # 8. Commit all changes atomically
        await self.db.commit()

        # 9. Reload and return
        journal = await self.journal_repo.get_with_lines(journal_id)
        return JournalEntryResponse.model_validate(journal)

    async def reverse_journal(
        self,
        school_id: UUID,
        journal_id: UUID,
        user_id: UUID,
        reason: str,
    ) -> JournalEntryResponse:
        """
        Reverse a posted journal entry by creating an offsetting POSTED journal.

        The reversal journal is created as DRAFT, then immediately posted.
        Original journal marked as REVERSED.

        Validates:
        1. Original journal exists and is POSTED
        2. Original journal not already reversed
        3. Period is still OPEN

        Creates:
        1. New reversal journal with swapped debit/credit
        2. Posts reversal journal
        3. Marks original as REVERSED

        Args:
            school_id: School context
            journal_id: Journal to reverse
            user_id: User authorizing reversal
            reason: Reason for reversal

        Returns:
            The posted reversal journal

        Raises:
            NotFoundError: If journal not found
            ValidationError: If journal cannot be reversed
        """
        # 1. Fetch original journal
        original_query = (
            select(JournalEntry)
            .where(
                and_(
                    JournalEntry.id == journal_id,
                    JournalEntry.school_id == school_id,
                )
            )
            .options(selectinload(JournalEntry.lines))
            .with_for_update()
        )
        result = await self.db.execute(original_query)
        original = result.scalar_one_or_none()

        if not original:
            raise NotFoundError(f"Journal {journal_id} not found")

        # 2. Validate original is POSTED
        if original.status != JournalStatusEnum.POSTED.value:
            raise ValidationError(
                f"Cannot reverse journal with status {original.status}. Only POSTED can be reversed."
            )

        # 3. Validate not already reversed
        if original.reversed_by_id is not None:
            raise ValidationError(
                f"Journal {original.reference} has already been reversed"
            )

        # 4. Validate period is still OPEN
        period_query = select(AccountingPeriod).where(
            AccountingPeriod.id == original.period_id
        )
        period_result = await self.db.execute(period_query)
        period = period_result.scalar_one_or_none()

        if not period:
            raise NotFoundError("Original period not found")
        if period.status != PeriodStatusEnum.OPEN.value:
            raise ValidationError(
                "Cannot reverse journal: period is closed. "
                "Reversals require an open period."
            )

        # 5. Generate reversal reference
        reversal_reference = f"REV-{original.reference}"

        # 6. Create reversal journal (initially DRAFT)
        reversal = JournalEntry(
            school_id=school_id,
            reference=reversal_reference,
            transaction_date=original.transaction_date,
            description=f"Reversal of {original.reference}: {reason}",
            period_id=original.period_id,
            status=JournalStatusEnum.DRAFT.value,
            created_by_id=user_id,
            reverses_id=original.id,
        )
        self.db.add(reversal)
        await self.db.flush()

        # 7. Create reversed lines (swap debit/credit)
        for orig_line in original.lines:
            reversal_line = JournalLine(
                journal_id=reversal.id,
                account_id=orig_line.account_id,
                cost_center_id=orig_line.cost_center_id,
                description=f"Reversal of {orig_line.description or original.reference}",
                debit=orig_line.credit,  # Swap
                credit=orig_line.debit,  # Swap
            )
            self.db.add(reversal_line)

        await self.db.flush()

        # 8. Post the reversal journal
        reversal_posted = await self.post_journal(school_id, reversal.id, user_id)

        # 9. Mark original as REVERSED
        original.status = JournalStatusEnum.REVERSED.value
        original.reversed_by_id = user_id

        await self.db.commit()

        return reversal_posted

    async def get_journal(
        self, school_id: UUID, journal_id: UUID
    ) -> JournalEntryResponse:
        """Fetch a single journal entry by ID."""
        journal = await self.journal_repo.get_with_lines(journal_id)
        if not journal or journal.school_id != school_id:
            raise NotFoundError(f"Journal {journal_id} not found")
        return JournalEntryResponse.model_validate(journal)

    async def list_journals(
        self,
        school_id: UUID,
        period_id: Optional[UUID] = None,
        status: Optional[str] = None,
        skip: int = 0,
        limit: int = 50,
    ) -> tuple[List[JournalEntryResponse], int]:
        """
        List journals with optional filtering.

        Args:
            school_id: School context
            period_id: Filter by period (optional)
            status: Filter by status (optional): DRAFT, POSTED, REVERSED
            skip: Pagination offset
            limit: Pagination limit

        Returns:
            Tuple of (journals, total_count)
        """
        filters = [
            JournalEntry.school_id == school_id,
            JournalEntry.is_deleted == False,
        ]
        if period_id:
            filters.append(JournalEntry.period_id == period_id)
        if status:
            filters.append(JournalEntry.status == status)

        # Count query
        count_query = select(func.count(JournalEntry.id)).where(and_(*filters))
        count_result = await self.db.execute(count_query)
        total = count_result.scalar() or 0

        # Data query
        data_query = (
            select(JournalEntry)
            .where(and_(*filters))
            .options(selectinload(JournalEntry.lines))
            .order_by(JournalEntry.transaction_date.desc(), JournalEntry.created_at.desc())
            .offset(skip)
            .limit(limit)
        )
        data_result = await self.db.execute(data_query)
        journals = [
            JournalEntryResponse.model_validate(j) for j in data_result.scalars().all()
        ]

        return journals, total

    async def _generate_reference(self, school_id: UUID, transaction_date) -> str:
        """Generate a unique journal reference."""
        # Format: JRN-YYYYMM-XXXXXX (random 6-char suffix)
        date_part = transaction_date.strftime("%Y%m")
        random_part = secrets.token_hex(3).upper()
        reference = f"JRN-{date_part}-{random_part}"

        # Ensure uniqueness
        while True:
            existing = await self.journal_repo.get_by_reference(school_id, reference)
            if not existing:
                return reference
            random_part = secrets.token_hex(3).upper()
            reference = f"JRN-{date_part}-{random_part}"
