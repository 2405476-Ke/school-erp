"""
SQLAlchemy ORM models for Procurement and Accounts Payable.

Models:
- Supplier: Vendor management with KRA PIN and bank details
- PurchaseRequisition/Item: Internal purchase requests
- PurchaseOrder (LPO): Local Purchase Orders from approved requisitions
- SupplierInvoice: Vendor invoices for matching
- GoodsReceivedNote (GRN): Goods receipt tracking
- APPayment: Payment records for matched invoices
"""

from datetime import datetime, date
from uuid import UUID
from enum import Enum
from decimal import Decimal

from sqlalchemy import (
    CheckConstraint,
    ForeignKey,
    Index,
    UniqueConstraint,
    String,
    Text,
    DECIMAL,
    Integer,
    Boolean,
    Date,
    DateTime,
    Enum as SQLEnum,
)
from sqlalchemy.orm import Mapped, mapped_column, relationship

from src.core.models import AuditableBase, TenantMixin


# ============================================================================
# ENUMS
# ============================================================================


class RequisitionStatus(str, Enum):
    """Purchase requisition status."""
    DRAFT = "DRAFT"
    SUBMITTED = "SUBMITTED"
    APPROVED = "APPROVED"
    REJECTED = "REJECTED"
    CLOSED = "CLOSED"


class ApprovalLevel(str, Enum):
    """Delegation of Authority levels."""
    BURSAR = "BURSAR"  # Up to 10,000 KES
    PRINCIPAL = "PRINCIPAL"  # Up to 50,000 KES
    BOM = "BOM"  # Above 50,000 KES (Board of Management)


class LPOStatus(str, Enum):
    """Local Purchase Order status."""
    OPEN = "OPEN"
    PARTIAL_RECEIVED = "PARTIAL_RECEIVED"
    FULLY_RECEIVED = "FULLY_RECEIVED"
    CLOSED = "CLOSED"
    CANCELLED = "CANCELLED"


class InvoiceStatus(str, Enum):
    """Supplier invoice status."""
    DRAFT = "DRAFT"
    SUBMITTED = "SUBMITTED"
    MATCHED = "MATCHED"
    UNMATCHED = "UNMATCHED"
    PAID = "PAID"
    REJECTED = "REJECTED"


class PaymentStatus(str, Enum):
    """AP payment status."""
    PENDING = "PENDING"
    PROCESSED = "PROCESSED"
    PAID = "PAID"
    CANCELLED = "CANCELLED"


# ============================================================================
# SUPPLIER MODEL
# ============================================================================


class Supplier(AuditableBase, TenantMixin):
    """
    Supplier/Vendor management.
    
    Attributes:
        school_id: Tenant identifier
        name: Supplier name
        email: Supplier email
        phone: Supplier contact
        kra_pin: KRA Personal Identification Number (unique per school)
        bank_account_number: Supplier bank account
        bank_name: Bank name
        bank_branch: Branch name
        account_name: Account holder name
        is_approved: Supplier approved for procurement
        is_active: Active status
    """
    __tablename__ = "suppliers"
    
    name: Mapped[str] = mapped_column(String(255))
    email: Mapped[str | None] = mapped_column(String(255), nullable=True)
    phone: Mapped[str | None] = mapped_column(String(20), nullable=True)
    kra_pin: Mapped[str] = mapped_column(String(50))
    bank_account_number: Mapped[str] = mapped_column(String(50))
    bank_name: Mapped[str] = mapped_column(String(100))
    bank_branch: Mapped[str | None] = mapped_column(String(100), nullable=True)
    account_name: Mapped[str] = mapped_column(String(100))
    is_approved: Mapped[bool] = mapped_column(default=False, comment="Approved for procurement")
    is_active: Mapped[bool] = mapped_column(default=True)
    
    # Relationships
    purchase_orders: Mapped[list["PurchaseOrder"]] = relationship(
        back_populates="supplier",
        cascade="all, delete-orphan",
        lazy="select",
    )
    invoices: Mapped[list["SupplierInvoice"]] = relationship(
        back_populates="supplier",
        cascade="all, delete-orphan",
        lazy="select",
    )
    
    __table_args__ = (
        UniqueConstraint("school_id", "kra_pin", name="uq_supplier_kra_pin"),
        UniqueConstraint("school_id", "name", name="uq_supplier_name"),
        Index("idx_supplier_school_approved", "school_id", "is_approved"),
    )


# ============================================================================
# PURCHASE REQUISITION MODELS
# ============================================================================


class PurchaseRequisition(AuditableBase, TenantMixin):
    """
    Internal purchase requisition request.
    
    WORKFLOW:
    1. Created in DRAFT status
    2. Submitted for approval
    3. Routed by DOA: BURSAR (10k), PRINCIPAL (50k), BOM (50k+)
    4. Upon final approval → auto-generate LPO
    5. Closed when LPO fully received
    
    Attributes:
        school_id: Tenant identifier
        requisition_number: Unique requisition ID (auto-generated)
        description: Purpose/description
        total_amount: Sum of all line items
        status: DRAFT/SUBMITTED/APPROVED/REJECTED/CLOSED
        required_approval_level: Calculated DOA level
        submitted_by: User who submitted
        submitted_date: Submission timestamp
        approved_by: User who approved (null if not approved)
        approved_date: Approval timestamp
        approval_level: BURSAR/PRINCIPAL/BOM (null if not approved)
    """
    __tablename__ = "purchase_requisitions"
    
    requisition_number: Mapped[str] = mapped_column(String(50))
    description: Mapped[str] = mapped_column(Text)
    total_amount: Mapped[Decimal] = mapped_column(DECIMAL(15, 2))
    status: Mapped[RequisitionStatus] = mapped_column(SQLEnum(RequisitionStatus), default=RequisitionStatus.DRAFT)
    required_approval_level: Mapped[ApprovalLevel] = mapped_column(SQLEnum(ApprovalLevel))
    submitted_by: Mapped[UUID | None] = mapped_column(
        ForeignKey("users.id", ondelete="SET NULL"),
        nullable=True,
    )
    submitted_date: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)
    approved_by: Mapped[UUID | None] = mapped_column(
        ForeignKey("users.id", ondelete="SET NULL"),
        nullable=True,
    )
    approved_date: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)
    approval_level: Mapped[ApprovalLevel | None] = mapped_column(SQLEnum(ApprovalLevel), nullable=True)
    
    # Relationships
    line_items: Mapped[list["PurchaseRequisitionItem"]] = relationship(
        back_populates="requisition",
        cascade="all, delete-orphan",
        lazy="select",
    )
    purchase_order: Mapped["PurchaseOrder | None"] = relationship(
        back_populates="requisition",
        uselist=False,
        lazy="select",
    )
    
    __table_args__ = (
        UniqueConstraint("school_id", "requisition_number", name="uq_requisition_number"),
        CheckConstraint("total_amount > 0", name="ck_requisition_amount_positive"),
        Index("idx_requisition_status", "status"),
        Index("idx_requisition_approval_level", "required_approval_level"),
    )


class PurchaseRequisitionItem(AuditableBase, TenantMixin):
    """
    Line item in purchase requisition.
    
    Attributes:
        school_id: Tenant identifier
        requisition_id: FK to PurchaseRequisition
        description: Item description
        quantity: Quantity required
        unit_price: Price per unit
        total_price: quantity * unit_price
    """
    __tablename__ = "purchase_requisition_items"
    
    requisition_id: Mapped[UUID] = mapped_column(
        ForeignKey("purchase_requisitions.id", ondelete="CASCADE")
    )
    description: Mapped[str] = mapped_column(String(255))
    quantity: Mapped[Decimal] = mapped_column(DECIMAL(10, 2))
    unit_price: Mapped[Decimal] = mapped_column(DECIMAL(15, 2))
    total_price: Mapped[Decimal] = mapped_column(DECIMAL(15, 2))
    
    # Relationships
    requisition: Mapped["PurchaseRequisition"] = relationship(back_populates="line_items")
    
    __table_args__ = (
        CheckConstraint("quantity > 0", name="ck_pr_item_quantity_positive"),
        CheckConstraint("unit_price > 0", name="ck_pr_item_price_positive"),
        CheckConstraint("total_price > 0", name="ck_pr_item_total_positive"),
        Index("idx_pr_item_requisition", "requisition_id"),
    )


# ============================================================================
# PURCHASE ORDER (LPO) MODELS
# ============================================================================


class PurchaseOrder(AuditableBase, TenantMixin):
    """
    Local Purchase Order (LPO) generated from approved requisition.
    
    WORKFLOW:
    1. Auto-generated when requisition is finally approved
    2. Created in OPEN status
    3. Sent to supplier
    4. Upon goods receipt → PARTIAL_RECEIVED or FULLY_RECEIVED
    5. Upon 3-way match success → marked for payment
    
    Attributes:
        school_id: Tenant identifier
        lpo_number: Unique LPO ID
        requisition_id: FK to approved requisition
        supplier_id: FK to Supplier
        order_date: When LPO was created
        expected_delivery_date: Expected delivery
        total_amount: Sum of LPO items (negotiated price)
        status: OPEN/PARTIAL_RECEIVED/FULLY_RECEIVED/CLOSED/CANCELLED
    """
    __tablename__ = "purchase_orders"
    
    lpo_number: Mapped[str] = mapped_column(String(50))
    requisition_id: Mapped[UUID] = mapped_column(
        ForeignKey("purchase_requisitions.id", ondelete="RESTRICT")
    )
    supplier_id: Mapped[UUID] = mapped_column(
        ForeignKey("suppliers.id", ondelete="RESTRICT")
    )
    order_date: Mapped[date] = mapped_column(Date)
    expected_delivery_date: Mapped[date | None] = mapped_column(Date, nullable=True)
    total_amount: Mapped[Decimal] = mapped_column(DECIMAL(15, 2))
    status: Mapped[LPOStatus] = mapped_column(SQLEnum(LPOStatus), default=LPOStatus.OPEN)
    
    # Relationships
    requisition: Mapped["PurchaseRequisition"] = relationship(back_populates="purchase_order")
    supplier: Mapped["Supplier"] = relationship(back_populates="purchase_orders")
    line_items: Mapped[list["PurchaseOrderItem"]] = relationship(
        back_populates="purchase_order",
        cascade="all, delete-orphan",
        lazy="select",
    )
    grn_records: Mapped[list["GoodsReceivedNote"]] = relationship(
        back_populates="purchase_order",
        cascade="all, delete-orphan",
        lazy="select",
    )
    invoices: Mapped[list["SupplierInvoice"]] = relationship(
        back_populates="purchase_order",
        lazy="select",
    )
    
    __table_args__ = (
        UniqueConstraint("school_id", "lpo_number", name="uq_lpo_number"),
        CheckConstraint("total_amount > 0", name="ck_lpo_amount_positive"),
        Index("idx_lpo_status", "status"),
        Index("idx_lpo_supplier", "supplier_id"),
        Index("idx_lpo_requisition", "requisition_id"),
    )


class PurchaseOrderItem(AuditableBase, TenantMixin):
    """
    Line item in purchase order.
    
    Attributes:
        school_id: Tenant identifier
        purchase_order_id: FK to PurchaseOrder
        description: Item description
        quantity: Quantity ordered
        unit_price: Negotiated price per unit
        total_price: quantity * unit_price
        received_quantity: Cumulative quantity received (from GRNs)
    """
    __tablename__ = "purchase_order_items"
    
    purchase_order_id: Mapped[UUID] = mapped_column(
        ForeignKey("purchase_orders.id", ondelete="CASCADE")
    )
    description: Mapped[str] = mapped_column(String(255))
    quantity: Mapped[Decimal] = mapped_column(DECIMAL(10, 2))
    unit_price: Mapped[Decimal] = mapped_column(DECIMAL(15, 2))
    total_price: Mapped[Decimal] = mapped_column(DECIMAL(15, 2))
    received_quantity: Mapped[Decimal] = mapped_column(DECIMAL(10, 2), default=0)
    
    # Relationships
    purchase_order: Mapped["PurchaseOrder"] = relationship(back_populates="line_items")
    
    __table_args__ = (
        CheckConstraint("quantity > 0", name="ck_po_item_quantity_positive"),
        CheckConstraint("unit_price > 0", name="ck_po_item_price_positive"),
        CheckConstraint("received_quantity >= 0", name="ck_po_item_received_nonnegative"),
        CheckConstraint("received_quantity <= quantity", name="ck_po_item_received_lte_qty"),
        Index("idx_po_item_order", "purchase_order_id"),
    )


# ============================================================================
# GOODS RECEIVED NOTE (GRN) MODEL
# ============================================================================


class GoodsReceivedNote(AuditableBase, TenantMixin):
    """
    Goods Received Note tracking physical receipt of goods.
    
    Used in 3-way match:
    - GRN Quantities must match Invoice Quantities (2% tolerance)
    
    Attributes:
        school_id: Tenant identifier
        grn_number: Unique GRN ID
        purchase_order_id: FK to PurchaseOrder
        receipt_date: When goods were received
        received_by_staff_id: Staff who received goods
        notes: Condition/notes on receipt
    """
    __tablename__ = "goods_received_notes"
    
    grn_number: Mapped[str] = mapped_column(String(50))
    purchase_order_id: Mapped[UUID] = mapped_column(
        ForeignKey("purchase_orders.id", ondelete="CASCADE")
    )
    receipt_date: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    received_by_staff_id: Mapped[UUID | None] = mapped_column(
        ForeignKey("staff.id", ondelete="SET NULL"),
        nullable=True,
    )
    notes: Mapped[str | None] = mapped_column(Text, nullable=True)
    
    # Relationships
    purchase_order: Mapped["PurchaseOrder"] = relationship(back_populates="grn_records")
    line_items: Mapped[list["GRNLineItem"]] = relationship(
        back_populates="grn",
        cascade="all, delete-orphan",
        lazy="select",
    )
    
    __table_args__ = (
        UniqueConstraint("school_id", "grn_number", name="uq_grn_number"),
        Index("idx_grn_po", "purchase_order_id"),
    )


class GRNLineItem(AuditableBase, TenantMixin):
    """
    Line item in GRN (quantities received).
    
    Attributes:
        school_id: Tenant identifier
        grn_id: FK to GoodsReceivedNote
        description: Item description
        quantity_received: Quantity actually received
    """
    __tablename__ = "grn_line_items"
    
    grn_id: Mapped[UUID] = mapped_column(
        ForeignKey("goods_received_notes.id", ondelete="CASCADE")
    )
    description: Mapped[str] = mapped_column(String(255))
    quantity_received: Mapped[Decimal] = mapped_column(DECIMAL(10, 2))
    
    # Relationships
    grn: Mapped["GoodsReceivedNote"] = relationship(back_populates="line_items")
    
    __table_args__ = (
        CheckConstraint("quantity_received > 0", name="ck_grn_qty_positive"),
        Index("idx_grn_item_grn", "grn_id"),
    )


# ============================================================================
# SUPPLIER INVOICE MODEL
# ============================================================================


class SupplierInvoice(AuditableBase, TenantMixin):
    """
    Supplier invoice for 3-way matching.
    
    3-WAY MATCH PROCESS:
    1. Invoice Quantities must match GRN Quantities (within 2%)
    2. Invoice Prices must match LPO Prices (within 2%)
    3. If match succeeds → GL posting (DR Expense, CR AP)
    4. If match fails → marked UNMATCHED, manual review required
    
    Attributes:
        school_id: Tenant identifier
        invoice_number: Supplier invoice number (unique per supplier per school)
        purchase_order_id: FK to PurchaseOrder
        supplier_id: FK to Supplier
        invoice_date: Invoice date
        invoice_amount: Total invoice amount
        status: DRAFT/SUBMITTED/MATCHED/UNMATCHED/PAID/REJECTED
        notes: Additional notes
    """
    __tablename__ = "supplier_invoices"
    
    invoice_number: Mapped[str] = mapped_column(String(50))
    purchase_order_id: Mapped[UUID] = mapped_column(
        ForeignKey("purchase_orders.id", ondelete="RESTRICT")
    )
    supplier_id: Mapped[UUID] = mapped_column(
        ForeignKey("suppliers.id", ondelete="RESTRICT")
    )
    invoice_date: Mapped[date] = mapped_column(Date)
    invoice_amount: Mapped[Decimal] = mapped_column(DECIMAL(15, 2))
    status: Mapped[InvoiceStatus] = mapped_column(SQLEnum(InvoiceStatus), default=InvoiceStatus.DRAFT)
    three_way_match_result: Mapped[str | None] = mapped_column(Text, nullable=True, comment="Match result details")
    notes: Mapped[str | None] = mapped_column(Text, nullable=True)
    
    # Relationships
    purchase_order: Mapped["PurchaseOrder"] = relationship(back_populates="invoices")
    supplier: Mapped["Supplier"] = relationship(back_populates="invoices")
    line_items: Mapped[list["InvoiceLineItem"]] = relationship(
        back_populates="invoice",
        cascade="all, delete-orphan",
        lazy="select",
    )
    payment: Mapped["APPayment | None"] = relationship(
        back_populates="invoice",
        uselist=False,
        lazy="select",
    )
    
    __table_args__ = (
        UniqueConstraint("school_id", "supplier_id", "invoice_number", name="uq_invoice_number"),
        CheckConstraint("invoice_amount > 0", name="ck_invoice_amount_positive"),
        Index("idx_invoice_po", "purchase_order_id"),
        Index("idx_invoice_supplier", "supplier_id"),
        Index("idx_invoice_status", "status"),
    )


class InvoiceLineItem(AuditableBase, TenantMixin):
    """
    Line item in supplier invoice.
    
    Used in 3-way match:
    - quantity and unit_price compared against LPO and GRN
    
    Attributes:
        school_id: Tenant identifier
        invoice_id: FK to SupplierInvoice
        description: Item description
        quantity: Invoice quantity
        unit_price: Invoice price per unit
        total_price: quantity * unit_price
    """
    __tablename__ = "invoice_line_items"
    
    invoice_id: Mapped[UUID] = mapped_column(
        ForeignKey("supplier_invoices.id", ondelete="CASCADE")
    )
    description: Mapped[str] = mapped_column(String(255))
    quantity: Mapped[Decimal] = mapped_column(DECIMAL(10, 2))
    unit_price: Mapped[Decimal] = mapped_column(DECIMAL(15, 2))
    total_price: Mapped[Decimal] = mapped_column(DECIMAL(15, 2))
    
    # Relationships
    invoice: Mapped["SupplierInvoice"] = relationship(back_populates="line_items")
    
    __table_args__ = (
        CheckConstraint("quantity > 0", name="ck_invoice_item_qty_positive"),
        CheckConstraint("unit_price > 0", name="ck_invoice_item_price_positive"),
        Index("idx_invoice_item_invoice", "invoice_id"),
    )


# ============================================================================
# ACCOUNTS PAYABLE PAYMENT MODEL
# ============================================================================


class APPayment(AuditableBase, TenantMixin):
    """
    Accounts Payable payment record for matched invoice.
    
    Created after successful 3-way match.
    GL Entry posted: DR Expense (or Inventory), CR Accounts Payable
    
    Attributes:
        school_id: Tenant identifier
        invoice_id: FK to matched SupplierInvoice
        supplier_id: FK to Supplier
        payment_amount: Amount to pay (invoice_amount)
        due_date: Payment due date
        status: PENDING/PROCESSED/PAID/CANCELLED
        payment_date: When payment was made (null if not paid)
        payment_reference: Bank reference/check number
        gl_entry_id: FK to GL Journal Entry (for posting)
    """
    __tablename__ = "ap_payments"
    
    invoice_id: Mapped[UUID] = mapped_column(
        ForeignKey("supplier_invoices.id", ondelete="RESTRICT"),
        unique=True,  # One payment per invoice
    )
    supplier_id: Mapped[UUID] = mapped_column(
        ForeignKey("suppliers.id", ondelete="RESTRICT")
    )
    payment_amount: Mapped[Decimal] = mapped_column(DECIMAL(15, 2))
    due_date: Mapped[date] = mapped_column(Date)
    status: Mapped[PaymentStatus] = mapped_column(SQLEnum(PaymentStatus), default=PaymentStatus.PENDING)
    payment_date: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)
    payment_reference: Mapped[str | None] = mapped_column(String(100), nullable=True)
    gl_entry_id: Mapped[UUID | None] = mapped_column(
        ForeignKey("journal_entries.id", ondelete="SET NULL"),
        nullable=True,
    )
    
    # Relationships
    invoice: Mapped["SupplierInvoice"] = relationship(back_populates="payment")
    
    __table_args__ = (
        CheckConstraint("payment_amount > 0", name="ck_ap_payment_amount_positive"),
        Index("idx_ap_payment_status", "status"),
        Index("idx_ap_payment_supplier", "supplier_id"),
        Index("idx_ap_payment_invoice", "invoice_id"),
    )


# Forward references for cross-module imports
User = None
Staff = None
JournalEntry = None
