"""
Supplier Service.

Manages supplier master data with approval workflow.
"""

import logging
from uuid import UUID

from sqlalchemy import and_, select
from sqlalchemy.ext.asyncio import AsyncSession

from src.core.exceptions import NotFoundError, ValidationError
from src.modules.procurement.models.procurement import Supplier

logger = logging.getLogger(__name__)


class SupplierService:
    """Service for managing suppliers."""
    
    def __init__(self, db: AsyncSession):
        """Initialize with database session."""
        self.db = db
    
    async def create_supplier(
        self,
        school_id: UUID,
        name: str,
        kra_pin: str,
        bank_account_number: str,
        bank_name: str,
        account_name: str,
        email: str | None = None,
        phone: str | None = None,
        bank_branch: str | None = None,
    ) -> dict:
        """
        Create supplier.
        
        Args:
            school_id: Tenant identifier
            name: Supplier name
            kra_pin: KRA PIN (unique per school)
            bank_account_number: Bank account
            bank_name: Bank name
            account_name: Account holder name
            email: Supplier email
            phone: Supplier phone
            bank_branch: Bank branch
        
        Returns:
            dict with supplier_id, name, status, message
        
        Raises:
            ValidationError: If KRA PIN already exists
        """
        logger.debug(f"Creating supplier: {name}")
        
        # Check if KRA PIN already exists for this school
        existing = await self.db.scalar(
            select(Supplier).where(
                and_(
                    Supplier.school_id == school_id,
                    Supplier.kra_pin == kra_pin,
                )
            )
        )
        
        if existing:
            raise ValidationError(f"Supplier with KRA PIN {kra_pin} already exists")
        
        # Check if supplier name already exists for this school
        existing_name = await self.db.scalar(
            select(Supplier).where(
                and_(
                    Supplier.school_id == school_id,
                    Supplier.name == name,
                )
            )
        )
        
        if existing_name:
            raise ValidationError(f"Supplier {name} already exists")
        
        # Create supplier
        supplier = Supplier(
            school_id=school_id,
            name=name,
            kra_pin=kra_pin,
            bank_account_number=bank_account_number,
            bank_name=bank_name,
            account_name=account_name,
            email=email,
            phone=phone,
            bank_branch=bank_branch,
            is_approved=False,  # Must be approved before use
            is_active=True,
        )
        
        self.db.add(supplier)
        await self.db.commit()
        
        logger.info(f"Supplier created: {supplier.id}, name={name}")
        
        return {
            "supplier_id": str(supplier.id),
            "name": name,
            "kra_pin": kra_pin,
            "is_approved": False,
            "message": f"Supplier {name} created. Awaiting approval.",
        }
    
    async def approve_supplier(
        self,
        school_id: UUID,
        supplier_id: UUID,
        approved: bool = True,
    ) -> dict:
        """
        Approve or revoke supplier approval.
        
        Args:
            school_id: Tenant identifier
            supplier_id: Supplier to approve
            approved: True to approve, False to revoke
        
        Returns:
            dict with supplier_id, name, is_approved, message
        
        Raises:
            NotFoundError: If supplier not found
        """
        logger.debug(f"Updating approval for supplier {supplier_id}: approved={approved}")
        
        # Fetch supplier
        supplier = await self._get_supplier(school_id, supplier_id)
        
        # Update approval status
        supplier.is_approved = approved
        
        await self.db.commit()
        
        logger.info(f"Supplier {supplier_id} approval updated: {approved}")
        
        status_text = "approved" if approved else "approval revoked"
        
        return {
            "supplier_id": str(supplier_id),
            "name": supplier.name,
            "is_approved": approved,
            "message": f"Supplier {supplier.name} {status_text}.",
        }
    
    async def get_supplier(
        self,
        school_id: UUID,
        supplier_id: UUID,
    ) -> dict:
        """Get supplier detail."""
        supplier = await self._get_supplier(school_id, supplier_id)
        
        return {
            "id": str(supplier.id),
            "name": supplier.name,
            "email": supplier.email,
            "phone": supplier.phone,
            "kra_pin": supplier.kra_pin,
            "bank_account_number": supplier.bank_account_number,
            "bank_name": supplier.bank_name,
            "bank_branch": supplier.bank_branch,
            "account_name": supplier.account_name,
            "is_approved": supplier.is_approved,
            "is_active": supplier.is_active,
            "created_at": supplier.created_at.isoformat(),
        }
    
    async def list_suppliers(
        self,
        school_id: UUID,
        approved_only: bool = False,
    ) -> list[dict]:
        """
        List suppliers.
        
        Args:
            school_id: Tenant identifier
            approved_only: Only return approved suppliers
        
        Returns:
            List of supplier dicts
        """
        query = select(Supplier).where(Supplier.school_id == school_id)
        
        if approved_only:
            query = query.where(Supplier.is_approved == True)
        
        query = query.order_by(Supplier.name)
        
        result = await self.db.execute(query)
        suppliers = result.scalars().all()
        
        return [
            {
                "id": str(s.id),
                "name": s.name,
                "kra_pin": s.kra_pin,
                "is_approved": s.is_approved,
                "is_active": s.is_active,
                "created_at": s.created_at.isoformat(),
            }
            for s in suppliers
        ]
    
    async def _get_supplier(
        self,
        school_id: UUID,
        supplier_id: UUID,
    ) -> Supplier:
        """Get supplier with validation."""
        query = select(Supplier).where(
            and_(
                Supplier.id == supplier_id,
                Supplier.school_id == school_id,
            )
        )
        supplier = await self.db.scalar(query)
        
        if not supplier:
            raise NotFoundError(f"Supplier {supplier_id} not found")
        
        return supplier
