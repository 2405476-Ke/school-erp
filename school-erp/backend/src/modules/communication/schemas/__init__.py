"""
Communication schemas.
"""

from src.modules.communication.schemas.communication import (
    CreateMessageTemplateRequest,
    MessageTemplateResponse,
    CommunicationLogResponse,
    BulkCommunicationBatchResponse,
    QueueFeeRemindersRequest,
    QueueBulkCommunicationRequest,
    OptOutPreferenceRequest,
    OptOutPreferenceResponse,
)

__all__ = [
    "CreateMessageTemplateRequest",
    "MessageTemplateResponse",
    "CommunicationLogResponse",
    "BulkCommunicationBatchResponse",
    "QueueFeeRemindersRequest",
    "QueueBulkCommunicationRequest",
    "OptOutPreferenceRequest",
    "OptOutPreferenceResponse",
]
