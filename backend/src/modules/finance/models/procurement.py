
from uuid import UUID
from decimal import Decimal
from typing import List, Optional
from sqlalchemy import String, Numeric, Text, ForeignKey, Enum, Boolean
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy.dialects.postgresql import UUID as PG_UUID
from enum import Enum as PyEnum

from src.shared.base_model import AuditableBase, TenantMixin

class RequisitionStatus(str, PyEnum):
    DRAFT = "DRAFT"
    PENDING_TIER_1 = "PENDING_TIER_1" # Bursar
    PENDING_TIER_2 = "PENDING_TIER_2" # Principal
    APPROVED = "APPROVED"
    REJECTED = "REJECTED"
    FULFILLED = "FULFILLED"

class VoteHeadBudget(AuditableBase, TenantMixin):
    """
    Tracks the budget for a specific expense Vote Head (Account).
    """
    __tablename__ = "vote_head_budgets"

    account_id: Mapped[UUID] = mapped_column(
        PG_UUID(as_uuid=True), ForeignKey("accounts.id", ondelete="CASCADE"), nullable=False, unique=True
    )
    financial_year_id: Mapped[UUID] = mapped_column(
        PG_UUID(as_uuid=True), ForeignKey("financial_years.id", ondelete="CASCADE"), nullable=False
    )
    
    total_budget: Mapped[Decimal] = mapped_column(Numeric(15, 4), default=Decimal("0.0000"), nullable=False)
    committed_amount: Mapped[Decimal] = mapped_column(Numeric(15, 4), default=Decimal("0.0000"), nullable=False)
    spent_amount: Mapped[Decimal] = mapped_column(Numeric(15, 4), default=Decimal("0.0000"), nullable=False)

    @property
    def available_balance(self) -> Decimal:
        return self.total_budget - self.committed_amount - self.spent_amount

class PurchaseRequisition(AuditableBase, TenantMixin):
    """
    Purchase Requisition created by HODs.
    """
    __tablename__ = "purchase_requisitions"

    requisition_number: Mapped[str] = mapped_column(String(50), nullable=False, unique=True, index=True)
    department: Mapped[str] = mapped_column(String(100), nullable=False)
    description: Mapped[str] = mapped_column(Text, nullable=False)
    
    vote_head_account_id: Mapped[UUID] = mapped_column(
        PG_UUID(as_uuid=True), ForeignKey("accounts.id"), nullable=False
    )
    
    status: Mapped[str] = mapped_column(
        String(20), default=RequisitionStatus.DRAFT.value, nullable=False, index=True
    )
    
    total_amount: Mapped[Decimal] = mapped_column(Numeric(15, 4), default=Decimal("0.0000"), nullable=False)
    
    # Maker-Checker Workflow
    requested_by_id: Mapped[UUID] = mapped_column(PG_UUID(as_uuid=True), nullable=False)
    tier_1_approved_by_id: Mapped[Optional[UUID]] = mapped_column(PG_UUID(as_uuid=True), nullable=True) # Bursar
    tier_2_approved_by_id: Mapped[Optional[UUID]] = mapped_column(PG_UUID(as_uuid=True), nullable=True) # Principal
    
    rejection_reason: Mapped[Optional[str]] = mapped_column(Text, nullable=True)

    items: Mapped[List["RequisitionItem"]] = relationship(
        cascade="all, delete-orphan"
    )

class RequisitionItem(AuditableBase):
    """
    Line items for a purchase requisition.
    """
    __tablename__ = "requisition_items"

    requisition_id: Mapped[UUID] = mapped_column(
        PG_UUID(as_uuid=True), ForeignKey("purchase_requisitions.id", ondelete="CASCADE"), nullable=False
    )
    description: Mapped[str] = mapped_column(String(255), nullable=False)
    quantity: Mapped[Decimal] = mapped_column(Numeric(10, 2), nullable=False)
    unit_price: Mapped[Decimal] = mapped_column(Numeric(15, 4), nullable=False)
    total_price: Mapped[Decimal] = mapped_column(Numeric(15, 4), nullable=False)
