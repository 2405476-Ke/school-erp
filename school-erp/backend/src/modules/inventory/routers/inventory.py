"""
FastAPI routers for Inventory, Stores & Stock Management.

Endpoints for:
- Warehouses
- Inventory Items
- Stock Balances
- Goods Received Notes (GRN) and posting
- Stock Issues
"""

import logging
from uuid import UUID
from decimal import Decimal

from fastapi import APIRouter, Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession

from src.core.database import get_db
from src.core.exceptions import NotFoundError, ValidationError
from src.core.response import APIResponse
from src.modules.inventory.schemas.inventory import (
    CreateWarehouseRequest,
    WarehouseResponse,
    CreateItemCategoryRequest,
    ItemCategoryResponse,
    CreateInventoryItemRequest,
    InventoryItemResponse,
    InventoryItemDetailResponse,
    CreateGRNRequest,
    GRNResponse,
    PostGRNRequest,
    PostGRNResponse,
    CreateStockIssueRequest,
    StockIssueResponse,
    StockBalanceResponse,
    StockAuditResponse,
    InventorySummaryResponse,
)
from src.modules.inventory.services.stock_service import StockService
from src.modules.inventory.models.inventory import (
    Warehouse,
    ItemCategory,
    InventoryItem,
    GoodsReceivedNote,
    GRNItem,
)

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/inventory", tags=["Inventory & Stores"])


# ============================================================================
# WAREHOUSE MANAGEMENT
# ============================================================================


@router.post("/warehouses", response_model=APIResponse)
async def create_warehouse(
    request: CreateWarehouseRequest,
    db: AsyncSession = Depends(get_db),
    school_id: UUID = Depends(lambda: UUID("00000000-0000-0000-0000-000000000000")),
) -> APIResponse:
    """Create warehouse."""
    try:
        warehouse = Warehouse(
            school_id=school_id,
            name=request.name,
            code=request.code,
            location=request.location,
            warehouse_type=request.warehouse_type,
            capacity_units=request.capacity_units,
            warehouse_manager_staff_id=request.warehouse_manager_staff_id,
        )
        
        db.add(warehouse)
        await db.commit()
        
        return APIResponse.success(
            data={
                "warehouse_id": str(warehouse.id),
                "name": warehouse.name,
                "code": warehouse.code,
                "message": f"Warehouse {warehouse.name} created",
            },
            message="Warehouse created successfully",
            status_code=201,
        )
    
    except ValidationError as e:
        return APIResponse.error(
            error=str(e),
            message="Warehouse creation failed",
            status_code=400,
        )
    
    except Exception as e:
        logger.error(f"Error creating warehouse: {e}")
        return APIResponse.error(
            error=str(e),
            message="Failed to create warehouse",
            status_code=500,
        )


@router.get("/warehouses", response_model=APIResponse)
async def list_warehouses(
    db: AsyncSession = Depends(get_db),
    school_id: UUID = Depends(lambda: UUID("00000000-0000-0000-0000-000000000000")),
) -> APIResponse:
    """List warehouses."""
    try:
        from sqlalchemy import select
        
        result = await db.execute(
            select(Warehouse).where(Warehouse.school_id == school_id)
        )
        warehouses = result.scalars().all()
        
        return APIResponse.success(
            data=[
                {
                    "id": str(w.id),
                    "name": w.name,
                    "code": w.code,
                    "location": w.location,
                    "warehouse_type": w.warehouse_type,
                }
                for w in warehouses
            ],
            message=f"Found {len(warehouses)} warehouses",
            status_code=200,
        )
    
    except Exception as e:
        logger.error(f"Error listing warehouses: {e}")
        return APIResponse.error(
            error=str(e),
            message="Failed to list warehouses",
            status_code=500,
        )


# ============================================================================
# INVENTORY ITEM MANAGEMENT
# ============================================================================


@router.post("/item-categories", response_model=APIResponse)
async def create_item_category(
    request: CreateItemCategoryRequest,
    db: AsyncSession = Depends(get_db),
    school_id: UUID = Depends(lambda: UUID("00000000-0000-0000-0000-000000000000")),
) -> APIResponse:
    """Create item category."""
    try:
        category = ItemCategory(
            school_id=school_id,
            name=request.name,
            code=request.code,
            description=request.description,
        )
        
        db.add(category)
        await db.commit()
        
        return APIResponse.success(
            data={
                "category_id": str(category.id),
                "name": category.name,
                "code": category.code,
            },
            message="Category created",
            status_code=201,
        )
    
    except Exception as e:
        logger.error(f"Error creating category: {e}")
        return APIResponse.error(error=str(e), message="Failed to create category", status_code=500)


@router.post("/items", response_model=APIResponse)
async def create_inventory_item(
    request: CreateInventoryItemRequest,
    db: AsyncSession = Depends(get_db),
    school_id: UUID = Depends(lambda: UUID("00000000-0000-0000-0000-000000000000")),
) -> APIResponse:
    """Create inventory item."""
    try:
        item = InventoryItem(
            school_id=school_id,
            category_id=request.category_id,
            name=request.name,
            code=request.code,
            description=request.description,
            unit_of_measure=request.unit_of_measure,
            reorder_level=request.reorder_level,
            unit_cost=request.unit_cost,
        )
        
        db.add(item)
        await db.commit()
        
        return APIResponse.success(
            data={
                "item_id": str(item.id),
                "name": item.name,
                "code": item.code,
                "reorder_level": item.reorder_level,
                "unit_cost": item.unit_cost,
            },
            message="Item created",
            status_code=201,
        )
    
    except Exception as e:
        logger.error(f"Error creating item: {e}")
        return APIResponse.error(error=str(e), message="Failed to create item", status_code=500)


@router.get("/items/{item_id}", response_model=APIResponse)
async def get_item(
    item_id: UUID,
    db: AsyncSession = Depends(get_db),
    school_id: UUID = Depends(lambda: UUID("00000000-0000-0000-0000-000000000000")),
) -> APIResponse:
    """Get inventory item."""
    try:
        from sqlalchemy import select
        
        result = await db.execute(
            select(InventoryItem).where(
                InventoryItem.id == item_id,
                InventoryItem.school_id == school_id,
            )
        )
        item = result.scalars().first()
        
        if not item:
            return APIResponse.error(error="Not found", message="Item not found", status_code=404)
        
        return APIResponse.success(
            data={
                "id": str(item.id),
                "name": item.name,
                "code": item.code,
                "category": item.category.name if item.category else None,
                "unit_of_measure": item.unit_of_measure.value,
                "reorder_level": item.reorder_level,
                "unit_cost": item.unit_cost,
            },
            message="Item retrieved",
            status_code=200,
        )
    
    except Exception as e:
        logger.error(f"Error getting item: {e}")
        return APIResponse.error(error=str(e), message="Failed to get item", status_code=500)


# ============================================================================
# GOODS RECEIVED NOTES (GRN)
# ============================================================================


@router.post("/grn/receive", response_model=APIResponse)
async def create_grn(
    request: CreateGRNRequest,
    db: AsyncSession = Depends(get_db),
    school_id: UUID = Depends(lambda: UUID("00000000-0000-0000-0000-000000000000")),
) -> APIResponse:
    """Create Goods Received Note."""
    try:
        from datetime import datetime
        
        # Validate items
        if not request.items:
            return APIResponse.error(error="No items", message="GRN must have items", status_code=400)
        
        # Generate GRN number
        from sqlalchemy import select, func
        
        result = await db.execute(
            select(func.count(GoodsReceivedNote.id)).where(
                GoodsReceivedNote.school_id == school_id
            )
        )
        count = result.scalar() or 0
        grn_number = f"GRN-{datetime.now().year}-{count + 1:04d}"
        
        # Create GRN
        grn = GoodsReceivedNote(
            school_id=school_id,
            grn_number=grn_number,
            warehouse_id=request.warehouse_id,
            purchase_order_id=request.purchase_order_id,
            supplier_name=request.supplier_name,
            received_by_staff_id=request.received_by_staff_id,
            grn_notes=request.grn_notes,
            received_date=datetime.utcnow(),
        )
        
        db.add(grn)
        await db.flush()
        
        # Create line items
        for item_req in request.items:
            total_cost = (item_req.quantity_received * item_req.unit_cost).quantize(Decimal("0.01"))
            
            grn_item = GRNItem(
                school_id=school_id,
                grn_id=grn.id,
                item_id=item_req.item_id,
                quantity_received=item_req.quantity_received,
                unit_cost=item_req.unit_cost,
                total_cost=total_cost,
                expiry_date=item_req.expiry_date,
                batch_number=item_req.batch_number,
                condition_notes=item_req.condition_notes,
            )
            db.add(grn_item)
        
        await db.commit()
        
        return APIResponse.success(
            data={
                "grn_id": str(grn.id),
                "grn_number": grn_number,
                "items_count": len(request.items),
                "status": "CREATED",
            },
            message=f"GRN {grn_number} created. Use /post endpoint to update stock.",
            status_code=201,
        )
    
    except Exception as e:
        logger.error(f"Error creating GRN: {e}")
        await db.rollback()
        return APIResponse.error(error=str(e), message="Failed to create GRN", status_code=500)


@router.post("/grn/{grn_id}/post", response_model=APIResponse)
async def post_grn(
    grn_id: UUID,
    db: AsyncSession = Depends(get_db),
    school_id: UUID = Depends(lambda: UUID("00000000-0000-0000-0000-000000000000")),
) -> APIResponse:
    """
    CRITICAL: Post GRN to update stock balances.
    
    This endpoint triggers the receive_goods() logic:
    - Updates StockBalance for each GRN item
    - Marks GRN as posted
    """
    try:
        service = StockService(db)
        result = await service.receive_goods(school_id, grn_id)
        
        return APIResponse.success(
            data=result,
            message="GRN posted to inventory",
            status_code=200,
        )
    
    except NotFoundError as e:
        return APIResponse.error(error=str(e), message="GRN not found", status_code=404)
    
    except ValidationError as e:
        return APIResponse.error(error=str(e), message="GRN posting failed", status_code=400)
    
    except Exception as e:
        logger.error(f"Error posting GRN: {e}", exc_info=True)
        return APIResponse.error(error=str(e), message="Failed to post GRN", status_code=500)


@router.get("/grn/{grn_id}", response_model=APIResponse)
async def get_grn(
    grn_id: UUID,
    db: AsyncSession = Depends(get_db),
    school_id: UUID = Depends(lambda: UUID("00000000-0000-0000-0000-000000000000")),
) -> APIResponse:
    """Get GRN detail."""
    try:
        from sqlalchemy import select
        
        result = await db.execute(
            select(GoodsReceivedNote).where(GoodsReceivedNote.id == grn_id)
        )
        grn = result.scalars().first()
        
        if not grn:
            return APIResponse.error(error="Not found", message="GRN not found", status_code=404)
        
        return APIResponse.success(
            data={
                "id": str(grn.id),
                "grn_number": grn.grn_number,
                "warehouse": grn.warehouse.name if grn.warehouse else None,
                "supplier_name": grn.supplier_name,
                "received_date": grn.received_date.isoformat(),
                "is_posted": grn.is_posted_to_inventory,
                "items_count": len(grn.grn_items),
            },
            message="GRN retrieved",
            status_code=200,
        )
    
    except Exception as e:
        logger.error(f"Error getting GRN: {e}")
        return APIResponse.error(error=str(e), message="Failed to get GRN", status_code=500)


# ============================================================================
# STOCK ISSUES
# ============================================================================


@router.post("/stock-issue", response_model=APIResponse)
async def create_stock_issue(
    request: CreateStockIssueRequest,
    db: AsyncSession = Depends(get_db),
    school_id: UUID = Depends(lambda: UUID("00000000-0000-0000-0000-000000000000")),
) -> APIResponse:
    """
    CRITICAL: Issue stock from warehouse.
    
    Validates sufficient quantity and decrements balance.
    Triggers reorder alert if below reorder level.
    """
    try:
        service = StockService(db)
        result = await service.issue_stock(
            school_id=school_id,
            warehouse_id=request.warehouse_id,
            item_id=request.item_id,
            quantity_to_issue=request.quantity_issued,
            issued_to_department=request.issued_to_department,
            issued_by_staff_id=request.issued_by_staff_id,
            received_by_name=request.received_by_name,
            purpose=request.purpose,
            reference_number=request.reference_number,
        )
        
        status_code = 200
        message = "Stock issued successfully"
        
        if result.get("below_reorder"):
            message += f" - ⚠️ REORDER ALERT: {result['alert_message']}"
        
        return APIResponse.success(
            data=result,
            message=message,
            status_code=status_code,
        )
    
    except NotFoundError as e:
        return APIResponse.error(error=str(e), message="Resource not found", status_code=404)
    
    except ValidationError as e:
        return APIResponse.error(error=str(e), message="Issue validation failed", status_code=400)
    
    except Exception as e:
        logger.error(f"Error issuing stock: {e}")
        return APIResponse.error(error=str(e), message="Failed to issue stock", status_code=500)


# ============================================================================
# STOCK BALANCES & QUERIES
# ============================================================================


@router.get("/stock-balance/{warehouse_id}/{item_id}", response_model=APIResponse)
async def get_stock_balance(
    warehouse_id: UUID,
    item_id: UUID,
    db: AsyncSession = Depends(get_db),
    school_id: UUID = Depends(lambda: UUID("00000000-0000-0000-0000-000000000000")),
) -> APIResponse:
    """Get stock balance for item in warehouse."""
    try:
        service = StockService(db)
        result = await service.get_stock_balance(school_id, warehouse_id, item_id)
        
        return APIResponse.success(
            data=result,
            message="Stock balance retrieved",
            status_code=200,
        )
    
    except NotFoundError as e:
        return APIResponse.error(error=str(e), message="Not found", status_code=404)
    
    except Exception as e:
        logger.error(f"Error getting stock balance: {e}")
        return APIResponse.error(error=str(e), message="Failed to get balance", status_code=500)


@router.get("/stock-balances/{warehouse_id}", response_model=APIResponse)
async def list_warehouse_stock(
    warehouse_id: UUID,
    db: AsyncSession = Depends(get_db),
    school_id: UUID = Depends(lambda: UUID("00000000-0000-0000-0000-000000000000")),
    below_reorder: bool = Query(False),
) -> APIResponse:
    """List stock balances in warehouse."""
    try:
        service = StockService(db)
        balances = await service.list_stock_balances(
            school_id,
            warehouse_id=warehouse_id,
            below_reorder_only=below_reorder,
        )
        
        return APIResponse.success(
            data=balances,
            message=f"Found {len(balances)} items",
            status_code=200,
        )
    
    except Exception as e:
        logger.error(f"Error listing stock: {e}")
        return APIResponse.error(error=str(e), message="Failed to list stock", status_code=500)


@router.get("/warehouse/{warehouse_id}/inventory-value", response_model=APIResponse)
async def get_warehouse_value(
    warehouse_id: UUID,
    db: AsyncSession = Depends(get_db),
    school_id: UUID = Depends(lambda: UUID("00000000-0000-0000-0000-000000000000")),
) -> APIResponse:
    """Get total inventory value in warehouse."""
    try:
        service = StockService(db)
        result = await service.get_warehouse_inventory_value(school_id, warehouse_id)
        
        return APIResponse.success(
            data=result,
            message="Warehouse value calculated",
            status_code=200,
        )
    
    except NotFoundError as e:
        return APIResponse.error(error=str(e), message="Warehouse not found", status_code=404)
    
    except Exception as e:
        logger.error(f"Error calculating warehouse value: {e}")
        return APIResponse.error(error=str(e), message="Failed to calculate value", status_code=500)


@router.get("/reorder-alerts", response_model=APIResponse)
async def get_reorder_alerts(
    db: AsyncSession = Depends(get_db),
    school_id: UUID = Depends(lambda: UUID("00000000-0000-0000-0000-000000000000")),
) -> APIResponse:
    """Get items below reorder level."""
    try:
        service = StockService(db)
        alerts = await service.get_reorder_alerts(school_id)
        
        return APIResponse.success(
            data=alerts,
            message=f"Found {len(alerts)} items below reorder level",
            status_code=200,
        )
    
    except Exception as e:
        logger.error(f"Error getting reorder alerts: {e}")
        return APIResponse.error(error=str(e), message="Failed to get alerts", status_code=500)
