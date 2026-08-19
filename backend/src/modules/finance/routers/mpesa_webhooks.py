"""
M-Pesa Webhook Routers: FastAPI endpoints for Safaricom callbacks.

Handles:
- STK Push Callbacks (payment results)
- C2B Validation (pre-payment validation)
- C2B Confirmation (post-payment confirmation)
"""
import logging
from uuid import UUID

from fastapi import APIRouter, Depends, Request
from sqlalchemy.ext.asyncio import AsyncSession

from src.core.database import get_db
from src.core.exceptions import ValidationError, NotFoundError
from src.core.response import APIResponse
from src.modules.finance.schemas.mpesa import (
    InitiatePaymentRequest,
    InitiatePaymentResponse,
    StkPushCallback,
    C2BValidationRequest,
    C2BValidationResponse,
    C2BConfirmationRequest,
    C2BConfirmationResponse,
    MpesaTransactionResponse,
)
from src.modules.finance.services.mpesa_service import MpesaService

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/webhooks/mpesa", tags=["M-Pesa Webhooks"])


# ============================================================================
# WEBHOOK ENDPOINTS (Called by Safaricom)
# ============================================================================


@router.post("/stk-callback", response_model=APIResponse)
async def stk_push_callback(
    request: Request,
    db: AsyncSession = Depends(get_db),
) -> APIResponse:
    """
    STK Push callback endpoint.

    Called by Safaricom when customer responds to STK prompt.
    Webhook Safaricom will POST here with JSON body containing:
    {
      "Body": {
        "stkCallback": {
          "MerchantRequestID": "...",
          "CheckoutRequestID": "...",
          "ResultCode": 0,
          "ResultDesc": "...",
          "CallbackMetadata": {...}
        }
      }
    }

    CRITICAL FLOW:
    1. Parse JSON body
    2. If ResultCode == 0: Auto-create fee receipt (calls ReceiptService)
    3. GL journal posted automatically
    4. Return 200 OK so Safaricom doesn't retry

    Returns:
        APIResponse with status
    """
    try:
        # 1. Parse JSON body
        body = await request.json()
        payload = StkPushCallback(**body)

        logger.info(
            f"STK callback received: "
            f"checkout_id={payload.checkout_request_id}, "
            f"result_code={payload.result_code}"
        )

        # 2. Process callback via MpesaService
        service = MpesaService(db)
        result = await service.process_stk_callback(payload)

        logger.info(f"STK callback processed: {result}")

        # 3. Return success so Safaricom stops retrying
        return APIResponse.success(
            data=result,
            message="STK callback processed",
            status_code=200,
        )

    except ValidationError as e:
        logger.error(f"STK callback validation error: {e}")
        # Still return 200 so Safaricom doesn't retry
        return APIResponse.error(
            error=str(e),
            message="Validation error (will reconcile manually)",
            status_code=200,
        )

    except NotFoundError as e:
        logger.error(f"STK callback not found: {e}")
        return APIResponse.error(
            error=str(e),
            message="Transaction not found (will reconcile manually)",
            status_code=200,
        )

    except Exception as e:
        logger.error(f"STK callback exception: {e}", exc_info=True)
        # Still return 200 to stop Safaricom retrying
        return APIResponse.error(
            error=str(e),
            message="Unexpected error (will reconcile manually)",
            status_code=200,
        )


@router.post("/c2b-validation", response_model=APIResponse)
async def c2b_validation(
    payload: C2BValidationRequest,
    db: AsyncSession = Depends(get_db),
) -> APIResponse:
    """
    C2B validation callback endpoint.

    Called by Safaricom BEFORE payment is taken from customer.
    Must respond with:
    {
      "ResultCode": 0,
      "ResultDesc": "Success"
    }

    to accept payment, or non-zero ResultCode to reject.

    Args:
        payload: C2BValidationRequest from Safaricom
        db: Database session

    Returns:
        Validation response
    """
    try:
        logger.info(
            f"C2B validation: bill_ref={payload.BillRefNumber}, "
            f"amount={payload.TransAmount}, "
            f"phone={payload.CallerMSISDN}"
        )

        service = MpesaService(db)
        result = await service.process_c2b_validation(payload)

        # Return response as-is (no APIResponse wrapper for webhooks)
        return APIResponse.success(
            data=result,
            message="C2B validation processed",
            status_code=200,
        )

    except Exception as e:
        logger.error(f"C2B validation error: {e}")
        # Accept payment anyway (operator will reconcile)
        return APIResponse.success(
            data={"ResultCode": 0, "ResultDesc": "Success"},
            message="Default accept (error in validation)",
            status_code=200,
        )


@router.post("/c2b-confirmation", response_model=APIResponse)
async def c2b_confirmation(
    payload: C2BConfirmationRequest,
    db: AsyncSession = Depends(get_db),
) -> APIResponse:
    """
    C2B confirmation callback endpoint.

    Called by Safaricom AFTER payment is deducted from customer.
    Payment is now final. Must create receipt and post GL.

    CRITICAL FLOW:
    1. Parse callback payload
    2. Call ReceiptService.allocate_payment() to create receipt and post GL
    3. Return 200 OK

    Args:
        payload: C2BConfirmationRequest from Safaricom
        db: Database session

    Returns:
        Confirmation response
    """
    try:
        logger.info(
            f"C2B confirmation: trans_id={payload.TransID}, "
            f"amount={payload.TransAmount}, "
            f"bill_ref={payload.BillRefNumber}"
        )

        service = MpesaService(db)
        result = await service.process_c2b_confirmation(payload)

        return APIResponse.success(
            data=result,
            message="C2B confirmation processed",
            status_code=200,
        )

    except Exception as e:
        logger.error(f"C2B confirmation error: {e}")
        # Accept anyway (operator will reconcile)
        return APIResponse.success(
            data={"ResultCode": 0, "ResultDesc": "Success"},
            message="Default accept (error in confirmation)",
            status_code=200,
        )


# ============================================================================
# REGULAR ENDPOINTS (Called by frontend/app)
# ============================================================================


@router.post("/initiate-payment", response_model=APIResponse)
async def initiate_payment(
    request_data: InitiatePaymentRequest,
    db: AsyncSession = Depends(get_db),
) -> APIResponse:
    """
    Initiate M-Pesa payment.

    Frontend/mobile app calls this to start payment flow.
    Shows STK prompt on customer's phone.

    FLOW:
    1. Validate student exists
    2. Generate CheckoutRequestID for idempotency
    3. Call DarajaClient.initiate_stk_push() (REAL HTTPX)
    4. Store MpesaTransaction (PENDING)
    5. Return CheckoutRequestID to client

    Request:
    {
      "student_id": "uuid",
      "phone_number": "254712345678",
      "amount": 1000.00,
      "invoice_id": "uuid",  // optional
      "description": "Fee Payment"  // optional
    }

    Response:
    {
      "success": true,
      "data": {
        "checkout_request_id": "...",
        "merchant_request_id": "...",
        "response_code": "0",
        "status": "PENDING",
        "phone_number": "254712345678",
        "amount": 1000.00
      }
    }

    Args:
        request_data: Payment initiation request
        db: Database session

    Returns:
        APIResponse with CheckoutRequestID
    """
    try:
        logger.info(
            f"Initiating payment: student={request_data.student_id}, "
            f"amount={request_data.amount}"
        )

        service = MpesaService(db)
        response = await service.trigger_fee_payment(request_data)

        return APIResponse.success(
            data=response,
            message="Payment initiated - check phone for STK prompt",
            status_code=201,
        )

    except NotFoundError as e:
        logger.error(f"Student not found: {e}")
        return APIResponse.error(
            error=str(e),
            message="Student not found",
            status_code=404,
        )

    except ValidationError as e:
        logger.error(f"Validation error: {e}")
        return APIResponse.error(
            error=str(e),
            message="Invalid request",
            status_code=400,
        )

    except Exception as e:
        logger.error(f"Payment initiation failed: {e}")
        return APIResponse.error(
            error=str(e),
            message="Failed to initiate payment",
            status_code=500,
        )


@router.get("/transaction-status/{checkout_request_id}", response_model=APIResponse)
async def get_transaction_status(
    checkout_request_id: str,
    db: AsyncSession = Depends(get_db),
) -> APIResponse:
    """
    Get status of M-Pesa transaction.

    Called by frontend to poll status after STK initiated.

    Response:
    {
      "success": true,
      "data": {
        "id": "uuid",
        "checkout_request_id": "...",
        "status": "SUCCESS|PENDING|FAILED",
        "amount": 1000.00,
        "receipt_number": "LHR12345ABC",
        "receipt_created": true,
        "fee_receipt_id": "uuid"
      }
    }

    Args:
        checkout_request_id: Checkout request ID from initiate_payment
        db: Database session

    Returns:
        Transaction status
    """
    try:
        logger.info(f"Querying transaction: {checkout_request_id}")

        service = MpesaService(db)
        txn = await service.get_transaction_status(checkout_request_id)

        if not txn:
            return APIResponse.error(
                error=f"Transaction {checkout_request_id} not found",
                message="Not found",
                status_code=404,
            )

        response = MpesaTransactionResponse(
            id=txn.id,
            checkout_request_id=txn.checkout_request_id,
            merchant_request_id=txn.merchant_request_id,
            receipt_number=txn.receipt_number,
            student_id=txn.student_id,
            phone_number=txn.phone_number,
            amount=txn.amount,
            status=txn.status,
            result_code=txn.result_code,
            result_description=txn.result_description,
            initiated_at=txn.initiated_at.isoformat(),
            callback_received_at=(
                txn.callback_received_at.isoformat()
                if txn.callback_received_at
                else None
            ),
            receipt_created=txn.receipt_created,
            fee_receipt_id=txn.fee_receipt_id,
        )

        return APIResponse.success(
            data=response,
            message="Transaction found",
            status_code=200,
        )

    except Exception as e:
        logger.error(f"Status query failed: {e}")
        return APIResponse.error(
            error=str(e),
            message="Failed to retrieve status",
            status_code=500,
        )


@router.get("/student-transactions/{student_id}", response_model=APIResponse)
async def get_student_transactions(
    student_id: UUID,
    status: str = None,
    limit: int = 50,
    db: AsyncSession = Depends(get_db),
) -> APIResponse:
    """
    Get payment history for student.

    Response:
    {
      "success": true,
      "data": [
        {
          "id": "uuid",
          "checkout_request_id": "...",
          "status": "SUCCESS",
          "amount": 1000.00,
          "initiated_at": "2025-01-16T14:30:00Z",
          "receipt_created": true
        }
      ]
    }

    Args:
        student_id: Student ID
        status: Optional status filter (SUCCESS, FAILED, PENDING)
        limit: Max results (default 50)
        db: Database session

    Returns:
        List of transactions
    """
    try:
        logger.info(
            f"Querying transactions for student {student_id}, status={status}"
        )

        service = MpesaService(db)
        transactions = await service.get_transactions_by_student(
            student_id=student_id,
            status=status,
            limit=limit,
        )

        responses = [
            MpesaTransactionResponse(
                id=txn.id,
                checkout_request_id=txn.checkout_request_id,
                merchant_request_id=txn.merchant_request_id,
                receipt_number=txn.receipt_number,
                student_id=txn.student_id,
                phone_number=txn.phone_number,
                amount=txn.amount,
                status=txn.status,
                result_code=txn.result_code,
                result_description=txn.result_description,
                initiated_at=txn.initiated_at.isoformat(),
                callback_received_at=(
                    txn.callback_received_at.isoformat()
                    if txn.callback_received_at
                    else None
                ),
                receipt_created=txn.receipt_created,
                fee_receipt_id=txn.fee_receipt_id,
            )
            for txn in transactions
        ]

        return APIResponse.success(
            data=responses,
            message=f"Found {len(responses)} transactions",
            status_code=200,
        )

    except Exception as e:
        logger.error(f"Transaction query failed: {e}")
        return APIResponse.error(
            error=str(e),
            message="Failed to retrieve transactions",
            status_code=500,
        )
