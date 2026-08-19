"""
M-Pesa Transaction Models

Stores M-Pesa payment transactions and their status.
Used for tracking payments, idempotency, and reconciliation.
"""
from datetime import datetime
from decimal import Decimal
from uuid import UUID

from sqlalchemy import String, Numeric, DateTime, Boolean, Index
from sqlalchemy.orm import Mapped, mapped_column

from src.shared.base_model import AuditableBase, TenantMixin


class MpesaTransaction(AuditableBase, TenantMixin):
    """
    M-Pesa transaction record.

    Stores payment attempts, confirmations, and reconciliation.
    Used for idempotency: CheckoutRequestID must be unique per student per payment.
    """

    __tablename__ = "mpesa_transactions"

    # Identifiers
    checkout_request_id: Mapped[str] = mapped_column(
        String(100),
        nullable=False,
        index=True,
    )  # Unique per transaction
    merchant_request_id: Mapped[str] = mapped_column(
        String(100),
        nullable=True,
    )  # Safaricom's request ID
    receipt_number: Mapped[str] = mapped_column(
        String(50),
        nullable=True,
    )  # M-Pesa receipt (e.g., LHR12345ABC)

    # Transaction details
    student_id: Mapped[UUID] = mapped_column(
        nullable=False,
        index=True,
    )  # Who paid
    phone_number: Mapped[str] = mapped_column(
        String(20),
        nullable=False,
    )  # Customer phone
    amount: Mapped[Decimal] = mapped_column(
        Numeric(15, 4),
        nullable=False,
    )  # Amount in KES

    # Status tracking
    status: Mapped[str] = mapped_column(
        String(50),
        default="PENDING",
        index=True,
    )  # PENDING, SUCCESS, FAILED, TIMEOUT
    result_code: Mapped[int] = mapped_column(
        nullable=True,
    )  # Safaricom result code (0 = success)
    result_description: Mapped[str] = mapped_column(
        String(500),
        nullable=True,
    )  # Safaricom result message
    response_code: Mapped[str] = mapped_column(
        String(50),
        nullable=True,
    )  # Initial response code

    # Timestamps
    initiated_at: Mapped[datetime] = mapped_column(
        DateTime,
        nullable=False,
    )  # When STK was pushed
    callback_received_at: Mapped[datetime] = mapped_column(
        DateTime,
        nullable=True,
    )  # When callback received
    receipt_created: Mapped[bool] = mapped_column(
        Boolean,
        default=False,
    )  # Whether fee receipt was created

    # Reconciliation
    fee_receipt_id: Mapped[UUID] = mapped_column(
        nullable=True,
    )  # Link to FeeReceipt (if created)
    journal_entry_id: Mapped[UUID] = mapped_column(
        nullable=True,
    )  # Link to GL journal (if posted)

    # Indices for queries
    __table_args__ = (
        Index("idx_mpesa_student_phone", "student_id", "phone_number"),
        Index("idx_mpesa_status", "status", "callback_received_at"),
        Index("idx_mpesa_checkout_id", "checkout_request_id", unique=True),
    )

    class Config:
        """SQLAlchemy config."""
        use_enum_values = True
