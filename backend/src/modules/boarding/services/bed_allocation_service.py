"""
Bed allocation service for boarding management.

CRITICAL: Manages physical bed assignments to students with strict validation.

Guarantees:
- Only BOARDER students can be assigned beds
- Only unoccupied beds can be allocated
- Atomic operations (bed occupancy status and allocation record created together)
- No overbooking or conflicts
"""

import logging
from datetime import date, datetime
from uuid import UUID

from sqlalchemy import and_, select, update
from sqlalchemy.ext.asyncio import AsyncSession

from src.core.exceptions import NotFoundError, ValidationError
from src.modules.boarding.models.boarding import Bed, BedAllocation, Hostel, Dormitory
from src.modules.admissions.models.students import Student, BoardingStatus

logger = logging.getLogger(__name__)


class BedAllocationService:
    """Service for managing bed allocations to students."""
    
    def __init__(self, db: AsyncSession):
        """Initialize with database session."""
        self.db = db
    
    async def allocate_bed(
        self,
        school_id: UUID,
        student_id: UUID,
        bed_id: UUID,
        start_date: date | None = None,
        end_date: date | None = None,
    ) -> dict:
        """
        CRITICAL ALGORITHM: Allocate physical bed to student.
        
        STRICT VALIDATION:
        1. Fetch Student, validate boarding_status is BOARDER
        2. Fetch Bed, validate NOT currently occupied
        3. Create BedAllocation record
        4. Update Bed.is_occupied = True
        5. Update Dormitory.current_occupancy += 1
        6. Update Hostel.current_occupancy += 1
        7. COMMIT ATOMICALLY - if any step fails, ROLLBACK all
        
        Args:
            school_id: Tenant identifier
            student_id: Student to allocate
            bed_id: Bed to allocate
            start_date: Allocation start (default: today)
            end_date: Allocation end (null if ongoing)
        
        Returns:
            dict with allocation_id, student_name, bed_details, location, message
        
        Raises:
            NotFoundError: If student or bed not found
            ValidationError: If student not BOARDER, or bed already occupied, or date conflict
        """
        if start_date is None:
            start_date = date.today()
        
        logger.debug(f"Allocating bed {bed_id} to student {student_id}")
        
        # STEP 1: Fetch Student, validate boarding_status
        student_query = select(Student).where(
            and_(
                Student.id == student_id,
                Student.school_id == school_id,
            )
        )
        student = await self.db.scalar(student_query)
        
        if not student:
            logger.warning(f"Student {student_id} not found in school {school_id}")
            raise NotFoundError(f"Student {student_id} not found")
        
        # Validate boarding status
        if student.boarding_status != BoardingStatus.BOARDING:
            logger.warning(
                f"Student {student_id} has boarding_status {student.boarding_status}, not BOARDING"
            )
            raise ValidationError(
                f"Student {student.first_name} {student.last_name} is not a BOARDING student. "
                f"Current status: {student.boarding_status.value}"
            )
        
        logger.debug(f"Student {student_id} validated as BOARDING: {student.first_name} {student.last_name}")
        
        # STEP 2: Fetch Bed with relationships, validate NOT occupied
        bed_query = select(Bed).where(
            and_(
                Bed.id == bed_id,
                Bed.school_id == school_id,
            )
        ).options(
            # Eager load dormitory to get dormitory details
        )
        bed = await self.db.scalar(bed_query)
        
        if not bed:
            logger.warning(f"Bed {bed_id} not found in school {school_id}")
            raise NotFoundError(f"Bed {bed_id} not found")
        
        # Validate bed is not occupied
        if bed.is_occupied:
            logger.warning(f"Bed {bed_id} ({bed.bed_number}) is already occupied")
            raise ValidationError(
                f"Bed {bed.bed_number} is already occupied. "
                f"Please select a different bed."
            )
        
        # Validate bed is active
        if not bed.is_active:
            logger.warning(f"Bed {bed_id} ({bed.bed_number}) is not active")
            raise ValidationError(
                f"Bed {bed.bed_number} is not available for allocation."
            )
        
        logger.debug(f"Bed {bed_id} validated: {bed.bed_number}, is_occupied={bed.is_occupied}")
        
        # STEP 3: Check for existing active allocation for this student
        # A student should not have two overlapping allocations
        existing_query = select(BedAllocation).where(
            and_(
                BedAllocation.student_id == student_id,
                BedAllocation.school_id == school_id,
                BedAllocation.is_active,
                # Active allocation: no end_date or end_date >= requested start_date
                (
                    (BedAllocation.end_date.is_(None)) |
                    (BedAllocation.end_date >= start_date)
                ),
            )
        )
        existing_allocation = await self.db.scalar(existing_query)
        
        if existing_allocation:
            logger.warning(
                f"Student {student_id} already has active allocation in bed {existing_allocation.bed_id}"
            )
            raise ValidationError(
                f"Student already has an active bed allocation. "
                f"Please deallocate the previous bed before assigning a new one."
            )
        
        # STEP 4: Create BedAllocation record
        allocation = BedAllocation(
            school_id=school_id,
            student_id=student_id,
            bed_id=bed_id,
            start_date=start_date,
            end_date=end_date,
            is_active=True,
        )
        self.db.add(allocation)
        await self.db.flush()  # Get allocation ID without committing
        
        logger.debug(f"Created BedAllocation record: {allocation.id}")
        
        # STEP 5: Update Bed.is_occupied = True
        bed.is_occupied = True
        logger.debug(f"Updated Bed {bed_id}: is_occupied=True")
        
        # STEP 6: Update Dormitory occupancy
        dormitory_query = select(Dormitory).where(
            Dormitory.id == bed.dormitory_id
        )
        dormitory = await self.db.scalar(dormitory_query)
        
        if dormitory:
            dormitory.current_occupancy += 1
            logger.debug(
                f"Updated Dormitory {dormitory.id}: current_occupancy={dormitory.current_occupancy}"
            )
        
        # STEP 7: Update Hostel occupancy
        hostel_query = select(Hostel).where(
            Hostel.id == dormitory.hostel_id
        )
        hostel = await self.db.scalar(hostel_query)
        
        if hostel:
            hostel.current_occupancy += 1
            logger.debug(
                f"Updated Hostel {hostel.id}: current_occupancy={hostel.current_occupancy}"
            )
        
        # STEP 8: Commit atomically
        try:
            await self.db.commit()
            logger.info(
                f"Bed allocation successful: student={student_id}, bed={bed_id}, "
                f"location={hostel.name}-{dormitory.name}-{bed.bed_number}"
            )
        except Exception as e:
            logger.error(f"Error committing bed allocation: {e}")
            await self.db.rollback()
            raise
        
        # STEP 9: Return summary
        return {
            "allocation_id": str(allocation.id),
            "student_id": str(student_id),
            "student_name": f"{student.first_name} {student.last_name}",
            "bed_id": str(bed_id),
            "bed_number": bed.bed_number,
            "dormitory_name": dormitory.name,
            "hostel_name": hostel.name,
            "start_date": start_date.isoformat(),
            "end_date": end_date.isoformat() if end_date else None,
            "location": f"{hostel.name} - {dormitory.name} - {bed.bed_number}",
            "message": f"Student {student.first_name} {student.last_name} "
                      f"successfully allocated to bed {bed.bed_number} "
                      f"in {hostel.name}, {dormitory.name}",
        }
    
    async def deallocate_bed(
        self,
        school_id: UUID,
        allocation_id: UUID,
        end_date: date | None = None,
    ) -> dict:
        """
        Deallocate bed from student (end allocation).
        
        Args:
            school_id: Tenant identifier
            allocation_id: Allocation to end
            end_date: Deallocation date (default: today)
        
        Returns:
            dict with success message
        
        Raises:
            NotFoundError: If allocation not found
        """
        if end_date is None:
            end_date = date.today()
        
        logger.debug(f"Deallocating bed for allocation {allocation_id}")
        
        # Fetch allocation
        allocation_query = select(BedAllocation).where(
            and_(
                BedAllocation.id == allocation_id,
                BedAllocation.school_id == school_id,
            )
        )
        allocation = await self.db.scalar(allocation_query)
        
        if not allocation:
            logger.warning(f"Allocation {allocation_id} not found")
            raise NotFoundError(f"Allocation {allocation_id} not found")
        
        # Fetch bed and dormitory
        bed_query = select(Bed).where(Bed.id == allocation.bed_id)
        bed = await self.db.scalar(bed_query)
        
        dormitory_query = select(Dormitory).where(
            Dormitory.id == bed.dormitory_id
        )
        dormitory = await self.db.scalar(dormitory_query)
        
        hostel_query = select(Hostel).where(Hostel.id == dormitory.hostel_id)
        hostel = await self.db.scalar(hostel_query)
        
        # Update allocation
        allocation.end_date = end_date
        allocation.is_active = False
        
        # Update bed occupancy (only if no other active allocations exist)
        other_active = await self.db.scalar(
            select(BedAllocation).where(
                and_(
                    BedAllocation.bed_id == bed.id,
                    BedAllocation.is_active,
                    BedAllocation.id != allocation_id,
                )
            )
        )
        
        if not other_active:
            bed.is_occupied = False
            dormitory.current_occupancy = max(0, dormitory.current_occupancy - 1)
            hostel.current_occupancy = max(0, hostel.current_occupancy - 1)
            logger.debug(f"Bed {bed.id} released: is_occupied=False")
        
        await self.db.commit()
        logger.info(f"Bed deallocation successful for allocation {allocation_id}")
        
        return {
            "allocation_id": str(allocation_id),
            "bed_number": bed.bed_number,
            "end_date": end_date.isoformat(),
            "message": f"Bed {bed.bed_number} successfully deallocated",
        }
    
    async def get_allocation(
        self,
        school_id: UUID,
        allocation_id: UUID,
    ) -> BedAllocation:
        """Get bed allocation record."""
        query = select(BedAllocation).where(
            and_(
                BedAllocation.id == allocation_id,
                BedAllocation.school_id == school_id,
            )
        )
        allocation = await self.db.scalar(query)
        
        if not allocation:
            raise NotFoundError(f"Allocation {allocation_id} not found")
        
        return allocation
    
    async def get_student_allocation(
        self,
        school_id: UUID,
        student_id: UUID,
        active_only: bool = True,
    ) -> BedAllocation | None:
        """
        Get student's bed allocation.
        
        Args:
            school_id: Tenant identifier
            student_id: Student to query
            active_only: Only return active allocations
        
        Returns:
            BedAllocation or None if not allocated
        """
        query = select(BedAllocation).where(
            and_(
                BedAllocation.student_id == student_id,
                BedAllocation.school_id == school_id,
            )
        )
        
        if active_only:
            query = query.where(BedAllocation.is_active)
        
        query = query.order_by(BedAllocation.start_date.desc())
        
        return await self.db.scalar(query)
    
    async def list_allocations(
        self,
        school_id: UUID,
        dormitory_id: UUID | None = None,
        active_only: bool = False,
    ) -> list[BedAllocation]:
        """List bed allocations with filters."""
        query = select(BedAllocation).where(
            BedAllocation.school_id == school_id
        )
        
        if dormitory_id:
            # Join with bed to filter by dormitory
            query = query.join(Bed).where(
                Bed.dormitory_id == dormitory_id
            )
        
        if active_only:
            query = query.where(BedAllocation.is_active)
        
        query = query.order_by(BedAllocation.created_at.desc())
        
        result = await self.db.execute(query)
        return result.scalars().all()
    
    async def get_bed_status(
        self,
        school_id: UUID,
        bed_id: UUID,
    ) -> dict:
        """
        Get current bed status and occupancy info.
        
        Returns:
            dict with bed_id, bed_number, is_occupied, current_occupant (name, id, since date)
        """
        bed_query = select(Bed).where(
            and_(
                Bed.id == bed_id,
                Bed.school_id == school_id,
            )
        )
        bed = await self.db.scalar(bed_query)
        
        if not bed:
            raise NotFoundError(f"Bed {bed_id} not found")
        
        current_occupant = None
        if bed.is_occupied:
            # Get current active allocation
            allocation_query = select(BedAllocation).where(
                and_(
                    BedAllocation.bed_id == bed_id,
                    BedAllocation.is_active,
                    (BedAllocation.end_date.is_(None)) |
                    (BedAllocation.end_date >= date.today()),
                )
            ).order_by(BedAllocation.start_date.desc())
            
            allocation = await self.db.scalar(allocation_query)
            if allocation and allocation.student:
                current_occupant = {
                    "student_id": str(allocation.student_id),
                    "student_name": f"{allocation.student.first_name} {allocation.student.last_name}",
                    "admission_number": allocation.student.admission_number,
                    "since": allocation.start_date.isoformat(),
                }
        
        return {
            "bed_id": str(bed_id),
            "bed_number": bed.bed_number,
            "is_occupied": bed.is_occupied,
            "is_active": bed.is_active,
            "current_occupant": current_occupant,
        }
    
    async def get_hostel_occupancy(
        self,
        school_id: UUID,
        hostel_id: UUID,
    ) -> dict:
        """Get hostel occupancy statistics."""
        hostel_query = select(Hostel).where(
            and_(
                Hostel.id == hostel_id,
                Hostel.school_id == school_id,
            )
        )
        hostel = await self.db.scalar(hostel_query)
        
        if not hostel:
            raise NotFoundError(f"Hostel {hostel_id} not found")
        
        occupancy_rate = (
            (hostel.current_occupancy / hostel.capacity * 100)
            if hostel.capacity > 0
            else 0
        )
        
        return {
            "hostel_id": str(hostel_id),
            "hostel_name": hostel.name,
            "capacity": hostel.capacity,
            "current_occupancy": hostel.current_occupancy,
            "available_beds": hostel.capacity - hostel.current_occupancy,
            "occupancy_rate": round(occupancy_rate, 2),
        }
