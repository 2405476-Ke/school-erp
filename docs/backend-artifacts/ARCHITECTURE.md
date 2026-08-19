# Kenya Secondary School ERP - Architecture Document

## 1. Domain-Driven Design Overview

The ERP is designed around bounded contexts. Each context manages a specific domain area of the school, ensuring low coupling and high cohesion.

- **Finance Context:** Manages student fee accounts, general ledgers, chart of accounts, budgeting, vendor payments, and M-Pesa integrations. Implements double-entry accounting.
- **Academic Context:** Manages grading, subjects, curriculum execution, examinations, and report card generation (compliant with KEMIS/NEMIS standards).
- **HR Context:** Manages employee records (TSC teachers, BOM teachers, support staff), attendance, leave, and payroll generation (handling PAYE, NSSF, NHIF, and Housing Levy).
- **Student Lifecycle (Admissions) Context:** Tracks the student journey from application/admission through enrollment, promotion, and alumni status.
- **Operations (Boarding/Inventory) Context:** Manages dormitories, bed allocation, dining hall inventory, procurement, and asset tracking.
- **Communication Context:** A centralized hub for dispatching SMS, Emails, and App notifications to parents, teachers, and staff.

## 2. Layered Architecture

We implement a rigorous 4-layer architecture:
1. **Router Layer:** Handles HTTP concerns. Receives requests, calls services, returns structured responses. No business logic.
2. **Service Layer:** Orchestrates business rules, transactions, and orchestrates across repositories or other domains.
3. **Repository Layer:** Encapsulates all data access logic (SQLAlchemy queries). Abstracted behind interfaces.
4. **Domain Model Layer:** SQLAlchemy ORM models representing the business entities.

### Working Example: Payment Receipt via M-Pesa Callback

```python
# src/modules/finance/routers.py
from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession
from src.core.database import get_db
from src.modules.finance.schemas import MPesaCallbackPayload
from src.modules.finance.services import PaymentService
from src.shared.response import APIResponse

router = APIRouter()

@router.post("/mpesa/callback")
async def mpesa_callback(
    payload: MPesaCallbackPayload,
    db: AsyncSession = Depends(get_db)
):
    payment_service = PaymentService(db)
    result = await payment_service.process_mpesa_payment(payload)
    return APIResponse.success(data=result, message="Payment processed successfully")

# src/modules/finance/services.py
from sqlalchemy.ext.asyncio import AsyncSession
from src.modules.finance.repository import LedgerRepository, ReceiptRepository
from src.modules.communication.tasks import send_sms_task
from src.shared.exceptions import ValidationError

class PaymentService:
    def __init__(self, db: AsyncSession):
        self.db = db
        self.ledger_repo = LedgerRepository(db)
        self.receipt_repo = ReceiptRepository(db)

    async def process_mpesa_payment(self, payload: MPesaCallbackPayload):
        if payload.ResultCode != 0:
            # Handle failed transaction
            return {"status": "ignored", "reason": "Transaction failed"}

        async with self.db.begin(): # Transactional boundary
            # 1. Register Receipt
            receipt = await self.receipt_repo.create({
                "transaction_id": payload.receipt_number,
                "amount": payload.amount,
                "phone_number": payload.phone_number
            })
            
            # 2. Allocate to Student Account (Double-entry logic)
            await self.ledger_repo.post_journal_entry(
                debit_account="MPESA_PAYBILL",
                credit_account="STUDENT_RECEIVABLES",
                amount=payload.amount,
                reference=receipt.id
            )

        # 3. Async event - Send SMS confirmation to Parent
        send_sms_task.delay(
            phone_number=payload.phone_number,
            message=f"Received KES {payload.amount} for student fees. Receipt: {payload.receipt_number}"
        )

        return receipt.model_dump()
```

## 3. Base Classes

### `src/shared/base_model.py`
```python
import uuid
from datetime import datetime
from sqlalchemy import Column, DateTime, Boolean, String, ForeignKey
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.ext.declarative import declared_attr
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column

class Base(DeclarativeBase):
    pass

class AuditableBase(Base):
    __abstract__ = True

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4, index=True
    )
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=datetime.utcnow)
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=datetime.utcnow, onupdate=datetime.utcnow
    )
    created_by: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), nullable=True)
    is_deleted: Mapped[bool] = mapped_column(Boolean, default=False)
```

### `src/shared/base_repository.py`
```python
from typing import TypeVar, Generic, Type, Optional, List, Any
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, update
from src.shared.base_model import Base

ModelType = TypeVar("ModelType", bound=Base)

class BaseRepository(Generic[ModelType]):
    def __init__(self, model: Type[ModelType], db: AsyncSession):
        self.model = model
        self.db = db

    async def get(self, id: Any) -> Optional[ModelType]:
        query = select(self.model).where(self.model.id == id, self.model.is_deleted == False)
        result = await self.db.execute(query)
        return result.scalar_one_or_none()

    async def get_all(self, skip: int = 0, limit: int = 100) -> List[ModelType]:
        query = select(self.model).where(self.model.is_deleted == False).offset(skip).limit(limit)
        result = await self.db.execute(query)
        return result.scalars().all()

    async def create(self, obj_in: dict) -> ModelType:
        db_obj = self.model(**obj_in)
        self.db.add(db_obj)
        await self.db.flush()
        return db_obj

    async def update(self, id: Any, obj_in: dict) -> Optional[ModelType]:
        query = update(self.model).where(self.model.id == id).values(**obj_in).returning(self.model)
        result = await self.db.execute(query)
        return result.scalar_one_or_none()

    async def soft_delete(self, id: Any) -> bool:
        query = update(self.model).where(self.model.id == id).values(is_deleted=True)
        result = await self.db.execute(query)
        return result.rowcount > 0
```

### `src/shared/pagination.py`
```python
from pydantic import BaseModel
from typing import Generic, TypeVar, List, Optional

T = TypeVar("T")

class OffsetPagination(BaseModel, Generic[T]):
    items: List[T]
    total: int
    page: int
    size: int
    pages: int

class CursorPagination(BaseModel, Generic[T]):
    items: List[T]
    next_cursor: Optional[str]
    has_next: bool
```

### `src/shared/exceptions.py`
```python
from fastapi import HTTPException, status

class ERPException(HTTPException):
    def __init__(self, status_code: int, detail: str):
        super().__init__(status_code=status_code, detail=detail)

class NotFoundError(ERPException):
    def __init__(self, detail: str = "Resource not found"):
        super().__init__(status.HTTP_404_NOT_FOUND, detail)

class ValidationError(ERPException):
    def __init__(self, detail: str = "Validation failed"):
        super().__init__(status.HTTP_400_BAD_REQUEST, detail)

class InsufficientFundsError(ERPException):
    def __init__(self, detail: str = "Insufficient funds for allocation"):
        super().__init__(status.HTTP_400_BAD_REQUEST, detail)

class DuplicateEntryError(ERPException):
    def __init__(self, detail: str = "Entry already exists"):
        super().__init__(status.HTTP_409_CONFLICT, detail)

class UnauthorizedError(ERPException):
    def __init__(self, detail: str = "Authentication required"):
        super().__init__(status.HTTP_401_UNAUTHORIZED, detail)

class ForbiddenError(ERPException):
    def __init__(self, detail: str = "Permission denied"):
        super().__init__(status.HTTP_403_FORBIDDEN, detail)
```

### `src/shared/response.py`
```python
from typing import Generic, TypeVar, Optional, Any
from pydantic import BaseModel

T = TypeVar("T")

class APIResponse(BaseModel, Generic[T]):
    success: bool
    message: str
    data: Optional[T] = None
    meta: Optional[dict[str, Any]] = None

    @classmethod
    def success(cls, data: T, message: str = "Success", meta: Optional[dict] = None):
        return cls(success=True, message=message, data=data, meta=meta)

    @classmethod
    def error(cls, message: str):
        return cls(success=False, message=message, data=None)
```

## 4. Database Connection (`src/core/database.py`)

```python
from typing import AsyncGenerator
from sqlalchemy.ext.asyncio import create_async_engine, async_sessionmaker, AsyncSession
from src.core.config import settings

# Create Async Engine with connection pooling suited for high concurrency
engine = create_async_engine(
    str(settings.DATABASE_URL),
    echo=settings.DEBUG,
    pool_pre_ping=True,
    pool_size=20,
    max_overflow=10,
)

# Create session factory
AsyncSessionLocal = async_sessionmaker(
    bind=engine,
    class_=AsyncSession,
    expire_on_commit=False,
    autocommit=False,
    autoflush=False,
)

async def get_db() -> AsyncGenerator[AsyncSession, None]:
    """
    Dependency to yield an async database session per request.
    """
    async with AsyncSessionLocal() as session:
        try:
            yield session
        except Exception:
            await session.rollback()
            raise
        finally:
            await session.close()
```

## 5. Event-Driven Architecture (Celery)

The architecture leverages Celery with Redis as a broker to offload blocking tasks and external API calls.
- **M-Pesa Callback Processing:** Validation and deep processing of C2B and Express callbacks are offloaded to avoid keeping Daraja waiting and hitting timeouts.
- **SMS & Email Dispatch:** Bulk messaging (e.g., term opening announcements, fee balances) is distributed across Celery workers.
- **Report Generation:** Heavy PDF generation (Student terminal report cards, Payroll summaries, NEMIS export files) are queued. WebSockets or polling are used to notify the frontend upon completion.

## 6. Caching Strategy (Redis)

Redis is heavily utilized to optimize performance:
- **M-Pesa OAuth Tokens:** Daraja access tokens expire every 60 minutes. They are fetched once, cached in Redis with a 55-minute TTL, eliminating the need to request a new token per API call.
- **Role-Based Access Control (RBAC):** User permissions and module access arrays are cached upon login.
- **Report Caching:** Static or slowly changing data (e.g., active term syllabus, BOM lists) are cached.

## 7. Security Architecture

- **Authentication:** Stateless JWT (JSON Web Tokens) are used. 
  - `access_token`: Short-lived (e.g., 30 mins) used for API access.
  - `refresh_token`: Long-lived (e.g., 7 days) stored securely to obtain new access tokens.
- **Password Hashing:** Passlib with bcrypt is used for secure hashing.
- **RBAC Middleware:** A custom dependency checks the JWT scope against required permissions for the endpoint. E.g., `Depends(RoleChecker(["finance_admin", "superadmin"]))`.
- **Soft Deletes:** Deletion of critical records (invoices, student profiles) sets `is_deleted=True` rather than dropping the row, preserving audit trails.
```
