import uuid
from typing import List, Optional
from pydantic import BaseModel

class GenerateTimetableRequest(BaseModel):
    school_id: uuid.UUID
    term_id: uuid.UUID
    max_iterations: int = 1000

class LessonAllocationSchema(BaseModel):
    subject_id: uuid.UUID
    subject_name: str
    teacher_id: uuid.UUID
    teacher_name: str
    stream_id: uuid.UUID
    stream_name: str
    room_id: Optional[uuid.UUID]
    room_name: Optional[str]
    day_of_week: int
    period_number: int

class TimetableResponse(BaseModel):
    status: str
    message: str
    allocations: List[LessonAllocationSchema]
    total_lessons_scheduled: int
