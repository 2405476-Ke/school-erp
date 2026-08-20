from datetime import date
from decimal import Decimal
from typing import Optional
from uuid import UUID

from sqlalchemy import Boolean, Date, Enum, ForeignKey, Numeric, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from src.shared.base_model import AuditableBase, TenantMixin

class DepreciationMethod(str, Enum):
    STRAIGHT_LINE = "STRAIGHT_LINE"
    REDUCING_BALANCE = "REDUCING_BALANCE"

class FixedAsset(AuditableBase, TenantMixin):
    """Fixed Asset Register."""
    __tablename__ = "fixed_assets"

    asset_code: Mapped[str] = mapped_column(String(50), nullable=False, index=True)
    name: Mapped[str] = mapped_column(String(150), nullable=False)
    description: Mapped[Optional[str]] = mapped_column(Text)
    
    purchase_date: Mapped[date] = mapped_column(Date, nullable=False)
    purchase_value: Mapped[Decimal] = mapped_column(Numeric(15, 4), nullable=False)
    salvage_value: Mapped[Decimal] = mapped_column(Numeric(15, 4), default=0.0)
    useful_life_years: Mapped[int] = mapped_column(nullable=False)
    
    depreciation_method: Mapped[str] = mapped_column(String(50), nullable=False)
    accumulated_depreciation: Mapped[Decimal] = mapped_column(Numeric(15, 4), default=0.0)
    
    asset_account_id: Mapped[UUID] = mapped_column(ForeignKey("accounts.id"), nullable=False)
    expense_account_id: Mapped[UUID] = mapped_column(ForeignKey("accounts.id"), nullable=False)
    accumulated_account_id: Mapped[UUID] = mapped_column(ForeignKey("accounts.id"), nullable=False)
    
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)

class DepreciationLog(AuditableBase, TenantMixin):
    """Log of automated depreciation runs to prevent duplicates."""
    __tablename__ = "depreciation_logs"
    
    asset_id: Mapped[UUID] = mapped_column(ForeignKey("fixed_assets.id"), nullable=False)
    period_id: Mapped[UUID] = mapped_column(ForeignKey("accounting_periods.id"), nullable=False)
    journal_entry_id: Mapped[UUID] = mapped_column(ForeignKey("journal_entries.id"), nullable=False)
    amount: Mapped[Decimal] = mapped_column(Numeric(15, 4), nullable=False)
