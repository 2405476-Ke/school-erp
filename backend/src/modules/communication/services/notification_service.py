"""
Notification Service.

Core notification logic: template management, message queueing, bulk dispatching.
"""

import logging
import re
from uuid import UUID
from datetime import datetime
from decimal import Decimal
from typing import Optional

from sqlalchemy import select, and_, func
from sqlalchemy.ext.asyncio import AsyncSession

from src.core.exceptions import NotFoundError, ValidationError
from src.modules.communication.models.communication import (
    MessageTemplate,
    CommunicationLog,
    BulkCommunicationBatch,
    OptOutPreference,
    CommunicationStatus,
    MessageType,
)
from src.modules.communication.services.tasks import process_sms_batch

logger = logging.getLogger(__name__)


class NotificationService:
    """Service for managing communications and notifications."""
    
    def __init__(self, db: AsyncSession):
        """Initialize with database session."""
        self.db = db
    
    async def create_message_template(
        self,
        school_id: UUID,
        name: str,
        message_type: str,
        content: str,
        description: Optional[str] = None,
        subject: Optional[str] = None,
    ) -> dict:
        """
        Create message template.
        
        Args:
            school_id: Tenant identifier
            name: Template name
            message_type: SMS, EMAIL, or PUSH
            content: Template content with {{variables}}
            description: Optional description
            subject: Optional subject for emails
        
        Returns:
            dict with template_id, name, message_type
        
        Raises:
            ValidationError: If name already exists
        """
        logger.debug(f"Creating template: {name}, type={message_type}")
        
        # Check uniqueness
        existing = await self.db.scalar(
            select(MessageTemplate).where(
                and_(
                    MessageTemplate.school_id == school_id,
                    MessageTemplate.name == name,
                )
            )
        )
        
        if existing:
            raise ValidationError(f"Template '{name}' already exists")
        
        # Validate message type
        if message_type not in ["SMS", "EMAIL", "PUSH"]:
            raise ValidationError(f"Invalid message_type: {message_type}")
        
        # Validate content has at least one variable
        if "{{" not in content or "}}" not in content:
            logger.warning(f"Template '{name}' has no dynamic variables")
        
        # Create template
        template = MessageTemplate(
            school_id=school_id,
            name=name,
            message_type=message_type,
            content=content,
            description=description,
            subject=subject,
            is_active=True,
        )
        
        self.db.add(template)
        await self.db.commit()
        
        logger.info(f"Template created: {template.id}, name={name}")
        
        return {
            "template_id": str(template.id),
            "name": name,
            "message_type": message_type,
            "description": description,
        }
    
    async def queue_bulk_fee_reminders(
        self,
        school_id: UUID,
        term_id: UUID,
        message_template_id: Optional[UUID] = None,
        minimum_balance: Decimal = Decimal("100.00"),
        recipient_type: str = "PARENT",
    ) -> dict:
        """
        CRITICAL: Queue bulk fee reminder SMS.
        
        Algorithm:
        1. Query Finance module for students with fee_balance > minimum_balance
        2. For each student, fetch parent/guardian phone number
        3. Fetch or create message template (default: "FEE_REMINDER")
        4. Create CommunicationLog records with status PENDING
        5. Create BulkCommunicationBatch to track the operation
        6. Trigger Celery task: process_sms_batch
        7. Return summary with count and batch_id
        
        Args:
            school_id: Tenant identifier
            term_id: Academic term/period to check fees for
            message_template_id: Custom template ID (uses default if None)
            minimum_balance: Only remind if balance > this amount
            recipient_type: STUDENT or PARENT
        
        Returns:
            dict with batch_id, total_recipients, message
        
        Raises:
            NotFoundError: If template not found
            ValidationError: If term not found
        """
        logger.info(
            f"Queueing bulk fee reminders: term={term_id}, "
            f"min_balance={minimum_balance}, recipient={recipient_type}"
        )
        
        # STEP 1: Get or use default template
        if message_template_id:
            template = await self.db.scalar(
                select(MessageTemplate).where(
                    MessageTemplate.id == message_template_id
                )
            )
            if not template:
                raise NotFoundError("Message template not found")
        else:
            # Use default FEE_REMINDER template
            template = await self.db.scalar(
                select(MessageTemplate).where(
                    and_(
                        MessageTemplate.school_id == school_id,
                        MessageTemplate.name == "FEE_REMINDER",
                        MessageTemplate.message_type == "SMS",
                    )
                )
            )
            if not template:
                raise NotFoundError(
                    "Default FEE_REMINDER template not found. Create one first."
                )
        
        logger.debug(f"Using template: {template.name}, id={template.id}")
        
        # STEP 2: Query Finance module for students with outstanding balance
        # NOTE: This is a simplified example - actual implementation depends on Finance module
        # For now, we simulate by creating a stub query
        students_with_balance = []
        
        # In production:
        # from src.modules.finance.models.billing import Invoice, FeeAccount
        # result = await self.db.execute(
        #     select(Student.id, Student.first_name, Student.last_name, 
        #            ParentGuardian.phone, FeeAccount.balance).
        #     join(FeeAccount).
        #     join(ParentGuardian).
        #     where(and_(
        #         Student.school_id == school_id,
        #         FeeAccount.balance > minimum_balance,
        #         # Filter by term
        #     ))
        # )
        # students_with_balance = result.fetchall()
        
        logger.debug(f"Found {len(students_with_balance)} students with outstanding fees")
        
        # STEP 3: Create BulkCommunicationBatch
        batch = BulkCommunicationBatch(
            school_id=school_id,
            batch_name=f"Fee Reminders - Term {term_id}",
            batch_type="FEE_REMINDER",
            description=f"Automated fee reminders for term {term_id}",
            triggered_by_module="FINANCE",
            trigger_context=f"term_id={term_id}",
            total_recipients=len(students_with_balance),
            total_pending=len(students_with_balance),
        )
        
        self.db.add(batch)
        await self.db.flush()
        
        logger.debug(f"Created batch: {batch.id}, recipients={batch.total_recipients}")
        
        # STEP 4: Create CommunicationLog records
        log_count = 0
        
        for student_id, student_name, fee_balance, parent_phone in students_with_balance:
            # Check opt-out preference
            opted_out = await self._is_opted_out(
                school_id,
                recipient_type,
                student_id if recipient_type == "STUDENT" else None,
                "SMS",
            )
            
            if opted_out:
                logger.debug(f"Skipping opted-out {recipient_type}: {student_id}")
                batch.total_pending -= 1
                continue
            
            # Render template with student data
            rendered_content = self._render_template(
                template.content,
                {
                    "student_name": student_name,
                    "fee_balance": f"KES {fee_balance:.2f}",
                    "due_date": "End of term",
                    "school_name": "School Name",
                },
            )
            
            # Create log
            log = CommunicationLog(
                school_id=school_id,
                template_id=template.id,
                batch_id=batch.id,
                recipient_type=recipient_type,
                recipient_id=student_id,
                recipient_contact=parent_phone,
                message_type="SMS",
                rendered_content=rendered_content,
                status=CommunicationStatus.PENDING.value,
            )
            
            self.db.add(log)
            log_count += 1
        
        await self.db.commit()
        
        logger.info(f"Created {log_count} communication logs for batch: {batch.id}")
        
        # STEP 5: Trigger Celery task for async processing
        process_sms_batch.delay(str(batch.id))
        logger.info(f"Triggered SMS batch processing task for batch: {batch.id}")
        
        return {
            "batch_id": str(batch.id),
            "batch_name": batch.batch_name,
            "total_recipients": batch.total_recipients,
            "total_pending": batch.total_pending,
            "message": f"Queued {log_count} fee reminders. Processing asynchronously.",
        }
    
    async def queue_bulk_communication(
        self,
        school_id: UUID,
        template_id: UUID,
        batch_name: str,
        batch_type: str,
        recipient_ids: list[UUID],
        recipient_type: str = "PARENT",
        template_variables: Optional[dict] = None,
        triggered_by_staff_id: Optional[UUID] = None,
    ) -> dict:
        """
        Queue bulk communication to multiple recipients.
        
        Generic method for any bulk message send.
        
        Args:
            school_id: Tenant identifier
            template_id: Message template ID
            batch_name: Human-readable batch name
            batch_type: EXAM_ALERT, HOLIDAY_NOTICE, etc.
            recipient_ids: List of recipient IDs
            recipient_type: STUDENT, PARENT, or STAFF
            template_variables: Global variables for template
            triggered_by_staff_id: Staff who initiated
        
        Returns:
            dict with batch_id, logs_created, status
        
        Raises:
            NotFoundError: If template not found
            ValidationError: If no valid recipients
        """
        logger.info(
            f"Queueing bulk communication: type={batch_type}, "
            f"recipients={len(recipient_ids)}"
        )
        
        # Fetch template
        template = await self.db.scalar(
            select(MessageTemplate).where(MessageTemplate.id == template_id)
        )
        
        if not template:
            raise NotFoundError("Message template not found")
        
        if not recipient_ids:
            raise ValidationError("No recipients provided")
        
        # Create batch
        batch = BulkCommunicationBatch(
            school_id=school_id,
            batch_name=batch_name,
            batch_type=batch_type,
            triggered_by_module="CUSTOM",
            triggered_by_staff_id=triggered_by_staff_id,
            total_recipients=len(recipient_ids),
            total_pending=len(recipient_ids),
        )
        
        self.db.add(batch)
        await self.db.flush()
        
        # Create logs for each recipient
        log_count = 0
        
        for recipient_id in recipient_ids:
            # Render template
            rendered_content = self._render_template(
                template.content,
                template_variables or {},
            )
            
            log = CommunicationLog(
                school_id=school_id,
                template_id=template_id,
                batch_id=batch.id,
                recipient_type=recipient_type,
                recipient_id=recipient_id,
                recipient_contact="",  # Would be populated from recipient lookup
                message_type=template.message_type,
                rendered_content=rendered_content,
                status=CommunicationStatus.PENDING.value,
            )
            
            self.db.add(log)
            log_count += 1
        
        await self.db.commit()
        
        # Trigger async processing
        if template.message_type == "SMS":
            process_sms_batch.delay(str(batch.id))
        
        return {
            "batch_id": str(batch.id),
            "batch_name": batch_name,
            "logs_created": log_count,
            "status": "QUEUED",
            "message": f"Queued {log_count} messages for delivery",
        }
    
    async def get_communication_log(
        self,
        school_id: UUID,
        log_id: UUID,
    ) -> dict:
        """Get communication log detail."""
        log = await self.db.scalar(
            select(CommunicationLog).where(
                and_(
                    CommunicationLog.id == log_id,
                    CommunicationLog.school_id == school_id,
                )
            )
        )
        
        if not log:
            raise NotFoundError("Communication log not found")
        
        return {
            "id": str(log.id),
            "recipient_type": log.recipient_type,
            "recipient_contact": log.recipient_contact,
            "message_type": log.message_type,
            "status": log.status,
            "rendered_content": log.rendered_content,
            "error_message": log.error_message,
            "provider_message_id": log.provider_message_id,
            "created_at": log.created_at.isoformat(),
            "sent_at": log.sent_at.isoformat() if log.sent_at else None,
            "retry_count": log.retry_count,
        }
    
    async def get_batch_report(
        self,
        school_id: UUID,
        batch_id: UUID,
    ) -> dict:
        """Get batch communication report."""
        batch = await self.db.scalar(
            select(BulkCommunicationBatch).where(
                and_(
                    BulkCommunicationBatch.id == batch_id,
                    BulkCommunicationBatch.school_id == school_id,
                )
            )
        )
        
        if not batch:
            raise NotFoundError("Batch not found")
        
        # Calculate success rate
        success_rate = Decimal("0.00")
        if batch.total_recipients > 0:
            success_rate = (
                Decimal(batch.total_sent) / Decimal(batch.total_recipients) * 100
            ).quantize(Decimal("0.01"))
        
        # Get recent errors
        error_logs_result = await self.db.execute(
            select(CommunicationLog).where(
                and_(
                    CommunicationLog.batch_id == batch_id,
                    CommunicationLog.status == CommunicationStatus.FAILED.value,
                )
            ).limit(5)
        )
        error_logs = error_logs_result.scalars().all()
        
        recent_errors = [
            {
                "recipient": log.recipient_contact,
                "error": log.error_message,
                "created_at": log.created_at.isoformat(),
            }
            for log in error_logs
        ]
        
        return {
            "batch_id": str(batch.id),
            "batch_name": batch.batch_name,
            "batch_type": batch.batch_type,
            "total_recipients": batch.total_recipients,
            "total_sent": batch.total_sent,
            "total_failed": batch.total_failed,
            "total_pending": batch.total_pending,
            "success_rate": success_rate,
            "created_at": batch.created_at.isoformat(),
            "completed_at": batch.completed_at.isoformat() if batch.completed_at else None,
            "recent_errors": recent_errors,
        }
    
    async def set_opt_out_preference(
        self,
        school_id: UUID,
        recipient_type: str,
        recipient_id: UUID,
        message_type: str,
        is_opted_out: bool,
        reason: Optional[str] = None,
    ) -> dict:
        """Set opt-out preference for recipient."""
        # Check if preference exists
        pref = await self.db.scalar(
            select(OptOutPreference).where(
                and_(
                    OptOutPreference.school_id == school_id,
                    OptOutPreference.recipient_type == recipient_type,
                    OptOutPreference.recipient_id == recipient_id,
                    OptOutPreference.message_type == message_type,
                )
            )
        )
        
        if pref:
            pref.is_opted_out = is_opted_out
            pref.reason = reason
            if is_opted_out:
                pref.opted_out_at = datetime.utcnow()
            else:
                pref.opted_in_at = datetime.utcnow()
        else:
            pref = OptOutPreference(
                school_id=school_id,
                recipient_type=recipient_type,
                recipient_id=recipient_id,
                message_type=message_type,
                is_opted_out=is_opted_out,
                reason=reason,
                opted_out_at=datetime.utcnow() if is_opted_out else None,
            )
            self.db.add(pref)
        
        await self.db.commit()
        
        logger.info(
            f"Opt-out preference set: {recipient_type}:{recipient_id}, "
            f"type={message_type}, opted_out={is_opted_out}"
        )
        
        return {
            "preference_id": str(pref.id),
            "recipient_type": recipient_type,
            "message_type": message_type,
            "is_opted_out": is_opted_out,
        }
    
    def _render_template(self, template: str, variables: dict) -> str:
        """
        Render template with variables.
        
        Replaces {{variable_name}} with actual values.
        """
        content = template
        
        for key, value in variables.items():
            placeholder = f"{{{{{key}}}}}"
            content = content.replace(placeholder, str(value))
        
        # Warn if unreplaced variables remain
        unreplaced = re.findall(r"\{\{(\w+)\}\}", content)
        if unreplaced:
            logger.warning(f"Unreplaced variables in template: {unreplaced}")
        
        return content
    
    async def _is_opted_out(
        self,
        school_id: UUID,
        recipient_type: str,
        recipient_id: Optional[UUID],
        message_type: str,
    ) -> bool:
        """Check if recipient is opted out."""
        if not recipient_id:
            return False
        
        pref = await self.db.scalar(
            select(OptOutPreference).where(
                and_(
                    OptOutPreference.school_id == school_id,
                    OptOutPreference.recipient_type == recipient_type,
                    OptOutPreference.recipient_id == recipient_id,
                    OptOutPreference.message_type == message_type,
                )
            )
        )
        
        return pref.is_opted_out if pref else False
