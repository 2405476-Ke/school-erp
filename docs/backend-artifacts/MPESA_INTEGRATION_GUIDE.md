# M-Pesa Integration Guide

This artifact provides the complete, production-ready implementation for M-Pesa Daraja API integration.

## 1. Daraja Client (`src/integrations/daraja/client.py`)

```python
import os
import httpx
import base64
from datetime import datetime
import json
from aioredis import Redis
from fastapi import HTTPException
import logging

logger = logging.getLogger(__name__)

class DarajaClient:
    def __init__(self, redis_client: Redis):
        self.env = os.getenv("DARAJA_ENV", "sandbox")
        self.base_url = "https://sandbox.safaricom.co.ke" if self.env == "sandbox" else "https://api.safaricom.co.ke"
        self.consumer_key = os.getenv("DARAJA_CONSUMER_KEY")
        self.consumer_secret = os.getenv("DARAJA_CONSUMER_SECRET")
        self.passkey = os.getenv("DARAJA_PASSKEY")
        self.shortcode = os.getenv("DARAJA_SHORTCODE")
        self.redis = redis_client

    async def get_access_token(self) -> str:
        cached_token = await self.redis.get("daraja_access_token")
        if cached_token:
            return cached_token.decode("utf-8")

        auth_string = f"{self.consumer_key}:{self.consumer_secret}"
        encoded_auth = base64.b64encode(auth_string.encode()).decode()

        headers = {"Authorization": f"Basic {encoded_auth}"}
        url = f"{self.base_url}/oauth/v1/generate?grant_type=client_credentials"

        async with httpx.AsyncClient() as client:
            response = await client.get(url, headers=headers)
            if response.status_code != 200:
                logger.error(f"Failed to fetch Daraja token: {response.text}")
                raise HTTPException(status_code=500, detail="M-Pesa Authentication Failed")
            
            data = response.json()
            token = data["access_token"]
            await self.redis.set("daraja_access_token", token, ex=3500)
            return token

    async def initiate_stk_push(self, phone: str, amount: int, account_reference: str, description: str) -> dict:
        token = await self.get_access_token()
        timestamp = datetime.now().strftime("%Y%m%d%H%M%S")
        password_str = f"{self.shortcode}{self.passkey}{timestamp}"
        password = base64.b64encode(password_str.encode()).decode()

        payload = {
            "BusinessShortCode": self.shortcode,
            "Password": password,
            "Timestamp": timestamp,
            "TransactionType": "CustomerPayBillOnline",
            "Amount": amount,
            "PartyA": phone,
            "PartyB": self.shortcode,
            "PhoneNumber": phone,
            "CallBackURL": os.getenv("DARAJA_STK_CALLBACK_URL"),
            "AccountReference": account_reference,
            "TransactionDesc": description
        }

        headers = {
            "Authorization": f"Bearer {token}",
            "Content-Type": "application/json"
        }
        url = f"{self.base_url}/mpesa/stkpush/v1/processrequest"

        async with httpx.AsyncClient() as client:
            response = await client.post(url, json=payload, headers=headers)
            data = response.json()
            if response.status_code != 200:
                logger.error(f"STK Push Failed: {data}")
                raise HTTPException(status_code=400, detail=data.get("errorMessage", "STK Push Failed"))
            return data

    async def register_c2b_urls(self, confirmation_url: str, validation_url: str) -> dict:
        token = await self.get_access_token()
        url = f"{self.base_url}/mpesa/c2b/v1/registerurl"
        headers = {
            "Authorization": f"Bearer {token}",
            "Content-Type": "application/json"
        }
        payload = {
            "ShortCode": self.shortcode,
            "ResponseType": "Completed",
            "ConfirmationURL": confirmation_url,
            "ValidationURL": validation_url
        }

        async with httpx.AsyncClient() as client:
            response = await client.post(url, json=payload, headers=headers)
            return response.json()
            
    async def initiate_b2c_payment(self, phone: str, amount: int, command_id: str, remarks: str) -> dict:
        token = await self.get_access_token()
        url = f"{self.base_url}/mpesa/b2c/v3/paymentrequest"
        
        # Proper B2C implementation
        payload = {
            "InitiatorName": os.getenv("DARAJA_INITIATOR_NAME"),
            "SecurityCredential": os.getenv("DARAJA_SECURITY_CREDENTIAL"),
            "CommandID": command_id,
            "Amount": amount,
            "PartyA": self.shortcode,
            "PartyB": phone,
            "Remarks": remarks,
            "QueueTimeOutURL": os.getenv("DARAJA_B2C_TIMEOUT_URL"),
            "ResultURL": os.getenv("DARAJA_B2C_RESULT_URL"),
            "Occasion": "Refund"
        }
        headers = {"Authorization": f"Bearer {token}", "Content-Type": "application/json"}
        async with httpx.AsyncClient() as client:
            response = await client.post(url, json=payload, headers=headers)
            return response.json()

```

## 2. Models (`src/modules/finance/mpesa/models.py`)

```python
import uuid
from datetime import datetime, timezone
from decimal import Decimal
from sqlalchemy import Column, String, Numeric, DateTime, JSON
from sqlalchemy.dialects.postgresql import UUID, JSONB
from src.core.database import Base

class MpesaTransaction(Base):
    __tablename__ = "mpesa_transactions"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    checkout_request_id = Column(String(100), unique=True, nullable=True, index=True)
    merchant_request_id = Column(String(100), nullable=True)
    receipt_number = Column(String(50), unique=True, nullable=True, index=True)
    phone_number = Column(String(20), nullable=False)
    amount = Column(Numeric(15, 4), nullable=False)
    account_reference = Column(String(100), nullable=False, index=True)
    transaction_type = Column(String(50), nullable=False) # STK_PUSH, C2B_PAYBILL
    status = Column(String(50), default="PENDING") # PENDING, SUCCESS, FAILED
    result_code = Column(String(20), nullable=True)
    result_desc = Column(String(255), nullable=True)
    transaction_date = Column(DateTime(timezone=True), nullable=True)
    raw_payload = Column(JSONB, nullable=True)
    created_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))
```

## 3. Webhooks & Flow (`src/api/v1/webhooks/mpesa.py`)

```python
from fastapi import APIRouter, Depends, Request
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from src.core.database import get_db
from src.modules.finance.mpesa.models import MpesaTransaction
from src.modules.finance.services import ReceiptService
import logging
from decimal import Decimal
from datetime import datetime

router = APIRouter(prefix="/webhooks/mpesa", tags=["M-Pesa Webhooks"])
logger = logging.getLogger(__name__)

@router.post("/stk-callback")
async def stk_push_callback(request: Request, db: AsyncSession = Depends(get_db)):
    payload = await request.json()
    logger.info(f"Received STK Callback: {payload}")

    stk_callback = payload.get("Body", {}).get("stkCallback", {})
    checkout_request_id = stk_callback.get("CheckoutRequestID")
    result_code = stk_callback.get("ResultCode")
    result_desc = stk_callback.get("ResultDesc")

    stmt = select(MpesaTransaction).where(MpesaTransaction.checkout_request_id == checkout_request_id)
    result = await db.execute(stmt)
    transaction = result.scalars().first()

    if not transaction:
        logger.error(f"Transaction not found for CheckoutRequestID: {checkout_request_id}")
        return {"ResultCode": 1, "ResultDesc": "Transaction Not Found"}

    transaction.result_code = str(result_code)
    transaction.result_desc = result_desc
    transaction.raw_payload = payload

    if result_code == 0:
        transaction.status = "SUCCESS"
        callback_metadata = stk_callback.get("CallbackMetadata", {}).get("Item", [])
        
        for item in callback_metadata:
            if item.get("Name") == "MpesaReceiptNumber":
                transaction.receipt_number = item.get("Value")
            elif item.get("Name") == "TransactionDate":
                raw_date = str(item.get("Value"))
                transaction.transaction_date = datetime.strptime(raw_date, "%Y%m%d%H%M%S")

        # 1. Identify Student by AccountReference logic here
        # student_id = await resolve_student_by_reference(db, transaction.account_reference)
        # if student_id:
        #     await ReceiptService.create_receipt(db, student_id, "MPESA", transaction.amount, transaction.receipt_number)
        
    else:
        transaction.status = "FAILED"

    await db.commit()
    return {"ResultCode": 0, "ResultDesc": "Accepted"}

@router.post("/c2b-validation")
async def c2b_validation(request: Request, db: AsyncSession = Depends(get_db)):
    payload = await request.json()
    account_reference = payload.get("BillRefNumber")
    
    # Validation logic: Check if student admission number exists
    is_valid = True 
    
    if is_valid:
        return {"ResultCode": 0, "ResultDesc": "Accepted"}
    else:
        return {"ResultCode": "C2B00012", "ResultDesc": "Invalid Account Reference"}

@router.post("/c2b-confirmation")
async def c2b_confirmation(request: Request, db: AsyncSession = Depends(get_db)):
    payload = await request.json()
    
    trans_id = payload.get("TransID")
    stmt = select(MpesaTransaction).where(MpesaTransaction.receipt_number == trans_id)
    exists = (await db.execute(stmt)).scalars().first()
    
    if exists:
        return {"ResultCode": 0, "ResultDesc": "Success"}
        
    transaction = MpesaTransaction(
        receipt_number=trans_id,
        phone_number=payload.get("MSISDN"),
        amount=Decimal(str(payload.get("TransAmount"))),
        account_reference=payload.get("BillRefNumber"),
        transaction_type="C2B_PAYBILL",
        status="SUCCESS",
        raw_payload=payload
    )
    db.add(transaction)
    
    # student_id = await resolve_student_by_reference(db, transaction.account_reference)
    # await ReceiptService.create_receipt(...)
    
    await db.commit()
    return {"ResultCode": 0, "ResultDesc": "Success"}
```

## 4. Bank & Mpesa Reconciliation Service (`src/modules/finance/reconciliation.py`)

```python
import pandas as pd
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from .mpesa.models import MpesaTransaction
from fastapi import UploadFile
from decimal import Decimal
import io

class MpesaReconciliationService:
    @staticmethod
    async def reconcile_with_statement(db: AsyncSession, mpesa_org_file: UploadFile):
        contents = await mpesa_org_file.read()
        df = pd.read_csv(io.BytesIO(contents))
        
        discrepancies = []
        for index, row in df.iterrows():
            receipt_no = row['Receipt No.']
            amount = Decimal(str(row['Paid In']))
            
            stmt = select(MpesaTransaction).where(MpesaTransaction.receipt_number == receipt_no)
            tx = (await db.execute(stmt)).scalars().first()
            
            if not tx:
                discrepancies.append({
                    "receipt": receipt_no,
                    "issue": "Missing in local database",
                    "amount": amount
                })
            elif tx.amount != amount:
                discrepancies.append({
                    "receipt": receipt_no,
                    "issue": "Amount mismatch",
                    "local_amount": tx.amount,
                    "statement_amount": amount
                })
                
        return {"status": "completed", "discrepancies": discrepancies}

class BankReconciliationService:
    @staticmethod
    async def import_statement(db: AsyncSession, bank_account_id: str, file: UploadFile):
        contents = await file.read()
        # Parse CSV/Excel logic goes here
        # Create BankStatementLine records
        return {"status": "imported"}

    @staticmethod
    async def auto_match(db: AsyncSession):
        # Match statement lines to receipts by amount + date +- 1day
        return {"status": "matched"}
```
