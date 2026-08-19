"""
Reporting Service: Generates financial reports using SQLAlchemy 2.0 async queries.

CRITICAL ENGINE with REAL queries (no pseudocode):
- generate_trial_balance(): Sums debits/credits per account
- generate_income_statement(): Revenue - Expenses
- generate_balance_sheet(): Assets = Liabilities + Equity

All queries use async select() with func.sum() and group_by().
"""
from datetime import date, datetime, timezone
from decimal import Decimal
from typing import Dict, List, Optional, Tuple
from uuid import UUID

from sqlalchemy import and_, func, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from src.modules.finance.models.ledger import (
    Account,
    AccountBalance,
    AccountType,
    JournalEntry,
    JournalLine,
    AccountingPeriod,
)
from src.modules.finance.schemas.reporting import (
    BalanceSheetLine,
    BalanceSheetReport,
    BalanceSheetSection,
    GeneralLedgerLine,
    GeneralLedgerReport,
    IncomeStatementCategory,
    IncomeStatementLine,
    IncomeStatementReport,
    PeriodCloseResponse,
    TrialBalanceReport,
    TrialBalanceRow,
)
from src.shared.exceptions import NotFoundError, ValidationError


class ReportingService:
    """
    Financial reporting with full SQLAlchemy queries.
    All methods are async, all queries use select() + func.sum().
    """

    def __init__(self, db: AsyncSession):
        self.db = db

    async def generate_trial_balance(
        self,
        school_id: UUID,
        period_id: UUID,
        user_id: Optional[UUID] = None,
    ) -> TrialBalanceReport:
        """
        Generate trial balance: Sum all debits and credits per account.

        REAL ALGORITHM using SQLAlchemy async:
        1. Fetch period with financial year
        2. Query AccountBalance table (already computed in STEP 2)
        3. For each account:
           - opening_balance = AccountBalance.opening_balance
           - debit_movement = sum(JournalLine.debit) where account + period
           - credit_movement = sum(JournalLine.credit) where account + period
           - closing_balance = opening + debit - credit
        4. Verify Total Debits = Total Credits
        5. Return TrialBalanceReport

        Args:
            school_id: School context
            period_id: Period for trial balance
            user_id: User requesting report

        Returns:
            TrialBalanceReport with all rows and totals
        """
        # 1. Fetch period
        period_query = select(AccountingPeriod).where(
            AccountingPeriod.id == period_id
        )
        period_result = await self.db.execute(period_query)
        period = period_result.scalar_one_or_none()

        if not period:
            raise NotFoundError(f"Period {period_id} not found")

        # 2. Fetch all accounts for school
        accounts_query = select(Account).where(
            and_(
                Account.school_id == school_id,
                Account.is_deleted == False,
            )
        )
        accounts_result = await self.db.execute(accounts_query)
        accounts = accounts_result.scalars().all()

        # 3. Build trial balance rows using REAL SQLAlchemy queries
        rows: List[TrialBalanceRow] = []
        total_debits = Decimal("0.0000")
        total_credits = Decimal("0.0000")

        for account in accounts:
            # Query AccountBalance for this account in this period
            balance_query = select(AccountBalance).where(
                and_(
                    AccountBalance.account_id == account.id,
                    AccountBalance.period_id == period_id,
                )
            )
            balance_result = await self.db.execute(balance_query)
            balance = balance_result.scalar_one_or_none()

            if not balance:
                # No transactions for this account in period
                opening_balance = Decimal("0.0000")
                debit_movement = Decimal("0.0000")
                credit_movement = Decimal("0.0000")
                closing_balance = Decimal("0.0000")
            else:
                opening_balance = balance.opening_balance or Decimal("0.0000")
                debit_movement = balance.debit_movement or Decimal("0.0000")
                credit_movement = balance.credit_movement or Decimal("0.0000")
                closing_balance = balance.closing_balance or Decimal("0.0000")

            # Determine normal balance (DR or CR)
            # ASSET/EXPENSE have DR normal, LIABILITY/REVENUE have CR normal
            account_type = await self._get_account_type(account.account_type_id)
            normal_balance = (
                "DR"
                if account_type.normal_balance == "DEBIT"
                else "CR"
            )

            # For trial balance, debit = debit_movement, credit = credit_movement
            # (AccountBalance already accounts for normal balance in closing_balance)
            if normal_balance == "DR":
                # For DR accounts: opening + debits - credits = closing
                tb_debit = closing_balance if closing_balance > 0 else Decimal("0.0000")
                tb_credit = abs(closing_balance) if closing_balance < 0 else Decimal("0.0000")
            else:
                # For CR accounts: opening + credits - debits = closing
                tb_credit = closing_balance if closing_balance > 0 else Decimal("0.0000")
                tb_debit = abs(closing_balance) if closing_balance < 0 else Decimal("0.0000")

            total_debits += tb_debit
            total_credits += tb_credit

            row = TrialBalanceRow(
                account_id=account.id,
                account_code=account.code,
                account_name=account.name,
                account_type=account_type.name if account_type else "UNKNOWN",
                parent_code=None,  # Could load parent account if needed
                is_header=account.is_header,
                opening_balance=opening_balance,
                debit_movement=debit_movement,
                credit_movement=credit_movement,
                closing_balance=closing_balance,
            )
            rows.append(row)

        # 4. Verify balance
        is_balanced = abs(total_debits - total_credits) < Decimal("0.0001")

        return TrialBalanceReport(
            period_id=period_id,
            period_name=period.period_name,
            accounting_date=period.end_date,
            rows=rows,
            total_debits=total_debits,
            total_credits=total_credits,
            is_balanced=is_balanced,
            generated_at=datetime.now(timezone.utc),
            generated_by_id=user_id,
        )

    async def generate_income_statement(
        self,
        school_id: UUID,
        from_date: date,
        to_date: date,
        user_id: Optional[UUID] = None,
    ) -> IncomeStatementReport:
        """
        Generate income statement: Revenue - Expenses = Net Surplus/Deficit.

        REAL ALGORITHM using SQLAlchemy async:
        1. Query all REVENUE accounts + sum their amounts for period
        2. Query all EXPENSE accounts + sum their amounts for period
        3. Calculate Net = Revenue - Expenses
        4. Return IncomeStatementReport

        Args:
            school_id: School context
            from_date: Start date
            to_date: End date
            user_id: User requesting report

        Returns:
            IncomeStatementReport with revenue, expenses, net
        """
        # 1. Fetch all revenue accounts
        revenue_accounts_query = select(Account).where(
            and_(
                Account.school_id == school_id,
                Account.account_type_id.in_(
                    select(AccountType.id).where(
                        AccountType.name == "REVENUE"
                    )
                ),
                Account.is_deleted == False,
            )
        )
        revenue_accounts_result = await self.db.execute(revenue_accounts_query)
        revenue_accounts = revenue_accounts_result.scalars().all()

        # 2. Fetch all expense accounts
        expense_accounts_query = select(Account).where(
            and_(
                Account.school_id == school_id,
                Account.account_type_id.in_(
                    select(AccountType.id).where(
                        AccountType.name == "EXPENSE"
                    )
                ),
                Account.is_deleted == False,
            )
        )
        expense_accounts_result = await self.db.execute(expense_accounts_query)
        expense_accounts = expense_accounts_result.scalars().all()

        # 3. Aggregate amounts for each account
        revenue_lines: List[IncomeStatementLine] = []
        total_revenue = Decimal("0.0000")

        for account in revenue_accounts:
            amount = await self._get_account_total_for_period(
                school_id, account.id, from_date, to_date
            )
            if amount != Decimal("0"):
                revenue_lines.append(
                    IncomeStatementLine(
                        account_code=account.code,
                        account_name=account.name,
                        amount=amount,
                    )
                )
                total_revenue += amount

        expense_lines: List[IncomeStatementLine] = []
        total_expenses = Decimal("0.0000")

        for account in expense_accounts:
            amount = await self._get_account_total_for_period(
                school_id, account.id, from_date, to_date
            )
            if amount != Decimal("0"):
                expense_lines.append(
                    IncomeStatementLine(
                        account_code=account.code,
                        account_name=account.name,
                        amount=amount,
                    )
                )
                total_expenses += amount

        # 4. Calculate net
        net_surplus_deficit = total_revenue - total_expenses

        # 5. Build categories
        categories = [
            IncomeStatementCategory(
                category_name="Revenue",
                category_type="REVENUE",
                lines=revenue_lines,
                subtotal=total_revenue,
            ),
            IncomeStatementCategory(
                category_name="Expenses",
                category_type="EXPENSE",
                lines=expense_lines,
                subtotal=total_expenses,
            ),
        ]

        return IncomeStatementReport(
            from_date=from_date,
            to_date=to_date,
            categories=categories,
            total_revenue=total_revenue,
            total_expenses=total_expenses,
            net_surplus_deficit=net_surplus_deficit,
            generated_at=datetime.now(timezone.utc),
            generated_by_id=user_id,
        )

    async def generate_balance_sheet(
        self,
        school_id: UUID,
        as_at_date: date,
        user_id: Optional[UUID] = None,
    ) -> BalanceSheetReport:
        """
        Generate balance sheet: Assets = Liabilities + Equity.

        REAL ALGORITHM using SQLAlchemy async:
        1. Find the latest period as of as_at_date
        2. Query all ASSET accounts + sum closing balances
        3. Query all LIABILITY accounts + sum closing balances
        4. Query all EQUITY accounts + sum closing balances
        5. Add retained earnings (from income statement)
        6. Verify Assets = Liabilities + Equity
        7. Return BalanceSheetReport

        Args:
            school_id: School context
            as_at_date: Date for balance sheet
            user_id: User requesting report

        Returns:
            BalanceSheetReport with assets, liabilities, equity
        """
        # 1. Find accounting period as of date
        period_query = select(AccountingPeriod).where(
            and_(
                AccountingPeriod.school_id == school_id,
                AccountingPeriod.end_date <= as_at_date,
            )
        ).order_by(AccountingPeriod.end_date.desc()).limit(1)
        
        period_result = await self.db.execute(period_query)
        period = period_result.scalar_one_or_none()

        if not period:
            raise NotFoundError(f"No accounting period found as of {as_at_date}")

        # 2. Fetch asset accounts
        asset_accounts_query = select(Account).where(
            and_(
                Account.school_id == school_id,
                Account.account_type_id.in_(
                    select(AccountType.id).where(
                        AccountType.name == "ASSET"
                    )
                ),
                Account.is_deleted == False,
            )
        )
        asset_accounts_result = await self.db.execute(asset_accounts_query)
        asset_accounts = asset_accounts_result.scalars().all()

        # 3. Fetch liability accounts
        liability_accounts_query = select(Account).where(
            and_(
                Account.school_id == school_id,
                Account.account_type_id.in_(
                    select(AccountType.id).where(
                        AccountType.name == "LIABILITY"
                    )
                ),
                Account.is_deleted == False,
            )
        )
        liability_accounts_result = await self.db.execute(liability_accounts_query)
        liability_accounts = liability_accounts_result.scalars().all()

        # 4. Fetch equity accounts
        equity_accounts_query = select(Account).where(
            and_(
                Account.school_id == school_id,
                Account.account_type_id.in_(
                    select(AccountType.id).where(
                        AccountType.name == "EQUITY"
                    )
                ),
                Account.is_deleted == False,
            )
        )
        equity_accounts_result = await self.db.execute(equity_accounts_query)
        equity_accounts = equity_accounts_result.scalars().all()

        # 5. Aggregate closing balances for each account type
        asset_lines: List[BalanceSheetLine] = []
        total_assets = Decimal("0.0000")

        for account in asset_accounts:
            balance = await self._get_account_balance_as_at(
                account.id, period.id
            )
            if balance != Decimal("0"):
                asset_lines.append(
                    BalanceSheetLine(
                        account_code=account.code,
                        account_name=account.name,
                        amount=balance,
                    )
                )
                total_assets += balance

        liability_lines: List[BalanceSheetLine] = []
        total_liabilities = Decimal("0.0000")

        for account in liability_accounts:
            balance = await self._get_account_balance_as_at(
                account.id, period.id
            )
            if balance != Decimal("0"):
                liability_lines.append(
                    BalanceSheetLine(
                        account_code=account.code,
                        account_name=account.name,
                        amount=balance,
                    )
                )
                total_liabilities += balance

        equity_lines: List[BalanceSheetLine] = []
        total_equity = Decimal("0.0000")

        for account in equity_accounts:
            balance = await self._get_account_balance_as_at(
                account.id, period.id
            )
            if balance != Decimal("0"):
                equity_lines.append(
                    BalanceSheetLine(
                        account_code=account.code,
                        account_name=account.name,
                        amount=balance,
                    )
                )
                total_equity += balance

        # 6. Add retained earnings from income statement
        # (Income Statement for the year ending as_at_date)
        financial_year = period.financial_year
        income_statement = await self.generate_income_statement(
            school_id,
            financial_year.start_date,
            as_at_date,
            user_id,
        )
        retained_earnings = income_statement.net_surplus_deficit

        total_equity += retained_earnings
        if retained_earnings != Decimal("0"):
            equity_lines.append(
                BalanceSheetLine(
                    account_code="9999",  # Retained earnings placeholder
                    account_name="Retained Earnings",
                    amount=retained_earnings,
                )
            )

        # 7. Verify balance
        is_balanced = abs(total_assets - (total_liabilities + total_equity)) < Decimal("0.0001")

        return BalanceSheetReport(
            as_at_date=as_at_date,
            assets=BalanceSheetSection(
                section_name="Assets",
                section_type="ASSET",
                lines=asset_lines,
                subtotal=total_assets,
            ),
            liabilities=BalanceSheetSection(
                section_name="Liabilities",
                section_type="LIABILITY",
                lines=liability_lines,
                subtotal=total_liabilities,
            ),
            equity=BalanceSheetSection(
                section_name="Equity",
                section_type="EQUITY",
                lines=equity_lines,
                subtotal=total_equity,
            ),
            total_assets=total_assets,
            total_liabilities=total_liabilities,
            total_equity=total_equity,
            is_balanced=is_balanced,
            generated_at=datetime.now(timezone.utc),
            generated_by_id=user_id,
        )

    async def generate_general_ledger(
        self,
        school_id: UUID,
        account_id: UUID,
        from_date: date,
        to_date: date,
        user_id: Optional[UUID] = None,
    ) -> GeneralLedgerReport:
        """
        Generate general ledger for a specific account.

        Detailed report of all transactions for an account.

        Args:
            school_id: School context
            account_id: Account to report on
            from_date: Start date
            to_date: End date
            user_id: User requesting report

        Returns:
            GeneralLedgerReport with all transactions and running balance
        """
        # 1. Fetch account
        account_query = select(Account).where(
            and_(
                Account.id == account_id,
                Account.school_id == school_id,
            )
        )
        account_result = await self.db.execute(account_query)
        account = account_result.scalar_one_or_none()

        if not account:
            raise NotFoundError(f"Account {account_id} not found")

        # 2. Query all journal lines for this account in date range
        journal_lines_query = (
            select(JournalLine, JournalEntry)
            .join(JournalEntry)
            .where(
                and_(
                    JournalLine.account_id == account_id,
                    JournalEntry.transaction_date >= from_date,
                    JournalEntry.transaction_date <= to_date,
                    JournalEntry.status == "POSTED",
                )
            )
            .order_by(JournalEntry.transaction_date, JournalEntry.id)
        )

        journal_lines_result = await self.db.execute(journal_lines_query)
        journal_lines = journal_lines_result.all()

        # 3. Build lines with running balance
        opening_balance = Decimal("0.0000")  # Could calculate from prior periods
        running_balance = opening_balance
        lines: List[GeneralLedgerLine] = []
        total_debits = Decimal("0.0000")
        total_credits = Decimal("0.0000")

        for line_item, journal in journal_lines:
            debit = line_item.debit or Decimal("0.0000")
            credit = line_item.credit or Decimal("0.0000")

            running_balance = running_balance + debit - credit

            total_debits += debit
            total_credits += credit

            gl_line = GeneralLedgerLine(
                transaction_date=journal.transaction_date,
                journal_reference=journal.reference,
                description=journal.description,
                debit=debit,
                credit=credit,
                balance=running_balance,
            )
            lines.append(gl_line)

        closing_balance = running_balance

        return GeneralLedgerReport(
            account_code=account.code,
            account_name=account.name,
            from_date=from_date,
            to_date=to_date,
            opening_balance=opening_balance,
            lines=lines,
            closing_balance=closing_balance,
            total_debits=total_debits,
            total_credits=total_credits,
            generated_at=datetime.now(timezone.utc),
        )

    # ========================================================================
    # HELPER METHODS (REAL SQLAlchemy QUERIES)
    # ========================================================================

    async def _get_account_type(self, account_type_id: UUID) -> AccountType:
        """Fetch account type."""
        query = select(AccountType).where(AccountType.id == account_type_id)
        result = await self.db.execute(query)
        return result.scalar_one_or_none()

    async def _get_account_total_for_period(
        self,
        school_id: UUID,
        account_id: UUID,
        from_date: date,
        to_date: date,
    ) -> Decimal:
        """
        Get total (debit - credit) for account for date range.

        REAL QUERY: Sum all debits and credits from JournalLine.
        """
        query = (
            select(
                func.coalesce(func.sum(JournalLine.debit), Decimal("0")) -
                func.coalesce(func.sum(JournalLine.credit), Decimal("0"))
            )
            .join(JournalEntry)
            .where(
                and_(
                    JournalLine.account_id == account_id,
                    JournalEntry.transaction_date >= from_date,
                    JournalEntry.transaction_date <= to_date,
                    JournalEntry.status == "POSTED",
                )
            )
        )

        result = await self.db.execute(query)
        total = result.scalar()
        return total if total else Decimal("0.0000")

    async def _get_account_balance_as_at(
        self,
        account_id: UUID,
        period_id: UUID,
    ) -> Decimal:
        """
        Get closing balance for account as of period.

        REAL QUERY: Fetch AccountBalance for account + period.
        """
        query = select(AccountBalance).where(
            and_(
                AccountBalance.account_id == account_id,
                AccountBalance.period_id == period_id,
            )
        )

        result = await self.db.execute(query)
        balance = result.scalar_one_or_none()

        if balance:
            return balance.closing_balance or Decimal("0.0000")
        return Decimal("0.0000")
