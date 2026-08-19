"""
M-Pesa Schemas: Pydantic v2 models for Safaricom webhook payloads.

Exact representations of Safaricom M-Pesa callbacks:
- STK Push Callback
- C2B Validation
- C2B Confirmation
"""
from decimal import Decimal
from typing import Optional
from uuid import UUID

from pydantic import BaseModel, Field


# ============================================================================
# STK PUSH CALLBACK (Most common for fee payments)
# ============================================================================


class StkPushItem(BaseModel):
    """Individual item in STK callback."""

    Name: str
    Value: Optional[str] = None

    class Config:
        extra = "allow"


class StkPushResult(BaseModel):
    """STK Push callback result."""

    MerchantRequestID: str
    CheckoutRequestID: str
    ResultCode: int  # 0 = Success, non-zero = failure
    ResultDesc: str
    CallbackMetadata: Optional[dict] = None

    class Config:
        extra = "allow"


class StkPushCallback(BaseModel):
    """
    Complete STK Push callback from Safaricom.

    Received when customer completes (or fails) STK prompt.

    Example:
    {
      "Body": {
        "stkCallback": {
          "MerchantRequestID": "...",
          "CheckoutRequestID": "...",
          "ResultCode": 0,
          "ResultDesc": "The service request has been accepted successfully.",
          "CallbackMetadata": {
            "Item": [
              {"Name": "Amount", "Value": 1},
              {"Name": "MpesaReceiptNumber", "Value": "LHR12345ABC"},
              {"Name": "TransactionDate", "Value": 20250116143025},
              {"Name": "PhoneNumber", "Value": "254712345678"}
            ]
          }
        }
      }
    }
    """

    Body: dict = Field(...)

    class Config:
        extra = "allow"

    @property
    def stk_callback(self) -> dict:
        """Get stkCallback from body."""
        return self.Body.get("stkCallback", {})

    @property
    def result_code(self) -> int:
        """Get ResultCode."""
        return self.stk_callback.get("ResultCode")

    @property
    def checkout_request_id(self) -> str:
        """Get CheckoutRequestID."""
        return self.stk_callback.get("CheckoutRequestID")

    @property
    def merchant_request_id(self) -> str:
        """Get MerchantRequestID."""
        return self.stk_callback.get("MerchantRequestID")

    @property
    def is_success(self) -> bool:
        """Check if payment was successful."""
        return self.result_code == 0

    @property
    def callback_metadata(self) -> dict:
        """Get CallbackMetadata items as dict."""
        items = {}
        metadata = self.stk_callback.get("CallbackMetadata", {})
        for item in metadata.get("Item", []):
            name = item.get("Name")
            value = item.get("Value")
            items[name] = value
        return items

    @property
    def receipt_number(self) -> Optional[str]:
        """Extract M-Pesa receipt number from callback."""
        metadata = self.callback_metadata
        return metadata.get("MpesaReceiptNumber")

    @property
    def phone_number(self) -> Optional[str]:
        """Extract customer phone from callback."""
        metadata = self.callback_metadata
        phone = metadata.get("PhoneNumber")
        return str(phone) if phone else None

    @property
    def amount(self) -> Optional[Decimal]:
        """Extract amount from callback."""
        metadata = self.callback_metadata
        amount = metadata.get("Amount")
        return Decimal(str(amount)) if amount else None

    @property
    def transaction_date(self) -> Optional[str]:
        """Extract transaction date from callback."""
        metadata = self.callback_metadata
        return metadata.get("TransactionDate")


# ============================================================================
# C2B VALIDATION (Pre-payment validation)
# ============================================================================


class C2BValidationRequest(BaseModel):
    """
    C2B validation callback.

    Sent by Safaricom to validate incoming C2B payment.
    Must return JSON: {"ResultCode": 0, "ResultDesc": "Success"}

    Example:
    {
      "TransactionType": "Pay Bills Online",
      "TransID": "LHR12345ABC",
      "TransTime": "20250116143025",
      "TransAmount": 1000,
      "BusinessShortCode": 174379,
      "BillRefNumber": "AAAA0001",
      "InvokedPartner": null,
      "OnUs": null,
      "CallerMSISDN": "254712345678",
      "Merchant": null
    }
    """

    TransactionType: str
    TransID: str
    TransTime: str
    TransAmount: Decimal
    BusinessShortCode: int
    BillRefNumber: str
    CallerMSISDN: str
    InvokedPartner: Optional[str] = None
    OnUs: Optional[str] = None
    Merchant: Optional[str] = None

    class Config:
        extra = "allow"


class C2BValidationResponse(BaseModel):
    """Response to C2B validation."""

    ResultCode: int = 0
    ResultDesc: str = "Success"


# ============================================================================
# C2B CONFIRMATION (Post-payment confirmation)
# ============================================================================


class C2BConfirmationRequest(BaseModel):
    """
    C2B confirmation callback.

    Sent by Safaricom after payment is confirmed.
    Payment is now final.

    Example:
    {
      "TransactionType": "Pay Bills Online",
      "TransID": "LHR12345ABC",
      "TransTime": "20250116143025",
      "TransAmount": 1000,
      "BusinessShortCode": 174379,
      "BillRefNumber": "AAAA0001",
      "InvokedPartner": null,
      "OnUs": null,
      "CallerMSISDN": "254712345678",
      "Merchant": null
    }
    """

    TransactionType: str
    TransID: str
    TransTime: str
    TransAmount: Decimal
    BusinessShortCode: int
    BillRefNumber: str
    CallerMSISDN: str
    InvokedPartner: Optional[str] = None
    OnUs: Optional[str] = None
    Merchant: Optional[str] = None

    class Config:
        extra = "allow"


class C2BConfirmationResponse(BaseModel):
    """Response to C2B confirmation."""

    ResultCode: int = 0
    ResultDesc: str = "Success"


# ============================================================================
# REQUEST/RESPONSE SCHEMAS
# ============================================================================


class InitiatePaymentRequest(BaseModel):
    """Request to trigger M-Pesa payment."""

    student_id: UUID
    phone_number: str
    amount: Decimal = Field(..., gt=0, decimal_places=2)
    invoice_id: Optional[UUID] = None
    description: Optional[str] = None


class InitiatePaymentResponse(BaseModel):
    """Response after STK push initiated."""

    checkout_request_id: str
    merchant_request_id: str
    response_code: str
    response_description: str
    status: str = "PENDING"
    phone_number: str
    amount: Decimal


class MpesaTransactionResponse(BaseModel):
    """M-Pesa transaction details."""

    id: UUID
    checkout_request_id: str
    merchant_request_id: Optional[str]
    receipt_number: Optional[str]
    student_id: UUID
    phone_number: str
    amount: Decimal
    status: str
    result_code: Optional[int]
    result_description: Optional[str]
    initiated_at: str
    callback_received_at: Optional[str]
    receipt_created: bool
    fee_receipt_id: Optional[UUID]
