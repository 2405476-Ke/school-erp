"""
Leave Management Service for staff leave requests, approvals, and biometric attendance.

Implements:
- Two-tier leave approval workflow (Deputy Principal -> Principal)
- Leave balance deduction on final approval
- Biometric attendance recording
"""

import logging
from datetime import datetime, date, timezone
from decimal import Decimal
from uuid import UUID

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from src.shared.exceptions import NotFoundError, ValidationError
from src.modules.hr.models.hr_leave import (
    LeaveRequest,
    LeaveBalance,
    AttendanceRecord,
    LeaveType,
    LeaveStatus,
)

logger = logging.getLogger(__name__)


def _utcnow() -> datetime:
    """Return current UTC datetime."""
    return datetime.now(timezone.utc)


class LeaveService:
    """
    Service for managing staff leave requests and biometric attendance.

    Leave Approval Workflow:
        PENDING -> (Deputy Principal) -> APPROVED_TIER1 -> (Principal) -> APPROVED
        PENDING / APPROVED_TIER1 -> (any approver) -> REJECTED
    """

    def __init__(self, db: AsyncSession):
        self.db = db

    async def submit_leave_request(
        self,
        school_id: UUID,
        staff_id: UUID,
        leave_type: LeaveType,
        from_date: date,
        to_date: date,
        reason: str,
    ) -> LeaveRequest:
        """
        Submit a new leave request on behalf of a staff member.

        Validates that from_date <= to_date, then creates a LeaveRequest
        in PENDING status awaiting Tier 1 (Deputy Principal) approval.

        Args:
            school_id: Tenant school identifier.
            staff_id: UUID of the staff member applying.
            leave_type: Type of leave (ANNUAL, SICK, etc.).
            from_date: First day of requested leave.
            to_date: Last day of requested leave (inclusive).
            reason: Staff-provided reason for the leave.

        Returns:
            The newly created LeaveRequest instance.

        Raises:
            ValidationError: If from_date is after to_date or reason is empty.
        """
        if from_date > to_date:
            raise ValidationError(
                f"from_date ({from_date}) cannot be after to_date ({to_date})"
            )
        if not reason or not reason.strip():
            raise ValidationError("A reason must be provided for the leave request")

        request = LeaveRequest(
            school_id=school_id,
            staff_id=staff_id,
            leave_type=leave_type,
            from_date=from_date,
            to_date=to_date,
            reason=reason.strip(),
            status=LeaveStatus.PENDING,
        )
        self.db.add(request)
        await self.db.flush()

        logger.info(
            "Leave request submitted: staff=%s type=%s from=%s to=%s",
            staff_id,
            leave_type,
            from_date,
            to_date,
        )
        return request

    async def approve_leave_tier1(
        self,
        request_id: UUID,
        approver_id: UUID,
    ) -> LeaveRequest:
        """
        Tier 1 (Deputy Principal) approval of a leave request.

        Moves the request from PENDING -> APPROVED_TIER1.

        Args:
            request_id: UUID of the LeaveRequest.
            approver_id: UUID of the Deputy Principal approving.

        Returns:
            Updated LeaveRequest.

        Raises:
            NotFoundError: If the request does not exist.
            ValidationError: If the request is not in PENDING status.
        """
        request = await self.db.get(LeaveRequest, request_id)
        if not request:
            raise NotFoundError(f"Leave request {request_id} not found")

        if request.status != LeaveStatus.PENDING:
            raise ValidationError(
                f"Tier 1 approval requires PENDING status, got {request.status}"
            )

        request.status = LeaveStatus.APPROVED_TIER1
        request.tier1_approved_by_id = approver_id
        request.tier1_approved_at = _utcnow()

        logger.info(
            "Leave request %s approved at Tier 1 by %s", request_id, approver_id
        )
        return request

    async def approve_leave_tier2(
        self,
        request_id: UUID,
        approver_id: UUID,
    ) -> LeaveRequest:
        """
        Tier 2 (Principal) final approval of a leave request.

        Moves the request from APPROVED_TIER1 -> APPROVED and deducts
        the consumed days from the staff member's LeaveBalance for the year.

        Args:
            request_id: UUID of the LeaveRequest.
            approver_id: UUID of the Principal approving.

        Returns:
            Updated LeaveRequest.

        Raises:
            NotFoundError: If the request or leave balance does not exist.
            ValidationError: If the request is not in APPROVED_TIER1 status,
                             or if the staff member has insufficient leave days.
        """
        request = await self.db.get(LeaveRequest, request_id)
        if not request:
            raise NotFoundError(f"Leave request {request_id} not found")

        if request.status != LeaveStatus.APPROVED_TIER1:
            raise ValidationError(
                f"Tier 2 approval requires APPROVED_TIER1 status, got {request.status}"
            )

        # Calculate calendar days consumed (inclusive)
        delta = (request.to_date - request.from_date).days + 1
        days_consumed = Decimal(str(delta))

        # Fetch leave balance for the year
        year = request.from_date.year
        balance = await self.db.scalar(
            select(LeaveBalance).where(
                LeaveBalance.school_id == request.school_id,
                LeaveBalance.staff_id == request.staff_id,
                LeaveBalance.year == year,
                LeaveBalance.leave_type == request.leave_type,
            )
        )

        if not balance:
            raise NotFoundError(
                f"No leave balance found for staff {request.staff_id}, "
                f"year {year}, type {request.leave_type}"
            )

        remaining = balance.entitled_days - balance.used_days
        if days_consumed > remaining:
            raise ValidationError(
                f"Insufficient leave balance: requested {days_consumed} day(s) but "
                f"only {remaining} remaining for {request.leave_type} in {year}"
            )

        # Deduct consumed days from balance
        balance.used_days += days_consumed

        # Fully approve the request
        request.status = LeaveStatus.APPROVED
        request.tier2_approved_by_id = approver_id
        request.tier2_approved_at = _utcnow()

        logger.info(
            "Leave request %s fully approved by %s; deducted %.1f day(s) from balance",
            request_id,
            approver_id,
            days_consumed,
        )
        return request

    async def reject_leave(
        self,
        request_id: UUID,
        approver_id: UUID,
        reason: str,
    ) -> LeaveRequest:
        """
        Reject a pending or tier-1-approved leave request.

        Moves the request to REJECTED status and records the rejection reason.

        Args:
            request_id: UUID of the LeaveRequest.
            approver_id: UUID of the user rejecting the request.
            reason: Mandatory reason for rejection.

        Returns:
            Updated LeaveRequest.

        Raises:
            NotFoundError: If the request does not exist.
            ValidationError: If the request is already finalised (APPROVED,
                             CANCELLED, or REJECTED), or if no reason is provided.
        """
        if not reason or not reason.strip():
            raise ValidationError("A rejection reason must be provided")

        request = await self.db.get(LeaveRequest, request_id)
        if not request:
            raise NotFoundError(f"Leave request {request_id} not found")

        if request.status in (
            LeaveStatus.APPROVED,
            LeaveStatus.CANCELLED,
            LeaveStatus.REJECTED,
        ):
            raise ValidationError(
                f"Cannot reject a request in status {request.status}"
            )

        request.status = LeaveStatus.REJECTED
        request.rejection_reason = reason.strip()

        logger.info(
            "Leave request %s rejected by %s: %s", request_id, approver_id, reason
        )
        return request

    async def record_biometric_attendance(
        self,
        school_id: UUID,
        staff_id: UUID,
        clock_in_time: datetime,
        device_id: str,
    ) -> AttendanceRecord:
        """
        Record a biometric clock-in event for a staff member.

        Idempotent: if an AttendanceRecord already exists for the date,
        the existing record is returned unchanged.

        Args:
            school_id: Tenant school identifier.
            staff_id: UUID of the staff member.
            clock_in_time: Exact datetime from the biometric device.
            device_id: Identifier of the biometric terminal.

        Returns:
            New or existing AttendanceRecord for that date.
        """
        attendance_date = clock_in_time.date()

        # Idempotency check: return existing record if already present
        existing = await self.db.scalar(
            select(AttendanceRecord).where(
                AttendanceRecord.school_id == school_id,
                AttendanceRecord.staff_id == staff_id,
                AttendanceRecord.attendance_date == attendance_date,
            )
        )
        if existing:
            logger.debug(
                "Attendance record already exists for staff=%s date=%s; returning existing",
                staff_id,
                attendance_date,
            )
            return existing

        record = AttendanceRecord(
            school_id=school_id,
            staff_id=staff_id,
            attendance_date=attendance_date,
            clock_in=clock_in_time,
            clock_out=None,
            source="BIOMETRIC",
            biometric_device_id=device_id,
            is_present=True,
        )
        self.db.add(record)
        await self.db.flush()

        logger.info(
            "Biometric attendance recorded: staff=%s date=%s device=%s",
            staff_id,
            attendance_date,
            device_id,
        )
        return record