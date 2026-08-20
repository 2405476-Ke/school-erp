import uuid
from sqlalchemy import Column, String, Integer, ForeignKey, Boolean
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship

from src.shared.base_model import AuditableBase, TenantMixin

class Room(AuditableBase, TenantMixin):
    __tablename__ = "rooms"
    name = Column(String(100), nullable=False)
    capacity = Column(Integer, default=40)
    is_lab = Column(Boolean, default=False)

class Timetable(AuditableBase, TenantMixin):
    __tablename__ = "timetables"
    term_id = Column(UUID(as_uuid=True), ForeignKey("terms.id"), nullable=False)
    is_active = Column(Boolean, default=True)

class LessonAllocation(AuditableBase, TenantMixin):
    __tablename__ = "lesson_allocations"
    timetable_id = Column(UUID(as_uuid=True), ForeignKey("timetables.id"), nullable=False)
    subject_id = Column(UUID(as_uuid=True), ForeignKey("subjects.id"), nullable=False)
    teacher_id = Column(UUID(as_uuid=True), ForeignKey("staff.id"), nullable=False)
    stream_id = Column(UUID(as_uuid=True), ForeignKey("streams.id"), nullable=False)
    room_id = Column(UUID(as_uuid=True), ForeignKey("rooms.id"), nullable=True)
    
    # Grid coordinates
    day_of_week = Column(Integer, nullable=False) # 1=Monday, 5=Friday
    period_number = Column(Integer, nullable=False) # 1 to 8
