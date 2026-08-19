"""
Inventory, Stores & Fixed Assets Data Models.

Tracks:
- Warehouse locations and stock levels
- Inventory items with reorder levels
- Stock balances by warehouse
- GRN integration with stock updates
- Stock issues to departments
- Fixed assets with depreciation
"""

from datetime import datetime, date
from decimal import Decimal
from enum import Enum
from uuid import UUID

from sqlalchemy import (
    Column, String, Integer, Numeric, DateTime, Date, Boolean, ForeignKey,
    UniqueConstraint, CheckConstraint, Index, Text, Enum as SQLEnum, func
)
from sqlalchemy.dialects.postgresql import UUID as PG_UUID
from sqlalchemy.orm import relationship

from src.core.database import Base


# ============================================================================
# ENUMS
# ============================================================================


class UnitOfMeasure(str, Enum):
    """Unit of measurement for inventory items."""
    PIECES = "PIECES"
    KILOGRAMS = "KILOGRAMS"
    LITRES = "LITRES"
    METRES = "METRES"
    BOXES = "BOXES"
    BUNDLES = "BUNDLES"
    PACKS = "PACKS"
    DOZENS = "DOZENS"
    REAMS = "REAMS"


class AssetStatus(str, Enum):
    """Status of fixed assets."""
    ACTIVE = "ACTIVE"
    INACTIVE = "INACTIVE"
    DISPOSED = "DISPOSED"
    UNDER_MAINTENANCE = "UNDER_MAINTENANCE"


class DepreciationMethod(str, Enum):
    """Depreciation calculation method."""
    STRAIGHT_LINE = "STRAIGHT_LINE"
    REDUCING_BALANCE = "REDUCING_BALANCE"


# ============================================================================
# WAREHOUSE & INVENTORY MASTER
# ============================================================================


class Warehouse(Base):
    """Warehouse or store location."""
    __tablename__ = "warehouses"
    
    id = Column(PG_UUID(as_uuid=True), primary_key=True, default=UUID)
    school_id = Column(PG_UUID(as_uuid=True), nullable=False, index=True)
    name = Column(String(255), nullable=False)
    code = Column(String(50), nullable=False)
    location = Column(String(255), nullable=True)
    warehouse_type = Column(String(100), nullable=True)  # E.g., "Food Store", "Stationery", "Equipment"
    capacity_units = Column(Numeric(15, 2), nullable=True, comment="Max capacity in unit of measure")
    current_volume = Column(Numeric(15, 2), default=0, comment="Current usage")
    warehouse_manager_staff_id = Column(PG_UUID(as_uuid=True), nullable=True, index=True)
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime, default=datetime.utcnow, index=True)
    
    # Relationships
    stock_balances = relationship("StockBalance", back_populates="warehouse", cascade="all, delete-orphan")
    stock_issues = relationship("StockIssue", back_populates="warehouse", cascade="all, delete-orphan")
    
    __table_args__ = (
        UniqueConstraint("school_id", "code", name="uq_warehouse_code"),
        CheckConstraint("capacity_units > 0", name="ck_warehouse_capacity_positive"),
        Index("idx_warehouse_school_active", "school_id", "is_active"),
    )


class ItemCategory(Base):
    """Inventory item categories."""
    __tablename__ = "item_categories"
    
    id = Column(PG_UUID(as_uuid=True), primary_key=True, default=UUID)
    school_id = Column(PG_UUID(as_uuid=True), nullable=False, index=True)
    name = Column(String(255), nullable=False)
    code = Column(String(50), nullable=False)
    description = Column(Text, nullable=True)
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    
    # Relationships
    items = relationship("InventoryItem", back_populates="category", cascade="all, delete-orphan")
    
    __table_args__ = (
        UniqueConstraint("school_id", "code", name="uq_category_code"),
        Index("idx_category_school", "school_id"),
    )


class InventoryItem(Base):
    """Inventory items (consumables and goods)."""
    __tablename__ = "inventory_items"
    
    id = Column(PG_UUID(as_uuid=True), primary_key=True, default=UUID)
    school_id = Column(PG_UUID(as_uuid=True), nullable=False, index=True)
    category_id = Column(PG_UUID(as_uuid=True), ForeignKey("item_categories.id"), nullable=False, index=True)
    name = Column(String(255), nullable=False)
    code = Column(String(100), nullable=False)
    description = Column(Text, nullable=True)
    unit_of_measure = Column(SQLEnum(UnitOfMeasure), nullable=False, default=UnitOfMeasure.PIECES)
    reorder_level = Column(Numeric(15, 2), nullable=False, comment="Minimum quantity before reorder alert")
    unit_cost = Column(Numeric(15, 2), nullable=False, comment="Standard unit cost in KES")
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    
    # Relationships
    category = relationship("ItemCategory", back_populates="items")
    stock_balances = relationship("StockBalance", back_populates="item", cascade="all, delete-orphan")
    stock_issues = relationship("StockIssue", back_populates="item", cascade="all, delete-orphan")
    grn_items = relationship("GRNItem", back_populates="item", cascade="all, delete-orphan")
    
    __table_args__ = (
        UniqueConstraint("school_id", "code", name="uq_item_code"),
        CheckConstraint("reorder_level >= 0", name="ck_item_reorder_positive"),
        CheckConstraint("unit_cost > 0", name="ck_item_cost_positive"),
        Index("idx_item_school_category", "school_id", "category_id"),
    )


# ============================================================================
# STOCK TRACKING
# ============================================================================


class StockBalance(Base):
    """Running inventory balance by warehouse and item."""
    __tablename__ = "stock_balances"
    
    id = Column(PG_UUID(as_uuid=True), primary_key=True, default=UUID)
    school_id = Column(PG_UUID(as_uuid=True), nullable=False, index=True)
    warehouse_id = Column(PG_UUID(as_uuid=True), ForeignKey("warehouses.id"), nullable=False, index=True)
    item_id = Column(PG_UUID(as_uuid=True), ForeignKey("inventory_items.id"), nullable=False, index=True)
    quantity_on_hand = Column(Numeric(15, 2), default=0, nullable=False, comment="Current stock quantity")
    reorder_quantity = Column(Numeric(15, 2), default=0, comment="Quantity to order when below reorder_level")
    last_received_date = Column(DateTime, nullable=True)
    last_issued_date = Column(DateTime, nullable=True)
    last_counted_date = Column(DateTime, nullable=True, comment="Last physical stocktake")
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationships
    warehouse = relationship("Warehouse", back_populates="stock_balances")
    item = relationship("InventoryItem", back_populates="stock_balances")
    
    __table_args__ = (
        UniqueConstraint("school_id", "warehouse_id", "item_id", name="uq_stock_balance"),
        CheckConstraint("quantity_on_hand >= 0", name="ck_stock_balance_positive"),
        Index("idx_stock_balance_school", "school_id"),
        Index("idx_stock_balance_warehouse_item", "warehouse_id", "item_id"),
    )


# ============================================================================
# GRN - GOODS RECEIVED (INTEGRATION WITH PROCUREMENT)
# ============================================================================


class GoodsReceivedNote(Base):
    """
    Goods Received Notes - tracks physical receipt of items.
    
    Links to procurement LPO but focuses on inventory receipt.
    Triggers StockBalance updates.
    """
    __tablename__ = "goods_received_notes_inventory"
    
    id = Column(PG_UUID(as_uuid=True), primary_key=True, default=UUID)
    school_id = Column(PG_UUID(as_uuid=True), nullable=False, index=True)
    grn_number = Column(String(50), nullable=False)
    purchase_order_id = Column(PG_UUID(as_uuid=True), nullable=True, comment="Link to procurement LPO")
    warehouse_id = Column(PG_UUID(as_uuid=True), ForeignKey("warehouses.id"), nullable=False, index=True)
    received_date = Column(DateTime, default=datetime.utcnow)
    received_by_staff_id = Column(PG_UUID(as_uuid=True), nullable=True)
    supplier_name = Column(String(255), nullable=True)
    grn_notes = Column(Text, nullable=True, comment="Condition of goods, damage, etc")
    is_posted_to_inventory = Column(Boolean, default=False, comment="Whether stock balance was updated")
    posted_date = Column(DateTime, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    
    # Relationships
    warehouse = relationship("Warehouse")
    grn_items = relationship("GRNItem", back_populates="grn", cascade="all, delete-orphan")
    
    __table_args__ = (
        UniqueConstraint("school_id", "grn_number", name="uq_grn_number"),
        Index("idx_grn_school_warehouse", "school_id", "warehouse_id"),
        Index("idx_grn_posted", "is_posted_to_inventory"),
    )


class GRNItem(Base):
    """Line items in a Goods Received Note."""
    __tablename__ = "grn_items_inventory"
    
    id = Column(PG_UUID(as_uuid=True), primary_key=True, default=UUID)
    school_id = Column(PG_UUID(as_uuid=True), nullable=False)
    grn_id = Column(PG_UUID(as_uuid=True), ForeignKey("goods_received_notes_inventory.id"), nullable=False, index=True)
    item_id = Column(PG_UUID(as_uuid=True), ForeignKey("inventory_items.id"), nullable=False, index=True)
    quantity_received = Column(Numeric(15, 2), nullable=False)
    unit_cost = Column(Numeric(15, 2), nullable=False, comment="Cost per unit at time of receipt")
    total_cost = Column(Numeric(15, 2), nullable=False, comment="quantity_received * unit_cost")
    expiry_date = Column(Date, nullable=True, comment="For perishable items")
    batch_number = Column(String(50), nullable=True)
    condition_notes = Column(Text, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    
    # Relationships
    grn = relationship("GoodsReceivedNote", back_populates="grn_items")
    item = relationship("InventoryItem", back_populates="grn_items")
    
    __table_args__ = (
        CheckConstraint("quantity_received > 0", name="ck_grn_item_qty_positive"),
        CheckConstraint("unit_cost > 0", name="ck_grn_item_cost_positive"),
        Index("idx_grn_item_grn", "grn_id"),
        Index("idx_grn_item_item", "item_id"),
    )


# ============================================================================
# STOCK ISSUES / OUTBOUND
# ============================================================================


class StockIssue(Base):
    """Tracks items issued from warehouse to departments/kitchen."""
    __tablename__ = "stock_issues"
    
    id = Column(PG_UUID(as_uuid=True), primary_key=True, default=UUID)
    school_id = Column(PG_UUID(as_uuid=True), nullable=False, index=True)
    warehouse_id = Column(PG_UUID(as_uuid=True), ForeignKey("warehouses.id"), nullable=False, index=True)
    item_id = Column(PG_UUID(as_uuid=True), ForeignKey("inventory_items.id"), nullable=False, index=True)
    quantity_issued = Column(Numeric(15, 2), nullable=False)
    unit_cost = Column(Numeric(15, 2), nullable=False, comment="Cost at time of issue")
    total_cost = Column(Numeric(15, 2), nullable=False, comment="quantity_issued * unit_cost")
    issue_date = Column(DateTime, default=datetime.utcnow, index=True)
    issued_to_department = Column(String(100), nullable=False)  # E.g., "Kitchen", "Laundry", "Maintenance"
    issued_by_staff_id = Column(PG_UUID(as_uuid=True), nullable=True)
    received_by_name = Column(String(255), nullable=True)
    purpose = Column(Text, nullable=True)
    reference_number = Column(String(100), nullable=True, comment="E.g., requisition number")
    created_at = Column(DateTime, default=datetime.utcnow)
    
    # Relationships
    warehouse = relationship("Warehouse", back_populates="stock_issues")
    item = relationship("InventoryItem", back_populates="stock_issues")
    
    __table_args__ = (
        CheckConstraint("quantity_issued > 0", name="ck_issue_qty_positive"),
        CheckConstraint("unit_cost > 0", name="ck_issue_cost_positive"),
        Index("idx_stock_issue_school", "school_id"),
        Index("idx_stock_issue_warehouse_item", "warehouse_id", "item_id"),
        Index("idx_stock_issue_date", "issue_date"),
    )


# ============================================================================
# FIXED ASSETS
# ============================================================================


class FixedAsset(Base):
    """Fixed assets with depreciation tracking."""
    __tablename__ = "fixed_assets"
    
    id = Column(PG_UUID(as_uuid=True), primary_key=True, default=UUID)
    school_id = Column(PG_UUID(as_uuid=True), nullable=False, index=True)
    asset_number = Column(String(50), nullable=False, comment="Unique asset ID/tag")
    asset_name = Column(String(255), nullable=False)
    asset_category = Column(String(100), nullable=False)  # E.g., "Building", "Furniture", "Equipment", "Vehicle"
    asset_description = Column(Text, nullable=True)
    purchase_cost = Column(Numeric(15, 2), nullable=False, comment="Original purchase price in KES")
    purchase_date = Column(Date, nullable=False)
    useful_life_years = Column(Integer, nullable=False, comment="Expected useful life in years")
    depreciation_method = Column(SQLEnum(DepreciationMethod), default=DepreciationMethod.STRAIGHT_LINE)
    salvage_value = Column(Numeric(15, 2), default=0, comment="Expected residual value")
    accumulated_depreciation = Column(Numeric(15, 2), default=0, comment="Running total of depreciation")
    asset_status = Column(SQLEnum(AssetStatus), default=AssetStatus.ACTIVE)
    location = Column(String(255), nullable=True)
    asset_manager_staff_id = Column(PG_UUID(as_uuid=True), nullable=True)
    disposal_date = Column(Date, nullable=True)
    disposal_reason = Column(Text, nullable=True)
    last_depreciation_date = Column(DateTime, nullable=True, comment="Date of last depreciation run")
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    __table_args__ = (
        UniqueConstraint("school_id", "asset_number", name="uq_asset_number"),
        CheckConstraint("purchase_cost > 0", name="ck_asset_cost_positive"),
        CheckConstraint("useful_life_years > 0", name="ck_asset_life_positive"),
        CheckConstraint("salvage_value >= 0", name="ck_asset_salvage_non_negative"),
        CheckConstraint("accumulated_depreciation >= 0", name="ck_asset_accum_non_negative"),
        Index("idx_asset_school", "school_id"),
        Index("idx_asset_status", "asset_status"),
        Index("idx_asset_category", "asset_category"),
    )


class DepreciationEntry(Base):
    """Monthly depreciation transactions for fixed assets."""
    __tablename__ = "depreciation_entries"
    
    id = Column(PG_UUID(as_uuid=True), primary_key=True, default=UUID)
    school_id = Column(PG_UUID(as_uuid=True), nullable=False, index=True)
    asset_id = Column(PG_UUID(as_uuid=True), ForeignKey("fixed_assets.id"), nullable=False, index=True)
    depreciation_month = Column(Integer, nullable=False, comment="Month (1-12)")
    depreciation_year = Column(Integer, nullable=False, comment="Calendar year")
    monthly_depreciation = Column(Numeric(15, 2), nullable=False, comment="Depreciation amount for this month")
    accumulated_to_date = Column(Numeric(15, 2), nullable=False, comment="Total depreciation up to end of month")
    net_book_value = Column(Numeric(15, 2), nullable=False, comment="purchase_cost - accumulated_depreciation")
    journal_entry_id = Column(PG_UUID(as_uuid=True), nullable=True, comment="GL entry ID if posted")
    is_posted = Column(Boolean, default=False)
    posted_date = Column(DateTime, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    
    __table_args__ = (
        UniqueConstraint("school_id", "asset_id", "depreciation_month", "depreciation_year", 
                        name="uq_depreciation_period"),
        CheckConstraint("depreciation_month >= 1 AND depreciation_month <= 12", 
                       name="ck_depreciation_month_valid"),
        CheckConstraint("depreciation_year > 2000", name="ck_depreciation_year_valid"),
        Index("idx_depreciation_school", "school_id"),
        Index("idx_depreciation_period", "depreciation_year", "depreciation_month"),
    )
