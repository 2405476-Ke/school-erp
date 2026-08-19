"""
Celery Background Tasks for Message Dispatching.

CRITICAL: All SMS/Email sending happens asynchronously via Celery tasks
to avoid blocking the FastAPI server.
"""

import logging
import asyncio
import json
from uuid import UUID
from decimal import Decimal
from datetime import datetime
from typing import Optional

from sqlalchemy import select, and_
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy.orm import sessionmaker

from src.core.celery_app import celery_app
from src.core.config import settings
from src.modules.communication.models.communication import (
    CommunicationLog,
    CommunicationStatus,
    BulkCommunicationBatch,
)
from src.modules.communication.integrations.sms_provider import (
    AfricasTalkingClient,
    EmailProvider,
    PushNotificationProvider,
)

logger = logging.getLogger(__name__)


# Create async database session factory for Celery tasks
async_engine = create_async_engine(settings.DATABASE_URL, echo=False)
AsyncSessionLocal = sessionmaker(async_engine, class_=AsyncSession, expire_on_commit=False)


@celery_app.task(
    name="communication.process_sms_batch",
    bind=True,
    max_retries=3,
    default_retry_delay=60,
)
def process_sms_batch(
    self,
    batch_id: str,
    limit: int = 100,
):
    """
    CRITICAL CELERY TASK: Process pending SMS messages in batch.
    
    Algorithm:
    1. Query PENDING communication logs for this batch
    2. Chunk into batches of `limit` messages
    3. For each chunk:
       a. Get SMS provider client
       b. Send message via Africa's Talking
       c. Update log status to SENT or FAILED
       d. Update batch counters
    4. Mark batch complete if all messages processed
    5. Retry logic: On timeout/network error, retry up to 3 times
    
    Args:
        batch_id: Batch UUID to process
        limit: Max messages to process per task invocation
    """
    logger.info(f"Starting SMS batch processing: batch_id={batch_id}, limit={limit}")
    
    try:
        # Run async function within Celery sync context
        asyncio.run(_async_process_sms_batch(batch_id, limit))
        logger.info(f"SMS batch completed: {batch_id}")
    
    except Exception as exc:
        logger.error(f"SMS batch failed: {batch_id}, error={str(exc)}", exc_info=True)
        
        # Retry with exponential backoff
        if self.request.retries < self.max_retries:
            retry_delay = 60 * (2 ** self.request.retries)  # 60s, 120s, 240s
            logger.warning(f"Retrying SMS batch in {retry_delay}s: {batch_id}")
            raise self.retry(exc=exc, countdown=retry_delay)
        else:
            logger.error(f"Max retries exceeded for SMS batch: {batch_id}")
            raise


async def _async_process_sms_batch(batch_id: str, limit: int = 100):
    """
    Async implementation of SMS batch processing.
    
    Handles actual message dispatching with provider API calls.
    """
    logger.debug(f"Async SMS batch processing: batch_id={batch_id}")
    
    async with AsyncSessionLocal() as db:
        # STEP 1: Fetch batch
        batch_result = await db.execute(
            select(BulkCommunicationBatch).where(
                BulkCommunicationBatch.id == UUID(batch_id)
            )
        )
        batch = batch_result.scalars().first()
        
        if not batch:
            logger.error(f"Batch not found: {batch_id}")
            raise ValueError(f"Batch not found: {batch_id}")
        
        logger.debug(f"Processing batch: {batch.batch_name}, total_recipients={batch.total_recipients}")
        
        # STEP 2: Fetch pending logs for this batch
        pending_logs_result = await db.execute(
            select(CommunicationLog).where(
                and_(
                    CommunicationLog.batch_id == UUID(batch_id),
                    CommunicationLog.status == CommunicationStatus.PENDING.value,
                    CommunicationLog.retry_count < CommunicationLog.max_retries,
                )
            ).limit(limit)
        )
        logs = pending_logs_result.scalars().all()
        
        logger.info(f"Found {len(logs)} pending messages in batch")
        
        if not logs:
            logger.info(f"No more pending messages in batch: {batch_id}")
            batch.completed_at = datetime.utcnow()
            await db.commit()
            return
        
        # Initialize provider clients
        sms_client = AfricasTalkingClient(
            api_key=settings.AFRICAS_TALKING_API_KEY,
            username=settings.AFRICAS_TALKING_USERNAME,
        )
        
        # STEP 3: Process each log
        sent_count = 0
        failed_count = 0
        
        for log in logs:
            try:
                logger.debug(f"Sending to {log.recipient_contact}: {log.message_type}")
                
                # Send based on message type
                if log.message_type == "SMS":
                    response = await sms_client.send_sms(
                        log.recipient_contact,
                        log.rendered_content,
                    )
                else:
                    # Email/Push not yet implemented in this batch
                    logger.warning(f"Message type not yet supported in batch: {log.message_type}")
                    response = None
                
                if response:
                    # Update log with response
                    log.status = response.status
                    log.provider_message_id = response.message_id
                    log.provider_response = json.dumps(response.raw_response)
                    log.sent_at = datetime.utcnow()
                    
                    if response.success:
                        logger.debug(f"Message sent: {log.id}, provider_id={response.message_id}")
                        sent_count += 1
                    else:
                        log.error_message = response.error
                        logger.warning(f"Message failed: {log.id}, error={response.error}")
                        failed_count += 1
                        
                        # Increment retry count for potential retry
                        log.retry_count += 1
                
            except Exception as e:
                logger.error(f"Error processing message {log.id}: {str(e)}", exc_info=True)
                log.status = CommunicationStatus.FAILED.value
                log.error_message = str(e)
                log.retry_count += 1
                failed_count += 1
        
        # STEP 4: Update batch counters
        batch.total_sent += sent_count
        batch.total_failed += failed_count
        
        # Recalculate pending
        remaining_result = await db.execute(
            select(CommunicationLog).where(
                and_(
                    CommunicationLog.batch_id == UUID(batch_id),
                    CommunicationLog.status == CommunicationStatus.PENDING.value,
                )
            )
        )
        remaining = len(remaining_result.scalars().all())
        batch.total_pending = remaining
        
        # If no more pending, mark batch complete
        if remaining == 0:
            batch.completed_at = datetime.utcnow()
            logger.info(f"Batch completed: {batch.batch_name}, sent={batch.total_sent}, failed={batch.total_failed}")
        
        # Commit all changes
        await db.commit()
        logger.info(f"Batch checkpoint: sent={sent_count}, failed={failed_count}, remaining={remaining}")


@celery_app.task(
    name="communication.retry_failed_messages",
    bind=True,
    max_retries=2,
)
def retry_failed_messages(self, batch_id: str):
    """
    Retry messages that failed in a batch.
    
    Called periodically to retry failed messages with exponential backoff.
    """
    logger.info(f"Retrying failed messages for batch: {batch_id}")
    
    try:
        asyncio.run(_async_retry_failed_messages(batch_id))
    except Exception as exc:
        if self.request.retries < self.max_retries:
            retry_delay = 300 * (2 ** self.request.retries)  # 5min, 10min
            logger.warning(f"Retrying failed messages in {retry_delay}s")
            raise self.retry(exc=exc, countdown=retry_delay)
        else:
            logger.error(f"Max retries for failed messages: {batch_id}")
            raise


async def _async_retry_failed_messages(batch_id: str):
    """Async retry implementation."""
    logger.debug(f"Async retry for batch: {batch_id}")
    
    async with AsyncSessionLocal() as db:
        # Query failed messages with retry_count < max_retries
        failed_logs_result = await db.execute(
            select(CommunicationLog).where(
                and_(
                    CommunicationLog.batch_id == UUID(batch_id),
                    CommunicationLog.status == CommunicationStatus.FAILED.value,
                    CommunicationLog.retry_count < CommunicationLog.max_retries,
                )
            )
        )
        logs = failed_logs_result.scalars().all()
        
        logger.info(f"Found {len(logs)} failed messages to retry")
        
        if not logs:
            logger.info("No failed messages to retry")
            return
        
        # Trigger SMS batch processing for these messages
        # Reset status to PENDING so they get processed
        for log in logs:
            log.status = CommunicationStatus.PENDING.value
        
        await db.commit()
        logger.info(f"Reset {len(logs)} messages to PENDING for retry")
        
        # Trigger batch processing task
        process_sms_batch.delay(batch_id)


@celery_app.task(name="communication.cleanup_old_logs")
def cleanup_old_logs():
    """
    Cleanup communication logs older than 90 days.
    
    Scheduled task to remove old communication records.
    """
    logger.info("Starting cleanup of old communication logs")
    
    try:
        asyncio.run(_async_cleanup_old_logs())
    except Exception as e:
        logger.error(f"Cleanup failed: {str(e)}", exc_info=True)
        raise


async def _async_cleanup_old_logs():
    """Async cleanup implementation."""
    from datetime import timedelta
    
    async with AsyncSessionLocal() as db:
        cutoff_date = datetime.utcnow() - timedelta(days=90)
        
        # Delete old SENT/FAILED logs
        result = await db.execute(
            select(CommunicationLog).where(
                and_(
                    CommunicationLog.created_at < cutoff_date,
                    CommunicationLog.status.in_([
                        CommunicationStatus.SENT.value,
                        CommunicationStatus.FAILED.value,
                        CommunicationStatus.DELIVERED.value,
                    ])
                )
            )
        )
        logs = result.scalars().all()
        
        deleted_count = len(logs)
        for log in logs:
            await db.delete(log)
        
        await db.commit()
        logger.info(f"Cleaned up {deleted_count} communication logs older than 90 days")
