"""
Gate Security Service.

CRITICAL: Verifies student exit authorization against Boarding leave passes.
Tracks all gate events with comprehensive audit trail.
"""

import logging
from datetime import datetime, timedelta
from uuid import UUID
from typing import Optional, Tuple

from sqlalchemy import select, and_, func
from sqlalchemy.ext.asyncio import AsyncSession

from src.core.exceptions import NotFoundError, ValidationError, ForbiddenError
from src.modules.security.models.gate import (
    Visitor,
    VisitorLog,
    StudentGateEvent,
    GateSuspicion,
    VisitorType,
    StudentEventType,
    VisitorStatus,
    GateSuspicion as GateSuspicionModel,
)

logger = logging.getLogger(__name__)


class ForbiddenExitError(Exception):
    """Raised when student attempts unauthorized exit."""
    
    def __init__(self, reason: str, alert_level: str = "HIGH"):
        self.reason = reason
        self.alert_level = alert_level
        super().__init__(reason)


class GateService:
    """Security service for gate access control."""
    
    def __init__(self, db: AsyncSession):
        """Initialize with database session."""
        self.db = db
    
    async def log_visitor_entry(
        self,
        school_id: UUID,
        first_name: str,
        last_name: str,
        national_id: str,
        phone: str,
        visitor_type: str,
        purpose: str,
        host_staff_id: Optional[UUID] = None,
        vehicle_registration: Optional[str] = None,
        vehicle_description: Optional[str] = None,
        email: Optional[str] = None,
        checked_by_user_id: Optional[UUID] = None,
    ) -> dict:
        """
        CRITICAL: Register visitor entry and generate gate pass.
        
        Algorithm:
        1. Check if visitor is blacklisted
        2. Look up or create Visitor record
        3. Generate gate pass number: PASS-YYYYMMDD-NNNNN
        4. Create VisitorLog with CHECKED_IN status
        5. Update visitor's last_visited_at and visit count
        6. Return gate pass details
        
        Args:
            school_id: Tenant identifier
            first_name, last_name, national_id, phone: Visitor identification
            visitor_type: PARENT, DELIVERY, CONTRACTOR, etc.
            purpose: Reason for visit
            host_staff_id: Staff person hosting visitor
            vehicle_registration: Vehicle plate if applicable
            vehicle_description: Vehicle details
            email: Visitor email
            checked_by_user_id: Guard's user ID
        
        Returns:
            dict with gate_pass_number, visitor_id, status
        
        Raises:
            ForbiddenError: If visitor is blacklisted
            ValidationError: If required fields missing
        """
        logger.info(
            f"Visitor entry: {first_name} {last_name}, "
            f"type={visitor_type}, purpose={purpose}"
        )
        
        # STEP 1: Check national ID is blacklisted
        visitor = await self.db.scalar(
            select(Visitor).where(
                and_(
                    Visitor.school_id == school_id,
                    Visitor.national_id == national_id,
                )
            )
        )
        
        if visitor and visitor.is_blacklisted:
            logger.warning(
                f"BLACKLIST ALERT: Visitor {first_name} {last_name} "
                f"(ID: {national_id}) attempted entry. Reason: {visitor.blacklist_reason}"
            )
            
            # Create suspicion record
            await self._create_suspicion(
                school_id=school_id,
                visitor_id=visitor.id,
                incident_type="BLACKLIST_MATCH",
                description=f"Blacklisted visitor {first_name} {last_name} attempted entry",
                severity="CRITICAL",
            )
            
            raise ForbiddenError(
                f"Visitor is blacklisted: {visitor.blacklist_reason}"
            )
        
        # STEP 2: Look up or create Visitor record
        if not visitor:
            visitor = Visitor(
                school_id=school_id,
                first_name=first_name,
                last_name=last_name,
                national_id=national_id,
                phone=phone,
                email=email,
                visitor_type=visitor_type,
                vehicle_registration=vehicle_registration,
                vehicle_description=vehicle_description,
            )
            self.db.add(visitor)
            await self.db.flush()
            logger.debug(f"New visitor record created: {visitor.id}")
        
        # STEP 3: Generate gate pass number
        # Format: PASS-YYYYMMDD-NNNNN
        today = datetime.utcnow().strftime("%Y%m%d")
        
        # Count today's passes for this school
        count_result = await self.db.execute(
            select(func.count(VisitorLog.id)).where(
                and_(
                    VisitorLog.school_id == school_id,
                    func.DATE(VisitorLog.check_in_time) == today,
                )
            )
        )
        pass_count = (count_result.scalar() or 0) + 1
        gate_pass_number = f"PASS-{today}-{pass_count:05d}"
        
        logger.debug(f"Generated gate pass: {gate_pass_number}")
        
        # STEP 4: Create VisitorLog
        log = VisitorLog(
            school_id=school_id,
            visitor_id=visitor.id,
            purpose=purpose,
            host_staff_id=host_staff_id,
            gate_pass_number=gate_pass_number,
            check_in_time=datetime.utcnow(),
            status=VisitorStatus.CHECKED_IN.value,
            checked_by_user_id=checked_by_user_id,
        )
        
        self.db.add(log)
        
        # STEP 5: Update visitor record
        visitor.last_visited_at = datetime.utcnow()
        visitor.total_visits += 1
        
        await self.db.commit()
        
        logger.info(
            f"Visitor checked in: {gate_pass_number}, "
            f"visitor={first_name} {last_name}, host_staff={host_staff_id}"
        )
        
        return {
            "gate_pass_number": gate_pass_number,
            "visitor_id": str(visitor.id),
            "visitor_name": f"{first_name} {last_name}",
            "visitor_type": visitor_type,
            "check_in_time": log.check_in_time.isoformat(),
            "purpose": purpose,
            "status": VisitorStatus.CHECKED_IN.value,
            "message": f"Gate pass {gate_pass_number} issued. Welcome to campus.",
        }
    
    async def checkout_visitor(
        self,
        school_id: UUID,
        gate_pass_number: str,
        security_notes: Optional[str] = None,
        checked_by_user_id: Optional[UUID] = None,
    ) -> dict:
        """
        Log visitor checkout.
        
        Args:
            school_id: Tenant identifier
            gate_pass_number: Gate pass to check out
            security_notes: Any security observations
            checked_by_user_id: Guard's user ID
        
        Returns:
            dict with checkout details
        
        Raises:
            NotFoundError: If gate pass not found
        """
        logger.debug(f"Checking out visitor: {gate_pass_number}")
        
        log = await self.db.scalar(
            select(VisitorLog).where(
                and_(
                    VisitorLog.school_id == school_id,
                    VisitorLog.gate_pass_number == gate_pass_number,
                )
            )
        )
        
        if not log:
            raise NotFoundError(f"Gate pass not found: {gate_pass_number}")
        
        if log.status == VisitorStatus.CHECKED_OUT.value:
            raise ValidationError(f"Gate pass already checked out: {gate_pass_number}")
        
        log.check_out_time = datetime.utcnow()
        log.status = VisitorStatus.CHECKED_OUT.value
        log.security_notes = security_notes
        
        await self.db.commit()
        
        visitor = log.visitor
        visit_duration = (log.check_out_time - log.check_in_time).total_seconds() / 60
        
        logger.info(
            f"Visitor checked out: {gate_pass_number}, "
            f"duration={visit_duration:.0f} minutes"
        )
        
        return {
            "gate_pass_number": gate_pass_number,
            "visitor_name": f"{visitor.first_name} {visitor.last_name}",
            "check_in_time": log.check_in_time.isoformat(),
            "check_out_time": log.check_out_time.isoformat(),
            "visit_duration_minutes": int(visit_duration),
            "status": VisitorStatus.CHECKED_OUT.value,
            "message": f"Visitor {visitor.first_name} checked out successfully.",
        }
    
    async def scan_student_exit(
        self,
        school_id: UUID,
        student_id: UUID,
        guard_user_id: UUID,
    ) -> dict:
        """
        CRITICAL SECURITY FUNCTION: Verify student exit authorization.
        
        Algorithm:
        1. Validate student exists in Admissions module
        2. Call ExeatService.verify_gate_exit() from Boarding module
           - Returns: {allowed: bool, leave_pass_id, exeat_type, return_time, etc.}
        3. If allowed:
           a. Create StudentGateEvent(EXIT, is_authorized=True)
           b. Return clearance with leave pass details
           c. Log message with return time
        4. If NOT allowed:
           a. Raise ForbiddenExitError
           b. Log StudentGateEvent(EXIT, is_authorized=False)
           c. Create GateSuspicion record
           d. Trigger alert to Boarding Master
        
        Args:
            school_id: Tenant identifier
            student_id: Student to scan for exit
            guard_user_id: Security guard's user ID
        
        Returns:
            dict with clearance decision and pass details
        
        Raises:
            ForbiddenExitError: If student not authorized to exit
            NotFoundError: If student not found
        """
        logger.info(f"Scanning student exit: student_id={student_id}")
        
        # STEP 1: Fetch student from Admissions module
        from src.modules.admissions.models.students import Student
        
        student = await self.db.scalar(
            select(Student).where(
                and_(
                    Student.id == student_id,
                    Student.school_id == school_id,
                )
            )
        )
        
        if not student:
            logger.warning(f"Student not found for exit scan: {student_id}")
            raise NotFoundError(f"Student {student_id} not found")
        
        logger.debug(f"Student identified: {student.first_name} {student.last_name}, class={student.current_class_id}")
        
        # STEP 2: Call Boarding module to verify leave pass
        # CRITICAL: This cross-module call determines if exit is authorized
        from src.modules.boarding.services.exeat_service import ExeatService
        
        exeat_service = ExeatService(self.db)
        current_time = datetime.utcnow()
        
        try:
            authorization_result = await exeat_service.verify_gate_exit(
                school_id=school_id,
                student_id=student_id,
                current_time=current_time,
            )
            
            logger.debug(f"Exeat verification result: {authorization_result}")
            
        except Exception as e:
            logger.error(f"Exeat verification error: {str(e)}", exc_info=True)
            authorization_result = {
                "allowed": False,
                "reason": "System error checking leave pass",
            }
        
        # STEP 3: Process authorization decision
        if authorization_result.get("allowed", False):
            # ✓ AUTHORIZED EXIT
            logger.info(
                f"AUTHORIZED EXIT: {student.first_name} {student.last_name}, "
                f"exeat_type={authorization_result.get('exeat_type')}"
            )
            
            # Create event record
            event = StudentGateEvent(
                school_id=school_id,
                student_id=student_id,
                event_type=StudentEventType.EXIT.value,
                is_authorized=True,
                leave_pass_id=authorization_result.get("leave_pass_id"),
                authorization_details=f"Approved via {authorization_result.get('exeat_type')} exeat",
                logged_by_user_id=guard_user_id,
            )
            
            self.db.add(event)
            await self.db.commit()
            
            logger.info(f"Gate event logged: {event.id}, EXIT, AUTHORIZED")
            
            return {
                "allowed": True,
                "student_id": str(student_id),
                "student_name": f"{student.first_name} {student.last_name}",
                "class_level": student.current_class,
                "event_id": str(event.id),
                "exeat_type": authorization_result.get("exeat_type"),
                "expected_return_time": authorization_result.get("expected_return_time"),
                "contact_person_name": authorization_result.get("contact_person_name"),
                "contact_person_phone": authorization_result.get("contact_person_phone"),
                "message": f"✓ CLEAR TO EXIT: {student.first_name} has approved {authorization_result.get('exeat_type')} leave. Expected return: {authorization_result.get('expected_return_time')}",
            }
        
        else:
            # ✗ UNAUTHORIZED EXIT
            reason = authorization_result.get("reason", "No approved leave pass")
            logger.warning(
                f"UNAUTHORIZED EXIT ATTEMPT: {student.first_name} {student.last_name}, "
                f"reason={reason}"
            )
            
            # Create event record
            event = StudentGateEvent(
                school_id=school_id,
                student_id=student_id,
                event_type=StudentEventType.EXIT.value,
                is_authorized=False,
                logged_by_user_id=guard_user_id,
                alert_generated=True,
                alert_message=f"Unauthorized exit attempt: {reason}",
            )
            
            self.db.add(event)
            await self.db.flush()
            
            # Create suspicion record
            await self._create_suspicion(
                school_id=school_id,
                student_id=student_id,
                gate_event_id=event.id,
                incident_type="UNAUTHORIZED_EXIT",
                description=f"Student {student.first_name} {student.last_name} attempted unauthorized exit: {reason}",
                severity="HIGH",
            )
            
            await self.db.commit()
            
            logger.critical(
                f"Gate event logged: {event.id}, EXIT, UNAUTHORIZED, alert_generated=True"
            )
            
            # Raise exception with details for API response
            raise ForbiddenExitError(reason=reason, alert_level="HIGH")
    
    async def scan_student_entry(
        self,
        school_id: UUID,
        student_id: UUID,
        guard_user_id: UUID,
    ) -> dict:
        """
        Log student return to campus.
        
        Algorithm:
        1. Verify student exists
        2. Create StudentGateEvent(ENTRY)
        3. Query active leave pass for this student
        4. If leave pass found:
           a. Update status to RETURNED
           b. Set return_time = now()
        5. Return confirmation
        
        Args:
            school_id: Tenant identifier
            student_id: Student returning to campus
            guard_user_id: Security guard's user ID
        
        Returns:
            dict with entry confirmation and leave pass update
        
        Raises:
            NotFoundError: If student not found
        """
        logger.info(f"Scanning student entry: student_id={student_id}")
        
        # Fetch student
        from src.modules.admissions.models.students import Student
        
        student = await self.db.scalar(
            select(Student).where(
                and_(
                    Student.id == student_id,
                    Student.school_id == school_id,
                )
            )
        )
        
        if not student:
            raise NotFoundError(f"Student not found: {student_id}")
        
        logger.debug(f"Student identified for entry: {student.first_name} {student.last_name}")
        
        # Create gate event
        event = StudentGateEvent(
            school_id=school_id,
            student_id=student_id,
            event_type=StudentEventType.ENTRY.value,
            is_authorized=True,  # Entry always logged
            logged_by_user_id=guard_user_id,
        )
        
        self.db.add(event)
        await self.db.flush()
        
        # Update leave pass status if applicable
        leave_pass_updated = False
        updated_status = None
        
        try:
            from src.modules.boarding.models.boarding import LeavePass, LeavePassStatus
            
            # Find active leave pass for this student
            leave_pass = await self.db.scalar(
                select(LeavePass).where(
                    and_(
                        LeavePass.student_id == student_id,
                        LeavePass.status == LeavePassStatus.APPROVED.value,
                    )
                )
            )
            
            if leave_pass:
                leave_pass.status = LeavePassStatus.RETURNED.value
                leave_pass.return_time = datetime.utcnow()
                
                leave_pass_updated = True
                updated_status = LeavePassStatus.RETURNED.value
                
                logger.debug(
                    f"Leave pass updated to RETURNED: {leave_pass.id}, "
                    f"return_time={leave_pass.return_time}"
                )
        
        except Exception as e:
            logger.warning(f"Error updating leave pass on entry: {str(e)}")
        
        await self.db.commit()
        
        logger.info(
            f"Student entry logged: {event.id}, student={student.first_name} {student.last_name}, "
            f"leave_pass_updated={leave_pass_updated}"
        )
        
        return {
            "logged": True,
            "student_id": str(student_id),
            "student_name": f"{student.first_name} {student.last_name}",
            "class_level": student.current_class,
            "event_type": StudentEventType.ENTRY.value,
            "timestamp": event.timestamp.isoformat(),
            "leave_pass_updated": leave_pass_updated,
            "leave_pass_status": updated_status,
            "message": f"✓ Welcome back {student.first_name}! Entry logged at {event.timestamp.strftime('%H:%M:%S')}",
        }
    
    async def get_student_gate_history(
        self,
        school_id: UUID,
        student_id: UUID,
        days_back: int = 30,
    ) -> list[dict]:
        """Get student's recent gate events."""
        cutoff_date = datetime.utcnow() - timedelta(days=days_back)
        
        events_result = await self.db.execute(
            select(StudentGateEvent).where(
                and_(
                    StudentGateEvent.school_id == school_id,
                    StudentGateEvent.student_id == student_id,
                    StudentGateEvent.created_at >= cutoff_date,
                )
            ).order_by(StudentGateEvent.timestamp.desc())
        )
        
        events = events_result.scalars().all()
        
        return [
            {
                "event_id": str(e.id),
                "event_type": e.event_type,
                "timestamp": e.timestamp.isoformat(),
                "is_authorized": e.is_authorized,
                "alert_generated": e.alert_generated,
                "alert_message": e.alert_message,
            }
            for e in events
        ]
    
    async def blacklist_visitor(
        self,
        school_id: UUID,
        national_id: str,
        reason: str,
    ) -> dict:
        """Blacklist a visitor from campus."""
        visitor = await self.db.scalar(
            select(Visitor).where(
                and_(
                    Visitor.school_id == school_id,
                    Visitor.national_id == national_id,
                )
            )
        )
        
        if not visitor:
            raise NotFoundError(f"Visitor not found: {national_id}")
        
        visitor.is_blacklisted = True
        visitor.blacklist_reason = reason
        
        await self.db.commit()
        
        logger.warning(f"Visitor blacklisted: {visitor.first_name} {visitor.last_name}, reason={reason}")
        
        return {
            "visitor_id": str(visitor.id),
            "visitor_name": f"{visitor.first_name} {visitor.last_name}",
            "is_blacklisted": True,
            "blacklist_reason": reason,
            "message": f"Visitor blacklisted and will be denied entry",
        }
    
    async def get_gate_audit_report(
        self,
        school_id: UUID,
        days_back: int = 1,
    ) -> dict:
        """Generate gate security audit report."""
        cutoff_date = datetime.utcnow() - timedelta(days=days_back)
        
        # Query student events
        student_events_result = await self.db.execute(
            select(StudentGateEvent).where(
                and_(
                    StudentGateEvent.school_id == school_id,
                    StudentGateEvent.created_at >= cutoff_date,
                )
            )
        )
        student_events = student_events_result.scalars().all()
        
        # Categorize events
        exits = [e for e in student_events if e.event_type == StudentEventType.EXIT.value]
        entries = [e for e in student_events if e.event_type == StudentEventType.ENTRY.value]
        
        authorized_exits = len([e for e in exits if e.is_authorized])
        unauthorized_exits = len([e for e in exits if not e.is_authorized])
        
        # Query visitor events
        visitor_logs_result = await self.db.execute(
            select(VisitorLog).where(
                and_(
                    VisitorLog.school_id == school_id,
                    VisitorLog.created_at >= cutoff_date,
                )
            )
        )
        visitor_logs = visitor_logs_result.scalars().all()
        
        visitor_checkouts = len([v for v in visitor_logs if v.status == VisitorStatus.CHECKED_OUT.value])
        
        # Query suspicions
        suspicions_result = await self.db.execute(
            select(GateSuspicionModel).where(
                and_(
                    GateSuspicionModel.school_id == school_id,
                    GateSuspicionModel.created_at >= cutoff_date,
                )
            )
        )
        suspicions = suspicions_result.scalars().all()
        
        critical_incidents = len([s for s in suspicions if s.severity == "CRITICAL"])
        
        # Calculate rates
        unauthorized_rate = 0.0
        if len(exits) > 0:
            unauthorized_rate = (unauthorized_exits / len(exits)) * 100
        
        period = f"Last {days_back} day(s)"
        
        return {
            "period": period,
            "total_student_exits": len(exits),
            "total_student_entries": len(entries),
            "authorized_exits": authorized_exits,
            "unauthorized_exits": unauthorized_exits,
            "unauthorized_exit_rate": round(unauthorized_rate, 2),
            "total_visitor_entries": len(visitor_logs),
            "visitor_check_outs": visitor_checkouts,
            "total_suspicions": len(suspicions),
            "critical_incidents": critical_incidents,
            "report_generated_at": datetime.utcnow().isoformat(),
        }
    
    async def _create_suspicion(
        self,
        school_id: UUID,
        incident_type: str,
        description: str,
        severity: str,
        student_id: Optional[UUID] = None,
        visitor_id: Optional[UUID] = None,
        gate_event_id: Optional[UUID] = None,
    ) -> GateSuspicionModel:
        """Create security suspicion record."""
        suspicion = GateSuspicionModel(
            school_id=school_id,
            student_id=student_id,
            visitor_id=visitor_id,
            gate_event_id=gate_event_id,
            incident_type=incident_type,
            description=description,
            severity=severity,
        )
        
        self.db.add(suspicion)
        await self.db.flush()
        
        logger.warning(
            f"Suspicion created: type={incident_type}, "
            f"severity={severity}, description={description}"
        )
        
        return suspicion
