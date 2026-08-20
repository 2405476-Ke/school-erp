
import logging
from uuid import UUID
from decimal import Decimal
from typing import List, Optional
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from src.shared.exceptions import ValidationError, NotFoundError
from src.modules.finance.models.procurement import (
    PurchaseRequisition, RequisitionItem, VoteHeadBudget, RequisitionStatus,
    LocalPurchaseOrder, GoodsReceivedNote, SupplierInvoice, LPOStatus
)
import hashlib
import uuid

logger = logging.getLogger(__name__)

class ProcurementService:
    def __init__(self, db: AsyncSession):
        self.db = db

    async def create_requisition(
        self, school_id: UUID, user_id: UUID, department: str, description: str, 
        vote_head_account_id: UUID, items: List[dict]
    ) -> PurchaseRequisition:
        # Calculate Total
        total_amount = Decimal("0.00")
        for item in items:
            total_amount += Decimal(str(item['quantity'])) * Decimal(str(item['unit_price']))
            
        # BR-PRO-002: Hard-stop Budget Overrun (FRD-PRO-002)
        budget_query = select(VoteHeadBudget).where(VoteHeadBudget.account_id == vote_head_account_id)
        budget = await self.db.scalar(budget_query)
        
        # If budget model doesn't exist, assume 0
        available = budget.available_balance if budget else Decimal("0.00")
        
        if total_amount > available:
            raise ValidationError(
                f"Budget Overrun: Requested amount (KES {total_amount:,.2f}) exceeds "
                f"available budget (KES {available:,.2f}) for this Vote Head."
            )

        # Create Requisition (Draft / Pending Tier 1)
        req = PurchaseRequisition(
            school_id=school_id,
            requisition_number="PR-001", # Mock sequence
            department=department,
            description=description,
            vote_head_account_id=vote_head_account_id,
            status=RequisitionStatus.PENDING_TIER_1.value,
            total_amount=total_amount,
            requested_by_id=user_id,
        )
        self.db.add(req)
        await self.db.flush()
        
        # Add Items
        for item_data in items:
            qty = Decimal(str(item_data['quantity']))
            price = Decimal(str(item_data['unit_price']))
            req_item = RequisitionItem(
                requisition_id=req.id,
                description=item_data['description'],
                quantity=qty,
                unit_price=price,
                total_price=qty * price
            )
            self.db.add(req_item)
            
        # Commit funds
        if budget:
            budget.committed_amount += total_amount
            
        await self.db.commit()
        return req

    async def approve_requisition(
        self, req_id: UUID, user_id: UUID, role: str
    ) -> PurchaseRequisition:
        req = await self.db.scalar(select(PurchaseRequisition).where(PurchaseRequisition.id == req_id))
        if not req: raise NotFoundError("Requisition not found")

        # BR-PRO-003: Maker-Checker Workflow
        if req.status == RequisitionStatus.PENDING_TIER_1.value:
            if role != "BURSAR":
                raise ValidationError("Tier 1 approval requires BURSAR role.")
            req.status = RequisitionStatus.PENDING_TIER_2.value
            req.tier_1_approved_by_id = user_id
            
        elif req.status == RequisitionStatus.PENDING_TIER_2.value:
            if role != "PRINCIPAL":
                raise ValidationError("Tier 2 approval requires PRINCIPAL role.")
            req.status = RequisitionStatus.APPROVED.value
            req.tier_2_approved_by_id = user_id
            
            # When fully approved, convert committed to spent (mock logic for demo)
            budget = await self.db.scalar(select(VoteHeadBudget).where(VoteHeadBudget.account_id == req.vote_head_account_id))
            if budget:
                budget.committed_amount -= req.total_amount
                budget.spent_amount += req.total_amount
        else:
            raise ValidationError(f"Cannot approve requisition in status {req.status}")
            
        await self.db.commit()
        return req


    async def generate_lpo(self, requisition_id: UUID, user_id: UUID) -> LocalPurchaseOrder:
        """
        Generates a digitally signed LPO from an approved requisition (BR-PRO-004)
        """
        req = await self.db.scalar(select(PurchaseRequisition).where(PurchaseRequisition.id == requisition_id))
        if not req:
            raise NotFoundError("Requisition not found")
            
        if req.status != RequisitionStatus.APPROVED.value:
            raise ValidationError("Requisition must be fully approved to generate LPO")
            
        # Generate digital signature (hash of req data + secret)
        sig_data = f"{req.id}-{req.total_amount}-secret_key_123"
        digital_sig = hashlib.sha256(sig_data.encode()).hexdigest()
        
        lpo = LocalPurchaseOrder(
            school_id=req.school_id,
            lpo_number=f"LPO-{str(uuid.uuid4())[:8].upper()}",
            requisition_id=req.id,
            status=LPOStatus.GENERATED.value,
            total_amount=req.total_amount,
            issued_by_id=user_id,
            digital_signature=digital_sig
        )
        self.db.add(lpo)
        
        req.status = RequisitionStatus.FULFILLED.value
        await self.db.commit()
        return lpo

    async def generate_grn(self, lpo_id: UUID, user_id: UUID, delivery_note: str) -> GoodsReceivedNote:
        """
        Storekeeper generates GRN against an LPO (BR-PRO-005)
        """
        lpo = await self.db.scalar(select(LocalPurchaseOrder).where(LocalPurchaseOrder.id == lpo_id))
        if not lpo:
            raise NotFoundError("LPO not found")
            
        grn = GoodsReceivedNote(
            school_id=lpo.school_id,
            grn_number=f"GRN-{str(uuid.uuid4())[:8].upper()}",
            lpo_id=lpo.id,
            received_by_id=user_id,
            delivery_note_number=delivery_note
        )
        self.db.add(grn)
        
        lpo.status = LPOStatus.FULFILLED.value
        await self.db.commit()
        return grn

    async def process_supplier_invoice(self, lpo_id: UUID, invoice_num: str, amount: Decimal) -> SupplierInvoice:
        """
        Receive supplier invoice
        """
        lpo = await self.db.scalar(select(LocalPurchaseOrder).where(LocalPurchaseOrder.id == lpo_id))
        inv = SupplierInvoice(
            school_id=lpo.school_id,
            invoice_number=invoice_num,
            lpo_id=lpo.id,
            invoice_amount=amount
        )
        self.db.add(inv)
        await self.db.commit()
        return inv

    async def execute_3_way_match(self, lpo_id: UUID) -> dict:
        """
        Enforces 3-way match: LPO + GRN + Invoice (BR-PRO-006)
        """
        lpo = await self.db.scalar(
            select(LocalPurchaseOrder)
            .options(selectinload(LocalPurchaseOrder.grns), selectinload(LocalPurchaseOrder.invoices))
            .where(LocalPurchaseOrder.id == lpo_id)
        )
        
        if not lpo:
            raise NotFoundError("LPO not found")
            
        if not lpo.grns:
            raise ValidationError("3-Way Match Failed: No Goods Received Note (GRN) found.")
            
        if not lpo.invoices:
            raise ValidationError("3-Way Match Failed: No Supplier Invoice found.")
            
        invoice = lpo.invoices[0] # Take latest invoice
        
        # Check amounts
        if invoice.invoice_amount > lpo.total_amount:
            raise ValidationError(
                f"3-Way Match Failed: Invoice amount (KES {invoice.invoice_amount}) "
                f"exceeds LPO amount (KES {lpo.total_amount})"
            )
            
        # Match successful
        invoice.is_three_way_matched = True
        invoice.approved_for_payment = True
        await self.db.commit()
        
        return {
            "status": "SUCCESS",
            "message": "3-Way Match verified successfully. Account Payable is now flagged for payment.",
            "invoice_id": invoice.id
        }
