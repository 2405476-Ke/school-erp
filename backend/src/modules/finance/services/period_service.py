"""
Period Service: Accounting period management and closure.

Implements close_accounting_period() to:
1. Verify no DRAFT journals
2. Lock period (no future posts allowed)
3. Calculate closing balances and create opening balances for next period
"""
from datetime import datetime, timezone
from decimal import Decimal
from uuid import UUID

from sqlalchemy import and_, func, select
from sqlalchemy.ext.asyncio import AsyncSession

from src.modules.finance.models.ledger import (
    Account,
    AccountBalance,
    AccountingPeriod,
    JournalEntry,
    JournalLine,
    PeriodClosure,
)
from src.modules.finance.services.reporting_service import ReportingService
from src.shared.exceptions import ValidationError, NotFoundError


class PeriodService:
    """
    Service for accounting period management.
    Handles period closure and rollforward of balances.
    """

    def __init__(self, db: AsyncSession):
        self.db = db
        self.reporting_service = ReportingService(db)

    async def close_accounting_period(
        self,
        school_id: UUID,
        period_id: UUID,
        user_id: UUID,
        closing_note: str = None,
    ) -> dict:
        """
        Close an accounting period.

        REAL BUSINESS LOGIC:
        1. Verify period exists and is OPEN
        2. Check for DRAFT journals (must not exist)
        3. Generate trial balance (verify balanced)
        4. Lock period (set status=CLOSED)
        5. For each account: Create next period's opening balance
        6. Create PeriodClosure record
        7. Return summary

        Args:
            school_id: School context
            period_id: Period to close
            user_id: User closing period
            closing_note: Optional note

        Returns:
            Dict with closure details

        Raises:
            ValidationError: If DRAFT journals exist or period already closed
            NotFoundError: If period not found
        """
        # 1. Fetch period
        period_query = select(AccountingPeriod).where(
            and_(
                AccountingPeriod.id == period_id,
                AccountingPeriod.school_id == school_id,
            )
        )
        period_result = await self.db.execute(period_query)
        period = period_result.scalar_one_or_none()

        if not period:
            raise NotFoundError(f"Period {period_id} not found")

        if period.status == "CLOSED":
            raise ValidationError(f"Period {period.period_name} is already closed")

        # 2. Check for DRAFT journals
        draft_count_query = (
            select(func.count(JournalEntry.id))
            .where(
                and_(
                    JournalEntry.accounting_period_id == period_id,
                    JournalEntry.status == "DRAFT",
                )
            )
        )
        draft_count_result = await self.db.execute(draft_count_query)
        draft_count = draft_count_result.scalar()

        if draft_count and draft_count > 0:
            raise ValidationError(
                f"Cannot close period with {draft_count} DRAFT journal entries. "
                f"All entries must be posted or reversed."
            )

        # 3. Generate trial balance to verify GL is balanced
        trial_balance = await self.reporting_service.generate_trial_balance(
            school_id, period_id, user_id
        )

        if not trial_balance.is_balanced:
            raise ValidationError(
                f"Cannot close period: Trial balance not balanced. "
                f"Debits: {trial_balance.total_debits}, Credits: {trial_balance.total_credits}"
            )

        # 4. Identify or create retained earnings account
        retained_earnings_account = await self._get_or_create_retained_earnings_account(
            school_id
        )

        # 5. Calculate retained earnings for the period
        financial_year = period.financial_year
        income_statement = await self.reporting_service.generate_income_statement(
            school_id,
            financial_year.start_date,
            period.end_date,
            user_id,
        )
        retained_earnings_amount = income_statement.net_surplus_deficit

        # 6. Lock period
        period.status = "CLOSED"
        period.is_closed = True

        # 7. Get next period (even if it's in the next financial year)
        # BR-FIN-004: Ensure we carry forward across financial years for Year-End close
        next_period_query = select(AccountingPeriod).where(
            and_(
                AccountingPeriod.school_id == school_id,
                AccountingPeriod.start_date > period.end_date,
            )
        ).order_by(AccountingPeriod.start_date).limit(1)

        next_period_result = await self.db.execute(next_period_query)
        next_period = next_period_result.scalar_one_or_none()

        # 8. Rollforward balances: Each account's closing balance becomes next period's opening
        if next_period:
            await self._rollforward_balances(period, next_period, retained_earnings_account)

        # 9. Create PeriodClosure record
        period_closure = PeriodClosure(
            accounting_period_id=period_id,
            closed_by_id=user_id,
            closed_at=datetime.now(timezone.utc),
            retained_earnings_account_id=retained_earnings_account.id,
            closing_note=closing_note,
        )
        self.db.add(period_closure)

        # 10. Commit
        await self.db.commit()

        return {
            "period_id": period_id,
            "period_name": period.period_name,
            "closed_at": period_closure.closed_at,
            "closed_by_id": user_id,
            "retained_earnings_account_id": retained_earnings_account.id,
            "retained_earnings_amount": retained_earnings_amount,
            "opening_balances_created": len([
                acc for acc in await self._get_all_accounts(school_id)
                if next_period
            ]),
            "message": f"Period {period.period_name} closed successfully. "
                       f"Retained earnings: {retained_earnings_amount}",
        }

    async def _get_or_create_retained_earnings_account(
        self, school_id: UUID
    ) -> Account:
        """
        Get or create retained earnings account (Equity type).

        Standard account code: 3100 (Retained Earnings).
        """
        # Try to find existing retained earnings account
        query = select(Account).where(
            and_(
                Account.school_id == school_id,
                Account.code == "3100",
            )
        )
        result = await self.db.execute(query)
        account = result.scalar_one_or_none()

        if account:
            return account

        # If not found, raise error (admin must create equity accounts)
        raise NotFoundError(
            f"Retained earnings account (code 3100) not found. "
            f"Admin must create equity accounts in Chart of Accounts."
        )

    async def _get_all_accounts(self, school_id: UUID) -> list:
        """Get all active accounts for school."""
        query = select(Account).where(
            and_(
                Account.school_id == school_id,
                Account.is_active == True,
                Account.is_deleted == False,
            )
        )
        result = await self.db.execute(query)
        return result.scalars().all()

    async def _rollforward_balances(
        self,
        closing_period: AccountingPeriod,
        opening_period: AccountingPeriod,
        retained_earnings_account: Account,
        is_year_end: bool = False,
        retained_earnings_amount: Decimal = Decimal('0.00'),
    ) -> None:
        """
        Rollforward closing balances from one period to next period's opening balances.
        BR-FIN-004: If is_year_end, zero out P&L accounts (Revenue & Expenses) 
        and roll the net amount into Retained Earnings.
        """
        closing_balances_query = select(AccountBalance).where(
            AccountBalance.period_id == closing_period.id
        )
        closing_balances_result = await self.db.execute(closing_balances_query)
        closing_balances = closing_balances_result.scalars().all()
        
        # We need to know account types to zero out P&L
        accounts_query = select(Account).where(Account.school_id == closing_period.school_id)
        accounts = (await self.db.execute(accounts_query)).scalars().all()
        # Assume Category is eagerly loaded or we can check category type. We will just look at root categories
        # For simplicity, if we don't have category type loaded, we assume codes 4xxx are Revenue and 5xxx are Expenses.
        
        opening_balances = []
        for cb in closing_balances:
            account = next((a for a in accounts if a.id == cb.account_id), None)
            if not account: continue
            
            # P&L check: if year end, Revenue (4xxx) and Expenses (5xxx) do NOT carry forward
            if is_year_end and (account.code.startswith("4") or account.code.startswith("5")):
                carried_balance = Decimal('0.00')
            else:
                carried_balance = cb.closing_balance
                
            # If this is the retained earnings account and it's year end, add the net income
            if is_year_end and cb.account_id == retained_earnings_account.id:
                carried_balance += retained_earnings_amount
                
            opening_balances.append(
                AccountBalance(
                    account_id=cb.account_id,
                    period_id=opening_period.id,
                    opening_balance=carried_balance,
                    debit_movement=Decimal('0.00'),
                    credit_movement=Decimal('0.00'),
                    closing_balance=carried_balance,
                )
            )
            
        self.db.add_all(opening_balances)

    async def reopen_accounting_period(
        self,
        school_id: UUID,
        period_id: UUID,
        user_id: UUID,
    ) -> dict:
        """
        Reopen a closed period (for corrections).

        CAUTION: Can only reopen if next period is not yet closed.

        Args:
            school_id: School context
            period_id: Period to reopen
            user_id: User reopening period

        Returns:
            Dict confirming reopen
        """
        # Fetch period
        period_query = select(AccountingPeriod).where(
            and_(
                AccountingPeriod.id == period_id,
                AccountingPeriod.school_id == school_id,
            )
        )
        period_result = await self.db.execute(period_query)
        period = period_result.scalar_one_or_none()

        if not period:
            raise NotFoundError(f"Period {period_id} not found")

        if period.status != "CLOSED":
            raise ValidationError(f"Period {period.period_name} is not closed")

        # Check if next period is closed
        next_period_query = select(AccountingPeriod).where(
            and_(
                AccountingPeriod.financial_year_id == period.financial_year_id,
                AccountingPeriod.start_date > period.end_date,
            )
        ).order_by(AccountingPeriod.start_date).limit(1)

        next_period_result = await self.db.execute(next_period_query)
        next_period = next_period_result.scalar_one_or_none()

        if next_period and next_period.status == "CLOSED":
            raise ValidationError(
                f"Cannot reopen period: Next period {next_period.period_name} is already closed. "
                f"Reopen next period first."
            )

        # Reopen
        period.status = "OPEN"

        # Delete PeriodClosure record
        closure_query = select(PeriodClosure).where(
            PeriodClosure.accounting_period_id == period_id
        )
        closure_result = await self.db.execute(closure_query)
        closure = closure_result.scalar_one_or_none()

        if closure:
            await self.db.delete(closure)

        await self.db.commit()

        return {
            "period_id": period_id,
            "period_name": period.period_name,
            "status": "OPEN",
            "reopened_by_id": user_id,
            "reopened_at": datetime.now(timezone.utc),
            "message": f"Period {period.period_name} reopened for corrections.",
        }
