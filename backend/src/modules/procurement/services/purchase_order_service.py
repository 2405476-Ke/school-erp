"""
Purchase Order (LPO) Service.

Generates Local Purchase Orders from approved requisitions.
Manages LPO status and receiving updates.
"""

import logging
from datetime import date, datetime
from uuid import UUID

from sqlalchemy import and_, select
from sqlalchemy.ext.asyncio import AsyncSession

from src.core.exceptions import NotFoundError, ValidationError
from src.modules.procurement.models.procurement import (
    PurchaseOrder,
    PurchaseOrderItem,
    PurchaseRequisition,
    PurchaseRequisitionItem,
    Supplier,
    LPOStatus,
    RequisitionStatus,
)

logger = logging.getLogger(__name__)


class PurchaseOrderService:
    """Service for managing purchase orders."""
    
    def __init__(self, db: AsyncSession):
        """Initialize with database session."""
        self.db = db
    
    async def generate_lpo_from_requisition(
        self,
        school_id: UUID,
        requisition_id: UUID,
        supplier_id: UUID | None = None,
        expected_delivery_date: date | None = None,
    ) -> dict:
        """
        Generate Local Purchase Order from approved requisition.
        
        Called automatically after requisition approval.
        
        Args:
            school_id: Tenant identifier
            requisition_id: Approved requisition
            supplier_id: Supplier to order from (optional for auto-generation)
            expected_delivery_date: Expected delivery date
        
        Returns:
            dict with purchase_order_id, lpo_number, status, message
        
        Raises:
            NotFoundError: If requisition not found
            ValidationError: If requisition not approved
        """
        logger.debug(f"Generating LPO for requisition {requisition_id}")
        
        # STEP 1: Fetch requisition
        req_query = select(PurchaseRequisition).where(
            and_(
                PurchaseRequisition.id == requisition_id,
                PurchaseRequisition.school_id == school_id,
            )
        )
        requisition = await self.db.scalar(req_query)
        
        if not requisition:
            logger.warning(f"Requisition {requisition_id} not found")
            raise NotFoundError(f"Requisition {requisition_id} not found")
        
        # Validate requisition is approved
        if requisition.status != RequisitionStatus.APPROVED:
            raise ValidationError(
                f"Requisition must be APPROVED to generate LPO. Current status: {requisition.status.value}"
            )
        
        # Validate supplier
        if supplier_id:
            supplier_query = select(Supplier).where(
                and_(
                    Supplier.id == supplier_id,
                    Supplier.school_id == school_id,
                )
            )
            supplier = await self.db.scalar(supplier_query)
            
            if not supplier:
                raise NotFoundError(f"Supplier {supplier_id} not found")
            
            if not supplier.is_approved:
                raise ValidationError(
                    f"Supplier {supplier.name} is not approved for procurement"
                )
        else:
            supplier = None
        
        # STEP 2: Generate LPO number
        lpo_number = await self._generate_lpo_number(school_id)
        
        # STEP 3: Create purchase order
        purchase_order = PurchaseOrder(
            school_id=school_id,
            lpo_number=lpo_number,
            requisition_id=requisition_id,
            supplier_id=supplier_id,
            order_date=date.today(),
            expected_delivery_date=expected_delivery_date,
            total_amount=requisition.total_amount,
            status=LPOStatus.OPEN,
        )
        
        self.db.add(purchase_order)
        await self.db.flush()  # Get PO ID
        
        # STEP 4: Create LPO line items from requisition items
        for req_item in requisition.line_items:
            po_item = PurchaseOrderItem(
                school_id=school_id,
                purchase_order_id=purchase_order.id,
                description=req_item.description,
                quantity=req_item.quantity,
                unit_price=req_item.unit_price,
                total_price=req_item.total_price,
                received_quantity=0,
            )
            self.db.add(po_item)
        
        await self.db.commit()
        
        logger.info(
            f"LPO generated: {purchase_order.id}, number={lpo_number}, "
            f"supplier={supplier_id}, amount={requisition.total_amount}"
        )
        
        return {
            "purchase_order_id": str(purchase_order.id),
            "lpo_number": lpo_number,
            "requisition_id": str(requisition_id),
            "requisition_number": requisition.requisition_number,
            "supplier_id": str(supplier_id) if supplier_id else None,
            "total_amount": requisition.total_amount,
            "status": LPOStatus.OPEN.value,
            "order_date": date.today().isoformat(),
            "message": f"LPO {lpo_number} generated from requisition {requisition.requisition_number}",
        }
    
    async def get_purchase_order(
        self,
        school_id: UUID,
        po_id: UUID,
    ) -> dict:
        """Get purchase order detail with line items."""
        po_query = select(PurchaseOrder).where(
            and_(
                PurchaseOrder.id == po_id,
                PurchaseOrder.school_id == school_id,
            )
        )
        po = await self.db.scalar(po_query)
        
        if not po:
            raise NotFoundError(f"Purchase Order {po_id} not found")
        
        line_items = [
            {
                "id": str(item.id),
                "description": item.description,
                "quantity": item.quantity,
                "unit_price": item.unit_price,
                "total_price": item.total_price,
                "received_quantity": item.received_quantity,
            }
            for item in po.line_items
        ]
        
        # Get supplier info if available
        supplier_name = po.supplier.name if po.supplier else None
        requisition_number = po.requisition.requisition_number if po.requisition else None
        
        return {
            "id": str(po.id),
            "lpo_number": po.lpo_number,
            "requisition_number": requisition_number,
            "supplier_name": supplier_name,
            "supplier_id": str(po.supplier_id) if po.supplier_id else None,
            "order_date": po.order_date.isoformat(),
            "expected_delivery_date": po.expected_delivery_date.isoformat() if po.expected_delivery_date else None,
            "total_amount": po.total_amount,
            "status": po.status.value,
            "line_items": line_items,
            "created_at": po.created_at.isoformat(),
        }
    
    async def list_purchase_orders(
        self,
        school_id: UUID,
        status: str | None = None,
        supplier_id: UUID | None = None,
    ) -> list[dict]:
        """List purchase orders with filters."""
        query = select(PurchaseOrder).where(
            PurchaseOrder.school_id == school_id
        )
        
        if status:
            query = query.where(PurchaseOrder.status == LPOStatus(status))
        
        if supplier_id:
            query = query.where(PurchaseOrder.supplier_id == supplier_id)
        
        query = query.order_by(PurchaseOrder.order_date.desc())
        
        result = await self.db.execute(query)
        orders = result.scalars().all()
        
        return [
            {
                "id": str(o.id),
                "lpo_number": o.lpo_number,
                "supplier_name": o.supplier.name if o.supplier else None,
                "order_date": o.order_date.isoformat(),
                "total_amount": o.total_amount,
                "status": o.status.value,
                "created_at": o.created_at.isoformat(),
            }
            for o in orders
        ]
    
    async def _generate_lpo_number(self, school_id: UUID) -> str:
        """Generate unique LPO number."""
        # Query max existing LPO number
        query = select(PurchaseOrder).where(
            PurchaseOrder.school_id == school_id
        ).order_by(PurchaseOrder.created_at.desc())
        
        result = await self.db.execute(query)
        last_po = result.scalars().first()
        
        if last_po and last_po.lpo_number:
            try:
                parts = last_po.lpo_number.split("-")
                sequence = int(parts[-1]) + 1
            except (IndexError, ValueError):
                sequence = 1
        else:
            sequence = 1
        
        year = datetime.utcnow().year
        lpo_number = f"LPO-{year}-{sequence:04d}"
        
        logger.debug(f"Generated LPO number: {lpo_number}")
        
        return lpo_number
