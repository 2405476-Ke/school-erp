"""
Gate Security Schemas (Pydantic v2).

Request/Response models for visitor management and student gate events.
"""

from datetime import datetime
from uuid import UUID
from typing import Optional

from pydantic import BaseModel, Field, field_validator


class CreateVisitorRequest(BaseModel):
    """Register visitor request."""
    
    first_name: str = Field(..., min_length=1, max_length=100)
    last_name: str = Field(..., min_length=1, max_length=100)
    national_id: str = Field(..., min_length=5, max_length=50)
    phone: str = Field(..., regex=r"^\+?[0-9]{10,15}$")
    email: Optional[str] = Field(None, max_length=255)
    visitor_type: str = Field(..., description="PARENT, DELIVERY, CONTRACTOR, etc.")
    vehicle_registration: Optional[str] = Field(None, max_length=50)
    vehicle_description: Optional[str] = Field(None, max_length=255)
    purpose: str = Field(..., min_length=5, max_length=500, description="Reason for visit")
    host_staff_id: Optional[UUID] = Field(None, description="Staff person hosting visitor")
    
    @field_validator("visitor_type")
    @classmethod
    def validate_type(cls, v):
        valid_types = ["PARENT", "DELIVERY", "CONTRACTOR", "MAINTENANCE", "SALES", "VENDOR", "GUEST", "OTHER"]
        if v not in valid_types:
            raise ValueError(f"visitor_type must be one of: {', '.join(valid_types)}")
        return v


class VisitorResponse(BaseModel):
    """Visitor response."""
    
    id: str
    first_name: str
    last_name: str
    national_id: str
    phone: str
    visitor_type: str
    vehicle_registration: Optional[str]
    is_blacklisted: bool
    total_visits: int
    last_visited_at: Optional[datetime]
    created_at: datetime


class VisitorLogResponse(BaseModel):
    """Visitor log response."""
    
    id: str
    visitor_id: str
    gate_pass_number: str
    purpose: str
    check_in_time: datetime
    check_out_time: Optional[datetime]
    status: str
    security_notes: Optional[str]


class CheckOutVisitorRequest(BaseModel):
    """Check out visitor."""
    
    security_notes: Optional[str] = Field(None, max_length=500)


class ScanStudentExitRequest(BaseModel):
    """Scan student for exit."""
    
    student_id: UUID = Field(..., description="Student UUID or ID number to scan")
    guard_user_id: UUID = Field(..., description="Security guard's user ID")


class ScanStudentEntryRequest(BaseModel):
    """Scan student for entry/return."""
    
    student_id: UUID
    guard_user_id: UUID


class StudentGateEventResponse(BaseModel):
    """Student gate event response."""
    
    id: str
    student_id: str
    event_type: str  # EXIT or ENTRY
    timestamp: datetime
    is_authorized: bool
    leave_pass_id: Optional[str]
    authorization_details: Optional[str]
    alert_generated: bool
    alert_message: Optional[str]


class StudentExitClearanceResponse(BaseModel):
    """Response for student exit scan - CLEARANCE DECISION."""
    
    allowed: bool
    student_id: str
    student_name: str
    class_level: str
    event_id: str
    exeat_type: Optional[str]
    expected_return_time: Optional[datetime]
    contact_person_name: Optional[str]
    contact_person_phone: Optional[str]
    message: str


class StudentUnauthorizedExitAlert(BaseModel):
    """Alert for unauthorized exit attempt."""
    
    denied: bool = True
    student_id: str
    student_name: str
    class_level: str
    reason: str  # No leave pass, expired leave pass, wrong time, etc.
    alert_generated: bool = True
    alert_message: str
    timestamp: datetime


class StudentEntryLoggingResponse(BaseModel):
    """Response for student entry/return log."""
    
    logged: bool
    student_id: str
    student_name: str
    event_type: str  # ENTRY
    timestamp: datetime
    leave_pass_updated: bool = False
    leave_pass_status: Optional[str]  # RETURNED
    message: str


class GateSuspicionResponse(BaseModel):
    """Flagged security incident."""
    
    id: str
    student_id: Optional[str]
    visitor_id: Optional[str]
    incident_type: str
    description: str
    severity: str  # LOW, MEDIUM, HIGH, CRITICAL
    is_resolved: bool
    created_at: datetime
    resolved_at: Optional[datetime]


class GateAuditReportResponse(BaseModel):
    """Gate audit report for day/period."""
    
    period: str
    total_student_exits: int
    total_student_entries: int
    authorized_exits: int
    unauthorized_exits: int
    unauthorized_exit_rate: float  # Percentage
    total_visitor_entries: int
    visitor_check_outs: int
    total_suspicions: int
    critical_incidents: int
    report_generated_at: datetime
