"""
FastAPI routers for Discipline Management.

Endpoints for:
- Reporting disciplinary incidents
- Issuing disciplinary actions
- Tracking student discipline records
"""

import logging
from uuid import UUID
from datetime import date

from fastapi import APIRouter, Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession

from src.core.database import get_db
from src.core.exceptions import NotFoundError, ValidationError
from src.core.response import APIResponse
from src.modules.boarding.schemas.boarding import (
    ReportDisciplinaryIncidentRequest,
    DisciplinaryIncidentResponse,
    DisciplinaryIncidentDetailResponse,
    IssueDisciplinaryActionRequest,
    IssueDisciplinaryActionResponse,
    DisciplinaryActionResponse,
    StudentDisciplinaryRecordResponse,
)
from src.modules.boarding.services.discipline_service import DisciplinaryService

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/discipline", tags=["Discipline Management"])


@router.post("/incidents", response_model=APIResponse)
async def report_incident(
    request: ReportDisciplinaryIncidentRequest,
    db: AsyncSession = Depends(get_db),
    school_id: UUID = Depends(lambda: UUID("00000000-0000-0000-0000-000000000000")),
    reported_by_user_id: UUID = Depends(lambda: UUID("00000000-0000-0000-0000-000000000000")),
) -> APIResponse:
    """
    Report disciplinary incident.
    
    Categories:
    - ACADEMIC: Late assignments, poor performance
    - CONDUCT: Disrespect, rudeness, insubordination
    - CURFEW: Breaking curfew, night violations
    - SUBSTANCE: Drugs, alcohol, vaping
    - SAFETY: Fighting, weapons, threats
    - PROPERTY: Theft, vandalism, damage
    - UNIFORM: Uniform code violations
    - OTHER: Other infractions
    
    Severity: 1-5 (1=minor, 5=critical)
    """
    try:
        # Convert reported_by to staff_id (would normally come from auth context)
        service = DisciplinaryService(db)
        result = await service.report_incident(
            school_id=school_id,
            student_id=request.student_id,
            category=request.category,
            description=request.description,
            incident_date=request.incident_date,
            location=request.location,
            witnesses=request.witnesses,
            severity=request.severity,
            reported_by_staff_id=None,  # Would come from auth context in production
        )
        
        return APIResponse.success(
            data=result,
            message="Incident reported successfully",
            status_code=201,
        )
    
    except NotFoundError as e:
        return APIResponse.error(
            error=str(e),
            message="Student not found",
            status_code=404,
        )
    
    except ValidationError as e:
        return APIResponse.error(
            error=str(e),
            message="Report validation failed",
            status_code=400,
        )
    
    except Exception as e:
        logger.error(f"Error reporting incident: {e}")
        return APIResponse.error(
            error=str(e),
            message="Failed to report incident",
            status_code=500,
        )


@router.get("/incidents/{incident_id}", response_model=APIResponse)
async def get_incident(
    incident_id: UUID,
    db: AsyncSession = Depends(get_db),
    school_id: UUID = Depends(lambda: UUID("00000000-0000-0000-0000-000000000000")),
) -> APIResponse:
    """Get incident details with all associated actions."""
    try:
        service = DisciplinaryService(db)
        incident = await service.get_incident(school_id, incident_id)
        
        actions = [
            DisciplinaryActionResponse(
                id=action.id,
                incident_id=action.incident_id,
                action_type=action.action_type.value,
                description=action.description,
                start_date=action.start_date,
                end_date=action.end_date,
                issued_date=action.issued_date,
                duration_days=(action.end_date - action.start_date).days + 1 if action.end_date else None,
                issued_by=None,  # Would populate from staff lookup
                reason=action.reason,
            )
            for action in incident.disciplinary_actions
        ]
        
        response = DisciplinaryIncidentDetailResponse(
            id=incident.id,
            student_id=incident.student_id,
            student_name=f"{incident.student.first_name} {incident.student.last_name}",
            student_admission_number=incident.student.admission_number,
            category=incident.category.value,
            description=incident.description,
            incident_date=incident.incident_date,
            reported_date=incident.reported_date,
            location=incident.location,
            witnesses=incident.witnesses,
            severity=incident.severity,
            reported_by=None,  # Would populate from staff lookup
            actions=actions,
        )
        
        return APIResponse.success(
            data=response,
            message="Incident retrieved",
            status_code=200,
        )
    
    except NotFoundError as e:
        return APIResponse.error(
            error=str(e),
            message="Incident not found",
            status_code=404,
        )
    
    except Exception as e:
        logger.error(f"Error retrieving incident: {e}")
        return APIResponse.error(
            error=str(e),
            message="Failed to retrieve incident",
            status_code=500,
        )


@router.get("/incidents", response_model=APIResponse)
async def list_incidents(
    db: AsyncSession = Depends(get_db),
    school_id: UUID = Depends(lambda: UUID("00000000-0000-0000-0000-000000000000")),
    student_id: UUID = Query(None, description="Filter by student"),
    category: str = Query(None, description="Filter by category"),
    severity: int = Query(None, ge=1, le=5, description="Filter by minimum severity"),
    from_date: date = Query(None, description="Filter from date"),
    to_date: date = Query(None, description="Filter to date"),
) -> APIResponse:
    """List incidents with filters."""
    try:
        service = DisciplinaryService(db)
        incidents = await service.list_incidents(
            school_id=school_id,
            student_id=student_id,
            category=category,
            severity=severity,
            from_date=from_date,
            to_date=to_date,
        )
        
        responses = [
            DisciplinaryIncidentResponse(
                id=incident.id,
                student_id=incident.student_id,
                student_name=f"{incident.student.first_name} {incident.student.last_name}",
                student_admission_number=incident.student.admission_number,
                category=incident.category.value,
                description=incident.description,
                incident_date=incident.incident_date,
                reported_date=incident.reported_date,
                location=incident.location,
                severity=incident.severity,
                reported_by=None,
                actions_count=len(incident.disciplinary_actions),
            )
            for incident in incidents
        ]
        
        return APIResponse.success(
            data=responses,
            message=f"Found {len(responses)} incidents",
            status_code=200,
        )
    
    except Exception as e:
        logger.error(f"Error listing incidents: {e}")
        return APIResponse.error(
            error=str(e),
            message="Failed to list incidents",
            status_code=500,
        )


@router.post("/actions", response_model=APIResponse)
async def issue_action(
    request: IssueDisciplinaryActionRequest,
    db: AsyncSession = Depends(get_db),
    school_id: UUID = Depends(lambda: UUID("00000000-0000-0000-0000-000000000000")),
    issued_by_user_id: UUID = Depends(lambda: UUID("00000000-0000-0000-0000-000000000000")),
) -> APIResponse:
    """
    Issue disciplinary action in response to incident.
    
    Action Types:
    - WARNING: Verbal or written warning
    - DETENTION: After-school or weekend detention
    - SUSPENSION: Temporary removal from school
    - EXPULSION: Permanent removal from school
    - COMMUNITY_SERVICE: Mandatory community work
    - FINE: Monetary penalty
    - RESTRICTION: Movement or activity restrictions
    - COUNSELING: Required counseling sessions
    """
    try:
        service = DisciplinaryService(db)
        result = await service.issue_action(
            school_id=school_id,
            incident_id=request.incident_id,
            action_type=request.action_type,
            description=request.description,
            start_date=request.start_date,
            end_date=request.end_date,
            reason=request.reason,
            issued_by_staff_id=None,  # Would come from auth context
        )
        
        response = IssueDisciplinaryActionResponse(
            action_id=result["action_id"],
            incident_id=result["incident_id"],
            student_name=result["student_name"],
            action_type=result["action_type"],
            start_date=result["start_date"],
            end_date=result["end_date"],
            message=result["message"],
        )
        
        return APIResponse.success(
            data=response,
            message="Action issued successfully",
            status_code=201,
        )
    
    except NotFoundError as e:
        return APIResponse.error(
            error=str(e),
            message="Incident not found",
            status_code=404,
        )
    
    except ValidationError as e:
        return APIResponse.error(
            error=str(e),
            message="Action validation failed",
            status_code=400,
        )
    
    except Exception as e:
        logger.error(f"Error issuing action: {e}")
        return APIResponse.error(
            error=str(e),
            message="Failed to issue action",
            status_code=500,
        )


@router.get("/students/{student_id}/record", response_model=APIResponse)
async def get_student_discipline_record(
    student_id: UUID,
    db: AsyncSession = Depends(get_db),
    school_id: UUID = Depends(lambda: UUID("00000000-0000-0000-0000-000000000000")),
) -> APIResponse:
    """
    Get complete disciplinary record for student.
    
    Includes:
    - Total incidents by category
    - Current active actions
    - Recent incident history
    """
    try:
        service = DisciplinaryService(db)
        record = await service.get_student_disciplinary_record(school_id, student_id)
        
        response = StudentDisciplinaryRecordResponse(
            student_id=record["student_id"],
            student_name=record["student_name"],
            student_admission_number=record["student_admission_number"],
            total_incidents=record["total_incidents"],
            incidents_by_category=record["incidents_by_category"],
            active_actions=record["active_actions"],
            recent_incidents=record["recent_incidents"],
        )
        
        return APIResponse.success(
            data=response,
            message="Discipline record retrieved",
            status_code=200,
        )
    
    except NotFoundError as e:
        return APIResponse.error(
            error=str(e),
            message="Student not found",
            status_code=404,
        )
    
    except Exception as e:
        logger.error(f"Error retrieving discipline record: {e}")
        return APIResponse.error(
            error=str(e),
            message="Failed to retrieve discipline record",
            status_code=500,
        )


@router.get("/statistics", response_model=APIResponse)
async def get_discipline_statistics(
    db: AsyncSession = Depends(get_db),
    school_id: UUID = Depends(lambda: UUID("00000000-0000-0000-0000-000000000000")),
    from_date: date = Query(None, description="Filter from date"),
    to_date: date = Query(None, description="Filter to date"),
) -> APIResponse:
    """
    Get discipline statistics for the school.
    
    Returns:
    - Incidents by category count
    - Incidents by severity count
    """
    try:
        service = DisciplinaryService(db)
        
        by_category = await service.get_incidents_by_category_count(
            school_id=school_id,
            from_date=from_date,
            to_date=to_date,
        )
        
        by_severity = await service.get_incidents_by_severity_count(
            school_id=school_id,
            from_date=from_date,
            to_date=to_date,
        )
        
        total_incidents = sum(by_category.values())
        
        response = {
            "total_incidents": total_incidents,
            "incidents_by_category": by_category,
            "incidents_by_severity": by_severity,
        }
        
        return APIResponse.success(
            data=response,
            message="Statistics retrieved",
            status_code=200,
        )
    
    except Exception as e:
        logger.error(f"Error getting statistics: {e}")
        return APIResponse.error(
            error=str(e),
            message="Failed to get statistics",
            status_code=500,
        )


@router.get("/actions/active", response_model=APIResponse)
async def get_active_actions(
    db: AsyncSession = Depends(get_db),
    school_id: UUID = Depends(lambda: UUID("00000000-0000-0000-0000-000000000000")),
    student_id: UUID = Query(None, description="Filter by student"),
    action_type: str = Query(None, description="Filter by action type"),
) -> APIResponse:
    """
    Get all active disciplinary actions.
    
    Returns only actions that have not yet ended.
    """
    try:
        service = DisciplinaryService(db)
        actions = await service.list_active_actions(
            school_id=school_id,
            student_id=student_id,
            action_type=action_type,
        )
        
        responses = [
            DisciplinaryActionResponse(
                id=action.id,
                incident_id=action.incident_id,
                action_type=action.action_type.value,
                description=action.description,
                start_date=action.start_date,
                end_date=action.end_date,
                issued_date=action.issued_date,
                duration_days=(action.end_date - action.start_date).days + 1 if action.end_date else None,
                issued_by=None,
                reason=action.reason,
            )
            for action in actions
        ]
        
        return APIResponse.success(
            data=responses,
            message=f"Found {len(responses)} active actions",
            status_code=200,
        )
    
    except Exception as e:
        logger.error(f"Error listing active actions: {e}")
        return APIResponse.error(
            error=str(e),
            message="Failed to list active actions",
            status_code=500,
        )
