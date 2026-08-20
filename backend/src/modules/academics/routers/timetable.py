from fastapi import APIRouter, Depends, HTTPException, status, Request
from sqlalchemy.ext.asyncio import AsyncSession
from typing import Any
import uuid

from src.core.database import get_db
from src.shared.response import APIResponse
from src.modules.academics.schemas.timetable import GenerateTimetableRequest, TimetableResponse
from src.modules.academics.services.timetable_service import TimetableGeneratorService

router = APIRouter(tags=["Academics - Timetable"])

@router.post("/timetable/generate", response_model=APIResponse)
async def generate_timetable_endpoint(
    payload: GenerateTimetableRequest,
    request: Request = None,
    db: AsyncSession = Depends(get_db)
):
    """
    Auto-generate a clash-free timetable for the given term.
    Resolves Teacher, Stream, and Subject conflicts automatically.
    """
    user = getattr(request.state, "user", None) if request else None
    school_id = user.school_id if user else payload.school_id

    service = TimetableGeneratorService(db)
    try:
        allocations = await service.generate_timetable(school_id=school_id, term_id=payload.term_id)
        return APIResponse(
            status="success",
            data={"total_allocations": len(allocations)},
            message="Successfully generated a 100% clash-free timetable."
        )
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

@router.get("/timetable/stream/{stream_id}", response_model=APIResponse)
async def get_stream_timetable_endpoint(
    stream_id: uuid.UUID,
    request: Request = None,
    db: AsyncSession = Depends(get_db)
):
    user = getattr(request.state, "user", None) if request else None
    school_id = user.school_id if user else uuid.UUID("00000000-0000-0000-0000-000000000000")

    service = TimetableGeneratorService(db)
    allocations = await service.get_stream_timetable(school_id=school_id, stream_id=stream_id)
    
    # Format for visual grid
    # Fetch subject names to send to frontend
    from sqlalchemy import select
    from src.modules.academics.models.core import Subject
    subjects_query = select(Subject).where(Subject.school_id == school_id)
    subjects = (await db.execute(subjects_query)).scalars().all()
    sub_map = {str(s.id): s.name for s in subjects}

    grid = []
    for a in allocations:
        grid.append({
            "day": a.day_of_week,
            "period": a.period_number,
            "subject_id": str(a.subject_id),
            "subject_name": sub_map.get(str(a.subject_id), "Unknown"),
            "teacher_id": str(a.teacher_id),
        })
        
    return APIResponse(
        status="success",
        data={"grid": grid},
        message="Timetable retrieved successfully"
    )

from src.modules.academics.schemas.timetable import ManualTimetableRequest

@router.post("/timetable/manual-save", response_model=APIResponse)
async def save_manual_timetable_endpoint(
    payload: ManualTimetableRequest,
    request: Request = None,
    db: AsyncSession = Depends(get_db)
):
    """
    Save a manually created timetable layout for a specific stream.
    Supports dynamic mapping of department/teacher rules.
    """
    user = getattr(request.state, "user", None) if request else None
    school_id = user.school_id if user else payload.school_id

    service = TimetableGeneratorService(db)
    
    # Convert Pydantic schemas to dictionaries for the service
    allocs = [{"day_of_week": a.day_of_week, "period_number": a.period_number, "subject_name": a.subject_name} for a in payload.allocations]
    
    try:
        saved = await service.save_manual_timetable(
            school_id=school_id, 
            term_id=payload.term_id, 
            stream_id=payload.stream_id, 
            allocations=allocs
        )
        return APIResponse(
            status="success",
            data={"saved_allocations": len(saved)},
            message="Timetable manually saved successfully."
        )
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))
