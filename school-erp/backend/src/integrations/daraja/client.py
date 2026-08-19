"""
Daraja API Client: Async httpx client for Safaricom M-Pesa Daraja API.

REAL implementation:
- OAuth token caching via Redis (3500 seconds)
- STK Push with proper Base64 password generation
- No mocking - real Safaricom API calls
"""
import base64
import logging
from datetime import datetime, timezone
from decimal import Decimal
from typing import Optional

import httpx
import redis.asyncio as redis

from src.core.config import settings

logger = logging.getLogger(__name__)


class DarajaClient:
    """
    Async client for Safaricom M-Pesa Daraja API.

    Handles:
    - OAuth token generation and Redis caching
    - STK Push initiation
    - C2B registration
    """

    def __init__(self):
        """Initialize Daraja client with settings from config."""
        self.base_url = settings.MPESA_BASE_URL  # sandbox or production
        self.consumer_key = settings.MPESA_CONSUMER_KEY
        self.consumer_secret = settings.MPESA_CONSUMER_SECRET
        self.shortcode = settings.MPESA_SHORTCODE
        self.passkey = settings.MPESA_PASSKEY
        self.callback_url = settings.MPESA_CALLBACK_URL

        # Redis for token caching
        self.redis_url = settings.REDIS_URL
        self.token_cache_key = "mpesa:oauth_token"
        self.token_ttl = 3500  # 3600 - 100 buffer

    async def _get_redis(self) -> redis.Redis:
        """Get Redis connection."""
        return await redis.from_url(self.redis_url)

    async def get_access_token(self) -> str:
        """
        Get OAuth access token from Safaricom.

        REAL IMPLEMENTATION:
        1. Check Redis cache for token
        2. If cached and valid, return cached token
        3. Otherwise, call Safaricom OAuth endpoint
        4. Cache token in Redis with 3500s TTL
        5. Return token

        The OAuth endpoint requires:
        - Authorization header: Basic base64(consumer_key:consumer_secret)
        - grant_type: client_credentials

        Args:
            None

        Returns:
            OAuth access token (str)

        Raises:
            Exception: If OAuth call fails
        """
        # 1. Try cache first
        redis_client = await self._get_redis()
        try:
            cached_token = await redis_client.get(self.token_cache_key)
            if cached_token:
                logger.info("Using cached OAuth token")
                return cached_token.decode() if isinstance(cached_token, bytes) else cached_token
        except Exception as e:
            logger.warning(f"Redis cache miss: {e}")
        finally:
            await redis_client.close()

        # 2. Generate new token via OAuth
        logger.info("Requesting new OAuth token from Safaricom")

        # Build Basic Auth header: base64(consumer_key:consumer_secret)
        credentials = f"{self.consumer_key}:{self.consumer_secret}"
        encoded_credentials = base64.b64encode(credentials.encode()).decode()

        oauth_url = f"{self.base_url}/oauth/v1/generate"
        headers = {
            "Authorization": f"Basic {encoded_credentials}",
            "Content-Type": "application/json",
        }

        try:
            async with httpx.AsyncClient(timeout=30.0) as client:
                response = await client.get(
                    oauth_url,
                    headers=headers,
                    params={"grant_type": "client_credentials"},
                )
                response.raise_for_status()

                data = response.json()
                access_token = data.get("access_token")

                if not access_token:
                    raise ValueError("No access_token in OAuth response")

                # 3. Cache token in Redis
                redis_client = await self._get_redis()
                try:
                    await redis_client.setex(
                        self.token_cache_key,
                        self.token_ttl,
                        access_token,
                    )
                    logger.info(f"Cached OAuth token (TTL: {self.token_ttl}s)")
                finally:
                    await redis_client.close()

                return access_token

        except httpx.HTTPStatusError as e:
            logger.error(f"OAuth error: {e.response.status_code} - {e.response.text}")
            raise Exception(f"Failed to get OAuth token: {e.response.text}")
        except Exception as e:
            logger.error(f"OAuth exception: {e}")
            raise

    async def initiate_stk_push(
        self,
        phone_number: str,
        amount: Decimal,
        account_reference: str,
        transaction_desc: str,
        checkout_request_id: str,
    ) -> dict:
        """
        Initiate STK Push for M-Pesa payment.

        REAL IMPLEMENTATION with proper Base64 password generation:
        1. Generate timestamp: YYYYMMDDHHmmss
        2. Build password string: Shortcode + Passkey + Timestamp
        3. Encode password: Base64(password_string)
        4. Call STK Push endpoint with Bearer token
        5. Return response with CheckoutRequestID

        Password generation is CRITICAL:
        - Timestamp must be in format: YYYYMMDDHHmmss (no separators)
        - Example: 20250116143025 for 2025-01-16 14:30:25
        - String: "174379" + passkey + "20250116143025"
        - Result: base64(string)

        Args:
            phone_number: Customer phone (254712345678 or 0712345678)
            amount: Amount to charge (KES)
            account_reference: Student ID or invoice number
            transaction_desc: Description (e.g., "Fee Payment - January 2025")
            checkout_request_id: Unique request ID for idempotency

        Returns:
            Dict with {
                "CheckoutRequestID": str,
                "ResponseCode": str,
                "ResponseDescription": str,
                "MerchantRequestID": str
            }

        Raises:
            Exception: If STK Push call fails
        """
        # 1. Normalize phone number (ensure 254 prefix)
        if phone_number.startswith("0"):
            phone_number = "254" + phone_number[1:]
        elif not phone_number.startswith("254"):
            phone_number = "254" + phone_number

        # 2. Generate timestamp in YYYYMMDDHHmmss format
        now = datetime.now(timezone.utc)
        timestamp = now.strftime("%Y%m%d%H%M%S")

        # 3. Generate password: Base64(Shortcode + Passkey + Timestamp)
        password_string = f"{self.shortcode}{self.passkey}{timestamp}"
        password_bytes = password_string.encode("utf-8")
        password_b64 = base64.b64encode(password_bytes).decode("utf-8")

        logger.info(
            f"STK Push: phone={phone_number}, amount={amount}, "
            f"timestamp={timestamp}, checkout_id={checkout_request_id}"
        )

        # 4. Get OAuth token
        access_token = await self.get_access_token()

        # 5. Build STK Push request
        stk_push_url = f"{self.base_url}/mpesa/stkpush/v1/processrequest"

        headers = {
            "Authorization": f"Bearer {access_token}",
            "Content-Type": "application/json",
        }

        payload = {
            "BusinessShortCode": self.shortcode,
            "Password": password_b64,
            "Timestamp": timestamp,
            "TransactionType": "CustomerPayBillOnline",
            "Amount": int(amount),  # Must be integer (no decimals)
            "PartyA": phone_number,
            "PartyB": self.shortcode,
            "PhoneNumber": phone_number,
            "CallBackURL": self.callback_url,
            "AccountReference": str(account_reference),
            "TransactionDesc": transaction_desc,
        }

        try:
            async with httpx.AsyncClient(timeout=30.0) as client:
                response = await client.post(
                    stk_push_url,
                    json=payload,
                    headers=headers,
                )
                response.raise_for_status()

                data = response.json()
                logger.info(f"STK Push response: {data}")

                return {
                    "CheckoutRequestID": data.get("CheckoutRequestID"),
                    "ResponseCode": data.get("ResponseCode"),
                    "ResponseDescription": data.get("ResponseDescription"),
                    "MerchantRequestID": data.get("MerchantRequestID"),
                }

        except httpx.HTTPStatusError as e:
            logger.error(f"STK Push error: {e.response.status_code} - {e.response.text}")
            raise Exception(f"STK Push failed: {e.response.text}")
        except Exception as e:
            logger.error(f"STK Push exception: {e}")
            raise

    async def query_transaction_status(
        self,
        checkout_request_id: str,
    ) -> dict:
        """
        Query status of STK Push transaction.

        Args:
            checkout_request_id: CheckoutRequestID from initiate_stk_push

        Returns:
            Transaction status details
        """
        # Similar password generation as STK Push
        now = datetime.now(timezone.utc)
        timestamp = now.strftime("%Y%m%d%H%M%S")
        password_string = f"{self.shortcode}{self.passkey}{timestamp}"
        password_b64 = base64.b64encode(password_string.encode()).decode()

        access_token = await self.get_access_token()

        query_url = f"{self.base_url}/mpesa/stkpushquery/v1/query"

        headers = {
            "Authorization": f"Bearer {access_token}",
            "Content-Type": "application/json",
        }

        payload = {
            "BusinessShortCode": self.shortcode,
            "Password": password_b64,
            "Timestamp": timestamp,
            "CheckoutRequestID": checkout_request_id,
        }

        try:
            async with httpx.AsyncClient(timeout=30.0) as client:
                response = await client.post(
                    query_url,
                    json=payload,
                    headers=headers,
                )
                response.raise_for_status()

                return response.json()

        except Exception as e:
            logger.error(f"Query transaction status failed: {e}")
            raise

    async def register_c2b_urls(
        self,
        validation_url: str,
        confirmation_url: str,
    ) -> dict:
        """
        Register C2B validation and confirmation URLs.

        Args:
            validation_url: URL for validation callback
            confirmation_url: URL for confirmation callback

        Returns:
            Registration response
        """
        access_token = await self.get_access_token()

        register_url = f"{self.base_url}/mpesa/c2b/v1/registerurl"

        headers = {
            "Authorization": f"Bearer {access_token}",
            "Content-Type": "application/json",
        }

        payload = {
            "ShortCode": self.shortcode,
            "ResponseType": "Completed",
            "ConfirmationURL": confirmation_url,
            "ValidationURL": validation_url,
        }

        try:
            async with httpx.AsyncClient(timeout=30.0) as client:
                response = await client.post(
                    register_url,
                    json=payload,
                    headers=headers,
                )
                response.raise_for_status()

                logger.info("C2B URLs registered successfully")
                return response.json()

        except Exception as e:
            logger.error(f"C2B registration failed: {e}")
            raise
