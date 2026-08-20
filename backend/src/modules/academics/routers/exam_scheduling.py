from fastapi import APIRouter, Depends, HTTPException, Request
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, and_, delete
import uuid
from datetime import datetime
from pydantic import BaseModel
from typing import List, Optional

from src.core.database import get_db
from src.shared.response import APIResponse
from src.modules.academics.models.exams_844 import ExamSchedule, Exam
from src.modules.academics.models.core import Subject
from src.modules.hr.models import Staff

router = APIRouter(tags=["Academics - Exam Scheduling"])

class ExamScheduleItem(BaseModel):
    subject_id: uuid.UUID
    class_level: str
    start_time: datetime
    end_time: datetime
    invigilator_id: Optional[uuid.UUID] = None
    room_id: Optional[uuid.UUID] = None

class ExamSchedulePayload(BaseModel):
    exam_id: uuid.UUID
    school_id: uuid.UUID
    schedules: List[ExamScheduleItem]

@router.get("/exams/{exam_id}/schedule", response_model=APIResponse)
async def get_exam_schedule(
    exam_id: uuid.UUID,
    request: Request = None,
    db: AsyncSession = Depends(get_db)
):
    user = getattr(request.state, "user", None) if request else None
    school_id = user.school_id if user else uuid.UUID("00000000-0000-0000-0000-000000000000")

    query = select(ExamSchedule).where(
        and_(ExamSchedule.school_id == school_id, ExamSchedule.exam_id == exam_id)
    )
    schedules = (await db.execute(query)).scalars().all()

    # Pre-fetch subject and staff names for UI
    subjects_q = select(Subject).where(Subject.school_id == school_id)
    staff_q = select(Staff).where(Staff.school_id == school_id)
    
    subjects = (await db.execute(subjects_q)).scalars().all()
    staffs = (await db.execute(staff_q)).scalars().all()
    
    sub_map = {s.id: s.name for s in subjects}
    staff_map = {s.id: f"{s.first_name} {s.last_name}" for s in staffs}

    data = []
    for s in schedules:
        data.append({
            "id": str(s.id),
            "subject_id": str(s.subject_id),
            "subject_name": sub_map.get(s.subject_id, "Unknown Subject"),
            "class_level": s.class_level,
            "start_time": s.start_time.isoformat(),
            "end_time": s.end_time.isoformat(),
            "invigilator_id": str(s.invigilator_id) if s.invigilator_id else None,
            "invigilator_name": staff_map.get(s.invigilator_id, "Unassigned") if s.invigilator_id else "Unassigned",
            "room_id": str(s.room_id) if s.room_id else None
        })

    return APIResponse(
        status="success",
        data=data,
        message="Exam schedule fetched successfully."
    )

@router.post("/exams/schedule", response_model=APIResponse)
async def save_exam_schedule(
    payload: ExamSchedulePayload,
    request: Request = None,
    db: AsyncSession = Depends(get_db)
):
    user = getattr(request.state, "user", None) if request else None
    school_id = user.school_id if user else payload.school_id

    # Validate exam exists
    exam = (await db.execute(select(Exam).where(Exam.id == payload.exam_id))).scalars().first()
    if not exam:
        raise HTTPException(status_code=404, detail="Exam sitting not found.")

    # Drop existing schedule for this exam
    await db.execute(delete(ExamSchedule).where(ExamSchedule.exam_id == payload.exam_id))

    new_schedules = []
    for item in payload.schedules:
        new_schedules.append(
            ExamSchedule(
                school_id=school_id,
                exam_id=payload.exam_id,
                subject_id=item.subject_id,
                class_level=item.class_level,
                start_time=item.start_time,
                end_time=item.end_time,
                invigilator_id=item.invigilator_id,
                room_id=item.room_id
            )
        )
    
    if new_schedules:
        db.add_all(new_schedules)
    
    await db.commit()

    return APIResponse(
        status="success",
        data={"scheduled_items": len(new_schedules)},
        message="Exam schedule saved successfully."
    )
