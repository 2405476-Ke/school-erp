"""
Communication Schemas (Pydantic v2).

Request/Response models for templates, logs, and batch operations.
"""

from datetime import datetime
from decimal import Decimal
from uuid import UUID
from typing import Optional

from pydantic import BaseModel, Field, field_validator


class CreateMessageTemplateRequest(BaseModel):
    """Create message template request."""
    
    name: str = Field(..., min_length=1, max_length=255, description="Template name")
    message_type: str = Field(..., description="SMS, EMAIL, or PUSH")
    description: Optional[str] = Field(None, max_length=1000)
    subject: Optional[str] = Field(None, max_length=500, description="For email templates")
    content: str = Field(..., min_length=10, description="Template with {{variables}}")
    
    @field_validator("message_type")
    @classmethod
    def validate_type(cls, v):
        if v not in ["SMS", "EMAIL", "PUSH"]:
            raise ValueError("message_type must be SMS, EMAIL, or PUSH")
        return v


class MessageTemplateResponse(BaseModel):
    """Message template response."""
    
    id: str
    name: str
    message_type: str
    description: Optional[str]
    subject: Optional[str]
    content: str
    is_active: bool
    created_at: datetime
    updated_at: datetime


class CommunicationLogResponse(BaseModel):
    """Communication log response."""
    
    id: str
    recipient_type: str
    recipient_contact: str
    message_type: str
    status: str
    rendered_content: str
    error_message: Optional[str]
    provider_message_id: Optional[str]
    created_at: datetime
    sent_at: Optional[datetime]
    retry_count: int


class BulkCommunicationBatchResponse(BaseModel):
    """Bulk communication batch response."""
    
    id: str
    batch_name: str
    batch_type: str
    description: Optional[str]
    triggered_by_module: str
    total_recipients: int
    total_sent: int
    total_failed: int
    total_pending: int
    created_at: datetime
    started_at: Optional[datetime]
    completed_at: Optional[datetime]


class QueueFeeRemindersRequest(BaseModel):
    """Queue fee reminder SMS for students with outstanding balance."""
    
    term_id: UUID = Field(..., description="Term/period to check fees for")
    message_template_id: Optional[UUID] = Field(None, description="Custom template ID, uses default if None")
    minimum_balance: Decimal = Field(default=Decimal("100.00"), gt=0, description="Only remind if balance > this")
    recipient_type: str = Field(default="PARENT", description="STUDENT or PARENT")


class QueueBulkCommunicationRequest(BaseModel):
    """Queue bulk communication."""
    
    template_id: UUID = Field(..., description="Message template ID")
    batch_name: str = Field(..., min_length=1, max_length=255)
    batch_type: str = Field(..., min_length=1, max_length=100)
    recipient_ids: list[UUID] = Field(..., min_items=1, max_items=10000, description="List of recipient IDs")
    recipient_type: str = Field(..., description="STUDENT, PARENT, or STAFF")
    template_variables: Optional[dict] = Field(None, description="Global variables for template rendering")


class FeeReminderContext(BaseModel):
    """Fee reminder context for template rendering."""
    
    student_name: str
    class_level: str
    fee_balance: Decimal
    due_date: str
    contact_person_name: Optional[str]


class SendTestSMSRequest(BaseModel):
    """Send test SMS to validate configuration."""
    
    phone_number: str = Field(..., regex=r"^\+?[0-9]{10,15}$", description="Phone number with or without +")
    message: str = Field(..., min_length=1, max_length=160, description="Test message")


class OptOutPreferenceRequest(BaseModel):
    """Update opt-out preference."""
    
    recipient_type: str = Field(..., description="STUDENT or PARENT")
    recipient_id: UUID
    message_type: str = Field(..., description="SMS, EMAIL, or PUSH")
    is_opted_out: bool = Field(..., description="True to opt out, False to opt in")
    reason: Optional[str] = Field(None, max_length=500)


class OptOutPreferenceResponse(BaseModel):
    """Opt-out preference response."""
    
    id: str
    recipient_type: str
    recipient_id: str
    message_type: str
    is_opted_out: bool
    opted_out_at: Optional[datetime]
    opted_in_at: Optional[datetime]


class CommunicationReportResponse(BaseModel):
    """Communication report/summary."""
    
    batch_id: str
    batch_name: str
    batch_type: str
    total_recipients: int
    total_sent: int
    total_failed: int
    total_pending: int
    success_rate: Decimal = Field(..., ge=0, le=100, decimal_places=2)
    created_at: datetime
    completed_at: Optional[datetime]
    average_delivery_time_seconds: Optional[float]
    recent_errors: list[dict] = Field(default_factory=list)
