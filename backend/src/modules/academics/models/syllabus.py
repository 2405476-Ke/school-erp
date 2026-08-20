import uuid
from sqlalchemy import Column, String, Integer, ForeignKey, Boolean, DateTime
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship
from datetime import datetime

from src.shared.base_model import AuditableBase, TenantMixin

class MasterSyllabusTopic(AuditableBase, TenantMixin):
    __tablename__ = "master_syllabus_topics"
    subject_id = Column(UUID(as_uuid=True), ForeignKey("subjects.id"), nullable=False)
    class_level = Column(String(50), nullable=False) # e.g. "Form 1"
    topic_number = Column(Integer, nullable=False)
    title = Column(String(255), nullable=False)
    description = Column(String, nullable=True)

class SyllabusCoverage(AuditableBase, TenantMixin):
    __tablename__ = "syllabus_coverage"
    topic_id = Column(UUID(as_uuid=True), ForeignKey("master_syllabus_topics.id"), nullable=False)
    stream_id = Column(UUID(as_uuid=True), ForeignKey("streams.id"), nullable=False)
    teacher_id = Column(UUID(as_uuid=True), ForeignKey("staff.id"), nullable=False)
    is_completed = Column(Boolean, default=False)
    completed_at = Column(DateTime, nullable=True)
