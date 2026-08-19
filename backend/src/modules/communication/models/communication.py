"""
Communication Models.

Handles SMS/Email templates, communication logs, and batch tracking.
"""

from datetime import datetime
from uuid import UUID
from enum import Enum

from sqlalchemy import (
    Column,
    String,
    Text,
    DateTime,
    Boolean,
    Integer,
    ForeignKey,
    CheckConstraint,
    UniqueConstraint,
    Index,
)
from sqlalchemy.orm import relationship
from sqlalchemy.dialects.postgresql import UUID as PGUUID

from src.core.database import Base


class MessageType(str, Enum):
    """Message type enum."""
    SMS = "SMS"
    EMAIL = "EMAIL"
    PUSH = "PUSH"


class CommunicationStatus(str, Enum):
    """Communication delivery status."""
    PENDING = "PENDING"
    SENT = "SENT"
    FAILED = "FAILED"
    DELIVERED = "DELIVERED"
    BOUNCED = "BOUNCED"


class MessageTemplate(Base):
    """
    Message template with dynamic variables.
    
    Supports SMS, Email, and Push notifications.
    Template variables: {{student_name}}, {{fee_balance}}, {{due_date}}, etc.
    """
    
    __tablename__ = "message_templates"
    
    id = Column(PGUUID(as_uuid=True), primary_key=True, default=UUID)
    school_id = Column(PGUUID(as_uuid=True), nullable=False, index=True)
    
    # Template metadata
    name = Column(String(255), nullable=False)
    message_type = Column(String(20), nullable=False)  # SMS, EMAIL, PUSH
    description = Column(Text, nullable=True)
    
    # Template content
    subject = Column(String(500), nullable=True)  # For email
    content = Column(Text, nullable=False)  # Template with {{variables}}
    
    # Status and audit
    is_active = Column(Boolean, default=True, nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)
    
    # Relationships
    communication_logs = relationship(
        "CommunicationLog",
        back_populates="template",
        cascade="all, delete-orphan",
    )
    
    # Constraints
    __table_args__ = (
        UniqueConstraint("school_id", "name", name="uq_template_school_name"),
        CheckConstraint("message_type IN ('SMS', 'EMAIL', 'PUSH')", name="ck_message_type"),
    )


class CommunicationLog(Base):
    """
    Log of all communication attempts.
    
    Tracks SMS/Email/Push delivery status and errors.
    """
    
    __tablename__ = "communication_logs"
    
    id = Column(PGUUID(as_uuid=True), primary_key=True, default=UUID)
    school_id = Column(PGUUID(as_uuid=True), nullable=False, index=True)
    
    # Template reference
    template_id = Column(PGUUID(as_uuid=True), ForeignKey("message_templates.id"), nullable=False)
    
    # Batch reference
    batch_id = Column(PGUUID(as_uuid=True), ForeignKey("bulk_communication_batches.id"), nullable=True)
    
    # Recipient info
    recipient_type = Column(String(50), nullable=False)  # STUDENT, PARENT, STAFF
    recipient_id = Column(PGUUID(as_uuid=True), nullable=True)  # ID of recipient
    recipient_contact = Column(String(255), nullable=False)  # Phone or email
    
    # Message content
    message_type = Column(String(20), nullable=False)  # SMS, EMAIL, PUSH
    rendered_content = Column(Text, nullable=False)  # Actual message sent
    
    # Delivery status
    status = Column(String(50), nullable=False, index=True)  # PENDING, SENT, FAILED, DELIVERED
    error_message = Column(Text, nullable=True)  # If FAILED
    
    # Provider response
    provider_message_id = Column(String(255), nullable=True)  # ID from SMS provider
    provider_response = Column(Text, nullable=True)  # Full response JSON
    
    # Audit
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False, index=True)
    sent_at = Column(DateTime, nullable=True)
    retry_count = Column(Integer, default=0, nullable=False)
    max_retries = Column(Integer, default=3, nullable=False)
    
    # Relationships
    template = relationship("MessageTemplate", back_populates="communication_logs")
    batch = relationship("BulkCommunicationBatch", back_populates="logs")
    
    # Constraints
    __table_args__ = (
        CheckConstraint("message_type IN ('SMS', 'EMAIL', 'PUSH')", name="ck_log_message_type"),
        CheckConstraint("status IN ('PENDING', 'SENT', 'FAILED', 'DELIVERED', 'BOUNCED')", name="ck_log_status"),
        Index("idx_school_status_created", "school_id", "status", "created_at"),
        Index("idx_recipient_type_id", "recipient_type", "recipient_id"),
    )


class BulkCommunicationBatch(Base):
    """
    Tracks a mass communication event.
    
    Used to group related SMS/Email sends for reporting and retry management.
    """
    
    __tablename__ = "bulk_communication_batches"
    
    id = Column(PGUUID(as_uuid=True), primary_key=True, default=UUID)
    school_id = Column(PGUUID(as_uuid=True), nullable=False, index=True)
    
    # Batch metadata
    batch_name = Column(String(255), nullable=False)
    batch_type = Column(String(100), nullable=False)  # FEE_REMINDER, EXAM_ALERT, HOLIDAY_NOTICE, etc.
    description = Column(Text, nullable=True)
    
    # Trigger context
    triggered_by_module = Column(String(100), nullable=False)  # FINANCE, ADMISSIONS, ACADEMICS, etc.
    triggered_by_staff_id = Column(PGUUID(as_uuid=True), nullable=True)
    trigger_context = Column(String(500), nullable=True)  # e.g., "term_id=UUID", "class_level_id=UUID"
    
    # Status tracking
    total_recipients = Column(Integer, default=0, nullable=False)
    total_sent = Column(Integer, default=0, nullable=False)
    total_failed = Column(Integer, default=0, nullable=False)
    total_pending = Column(Integer, default=0, nullable=False)
    
    # Timing
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    started_at = Column(DateTime, nullable=True)
    completed_at = Column(DateTime, nullable=True)
    
    # Relationships
    logs = relationship(
        "CommunicationLog",
        back_populates="batch",
        cascade="all, delete-orphan",
    )
    
    __table_args__ = (
        Index("idx_school_batch_type", "school_id", "batch_type"),
        Index("idx_batch_created_at", "created_at"),
    )


class OptOutPreference(Base):
    """
    Tracks opt-out preferences for communication.
    
    Allows students/parents to opt out of certain message types.
    """
    
    __tablename__ = "opt_out_preferences"
    
    id = Column(PGUUID(as_uuid=True), primary_key=True, default=UUID)
    school_id = Column(PGUUID(as_uuid=True), nullable=False, index=True)
    
    # Recipient
    recipient_type = Column(String(50), nullable=False)  # STUDENT, PARENT
    recipient_id = Column(PGUUID(as_uuid=True), nullable=False)
    
    # Opt-out preference
    message_type = Column(String(20), nullable=False)  # SMS, EMAIL, PUSH
    is_opted_out = Column(Boolean, default=False, nullable=False)
    
    # Reason and audit
    reason = Column(String(500), nullable=True)
    opted_out_at = Column(DateTime, nullable=True)
    opted_in_at = Column(DateTime, nullable=True)
    
    __table_args__ = (
        UniqueConstraint("school_id", "recipient_type", "recipient_id", "message_type", 
                        name="uq_optout_preference"),
    )
