"""
Pydantic v2 schemas for Procurement and Accounts Payable.

Schemas for:
- Supplier CRUD
- Purchase Requisition (with DOA)
- Purchase Order (LPO)
- Goods Received Note (GRN)
- Supplier Invoice
- AP Payment (with 3-way match)
"""

from datetime import datetime, date
from decimal import Decimal
from uuid import UUID

from pydantic import BaseModel, Field, field_validator


# ============================================================================
# SUPPLIER SCHEMAS
# ============================================================================


class SupplierCreate(BaseModel):
    """Create supplier request."""
    name: str = Field(..., min_length=1, max_length=255, description="Supplier name")
    email: str | None = Field(None, max_length=255)
    phone: str | None = Field(None, max_length=20)
    kra_pin: str = Field(..., min_length=1, max_length=50, description="KRA PIN (unique per school)")
    bank_account_number: str = Field(..., min_length=1, max_length=50)
    bank_name: str = Field(..., min_length=1, max_length=100)
    bank_branch: str | None = Field(None, max_length=100)
    account_name: str = Field(..., min_length=1, max_length=100)


class SupplierResponse(BaseModel):
    """Supplier response model."""
    id: UUID
    name: str
    email: str | None
    phone: str | None
    kra_pin: str
    bank_account_number: str
    bank_name: str
    bank_branch: str | None
    account_name: str
    is_approved: bool
    is_active: bool
    created_at: datetime


class SupplierApproveRequest(BaseModel):
    """Approve supplier for procurement."""
    supplier_id: UUID
    is_approved: bool = Field(..., description="True to approve, False to revoke")


# ============================================================================
# PURCHASE REQUISITION SCHEMAS
# ============================================================================


class PurchaseRequisitionItemCreate(BaseModel):
    """Create requisition line item."""
    description: str = Field(..., min_length=1, max_length=255)
    quantity: Decimal = Field(..., decimal_places=2, gt=0)
    unit_price: Decimal = Field(..., decimal_places=2, gt=0)
    
    @property
    def total_price(self) -> Decimal:
        """Calculate total price."""
        return (self.quantity * self.unit_price).quantize(Decimal("0.01"))


class PurchaseRequisitionItemResponse(BaseModel):
    """Requisition line item response."""
    id: UUID
    description: str
    quantity: Decimal
    unit_price: Decimal
    total_price: Decimal


class CreatePurchaseRequisitionRequest(BaseModel):
    """Create purchase requisition request."""
    description: str = Field(..., min_length=20, description="Purpose/description of requisition")
    items: list[PurchaseRequisitionItemCreate] = Field(..., min_items=1)
    
    @field_validator("items")
    @classmethod
    def validate_items_not_empty(cls, v):
        """Ensure at least one item."""
        if not v:
            raise ValueError("Requisition must have at least one item")
        return v
    
    @property
    def total_amount(self) -> Decimal:
        """Calculate total requisition amount."""
        return sum(item.total_price for item in self.items).quantize(Decimal("0.01"))


class PurchaseRequisitionResponse(BaseModel):
    """Purchase requisition response."""
    id: UUID
    requisition_number: str
    description: str
    total_amount: Decimal
    status: str
    required_approval_level: str
    submitted_date: datetime | None
    approved_date: datetime | None
    approval_level: str | None
    created_at: datetime


class PurchaseRequisitionDetailResponse(BaseModel):
    """Requisition detail with line items."""
    id: UUID
    requisition_number: str
    description: str
    total_amount: Decimal
    status: str
    required_approval_level: str
    submitted_by: str | None
    submitted_date: datetime | None
    approved_by: str | None
    approved_date: datetime | None
    approval_level: str | None
    line_items: list[PurchaseRequisitionItemResponse] = []
    created_at: datetime


class ApprovePurchaseRequisitionRequest(BaseModel):
    """Approve purchase requisition."""
    requisition_id: UUID
    approved: bool = Field(..., description="True to approve, False to reject")
    approval_reason: str | None = Field(None, description="Reason for rejection")


class ApprovePurchaseRequisitionResponse(BaseModel):
    """Response from approve requisition."""
    requisition_id: UUID
    requisition_number: str
    status: str
    approval_level: str
    approved_date: datetime
    message: str
    purchase_order_id: UUID | None = Field(None, description="Generated LPO if approved")


# ============================================================================
# PURCHASE ORDER (LPO) SCHEMAS
# ============================================================================


class PurchaseOrderItemCreate(BaseModel):
    """Create LPO line item."""
    description: str = Field(..., min_length=1, max_length=255)
    quantity: Decimal = Field(..., decimal_places=2, gt=0)
    unit_price: Decimal = Field(..., decimal_places=2, gt=0)


class PurchaseOrderItemResponse(BaseModel):
    """LPO line item response."""
    id: UUID
    description: str
    quantity: Decimal
    unit_price: Decimal
    total_price: Decimal
    received_quantity: Decimal


class CreatePurchaseOrderRequest(BaseModel):
    """Create purchase order (LPO)."""
    requisition_id: UUID
    supplier_id: UUID
    expected_delivery_date: date | None = None
    items: list[PurchaseOrderItemCreate] = Field(..., min_items=1)


class PurchaseOrderResponse(BaseModel):
    """Purchase order response."""
    id: UUID
    lpo_number: str
    supplier_name: str
    order_date: date
    expected_delivery_date: date | None
    total_amount: Decimal
    status: str
    created_at: datetime


class PurchaseOrderDetailResponse(BaseModel):
    """LPO detail with line items."""
    id: UUID
    lpo_number: str
    requisition_number: str
    supplier_name: str
    supplier_id: UUID
    order_date: date
    expected_delivery_date: date | None
    total_amount: Decimal
    status: str
    line_items: list[PurchaseOrderItemResponse] = []
    created_at: datetime


# ============================================================================
# GOODS RECEIVED NOTE (GRN) SCHEMAS
# ============================================================================


class GRNLineItemCreate(BaseModel):
    """Create GRN line item."""
    description: str = Field(..., min_length=1, max_length=255)
    quantity_received: Decimal = Field(..., decimal_places=2, gt=0)


class GRNLineItemResponse(BaseModel):
    """GRN line item response."""
    id: UUID
    description: str
    quantity_received: Decimal


class CreateGRNRequest(BaseModel):
    """Create goods received note."""
    purchase_order_id: UUID
    received_by_staff_id: UUID | None = None
    items: list[GRNLineItemCreate] = Field(..., min_items=1)
    notes: str | None = Field(None, max_length=500)


class GRNResponse(BaseModel):
    """GRN response."""
    id: UUID
    grn_number: str
    purchase_order_id: UUID
    lpo_number: str
    receipt_date: datetime
    received_by: str | None
    line_items: list[GRNLineItemResponse] = []
    notes: str | None
    created_at: datetime


# ============================================================================
# SUPPLIER INVOICE SCHEMAS
# ============================================================================


class InvoiceLineItemCreate(BaseModel):
    """Create invoice line item."""
    description: str = Field(..., min_length=1, max_length=255)
    quantity: Decimal = Field(..., decimal_places=2, gt=0)
    unit_price: Decimal = Field(..., decimal_places=2, gt=0)


class InvoiceLineItemResponse(BaseModel):
    """Invoice line item response."""
    id: UUID
    description: str
    quantity: Decimal
    unit_price: Decimal
    total_price: Decimal


class SubmitSupplierInvoiceRequest(BaseModel):
    """Submit supplier invoice for processing."""
    purchase_order_id: UUID
    supplier_id: UUID
    invoice_number: str = Field(..., min_length=1, max_length=50)
    invoice_date: date
    items: list[InvoiceLineItemCreate] = Field(..., min_items=1)
    notes: str | None = Field(None, max_length=500)
    
    @property
    def invoice_amount(self) -> Decimal:
        """Calculate total invoice amount."""
        return sum(
            item.quantity * item.unit_price
            for item in self.items
        ).quantize(Decimal("0.01"))


class SupplierInvoiceResponse(BaseModel):
    """Supplier invoice response."""
    id: UUID
    invoice_number: str
    supplier_name: str
    lpo_number: str
    invoice_date: date
    invoice_amount: Decimal
    status: str
    three_way_match_result: str | None
    created_at: datetime


class SupplierInvoiceDetailResponse(BaseModel):
    """Invoice detail with line items and match result."""
    id: UUID
    invoice_number: str
    supplier_name: str
    supplier_id: UUID
    lpo_number: str
    purchase_order_id: UUID
    invoice_date: date
    invoice_amount: Decimal
    status: str
    line_items: list[InvoiceLineItemResponse] = []
    three_way_match_result: str | None
    notes: str | None
    created_at: datetime


# ============================================================================
# 3-WAY MATCH & AP PAYMENT SCHEMAS
# ============================================================================


class ProcessInvoiceRequest(BaseModel):
    """Process supplier invoice (3-way match)."""
    invoice_id: UUID
    grn_id: UUID


class ProcessInvoiceResponse(BaseModel):
    """Response from invoice processing (3-way match)."""
    invoice_id: UUID
    invoice_number: str
    status: str
    match_result: str
    ap_payment_id: UUID | None = Field(None, description="AP Payment if match successful")
    message: str


class APPaymentResponse(BaseModel):
    """AP payment response."""
    id: UUID
    invoice_number: str
    supplier_name: str
    payment_amount: Decimal
    due_date: date
    status: str
    payment_date: datetime | None
    payment_reference: str | None
    created_at: datetime


class APPaymentDetailResponse(BaseModel):
    """AP payment detail."""
    id: UUID
    invoice_id: UUID
    invoice_number: str
    supplier_name: str
    supplier_id: UUID
    payment_amount: Decimal
    due_date: date
    status: str
    payment_date: datetime | None
    payment_reference: str | None
    gl_entry_id: UUID | None
    created_at: datetime


class ProcessAPPaymentRequest(BaseModel):
    """Process AP payment."""
    payment_id: UUID
    payment_date: datetime = Field(..., description="Date payment was made")
    payment_reference: str = Field(..., min_length=1, max_length=100, description="Check/reference number")


class ProcessAPPaymentResponse(BaseModel):
    """Response from process payment."""
    payment_id: UUID
    invoice_number: str
    status: str
    payment_date: datetime
    payment_reference: str
    message: str


# ============================================================================
# SUMMARY/LIST SCHEMAS
# ============================================================================


class ProcurementSummaryResponse(BaseModel):
    """Procurement summary statistics."""
    pending_requisitions: int
    pending_approvals: int
    open_lpos: int
    pending_invoices: int
    pending_payments: int
    total_po_amount: Decimal
    total_paid_amount: Decimal


class ThreeWayMatchErrorResponse(BaseModel):
    """3-way match error details."""
    status: str = "UNMATCHED"
    invoice_id: UUID
    invoice_number: str
    errors: list[str]
    message: str
