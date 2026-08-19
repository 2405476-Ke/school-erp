"""
Stock Management Service.

Handles inventory receipt and issuance with:
- GRN posting to StockBalance
- Reorder level monitoring
- Stock depletion validation
"""

import logging
from datetime import datetime
from decimal import Decimal
from uuid import UUID

from sqlalchemy import and_, select, func
from sqlalchemy.ext.asyncio import AsyncSession

from src.core.exceptions import NotFoundError, ValidationError
from src.modules.inventory.models.inventory import (
    GoodsReceivedNote,
    GRNItem,
    StockBalance,
    StockIssue,
    InventoryItem,
    Warehouse,
)

logger = logging.getLogger(__name__)


class StockService:
    """Service for managing stock and inventory."""
    
    def __init__(self, db: AsyncSession):
        """Initialize with database session."""
        self.db = db
    
    async def receive_goods(
        self,
        school_id: UUID,
        grn_id: UUID,
    ) -> dict:
        """
        CRITICAL: Post GRN to inventory system.
        
        Transactional logic:
        1. Fetch GRN with line items
        2. For each GRN item:
           a. Fetch or create StockBalance (warehouse, item)
           b. Increment quantity_on_hand by quantity_received
           c. Update last_received_date
        3. Mark GRN as posted
        4. COMMIT atomically
        
        Args:
            school_id: Tenant identifier
            grn_id: GRN to post
        
        Returns:
            dict with grn_id, items_posted, stock_balances_updated
        
        Raises:
            NotFoundError: If GRN not found
            ValidationError: If GRN already posted
        """
        logger.debug(f"Receiving goods from GRN {grn_id}")
        
        # STEP 1: Fetch GRN
        grn_query = select(GoodsReceivedNote).where(
            and_(
                GoodsReceivedNote.id == grn_id,
                GoodsReceivedNote.school_id == school_id,
            )
        )
        grn = await self.db.scalar(grn_query)
        
        if not grn:
            logger.warning(f"GRN {grn_id} not found")
            raise NotFoundError(f"GRN {grn_id} not found")
        
        # Validate not already posted
        if grn.is_posted_to_inventory:
            raise ValidationError(f"GRN {grn.grn_number} already posted to inventory")
        
        logger.debug(f"Processing GRN {grn.grn_number} with {len(grn.grn_items)} items")
        
        # STEP 2: Process each item
        items_posted = 0
        stock_balances_updated = 0
        
        for grn_item in grn.grn_items:
            logger.debug(
                f"Posting item {grn_item.item.name}: qty={grn_item.quantity_received}"
            )
            
            # Fetch existing stock balance or create new one
            stock_query = select(StockBalance).where(
                and_(
                    StockBalance.school_id == school_id,
                    StockBalance.warehouse_id == grn.warehouse_id,
                    StockBalance.item_id == grn_item.item_id,
                )
            )
            stock = await self.db.scalar(stock_query)
            
            if stock:
                # Update existing balance
                old_qty = stock.quantity_on_hand
                stock.quantity_on_hand += grn_item.quantity_received
                stock.last_received_date = datetime.utcnow()
                stock.updated_at = datetime.utcnow()
                
                logger.debug(
                    f"Updated stock balance: {old_qty} → {stock.quantity_on_hand} "
                    f"for {grn_item.item.name} in {grn.warehouse.name}"
                )
            else:
                # Create new balance
                stock = StockBalance(
                    school_id=school_id,
                    warehouse_id=grn.warehouse_id,
                    item_id=grn_item.item_id,
                    quantity_on_hand=grn_item.quantity_received,
                    reorder_quantity=0,
                    last_received_date=datetime.utcnow(),
                )
                self.db.add(stock)
                
                logger.debug(
                    f"Created new stock balance: {grn_item.quantity_received} "
                    f"for {grn_item.item.name} in {grn.warehouse.name}"
                )
                
                stock_balances_updated += 1
            
            items_posted += 1
        
        # STEP 3: Mark GRN as posted
        grn.is_posted_to_inventory = True
        grn.posted_date = datetime.utcnow()
        
        # COMMIT atomically
        await self.db.commit()
        
        logger.info(
            f"GRN {grn.grn_number} posted: {items_posted} items, "
            f"{stock_balances_updated} new balances created"
        )
        
        return {
            "grn_id": str(grn_id),
            "grn_number": grn.grn_number,
            "warehouse_name": grn.warehouse.name,
            "items_posted": items_posted,
            "stock_balances_updated": stock_balances_updated,
            "posted_date": grn.posted_date.isoformat(),
            "message": f"GRN {grn.grn_number} posted: {items_posted} items added to inventory",
        }
    
    async def issue_stock(
        self,
        school_id: UUID,
        warehouse_id: UUID,
        item_id: UUID,
        quantity_to_issue: Decimal,
        issued_to_department: str,
        issued_by_staff_id: UUID | None = None,
        received_by_name: str | None = None,
        purpose: str | None = None,
        reference_number: str | None = None,
    ) -> dict:
        """
        CRITICAL: Issue stock from warehouse.
        
        Validation & Depletion Logic:
        1. Fetch StockBalance
        2. Validate quantity_on_hand >= quantity_to_issue
        3. Decrement quantity_on_hand
        4. Create StockIssue record
        5. If quantity_on_hand now < reorder_level → trigger alert
        6. COMMIT atomically
        
        Args:
            school_id: Tenant identifier
            warehouse_id: Source warehouse
            item_id: Item to issue
            quantity_to_issue: Quantity being removed
            issued_to_department: Department receiving stock
            issued_by_staff_id: Staff authorizing issue
            received_by_name: Person receiving stock
            purpose: Reason for issue
            reference_number: Requisition/reference number
        
        Returns:
            dict with issue_id, remaining_balance, below_reorder_alert
        
        Raises:
            NotFoundError: If warehouse, item, or balance not found
            ValidationError: If insufficient stock
        """
        logger.debug(
            f"Issuing {quantity_to_issue} of item {item_id} "
            f"from warehouse {warehouse_id} to {issued_to_department}"
        )
        
        # STEP 1: Validate warehouse exists
        warehouse_query = select(Warehouse).where(
            and_(
                Warehouse.id == warehouse_id,
                Warehouse.school_id == school_id,
            )
        )
        warehouse = await self.db.scalar(warehouse_query)
        
        if not warehouse:
            raise NotFoundError(f"Warehouse {warehouse_id} not found")
        
        # STEP 2: Validate item exists
        item_query = select(InventoryItem).where(
            and_(
                InventoryItem.id == item_id,
                InventoryItem.school_id == school_id,
            )
        )
        item = await self.db.scalar(item_query)
        
        if not item:
            raise NotFoundError(f"Item {item_id} not found")
        
        # STEP 3: Fetch stock balance
        stock_query = select(StockBalance).where(
            and_(
                StockBalance.school_id == school_id,
                StockBalance.warehouse_id == warehouse_id,
                StockBalance.item_id == item_id,
            )
        )
        stock = await self.db.scalar(stock_query)
        
        if not stock:
            raise ValidationError(
                f"No stock balance found for {item.name} in {warehouse.name}"
            )
        
        # STEP 4: Validate sufficient quantity
        if stock.quantity_on_hand < quantity_to_issue:
            raise ValidationError(
                f"Insufficient stock: {item.name}. "
                f"Available: {stock.quantity_on_hand}, Requested: {quantity_to_issue}"
            )
        
        logger.debug(f"Stock validation passed: available={stock.quantity_on_hand}")
        
        # STEP 5: Calculate cost
        unit_cost = item.unit_cost
        total_cost = (quantity_to_issue * unit_cost).quantize(Decimal("0.01"))
        
        # STEP 6: Create StockIssue record
        issue = StockIssue(
            school_id=school_id,
            warehouse_id=warehouse_id,
            item_id=item_id,
            quantity_issued=quantity_to_issue,
            unit_cost=unit_cost,
            total_cost=total_cost,
            issued_to_department=issued_to_department,
            issued_by_staff_id=issued_by_staff_id,
            received_by_name=received_by_name,
            purpose=purpose,
            reference_number=reference_number,
            issue_date=datetime.utcnow(),
        )
        
        self.db.add(issue)
        
        # STEP 7: Decrement stock balance
        old_qty = stock.quantity_on_hand
        stock.quantity_on_hand -= quantity_to_issue
        stock.last_issued_date = datetime.utcnow()
        stock.updated_at = datetime.utcnow()
        
        await self.db.commit()
        
        logger.info(
            f"Stock issued: {issue.id}, item={item.name}, qty={quantity_to_issue}, "
            f"balance: {old_qty} → {stock.quantity_on_hand}"
        )
        
        # STEP 8: Check if below reorder level
        below_reorder = stock.quantity_on_hand < item.reorder_level
        alert_message = ""
        
        if below_reorder:
            alert_message = (
                f"⚠️ REORDER ALERT: {item.name} in {warehouse.name} "
                f"is now below reorder level ({item.reorder_level}). "
                f"Current balance: {stock.quantity_on_hand}"
            )
            logger.warning(alert_message)
        
        return {
            "issue_id": str(issue.id),
            "item_name": item.name,
            "warehouse_name": warehouse.name,
            "quantity_issued": quantity_to_issue,
            "unit_cost": unit_cost,
            "total_cost": total_cost,
            "department": issued_to_department,
            "remaining_balance": stock.quantity_on_hand,
            "reorder_level": item.reorder_level,
            "below_reorder": below_reorder,
            "alert_message": alert_message,
            "issue_date": issue.issue_date.isoformat(),
            "message": f"Stock issued successfully. Remaining balance: {stock.quantity_on_hand}",
        }
    
    async def get_stock_balance(
        self,
        school_id: UUID,
        warehouse_id: UUID,
        item_id: UUID,
    ) -> dict:
        """Get stock balance detail."""
        stock_query = select(StockBalance).where(
            and_(
                StockBalance.school_id == school_id,
                StockBalance.warehouse_id == warehouse_id,
                StockBalance.item_id == item_id,
            )
        )
        stock = await self.db.scalar(stock_query)
        
        if not stock:
            raise NotFoundError(f"Stock balance not found")
        
        total_value = (stock.quantity_on_hand * stock.item.unit_cost).quantize(Decimal("0.01"))
        
        return {
            "id": str(stock.id),
            "warehouse_id": str(stock.warehouse_id),
            "warehouse_name": stock.warehouse.name,
            "item_id": str(stock.item_id),
            "item_name": stock.item.name,
            "item_code": stock.item.code,
            "quantity_on_hand": stock.quantity_on_hand,
            "unit_of_measure": stock.item.unit_of_measure.value,
            "reorder_level": stock.item.reorder_level,
            "unit_cost": stock.item.unit_cost,
            "total_value": total_value,
            "below_reorder": stock.quantity_on_hand < stock.item.reorder_level,
            "last_received_date": stock.last_received_date.isoformat() if stock.last_received_date else None,
            "last_issued_date": stock.last_issued_date.isoformat() if stock.last_issued_date else None,
            "last_counted_date": stock.last_counted_date.isoformat() if stock.last_counted_date else None,
        }
    
    async def list_stock_balances(
        self,
        school_id: UUID,
        warehouse_id: UUID | None = None,
        below_reorder_only: bool = False,
    ) -> list[dict]:
        """List stock balances with optional filters."""
        query = select(StockBalance).where(
            StockBalance.school_id == school_id
        )
        
        if warehouse_id:
            query = query.where(StockBalance.warehouse_id == warehouse_id)
        
        query = query.order_by(
            StockBalance.warehouse_id,
            StockBalance.item_id,
        )
        
        result = await self.db.execute(query)
        balances = result.scalars().all()
        
        output = []
        for stock in balances:
            if below_reorder_only and stock.quantity_on_hand >= stock.item.reorder_level:
                continue
            
            total_value = (stock.quantity_on_hand * stock.item.unit_cost).quantize(Decimal("0.01"))
            
            output.append({
                "id": str(stock.id),
                "warehouse_name": stock.warehouse.name,
                "item_name": stock.item.name,
                "item_code": stock.item.code,
                "quantity_on_hand": stock.quantity_on_hand,
                "unit_of_measure": stock.item.unit_of_measure.value,
                "reorder_level": stock.item.reorder_level,
                "unit_cost": stock.item.unit_cost,
                "total_value": total_value,
                "below_reorder": stock.quantity_on_hand < stock.item.reorder_level,
            })
        
        return output
    
    async def get_warehouse_inventory_value(
        self,
        school_id: UUID,
        warehouse_id: UUID,
    ) -> dict:
        """Get total inventory value in warehouse."""
        query = select(StockBalance).where(
            and_(
                StockBalance.school_id == school_id,
                StockBalance.warehouse_id == warehouse_id,
            )
        )
        
        result = await self.db.execute(query)
        balances = result.scalars().all()
        
        if not balances:
            warehouse_query = select(Warehouse).where(Warehouse.id == warehouse_id)
            warehouse = await self.db.scalar(warehouse_query)
            
            if not warehouse:
                raise NotFoundError(f"Warehouse not found")
            
            return {
                "warehouse_id": str(warehouse_id),
                "warehouse_name": warehouse.name,
                "total_items": 0,
                "total_value": Decimal("0.00"),
                "items": [],
            }
        
        warehouse = balances[0].warehouse
        total_value = Decimal("0.00")
        items = []
        
        for stock in balances:
            item_value = (stock.quantity_on_hand * stock.item.unit_cost).quantize(Decimal("0.01"))
            total_value += item_value
            
            items.append({
                "item_name": stock.item.name,
                "item_code": stock.item.code,
                "quantity": stock.quantity_on_hand,
                "unit_of_measure": stock.item.unit_of_measure.value,
                "unit_cost": stock.item.unit_cost,
                "total_value": item_value,
            })
        
        return {
            "warehouse_id": str(warehouse_id),
            "warehouse_name": warehouse.name,
            "total_items": len(items),
            "total_value": total_value,
            "items": items,
        }
    
    async def get_reorder_alerts(
        self,
        school_id: UUID,
    ) -> list[dict]:
        """Get items that need reordering (below reorder level)."""
        # Query all stock balances below reorder level
        from sqlalchemy import literal_column
        
        query = select(StockBalance).where(
            and_(
                StockBalance.school_id == school_id,
                StockBalance.quantity_on_hand < literal_column(
                    "(SELECT reorder_level FROM inventory_items WHERE id = stock_balances.item_id)"
                ),
            )
        )
        
        result = await self.db.execute(query)
        balances = result.scalars().all()
        
        alerts = []
        for stock in balances:
            shortage = stock.item.reorder_level - stock.quantity_on_hand
            
            alerts.append({
                "warehouse_name": stock.warehouse.name,
                "item_name": stock.item.name,
                "item_code": stock.item.code,
                "current_balance": stock.quantity_on_hand,
                "reorder_level": stock.item.reorder_level,
                "shortage": shortage,
                "unit_of_measure": stock.item.unit_of_measure.value,
                "unit_cost": stock.item.unit_cost,
            })
        
        return sorted(alerts, key=lambda x: x["shortage"], reverse=True)
