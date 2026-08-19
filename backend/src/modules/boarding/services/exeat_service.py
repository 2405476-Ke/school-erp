"""
Exeat/Leave Pass service for student security and movement control.

SECURITY CRITICAL: Manages student leave passes with strict approval workflow.

Gate/Security module calls verify_gate_exit() to authorize student departure.

Guarantees:
- Only authorized roles can approve passes (Boarding Master, Deputy Principal, Principal)
- Only APPROVED passes allow gate exit
- Gate exit verification checks timestamp against expected_return_time
- Tracks departure and return times for audit trail
"""

import logging
from datetime import datetime, date, timedelta
from uuid import UUID

from sqlalchemy import and_, select, func
from sqlalchemy.ext.asyncio import AsyncSession

from src.core.exceptions import NotFoundError, ValidationError
from src.modules.boarding.models.boarding import (
    StudentLeavePass,
    LeavePassStatus,
    ExeatType,
)
from src.modules.admissions.models.students import Student
from src.modules.auth.models.user import User, Role

logger = logging.getLogger(__name__)

# Roles authorized to approve leave passes
APPROVED_ROLES = ["BOARDING_MASTER", "DEPUTY_PRINCIPAL", "PRINCIPAL", "ADMIN"]


class ExeatService:
    """Service for managing student leave passes (exeat)."""
    
    def __init__(self, db: AsyncSession):
        """Initialize with database session."""
        self.db = db
    
    async def request_leave_pass(
        self,
        school_id: UUID,
        student_id: UUID,
        exeat_type: str,
        reason: str,
        expected_return_time: datetime,
        destination: str | None = None,
        contact_person_name: str | None = None,
        contact_person_phone: str | None = None,
    ) -> dict:
        """
        Student/guardian requests leave pass.
        
        Args:
            school_id: Tenant identifier
            student_id: Student requesting leave
            exeat_type: DAY_OUT/OVERNIGHT/WEEKEND/HOLIDAY/MEDICAL/BEREAVEMENT/SPECIAL
            reason: Reason for leave
            expected_return_time: When student will return
            destination: Where student is going
            contact_person_name: Emergency contact
            contact_person_phone: Emergency contact phone
        
        Returns:
            dict with leave_pass_id, status, message
        
        Raises:
            NotFoundError: If student not found
            ValidationError: If invalid data
        """
        logger.debug(f"Requesting leave pass for student {student_id}: {exeat_type}")
        
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
        
        # Validate student is active
        if not student.is_active:
            logger.warning(f"Student {student_id} is inactive")
            raise ValidationError(f"Student is not active")
        
        # Validate exeat_type
        try:
            ExeatType(exeat_type)
        except ValueError:
            raise ValidationError(f"Invalid exeat type: {exeat_type}")
        
        # Validate expected_return_time is in future
        if expected_return_time <= datetime.utcnow():
            logger.warning(f"Expected return time is in the past")
            raise ValidationError("Expected return time must be in the future")
        
        # Validate reason length
        if len(reason) < 10:
            raise ValidationError("Reason must be at least 10 characters")
        
        # Create leave pass
        leave_pass = StudentLeavePass(
            school_id=school_id,
            student_id=student_id,
            exeat_type=ExeatType(exeat_type),
            reason=reason,
            expected_return_time=expected_return_time,
            status=LeavePassStatus.REQUESTED,
            requested_date=datetime.utcnow(),
            destination=destination,
            contact_person_name=contact_person_name,
            contact_person_phone=contact_person_phone,
        )
        
        self.db.add(leave_pass)
        await self.db.commit()
        
        logger.info(
            f"Leave pass requested: student={student_id}, pass={leave_pass.id}, "
            f"type={exeat_type}, expected_return={expected_return_time}"
        )
        
        return {
            "leave_pass_id": str(leave_pass.id),
            "student_name": f"{student.first_name} {student.last_name}",
            "exeat_type": exeat_type,
            "status": LeavePassStatus.REQUESTED.value,
            "requested_date": datetime.utcnow().isoformat(),
            "expected_return_time": expected_return_time.isoformat(),
            "message": f"Leave pass requested for {student.first_name} {student.last_name}. "
                      f"Awaiting approval.",
        }
    
    async def approve_leave_pass(
        self,
        school_id: UUID,
        leave_pass_id: UUID,
        approved_by_user_id: UUID,
        approved: bool = True,
        approval_reason: str | None = None,
    ) -> dict:
        """
        CRITICAL: Approve or reject leave pass.
        
        SECURITY: Only authorized roles (Boarding Master, Deputy Principal, Principal)
        can approve passes.
        
        Args:
            school_id: Tenant identifier
            leave_pass_id: Leave pass to approve
            approved_by_user_id: User approving
            approved: True to approve, False to reject
            approval_reason: Reason for decision
        
        Returns:
            dict with leave_pass_id, status, approved_date, message
        
        Raises:
            NotFoundError: If leave pass or user not found
            ValidationError: If user not authorized or pass already processed
        """
        logger.debug(
            f"Processing leave pass approval: pass={leave_pass_id}, "
            f"approved={approved}, user={approved_by_user_id}"
        )
        
        # STEP 1: Fetch approving user and validate authorization
        user_query = select(User).where(User.id == approved_by_user_id)
        user = await self.db.scalar(user_query)
        
        if not user:
            logger.warning(f"User {approved_by_user_id} not found")
            raise NotFoundError(f"User not found")
        
        # Check user has authorized role
        user_role = user.role.value if hasattr(user.role, "value") else str(user.role)
        
        if user_role not in APPROVED_ROLES:
            logger.warning(
                f"User {approved_by_user_id} with role {user_role} not authorized to approve passes"
            )
            raise ValidationError(
                f"User role '{user_role}' is not authorized to approve leave passes. "
                f"Only {', '.join(APPROVED_ROLES)} can approve."
            )
        
        logger.debug(f"User {approved_by_user_id} authorized with role {user_role}")
        
        # STEP 2: Fetch leave pass
        pass_query = select(StudentLeavePass).where(
            and_(
                StudentLeavePass.id == leave_pass_id,
                StudentLeavePass.school_id == school_id,
            )
        )
        leave_pass = await self.db.scalar(pass_query)
        
        if not leave_pass:
            logger.warning(f"Leave pass {leave_pass_id} not found")
            raise NotFoundError(f"Leave pass {leave_pass_id} not found")
        
        # Validate pass is in REQUESTED status
        if leave_pass.status != LeavePassStatus.REQUESTED:
            logger.warning(
                f"Leave pass {leave_pass_id} has status {leave_pass.status}, cannot approve"
            )
            raise ValidationError(
                f"Leave pass has already been processed (status: {leave_pass.status.value}). "
                f"Cannot approve."
            )
        
        # STEP 3: Update leave pass status
        if approved:
            leave_pass.status = LeavePassStatus.APPROVED
            message = f"Leave pass APPROVED by {user.first_name} {user.last_name}"
        else:
            leave_pass.status = LeavePassStatus.REJECTED
            message = f"Leave pass REJECTED by {user.first_name} {user.last_name}"
        
        leave_pass.approved_by = approved_by_user_id
        leave_pass.approved_date = datetime.utcnow()
        
        await self.db.commit()
        
        logger.info(
            f"Leave pass processed: pass={leave_pass_id}, status={leave_pass.status.value}, "
            f"approved_by={approved_by_user_id}"
        )
        
        return {
            "leave_pass_id": str(leave_pass_id),
            "student_name": leave_pass.student.first_name + " " + leave_pass.student.last_name,
            "status": leave_pass.status.value,
            "approved_date": leave_pass.approved_date.isoformat(),
            "approved_by": f"{user.first_name} {user.last_name}",
            "message": message,
        }
    
    async def record_departure(
        self,
        school_id: UUID,
        leave_pass_id: UUID,
        departure_time: datetime,
    ) -> dict:
        """
        Record when student leaves school (at gate).
        
        Args:
            school_id: Tenant identifier
            leave_pass_id: Leave pass
            departure_time: When student departed
        
        Returns:
            dict with leave_pass_id, status, departure_time
        
        Raises:
            NotFoundError: If leave pass not found
            ValidationError: If pass not APPROVED
        """
        logger.debug(f"Recording departure for leave pass {leave_pass_id}")
        
        # Fetch leave pass
        pass_query = select(StudentLeavePass).where(
            and_(
                StudentLeavePass.id == leave_pass_id,
                StudentLeavePass.school_id == school_id,
            )
        )
        leave_pass = await self.db.scalar(pass_query)
        
        if not leave_pass:
            raise NotFoundError(f"Leave pass {leave_pass_id} not found")
        
        # Validate status is APPROVED
        if leave_pass.status != LeavePassStatus.APPROVED:
            raise ValidationError(
                f"Leave pass must be APPROVED to record departure. Current status: {leave_pass.status.value}"
            )
        
        # Update leave pass
        leave_pass.status = LeavePassStatus.DEPARTED
        leave_pass.departure_time = departure_time
        
        await self.db.commit()
        
        logger.info(
            f"Departure recorded: pass={leave_pass_id}, departure_time={departure_time}"
        )
        
        return {
            "leave_pass_id": str(leave_pass_id),
            "student_name": f"{leave_pass.student.first_name} {leave_pass.student.last_name}",
            "status": LeavePassStatus.DEPARTED.value,
            "departure_time": departure_time.isoformat(),
            "expected_return_time": leave_pass.expected_return_time.isoformat(),
            "message": f"Departure recorded at {departure_time.strftime('%H:%M')}",
        }
    
    async def record_return(
        self,
        school_id: UUID,
        leave_pass_id: UUID,
        actual_return_time: datetime,
    ) -> dict:
        """
        Record when student returns to school (at gate).
        
        Args:
            school_id: Tenant identifier
            leave_pass_id: Leave pass
            actual_return_time: When student returned
        
        Returns:
            dict with leave_pass_id, status, return_time, days_away
        
        Raises:
            NotFoundError: If leave pass not found
            ValidationError: If pass not DEPARTED
        """
        logger.debug(f"Recording return for leave pass {leave_pass_id}")
        
        # Fetch leave pass
        pass_query = select(StudentLeavePass).where(
            and_(
                StudentLeavePass.id == leave_pass_id,
                StudentLeavePass.school_id == school_id,
            )
        )
        leave_pass = await self.db.scalar(pass_query)
        
        if not leave_pass:
            raise NotFoundError(f"Leave pass {leave_pass_id} not found")
        
        # Validate status is DEPARTED
        if leave_pass.status != LeavePassStatus.DEPARTED:
            raise ValidationError(
                f"Leave pass must be DEPARTED to record return. Current status: {leave_pass.status.value}"
            )
        
        # Update leave pass
        leave_pass.status = LeavePassStatus.RETURNED
        leave_pass.actual_return_time = actual_return_time
        
        await self.db.commit()
        
        # Calculate days away
        if leave_pass.departure_time:
            days_away = (actual_return_time - leave_pass.departure_time).days
        else:
            days_away = 0
        
        logger.info(
            f"Return recorded: pass={leave_pass_id}, return_time={actual_return_time}, days_away={days_away}"
        )
        
        return {
            "leave_pass_id": str(leave_pass_id),
            "student_name": f"{leave_pass.student.first_name} {leave_pass.student.last_name}",
            "status": LeavePassStatus.RETURNED.value,
            "actual_return_time": actual_return_time.isoformat(),
            "expected_return_time": leave_pass.expected_return_time.isoformat(),
            "days_away": days_away,
            "on_time": actual_return_time <= leave_pass.expected_return_time,
            "message": f"Return recorded at {actual_return_time.strftime('%H:%M')}",
        }
    
    async def verify_gate_exit(
        self,
        school_id: UUID,
        student_id: UUID,
        current_time: datetime | None = None,
    ) -> dict:
        """
        CRITICAL SECURITY: Verify student can exit school (called by Gate/Security).
        
        Returns True ONLY if student has APPROVED leave pass for current timestamp.
        
        GATE LOGIC: Gate should allow exit only if verify_gate_exit() returns allowed=True.
        
        Args:
            school_id: Tenant identifier
            student_id: Student requesting exit
            current_time: Current datetime (default: utcnow)
        
        Returns:
            dict with allowed (bool), student_name, leave_pass_id, exeat_type,
            expected_return_time, destination, message
        """
        if current_time is None:
            current_time = datetime.utcnow()
        
        logger.debug(f"Verifying gate exit for student {student_id} at {current_time}")
        
        # Fetch most recent leave pass for student
        pass_query = select(StudentLeavePass).where(
            StudentLeavePass.student_id == student_id,
            StudentLeavePass.school_id == school_id,
        ).order_by(StudentLeavePass.requested_date.desc())
        
        result = await self.db.execute(pass_query)
        recent_passes = result.scalars().all()
        
        # Find valid pass: APPROVED and current_time <= expected_return_time
        valid_pass = None
        for pass_record in recent_passes:
            if (
                pass_record.status == LeavePassStatus.APPROVED and
                pass_record.expected_return_time and
                current_time <= pass_record.expected_return_time
            ):
                valid_pass = pass_record
                break
        
        if valid_pass:
            logger.info(
                f"Gate exit allowed: student={student_id}, pass={valid_pass.id}, "
                f"type={valid_pass.exeat_type.value}"
            )
            return {
                "allowed": True,
                "student_id": str(student_id),
                "student_name": f"{valid_pass.student.first_name} {valid_pass.student.last_name}",
                "leave_pass_id": str(valid_pass.id),
                "exeat_type": valid_pass.exeat_type.value,
                "expected_return_time": valid_pass.expected_return_time.isoformat(),
                "destination": valid_pass.destination,
                "contact_person_name": valid_pass.contact_person_name,
                "contact_person_phone": valid_pass.contact_person_phone,
                "message": f"Exit authorized - Return by {valid_pass.expected_return_time.strftime('%Y-%m-%d %H:%M')}",
            }
        else:
            # No valid pass found
            student_query = select(Student).where(
                and_(
                    Student.id == student_id,
                    Student.school_id == school_id,
                )
            )
            student = await self.db.scalar(student_query)
            
            if not student:
                reason = "Student not found"
            elif recent_passes:
                last_pass = recent_passes[0]
                if last_pass.status == LeavePassStatus.REJECTED:
                    reason = "Most recent leave pass was REJECTED"
                elif last_pass.status == LeavePassStatus.RETURNED:
                    reason = "Most recent leave pass has expired (student returned)"
                else:
                    reason = f"No valid leave pass (status: {last_pass.status.value})"
            else:
                reason = "No leave pass on record"
            
            logger.warning(f"Gate exit denied for student {student_id}: {reason}")
            
            return {
                "allowed": False,
                "student_id": str(student_id),
                "student_name": f"{student.first_name} {student.last_name}" if student else "Unknown",
                "leave_pass_id": None,
                "exeat_type": None,
                "expected_return_time": None,
                "destination": None,
                "message": f"Exit denied - {reason}",
            }
    
    async def extend_leave_pass(
        self,
        school_id: UUID,
        leave_pass_id: UUID,
        new_return_time: datetime,
        approver_user_id: UUID | None = None,
    ) -> dict:
        """
        Extend student's leave (exeat extension).
        
        Args:
            school_id: Tenant identifier
            leave_pass_id: Leave pass to extend
            new_return_time: New expected return time
            approver_user_id: User approving extension (if required)
        
        Returns:
            dict with leave_pass_id, status, new_return_time, message
        
        Raises:
            NotFoundError: If leave pass not found
            ValidationError: If pass cannot be extended
        """
        logger.debug(f"Extending leave pass {leave_pass_id} to {new_return_time}")
        
        # Fetch leave pass
        pass_query = select(StudentLeavePass).where(
            and_(
                StudentLeavePass.id == leave_pass_id,
                StudentLeavePass.school_id == school_id,
            )
        )
        leave_pass = await self.db.scalar(pass_query)
        
        if not leave_pass:
            raise NotFoundError(f"Leave pass {leave_pass_id} not found")
        
        # Validate pass can be extended (must be DEPARTED or APPROVED)
        if leave_pass.status not in [LeavePassStatus.DEPARTED, LeavePassStatus.APPROVED]:
            raise ValidationError(
                f"Cannot extend pass with status {leave_pass.status.value}"
            )
        
        # Validate new time is after current expected return
        if new_return_time <= leave_pass.expected_return_time:
            raise ValidationError(
                f"Extension time must be after current expected return time "
                f"({leave_pass.expected_return_time})"
            )
        
        # Update leave pass
        leave_pass.expected_return_time = new_return_time
        leave_pass.status = LeavePassStatus.EXTENDED
        
        await self.db.commit()
        
        logger.info(
            f"Leave pass extended: pass={leave_pass_id}, "
            f"new_return_time={new_return_time}"
        )
        
        return {
            "leave_pass_id": str(leave_pass_id),
            "student_name": f"{leave_pass.student.first_name} {leave_pass.student.last_name}",
            "status": LeavePassStatus.EXTENDED.value,
            "new_return_time": new_return_time.isoformat(),
            "message": f"Leave extension granted - New return time: {new_return_time.strftime('%Y-%m-%d %H:%M')}",
        }
    
    async def get_leave_pass(
        self,
        school_id: UUID,
        leave_pass_id: UUID,
    ) -> StudentLeavePass:
        """Get leave pass record."""
        query = select(StudentLeavePass).where(
            and_(
                StudentLeavePass.id == leave_pass_id,
                StudentLeavePass.school_id == school_id,
            )
        )
        leave_pass = await self.db.scalar(query)
        
        if not leave_pass:
            raise NotFoundError(f"Leave pass {leave_pass_id} not found")
        
        return leave_pass
    
    async def list_leave_passes(
        self,
        school_id: UUID,
        student_id: UUID | None = None,
        status: str | None = None,
    ) -> list[StudentLeavePass]:
        """List leave passes with filters."""
        query = select(StudentLeavePass).where(
            StudentLeavePass.school_id == school_id
        )
        
        if student_id:
            query = query.where(StudentLeavePass.student_id == student_id)
        
        if status:
            query = query.where(StudentLeavePass.status == LeavePassStatus(status))
        
        query = query.order_by(StudentLeavePass.requested_date.desc())
        
        result = await self.db.execute(query)
        return result.scalars().all()
    
    async def get_students_away_now(
        self,
        school_id: UUID,
        current_time: datetime | None = None,
    ) -> list[dict]:
        """
        Get list of students currently away (between departure and return).
        
        Returns:
            list of dicts with student_id, student_name, leave_pass_id, exeat_type,
            departure_time, expected_return_time
        """
        if current_time is None:
            current_time = datetime.utcnow()
        
        # Query for DEPARTED passes where expected return > current time
        query = select(StudentLeavePass).where(
            and_(
                StudentLeavePass.school_id == school_id,
                StudentLeavePass.status == LeavePassStatus.DEPARTED,
                StudentLeavePass.expected_return_time > current_time,
            )
        )
        
        result = await self.db.execute(query)
        passes = result.scalars().all()
        
        return [
            {
                "student_id": str(p.student_id),
                "student_name": f"{p.student.first_name} {p.student.last_name}",
                "leave_pass_id": str(p.id),
                "exeat_type": p.exeat_type.value,
                "departure_time": p.departure_time.isoformat() if p.departure_time else None,
                "expected_return_time": p.expected_return_time.isoformat(),
                "destination": p.destination,
            }
            for p in passes
        ]
