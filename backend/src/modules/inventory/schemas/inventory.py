"""
Pydantic v2 schemas for Inventory, Stores & Fixed Assets.
"""

from datetime import datetime, date
from decimal import Decimal
from uuid import UUID

from pydantic import BaseModel, Field, field_validator


# ============================================================================
# WAREHOUSE SCHEMAS
# ============================================================================


class CreateWarehouseRequest(BaseModel):
    """Create warehouse request."""
    name: str = Field(..., min_length=1, max_length=255)
    code: str = Field(..., min_length=1, max_length=50, description="Unique warehouse code")
    location: str | None = Field(None, max_length=255)
    warehouse_type: str | None = Field(None, max_length=100)
    capacity_units: Decimal | None = Field(None, decimal_places=2, gt=0)
    warehouse_manager_staff_id: UUID | None = None


class WarehouseResponse(BaseModel):
    """Warehouse response."""
    id: UUID
    name: str
    code: str
    location: str | None
    warehouse_type: str | None
    capacity_units: Decimal | None
    current_volume: Decimal
    is_active: bool
    created_at: datetime


# ============================================================================
# INVENTORY ITEM SCHEMAS
# ============================================================================


class CreateItemCategoryRequest(BaseModel):
    """Create item category."""
    name: str = Field(..., min_length=1, max_length=255)
    code: str = Field(..., min_length=1, max_length=50)
    description: str | None = None


class ItemCategoryResponse(BaseModel):
    """Item category response."""
    id: UUID
    name: str
    code: str
    description: str | None
    created_at: datetime


class CreateInventoryItemRequest(BaseModel):
    """Create inventory item."""
    category_id: UUID
    name: str = Field(..., min_length=1, max_length=255)
    code: str = Field(..., min_length=1, max_length=100)
    description: str | None = None
    unit_of_measure: str = Field(..., description="PIECES, KILOGRAMS, LITRES, etc")
    reorder_level: Decimal = Field(..., decimal_places=2, ge=0)
    unit_cost: Decimal = Field(..., decimal_places=2, gt=0)


class InventoryItemResponse(BaseModel):
    """Inventory item response."""
    id: UUID
    category_id: UUID
    name: str
    code: str
    description: str | None
    unit_of_measure: str
    reorder_level: Decimal
    unit_cost: Decimal
    is_active: bool
    created_at: datetime


class InventoryItemDetailResponse(BaseModel):
    """Inventory item with category."""
    id: UUID
    category_id: UUID
    category_name: str
    name: str
    code: str
    description: str | None
    unit_of_measure: str
    reorder_level: Decimal
    unit_cost: Decimal
    is_active: bool
    created_at: datetime


# ============================================================================
# STOCK BALANCE SCHEMAS
# ============================================================================


class StockBalanceResponse(BaseModel):
    """Stock balance response."""
    id: UUID
    warehouse_id: UUID
    warehouse_name: str
    item_id: UUID
    item_name: str
    item_code: str
    quantity_on_hand: Decimal
    reorder_quantity: Decimal
    unit_of_measure: str
    reorder_level: Decimal
    unit_cost: Decimal
    last_received_date: datetime | None
    last_issued_date: datetime | None
    last_counted_date: datetime | None
    below_reorder: bool
    total_value: Decimal  # quantity_on_hand * unit_cost


# ============================================================================
# GOODS RECEIVED NOTE (GRN) SCHEMAS
# ============================================================================


class GRNItemCreate(BaseModel):
    """Create GRN line item."""
    item_id: UUID
    quantity_received: Decimal = Field(..., decimal_places=2, gt=0)
    unit_cost: Decimal = Field(..., decimal_places=2, gt=0)
    expiry_date: date | None = None
    batch_number: str | None = Field(None, max_length=50)
    condition_notes: str | None = None


class CreateGRNRequest(BaseModel):
    """Create Goods Received Note."""
    warehouse_id: UUID
    purchase_order_id: UUID | None = None
    supplier_name: str | None = Field(None, max_length=255)
    received_by_staff_id: UUID | None = None
    items: list[GRNItemCreate] = Field(..., min_items=1)
    grn_notes: str | None = None


class GRNItemResponse(BaseModel):
    """GRN line item response."""
    id: UUID
    item_id: UUID
    item_name: str
    item_code: str
    unit_of_measure: str
    quantity_received: Decimal
    unit_cost: Decimal
    total_cost: Decimal
    expiry_date: date | None
    batch_number: str | None
    condition_notes: str | None


class GRNResponse(BaseModel):
    """Goods Received Note response."""
    id: UUID
    grn_number: str
    warehouse_id: UUID
    warehouse_name: str
    purchase_order_id: UUID | None
    supplier_name: str | None
    received_date: datetime
    is_posted_to_inventory: bool
    posted_date: datetime | None
    items: list[GRNItemResponse] = []
    created_at: datetime


class PostGRNRequest(BaseModel):
    """Post GRN to update stock balances."""
    grn_id: UUID


class PostGRNResponse(BaseModel):
    """Response from posting GRN."""
    grn_id: UUID
    grn_number: str
    status: str
    items_posted: int
    stock_balances_updated: int
    message: str


# ============================================================================
# STOCK ISSUE SCHEMAS
# ============================================================================


class CreateStockIssueRequest(BaseModel):
    """Issue stock from warehouse."""
    warehouse_id: UUID
    item_id: UUID
    quantity_issued: Decimal = Field(..., decimal_places=2, gt=0)
    issued_to_department: str = Field(..., min_length=1, max_length=100)
    issued_by_staff_id: UUID | None = None
    received_by_name: str | None = Field(None, max_length=255)
    purpose: str | None = None
    reference_number: str | None = Field(None, max_length=100)


class StockIssueResponse(BaseModel):
    """Stock issue response."""
    id: UUID
    warehouse_id: UUID
    warehouse_name: str
    item_id: UUID
    item_name: str
    item_code: str
    unit_of_measure: str
    quantity_issued: Decimal
    unit_cost: Decimal
    total_cost: Decimal
    issue_date: datetime
    issued_to_department: str
    received_by_name: str | None
    purpose: str | None
    reference_number: str | None
    created_at: datetime


class StockAuditResponse(BaseModel):
    """Stock audit report."""
    warehouse_id: UUID
    warehouse_name: str
    total_items: int
    total_value: Decimal
    items_below_reorder: list[dict]
    created_at: datetime


# ============================================================================
# FIXED ASSET SCHEMAS
# ============================================================================


class CreateFixedAssetRequest(BaseModel):
    """Create fixed asset."""
    asset_number: str = Field(..., min_length=1, max_length=50, description="Unique asset tag/ID")
    asset_name: str = Field(..., min_length=1, max_length=255)
    asset_category: str = Field(..., min_length=1, max_length=100)
    asset_description: str | None = None
    purchase_cost: Decimal = Field(..., decimal_places=2, gt=0)
    purchase_date: date
    useful_life_years: int = Field(..., gt=0, le=50)
    depreciation_method: str = Field("STRAIGHT_LINE", description="STRAIGHT_LINE or REDUCING_BALANCE")
    salvage_value: Decimal | None = Field(None, decimal_places=2, ge=0)
    location: str | None = Field(None, max_length=255)
    asset_manager_staff_id: UUID | None = None


class FixedAssetResponse(BaseModel):
    """Fixed asset response."""
    id: UUID
    asset_number: str
    asset_name: str
    asset_category: str
    asset_description: str | None
    purchase_cost: Decimal
    purchase_date: date
    useful_life_years: int
    depreciation_method: str
    salvage_value: Decimal
    accumulated_depreciation: Decimal
    net_book_value: Decimal  # purchase_cost - accumulated_depreciation
    asset_status: str
    location: str | None
    last_depreciation_date: datetime | None
    created_at: datetime


class FixedAssetDetailResponse(BaseModel):
    """Fixed asset detail with depreciation schedule."""
    id: UUID
    asset_number: str
    asset_name: str
    asset_category: str
    asset_description: str | None
    purchase_cost: Decimal
    purchase_date: date
    useful_life_years: int
    depreciation_method: str
    salvage_value: Decimal
    accumulated_depreciation: Decimal
    net_book_value: Decimal
    asset_status: str
    location: str | None
    last_depreciation_date: datetime | None
    monthly_depreciation_amount: Decimal
    created_at: datetime


class DepreciationEntryResponse(BaseModel):
    """Depreciation entry response."""
    id: UUID
    asset_id: UUID
    asset_number: str
    asset_name: str
    depreciation_month: int
    depreciation_year: int
    monthly_depreciation: Decimal
    accumulated_to_date: Decimal
    net_book_value: Decimal
    is_posted: bool
    posted_date: datetime | None
    created_at: datetime


class RunDepreciationRequest(BaseModel):
    """Request to run monthly depreciation."""
    depreciation_month: int = Field(..., ge=1, le=12)
    depreciation_year: int = Field(..., gt=2000)


class RunDepreciationResponse(BaseModel):
    """Response from running depreciation."""
    assets_processed: int
    depreciation_entries_created: int
    total_depreciation_amount: Decimal
    journal_entries_posted: int
    message: str


# ============================================================================
# SUMMARY/REPORT SCHEMAS
# ============================================================================


class InventorySummaryResponse(BaseModel):
    """Inventory summary statistics."""
    total_items: int
    total_item_value: Decimal
    items_below_reorder: int
    warehouses_count: int
    total_warehouse_value: Decimal


class AssetSummaryResponse(BaseModel):
    """Fixed assets summary."""
    total_assets: int
    active_assets: int
    total_asset_value: Decimal
    total_accumulated_depreciation: Decimal
    total_net_book_value: Decimal
