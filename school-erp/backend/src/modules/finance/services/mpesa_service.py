"""
M-Pesa Service: Business logic for payment initiation and callback handling.

Integrates with:
- DarajaClient (STK push)
- ReceiptService (auto-receipt creation)
- Database (idempotency tracking)
"""
import logging
import uuid
from datetime import datetime, timezone
from decimal import Decimal
from typing import Optional
from uuid import UUID

from sqlalchemy import select, and_
from sqlalchemy.ext.asyncio import AsyncSession

from src.core.exceptions import NotFoundError, ValidationError
from src.integrations.daraja.client import DarajaClient
from src.modules.finance.models.fees import Student, FeeReceipt
from src.modules.finance.models.mpesa import MpesaTransaction
from src.modules.finance.schemas.mpesa import (
    InitiatePaymentRequest,
    InitiatePaymentResponse,
    StkPushCallback,
    C2BValidationRequest,
    C2BConfirmationRequest,
)
from src.modules.finance.services.receipt_service import ReceiptService

logger = logging.getLogger(__name__)


class MpesaService:
    """
    M-Pesa payment service.

    Handles:
    1. Initiating STK push payments
    2. Processing callbacks (STK, C2B validation, C2B confirmation)
    3. Auto-receipt creation and GL posting
    4. Idempotency via CheckoutRequestID
    """

    def __init__(self, db: AsyncSession):
        """Initialize service with database session."""
        self.db = db
        self.daraja_client = DarajaClient()
        self.receipt_service = ReceiptService(db)

    async def trigger_fee_payment(
        self,
        request: InitiatePaymentRequest,
    ) -> InitiatePaymentResponse:
        """
        Initiate M-Pesa STK push payment.

        REAL IMPLEMENTATION:
        1. Fetch student by ID
        2. Generate unique CheckoutRequestID for idempotency
        3. Create MpesaTransaction record (status=PENDING)
        4. Call DarajaClient.initiate_stk_push() (REAL HTTPX REQUEST)
        5. Update transaction with response
        6. Return response

        Args:
            request: InitiatePaymentRequest with student_id, phone, amount

        Returns:
            InitiatePaymentResponse with CheckoutRequestID

        Raises:
            NotFoundError: If student not found
            Exception: If STK push fails
        """
        # 1. Verify student exists
        student_query = select(Student).where(Student.id == request.student_id)
        student = await self.db.scalar(student_query)

        if not student:
            raise NotFoundError(f"Student {request.student_id} not found")

        logger.info(
            f"Initiating payment for student {request.student_id}: "
            f"amount={request.amount}, phone={request.phone_number}"
        )

        # 2. Generate unique CheckoutRequestID for idempotency
        checkout_request_id = str(uuid.uuid4())

        # 3. Create MpesaTransaction record
        mpesa_txn = MpesaTransaction(
            school_id=student.school_id,
            checkout_request_id=checkout_request_id,
            student_id=request.student_id,
            phone_number=request.phone_number,
            amount=request.amount,
            status="PENDING",
            initiated_at=datetime.now(timezone.utc),
        )

        self.db.add(mpesa_txn)
        await self.db.flush()  # Get ID before commit
        mpesa_txn_id = mpesa_txn.id

        # 4. Call DarajaClient.initiate_stk_push() with REAL HTTPX
        try:
            account_reference = str(
                request.invoice_id or request.student_id
            )  # Use invoice ID if available
            transaction_desc = (
                request.description or f"Fee Payment - {student.first_name}"
            )

            stk_response = await self.daraja_client.initiate_stk_push(
                phone_number=request.phone_number,
                amount=request.amount,
                account_reference=account_reference,
                transaction_desc=transaction_desc,
                checkout_request_id=checkout_request_id,
            )

            # 5. Update transaction with response
            mpesa_txn.merchant_request_id = stk_response.get("MerchantRequestID")
            mpesa_txn.response_code = stk_response.get("ResponseCode")

            response_code = stk_response.get("ResponseCode")
            if response_code == "0":
                # Success - STK prompt shown
                mpesa_txn.status = "STK_PUSHED"
                logger.info(
                    f"STK push successful: checkout_id={checkout_request_id}"
                )
            else:
                # Initial failure
                mpesa_txn.status = "FAILED"
                mpesa_txn.result_description = stk_response.get(
                    "ResponseDescription"
                )
                logger.warning(
                    f"STK push failed with code {response_code}: "
                    f"{stk_response.get('ResponseDescription')}"
                )

            await self.db.commit()

            # 6. Return response
            return InitiatePaymentResponse(
                checkout_request_id=checkout_request_id,
                merchant_request_id=stk_response.get("MerchantRequestID"),
                response_code=response_code,
                response_description=stk_response.get("ResponseDescription"),
                status=mpesa_txn.status,
                phone_number=request.phone_number,
                amount=request.amount,
            )

        except Exception as e:
            logger.error(f"STK push exception: {e}")
            mpesa_txn.status = "FAILED"
            mpesa_txn.result_description = str(e)
            await self.db.commit()
            raise

    async def process_stk_callback(
        self,
        payload: StkPushCallback,
    ) -> dict:
        """
        Process STK Push callback from Safaricom.

        CRITICAL BUSINESS LOGIC:
        1. Extract CheckoutRequestID from payload
        2. Fetch MpesaTransaction (idempotency check)
        3. If already processed, return early
        4. If ResultCode == 0 (Success):
           a. Extract receipt number, phone, amount from callback
           b. Call ReceiptService.allocate_payment() to auto-create fee receipt
           c. Receipt automatically posts GL journal (from STEP 3)
           d. Update student balance, mark PAID/PARTIAL
        5. Update MpesaTransaction with callback details
        6. Link MpesaTransaction to FeeReceipt (idempotency)
        7. Commit atomically

        Args:
            payload: StkPushCallback from Safaricom

        Returns:
            Dict with status and message

        Raises:
            Exception: If database operations fail
        """
        checkout_request_id = payload.checkout_request_id
        result_code = payload.result_code
        is_success = payload.is_success

        logger.info(
            f"Processing STK callback: "
            f"checkout_id={checkout_request_id}, "
            f"result_code={result_code}, "
            f"success={is_success}"
        )

        # 1. Fetch MpesaTransaction (idempotency)
        query = select(MpesaTransaction).where(
            MpesaTransaction.checkout_request_id == checkout_request_id
        )
        mpesa_txn = await self.db.scalar(query)

        if not mpesa_txn:
            logger.error(f"MpesaTransaction not found: {checkout_request_id}")
            raise NotFoundError(f"Checkout request {checkout_request_id} not found")

        # 2. Check if already processed (idempotency)
        if mpesa_txn.callback_received_at is not None:
            logger.warning(
                f"Callback already processed: {checkout_request_id}, "
                f"status={mpesa_txn.status}"
            )
            return {
                "status": "idempotent",
                "message": f"Callback already processed",
                "receipt_created": mpesa_txn.receipt_created,
            }

        # 3. Update callback timestamp
        mpesa_txn.callback_received_at = datetime.now(timezone.utc)
        mpesa_txn.result_code = result_code
        mpesa_txn.result_description = payload.stk_callback.get("ResultDesc")
        mpesa_txn.merchant_request_id = payload.merchant_request_id

        # 4. CRITICAL: If success, auto-create receipt and post GL
        if is_success:
            try:
                receipt_number = payload.receipt_number
                amount = payload.amount
                phone = payload.phone_number

                logger.info(
                    f"Payment successful: receipt={receipt_number}, "
                    f"amount={amount}, phone={phone}"
                )

                if not all([receipt_number, amount, phone]):
                    raise ValidationError(
                        "Missing receipt number, amount, or phone from callback"
                    )

                # Fetch student to get school_id
                student_query = select(Student).where(Student.id == mpesa_txn.student_id)
                student = await self.db.scalar(student_query)

                if not student:
                    raise NotFoundError(f"Student {mpesa_txn.student_id} not found")

                # 4a. Create receipt (UNPOSTED)
                fee_receipt = await self.receipt_service.create_receipt(
                    school_id=student.school_id,
                    student_id=mpesa_txn.student_id,
                    receipt_date=datetime.now(timezone.utc).date(),
                    amount=amount,
                    payment_method="M-PESA",
                    reference_number=receipt_number,
                    created_by_id=None,  # System-created
                )

                # 4b. Allocate payment and post GL
                # This automatically:
                # - Allocates payment to invoices (FIFO + priority)
                # - Creates GL journal (DR Bank, CR Revenue)
                # - Posts GL journal atomically
                # - Updates StudentFeeAccount balance
                fee_receipt = await self.receipt_service.allocate_payment(
                    school_id=student.school_id,
                    receipt_id=fee_receipt.id,
                    user_id=None,  # System operation
                )

                # 5. Link MpesaTransaction to FeeReceipt (idempotency)
                mpesa_txn.fee_receipt_id = fee_receipt.id
                mpesa_txn.receipt_created = True
                mpesa_txn.status = "SUCCESS"

                logger.info(
                    f"Receipt created: receipt_id={fee_receipt.id}, "
                    f"mpesa_txn={checkout_request_id}"
                )

                # 6. Commit atomically
                await self.db.commit()

                return {
                    "status": "success",
                    "message": "Payment processed successfully",
                    "receipt_id": str(fee_receipt.id),
                    "amount": str(amount),
                }

            except Exception as e:
                logger.error(f"Receipt creation failed: {e}")
                mpesa_txn.status = "CALLBACK_PROCESSED_NO_RECEIPT"
                mpesa_txn.result_description = f"Callback OK but receipt failed: {str(e)}"
                await self.db.commit()

                # Don't raise - callback is still processed
                # Operator can manually create receipt
                return {
                    "status": "partial",
                    "message": f"Callback received but receipt creation failed: {str(e)}",
                    "receipt_created": False,
                }

        else:
            # Payment failed
            mpesa_txn.status = "FAILED"
            logger.info(
                f"Payment failed: result_code={result_code}, "
                f"description={result_code}"
            )

            await self.db.commit()

            return {
                "status": "failed",
                "message": f"Payment failed: {mpesa_txn.result_description}",
                "receipt_created": False,
            }

    async def process_c2b_validation(
        self,
        payload: C2BValidationRequest,
    ) -> dict:
        """
        Process C2B validation callback.

        Validates incoming C2B payment before confirmation.
        Must return {"ResultCode": 0, "ResultDesc": "Success"} to accept.

        Args:
            payload: C2BValidationRequest from Safaricom

        Returns:
            Validation response
        """
        # C2B validation - just accept all for now
        # In production, could validate invoice, student, etc.
        logger.info(f"C2B validation: bill_ref={payload.BillRefNumber}")

        return {
            "ResultCode": 0,
            "ResultDesc": "Success",
        }

    async def process_c2b_confirmation(
        self,
        payload: C2BConfirmationRequest,
    ) -> dict:
        """
        Process C2B confirmation callback.

        Confirms C2B payment is complete.
        Must create receipt and update GL.

        Args:
            payload: C2BConfirmationRequest from Safaricom

        Returns:
            Confirmation response
        """
        # Parse C2B payload
        trans_id = payload.TransID  # M-Pesa receipt number
        amount = payload.TransAmount
        phone = payload.CallerMSISDN
        bill_ref = payload.BillRefNumber  # Can be student_id or invoice_id

        logger.info(
            f"C2B confirmation: trans_id={trans_id}, "
            f"amount={amount}, bill_ref={bill_ref}"
        )

        try:
            # Fetch student by ID or ID in bill reference
            # Assume bill_ref is student_id for now
            try:
                student_id = UUID(bill_ref)
            except ValueError:
                logger.error(f"Invalid student_id in bill_ref: {bill_ref}")
                raise ValidationError(f"Invalid student ID: {bill_ref}")

            student_query = select(Student).where(Student.id == student_id)
            student = await self.db.scalar(student_query)

            if not student:
                raise NotFoundError(f"Student {student_id} not found")

            # Create receipt and allocate payment
            fee_receipt = await self.receipt_service.create_receipt(
                school_id=student.school_id,
                student_id=student_id,
                receipt_date=datetime.now(timezone.utc).date(),
                amount=amount,
                payment_method="M-PESA_C2B",
                reference_number=trans_id,
                created_by_id=None,
            )

            # Allocate payment and post GL
            fee_receipt = await self.receipt_service.allocate_payment(
                school_id=student.school_id,
                receipt_id=fee_receipt.id,
                user_id=None,
            )

            logger.info(f"C2B receipt created: receipt_id={fee_receipt.id}")

            return {
                "ResultCode": 0,
                "ResultDesc": "Success",
            }

        except Exception as e:
            logger.error(f"C2B confirmation failed: {e}")
            # Still return success to Safaricom (idempotency)
            # Operator will manually reconcile if needed
            return {
                "ResultCode": 0,
                "ResultDesc": "Success",
            }

    async def get_transaction_status(
        self,
        checkout_request_id: str,
    ) -> Optional[MpesaTransaction]:
        """
        Get transaction status.

        Args:
            checkout_request_id: Checkout request ID

        Returns:
            MpesaTransaction or None
        """
        query = select(MpesaTransaction).where(
            MpesaTransaction.checkout_request_id == checkout_request_id
        )
        return await self.db.scalar(query)

    async def get_transactions_by_student(
        self,
        student_id: UUID,
        status: Optional[str] = None,
        limit: int = 50,
    ) -> list[MpesaTransaction]:
        """
        Get payment history for student.

        Args:
            student_id: Student ID
            status: Optional status filter (SUCCESS, FAILED, PENDING)
            limit: Max results

        Returns:
            List of MpesaTransaction records
        """
        query = select(MpesaTransaction).where(
            MpesaTransaction.student_id == student_id
        )

        if status:
            query = query.where(MpesaTransaction.status == status)

        query = query.order_by(MpesaTransaction.initiated_at.desc()).limit(limit)

        result = await self.db.execute(query)
        return result.scalars().all()
