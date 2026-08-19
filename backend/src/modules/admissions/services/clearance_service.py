"""
Student Clearance Service.

Handles exit clearance for students (graduation, transfer, withdrawal).
CRITICAL: Must check Finance (fee balance), Library (unreturned books), Sports (unreturned gear).
"""

import logging
from uuid import UUID
from datetime import datetime

from sqlalchemy import and_, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from src.core.exceptions import NotFoundError, ValidationError
from src.modules.admissions.models.students import (
    Student,
    StudentClearance,
    ClearanceStatus,
)

logger = logging.getLogger(__name__)


class ClearanceService:
    """
    Service for student exit clearance.
    
    Checks:
    1. Finance: Unpaid fees or balances
    2. Library: Unreturned library books
    3. Sports: Unreturned sports gear (if applicable)
    """
    
    def __init__(self, db: AsyncSession):
        self.db = db
    
    async def initiate_clearance(
        self,
        school_id: UUID,
        student_id: UUID,
        fee_service: "FeeAccountService",
        library_service: "LibraryService" | None = None,
        sports_service: "SportsService" | None = None,
    ) -> dict:
        """
        CRITICAL ALGORITHM: Initiate student clearance.
        
        Steps:
        1. Fetch Student, validate active
        2. Check Finance: Get fee balance from FeeAccountService
           - Query FeeAccount for student
           - Calculate balance (total invoice amount - total received)
           - has_fee_balance = True if balance > 0
        3. Check Library: Get unreturned books from LibraryService
           - Query library transactions for student
           - Look for unreturned book items
           - has_library_books = True if any unreturned
        4. Check Sports: Get unreturned sports gear
           - Query sports inventory for student
           - Look for unreturned items
           - has_sports_gear = True if any unreturned
        5. Create StudentClearance record
           - Set status to CLEARED if all checks pass
           - Set to PARTIALLY_CLEARED if any items/balances exist
        6. Return clearance summary with required actions
        
        Args:
            school_id: Tenant ID
            student_id: Student ID
            fee_service: Finance service for fee account queries
            library_service: Library service for book queries (optional)
            sports_service: Sports service for gear queries (optional)
            
        Returns:
            Dictionary with clearance details and required actions
        """
        logger.info(f"Initiating clearance for student {student_id}")
        
        # Step 1: Fetch Student
        student_query = select(Student).where(
            and_(
                Student.id == student_id,
                Student.school_id == school_id,
            )
        )
        student = await self.db.scalar(student_query)
        
        if not student:
            raise NotFoundError(f"Student {student_id} not found")
        
        if not student.is_active:
            raise ValidationError(f"Cannot clear inactive student {student.admission_number}")
        
        logger.info(f"✓ Found student: {student.first_name} {student.last_name}")
        
        # Step 2: Check Finance - Fee Balance
        has_fee_balance = False
        fee_balance_amount = None
        
        try:
            fee_account = await fee_service.get_fee_account(
                school_id=school_id,
                student_id=student_id,
            )
            
            if fee_account:
                # Calculate balance: Total Invoiced - Total Received Payments
                fee_balance_amount = fee_account.balance
                has_fee_balance = fee_balance_amount > 0
                
                logger.info(f"✓ Fee account balance: {fee_balance_amount}, has_balance: {has_fee_balance}")
            
        except Exception as e:
            logger.error(f"Error checking fee balance: {e}")
            # If fee service fails, assume balance exists to be safe
            has_fee_balance = True
            fee_balance_amount = None
        
        # Step 3: Check Library - Unreturned Books
        has_library_books = False
        unreturned_books_count = 0
        
        if library_service:
            try:
                unreturned_books = await library_service.get_unreturned_books(
                    school_id=school_id,
                    student_id=student_id,
                )
                
                has_library_books = len(unreturned_books) > 0
                unreturned_books_count = len(unreturned_books)
                
                logger.info(f"✓ Unreturned library books: {unreturned_books_count}, has_books: {has_library_books}")
                
            except Exception as e:
                logger.error(f"Error checking library books: {e}")
                # If library service fails, assume books exist to be safe
                has_library_books = True
        
        # Step 4: Check Sports - Unreturned Gear
        has_sports_gear = False
        unreturned_gear_count = 0
        
        if sports_service:
            try:
                unreturned_gear = await sports_service.get_unreturned_gear(
                    school_id=school_id,
                    student_id=student_id,
                )
                
                has_sports_gear = len(unreturned_gear) > 0
                unreturned_gear_count = len(unreturned_gear)
                
                logger.info(f"✓ Unreturned sports gear: {unreturned_gear_count}, has_gear: {has_sports_gear}")
                
            except Exception as e:
                logger.error(f"Error checking sports gear: {e}")
                # If sports service fails, assume gear exists to be safe
                has_sports_gear = True
        
        # Step 5: Create StudentClearance record
        clearance_status = ClearanceStatus.CLEARED
        if has_fee_balance or has_library_books or has_sports_gear:
            clearance_status = ClearanceStatus.PARTIALLY_CLEARED
        
        clearance = StudentClearance(
            school_id=school_id,
            student_id=student_id,
            status=clearance_status,
            initiated_date=datetime.utcnow(),
            has_fee_balance=has_fee_balance,
            has_library_books=has_library_books,
            has_sports_gear=has_sports_gear,
            remarks="Clearance initiated - awaiting resolution",
        )
        
        self.db.add(clearance)
        await self.db.commit()
        
        logger.info(f"✓ Created StudentClearance: {clearance.id}, status: {clearance_status}")
        
        # Step 6: Return clearance summary
        required_actions = []
        if has_fee_balance:
            required_actions.append(f"Pay outstanding fees: {fee_balance_amount}")
        if has_library_books:
            required_actions.append(f"Return {unreturned_books_count} library book(s)")
        if has_sports_gear:
            required_actions.append(f"Return {unreturned_gear_count} sports item(s)")
        
        clearance_required = len(required_actions) > 0
        
        return {
            "clearance_id": str(clearance.id),
            "student_id": str(student_id),
            "student_name": f"{student.first_name} {student.last_name}",
            "admission_number": student.admission_number,
            "status": clearance_status.value,
            "initiated_date": clearance.initiated_date.isoformat(),
            "has_fee_balance": has_fee_balance,
            "fee_balance_amount": str(fee_balance_amount) if fee_balance_amount else None,
            "has_library_books": has_library_books,
            "unreturned_books_count": unreturned_books_count,
            "has_sports_gear": has_sports_gear,
            "unreturned_gear_count": unreturned_gear_count,
            "clearance_required": clearance_required,
            "required_actions": required_actions,
            "message": "Clearance initiated" if not clearance_required else "Clearance required - actions needed",
        }
    
    async def get_clearance(
        self,
        school_id: UUID,
        clearance_id: UUID,
    ) -> StudentClearance:
        """Fetch clearance record."""
        query = select(StudentClearance).where(
            and_(
                StudentClearance.id == clearance_id,
                StudentClearance.school_id == school_id,
            )
        ).options(
            selectinload(StudentClearance.student),
        )
        
        clearance = await self.db.scalar(query)
        
        if not clearance:
            raise NotFoundError(f"StudentClearance {clearance_id} not found")
        
        return clearance
    
    async def get_student_clearances(
        self,
        school_id: UUID,
        student_id: UUID,
    ) -> list[StudentClearance]:
        """Get all clearance records for student."""
        query = select(StudentClearance).where(
            and_(
                StudentClearance.school_id == school_id,
                StudentClearance.student_id == student_id,
            )
        ).order_by(StudentClearance.initiated_date.desc())
        
        result = await self.db.execute(query)
        return result.scalars().all()
    
    async def mark_fee_cleared(
        self,
        school_id: UUID,
        clearance_id: UUID,
    ) -> StudentClearance:
        """Mark fees as cleared in clearance record."""
        clearance = await self.get_clearance(school_id, clearance_id)
        
        clearance.has_fee_balance = False
        
        # Update overall status
        if not clearance.has_library_books and not clearance.has_sports_gear:
            clearance.status = ClearanceStatus.CLEARED
            clearance.cleared_date = datetime.utcnow()
            logger.info(f"Clearance {clearance_id} fully cleared")
        else:
            clearance.status = ClearanceStatus.PARTIALLY_CLEARED
            logger.info(f"Clearance {clearance_id} partially cleared")
        
        await self.db.commit()
        return clearance
    
    async def mark_library_cleared(
        self,
        school_id: UUID,
        clearance_id: UUID,
    ) -> StudentClearance:
        """Mark library books as cleared in clearance record."""
        clearance = await self.get_clearance(school_id, clearance_id)
        
        clearance.has_library_books = False
        
        # Update overall status
        if not clearance.has_fee_balance and not clearance.has_sports_gear:
            clearance.status = ClearanceStatus.CLEARED
            clearance.cleared_date = datetime.utcnow()
            logger.info(f"Clearance {clearance_id} fully cleared")
        else:
            clearance.status = ClearanceStatus.PARTIALLY_CLEARED
            logger.info(f"Clearance {clearance_id} partially cleared")
        
        await self.db.commit()
        return clearance
    
    async def mark_sports_cleared(
        self,
        school_id: UUID,
        clearance_id: UUID,
    ) -> StudentClearance:
        """Mark sports gear as cleared in clearance record."""
        clearance = await self.get_clearance(school_id, clearance_id)
        
        clearance.has_sports_gear = False
        
        # Update overall status
        if not clearance.has_fee_balance and not clearance.has_library_books:
            clearance.status = ClearanceStatus.CLEARED
            clearance.cleared_date = datetime.utcnow()
            logger.info(f"Clearance {clearance_id} fully cleared")
        else:
            clearance.status = ClearanceStatus.PARTIALLY_CLEARED
            logger.info(f"Clearance {clearance_id} partially cleared")
        
        await self.db.commit()
        return clearance
