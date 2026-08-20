from uuid import UUID
from decimal import Decimal
from typing import List, Optional
from datetime import date, datetime
from sqlalchemy import select, and_
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from src.modules.boarding.models.boarding import (
    Hostel, Dormitory, Bed, BedAllocation, 
    SickbayAdmission, StudentLeavePass, LeavePassStatus,
    DisciplinaryIncident, DisciplinaryAction
)


class BoardingService:
    """
    Service layer for the Boarding module.
    Handles: bed allocation, muster roll, sickbay, and disciplinary workflows.
    """
    
    def __init__(self, db: AsyncSession):
        self.db = db

    # ── BR-BRD-001: Hostel Infrastructure ──────────────────────
    async def get_hostel_overview(self, school_id: UUID) -> List[dict]:
        """Returns all hostels with dormitory and bed capacity breakdown."""
        hostels = await self.db.execute(
            select(Hostel)
            .options(selectinload(Hostel.dormitories).selectinload(Dormitory.beds))
            .where(Hostel.school_id == school_id, Hostel.is_active == True)
        )
        result = []
        for hostel in hostels.scalars().all():
            total_beds = sum(len(d.beds) for d in hostel.dormitories)
            occupied = sum(1 for d in hostel.dormitories for b in d.beds if b.is_occupied)
            result.append({
                "id": str(hostel.id),
                "name": hostel.name,
                "code": getattr(hostel, 'code', ''),
                "total_capacity": total_beds,
                "occupied": occupied,
                "available": total_beds - occupied,
                "utilization_pct": round((occupied / total_beds * 100) if total_beds > 0 else 0, 1),
                "dormitories": [
                    {"name": d.name, "capacity": len(d.beds), "occupied": sum(1 for b in d.beds if b.is_occupied)}
                    for d in hostel.dormitories
                ]
            })
        return result

    # ── BR-BRD-002: Bed Allocation ──────────────────────────────
    async def allocate_bed(self, school_id: UUID, student_id: UUID, bed_id: UUID, 
                           start_date: date, allocated_by_id: UUID) -> BedAllocation:
        """
        Allocates a specific bed to a student.
        Guards against overbooking (BR-BRD-002).
        """
        # Check bed is not already occupied
        bed = await self.db.scalar(select(Bed).where(Bed.id == bed_id, Bed.school_id == school_id))
        if not bed:
            raise ValueError("Bed not found")
        if bed.is_occupied:
            raise ValueError(f"Bed {bed.bed_number} is already occupied. Cannot overbook.")
        
        # Check student doesn't already have an active allocation
        existing = await self.db.scalar(
            select(BedAllocation).where(
                BedAllocation.student_id == student_id,
                BedAllocation.school_id == school_id,
                BedAllocation.is_active == True
            )
        )
        if existing:
            raise ValueError("Student already has an active bed allocation. Deallocate first.")
        
        allocation = BedAllocation(
            school_id=school_id,
            student_id=student_id,
            bed_id=bed_id,
            start_date=start_date,
            is_active=True
        )
        self.db.add(allocation)
        bed.is_occupied = True
        await self.db.commit()
        return allocation

    # ── BR-BRD-003: Muster Roll ─────────────────────────────────
    async def get_muster_roll(self, school_id: UUID, roll_date: date) -> dict:
        """
        Real-time muster roll: returns all boarders and their location status.
        Automatically excludes sickbay students from the 'Unaccounted' bucket.
        """
        # Get all active allocations (all boarders)
        allocations = await self.db.execute(
            select(BedAllocation)
            .options(selectinload(BedAllocation.bed).selectinload(Bed.dormitory).selectinload(Dormitory.hostel))
            .where(BedAllocation.school_id == school_id, BedAllocation.is_active == True)
        )
        boarders = allocations.scalars().all()
        
        # Get students on authorized leave (departed, not yet returned)
        on_leave_passes = await self.db.execute(
            select(StudentLeavePass).where(
                StudentLeavePass.school_id == school_id,
                StudentLeavePass.status == LeavePassStatus.DEPARTED.value
            )
        )
        on_leave_ids = {str(p.student_id) for p in on_leave_passes.scalars().all()}
        
        # Get students in sickbay
        sickbay_admissions = await self.db.execute(
            select(SickbayAdmission).where(
                SickbayAdmission.school_id == school_id,
                SickbayAdmission.is_active == True
            )
        )
        sickbay_ids = {str(s.student_id) for s in sickbay_admissions.scalars().all()}
        
        students = []
        counts = {"in_dorm": 0, "on_leave": 0, "sickbay": 0, "unaccounted": 0}
        
        for alloc in boarders:
            sid = str(alloc.student_id)
            bed = alloc.bed
            dorm_name = f"{bed.dormitory.hostel.name} / {bed.dormitory.name} / Bed {bed.bed_number}"
            
            if sid in sickbay_ids:
                status = "Sickbay"
                counts["sickbay"] += 1
            elif sid in on_leave_ids:
                status = "On Leave"
                counts["on_leave"] += 1
            else:
                # TODO: Could integrate biometric check-in here
                status = "In Dorm"
                counts["in_dorm"] += 1
            
            students.append({
                "student_id": sid,
                "dorm_location": dorm_name,
                "status": status
            })
        
        return {
            "date": str(roll_date),
            "recorded_time": datetime.now().strftime("%H:%M"),
            "summary": counts,
            "students": students
        }

    # ── BR-BRD-004: Sickbay Admission ──────────────────────────
    async def admit_to_sickbay(self, school_id: UUID, student_id: UUID, 
                                nurse_staff_id: UUID, diagnosis_notes: str,
                                expected_discharge: Optional[date] = None) -> SickbayAdmission:
        """
        Nurse flags a student as admitted to sickbay.
        Immediately removes student from dormitory muster roll (BR-BRD-004).
        """
        # Check not already admitted
        existing = await self.db.scalar(
            select(SickbayAdmission).where(
                SickbayAdmission.student_id == student_id,
                SickbayAdmission.school_id == school_id,
                SickbayAdmission.is_active == True
            )
        )
        if existing:
            raise ValueError("Student is already admitted to sickbay.")
        
        admission = SickbayAdmission(
            school_id=school_id,
            student_id=student_id,
            admitted_by_staff_id=nurse_staff_id,
            admitted_at=datetime.now(),
            diagnosis_notes=diagnosis_notes,
            expected_discharge_date=expected_discharge,
            is_active=True
        )
        self.db.add(admission)
        await self.db.commit()
        return admission

    async def discharge_from_sickbay(self, school_id: UUID, student_id: UUID) -> SickbayAdmission:
        """Discharge a student from sickbay, restoring them to the muster roll."""
        admission = await self.db.scalar(
            select(SickbayAdmission).where(
                SickbayAdmission.student_id == student_id,
                SickbayAdmission.school_id == school_id,
                SickbayAdmission.is_active == True
            )
        )
        if not admission:
            raise ValueError("No active sickbay admission found for this student.")
        
        admission.is_active = False
        admission.discharged_at = datetime.now()
        await self.db.commit()
        return admission

    # ── BR-BRD-005: Disciplinary Infractions ──────────────────
    async def log_disciplinary_incident(self, school_id: UUID, student_id: UUID,
                                         reported_by_staff_id: UUID, category: str,
                                         description: str, incident_date: date,
                                         location: str, severity: int) -> DisciplinaryIncident:
        """
        Records a disciplinary infraction linked to a student's profile (BR-BRD-005).
        """
        incident = DisciplinaryIncident(
            school_id=school_id,
            student_id=student_id,
            category=category,
            description=description,
            incident_date=incident_date,
            reported_by_staff_id=reported_by_staff_id,
            location=location,
            severity=max(1, min(5, severity))  # Clamp to 1–5
        )
        self.db.add(incident)
        await self.db.commit()
        return incident
