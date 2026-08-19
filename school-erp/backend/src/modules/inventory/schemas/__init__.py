"""
Inventory schemas.
"""

from src.modules.inventory.schemas.inventory import (
    CreateWarehouseRequest,
    WarehouseResponse,
    CreateItemCategoryRequest,
    ItemCategoryResponse,
    CreateInventoryItemRequest,
    InventoryItemResponse,
    CreateGRNRequest,
    GRNResponse,
    PostGRNRequest,
    PostGRNResponse,
    CreateStockIssueRequest,
    StockIssueResponse,
    CreateFixedAssetRequest,
    FixedAssetResponse,
    RunDepreciationRequest,
    RunDepreciationResponse,
)

__all__ = [
    "CreateWarehouseRequest",
    "WarehouseResponse",
    "CreateItemCategoryRequest",
    "ItemCategoryResponse",
    "CreateInventoryItemRequest",
    "InventoryItemResponse",
    "CreateGRNRequest",
    "GRNResponse",
    "PostGRNRequest",
    "PostGRNResponse",
    "CreateStockIssueRequest",
    "StockIssueResponse",
    "CreateFixedAssetRequest",
    "FixedAssetResponse",
    "RunDepreciationRequest",
    "RunDepreciationResponse",
]
