"""
Ledger repository: Data access layer for Chart of Accounts, Periods, Journal Entries, and Balances.
Implements typed queries with proper cursor management and transaction safety.
"""
from datetime import date
from decimal import Decimal
from typing import List, Optional, Tuple
from uuid import UUID

from sqlalchemy import and_, func, or_, select, update
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from src.modules.finance.models.ledger import (
    Account,
    AccountBalance,
    AccountCategory,
    AccountType,
    AccountingPeriod,
    CostCenter,
    FinancialYear,
    JournalEntry,
    JournalLine,
    PeriodStatusEnum,
    JournalStatusEnum,
)
from src.shared.base_repository import BaseRepository


class FinancialYearRepository(BaseRepository[FinancialYear]):
    """Repository for financial year data access."""

    def __init__(self, db: AsyncSession):
        super().__init__(FinancialYear, db)

    async def get_active_year(self, school_id: UUID) -> Optional[FinancialYear]:
        """Fetch the active financial year for a school."""
        query = (
            select(self.model)
            .where(
                and_(
                    self.model.school_id == school_id,
                    self.model.status == "OPEN",
                    self.model.is_deleted == False,
                )
            )
            .options(selectinload(FinancialYear.periods))
        )
        result = await self.db.execute(query)
        return result.scalar_one_or_none()

    async def get_year_by_name(self, school_id: UUID, year_name: str) -> Optional[FinancialYear]:
        """Fetch year by name and school."""
        query = (
            select(self.model)
            .where(
                and_(
                    self.model.school_id == school_id,
                    self.model.year_name == year_name,
                    self.model.is_deleted == False,
                )
            )
            .options(selectinload(FinancialYear.periods))
        )
        result = await self.db.execute(query)
        return result.scalar_one_or_none()


class AccountingPeriodRepository(BaseRepository[AccountingPeriod]):
    """Repository for accounting period data access."""

    def __init__(self, db: AsyncSession):
        super().__init__(AccountingPeriod, db)

    async def get_open_period_for_date(self, school_id: UUID, transaction_date: date) -> Optional[AccountingPeriod]:
        """Fetch the OPEN period containing the given date."""
        query = (
            select(self.model)
            .where(
                and_(
                    self.model.school_id == school_id,
                    self.model.start_date <= transaction_date,
                    self.model.end_date >= transaction_date,
                    self.model.status == PeriodStatusEnum.OPEN.value,
                    self.model.is_deleted == False,
                )
            )
        )
        result = await self.db.execute(query)
        return result.scalar_one_or_none()

    async def get_periods_by_year(
        self, school_id: UUID, financial_year_id: UUID
    ) -> List[AccountingPeriod]:
        """Fetch all periods in a financial year, ordered by start_date."""
        query = (
            select(self.model)
            .where(
                and_(
                    self.model.school_id == school_id,
                    self.model.financial_year_id == financial_year_id,
                    self.model.is_deleted == False,
                )
            )
            .order_by(self.model.start_date.asc())
        )
        result = await self.db.execute(query)
        return result.scalars().all()

    async def get_next_period(
        self, school_id: UUID, current_period_id: UUID
    ) -> Optional[AccountingPeriod]:
        """Fetch the next period (chronologically) after the given period."""
        current = await self.get_by_id(current_period_id)
        if not current or current.school_id != school_id:
            return None

        query = (
            select(self.model)
            .where(
                and_(
                    self.model.school_id == school_id,
                    self.model.financial_year_id == current.financial_year_id,
                    self.model.start_date > current.end_date,
                    self.model.is_deleted == False,
                )
            )
            .order_by(self.model.start_date.asc())
            .limit(1)
        )
        result = await self.db.execute(query)
        return result.scalar_one_or_none()


class AccountRepository(BaseRepository[Account]):
    """Repository for Chart of Accounts data access."""

    def __init__(self, db: AsyncSession):
        super().__init__(Account, db)

    async def get_by_code(self, school_id: UUID, code: str) -> Optional[Account]:
        """Fetch account by code within a school."""
        query = (
            select(self.model)
            .where(
                and_(
                    self.model.school_id == school_id,
                    self.model.code == code,
                    self.model.is_deleted == False,
                )
            )
        )
        result = await self.db.execute(query)
        return result.scalar_one_or_none()

    async def get_tree_roots(self, school_id: UUID) -> List[Account]:
        """Fetch all root accounts (parent_id IS NULL) for a school."""
        query = (
            select(self.model)
            .where(
                and_(
                    self.model.school_id == school_id,
                    self.model.parent_id == None,
                    self.model.is_deleted == False,
                )
            )
            .options(selectinload(Account.children))
            .order_by(self.model.code.asc())
        )
        result = await self.db.execute(query)
        return result.scalars().all()

    async def get_all_descendants(self, account_id: UUID) -> List[Account]:
        """Fetch all descendants of an account (recursive)."""
        # Simplified approach: fetch all accounts and build tree in memory
        # For large charts, consider using PostgreSQL WITH RECURSIVE
        query = (
            select(self.model)
            .where(self.model.is_deleted == False)
            .options(selectinload(Account.children))
        )
        result = await self.db.execute(query)
        all_accounts = result.scalars().all()

        descendants = []

        def collect_descendants(acc: Account):
            for child in acc.children:
                descendants.append(child)
                collect_descendants(child)

        parent = next((acc for acc in all_accounts if acc.id == account_id), None)
        if parent:
            collect_descendants(parent)

        return descendants

    async def get_active_by_type(
        self, school_id: UUID, account_type: str
    ) -> List[Account]:
        """Fetch all active accounts of a given type."""
        query = (
            select(self.model)
            .join(AccountCategory, self.model.category_id == AccountCategory.id)
            .join(AccountType, AccountCategory.account_type_id == AccountType.id)
            .where(
                and_(
                    self.model.school_id == school_id,
                    self.model.is_active == True,
                    self.model.is_deleted == False,
                    AccountType.name == account_type,
                )
            )
            .order_by(self.model.code.asc())
        )
        result = await self.db.execute(query)
        return result.scalars().all()

    async def has_posted_lines(self, account_id: UUID) -> bool:
        """Check if account has any posted journal lines."""
        query = (
            select(func.count(JournalLine.id))
            .join(JournalEntry, JournalLine.journal_id == JournalEntry.id)
            .where(
                and_(
                    JournalLine.account_id == account_id,
                    JournalEntry.status == JournalStatusEnum.POSTED.value,
                )
            )
        )
        result = await self.db.execute(query)
        count = result.scalar() or 0
        return count > 0


class CostCenterRepository(BaseRepository[CostCenter]):
    """Repository for cost center data access."""

    def __init__(self, db: AsyncSession):
        super().__init__(CostCenter, db)

    async def get_by_code(self, school_id: UUID, code: str) -> Optional[CostCenter]:
        """Fetch cost center by code within a school."""
        query = (
            select(self.model)
            .where(
                and_(
                    self.model.school_id == school_id,
                    self.model.code == code,
                    self.model.is_deleted == False,
                )
            )
        )
        result = await self.db.execute(query)
        return result.scalar_one_or_none()

    async def get_active(self, school_id: UUID) -> List[CostCenter]:
        """Fetch all active cost centers for a school."""
        query = (
            select(self.model)
            .where(
                and_(
                    self.model.school_id == school_id,
                    self.model.is_active == True,
                    self.model.is_deleted == False,
                )
            )
            .order_by(self.model.code.asc())
        )
        result = await self.db.execute(query)
        return result.scalars().all()


class JournalEntryRepository(BaseRepository[JournalEntry]):
    """Repository for journal entry data access."""

    def __init__(self, db: AsyncSession):
        super().__init__(JournalEntry, db)

    async def get_by_reference(self, school_id: UUID, reference: str) -> Optional[JournalEntry]:
        """Fetch journal by reference within a school."""
        query = (
            select(self.model)
            .where(
                and_(
                    self.model.school_id == school_id,
                    self.model.reference == reference,
                    self.model.is_deleted == False,
                )
            )
            .options(selectinload(JournalEntry.lines))
        )
        result = await self.db.execute(query)
        return result.scalar_one_or_none()

    async def get_with_lines(self, journal_id: UUID) -> Optional[JournalEntry]:
        """Fetch journal with all lines eagerly loaded."""
        query = (
            select(self.model)
            .where(self.model.id == journal_id)
            .options(selectinload(JournalEntry.lines).selectinload(JournalLine.account))
        )
        result = await self.db.execute(query)
        return result.scalar_one_or_none()

    async def get_draft_by_period(self, period_id: UUID) -> List[JournalEntry]:
        """Fetch all DRAFT journals in a period."""
        query = (
            select(self.model)
            .where(
                and_(
                    self.model.period_id == period_id,
                    self.model.status == JournalStatusEnum.DRAFT.value,
                    self.model.is_deleted == False,
                )
            )
            .order_by(self.model.created_at.desc())
        )
        result = await self.db.execute(query)
        return result.scalars().all()

    async def get_posted_by_period(self, period_id: UUID) -> List[JournalEntry]:
        """Fetch all POSTED journals in a period."""
        query = (
            select(self.model)
            .where(
                and_(
                    self.model.period_id == period_id,
                    self.model.status == JournalStatusEnum.POSTED.value,
                    self.model.is_deleted == False,
                )
            )
            .order_by(self.model.transaction_date.asc())
        )
        result = await self.db.execute(query)
        return result.scalars().all()

    async def get_by_date_range(
        self, school_id: UUID, from_date: date, to_date: date, status: Optional[str] = None
    ) -> List[JournalEntry]:
        """Fetch journals in a date range, optionally filtered by status."""
        filters = [
            self.model.school_id == school_id,
            self.model.transaction_date >= from_date,
            self.model.transaction_date <= to_date,
            self.model.is_deleted == False,
        ]
        if status:
            filters.append(self.model.status == status)

        query = (
            select(self.model)
            .where(and_(*filters))
            .options(selectinload(JournalEntry.lines))
            .order_by(self.model.transaction_date.asc(), self.model.created_at.asc())
        )
        result = await self.db.execute(query)
        return result.scalars().all()


class JournalLineRepository(BaseRepository[JournalLine]):
    """Repository for journal line data access."""

    def __init__(self, db: AsyncSession):
        super().__init__(JournalLine, db)

    async def get_by_journal(self, journal_id: UUID) -> List[JournalLine]:
        """Fetch all lines in a journal."""
        query = (
            select(self.model)
            .where(self.model.journal_id == journal_id)
            .options(selectinload(JournalLine.account), selectinload(JournalLine.cost_center))
            .order_by(self.model.created_at.asc())
        )
        result = await self.db.execute(query)
        return result.scalars().all()

    async def get_by_account_and_period(
        self, account_id: UUID, period_id: UUID, posted_only: bool = True
    ) -> List[JournalLine]:
        """Fetch all lines for an account in a period."""
        filters = [self.model.account_id == account_id]
        if posted_only:
            filters.append(JournalEntry.status == JournalStatusEnum.POSTED.value)

        query = (
            select(self.model)
            .join(JournalEntry, self.model.journal_id == JournalEntry.id)
            .where(and_(JournalEntry.period_id == period_id, *filters))
            .order_by(JournalEntry.transaction_date.asc())
        )
        result = await self.db.execute(query)
        return result.scalars().all()


class AccountBalanceRepository(BaseRepository[AccountBalance]):
    """Repository for account balance data access."""

    def __init__(self, db: AsyncSession):
        super().__init__(AccountBalance, db)

    async def get_for_account_period(
        self, account_id: UUID, period_id: UUID, cost_center_id: Optional[UUID] = None
    ) -> Optional[AccountBalance]:
        """Fetch balance for (account, period, cost_center)."""
        filters = [
            self.model.account_id == account_id,
            self.model.period_id == period_id,
            self.model.is_deleted == False,
        ]
        if cost_center_id:
            filters.append(self.model.cost_center_id == cost_center_id)
        else:
            filters.append(self.model.cost_center_id == None)

        query = select(self.model).where(and_(*filters))
        result = await self.db.execute(query)
        return result.scalar_one_or_none()

    async def get_by_period(self, school_id: UUID, period_id: UUID) -> List[AccountBalance]:
        """Fetch all balances in a period for a school."""
        query = (
            select(self.model)
            .where(
                and_(
                    self.model.school_id == school_id,
                    self.model.period_id == period_id,
                    self.model.is_deleted == False,
                )
            )
            .options(
                selectinload(AccountBalance.account),
                selectinload(AccountBalance.cost_center),
            )
            .order_by(self.model.account_id.asc())
        )
        result = await self.db.execute(query)
        return result.scalars().all()

    async def get_account_balances_by_period(
        self, account_id: UUID, period_id: UUID
    ) -> List[AccountBalance]:
        """Fetch all balance records for an account in a period (across all cost centers)."""
        query = (
            select(self.model)
            .where(
                and_(
                    self.model.account_id == account_id,
                    self.model.period_id == period_id,
                    self.model.is_deleted == False,
                )
            )
            .order_by(self.model.cost_center_id.asc())
        )
        result = await self.db.execute(query)
        return result.scalars().all()

    async def get_total_balance_for_period(
        self, school_id: UUID, period_id: UUID
    ) -> Tuple[Decimal, Decimal]:
        """Fetch total debits and credits for a period."""
        query = select(
            func.coalesce(func.sum(self.model.debit_movement), 0).label("total_debits"),
            func.coalesce(func.sum(self.model.credit_movement), 0).label("total_credits"),
        ).where(
            and_(
                self.model.school_id == school_id,
                self.model.period_id == period_id,
                self.model.is_deleted == False,
            )
        )
        result = await self.db.execute(query)
        row = result.first()
        return (
            Decimal(str(row[0])) if row else Decimal("0.0000"),
            Decimal(str(row[1])) if row else Decimal("0.0000"),
        )
