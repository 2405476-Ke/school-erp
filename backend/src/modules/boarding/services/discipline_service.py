"""
Disciplinary service for managing student infractions and actions.

Tracks incidents by category (Conduct, Curfew, Substance, Safety, Property, etc.)
and associated disciplinary actions (Warning, Detention, Suspension, Expulsion).
"""

import logging
from datetime import date, datetime
from uuid import UUID

from sqlalchemy import and_, select, func
from sqlalchemy.ext.asyncio import AsyncSession

from src.core.exceptions import NotFoundError, ValidationError
from src.modules.boarding.models.boarding import (
    DisciplinaryIncident,
    DisciplinaryAction,
    DisciplinaryCategory,
    DisciplinaryActionType,
)
from src.modules.admissions.models.students import Student

logger = logging.getLogger(__name__)


class DisciplinaryService:
    """Service for managing student discipline."""
    
    def __init__(self, db: AsyncSession):
        """Initialize with database session."""
        self.db = db
    
    async def report_incident(
        self,
        school_id: UUID,
        student_id: UUID,
        category: str,
        description: str,
        incident_date: date,
        location: str | None = None,
        witnesses: str | None = None,
        severity: int = 3,
        reported_by_staff_id: UUID | None = None,
    ) -> dict:
        """
        Report disciplinary incident.
        
        Args:
            school_id: Tenant identifier
            student_id: Student involved in incident
            category: ACADEMIC/CONDUCT/CURFEW/SUBSTANCE/SAFETY/PROPERTY/UNIFORM/OTHER
            description: Detailed description of incident
            incident_date: Date of incident
            location: Where incident occurred
            witnesses: Names of witnesses
            severity: 1-5 (1=minor, 5=critical)
            reported_by_staff_id: Staff who reported
        
        Returns:
            dict with incident_id, student_name, category, severity, message
        
        Raises:
            NotFoundError: If student not found
            ValidationError: If invalid data
        """
        logger.debug(
            f"Reporting incident for student {student_id}: {category} (severity {severity})"
        )
        
        # Fetch Student
        student_query = select(Student).where(
            and_(
                Student.id == student_id,
                Student.school_id == school_id,
            )
        )
        student = await self.db.scalar(student_query)
        
        if not student:
            logger.warning(f"Student {student_id} not found")
            raise NotFoundError(f"Student {student_id} not found")
        
        # Validate category
        try:
            DisciplinaryCategory(category)
        except ValueError:
            raise ValidationError(f"Invalid category: {category}")
        
        # Validate severity
        if not (1 <= severity <= 5):
            raise ValidationError("Severity must be between 1 and 5")
        
        # Validate description length
        if len(description) < 20:
            raise ValidationError("Description must be at least 20 characters")
        
        # Validate incident_date not in future
        if incident_date > date.today():
            raise ValidationError("Incident date cannot be in the future")
        
        # Create incident
        incident = DisciplinaryIncident(
            school_id=school_id,
            student_id=student_id,
            category=DisciplinaryCategory(category),
            description=description,
            incident_date=incident_date,
            reported_date=datetime.utcnow(),
            location=location,
            witnesses=witnesses,
            severity=severity,
            reported_by_staff_id=reported_by_staff_id,
        )
        
        self.db.add(incident)
        await self.db.commit()
        
        logger.info(
            f"Incident reported: student={student_id}, incident={incident.id}, "
            f"category={category}, severity={severity}"
        )
        
        severity_label = self._severity_label(severity)
        
        return {
            "incident_id": str(incident.id),
            "student_name": f"{student.first_name} {student.last_name}",
            "student_admission_number": student.admission_number,
            "category": category,
            "severity": severity,
            "severity_label": severity_label,
            "incident_date": incident_date.isoformat(),
            "message": f"Incident reported: {student.first_name} {student.last_name} - "
                      f"{category} (Severity: {severity_label})",
        }
    
    async def issue_action(
        self,
        school_id: UUID,
        incident_id: UUID,
        action_type: str,
        description: str,
        start_date: date,
        end_date: date | None,
        reason: str,
        issued_by_staff_id: UUID | None = None,
    ) -> dict:
        """
        Issue disciplinary action in response to incident.
        
        Args:
            school_id: Tenant identifier
            incident_id: Incident to action
            action_type: WARNING/DETENTION/SUSPENSION/EXPULSION/etc
            description: Details of action
            start_date: When action starts
            end_date: When action ends (null for permanent)
            reason: Justification
            issued_by_staff_id: Staff issuing action
        
        Returns:
            dict with action_id, action_type, start_date, end_date, message
        
        Raises:
            NotFoundError: If incident not found
            ValidationError: If invalid data
        """
        logger.debug(
            f"Issuing disciplinary action for incident {incident_id}: {action_type}"
        )
        
        # Fetch incident
        incident_query = select(DisciplinaryIncident).where(
            and_(
                DisciplinaryIncident.id == incident_id,
                DisciplinaryIncident.school_id == school_id,
            )
        )
        incident = await self.db.scalar(incident_query)
        
        if not incident:
            logger.warning(f"Incident {incident_id} not found")
            raise NotFoundError(f"Incident {incident_id} not found")
        
        # Validate action_type
        try:
            DisciplinaryActionType(action_type)
        except ValueError:
            raise ValidationError(f"Invalid action type: {action_type}")
        
        # Validate dates
        if end_date and end_date < start_date:
            raise ValidationError("end_date must be >= start_date")
        
        # Validate reason length
        if len(reason) < 20:
            raise ValidationError("Reason must be at least 20 characters")
        
        # Create action
        action = DisciplinaryAction(
            school_id=school_id,
            incident_id=incident_id,
            action_type=DisciplinaryActionType(action_type),
            description=description,
            start_date=start_date,
            end_date=end_date,
            issued_by_staff_id=issued_by_staff_id,
            issued_date=datetime.utcnow(),
            reason=reason,
        )
        
        self.db.add(action)
        await self.db.commit()
        
        logger.info(
            f"Action issued: incident={incident_id}, action={action.id}, "
            f"type={action_type}, start={start_date}, end={end_date}"
        )
        
        duration = ""
        if end_date:
            duration_days = (end_date - start_date).days + 1
            duration = f" ({duration_days} days)"
        
        return {
            "action_id": str(action.id),
            "incident_id": str(incident_id),
            "student_name": f"{incident.student.first_name} {incident.student.last_name}",
            "action_type": action_type,
            "start_date": start_date.isoformat(),
            "end_date": end_date.isoformat() if end_date else None,
            "message": f"Action issued: {action_type}{duration}",
        }
    
    async def get_incident(
        self,
        school_id: UUID,
        incident_id: UUID,
    ) -> DisciplinaryIncident:
        """Get incident with all actions."""
        query = select(DisciplinaryIncident).where(
            and_(
                DisciplinaryIncident.id == incident_id,
                DisciplinaryIncident.school_id == school_id,
            )
        )
        incident = await self.db.scalar(query)
        
        if not incident:
            raise NotFoundError(f"Incident {incident_id} not found")
        
        return incident
    
    async def get_student_disciplinary_record(
        self,
        school_id: UUID,
        student_id: UUID,
    ) -> dict:
        """
        Get complete disciplinary record for student.
        
        Returns:
            dict with total_incidents, incidents_by_category, active_actions, recent_incidents
        """
        # Fetch all incidents
        incidents_query = select(DisciplinaryIncident).where(
            and_(
                DisciplinaryIncident.student_id == student_id,
                DisciplinaryIncident.school_id == school_id,
            )
        ).order_by(DisciplinaryIncident.incident_date.desc())
        
        result = await self.db.execute(incidents_query)
        incidents = result.scalars().all()
        
        # Count by category
        incidents_by_category = {}
        for incident in incidents:
            category = incident.category.value
            incidents_by_category[category] = incidents_by_category.get(category, 0) + 1
        
        # Get active actions
        active_actions_query = select(DisciplinaryAction).where(
            and_(
                DisciplinaryAction.incident_id.in_([i.id for i in incidents]),
                (
                    (DisciplinaryAction.end_date.is_(None)) |
                    (DisciplinaryAction.end_date >= date.today())
                ),
            )
        ).order_by(DisciplinaryAction.start_date.desc())
        
        result = await self.db.execute(active_actions_query)
        active_actions = result.scalars().all()
        
        # Get student
        student_query = select(Student).where(
            and_(
                Student.id == student_id,
                Student.school_id == school_id,
            )
        )
        student = await self.db.scalar(student_query)
        
        if not student:
            raise NotFoundError(f"Student {student_id} not found")
        
        return {
            "student_id": str(student_id),
            "student_name": f"{student.first_name} {student.last_name}",
            "student_admission_number": student.admission_number,
            "total_incidents": len(incidents),
            "incidents_by_category": incidents_by_category,
            "active_actions_count": len(active_actions),
            "active_actions": [
                {
                    "id": str(action.id),
                    "action_type": action.action_type.value,
                    "start_date": action.start_date.isoformat(),
                    "end_date": action.end_date.isoformat() if action.end_date else None,
                    "description": action.description,
                }
                for action in active_actions
            ],
            "recent_incidents": [
                {
                    "id": str(incident.id),
                    "category": incident.category.value,
                    "incident_date": incident.incident_date.isoformat(),
                    "severity": incident.severity,
                    "severity_label": self._severity_label(incident.severity),
                    "description": incident.description[:100],  # First 100 chars
                    "actions_count": len(incident.disciplinary_actions),
                }
                for incident in incidents[:10]  # Last 10 incidents
            ],
        }
    
    async def list_incidents(
        self,
        school_id: UUID,
        student_id: UUID | None = None,
        category: str | None = None,
        severity: int | None = None,
        from_date: date | None = None,
        to_date: date | None = None,
    ) -> list[DisciplinaryIncident]:
        """
        List incidents with filters.
        
        Args:
            school_id: Tenant identifier
            student_id: Filter by student
            category: Filter by category
            severity: Filter by minimum severity
            from_date: Filter from date
            to_date: Filter to date
        
        Returns:
            list of DisciplinaryIncident
        """
        query = select(DisciplinaryIncident).where(
            DisciplinaryIncident.school_id == school_id
        )
        
        if student_id:
            query = query.where(DisciplinaryIncident.student_id == student_id)
        
        if category:
            query = query.where(DisciplinaryIncident.category == DisciplinaryCategory(category))
        
        if severity:
            query = query.where(DisciplinaryIncident.severity >= severity)
        
        if from_date:
            query = query.where(DisciplinaryIncident.incident_date >= from_date)
        
        if to_date:
            query = query.where(DisciplinaryIncident.incident_date <= to_date)
        
        query = query.order_by(DisciplinaryIncident.incident_date.desc())
        
        result = await self.db.execute(query)
        return result.scalars().all()
    
    async def list_active_actions(
        self,
        school_id: UUID,
        student_id: UUID | None = None,
        action_type: str | None = None,
    ) -> list[DisciplinaryAction]:
        """
        List active disciplinary actions.
        
        Returns only actions that have not yet ended (end_date is null or >= today).
        """
        query = select(DisciplinaryAction).where(
            DisciplinaryAction.school_id == school_id,
            (
                (DisciplinaryAction.end_date.is_(None)) |
                (DisciplinaryAction.end_date >= date.today())
            ),
        )
        
        # Join with incident to filter by student
        if student_id:
            query = query.join(DisciplinaryIncident).where(
                DisciplinaryIncident.student_id == student_id
            )
        
        if action_type:
            query = query.where(DisciplinaryAction.action_type == DisciplinaryActionType(action_type))
        
        query = query.order_by(DisciplinaryAction.start_date.desc())
        
        result = await self.db.execute(query)
        return result.scalars().all()
    
    async def get_incidents_by_category_count(
        self,
        school_id: UUID,
        from_date: date | None = None,
        to_date: date | None = None,
    ) -> dict:
        """
        Get count of incidents by category.
        
        Returns:
            dict with category as key and count as value
        """
        query = select(
            DisciplinaryIncident.category,
            func.count(DisciplinaryIncident.id).label("count")
        ).where(
            DisciplinaryIncident.school_id == school_id
        )
        
        if from_date:
            query = query.where(DisciplinaryIncident.incident_date >= from_date)
        
        if to_date:
            query = query.where(DisciplinaryIncident.incident_date <= to_date)
        
        query = query.group_by(DisciplinaryIncident.category)
        
        result = await self.db.execute(query)
        rows = result.all()
        
        return {
            row[0].value: row[1]
            for row in rows
        }
    
    async def get_incidents_by_severity_count(
        self,
        school_id: UUID,
        from_date: date | None = None,
        to_date: date | None = None,
    ) -> dict:
        """
        Get count of incidents by severity level.
        
        Returns:
            dict with severity (1-5) as key and count as value
        """
        query = select(
            DisciplinaryIncident.severity,
            func.count(DisciplinaryIncident.id).label("count")
        ).where(
            DisciplinaryIncident.school_id == school_id
        )
        
        if from_date:
            query = query.where(DisciplinaryIncident.incident_date >= from_date)
        
        if to_date:
            query = query.where(DisciplinaryIncident.incident_date <= to_date)
        
        query = query.group_by(DisciplinaryIncident.severity).order_by(DisciplinaryIncident.severity)
        
        result = await self.db.execute(query)
        rows = result.all()
        
        return {
            str(row[0]): row[1]
            for row in rows
        }
    
    def _severity_label(self, severity: int) -> str:
        """Convert severity number to label."""
        labels = {
            1: "Minor",
            2: "Low",
            3: "Medium",
            4: "High",
            5: "Critical",
        }
        return labels.get(severity, "Unknown")
