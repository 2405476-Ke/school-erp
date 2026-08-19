"""
Supplier Invoice Service.

Manages invoice submission and tracking.
"""

import logging
from datetime import date, datetime
from decimal import Decimal
from uuid import UUID

from sqlalchemy import and_, select
from sqlalchemy.ext.asyncio import AsyncSession

from src.core.exceptions import NotFoundError, ValidationError
from src.modules.procurement.models.procurement import (
    SupplierInvoice,
    InvoiceLineItem,
    PurchaseOrder,
    Supplier,
    InvoiceStatus,
)

logger = logging.getLogger(__name__)


class InvoiceService:
    """Service for managing supplier invoices."""
    
    def __init__(self, db: AsyncSession):
        """Initialize with database session."""
        self.db = db
    
    async def submit_invoice(
        self,
        school_id: UUID,
        purchase_order_id: UUID,
        supplier_id: UUID,
        invoice_number: str,
        invoice_date: date,
        items: list[dict],  # [{description, quantity, unit_price}, ...]
        notes: str | None = None,
    ) -> dict:
        """
        Submit supplier invoice for processing.
        
        Args:
            school_id: Tenant identifier
            purchase_order_id: LPO associated with invoice
            supplier_id: Supplier submitting invoice
            invoice_number: Invoice number
            invoice_date: Invoice date
            items: List of {description, quantity, unit_price}
            notes: Additional notes
        
        Returns:
            dict with invoice_id, invoice_number, status, message
        
        Raises:
            NotFoundError: If LPO or supplier not found
            ValidationError: If duplicate invoice number or invalid items
        """
        logger.debug(
            f"Submitting invoice: {invoice_number} for LPO {purchase_order_id}, "
            f"supplier {supplier_id}"
        )
        
        # STEP 1: Validate LPO exists
        lpo_query = select(PurchaseOrder).where(
            and_(
                PurchaseOrder.id == purchase_order_id,
                PurchaseOrder.school_id == school_id,
            )
        )
        lpo = await self.db.scalar(lpo_query)
        
        if not lpo:
            raise NotFoundError(f"LPO {purchase_order_id} not found")
        
        # STEP 2: Validate supplier exists
        supplier_query = select(Supplier).where(
            and_(
                Supplier.id == supplier_id,
                Supplier.school_id == school_id,
            )
        )
        supplier = await self.db.scalar(supplier_query)
        
        if not supplier:
            raise NotFoundError(f"Supplier {supplier_id} not found")
        
        # STEP 3: Check for duplicate invoice number (per supplier, per school)
        existing = await self.db.scalar(
            select(SupplierInvoice).where(
                and_(
                    SupplierInvoice.school_id == school_id,
                    SupplierInvoice.supplier_id == supplier_id,
                    SupplierInvoice.invoice_number == invoice_number,
                )
            )
        )
        
        if existing:
            raise ValidationError(
                f"Invoice {invoice_number} from {supplier.name} already exists"
            )
        
        # STEP 4: Validate items
        if not items:
            raise ValidationError("Invoice must have at least one item")
        
        total_amount = Decimal("0.00")
        invoice_items_data = []
        
        for idx, item in enumerate(items):
            try:
                qty = Decimal(str(item.get("quantity", 0)))
                unit_price = Decimal(str(item.get("unit_price", 0)))
            except (ValueError, TypeError):
                raise ValidationError(f"Item {idx+1}: Invalid quantity or unit_price")
            
            if qty <= 0 or unit_price <= 0:
                raise ValidationError(f"Item {idx+1}: Quantity and unit_price must be positive")
            
            total_price = (qty * unit_price).quantize(Decimal("0.01"))
            total_amount += total_price
            
            invoice_items_data.append({
                "description": item.get("description", ""),
                "quantity": qty,
                "unit_price": unit_price,
                "total_price": total_price,
            })
        
        if total_amount <= 0:
            raise ValidationError("Invoice total amount must be positive")
        
        # STEP 5: Create invoice
        invoice = SupplierInvoice(
            school_id=school_id,
            invoice_number=invoice_number,
            purchase_order_id=purchase_order_id,
            supplier_id=supplier_id,
            invoice_date=invoice_date,
            invoice_amount=total_amount,
            status=InvoiceStatus.SUBMITTED,
            notes=notes,
        )
        
        self.db.add(invoice)
        await self.db.flush()
        
        # STEP 6: Create invoice line items
        for item_data in invoice_items_data:
            line_item = InvoiceLineItem(
                school_id=school_id,
                invoice_id=invoice.id,
                description=item_data["description"],
                quantity=item_data["quantity"],
                unit_price=item_data["unit_price"],
                total_price=item_data["total_price"],
            )
            self.db.add(line_item)
        
        await self.db.commit()
        
        logger.info(
            f"Invoice submitted: {invoice.id}, number={invoice_number}, "
            f"supplier={supplier.name}, amount={total_amount}"
        )
        
        return {
            "invoice_id": str(invoice.id),
            "invoice_number": invoice_number,
            "supplier_name": supplier.name,
            "lpo_number": lpo.lpo_number,
            "invoice_date": invoice_date.isoformat(),
            "invoice_amount": total_amount,
            "status": InvoiceStatus.SUBMITTED.value,
            "item_count": len(invoice_items_data),
            "message": f"Invoice {invoice_number} submitted. Awaiting 3-way match.",
        }
    
    async def get_invoice(
        self,
        school_id: UUID,
        invoice_id: UUID,
    ) -> dict:
        """Get invoice detail with line items."""
        invoice_query = select(SupplierInvoice).where(
            and_(
                SupplierInvoice.id == invoice_id,
                SupplierInvoice.school_id == school_id,
            )
        )
        invoice = await self.db.scalar(invoice_query)
        
        if not invoice:
            raise NotFoundError(f"Invoice {invoice_id} not found")
        
        line_items = [
            {
                "id": str(item.id),
                "description": item.description,
                "quantity": item.quantity,
                "unit_price": item.unit_price,
                "total_price": item.total_price,
            }
            for item in invoice.line_items
        ]
        
        supplier_name = invoice.supplier.name if invoice.supplier else None
        lpo_number = invoice.purchase_order.lpo_number if invoice.purchase_order else None
        
        return {
            "id": str(invoice.id),
            "invoice_number": invoice.invoice_number,
            "supplier_name": supplier_name,
            "supplier_id": str(invoice.supplier_id),
            "lpo_number": lpo_number,
            "purchase_order_id": str(invoice.purchase_order_id),
            "invoice_date": invoice.invoice_date.isoformat(),
            "invoice_amount": invoice.invoice_amount,
            "status": invoice.status.value,
            "line_items": line_items,
            "three_way_match_result": invoice.three_way_match_result,
            "notes": invoice.notes,
            "created_at": invoice.created_at.isoformat(),
        }
    
    async def list_invoices(
        self,
        school_id: UUID,
        status: str | None = None,
        supplier_id: UUID | None = None,
        purchase_order_id: UUID | None = None,
    ) -> list[dict]:
        """List invoices with filters."""
        query = select(SupplierInvoice).where(
            SupplierInvoice.school_id == school_id
        )
        
        if status:
            query = query.where(SupplierInvoice.status == InvoiceStatus(status))
        
        if supplier_id:
            query = query.where(SupplierInvoice.supplier_id == supplier_id)
        
        if purchase_order_id:
            query = query.where(SupplierInvoice.purchase_order_id == purchase_order_id)
        
        query = query.order_by(SupplierInvoice.invoice_date.desc())
        
        result = await self.db.execute(query)
        invoices = result.scalars().all()
        
        return [
            {
                "id": str(i.id),
                "invoice_number": i.invoice_number,
                "supplier_name": i.supplier.name if i.supplier else None,
                "lpo_number": i.purchase_order.lpo_number if i.purchase_order else None,
                "invoice_date": i.invoice_date.isoformat(),
                "invoice_amount": i.invoice_amount,
                "status": i.status.value,
                "created_at": i.created_at.isoformat(),
            }
            for i in invoices
        ]
