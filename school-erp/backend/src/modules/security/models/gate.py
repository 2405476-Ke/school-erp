"""
Gate Security Models.

Tracks visitors and student exit/entry events with full audit trail.
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


class VisitorType(str, Enum):
    """Types of visitors to the school."""
    PARENT = "PARENT"
    DELIVERY = "DELIVERY"
    CONTRACTOR = "CONTRACTOR"
    MAINTENANCE = "MAINTENANCE"
    SALES = "SALES"
    VENDOR = "VENDOR"
    GUEST = "GUEST"
    OTHER = "OTHER"


class StudentEventType(str, Enum):
    """Student gate event types."""
    EXIT = "EXIT"
    ENTRY = "ENTRY"


class VisitorStatus(str, Enum):
    """Visitor check-in/check-out status."""
    CHECKED_IN = "CHECKED_IN"
    CHECKED_OUT = "CHECKED_OUT"
    NO_SHOW = "NO_SHOW"
    FLAGGED = "FLAGGED"


class Visitor(Base):
    """
    Visitor registration record.
    
    Tracks all non-staff, non-student visitors to school.
    """
    
    __tablename__ = "visitors"
    
    id = Column(PGUUID(as_uuid=True), primary_key=True, default=UUID)
    school_id = Column(PGUUID(as_uuid=True), nullable=False, index=True)
    
    # Visitor identification
    first_name = Column(String(100), nullable=False)
    last_name = Column(String(100), nullable=False)
    national_id = Column(String(50), nullable=False)
    phone = Column(String(20), nullable=False)
    email = Column(String(255), nullable=True)
    
    # Visitor classification
    visitor_type = Column(String(50), nullable=False)  # PARENT, DELIVERY, CONTRACTOR, etc.
    
    # Vehicle information
    vehicle_registration = Column(String(50), nullable=True)
    vehicle_description = Column(String(255), nullable=True)
    
    # Compliance
    is_blacklisted = Column(Boolean, default=False, nullable=False, index=True)
    blacklist_reason = Column(String(500), nullable=True)
    
    # Audit
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    last_visited_at = Column(DateTime, nullable=True)
    total_visits = Column(Integer, default=0, nullable=False)
    
    # Relationships
    visitor_logs = relationship(
        "VisitorLog",
        back_populates="visitor",
        cascade="all, delete-orphan",
    )
    
    # Constraints
    __table_args__ = (
        UniqueConstraint("school_id", "national_id", name="uq_visitor_school_id"),
        CheckConstraint("visitor_type IN ('PARENT', 'DELIVERY', 'CONTRACTOR', 'MAINTENANCE', 'SALES', 'VENDOR', 'GUEST', 'OTHER')", 
                       name="ck_visitor_type"),
        Index("idx_school_visitor_type", "school_id", "visitor_type"),
        Index("idx_visitor_blacklist", "is_blacklisted"),
    )


class VisitorLog(Base):
    """
    Visitor check-in/check-out log.
    
    Records each visitor's presence on campus with audit trail.
    """
    
    __tablename__ = "visitor_logs"
    
    id = Column(PGUUID(as_uuid=True), primary_key=True, default=UUID)
    school_id = Column(PGUUID(as_uuid=True), nullable=False, index=True)
    
    # Visitor reference
    visitor_id = Column(PGUUID(as_uuid=True), ForeignKey("visitors.id"), nullable=False)
    
    # Visit details
    purpose = Column(String(500), nullable=False)  # Reason for visit
    host_staff_id = Column(PGUUID(as_uuid=True), nullable=True)  # Staff person hosting visitor
    
    # Gate pass
    gate_pass_number = Column(String(50), nullable=False, index=True)  # PASS-YYYYMMDD-NNNN format
    
    # Times
    check_in_time = Column(DateTime, nullable=False, index=True)
    check_out_time = Column(DateTime, nullable=True)
    
    # Status
    status = Column(String(50), default=VisitorStatus.CHECKED_IN.value, nullable=False)
    
    # Security notes
    security_notes = Column(Text, nullable=True)
    checked_by_user_id = Column(PGUUID(as_uuid=True), nullable=True)
    
    # Audit
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    
    # Relationships
    visitor = relationship("Visitor", back_populates="visitor_logs")
    
    __table_args__ = (
        UniqueConstraint("school_id", "gate_pass_number", name="uq_gate_pass_school"),
        CheckConstraint("status IN ('CHECKED_IN', 'CHECKED_OUT', 'NO_SHOW', 'FLAGGED')", 
                       name="ck_visitor_log_status"),
        Index("idx_school_check_in", "school_id", "check_in_time"),
    )


class StudentGateEvent(Base):
    """
    Student exit/entry event log.
    
    CRITICAL: Tracks all student movements in/out of compound.
    Verifies authorization via leave pass system.
    """
    
    __tablename__ = "student_gate_events"
    
    id = Column(PGUUID(as_uuid=True), primary_key=True, default=UUID)
    school_id = Column(PGUUID(as_uuid=True), nullable=False, index=True)
    
    # Student reference
    student_id = Column(PGUUID(as_uuid=True), nullable=False)  # FK to admissions.Student
    
    # Event details
    event_type = Column(String(20), nullable=False)  # EXIT or ENTRY
    timestamp = Column(DateTime, default=datetime.utcnow, nullable=False, index=True)
    
    # Authorization
    is_authorized = Column(Boolean, nullable=False, index=True)
    leave_pass_id = Column(PGUUID(as_uuid=True), nullable=True)  # FK to boarding.LeavePass (if EXIT)
    authorization_details = Column(Text, nullable=True)
    
    # Security
    logged_by_user_id = Column(PGUUID(as_uuid=True), nullable=False)  # Guard's user ID
    alert_generated = Column(Boolean, default=False, nullable=False)
    alert_message = Column(Text, nullable=True)
    
    # Audit
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    
    __table_args__ = (
        CheckConstraint("event_type IN ('EXIT', 'ENTRY')", name="ck_event_type"),
        Index("idx_school_student_event", "school_id", "student_id", "event_type"),
        Index("idx_school_timestamp", "school_id", "timestamp"),
        Index("idx_unauthorized_events", "school_id", "is_authorized"),
    )


class GateSuspicion(Base):
    """
    Flagged security incidents at gate.
    
    Records attempted unauthorized exits, repeated late returns, etc.
    """
    
    __tablename__ = "gate_suspicions"
    
    id = Column(PGUUID(as_uuid=True), primary_key=True, default=UUID)
    school_id = Column(PGUUID(as_uuid=True), nullable=False, index=True)
    
    # Incident reference
    student_id = Column(PGUUID(as_uuid=True), nullable=True)  # If student-related
    visitor_id = Column(PGUUID(as_uuid=True), nullable=True)  # If visitor-related
    gate_event_id = Column(PGUUID(as_uuid=True), nullable=True)  # FK to StudentGateEvent
    
    # Incident details
    incident_type = Column(String(100), nullable=False)  # UNAUTHORIZED_EXIT, LATE_RETURN, BLACKLIST_MATCH, etc.
    description = Column(Text, nullable=False)
    severity = Column(String(20), default="MEDIUM", nullable=False)  # LOW, MEDIUM, HIGH, CRITICAL
    
    # Resolution
    is_resolved = Column(Boolean, default=False, nullable=False)
    resolved_at = Column(DateTime, nullable=True)
    resolution_notes = Column(Text, nullable=True)
    resolved_by_user_id = Column(PGUUID(as_uuid=True), nullable=True)
    
    # Audit
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    
    __table_args__ = (
        Index("idx_school_severity_resolved", "school_id", "severity", "is_resolved"),
        Index("idx_incident_type", "incident_type"),
    )
