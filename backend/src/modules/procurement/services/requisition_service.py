"""
Purchase Requisition Service with Delegation of Authority (DOA) logic.

DOA APPROVAL WORKFLOW:
- Amount <= 10,000 KES: Requires BURSAR approval
- Amount <= 50,000 KES: Requires PRINCIPAL approval
- Amount > 50,000 KES: Requires BOM (Board of Management) approval

Upon final approval:
- Auto-generate PurchaseOrder (LPO) with OPEN status
- Send to selected supplier
"""

import logging
from datetime import date, datetime
from decimal import Decimal
from uuid import UUID

from sqlalchemy import and_, select
from sqlalchemy.ext.asyncio import AsyncSession

from src.core.exceptions import NotFoundError, ValidationError
from src.modules.procurement.models.procurement import (
    PurchaseRequisition,
    PurchaseRequisitionItem,
    RequisitionStatus,
    ApprovalLevel,
)
from src.modules.auth.models.user import User, Role

logger = logging.getLogger(__name__)

# DOA thresholds in KES
DOA_THRESHOLDS = {
    10000: ApprovalLevel.BURSAR,      # <= 10k needs BURSAR
    50000: ApprovalLevel.PRINCIPAL,   # <= 50k needs PRINCIPAL
    float("inf"): ApprovalLevel.BOM,  # > 50k needs BOM
}


class RequisitionService:
    """Service for managing purchase requisitions."""
    
    def __init__(self, db: AsyncSession):
        """Initialize with database session."""
        self.db = db
    
    async def create_requisition(
        self,
        school_id: UUID,
        description: str,
        items: list[dict],  # [{description, quantity, unit_price}, ...]
        created_by_user_id: UUID,
    ) -> dict:
        """
        Create purchase requisition in DRAFT status.
        
        Args:
            school_id: Tenant identifier
            description: Requisition purpose
            items: List of {description, quantity, unit_price}
            created_by_user_id: User creating requisition
        
        Returns:
            dict with requisition_id, requisition_number, status, total_amount, required_approval_level
        
        Raises:
            ValidationError: If invalid data
        """
        logger.debug(f"Creating purchase requisition for school {school_id}")
        
        # Validate items
        if not items:
            raise ValidationError("Requisition must have at least one item")
        
        # Calculate total amount and create line items
        total_amount = Decimal("0.00")
        line_items_data = []
        
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
            
            line_items_data.append({
                "description": item.get("description", ""),
                "quantity": qty,
                "unit_price": unit_price,
                "total_price": total_price,
            })
        
        if total_amount <= 0:
            raise ValidationError("Requisition total amount must be positive")
        
        # Determine required approval level based on amount
        required_level = self._determine_approval_level(total_amount)
        logger.debug(f"Requisition amount {total_amount} requires {required_level.value} approval")
        
        # Generate requisition number
        requisition_number = await self._generate_requisition_number(school_id)
        
        # Create requisition
        requisition = PurchaseRequisition(
            school_id=school_id,
            requisition_number=requisition_number,
            description=description,
            total_amount=total_amount,
            status=RequisitionStatus.DRAFT,
            required_approval_level=required_level,
        )
        
        self.db.add(requisition)
        await self.db.flush()  # Get requisition ID
        
        # Create line items
        for item_data in line_items_data:
            line_item = PurchaseRequisitionItem(
                school_id=school_id,
                requisition_id=requisition.id,
                description=item_data["description"],
                quantity=item_data["quantity"],
                unit_price=item_data["unit_price"],
                total_price=item_data["total_price"],
            )
            self.db.add(line_item)
        
        await self.db.commit()
        
        logger.info(
            f"Requisition created: {requisition.id}, number={requisition_number}, "
            f"amount={total_amount}, approval_level={required_level.value}"
        )
        
        return {
            "requisition_id": str(requisition.id),
            "requisition_number": requisition_number,
            "status": RequisitionStatus.DRAFT.value,
            "total_amount": total_amount,
            "required_approval_level": required_level.value,
            "item_count": len(line_items_data),
            "message": f"Requisition {requisition_number} created. Requires {required_level.value} approval.",
        }
    
    async def submit_requisition(
        self,
        school_id: UUID,
        requisition_id: UUID,
        submitted_by_user_id: UUID,
    ) -> dict:
        """
        Submit requisition for approval.
        
        Changes status from DRAFT to SUBMITTED.
        """
        logger.debug(f"Submitting requisition {requisition_id}")
        
        # Fetch requisition
        requisition = await self._get_requisition(school_id, requisition_id)
        
        # Validate status
        if requisition.status != RequisitionStatus.DRAFT:
            raise ValidationError(
                f"Can only submit DRAFT requisitions. Current status: {requisition.status.value}"
            )
        
        # Update requisition
        requisition.status = RequisitionStatus.SUBMITTED
        requisition.submitted_by = submitted_by_user_id
        requisition.submitted_date = datetime.utcnow()
        
        await self.db.commit()
        
        logger.info(f"Requisition {requisition_id} submitted for approval")
        
        return {
            "requisition_id": str(requisition_id),
            "status": RequisitionStatus.SUBMITTED.value,
            "message": f"Requisition {requisition.requisition_number} submitted. "
                      f"Awaiting {requisition.required_approval_level.value} approval.",
        }
    
    async def approve_requisition(
        self,
        school_id: UUID,
        requisition_id: UUID,
        approved_by_user_id: UUID,
        approved: bool = True,
        approval_reason: str | None = None,
    ) -> dict:
        """
        CRITICAL: Approve or reject purchase requisition.
        
        DOA VALIDATION:
        1. Fetch approving user, validate role matches required approval level
        2. If approved: mark as APPROVED, generate LPO
        3. If rejected: mark as REJECTED
        
        Args:
            school_id: Tenant identifier
            requisition_id: Requisition to approve
            approved_by_user_id: User approving
            approved: True to approve, False to reject
            approval_reason: Reason for rejection
        
        Returns:
            dict with requisition_id, status, approval_level, purchase_order_id (if generated)
        
        Raises:
            NotFoundError: If requisition or user not found
            ValidationError: If user role doesn't match DOA level or invalid status
        """
        logger.debug(f"Processing approval for requisition {requisition_id}")
        
        # STEP 1: Fetch requisition
        requisition = await self._get_requisition(school_id, requisition_id)
        
        # Validate status
        if requisition.status != RequisitionStatus.SUBMITTED:
            raise ValidationError(
                f"Can only approve SUBMITTED requisitions. Current status: {requisition.status.value}"
            )
        
        # STEP 2: Fetch approving user and validate role
        user_query = select(User).where(User.id == approved_by_user_id)
        user = await self.db.scalar(user_query)
        
        if not user:
            logger.warning(f"User {approved_by_user_id} not found")
            raise NotFoundError(f"Approver user not found")
        
        # Get user role
        user_role = user.role.value if hasattr(user.role, "value") else str(user.role)
        
        # STEP 3: Validate DOA authorization
        if approved:
            required_role = requisition.required_approval_level.value
            
            logger.debug(
                f"DOA check: user_role={user_role}, required_role={required_role}"
            )
            
            # Map roles to approval levels
            role_to_level = {
                "BURSAR": ApprovalLevel.BURSAR,
                "PRINCIPAL": ApprovalLevel.PRINCIPAL,
                "DEPUTY_PRINCIPAL": ApprovalLevel.PRINCIPAL,  # DP can approve like PRINCIPAL
                "BOM": ApprovalLevel.BOM,
                "ADMIN": ApprovalLevel.BOM,  # Admin can approve anything
            }
            
            user_approval_level = role_to_level.get(user_role)
            
            if not user_approval_level:
                logger.warning(f"User role {user_role} not authorized for approvals")
                raise ValidationError(
                    f"User role '{user_role}' is not authorized to approve requisitions"
                )
            
            # Check if user can approve this level
            # ADMIN can approve anything, BOM can approve BOM/PRINCIPAL/BURSAR
            # PRINCIPAL can approve PRINCIPAL/BURSAR, BURSAR can only approve BURSAR
            can_approve = False
            
            if user_approval_level == ApprovalLevel.BOM:
                can_approve = True  # BOM/Admin can approve all levels
            elif user_approval_level == ApprovalLevel.PRINCIPAL:
                can_approve = requisition.required_approval_level in [
                    ApprovalLevel.PRINCIPAL,
                    ApprovalLevel.BURSAR,
                ]
            elif user_approval_level == ApprovalLevel.BURSAR:
                can_approve = requisition.required_approval_level == ApprovalLevel.BURSAR
            
            if not can_approve:
                logger.warning(
                    f"User with role {user_role} cannot approve {required_role} requisition"
                )
                raise ValidationError(
                    f"User role '{user_role}' cannot approve {required_role} requisitions. "
                    f"Insufficient authorization level."
                )
        
        # STEP 4: Update requisition status
        if approved:
            requisition.status = RequisitionStatus.APPROVED
            requisition.approval_level = requisition.required_approval_level
            message = f"Requisition approved by {user.first_name} {user.last_name}"
        else:
            requisition.status = RequisitionStatus.REJECTED
            message = f"Requisition rejected: {approval_reason or 'No reason provided'}"
        
        requisition.approved_by = approved_by_user_id
        requisition.approved_date = datetime.utcnow()
        
        await self.db.commit()
        
        logger.info(
            f"Requisition {requisition_id} processed: status={requisition.status.value}, "
            f"approval_level={requisition.approval_level.value if requisition.approval_level else 'None'}"
        )
        
        # STEP 5: If approved, generate LPO
        purchase_order_id = None
        if approved:
            logger.debug(f"Generating LPO for approved requisition {requisition_id}")
            # Import here to avoid circular dependency
            from src.modules.procurement.services.purchase_order_service import PurchaseOrderService
            
            po_service = PurchaseOrderService(self.db)
            lpo_result = await po_service.generate_lpo_from_requisition(
                school_id=school_id,
                requisition_id=requisition_id,
            )
            purchase_order_id = lpo_result["purchase_order_id"]
        
        return {
            "requisition_id": str(requisition_id),
            "requisition_number": requisition.requisition_number,
            "status": requisition.status.value,
            "approval_level": requisition.approval_level.value if requisition.approval_level else None,
            "approved_date": requisition.approved_date.isoformat(),
            "purchase_order_id": purchase_order_id,
            "message": message,
        }
    
    async def get_requisition(
        self,
        school_id: UUID,
        requisition_id: UUID,
    ) -> dict:
        """Get requisition detail with line items."""
        requisition = await self._get_requisition(school_id, requisition_id)
        
        line_items = [
            {
                "id": str(item.id),
                "description": item.description,
                "quantity": item.quantity,
                "unit_price": item.unit_price,
                "total_price": item.total_price,
            }
            for item in requisition.line_items
        ]
        
        return {
            "id": str(requisition.id),
            "requisition_number": requisition.requisition_number,
            "description": requisition.description,
            "total_amount": requisition.total_amount,
            "status": requisition.status.value,
            "required_approval_level": requisition.required_approval_level.value,
            "submitted_date": requisition.submitted_date.isoformat() if requisition.submitted_date else None,
            "approved_date": requisition.approved_date.isoformat() if requisition.approved_date else None,
            "approval_level": requisition.approval_level.value if requisition.approval_level else None,
            "line_items": line_items,
            "created_at": requisition.created_at.isoformat(),
        }
    
    async def list_requisitions(
        self,
        school_id: UUID,
        status: str | None = None,
    ) -> list[dict]:
        """List requisitions with optional status filter."""
        query = select(PurchaseRequisition).where(
            PurchaseRequisition.school_id == school_id
        )
        
        if status:
            query = query.where(PurchaseRequisition.status == RequisitionStatus(status))
        
        query = query.order_by(PurchaseRequisition.created_at.desc())
        
        result = await self.db.execute(query)
        requisitions = result.scalars().all()
        
        return [
            {
                "id": str(r.id),
                "requisition_number": r.requisition_number,
                "total_amount": r.total_amount,
                "status": r.status.value,
                "required_approval_level": r.required_approval_level.value,
                "created_at": r.created_at.isoformat(),
            }
            for r in requisitions
        ]
    
    async def _get_requisition(
        self,
        school_id: UUID,
        requisition_id: UUID,
    ) -> PurchaseRequisition:
        """Get requisition with validation."""
        query = select(PurchaseRequisition).where(
            and_(
                PurchaseRequisition.id == requisition_id,
                PurchaseRequisition.school_id == school_id,
            )
        )
        requisition = await self.db.scalar(query)
        
        if not requisition:
            raise NotFoundError(f"Requisition {requisition_id} not found")
        
        return requisition
    
    def _determine_approval_level(self, amount: Decimal) -> ApprovalLevel:
        """
        Determine required approval level based on amount.
        
        DOA Logic:
        - <= 10,000 KES: BURSAR
        - <= 50,000 KES: PRINCIPAL
        - > 50,000 KES: BOM
        """
        if amount <= Decimal("10000"):
            return ApprovalLevel.BURSAR
        elif amount <= Decimal("50000"):
            return ApprovalLevel.PRINCIPAL
        else:
            return ApprovalLevel.BOM
    
    async def _generate_requisition_number(self, school_id: UUID) -> str:
        """Generate unique requisition number."""
        # Query max existing requisition number
        query = select(PurchaseRequisition).where(
            PurchaseRequisition.school_id == school_id
        ).order_by(PurchaseRequisition.created_at.desc())
        
        result = await self.db.execute(query)
        last_req = result.scalars().first()
        
        if last_req and last_req.requisition_number:
            # Extract sequence from last number (format: PR-YYYY-NNNN)
            try:
                parts = last_req.requisition_number.split("-")
                sequence = int(parts[-1]) + 1
            except (IndexError, ValueError):
                sequence = 1
        else:
            sequence = 1
        
        year = datetime.utcnow().year
        requisition_number = f"PR-{year}-{sequence:04d}"
        
        logger.debug(f"Generated requisition number: {requisition_number}")
        
        return requisition_number
