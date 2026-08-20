import uuid
from typing import List, Optional
from pydantic import BaseModel
from datetime import datetime

class TopicSchema(BaseModel):
    id: uuid.UUID
    topic_number: int
    title: str
    description: Optional[str]

class CoverageToggleRequest(BaseModel):
    school_id: uuid.UUID
    stream_id: uuid.UUID
    subject_id: uuid.UUID
    topic_id: uuid.UUID
    is_completed: bool

class SyllabusProgressResponse(BaseModel):
    total_topics: int
    completed_topics: int
    percentage: float
    topics: List[dict]
