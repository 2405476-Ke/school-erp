"""
Accounts Payable Service with 3-Way Matching Algorithm.

3-WAY MATCH PROCESS:
1. Invoice Quantities must match GRN Quantities (within 2% tolerance)
2. Invoice Prices must match LPO Prices (within 2% tolerance)
3. If match succeeds: Create AP Payment record, post GL entry
4. If match fails: Mark invoice UNMATCHED, raise error
"""

import logging
from datetime import date, datetime, timedelta
from decimal import Decimal
from uuid import UUID

from sqlalchemy import and_, select
from sqlalchemy.ext.asyncio import AsyncSession

from src.core.exceptions import NotFoundError, ValidationError
from src.modules.procurement.models.procurement import (
    SupplierInvoice,
    InvoiceLineItem,
    GoodsReceivedNote,
    GRNLineItem,
    PurchaseOrder,
    PurchaseOrderItem,
    APPayment,
    InvoiceStatus,
    PaymentStatus,
)

logger = logging.getLogger(__name__)

# 3-Way Match tolerance: 2%
MATCH_TOLERANCE = Decimal("0.02")


class ThreeWayMatchError(ValidationError):
    """Error raised when 3-way match fails."""
    pass


class APService:
    """Service for Accounts Payable processing."""
    
    def __init__(self, db: AsyncSession):
        """Initialize with database session."""
        self.db = db
    
    async def process_supplier_invoice(
        self,
        school_id: UUID,
        invoice_id: UUID,
        grn_id: UUID,
    ) -> dict:
        """
        CRITICAL ALGORITHM: Process supplier invoice with 3-way matching.
        
        3-WAY MATCH LOGIC:
        1. Fetch Invoice, GRN, and LPO
        2. For each invoice line item:
           a. Find matching GRN line item by description
           b. Match quantities: abs(invoice_qty - grn_qty) / grn_qty <= 2%
           c. Find matching LPO line item by description
           d. Match prices: abs(invoice_price - lpo_price) / lpo_price <= 2%
        3. If ANY match fails: Raise ThreeWayMatchError, mark invoice UNMATCHED
        4. If ALL matches succeed:
           a. Create APPayment record
           b. Post GL entry: DR Expense (or Inventory), CR Accounts Payable
           c. Mark invoice as MATCHED
        
        Args:
            school_id: Tenant identifier
            invoice_id: Supplier invoice to match
            grn_id: Goods Received Note to match against
        
        Returns:
            dict with invoice_id, status, match_result, ap_payment_id, message
        
        Raises:
            ThreeWayMatchError: If quantities or prices don't match (>2% variance)
            NotFoundError: If invoice, GRN, or LPO not found
        """
        logger.debug(f"Processing 3-way match: invoice={invoice_id}, grn={grn_id}")
        
        # STEP 1: Fetch invoice with line items
        invoice_query = select(SupplierInvoice).where(
            and_(
                SupplierInvoice.id == invoice_id,
                SupplierInvoice.school_id == school_id,
            )
        )
        invoice = await self.db.scalar(invoice_query)
        
        if not invoice:
            logger.warning(f"Invoice {invoice_id} not found")
            raise NotFoundError(f"Invoice {invoice_id} not found")
        
        # Validate invoice is in SUBMITTED status
        if invoice.status != InvoiceStatus.SUBMITTED:
            raise ValidationError(
                f"Invoice must be SUBMITTED to process. Current status: {invoice.status.value}"
            )
        
        # STEP 2: Fetch GRN with line items
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
        
        # STEP 3: Fetch LPO with line items
        po_query = select(PurchaseOrder).where(
            and_(
                PurchaseOrder.id == grn.purchase_order_id,
                PurchaseOrder.school_id == school_id,
            )
        )
        lpo = await self.db.scalar(po_query)
        
        if not lpo:
            logger.warning(f"LPO not found for GRN {grn_id}")
            raise NotFoundError(f"LPO not found for GRN")
        
        logger.debug(
            f"3-way match: Invoice={invoice.invoice_number}, "
            f"GRN={grn.grn_number}, LPO={lpo.lpo_number}"
        )
        
        # STEP 4: Perform 3-way matching
        match_errors = []
        
        for inv_item in invoice.line_items:
            logger.debug(f"Matching invoice item: {inv_item.description}")
            
            # Find matching GRN line item by description
            grn_item = self._find_matching_item(grn.line_items, inv_item.description)
            
            if not grn_item:
                error = f"Invoice item '{inv_item.description}' not found in GRN"
                logger.warning(error)
                match_errors.append(error)
                continue
            
            # Match quantities with 2% tolerance
            qty_match = self._match_quantities(
                invoice_qty=inv_item.quantity,
                grn_qty=grn_item.quantity_received,
            )
            
            if not qty_match:
                error = (
                    f"Item '{inv_item.description}': Quantity mismatch. "
                    f"Invoice={inv_item.quantity}, GRN={grn_item.quantity_received} "
                    f"(variance > 2%)"
                )
                logger.warning(error)
                match_errors.append(error)
                continue
            
            logger.debug(
                f"Quantity match OK: {inv_item.description} "
                f"(invoice={inv_item.quantity}, grn={grn_item.quantity_received})"
            )
            
            # Find matching LPO line item by description
            lpo_item = self._find_matching_item(lpo.line_items, inv_item.description)
            
            if not lpo_item:
                error = f"Invoice item '{inv_item.description}' not found in LPO"
                logger.warning(error)
                match_errors.append(error)
                continue
            
            # Match prices with 2% tolerance
            price_match = self._match_prices(
                invoice_price=inv_item.unit_price,
                lpo_price=lpo_item.unit_price,
            )
            
            if not price_match:
                error = (
                    f"Item '{inv_item.description}': Price mismatch. "
                    f"Invoice={inv_item.unit_price}, LPO={lpo_item.unit_price} "
                    f"(variance > 2%)"
                )
                logger.warning(error)
                match_errors.append(error)
                continue
            
            logger.debug(
                f"Price match OK: {inv_item.description} "
                f"(invoice={inv_item.unit_price}, lpo={lpo_item.unit_price})"
            )
        
        # STEP 5: Handle match results
        if match_errors:
            # Match failed
            logger.error(f"3-way match FAILED for invoice {invoice_id}")
            
            # Update invoice status
            invoice.status = InvoiceStatus.UNMATCHED
            invoice.three_way_match_result = "\n".join(match_errors)
            
            await self.db.commit()
            
            error_message = "3-Way Match FAILED:\n" + "\n".join(f"  - {e}" for e in match_errors)
            logger.debug(error_message)
            
            raise ThreeWayMatchError(error_message)
        
        # STEP 6: Match succeeded - create AP Payment
        logger.info(f"3-way match SUCCEEDED for invoice {invoice_id}")
        
        # Calculate due date (typically 30 days from invoice date)
        due_date = invoice.invoice_date + timedelta(days=30)
        
        ap_payment = APPayment(
            school_id=school_id,
            invoice_id=invoice_id,
            supplier_id=invoice.supplier_id,
            payment_amount=invoice.invoice_amount,
            due_date=due_date,
            status=PaymentStatus.PENDING,
        )
        
        self.db.add(ap_payment)
        
        # Update invoice status
        invoice.status = InvoiceStatus.MATCHED
        invoice.three_way_match_result = "Match successful"
        
        await self.db.commit()
        
        logger.info(
            f"AP Payment created: payment={ap_payment.id}, "
            f"invoice={invoice.invoice_number}, amount={invoice.invoice_amount}"
        )
        
        # STEP 7: Post GL entry (asynchronously call Journal Service)
        # For now, we'll prepare the GL posting data
        # In production, this would call JournalService.post_journal()
        
        gl_posting_data = {
            "school_id": school_id,
            "transaction_date": datetime.utcnow().date(),
            "description": f"AP Posting: Invoice {invoice.invoice_number} from {invoice.supplier.name}",
            "entries": [
                {
                    "account_code": "5001",  # Expenses/Cost of Goods Sold (to be configured)
                    "debit": invoice.invoice_amount,
                    "credit": Decimal("0.00"),
                    "description": f"Invoice {invoice.invoice_number}",
                },
                {
                    "account_code": "2001",  # Accounts Payable (to be configured)
                    "debit": Decimal("0.00"),
                    "credit": invoice.invoice_amount,
                    "description": f"AP - {invoice.supplier.name}",
                },
            ],
        }
        
        logger.debug(f"GL posting data prepared: {gl_posting_data}")
        
        # TODO: Call JournalService.post_journal(gl_posting_data)
        # For now, just store the data in ap_payment.gl_entry_id as None
        
        return {
            "invoice_id": str(invoice_id),
            "invoice_number": invoice.invoice_number,
            "status": InvoiceStatus.MATCHED.value,
            "match_result": "3-way match successful",
            "ap_payment_id": str(ap_payment.id),
            "payment_amount": invoice.invoice_amount,
            "due_date": due_date.isoformat(),
            "message": f"Invoice {invoice.invoice_number} matched successfully. "
                      f"AP Payment {str(ap_payment.id)} created.",
        }
    
    def _find_matching_item(self, items: list, description: str):
        """
        Find item in list by description (case-insensitive, partial match).
        
        Used to match invoice items to GRN/LPO items.
        """
        description_lower = description.lower().strip()
        
        for item in items:
            item_desc_lower = item.description.lower().strip()
            
            # Try exact match first
            if item_desc_lower == description_lower:
                return item
            
            # Try partial match (at least 80% match)
            if self._string_similarity(item_desc_lower, description_lower) > 0.8:
                return item
        
        return None
    
    def _match_quantities(
        self,
        invoice_qty: Decimal,
        grn_qty: Decimal,
    ) -> bool:
        """
        Match quantities with 2% tolerance.
        
        abs(invoice_qty - grn_qty) / grn_qty <= 2%
        """
        if grn_qty == 0:
            return invoice_qty == 0
        
        variance = abs(invoice_qty - grn_qty) / grn_qty
        
        return variance <= MATCH_TOLERANCE
    
    def _match_prices(
        self,
        invoice_price: Decimal,
        lpo_price: Decimal,
    ) -> bool:
        """
        Match prices with 2% tolerance.
        
        abs(invoice_price - lpo_price) / lpo_price <= 2%
        """
        if lpo_price == 0:
            return invoice_price == 0
        
        variance = abs(invoice_price - lpo_price) / lpo_price
        
        return variance <= MATCH_TOLERANCE
    
    def _string_similarity(self, s1: str, s2: str) -> float:
        """
        Calculate string similarity using basic algorithm.
        
        Returns value between 0 and 1 (1 = perfect match).
        """
        if not s1 or not s2:
            return 0.0
        
        # Simple similarity: count matching characters
        matches = sum(1 for c1, c2 in zip(s1, s2) if c1 == c2)
        total = max(len(s1), len(s2))
        
        return matches / total if total > 0 else 0.0
    
    async def process_ap_payment(
        self,
        school_id: UUID,
        payment_id: UUID,
        payment_date: datetime,
        payment_reference: str,
    ) -> dict:
        """
        Process AP payment (mark as PAID).
        
        Args:
            school_id: Tenant identifier
            payment_id: AP Payment to process
            payment_date: Date payment was made
            payment_reference: Bank reference/check number
        
        Returns:
            dict with payment_id, status, payment_date, message
        
        Raises:
            NotFoundError: If payment not found
            ValidationError: If payment not PENDING
        """
        logger.debug(f"Processing AP payment {payment_id}")
        
        # Fetch payment
        payment_query = select(APPayment).where(
            and_(
                APPayment.id == payment_id,
                APPayment.school_id == school_id,
            )
        )
        payment = await self.db.scalar(payment_query)
        
        if not payment:
            logger.warning(f"Payment {payment_id} not found")
            raise NotFoundError(f"Payment {payment_id} not found")
        
        # Validate status
        if payment.status != PaymentStatus.PENDING:
            raise ValidationError(
                f"Can only process PENDING payments. Current status: {payment.status.value}"
            )
        
        # Update payment
        payment.status = PaymentStatus.PAID
        payment.payment_date = payment_date
        payment.payment_reference = payment_reference
        
        await self.db.commit()
        
        logger.info(
            f"AP Payment processed: payment={payment_id}, "
            f"reference={payment_reference}, amount={payment.payment_amount}"
        )
        
        return {
            "payment_id": str(payment_id),
            "invoice_number": payment.invoice.invoice_number,
            "supplier_name": payment.invoice.supplier.name,
            "status": PaymentStatus.PAID.value,
            "payment_amount": payment.payment_amount,
            "payment_date": payment_date.isoformat(),
            "payment_reference": payment_reference,
            "message": f"Payment for invoice {payment.invoice.invoice_number} processed.",
        }
    
    async def get_ap_payment(
        self,
        school_id: UUID,
        payment_id: UUID,
    ) -> dict:
        """Get AP payment detail."""
        payment_query = select(APPayment).where(
            and_(
                APPayment.id == payment_id,
                APPayment.school_id == school_id,
            )
        )
        payment = await self.db.scalar(payment_query)
        
        if not payment:
            raise NotFoundError(f"Payment {payment_id} not found")
        
        return {
            "id": str(payment.id),
            "invoice_id": str(payment.invoice_id),
            "invoice_number": payment.invoice.invoice_number if payment.invoice else None,
            "supplier_name": payment.invoice.supplier.name if payment.invoice and payment.invoice.supplier else None,
            "payment_amount": payment.payment_amount,
            "due_date": payment.due_date.isoformat(),
            "status": payment.status.value,
            "payment_date": payment.payment_date.isoformat() if payment.payment_date else None,
            "payment_reference": payment.payment_reference,
            "created_at": payment.created_at.isoformat(),
        }
    
    async def list_ap_payments(
        self,
        school_id: UUID,
        status: str | None = None,
    ) -> list[dict]:
        """List AP payments with optional status filter."""
        query = select(APPayment).where(
            APPayment.school_id == school_id
        )
        
        if status:
            query = query.where(APPayment.status == PaymentStatus(status))
        
        query = query.order_by(APPayment.created_at.desc())
        
        result = await self.db.execute(query)
        payments = result.scalars().all()
        
        return [
            {
                "id": str(p.id),
                "invoice_number": p.invoice.invoice_number if p.invoice else None,
                "supplier_name": p.invoice.supplier.name if p.invoice and p.invoice.supplier else None,
                "payment_amount": p.payment_amount,
                "due_date": p.due_date.isoformat(),
                "status": p.status.value,
                "created_at": p.created_at.isoformat(),
            }
            for p in payments
        ]
