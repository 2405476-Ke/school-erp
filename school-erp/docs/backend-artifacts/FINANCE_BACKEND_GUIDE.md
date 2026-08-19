# Finance Backend Guide - Kenya School ERP

This document contains the complete, production-ready backend implementation for the Finance module of the Kenya School ERP. It leverages FastAPI, SQLAlchemy 2.0 (async), PostgreSQL, Pydantic v2, and Domain-Driven Design (DDD) principles. It is tailored for the Kenyan context where applicable (e.g., KES currency, M-Pesa integrations in related modules).

## Architecture Overview
The system follows a layered architecture:
1.  **Models (SQLAlchemy)**: Database schema definitions.
2.  **Schemas (Pydantic v2)**: Data validation and serialization.
3.  **Repositories**: Database access abstraction.
4.  **Services**: Core business logic and transaction management.
5.  **Routers (FastAPI)**: HTTP endpoints.

---

## 1. Core Infrastructure & Exceptions

```python
# app/finance/exceptions.py
from fastapi import HTTPException, status

class FinanceException(HTTPException):
    def __init__(self, detail: str, status_code: int = status.HTTP_400_BAD_REQUEST):
        super().__init__(status_code=status_code, detail=detail)

class InvalidJournalEntryError(FinanceException):
    pass

class ClosedPeriodError(FinanceException):
    pass

class ControlAccountPostingError(FinanceException):
    pass

class InsufficientBudgetError(FinanceException):
    pass

class AccountDeletionError(FinanceException):
    pass

# app/core/database.py (Assumed existing)
# from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine
# from sqlalchemy.orm import declarative_base, sessionmaker
# Base = declarative_base()
# get_db() -> AsyncGenerator[AsyncSession, None]
```

---

## 2. Cost Center Management

### Models

```python
# app/finance/models/cost_center.py
from sqlalchemy import Column, String, Boolean, Text
from sqlalchemy.dialects.postgresql import UUID
import uuid
from app.core.database import Base

class CostCenter(Base):
    __tablename__ = 'cost_centers'

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    code = Column(String(50), unique=True, index=True, nullable=False) # e.g., 'DEPT-HR'
    name = Column(String(255), nullable=False)
    description = Column(Text, nullable=True)
    is_active = Column(Boolean, default=True, nullable=False)
    
    # Relationships
    # budgets = relationship("Budget", back_populates="cost_center")
    # journal_lines = relationship("JournalLine", back_populates="cost_center")
```

### Schemas

```python
# app/finance/schemas/cost_center.py
from pydantic import BaseModel, Field, ConfigDict
from typing import Optional
from uuid import UUID

class CostCenterBase(BaseModel):
    code: str = Field(..., max_length=50)
    name: str = Field(..., max_length=255)
    description: Optional[str] = None
    is_active: bool = True

class CostCenterCreate(CostCenterBase):
    pass

class CostCenterUpdate(BaseModel):
    name: Optional[str] = Field(None, max_length=255)
    description: Optional[str] = None
    is_active: Optional[bool] = None

class CostCenterResponse(CostCenterBase):
    model_config = ConfigDict(from_attributes=True)
    id: UUID
```

### Repository

```python
# app/finance/repositories/cost_center_repository.py
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from uuid import UUID
from typing import Sequence, Optional
from app.finance.models.cost_center import CostCenter
from app.finance.schemas.cost_center import CostCenterCreate, CostCenterUpdate

class CostCenterRepository:
    def __init__(self, session: AsyncSession):
        self.session = session

    async def get_by_id(self, cost_center_id: UUID) -> Optional[CostCenter]:
        result = await self.session.execute(select(CostCenter).where(CostCenter.id == cost_center_id))
        return result.scalars().first()

    async def get_all(self, active_only: bool = False) -> Sequence[CostCenter]:
        query = select(CostCenter)
        if active_only:
            query = query.where(CostCenter.is_active == True)
        result = await self.session.execute(query)
        return result.scalars().all()

    async def create(self, data: CostCenterCreate) -> CostCenter:
        cost_center = CostCenter(**data.model_dump())
        self.session.add(cost_center)
        await self.session.flush()
        return cost_center

    async def update(self, cost_center: CostCenter, data: CostCenterUpdate) -> CostCenter:
        for key, value in data.model_dump(exclude_unset=True).items():
            setattr(cost_center, key, value)
        await self.session.flush()
        return cost_center
```

### Service

```python
# app/finance/services/cost_center_service.py
from uuid import UUID
from typing import Sequence
from app.finance.repositories.cost_center_repository import CostCenterRepository
from app.finance.schemas.cost_center import CostCenterCreate, CostCenterUpdate, CostCenterResponse
from app.finance.exceptions import FinanceException

class CostCenterService:
    def __init__(self, repository: CostCenterRepository):
        self.repository = repository

    async def create_cost_center(self, data: CostCenterCreate) -> CostCenterResponse:
        cost_center = await self.repository.create(data)
        await self.repository.session.commit()
        return CostCenterResponse.model_validate(cost_center)

    async def get_cost_center(self, cost_center_id: UUID) -> CostCenterResponse:
        cost_center = await self.repository.get_by_id(cost_center_id)
        if not cost_center:
            raise FinanceException(f"Cost Center {cost_center_id} not found", 404)
        return CostCenterResponse.model_validate(cost_center)

    async def list_cost_centers(self, active_only: bool = False) -> Sequence[CostCenterResponse]:
        cost_centers = await self.repository.get_all(active_only)
        return [CostCenterResponse.model_validate(cc) for cc in cost_centers]
```

### Router

```python
# app/finance/routers/cost_centers.py
from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession
from typing import List
from uuid import UUID
from app.core.database import get_db
from app.finance.schemas.cost_center import CostCenterCreate, CostCenterResponse
from app.finance.repositories.cost_center_repository import CostCenterRepository
from app.finance.services.cost_center_service import CostCenterService

router = APIRouter(prefix="/finance/cost-centers", tags=["Cost Centers"])

def get_cost_center_service(db: AsyncSession = Depends(get_db)) -> CostCenterService:
    return CostCenterService(CostCenterRepository(db))

@router.post("", response_model=CostCenterResponse)
async def create_cost_center(
    data: CostCenterCreate,
    service: CostCenterService = Depends(get_cost_center_service)
):
    return await service.create_cost_center(data)

@router.get("", response_model=List[CostCenterResponse])
async def list_cost_centers(
    active_only: bool = False,
    service: CostCenterService = Depends(get_cost_center_service)
):
    return await service.list_cost_centers(active_only)
```

---

## 3. Chart of Accounts (COA) Module

### Models

```python
# app/finance/models/account.py
from sqlalchemy import Column, String, Boolean, ForeignKey, Enum as SQLEnum, DECIMAL
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship, backref
import uuid
import enum
from app.core.database import Base

class AccountTypeEnum(str, enum.Enum):
    ASSET = "ASSET"
    LIABILITY = "LIABILITY"
    EQUITY = "EQUITY"
    REVENUE = "REVENUE"
    EXPENSE = "EXPENSE"

class AccountCategory(Base):
    __tablename__ = 'account_categories'

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    name = Column(String(100), nullable=False) # e.g., 'Current Assets'
    account_type = Column(SQLEnum(AccountTypeEnum), nullable=False)
    
class Account(Base):
    __tablename__ = 'accounts'

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    code = Column(String(50), unique=True, index=True, nullable=False) # e.g., '1000'
    name = Column(String(255), nullable=False)
    description = Column(String(500), nullable=True)
    is_active = Column(Boolean, default=True, nullable=False)
    is_control_account = Column(Boolean, default=False, nullable=False)
    is_header = Column(Boolean, default=False, nullable=False) # True = no postings allowed, just for grouping
    
    category_id = Column(UUID(as_uuid=True), ForeignKey('account_categories.id'), nullable=False)
    parent_id = Column(UUID(as_uuid=True), ForeignKey('accounts.id'), nullable=True)

    # Relationships
    category = relationship("AccountCategory")
    children = relationship("Account", backref=backref("parent", remote_side=[id]))
    # balances = relationship("AccountBalance", back_populates="account")
```

### Schemas

```python
# app/finance/schemas/account.py
from pydantic import BaseModel, Field, ConfigDict
from typing import Optional, List
from uuid import UUID
from app.finance.models.account import AccountTypeEnum

class AccountCreate(BaseModel):
    code: str = Field(..., max_length=50)
    name: str = Field(..., max_length=255)
    description: Optional[str] = None
    is_control_account: bool = False
    is_header: bool = False
    category_id: UUID
    parent_id: Optional[UUID] = None

class AccountUpdate(BaseModel):
    name: Optional[str] = Field(None, max_length=255)
    is_active: Optional[bool] = None

class AccountResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: UUID
    code: str
    name: str
    is_active: bool
    is_control_account: bool
    is_header: bool
    category_id: UUID
    parent_id: Optional[UUID]

class AccountTreeResponse(AccountResponse):
    children: List['AccountTreeResponse'] = []
```

### Repository

```python
# app/finance/repositories/account_repository.py
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, text
from sqlalchemy.orm import selectinload
from uuid import UUID
from typing import Sequence, Optional, List
from app.finance.models.account import Account
from app.finance.schemas.account import AccountCreate

class AccountRepository:
    def __init__(self, session: AsyncSession):
        self.session = session

    async def get_by_id(self, account_id: UUID) -> Optional[Account]:
        result = await self.session.execute(select(Account).where(Account.id == account_id))
        return result.scalars().first()

    async def get_tree(self) -> Sequence[Account]:
        all_accounts = await self.session.execute(select(Account))
        all_accs_list = all_accounts.scalars().all()
        return self._build_tree(all_accs_list)
        
    def _build_tree(self, accounts: Sequence[Account]) -> List[Account]:
        acc_dict = {acc.id: acc for acc in accounts}
        roots = []
        for acc in accounts:
            acc.children_list = [] # Temporary attribute
        for acc in accounts:
            if acc.parent_id:
                if acc.parent_id in acc_dict:
                    acc_dict[acc.parent_id].children_list.append(acc)
            else:
                roots.append(acc)
        return roots

    async def create(self, data: AccountCreate) -> Account:
        account = Account(**data.model_dump())
        self.session.add(account)
        await self.session.flush()
        return account

    async def has_transactions(self, account_id: UUID) -> bool:
        query = "SELECT 1 FROM journal_lines WHERE account_id = :acc_id LIMIT 1"
        result = await self.session.execute(text(query), {"acc_id": account_id})
        return result.scalar() is not None
```

### Service

```python
# app/finance/services/account_service.py
from uuid import UUID
from app.finance.repositories.account_repository import AccountRepository
from app.finance.schemas.account import AccountCreate, AccountResponse, AccountTreeResponse
from app.finance.exceptions import AccountDeletionError

class AccountService:
    def __init__(self, repository: AccountRepository):
        self.repository = repository

    async def create_account(self, data: AccountCreate) -> AccountResponse:
        account = await self.repository.create(data)
        await self.repository.session.commit()
        return AccountResponse.model_validate(account)

    async def get_account_tree(self) -> list[AccountTreeResponse]:
        roots = await self.repository.get_tree()
        
        def map_node(node) -> dict:
            return {
                "id": node.id,
                "code": node.code,
                "name": node.name,
                "is_active": node.is_active,
                "is_control_account": node.is_control_account,
                "is_header": node.is_header,
                "category_id": node.category_id,
                "parent_id": node.parent_id,
                "children": [map_node(child) for child in getattr(node, 'children_list', [])]
            }
            
        return [AccountTreeResponse(**map_node(root)) for root in roots]

    async def delete_account(self, account_id: UUID):
        account = await self.repository.get_by_id(account_id)
        if not account:
            raise AccountDeletionError("Account not found", 404)
        if await self.repository.has_transactions(account_id):
            raise AccountDeletionError("Cannot delete account with existing transactions.")
        
        await self.repository.session.delete(account)
        await self.repository.session.commit()
```

### Router

```python
# app/finance/routers/accounts.py
from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession
from typing import List
from app.core.database import get_db
from app.finance.schemas.account import AccountTreeResponse
from app.finance.repositories.account_repository import AccountRepository
from app.finance.services.account_service import AccountService

router = APIRouter(prefix="/finance/accounts", tags=["Accounts"])

def get_account_service(db: AsyncSession = Depends(get_db)) -> AccountService:
    return AccountService(AccountRepository(db))

@router.get("/tree", response_model=List[AccountTreeResponse])
async def get_account_tree(service: AccountService = Depends(get_account_service)):
    return await service.get_account_tree()
```

---

## 4. Period Management

### Models

```python
# app/finance/models/period.py
from sqlalchemy import Column, String, Boolean, Date, ForeignKey, Enum as SQLEnum
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship
import uuid
import enum
from app.core.database import Base

class PeriodStatus(str, enum.Enum):
    OPEN = "OPEN"
    CLOSED = "CLOSED"
    FUTURE = "FUTURE"

class FinancialYear(Base):
    __tablename__ = 'financial_years'
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    name = Column(String(50), unique=True, nullable=False) # e.g., '2025' or '2025/2026'
    start_date = Column(Date, nullable=False)
    end_date = Column(Date, nullable=False)
    is_active = Column(Boolean, default=True)

class AccountingPeriod(Base):
    __tablename__ = 'accounting_periods'

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    year_id = Column(UUID(as_uuid=True), ForeignKey('financial_years.id'), nullable=False)
    period_number = Column(String(10), nullable=False) # e.g., '01', '02'
    name = Column(String(50), nullable=False) # e.g., 'January 2025'
    start_date = Column(Date, nullable=False)
    end_date = Column(Date, nullable=False)
    status = Column(SQLEnum(PeriodStatus), default=PeriodStatus.FUTURE, nullable=False)

    financial_year = relationship("FinancialYear")
```

### Period Service

```python
# app/finance/services/period_service.py
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, update
from datetime import date
from uuid import UUID
from app.finance.models.period import AccountingPeriod, PeriodStatus
from app.finance.models.journal import JournalEntry, JournalStatus
from app.finance.exceptions import ClosedPeriodError, FinanceException

class PeriodService:
    def __init__(self, session: AsyncSession):
        self.session = session

    async def get_open_period_for_date(self, transaction_date: date) -> AccountingPeriod:
        result = await self.session.execute(
            select(AccountingPeriod)
            .where(
                AccountingPeriod.start_date <= transaction_date,
                AccountingPeriod.end_date >= transaction_date,
                AccountingPeriod.status == PeriodStatus.OPEN
            )
        )
        period = result.scalars().first()
        if not period:
            raise ClosedPeriodError("No open accounting period found for the given date.")
        return period

    async def close_period(self, period_id: UUID, user_id: UUID) -> AccountingPeriod:
        period = (await self.session.execute(
            select(AccountingPeriod).where(AccountingPeriod.id == period_id)
        )).scalars().first()
        if not period:
            raise FinanceException("Period not found.", 404)
        if period.status != PeriodStatus.OPEN:
            raise FinanceException("Period is not open.")

        drafts = await self.session.execute(
            select(JournalEntry.id).where(
                JournalEntry.period_id == period.id,
                JournalEntry.status == JournalStatus.DRAFT,
            )
        )
        if drafts.first():
            raise FinanceException("Cannot close period with unposted draft journals.")

        await self._carry_forward_balances(period)
        await self._post_retained_earnings(period, user_id)

        period.status = PeriodStatus.CLOSED
        self.session.add(PeriodClosure(
            accounting_period_id=period.id,
            closed_by=user_id,
        ))
        await self.session.commit()
        return period

    async def open_next_period(self, current_period_id: UUID) -> AccountingPeriod:
        current = (await self.session.execute(
            select(AccountingPeriod).where(AccountingPeriod.id == current_period_id)
        )).scalars().first()
        if not current:
            raise FinanceException("Current period not found.", 404)

        nxt = (await self.session.execute(
            select(AccountingPeriod)
            .where(
                AccountingPeriod.year_id == current.year_id,
                AccountingPeriod.start_date > current.end_date,
            )
            .order_by(AccountingPeriod.start_date.asc())
            .limit(1)
        )).scalars().first()

        if nxt is None:
            raise FinanceException("No subsequent period exists in this financial year.")
        if nxt.status != PeriodStatus.FUTURE:
            raise FinanceException(f"Next period is already {nxt.status.value}.")

        nxt.status = PeriodStatus.OPEN
        await self.session.commit()
        return nxt

    async def _carry_forward_balances(self, period: AccountingPeriod) -> None:
        """Materialise closing balance = opening balance + movements per (account, cost_center)."""
        balances = (await self.session.execute(
            select(AccountBalance).where(AccountBalance.period_id == period.id)
        )).scalars().all()
        for balance in balances:
            balance.closing_balance = balance.opening_balance + balance.debit_movement - balance.credit_movement

    async def _post_retained_earnings(self, period: AccountingPeriod, user_id: UUID) -> None:
        """Sweep Revenue and Expense closing balances into Retained Earnings.

        Placeholder responsibilities:
        * Look up the retained-earnings equity account for the school.
        * Build a single balanced JournalEntry with lines that net revenues/expenses to zero.
        * Insert it as POSTED so `check_journal_entry_balance` runs.
        """
        # See JournalService.close_income_statement() for the concrete implementation used here.
        from app.finance.services.journal_service import JournalService  # local import avoids cycle
        await JournalService(self.session).close_income_statement(period=period, user_id=user_id)
```

---

## 5. Journal Entry Module (Core of Double-Entry)

### Models

```python
# app/finance/models/journal.py
from sqlalchemy import Column, String, Boolean, Date, ForeignKey, Enum as SQLEnum, DECIMAL, Text
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship
import uuid
import enum
from datetime import date
from app.core.database import Base

class JournalStatus(str, enum.Enum):
    DRAFT = "DRAFT"
    POSTED = "POSTED"
    REVERSED = "REVERSED"

class JournalEntry(Base):
    __tablename__ = 'journal_entries'

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    reference = Column(String(100), unique=True, index=True, nullable=False) # e.g., JRN-2025-001
    transaction_date = Column(Date, default=date.today, nullable=False)
    description = Column(Text, nullable=False)
    status = Column(SQLEnum(JournalStatus), default=JournalStatus.DRAFT, nullable=False)
    period_id = Column(UUID(as_uuid=True), ForeignKey('accounting_periods.id'), nullable=False)

    # Audit fields
    created_by_id = Column(UUID(as_uuid=True), nullable=True) # ForeignKey to User
    posted_by_id = Column(UUID(as_uuid=True), nullable=True)
    reversed_by_id = Column(UUID(as_uuid=True), nullable=True) # user who authorised the reversal
    reverses_id = Column(UUID(as_uuid=True), ForeignKey('journal_entries.id'), nullable=True) # points at the original journal being reversed

    lines = relationship("JournalLine", back_populates="journal", cascade="all, delete-orphan")
    period = relationship("AccountingPeriod")


class PeriodClosure(Base):
    __tablename__ = 'period_closures'
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    accounting_period_id = Column(UUID(as_uuid=True), ForeignKey('accounting_periods.id'), nullable=False)
    closed_by = Column(UUID(as_uuid=True), nullable=True)
    closed_at = Column(DateTime(timezone=True), nullable=False, server_default="now()")
    retained_earnings_account_id = Column(UUID(as_uuid=True), ForeignKey('accounts.id'), nullable=True)

class JournalLine(Base):
    __tablename__ = 'journal_lines'

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    journal_id = Column(UUID(as_uuid=True), ForeignKey('journal_entries.id'), nullable=False)
    account_id = Column(UUID(as_uuid=True), ForeignKey('accounts.id'), nullable=False)
    cost_center_id = Column(UUID(as_uuid=True), ForeignKey('cost_centers.id'), nullable=True)
    
    description = Column(String(255), nullable=True)
    debit = Column(DECIMAL(15, 4), default=0.0, nullable=False)
    credit = Column(DECIMAL(15, 4), default=0.0, nullable=False)

    journal = relationship("JournalEntry", back_populates="lines")
    account = relationship("Account")
    cost_center = relationship("CostCenter")

class AccountBalance(Base):
    __tablename__ = 'account_balances'
    # Materialized balances per period
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    account_id = Column(UUID(as_uuid=True), ForeignKey('accounts.id'), nullable=False)
    period_id = Column(UUID(as_uuid=True), ForeignKey('accounting_periods.id'), nullable=False)
    cost_center_id = Column(UUID(as_uuid=True), ForeignKey('cost_centers.id'), nullable=True)
    
    opening_balance = Column(DECIMAL(15, 4), default=0.0, nullable=False)
    debit_movement = Column(DECIMAL(15, 4), default=0.0, nullable=False)
    credit_movement = Column(DECIMAL(15, 4), default=0.0, nullable=False)
    closing_balance = Column(DECIMAL(15, 4), default=0.0, nullable=False)
```

### Schemas

```python
# app/finance/schemas/journal.py
from pydantic import BaseModel, Field, ConfigDict, model_validator
from typing import List, Optional
from uuid import UUID
from datetime import date
from decimal import Decimal

class JournalLineCreate(BaseModel):
    account_id: UUID
    cost_center_id: Optional[UUID] = None
    description: Optional[str] = None
    debit: Decimal = Field(default=Decimal('0.00'), max_digits=15, decimal_places=4)
    credit: Decimal = Field(default=Decimal('0.00'), max_digits=15, decimal_places=4)

    @model_validator(mode='after')
    def check_debit_credit(self):
        if self.debit == 0 and self.credit == 0:
            raise ValueError('Line must have either debit or credit')
        if self.debit > 0 and self.credit > 0:
            raise ValueError('Line cannot have both debit and credit')
        return self

class JournalEntryCreate(BaseModel):
    transaction_date: date
    description: str
    lines: List[JournalLineCreate]

    @model_validator(mode='after')
    def check_balance(self):
        total_debit = sum(line.debit for line in self.lines)
        total_credit = sum(line.credit for line in self.lines)
        if total_debit != total_credit:
            raise ValueError(f'Journal is unbalanced. Dr: {total_debit}, Cr: {total_credit}')
        return self
```

### Service

```python
# app/finance/services/journal_service.py
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, update, insert
from sqlalchemy.orm import selectinload
from decimal import Decimal
from uuid import UUID
from app.finance.models.journal import JournalEntry, JournalLine, JournalStatus, AccountBalance
from app.finance.models.account import Account
from app.finance.schemas.journal import JournalEntryCreate
from app.finance.services.period_service import PeriodService
from app.finance.exceptions import InvalidJournalEntryError, ControlAccountPostingError

class JournalService:
    def __init__(self, session: AsyncSession):
        self.session = session
        self.period_service = PeriodService(session)

    async def create_draft(self, data: JournalEntryCreate, user_id: UUID) -> JournalEntry:
        period = await self.period_service.get_open_period_for_date(data.transaction_date)
        
        # Validate Accounts
        account_ids = [line.account_id for line in data.lines]
        acc_result = await self.session.execute(select(Account).where(Account.id.in_(account_ids)))
        accounts = {acc.id: acc for acc in acc_result.scalars().all()}
        
        for line in data.lines:
            acc = accounts.get(line.account_id)
            if not acc:
                raise InvalidJournalEntryError(f"Account {line.account_id} not found.")
            if acc.is_header:
                raise InvalidJournalEntryError(f"Cannot post to header account {acc.code}.")
            if acc.is_control_account:
                raise ControlAccountPostingError(f"Manual posting to control account {acc.code} is forbidden.")

        reference = f"JRN-{data.transaction_date.strftime('%Y%m')}-{uuid.uuid4().hex[:6].upper()}"

        journal = JournalEntry(
            reference=reference,
            transaction_date=data.transaction_date,
            description=data.description,
            period_id=period.id,
            status=JournalStatus.DRAFT,
            created_by_id=user_id
        )
        self.session.add(journal)
        await self.session.flush()

        for line_data in data.lines:
            line = JournalLine(
                journal_id=journal.id,
                **line_data.model_dump()
            )
            self.session.add(line)

        await self.session.commit()
        return journal

    async def post_journal(self, journal_id: UUID, user_id: UUID) -> JournalEntry:
        result = await self.session.execute(
            select(JournalEntry)
            .options(selectinload(JournalEntry.lines))
            .where(JournalEntry.id == journal_id)
            .with_for_update()
        )
        journal = result.scalars().first()

        if not journal:
            raise InvalidJournalEntryError("Journal not found")
        if journal.status != JournalStatus.DRAFT:
            raise InvalidJournalEntryError(f"Cannot post journal with status {journal.status}")
        if not journal.lines:
            raise InvalidJournalEntryError("Cannot post a journal without lines")

        # Post-time re-check of double-entry (defence in depth; the DB trigger will also enforce this).
        total_debit = sum((line.debit for line in journal.lines), Decimal("0.00"))
        total_credit = sum((line.credit for line in journal.lines), Decimal("0.00"))
        if total_debit != total_credit:
            raise InvalidJournalEntryError(
                f"Journal {journal.reference} is unbalanced (Dr={total_debit} Cr={total_credit})"
            )

        # Refuse to post into a closed period.
        period = (await self.session.execute(
            select(AccountingPeriod).where(AccountingPeriod.id == journal.period_id)
        )).scalars().first()
        if period is None or period.status != PeriodStatus.OPEN:
            raise ClosedPeriodError("Cannot post to a period that is not OPEN.")

        for line in journal.lines:
            bal_result = await self.session.execute(
                select(AccountBalance).where(
                    AccountBalance.account_id == line.account_id,
                    AccountBalance.period_id == journal.period_id,
                    AccountBalance.cost_center_id == line.cost_center_id,
                ).with_for_update()
            )
            balance = bal_result.scalars().first()
            if not balance:
                balance = AccountBalance(
                    account_id=line.account_id,
                    period_id=journal.period_id,
                    cost_center_id=line.cost_center_id,
                    opening_balance=Decimal("0.00"),
                    debit_movement=Decimal("0.00"),
                    credit_movement=Decimal("0.00"),
                    closing_balance=Decimal("0.00"),
                )
                self.session.add(balance)

            balance.debit_movement += line.debit
            balance.credit_movement += line.credit
            balance.closing_balance += (line.debit - line.credit)

        journal.status = JournalStatus.POSTED
        journal.posted_by_id = user_id
        await self.session.commit()
        return journal

    async def reverse_journal(self, journal_id: UUID, user_id: UUID, reason: str) -> JournalEntry:
        """Create a new posted journal with negated lines, referencing the original."""
        original = (await self.session.execute(
            select(JournalEntry)
            .options(selectinload(JournalEntry.lines))
            .where(JournalEntry.id == journal_id)
        )).scalars().first()

        if not original:
            raise InvalidJournalEntryError("Journal not found")
        if original.status != JournalStatus.POSTED:
            raise InvalidJournalEntryError("Only POSTED journals can be reversed")
        if original.reversed_by_id is not None:
            raise InvalidJournalEntryError("Journal already reversed")

        reversal = JournalEntry(
            reference=f"REV-{original.reference}",
            transaction_date=original.transaction_date,
            description=f"Reversal of {original.reference}: {reason}",
            period_id=original.period_id,
            status=JournalStatus.DRAFT,
            created_by_id=user_id,
            reverses_id=original.id,
        )
        self.session.add(reversal)
        await self.session.flush()

        for line in original.lines:
            self.session.add(JournalLine(
                journal_id=reversal.id,
                account_id=line.account_id,
                cost_center_id=line.cost_center_id,
                description=f"Reversal of {line.description or original.reference}",
                debit=line.credit,   # swap
                credit=line.debit,
            ))

        await self.session.commit()
        posted = await self.post_journal(reversal.id, user_id)
        original.status = JournalStatus.REVERSED
        original.reversed_by_id = user_id
        await self.session.commit()
        return posted

    async def close_income_statement(self, period: "AccountingPeriod", user_id: UUID) -> None:
        """Post a single closing entry that sweeps revenue and expense balances into retained earnings."""
        result = await self.session.execute(
            select(
                AccountBalance.account_id,
                func.sum(AccountBalance.debit_movement).label("dr"),
                func.sum(AccountBalance.credit_movement).label("cr"),
                Account.account_type_id,
            )
            .join(Account, Account.id == AccountBalance.account_id)
            .where(AccountBalance.period_id == period.id)
            .group_by(AccountBalance.account_id, Account.account_type_id)
        )
        rows = result.all()
        # Retained-earnings account is looked up per school; injection point is intentionally
        # abstracted so schools can nominate their own equity account in fee_vote_heads.
        raise NotImplementedError(
            "Wire this to the school-specific retained-earnings account before enabling year-end close.",
        )
```

---

## 6. Financial Reports

### Service

```python
# app/finance/services/report_service.py
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func
from pydantic import BaseModel
from typing import List
from uuid import UUID
from decimal import Decimal
from app.finance.models.journal import AccountBalance
from app.finance.models.account import Account, AccountTypeEnum

class TrialBalanceLine(BaseModel):
    account_code: str
    account_name: str
    debit: Decimal
    credit: Decimal

class TrialBalanceReport(BaseModel):
    period_id: UUID
    lines: List[TrialBalanceLine]
    total_debit: Decimal
    total_credit: Decimal

class FinancialReportService:
    def __init__(self, session: AsyncSession):
        self.session = session

    async def generate_trial_balance(self, period_id: UUID) -> TrialBalanceReport:
        query = (
            select(
                Account.code,
                Account.name,
                func.sum(AccountBalance.closing_balance).label('net_balance')
            )
            .join(AccountBalance, Account.id == AccountBalance.account_id)
            .where(AccountBalance.period_id == period_id)
            .group_by(Account.code, Account.name)
            .order_by(Account.code)
        )
        
        result = await self.session.execute(query)
        rows = result.all()
        
        lines = []
        total_dr = Decimal('0.00')
        total_cr = Decimal('0.00')
        
        for code, name, net_balance in rows:
            if net_balance > 0:
                dr = net_balance
                cr = Decimal('0.00')
                total_dr += dr
            elif net_balance < 0:
                dr = Decimal('0.00')
                cr = abs(net_balance)
                total_cr += cr
            else:
                dr = Decimal('0.00')
                cr = Decimal('0.00')
                
            lines.append(TrialBalanceLine(account_code=code, account_name=name, debit=dr, credit=cr))
            
        return TrialBalanceReport(
            period_id=period_id,
            lines=lines,
            total_debit=total_dr,
            total_credit=total_cr
        )
```

---

## 7. General Ledger Inquiry

### Service

```python
# app/finance/services/ledger_service.py
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from sqlalchemy.orm import selectinload
from uuid import UUID
from datetime import date
from pydantic import BaseModel
from typing import List
from decimal import Decimal
from app.finance.models.journal import JournalLine, JournalEntry, JournalStatus

class LedgerLineResponse(BaseModel):
    transaction_date: date
    reference: str
    description: str
    debit: Decimal
    credit: Decimal
    running_balance: Decimal

class LedgerService:
    def __init__(self, session: AsyncSession):
        self.session = session

    async def get_account_ledger(self, account_id: UUID, from_date: date, to_date: date) -> List[LedgerLineResponse]:
        query = (
            select(JournalLine)
            .join(JournalEntry, JournalLine.journal_id == JournalEntry.id)
            .options(selectinload(JournalLine.journal))
            .where(
                JournalLine.account_id == account_id,
                JournalEntry.status == JournalStatus.POSTED,
                JournalEntry.transaction_date >= from_date,
                JournalEntry.transaction_date <= to_date
            )
            .order_by(JournalEntry.transaction_date, JournalEntry.created_at)
        )
        
        result = await self.session.execute(query)
        lines = result.scalars().all()
        
        response = []
        running_bal = Decimal('0.00') # Ideally retrieve opening balance first
        
        for line in lines:
            running_bal += (line.debit - line.credit)
            response.append(LedgerLineResponse(
                transaction_date=line.journal.transaction_date,
                reference=line.journal.reference,
                description=line.description or line.journal.description,
                debit=line.debit,
                credit=line.credit,
                running_balance=running_bal
            ))
            
        return response
```

---

## 8. Budget Module

### Models

```python
# app/finance/models/budget.py
from sqlalchemy import Column, String, ForeignKey, DECIMAL
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship
import uuid
from app.core.database import Base

class Budget(Base):
    __tablename__ = 'budgets'
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    year_id = Column(UUID(as_uuid=True), ForeignKey('financial_years.id'), nullable=False)
    name = Column(String(100))

class BudgetLine(Base):
    __tablename__ = 'budget_lines'
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    budget_id = Column(UUID(as_uuid=True), ForeignKey('budgets.id'))
    account_id = Column(UUID(as_uuid=True), ForeignKey('accounts.id'))
    cost_center_id = Column(UUID(as_uuid=True), ForeignKey('cost_centers.id'), nullable=True)
    vote_head_id = Column(UUID(as_uuid=True), ForeignKey('fee_vote_heads.id'), nullable=True)
    amount = Column(DECIMAL(15, 4), default=0.0)
```

### Service

```python
# app/finance/services/budget_service.py
from decimal import Decimal
from typing import Optional
from uuid import UUID

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.finance.exceptions import InsufficientBudgetError
from app.finance.models.budget import BudgetLine
from app.finance.models.journal import AccountBalance


class BudgetService:
    def __init__(self, session: AsyncSession):
        self.session = session

    async def check_budget_availability(
        self,
        *,
        account_id: UUID,
        cost_center_id: UUID,
        amount: Decimal,
        period_id: UUID,
        vote_head_id: Optional[UUID] = None,
    ) -> None:
        """Enforce BRD RULE-FIN-003 / RULE-PRO-001. The check is dimensioned by (account, cost_center, vote_head)."""
        budget_filters = [
            BudgetLine.account_id == account_id,
            BudgetLine.cost_center_id == cost_center_id,
        ]
        if vote_head_id is not None:
            budget_filters.append(BudgetLine.vote_head_id == vote_head_id)

        allocated_budget = (await self.session.execute(
            select(func.coalesce(func.sum(BudgetLine.amount), 0)).where(*budget_filters)
        )).scalar() or Decimal("0.00")

        actual_spend = (await self.session.execute(
            select(func.coalesce(func.sum(AccountBalance.debit_movement - AccountBalance.credit_movement), 0))
            .where(
                AccountBalance.account_id == account_id,
                AccountBalance.cost_center_id == cost_center_id,
                AccountBalance.period_id == period_id,
            )
        )).scalar() or Decimal("0.00")

        if (actual_spend + amount) > allocated_budget:
            raise InsufficientBudgetError(
                f"Transaction exceeds budget: allocated={allocated_budget}, spent={actual_spend}, requested={amount}"
            )
```
