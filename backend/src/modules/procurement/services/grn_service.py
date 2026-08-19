"""
Goods Received Note (GRN) Service.

Tracks physical receipt of goods from suppliers.
Used in 3-way matching process.
"""

import logging
from datetime import datetime
from uuid import UUID

from sqlalchemy import and_, select
from sqlalchemy.ext.asyncio import AsyncSession

from src.core.exceptions import NotFoundError, ValidationError
from src.modules.procurement.models.procurement import (
    GoodsReceivedNote,
    GRNLineItem,
    PurchaseOrder,
    PurchaseOrderItem,
    LPOStatus,
)

logger = logging.getLogger(__name__)


class GRNService:
    """Service for managing Goods Received Notes."""
    
    def __init__(self, db: AsyncSession):
        """Initialize with database session."""
        self.db = db
    
    async def create_grn(
        self,
        school_id: UUID,
        purchase_order_id: UUID,
        items: list[dict],  # [{description, quantity_received}, ...]
        received_by_staff_id: UUID | None = None,
        notes: str | None = None,
    ) -> dict:
        """
        Create Goods Received Note.
        
        Args:
            school_id: Tenant identifier
            purchase_order_id: LPO being received
            items: List of {description, quantity_received}
            received_by_staff_id: Staff who received goods
            notes: Receipt notes/condition
        
        Returns:
            dict with grn_id, grn_number, status, message
        
        Raises:
            NotFoundError: If LPO not found
            ValidationError: If invalid items
        """
        logger.debug(f"Creating GRN for LPO {purchase_order_id}")
        
        # STEP 1: Fetch LPO
        lpo_query = select(PurchaseOrder).where(
            and_(
                PurchaseOrder.id == purchase_order_id,
                PurchaseOrder.school_id == school_id,
            )
        )
        lpo = await self.db.scalar(lpo_query)
        
        if not lpo:
            logger.warning(f"LPO {purchase_order_id} not found")
            raise NotFoundError(f"LPO {purchase_order_id} not found")
        
        # Validate LPO status
        if lpo.status == LPOStatus.CANCELLED:
            raise ValidationError(f"Cannot receive goods from cancelled LPO")
        
        # STEP 2: Validate items
        if not items:
            raise ValidationError("GRN must have at least one item")
        
        grn_items_data = []
        for idx, item in enumerate(items):
            try:
                qty = float(item.get("quantity_received", 0))
            except (ValueError, TypeError):
                raise ValidationError(f"Item {idx+1}: Invalid quantity_received")
            
            if qty <= 0:
                raise ValidationError(f"Item {idx+1}: quantity_received must be positive")
            
            grn_items_data.append({
                "description": item.get("description", ""),
                "quantity_received": qty,
            })
        
        # STEP 3: Generate GRN number
        grn_number = await self._generate_grn_number(school_id)
        
        # STEP 4: Create GRN
        grn = GoodsReceivedNote(
            school_id=school_id,
            grn_number=grn_number,
            purchase_order_id=purchase_order_id,
            receipt_date=datetime.utcnow(),
            received_by_staff_id=received_by_staff_id,
            notes=notes,
        )
        
        self.db.add(grn)
        await self.db.flush()
        
        # STEP 5: Create GRN line items
        for item_data in grn_items_data:
            grn_item = GRNLineItem(
                school_id=school_id,
                grn_id=grn.id,
                description=item_data["description"],
                quantity_received=item_data["quantity_received"],
            )
            self.db.add(grn_item)
        
        # STEP 6: Update LPO status and received quantities
        total_received = sum(item_data["quantity_received"] for item_data in grn_items_data)
        total_lpo_qty = sum(item.quantity for item in lpo.line_items)
        
        # Update received quantities on LPO items
        for lpo_item in lpo.line_items:
            # Find matching GRN item by description
            matching_grn = next(
                (i for i in grn_items_data if i["description"] == lpo_item.description),
                None
            )
            if matching_grn:
                lpo_item.received_quantity += matching_grn["quantity_received"]
        
        # Update LPO status
        if total_received >= total_lpo_qty:
            lpo.status = LPOStatus.FULLY_RECEIVED
        else:
            lpo.status = LPOStatus.PARTIAL_RECEIVED
        
        await self.db.commit()
        
        logger.info(
            f"GRN created: {grn.id}, number={grn_number}, "
            f"lpo={purchase_order_id}, items={len(grn_items_data)}"
        )
        
        return {
            "grn_id": str(grn.id),
            "grn_number": grn_number,
            "purchase_order_id": str(purchase_order_id),
            "lpo_number": lpo.lpo_number,
            "receipt_date": grn.receipt_date.isoformat(),
            "item_count": len(grn_items_data),
            "message": f"GRN {grn_number} created for LPO {lpo.lpo_number}",
        }
    
    async def get_grn(
        self,
        school_id: UUID,
        grn_id: UUID,
    ) -> dict:
        """Get GRN detail with line items."""
        grn_query = select(GoodsReceivedNote).where(
            and_(
                GoodsReceivedNote.id == grn_id,
                GoodsReceivedNote.school_id == school_id,
            )
        )
        grn = await self.db.scalar(grn_query)
        
        if not grn:
            raise NotFoundError(f"GRN {grn_id} not found")
        
        line_items = [
            {
                "id": str(item.id),
                "description": item.description,
                "quantity_received": item.quantity_received,
            }
            for item in grn.line_items
        ]
        
        lpo_number = grn.purchase_order.lpo_number if grn.purchase_order else None
        
        return {
            "id": str(grn.id),
            "grn_number": grn.grn_number,
            "purchase_order_id": str(grn.purchase_order_id),
            "lpo_number": lpo_number,
            "receipt_date": grn.receipt_date.isoformat(),
            "received_by": None,  # Would populate from staff lookup
            "line_items": line_items,
            "notes": grn.notes,
            "created_at": grn.created_at.isoformat(),
        }
    
    async def list_grns(
        self,
        school_id: UUID,
        purchase_order_id: UUID | None = None,
    ) -> list[dict]:
        """List GRNs with optional LPO filter."""
        query = select(GoodsReceivedNote).where(
            GoodsReceivedNote.school_id == school_id
        )
        
        if purchase_order_id:
            query = query.where(GoodsReceivedNote.purchase_order_id == purchase_order_id)
        
        query = query.order_by(GoodsReceivedNote.receipt_date.desc())
        
        result = await self.db.execute(query)
        grns = result.scalars().all()
        
        return [
            {
                "id": str(g.id),
                "grn_number": g.grn_number,
                "lpo_number": g.purchase_order.lpo_number if g.purchase_order else None,
                "receipt_date": g.receipt_date.isoformat(),
                "item_count": len(g.line_items),
                "created_at": g.created_at.isoformat(),
            }
            for g in grns
        ]
    
    async def _generate_grn_number(self, school_id: UUID) -> str:
        """Generate unique GRN number."""
        # Query max existing GRN number
        query = select(GoodsReceivedNote).where(
            GoodsReceivedNote.school_id == school_id
        ).order_by(GoodsReceivedNote.created_at.desc())
        
        result = await self.db.execute(query)
        last_grn = result.scalars().first()
        
        if last_grn and last_grn.grn_number:
            try:
                parts = last_grn.grn_number.split("-")
                sequence = int(parts[-1]) + 1
            except (IndexError, ValueError):
                sequence = 1
        else:
            sequence = 1
        
        year = datetime.utcnow().year
        grn_number = f"GRN-{year}-{sequence:04d}"
        
        logger.debug(f"Generated GRN number: {grn_number}")
        
        return grn_number
