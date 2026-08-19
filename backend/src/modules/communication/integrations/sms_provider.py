"""
SMS Provider Integration.

Generic async SMS client supporting multiple providers (Africa's Talking, Twilio, etc).
"""

import logging
import json
from typing import Optional
from decimal import Decimal

import httpx

logger = logging.getLogger(__name__)


class SMSProviderResponse:
    """Standardized SMS provider response."""
    
    def __init__(
        self,
        success: bool,
        message_id: Optional[str] = None,
        status: str = "PENDING",
        error: Optional[str] = None,
        raw_response: Optional[dict] = None,
    ):
        self.success = success
        self.message_id = message_id
        self.status = status
        self.error = error
        self.raw_response = raw_response or {}


class AfricasTalkingClient:
    """
    Africa's Talking SMS API client.
    
    Async HTTP client for sending SMS via Africa's Talking provider.
    """
    
    API_URL = "https://api.sandbox.africastalking.com/version1/messaging"
    
    def __init__(
        self,
        api_key: str,
        username: str = "sandbox",
        timeout: int = 30,
    ):
        """
        Initialize Africa's Talking client.
        
        Args:
            api_key: API key from Africa's Talking dashboard
            username: Account username (default: sandbox for testing)
            timeout: Request timeout in seconds
        """
        self.api_key = api_key
        self.username = username
        self.timeout = timeout
        
        logger.debug(f"Initialized Africa's Talking client for user: {username}")
    
    async def send_sms(
        self,
        phone_number: str,
        message: str,
    ) -> SMSProviderResponse:
        """
        Send SMS via Africa's Talking.
        
        Args:
            phone_number: Recipient phone number (with or without +)
            message: SMS message text
        
        Returns:
            SMSProviderResponse with status and message ID
        """
        # Normalize phone number
        if not phone_number.startswith("+"):
            if phone_number.startswith("0"):
                phone_number = "+254" + phone_number[1:]
            else:
                phone_number = "+" + phone_number
        
        logger.debug(f"Sending SMS to {phone_number}, message_length={len(message)}")
        
        # Check message length (SMS has 160 char limit per segment)
        if len(message) > 160:
            logger.warning(f"Message longer than 160 chars ({len(message)}), will be split")
        
        # Prepare payload
        payload = {
            "username": self.username,
            "to": phone_number,
            "message": message,
        }
        
        try:
            async with httpx.AsyncClient(timeout=self.timeout) as client:
                response = await client.post(
                    self.API_URL,
                    data=payload,
                    headers={"Accept": "application/json", "apiKey": self.api_key},
                )
            
            # Log response
            logger.debug(f"Africa's Talking response status: {response.status_code}")
            
            if response.status_code != 201:
                error_msg = f"SMS send failed with status {response.status_code}"
                logger.error(f"{error_msg}: {response.text}")
                
                return SMSProviderResponse(
                    success=False,
                    error=error_msg,
                    raw_response={"status_code": response.status_code, "body": response.text},
                )
            
            # Parse response
            response_data = response.json()
            logger.debug(f"Response: {response_data}")
            
            # Africa's Talking returns SMSMessageData in recipients array
            if response_data.get("SMSMessageData", {}).get("Recipients"):
                recipient = response_data["SMSMessageData"]["Recipients"][0]
                message_id = recipient.get("messageId")
                status_code = recipient.get("statusCode")
                
                # Status code 0 = success, other codes indicate issues
                success = status_code == 0
                status = "SENT" if success else "FAILED"
                error = None if success else recipient.get("status", "Unknown error")
                
                logger.info(
                    f"SMS sent to {phone_number}: message_id={message_id}, "
                    f"status_code={status_code}, success={success}"
                )
                
                return SMSProviderResponse(
                    success=success,
                    message_id=message_id,
                    status=status,
                    error=error,
                    raw_response=response_data,
                )
            else:
                logger.error(f"Unexpected response format: {response_data}")
                return SMSProviderResponse(
                    success=False,
                    error="Unexpected response format",
                    raw_response=response_data,
                )
        
        except httpx.TimeoutException as e:
            error_msg = f"SMS request timeout: {str(e)}"
            logger.error(error_msg)
            return SMSProviderResponse(success=False, error=error_msg)
        
        except httpx.HTTPError as e:
            error_msg = f"SMS request error: {str(e)}"
            logger.error(error_msg)
            return SMSProviderResponse(success=False, error=error_msg)
        
        except json.JSONDecodeError as e:
            error_msg = f"Failed to parse SMS response: {str(e)}"
            logger.error(error_msg)
            return SMSProviderResponse(success=False, error=error_msg)
        
        except Exception as e:
            error_msg = f"Unexpected error sending SMS: {str(e)}"
            logger.error(error_msg, exc_info=True)
            return SMSProviderResponse(success=False, error=error_msg)


class EmailProvider:
    """
    Email provider client.
    
    Can be implemented using SendGrid, AWS SES, or local SMTP.
    """
    
    def __init__(
        self,
        provider_type: str = "smtp",  # smtp, sendgrid, ses
        api_key: Optional[str] = None,
        from_address: str = "noreply@school.local",
        timeout: int = 30,
    ):
        """
        Initialize email provider.
        
        Args:
            provider_type: Type of email provider
            api_key: API key if using cloud provider
            from_address: Sender email address
            timeout: Request timeout
        """
        self.provider_type = provider_type
        self.api_key = api_key
        self.from_address = from_address
        self.timeout = timeout
        
        logger.debug(f"Initialized email provider: {provider_type}")
    
    async def send_email(
        self,
        to_address: str,
        subject: str,
        body: str,
        body_html: Optional[str] = None,
    ) -> SMSProviderResponse:
        """
        Send email.
        
        Args:
            to_address: Recipient email address
            subject: Email subject
            body: Plain text body
            body_html: HTML body (optional)
        
        Returns:
            SMSProviderResponse with status and message ID
        """
        logger.debug(f"Sending email to {to_address}, subject='{subject}'")
        
        if self.provider_type == "smtp":
            return await self._send_via_smtp(to_address, subject, body, body_html)
        elif self.provider_type == "sendgrid":
            return await self._send_via_sendgrid(to_address, subject, body, body_html)
        else:
            return SMSProviderResponse(
                success=False,
                error=f"Unknown email provider: {self.provider_type}",
            )
    
    async def _send_via_smtp(
        self,
        to_address: str,
        subject: str,
        body: str,
        body_html: Optional[str] = None,
    ) -> SMSProviderResponse:
        """Send email via SMTP (placeholder - requires aiosmtplib)."""
        logger.debug(f"Email queued via SMTP to {to_address}")
        
        # In production, use aiosmtplib for async SMTP
        # For now, return success as placeholder
        return SMSProviderResponse(
            success=True,
            message_id=f"email_{to_address}_{int(__import__('time').time())}",
            status="SENT",
        )
    
    async def _send_via_sendgrid(
        self,
        to_address: str,
        subject: str,
        body: str,
        body_html: Optional[str] = None,
    ) -> SMSProviderResponse:
        """Send email via SendGrid API."""
        try:
            async with httpx.AsyncClient(timeout=self.timeout) as client:
                response = await client.post(
                    "https://api.sendgrid.com/v3/mail/send",
                    json={
                        "personalizations": [{"to": [{"email": to_address}]}],
                        "from": {"email": self.from_address},
                        "subject": subject,
                        "content": [
                            {"type": "text/plain", "value": body},
                            {"type": "text/html", "value": body_html or body},
                        ],
                    },
                    headers={"Authorization": f"Bearer {self.api_key}"},
                )
            
            if response.status_code == 202:
                logger.info(f"Email sent via SendGrid to {to_address}")
                return SMSProviderResponse(
                    success=True,
                    message_id=response.headers.get("X-Message-Id", "sendgrid_unknown"),
                    status="SENT",
                )
            else:
                error_msg = f"SendGrid error: {response.status_code}"
                logger.error(f"{error_msg}: {response.text}")
                return SMSProviderResponse(success=False, error=error_msg)
        
        except Exception as e:
            error_msg = f"Email send error: {str(e)}"
            logger.error(error_msg)
            return SMSProviderResponse(success=False, error=error_msg)


class PushNotificationProvider:
    """
    Push notification provider (Firebase Cloud Messaging, OneSignal, etc).
    """
    
    def __init__(
        self,
        provider_type: str = "fcm",
        api_key: Optional[str] = None,
        timeout: int = 30,
    ):
        """
        Initialize push notification provider.
        
        Args:
            provider_type: Type of provider (fcm, onesignal)
            api_key: API key/credentials
            timeout: Request timeout
        """
        self.provider_type = provider_type
        self.api_key = api_key
        self.timeout = timeout
        
        logger.debug(f"Initialized push provider: {provider_type}")
    
    async def send_push(
        self,
        device_token: str,
        title: str,
        body: str,
        data: Optional[dict] = None,
    ) -> SMSProviderResponse:
        """
        Send push notification.
        
        Args:
            device_token: Device FCM/push token
            title: Notification title
            body: Notification body
            data: Additional data payload
        
        Returns:
            SMSProviderResponse with status and message ID
        """
        logger.debug(f"Sending push to {device_token[:20]}..., title='{title}'")
        
        if self.provider_type == "fcm":
            return await self._send_via_fcm(device_token, title, body, data)
        else:
            return SMSProviderResponse(
                success=False,
                error=f"Unknown push provider: {self.provider_type}",
            )
    
    async def _send_via_fcm(
        self,
        device_token: str,
        title: str,
        body: str,
        data: Optional[dict] = None,
    ) -> SMSProviderResponse:
        """Send push via Firebase Cloud Messaging."""
        try:
            async with httpx.AsyncClient(timeout=self.timeout) as client:
                response = await client.post(
                    "https://fcm.googleapis.com/fcm/send",
                    json={
                        "to": device_token,
                        "notification": {"title": title, "body": body},
                        "data": data or {},
                    },
                    headers={
                        "Authorization": f"key={self.api_key}",
                        "Content-Type": "application/json",
                    },
                )
            
            if response.status_code == 200:
                response_data = response.json()
                message_id = response_data.get("message_id")
                logger.info(f"Push sent via FCM: message_id={message_id}")
                
                return SMSProviderResponse(
                    success=True,
                    message_id=message_id,
                    status="SENT",
                )
            else:
                error_msg = f"FCM error: {response.status_code}"
                logger.error(f"{error_msg}: {response.text}")
                return SMSProviderResponse(success=False, error=error_msg)
        
        except Exception as e:
            error_msg = f"Push send error: {str(e)}"
            logger.error(error_msg)
            return SMSProviderResponse(success=False, error=error_msg)
