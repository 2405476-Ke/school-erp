"""
Communication & Notifications FastAPI Routers.

Endpoints for managing templates, queuing bulk messages, and viewing logs.
"""

import logging
from uuid import UUID
from decimal import Decimal

from fastapi import APIRouter, Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession

from src.core.database import get_db
from src.core.exceptions import NotFoundError, ValidationError
from src.core.response import APIResponse
from src.modules.communication.schemas.communication import (
    CreateMessageTemplateRequest,
    MessageTemplateResponse,
    CommunicationLogResponse,
    BulkCommunicationBatchResponse,
    QueueFeeRemindersRequest,
    QueueBulkCommunicationRequest,
    SendTestSMSRequest,
    OptOutPreferenceRequest,
    OptOutPreferenceResponse,
    CommunicationReportResponse,
)
from src.modules.communication.services.notification_service import NotificationService
from src.modules.communication.integrations.sms_provider import (
    AfricasTalkingClient,
)

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/communications", tags=["Communications & Notifications"])


# ============================================================================
# MESSAGE TEMPLATES
# ============================================================================


@router.post("/templates", response_model=APIResponse)
async def create_template(
    request: CreateMessageTemplateRequest,
    db: AsyncSession = Depends(get_db),
    school_id: UUID = Depends(lambda: UUID("00000000-0000-0000-0000-000000000000")),
) -> APIResponse:
    """Create message template."""
    try:
        service = NotificationService(db)
        result = await service.create_message_template(
            school_id=school_id,
            name=request.name,
            message_type=request.message_type,
            content=request.content,
            description=request.description,
            subject=request.subject,
        )
        
        return APIResponse.success(
            data=result,
            message="Message template created",
            status_code=201,
        )
    
    except ValidationError as e:
        return APIResponse.error(
            error=str(e),
            message="Template creation failed",
            status_code=400,
        )
    
    except Exception as e:
        logger.error(f"Error creating template: {e}")
        return APIResponse.error(
            error=str(e),
            message="Failed to create template",
            status_code=500,
        )


@router.get("/templates/{template_id}", response_model=APIResponse)
async def get_template(
    template_id: UUID,
    db: AsyncSession = Depends(get_db),
    school_id: UUID = Depends(lambda: UUID("00000000-0000-0000-0000-000000000000")),
) -> APIResponse:
    """Get message template."""
    try:
        from sqlalchemy import select, and_
        from src.modules.communication.models.communication import MessageTemplate
        
        template = await db.scalar(
            select(MessageTemplate).where(
                and_(
                    MessageTemplate.id == template_id,
                    MessageTemplate.school_id == school_id,
                )
            )
        )
        
        if not template:
            return APIResponse.error(
                error="Not found",
                message="Template not found",
                status_code=404,
            )
        
        return APIResponse.success(
            data={
                "id": str(template.id),
                "name": template.name,
                "message_type": template.message_type,
                "description": template.description,
                "subject": template.subject,
                "content": template.content,
                "is_active": template.is_active,
                "created_at": template.created_at.isoformat(),
            },
            message="Template retrieved",
            status_code=200,
        )
    
    except Exception as e:
        logger.error(f"Error getting template: {e}")
        return APIResponse.error(
            error=str(e),
            message="Failed to get template",
            status_code=500,
        )


# ============================================================================
# BULK FEE REMINDERS
# ============================================================================


@router.post("/queue/fee-reminders", response_model=APIResponse)
async def queue_fee_reminders(
    request: QueueFeeRemindersRequest,
    db: AsyncSession = Depends(get_db),
    school_id: UUID = Depends(lambda: UUID("00000000-0000-0000-0000-000000000000")),
) -> APIResponse:
    """
    CRITICAL: Queue bulk fee reminder SMS.
    
    This endpoint:
    1. Queries Finance module for students with outstanding fees
    2. Creates CommunicationLog records
    3. Triggers Celery task for async SMS dispatch
    4. Returns immediately with batch_id
    
    The actual SMS sending happens asynchronously in background.
    """
    try:
        service = NotificationService(db)
        result = await service.queue_bulk_fee_reminders(
            school_id=school_id,
            term_id=request.term_id,
            message_template_id=request.message_template_id,
            minimum_balance=request.minimum_balance,
            recipient_type=request.recipient_type,
        )
        
        return APIResponse.success(
            data=result,
            message="Fee reminders queued for async dispatch",
            status_code=202,
        )
    
    except NotFoundError as e:
        return APIResponse.error(
            error=str(e),
            message="Resource not found",
            status_code=404,
        )
    
    except ValidationError as e:
        return APIResponse.error(
            error=str(e),
            message="Queue operation failed",
            status_code=400,
        )
    
    except Exception as e:
        logger.error(f"Error queueing fee reminders: {e}", exc_info=True)
        return APIResponse.error(
            error=str(e),
            message="Failed to queue reminders",
            status_code=500,
        )


# ============================================================================
# BULK COMMUNICATIONS
# ============================================================================


@router.post("/queue/bulk", response_model=APIResponse)
async def queue_bulk_communication(
    request: QueueBulkCommunicationRequest,
    db: AsyncSession = Depends(get_db),
    school_id: UUID = Depends(lambda: UUID("00000000-0000-0000-0000-000000000000")),
) -> APIResponse:
    """Queue bulk communication to multiple recipients."""
    try:
        service = NotificationService(db)
        result = await service.queue_bulk_communication(
            school_id=school_id,
            template_id=request.template_id,
            batch_name=request.batch_name,
            batch_type=request.batch_type,
            recipient_ids=request.recipient_ids,
            recipient_type=request.recipient_type,
            template_variables=request.template_variables,
        )
        
        return APIResponse.success(
            data=result,
            message="Bulk communication queued",
            status_code=202,
        )
    
    except NotFoundError as e:
        return APIResponse.error(
            error=str(e),
            message="Template not found",
            status_code=404,
        )
    
    except ValidationError as e:
        return APIResponse.error(
            error=str(e),
            message="Queue validation failed",
            status_code=400,
        )
    
    except Exception as e:
        logger.error(f"Error queuing bulk communication: {e}")
        return APIResponse.error(
            error=str(e),
            message="Failed to queue communication",
            status_code=500,
        )


# ============================================================================
# COMMUNICATION LOGS & REPORTS
# ============================================================================


@router.get("/logs/{log_id}", response_model=APIResponse)
async def get_communication_log(
    log_id: UUID,
    db: AsyncSession = Depends(get_db),
    school_id: UUID = Depends(lambda: UUID("00000000-0000-0000-0000-000000000000")),
) -> APIResponse:
    """Get communication log detail."""
    try:
        service = NotificationService(db)
        result = await service.get_communication_log(school_id, log_id)
        
        return APIResponse.success(
            data=result,
            message="Log retrieved",
            status_code=200,
        )
    
    except NotFoundError as e:
        return APIResponse.error(
            error=str(e),
            message="Log not found",
            status_code=404,
        )
    
    except Exception as e:
        logger.error(f"Error getting log: {e}")
        return APIResponse.error(
            error=str(e),
            message="Failed to get log",
            status_code=500,
        )


@router.get("/batches/{batch_id}/report", response_model=APIResponse)
async def get_batch_report(
    batch_id: UUID,
    db: AsyncSession = Depends(get_db),
    school_id: UUID = Depends(lambda: UUID("00000000-0000-0000-0000-000000000000")),
) -> APIResponse:
    """Get batch communication report."""
    try:
        service = NotificationService(db)
        result = await service.get_batch_report(school_id, batch_id)
        
        return APIResponse.success(
            data=result,
            message="Report retrieved",
            status_code=200,
        )
    
    except NotFoundError as e:
        return APIResponse.error(
            error=str(e),
            message="Batch not found",
            status_code=404,
        )
    
    except Exception as e:
        logger.error(f"Error getting report: {e}")
        return APIResponse.error(
            error=str(e),
            message="Failed to get report",
            status_code=500,
        )


# ============================================================================
# OPT-OUT MANAGEMENT
# ============================================================================


@router.post("/opt-out", response_model=APIResponse)
async def set_opt_out(
    request: OptOutPreferenceRequest,
    db: AsyncSession = Depends(get_db),
    school_id: UUID = Depends(lambda: UUID("00000000-0000-0000-0000-000000000000")),
) -> APIResponse:
    """Set opt-out preference."""
    try:
        service = NotificationService(db)
        result = await service.set_opt_out_preference(
            school_id=school_id,
            recipient_type=request.recipient_type,
            recipient_id=request.recipient_id,
            message_type=request.message_type,
            is_opted_out=request.is_opted_out,
            reason=request.reason,
        )
        
        action = "opted out of" if request.is_opted_out else "opted in to"
        return APIResponse.success(
            data=result,
            message=f"Successfully {action} {request.message_type} messages",
            status_code=200,
        )
    
    except Exception as e:
        logger.error(f"Error setting opt-out: {e}")
        return APIResponse.error(
            error=str(e),
            message="Failed to set preference",
            status_code=500,
        )


# ============================================================================
# TESTING & ADMIN
# ============================================================================


@router.post("/test/send-sms", response_model=APIResponse)
async def send_test_sms(
    request: SendTestSMSRequest,
) -> APIResponse:
    """Send test SMS to validate provider configuration."""
    try:
        from src.core.config import settings
        
        client = AfricasTalkingClient(
            api_key=settings.AFRICAS_TALKING_API_KEY,
            username=settings.AFRICAS_TALKING_USERNAME,
        )
        
        response = await client.send_sms(
            phone_number=request.phone_number,
            message=request.message,
        )
        
        if response.success:
            return APIResponse.success(
                data={
                    "success": True,
                    "message_id": response.message_id,
                    "status": response.status,
                    "message": f"Test SMS sent to {request.phone_number}",
                },
                message="Test SMS sent successfully",
                status_code=200,
            )
        else:
            return APIResponse.error(
                error=response.error,
                message="Test SMS failed",
                status_code=400,
            )
    
    except Exception as e:
        logger.error(f"Error sending test SMS: {e}")
        return APIResponse.error(
            error=str(e),
            message="Failed to send test SMS",
            status_code=500,
        )


@router.post("/health/check-provider", response_model=APIResponse)
async def check_provider_health() -> APIResponse:
    """Check SMS provider health and configuration."""
    try:
        from src.core.config import settings
        
        # Check if credentials are configured
        if not settings.AFRICAS_TALKING_API_KEY:
            return APIResponse.error(
                error="Missing API key",
                message="Africa's Talking API key not configured",
                status_code=503,
            )
        
        logger.info("SMS provider is configured and ready")
        
        return APIResponse.success(
            data={
                "provider": "Africa's Talking",
                "status": "READY",
                "message": "SMS provider is configured and ready for use",
            },
            message="Provider health check passed",
            status_code=200,
        )
    
    except Exception as e:
        logger.error(f"Provider health check failed: {e}")
        return APIResponse.error(
            error=str(e),
            message="Provider health check failed",
            status_code=500,
        )
