"""
Communication & Notifications module.

Handles SMS, Email, and Push notifications with async Celery task processing.
"""

from src.modules.communication.models import (
    MessageTemplate,
    CommunicationLog,
    BulkCommunicationBatch,
    OptOutPreference,
)
from src.modules.communication.services import NotificationService, tasks
from src.modules.communication.routers import communication_router
from src.modules.communication.integrations import (
    AfricasTalkingClient,
    EmailProvider,
    PushNotificationProvider,
)

__all__ = [
    "MessageTemplate",
    "CommunicationLog",
    "BulkCommunicationBatch",
    "OptOutPreference",
    "NotificationService",
    "tasks",
    "communication_router",
    "AfricasTalkingClient",
    "EmailProvider",
    "PushNotificationProvider",
]
