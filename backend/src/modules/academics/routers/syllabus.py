from fastapi import APIRouter, Depends, HTTPException, Request
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, and_, delete
import uuid
from datetime import datetime

from src.core.database import get_db
from src.shared.response import APIResponse
from src.modules.academics.schemas.syllabus import CoverageToggleRequest, SyllabusProgressResponse
from src.modules.academics.models.syllabus import MasterSyllabusTopic, SyllabusCoverage
from src.modules.hr.models import Staff

router = APIRouter(tags=["Academics - Syllabus"])

@router.get("/syllabus/progress", response_model=APIResponse)
async def get_syllabus_progress(
    stream_id: uuid.UUID,
    subject_id: uuid.UUID,
    request: Request = None,
    db: AsyncSession = Depends(get_db)
):
    user = getattr(request.state, "user", None) if request else None
    school_id = user.school_id if user else uuid.UUID("00000000-0000-0000-0000-000000000000")

    # Fetch topics (mocked seeding if empty for demo purposes)
    topics_query = select(MasterSyllabusTopic).where(
        and_(MasterSyllabusTopic.school_id == school_id, MasterSyllabusTopic.subject_id == subject_id)
    ).order_by(MasterSyllabusTopic.topic_number)
    
    topics = (await db.execute(topics_query)).scalars().all()
    
    if not topics:
        # Seed mock data automatically if no topics exist (for demo compliance)
        mock_topics = [
            MasterSyllabusTopic(school_id=school_id, subject_id=subject_id, class_level="Any", topic_number=1, title="Introduction & Basic Concepts"),
            MasterSyllabusTopic(school_id=school_id, subject_id=subject_id, class_level="Any", topic_number=2, title="Core Principles & Theory"),
            MasterSyllabusTopic(school_id=school_id, subject_id=subject_id, class_level="Any", topic_number=3, title="Advanced Applications"),
            MasterSyllabusTopic(school_id=school_id, subject_id=subject_id, class_level="Any", topic_number=4, title="Practical Assessment & Revision")
        ]
        db.add_all(mock_topics)
        await db.commit()
        topics = mock_topics

    # Fetch coverage
    coverage_query = select(SyllabusCoverage).where(
        and_(SyllabusCoverage.school_id == school_id, SyllabusCoverage.stream_id == stream_id)
    )
    coverages = (await db.execute(coverage_query)).scalars().all()
    covered_topic_ids = {c.topic_id for c in coverages if c.is_completed}

    # Build response
    result_topics = []
    for t in topics:
        result_topics.append({
            "id": str(t.id),
            "topic_number": t.topic_number,
            "title": t.title,
            "is_completed": t.id in covered_topic_ids
        })
        
    completed_count = len(covered_topic_ids)
    total_count = len(topics)
    percentage = (completed_count / total_count * 100) if total_count > 0 else 0

    return APIResponse(
        status="success",
        data={
            "total_topics": total_count,
            "completed_topics": completed_count,
            "percentage": round(percentage, 1),
            "topics": result_topics
        },
        message="Syllabus progress fetched successfully."
    )

@router.post("/syllabus/coverage/toggle", response_model=APIResponse)
async def toggle_syllabus_coverage(
    payload: CoverageToggleRequest,
    request: Request = None,
    db: AsyncSession = Depends(get_db)
):
    user = getattr(request.state, "user", None) if request else None
    school_id = user.school_id if user else payload.school_id
    
    # Mock teacher for the transaction if not logged in
    staff_query = select(Staff).where(Staff.school_id == school_id)
    staff = (await db.execute(staff_query)).scalars().first()
    teacher_id = staff.id if staff else uuid.UUID("00000000-0000-0000-0000-000000000000")

    # Find existing coverage
    query = select(SyllabusCoverage).where(
        and_(
            SyllabusCoverage.school_id == school_id,
            SyllabusCoverage.stream_id == payload.stream_id,
            SyllabusCoverage.topic_id == payload.topic_id
        )
    )
    coverage = (await db.execute(query)).scalars().first()

    if coverage:
        coverage.is_completed = payload.is_completed
        coverage.completed_at = datetime.utcnow() if payload.is_completed else None
        coverage.teacher_id = teacher_id
    else:
        coverage = SyllabusCoverage(
            school_id=school_id,
            stream_id=payload.stream_id,
            topic_id=payload.topic_id,
            teacher_id=teacher_id,
            is_completed=payload.is_completed,
            completed_at=datetime.utcnow() if payload.is_completed else None
        )
        db.add(coverage)

    await db.commit()

    return APIResponse(
        status="success",
        data={"is_completed": payload.is_completed},
        message="Topic coverage updated successfully."
    )
