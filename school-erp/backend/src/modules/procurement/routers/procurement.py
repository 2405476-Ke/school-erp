"""
FastAPI routers for Procurement and Accounts Payable.

Endpoints for:
- Supplier management
- Purchase Requisition (with DOA)
- Purchase Orders (LPO)
- Goods Received Notes (GRN)
- Supplier Invoices
- Accounts Payable Payments (with 3-way match)
"""

import logging
from uuid import UUID
from datetime import date, datetime

from fastapi import APIRouter, Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession

from src.core.database import get_db
from src.core.exceptions import NotFoundError, ValidationError
from src.core.response import APIResponse
from src.modules.procurement.schemas.procurement import (
    SupplierCreate,
    SupplierResponse,
    SupplierApproveRequest,
    CreatePurchaseRequisitionRequest,
    PurchaseRequisitionResponse,
    PurchaseRequisitionDetailResponse,
    ApprovePurchaseRequisitionRequest,
    ApprovePurchaseRequisitionResponse,
    CreatePurchaseOrderRequest,
    PurchaseOrderResponse,
    PurchaseOrderDetailResponse,
    CreateGRNRequest,
    GRNResponse,
    SubmitSupplierInvoiceRequest,
    SupplierInvoiceResponse,
    SupplierInvoiceDetailResponse,
    ProcessInvoiceRequest,
    ProcessInvoiceResponse,
    APPaymentResponse,
    APPaymentDetailResponse,
    ProcessAPPaymentRequest,
    ProcessAPPaymentResponse,
    ThreeWayMatchErrorResponse,
)
from src.modules.procurement.services.supplier_service import SupplierService
from src.modules.procurement.services.requisition_service import RequisitionService
from src.modules.procurement.services.purchase_order_service import PurchaseOrderService
from src.modules.procurement.services.grn_service import GRNService
from src.modules.procurement.services.invoice_service import InvoiceService
from src.modules.procurement.services.ap_service import APService, ThreeWayMatchError

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/procurement", tags=["Procurement & AP"])


# ============================================================================
# SUPPLIER MANAGEMENT
# ============================================================================


@router.post("/suppliers", response_model=APIResponse)
async def create_supplier(
    request: SupplierCreate,
    db: AsyncSession = Depends(get_db),
    school_id: UUID = Depends(lambda: UUID("00000000-0000-0000-0000-000000000000")),
) -> APIResponse:
    """Create new supplier."""
    try:
        service = SupplierService(db)
        result = await service.create_supplier(
            school_id=school_id,
            name=request.name,
            kra_pin=request.kra_pin,
            bank_account_number=request.bank_account_number,
            bank_name=request.bank_name,
            account_name=request.account_name,
            email=request.email,
            phone=request.phone,
            bank_branch=request.bank_branch,
        )
        
        return APIResponse.success(
            data=result,
            message="Supplier created successfully",
            status_code=201,
        )
    
    except ValidationError as e:
        return APIResponse.error(
            error=str(e),
            message="Supplier creation failed",
            status_code=400,
        )
    
    except Exception as e:
        logger.error(f"Error creating supplier: {e}")
        return APIResponse.error(
            error=str(e),
            message="Failed to create supplier",
            status_code=500,
        )


@router.get("/suppliers", response_model=APIResponse)
async def list_suppliers(
    db: AsyncSession = Depends(get_db),
    school_id: UUID = Depends(lambda: UUID("00000000-0000-0000-0000-000000000000")),
    approved_only: bool = Query(False),
) -> APIResponse:
    """List suppliers."""
    try:
        service = SupplierService(db)
        suppliers = await service.list_suppliers(school_id, approved_only=approved_only)
        
        return APIResponse.success(
            data=suppliers,
            message=f"Found {len(suppliers)} suppliers",
            status_code=200,
        )
    
    except Exception as e:
        logger.error(f"Error listing suppliers: {e}")
        return APIResponse.error(
            error=str(e),
            message="Failed to list suppliers",
            status_code=500,
        )


@router.get("/suppliers/{supplier_id}", response_model=APIResponse)
async def get_supplier(
    supplier_id: UUID,
    db: AsyncSession = Depends(get_db),
    school_id: UUID = Depends(lambda: UUID("00000000-0000-0000-0000-000000000000")),
) -> APIResponse:
    """Get supplier detail."""
    try:
        service = SupplierService(db)
        supplier = await service.get_supplier(school_id, supplier_id)
        
        return APIResponse.success(
            data=supplier,
            message="Supplier retrieved",
            status_code=200,
        )
    
    except NotFoundError as e:
        return APIResponse.error(
            error=str(e),
            message="Supplier not found",
            status_code=404,
        )
    
    except Exception as e:
        logger.error(f"Error retrieving supplier: {e}")
        return APIResponse.error(
            error=str(e),
            message="Failed to retrieve supplier",
            status_code=500,
        )


@router.post("/suppliers/{supplier_id}/approve", response_model=APIResponse)
async def approve_supplier(
    supplier_id: UUID,
    request: SupplierApproveRequest,
    db: AsyncSession = Depends(get_db),
    school_id: UUID = Depends(lambda: UUID("00000000-0000-0000-0000-000000000000")),
) -> APIResponse:
    """Approve or revoke supplier."""
    try:
        service = SupplierService(db)
        result = await service.approve_supplier(
            school_id=school_id,
            supplier_id=supplier_id,
            approved=request.is_approved,
        )
        
        return APIResponse.success(
            data=result,
            message="Supplier approval updated",
            status_code=200,
        )
    
    except NotFoundError as e:
        return APIResponse.error(
            error=str(e),
            message="Supplier not found",
            status_code=404,
        )
    
    except Exception as e:
        logger.error(f"Error approving supplier: {e}")
        return APIResponse.error(
            error=str(e),
            message="Failed to approve supplier",
            status_code=500,
        )


# ============================================================================
# PURCHASE REQUISITION (with DOA)
# ============================================================================


@router.post("/requisitions", response_model=APIResponse)
async def create_requisition(
    request: CreatePurchaseRequisitionRequest,
    db: AsyncSession = Depends(get_db),
    school_id: UUID = Depends(lambda: UUID("00000000-0000-0000-0000-000000000000")),
    created_by_user_id: UUID = Depends(lambda: UUID("00000000-0000-0000-0000-000000000000")),
) -> APIResponse:
    """Create purchase requisition in DRAFT status."""
    try:
        service = RequisitionService(db)
        result = await service.create_requisition(
            school_id=school_id,
            description=request.description,
            items=[
                {
                    "description": item.description,
                    "quantity": item.quantity,
                    "unit_price": item.unit_price,
                }
                for item in request.items
            ],
            created_by_user_id=created_by_user_id,
        )
        
        return APIResponse.success(
            data=result,
            message="Requisition created",
            status_code=201,
        )
    
    except ValidationError as e:
        return APIResponse.error(
            error=str(e),
            message="Requisition validation failed",
            status_code=400,
        )
    
    except Exception as e:
        logger.error(f"Error creating requisition: {e}")
        return APIResponse.error(
            error=str(e),
            message="Failed to create requisition",
            status_code=500,
        )


@router.get("/requisitions/{requisition_id}", response_model=APIResponse)
async def get_requisition(
    requisition_id: UUID,
    db: AsyncSession = Depends(get_db),
    school_id: UUID = Depends(lambda: UUID("00000000-0000-0000-0000-000000000000")),
) -> APIResponse:
    """Get requisition detail."""
    try:
        service = RequisitionService(db)
        requisition = await service.get_requisition(school_id, requisition_id)
        
        return APIResponse.success(
            data=requisition,
            message="Requisition retrieved",
            status_code=200,
        )
    
    except NotFoundError as e:
        return APIResponse.error(
            error=str(e),
            message="Requisition not found",
            status_code=404,
        )
    
    except Exception as e:
        logger.error(f"Error retrieving requisition: {e}")
        return APIResponse.error(
            error=str(e),
            message="Failed to retrieve requisition",
            status_code=500,
        )


@router.post("/requisitions/{requisition_id}/approve", response_model=APIResponse)
async def approve_requisition(
    requisition_id: UUID,
    request: ApprovePurchaseRequisitionRequest,
    db: AsyncSession = Depends(get_db),
    school_id: UUID = Depends(lambda: UUID("00000000-0000-0000-0000-000000000000")),
    approver_user_id: UUID = Depends(lambda: UUID("00000000-0000-0000-0000-000000000000")),
) -> APIResponse:
    """
    CRITICAL: Approve/reject requisition with DOA routing.
    
    DOA LOGIC:
    - Amount <= 10,000 KES: BURSAR approval
    - Amount <= 50,000 KES: PRINCIPAL approval
    - Amount > 50,000 KES: BOM approval
    
    Upon final approval: Auto-generate LPO
    """
    try:
        service = RequisitionService(db)
        result = await service.approve_requisition(
            school_id=school_id,
            requisition_id=requisition_id,
            approved_by_user_id=approver_user_id,
            approved=request.approved,
            approval_reason=request.approval_reason,
        )
        
        return APIResponse.success(
            data=result,
            message="Requisition approval processed",
            status_code=200,
        )
    
    except NotFoundError as e:
        return APIResponse.error(
            error=str(e),
            message="Resource not found",
            status_code=404,
        )
    
    except ValidationError as e:
        return APIResponse.error(
            error=str(e),
            message="Approval failed",
            status_code=400,
        )
    
    except Exception as e:
        logger.error(f"Error approving requisition: {e}", exc_info=True)
        return APIResponse.error(
            error=str(e),
            message="Failed to approve requisition",
            status_code=500,
        )


# ============================================================================
# PURCHASE ORDERS (LPO)
# ============================================================================


@router.post("/purchase-orders", response_model=APIResponse)
async def create_purchase_order(
    request: CreatePurchaseOrderRequest,
    db: AsyncSession = Depends(get_db),
    school_id: UUID = Depends(lambda: UUID("00000000-0000-0000-0000-000000000000")),
) -> APIResponse:
    """Create purchase order (manual LPO creation)."""
    try:
        service = PurchaseOrderService(db)
        result = await service.generate_lpo_from_requisition(
            school_id=school_id,
            requisition_id=request.requisition_id,
            supplier_id=request.supplier_id,
            expected_delivery_date=request.expected_delivery_date,
        )
        
        return APIResponse.success(
            data=result,
            message="Purchase Order created",
            status_code=201,
        )
    
    except NotFoundError as e:
        return APIResponse.error(
            error=str(e),
            message="Resource not found",
            status_code=404,
        )
    
    except ValidationError as e:
        return APIResponse.error(
            error=str(e),
            message="Order creation failed",
            status_code=400,
        )
    
    except Exception as e:
        logger.error(f"Error creating purchase order: {e}")
        return APIResponse.error(
            error=str(e),
            message="Failed to create purchase order",
            status_code=500,
        )


@router.get("/purchase-orders/{po_id}", response_model=APIResponse)
async def get_purchase_order(
    po_id: UUID,
    db: AsyncSession = Depends(get_db),
    school_id: UUID = Depends(lambda: UUID("00000000-0000-0000-0000-000000000000")),
) -> APIResponse:
    """Get purchase order detail."""
    try:
        service = PurchaseOrderService(db)
        po = await service.get_purchase_order(school_id, po_id)
        
        return APIResponse.success(
            data=po,
            message="Purchase Order retrieved",
            status_code=200,
        )
    
    except NotFoundError as e:
        return APIResponse.error(
            error=str(e),
            message="Purchase Order not found",
            status_code=404,
        )
    
    except Exception as e:
        logger.error(f"Error retrieving purchase order: {e}")
        return APIResponse.error(
            error=str(e),
            message="Failed to retrieve purchase order",
            status_code=500,
        )


# ============================================================================
# GOODS RECEIVED NOTES (GRN)
# ============================================================================


@router.post("/grn", response_model=APIResponse)
async def create_grn(
    request: CreateGRNRequest,
    db: AsyncSession = Depends(get_db),
    school_id: UUID = Depends(lambda: UUID("00000000-0000-0000-0000-000000000000")),
) -> APIResponse:
    """Create Goods Received Note."""
    try:
        service = GRNService(db)
        result = await service.create_grn(
            school_id=school_id,
            purchase_order_id=request.purchase_order_id,
            items=[
                {
                    "description": item.description,
                    "quantity_received": float(item.quantity_received),
                }
                for item in request.items
            ],
            received_by_staff_id=request.received_by_staff_id,
            notes=request.notes,
        )
        
        return APIResponse.success(
            data=result,
            message="GRN created",
            status_code=201,
        )
    
    except NotFoundError as e:
        return APIResponse.error(
            error=str(e),
            message="LPO not found",
            status_code=404,
        )
    
    except ValidationError as e:
        return APIResponse.error(
            error=str(e),
            message="GRN validation failed",
            status_code=400,
        )
    
    except Exception as e:
        logger.error(f"Error creating GRN: {e}")
        return APIResponse.error(
            error=str(e),
            message="Failed to create GRN",
            status_code=500,
        )


@router.get("/grn/{grn_id}", response_model=APIResponse)
async def get_grn(
    grn_id: UUID,
    db: AsyncSession = Depends(get_db),
    school_id: UUID = Depends(lambda: UUID("00000000-0000-0000-0000-000000000000")),
) -> APIResponse:
    """Get GRN detail."""
    try:
        service = GRNService(db)
        grn = await service.get_grn(school_id, grn_id)
        
        return APIResponse.success(
            data=grn,
            message="GRN retrieved",
            status_code=200,
        )
    
    except NotFoundError as e:
        return APIResponse.error(
            error=str(e),
            message="GRN not found",
            status_code=404,
        )
    
    except Exception as e:
        logger.error(f"Error retrieving GRN: {e}")
        return APIResponse.error(
            error=str(e),
            message="Failed to retrieve GRN",
            status_code=500,
        )


# ============================================================================
# SUPPLIER INVOICES
# ============================================================================


@router.post("/invoices", response_model=APIResponse)
async def submit_invoice(
    request: SubmitSupplierInvoiceRequest,
    db: AsyncSession = Depends(get_db),
    school_id: UUID = Depends(lambda: UUID("00000000-0000-0000-0000-000000000000")),
) -> APIResponse:
    """Submit supplier invoice."""
    try:
        service = InvoiceService(db)
        result = await service.submit_invoice(
            school_id=school_id,
            purchase_order_id=request.purchase_order_id,
            supplier_id=request.supplier_id,
            invoice_number=request.invoice_number,
            invoice_date=request.invoice_date,
            items=[
                {
                    "description": item.description,
                    "quantity": item.quantity,
                    "unit_price": item.unit_price,
                }
                for item in request.items
            ],
            notes=request.notes,
        )
        
        return APIResponse.success(
            data=result,
            message="Invoice submitted",
            status_code=201,
        )
    
    except NotFoundError as e:
        return APIResponse.error(
            error=str(e),
            message="Resource not found",
            status_code=404,
        )
    
    except ValidationError as e:
        return APIResponse.error(
            error=str(e),
            message="Invoice validation failed",
            status_code=400,
        )
    
    except Exception as e:
        logger.error(f"Error submitting invoice: {e}")
        return APIResponse.error(
            error=str(e),
            message="Failed to submit invoice",
            status_code=500,
        )


@router.get("/invoices/{invoice_id}", response_model=APIResponse)
async def get_invoice(
    invoice_id: UUID,
    db: AsyncSession = Depends(get_db),
    school_id: UUID = Depends(lambda: UUID("00000000-0000-0000-0000-000000000000")),
) -> APIResponse:
    """Get invoice detail."""
    try:
        service = InvoiceService(db)
        invoice = await service.get_invoice(school_id, invoice_id)
        
        return APIResponse.success(
            data=invoice,
            message="Invoice retrieved",
            status_code=200,
        )
    
    except NotFoundError as e:
        return APIResponse.error(
            error=str(e),
            message="Invoice not found",
            status_code=404,
        )
    
    except Exception as e:
        logger.error(f"Error retrieving invoice: {e}")
        return APIResponse.error(
            error=str(e),
            message="Failed to retrieve invoice",
            status_code=500,
        )


# ============================================================================
# 3-WAY MATCHING & AP PAYMENTS (CRITICAL)
# ============================================================================


@router.post("/process-invoice", response_model=APIResponse)
async def process_invoice_three_way_match(
    request: ProcessInvoiceRequest,
    db: AsyncSession = Depends(get_db),
    school_id: UUID = Depends(lambda: UUID("00000000-0000-0000-0000-000000000000")),
) -> APIResponse:
    """
    CRITICAL: Process invoice with 3-way matching.
    
    3-WAY MATCH ALGORITHM:
    1. Invoice Quantities must match GRN Quantities (within 2% tolerance)
    2. Invoice Prices must match LPO Prices (within 2% tolerance)
    3. If match succeeds: Create AP Payment, post GL entry
    4. If match fails: Mark invoice UNMATCHED, raise error
    """
    try:
        service = APService(db)
        result = await service.process_supplier_invoice(
            school_id=school_id,
            invoice_id=request.invoice_id,
            grn_id=request.grn_id,
        )
        
        return APIResponse.success(
            data=result,
            message="Invoice processed with 3-way match",
            status_code=200,
        )
    
    except ThreeWayMatchError as e:
        # Match failed - return detailed error
        logger.warning(f"3-way match failed: {e}")
        return APIResponse.error(
            error=str(e),
            message="3-Way Match Failed",
            status_code=400,
        )
    
    except NotFoundError as e:
        return APIResponse.error(
            error=str(e),
            message="Resource not found",
            status_code=404,
        )
    
    except ValidationError as e:
        return APIResponse.error(
            error=str(e),
            message="Invoice processing failed",
            status_code=400,
        )
    
    except Exception as e:
        logger.error(f"Error processing invoice: {e}", exc_info=True)
        return APIResponse.error(
            error=str(e),
            message="Failed to process invoice",
            status_code=500,
        )


@router.post("/ap-payments/{payment_id}/process", response_model=APIResponse)
async def process_ap_payment(
    payment_id: UUID,
    request: ProcessAPPaymentRequest,
    db: AsyncSession = Depends(get_db),
    school_id: UUID = Depends(lambda: UUID("00000000-0000-0000-0000-000000000000")),
) -> APIResponse:
    """Process AP payment (mark as PAID)."""
    try:
        service = APService(db)
        result = await service.process_ap_payment(
            school_id=school_id,
            payment_id=payment_id,
            payment_date=request.payment_date,
            payment_reference=request.payment_reference,
        )
        
        return APIResponse.success(
            data=result,
            message="Payment processed",
            status_code=200,
        )
    
    except NotFoundError as e:
        return APIResponse.error(
            error=str(e),
            message="Payment not found",
            status_code=404,
        )
    
    except ValidationError as e:
        return APIResponse.error(
            error=str(e),
            message="Payment processing failed",
            status_code=400,
        )
    
    except Exception as e:
        logger.error(f"Error processing payment: {e}")
        return APIResponse.error(
            error=str(e),
            message="Failed to process payment",
            status_code=500,
        )


@router.get("/ap-payments/{payment_id}", response_model=APIResponse)
async def get_ap_payment(
    payment_id: UUID,
    db: AsyncSession = Depends(get_db),
    school_id: UUID = Depends(lambda: UUID("00000000-0000-0000-0000-000000000000")),
) -> APIResponse:
    """Get AP payment detail."""
    try:
        service = APService(db)
        payment = await service.get_ap_payment(school_id, payment_id)
        
        return APIResponse.success(
            data=payment,
            message="Payment retrieved",
            status_code=200,
        )
    
    except NotFoundError as e:
        return APIResponse.error(
            error=str(e),
            message="Payment not found",
            status_code=404,
        )
    
    except Exception as e:
        logger.error(f"Error retrieving payment: {e}")
        return APIResponse.error(
            error=str(e),
            message="Failed to retrieve payment",
            status_code=500,
        )


@router.get("/ap-payments", response_model=APIResponse)
async def list_ap_payments(
    db: AsyncSession = Depends(get_db),
    school_id: UUID = Depends(lambda: UUID("00000000-0000-0000-0000-000000000000")),
    status: str = Query(None),
) -> APIResponse:
    """List AP payments."""
    try:
        service = APService(db)
        payments = await service.list_ap_payments(school_id, status=status)
        
        return APIResponse.success(
            data=payments,
            message=f"Found {len(payments)} payments",
            status_code=200,
        )
    
    except Exception as e:
        logger.error(f"Error listing payments: {e}")
        return APIResponse.error(
            error=str(e),
            message="Failed to list payments",
            status_code=500,
        )
