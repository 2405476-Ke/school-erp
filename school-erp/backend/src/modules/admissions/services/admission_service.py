"""
Admission Service for student onboarding and lifecycle.

CRITICAL ALGORITHMS:
1. admit_student(): Transactional admission with Finance and Academics integration
2. generate_admission_number(): Sequential number generation
"""

import logging
from decimal import Decimal
from uuid import UUID
from datetime import date, datetime

from sqlalchemy import and_, select, func
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from src.core.exceptions import NotFoundError, ValidationError
from src.modules.admissions.models.students import (
    StudentProspect,
    Student,
    ProspectStatus,
    StudentActiveStatus,
)
from src.modules.academics.models.core import ClassLevel, Stream, StudentClassEnrollment
from src.modules.academics.services.enrollment_service import EnrollmentService

logger = logging.getLogger(__name__)


class AdmissionService:
    """
    Service for student admissions and lifecycle management.
    
    CRITICAL: The admit_student() function integrates with Finance and Academics modules
    to ensure complete onboarding in a single atomic transaction.
    """
    
    def __init__(self, db: AsyncSession):
        self.db = db
    
    async def generate_admission_number(
        self,
        school_id: UUID,
        year: int,
    ) -> str:
        """
        Generate sequential admission number.
        
        Format: ADM-{YEAR}-{SEQUENCE}
        Example: ADM-2024-001, ADM-2024-002, etc.
        
        ALGORITHM:
        1. Query existing StudentClassEnrollment for this school and year
        2. Find max sequence number
        3. Increment and pad with leading zeros
        4. Return formatted string
        
        Args:
            school_id: Tenant ID
            year: Academic year
            
        Returns:
            Formatted admission number (e.g., ADM-2024-001)
        """
        # Query max admission number for this year
        query = select(func.count(Student.id)).where(
            and_(
                Student.school_id == school_id,
                func.extract("year", Student.admission_date) == year,
            )
        )
        
        count_result = await self.db.scalar(query)
        count = count_result or 0
        
        # Generate next sequence
        sequence = count + 1
        admission_number = f"ADM-{year}-{sequence:03d}"
        
        logger.debug(f"Generated admission number: {admission_number}")
        return admission_number
    
    async def admit_student(
        self,
        school_id: UUID,
        prospect_id: UUID,
        class_level_id: UUID,
        stream_id: UUID | None,
        boarding_status: str,
        enrollment_service: "EnrollmentService",
        fee_account_service: "FeeAccountService",
        billing_service: "BillingService",
    ) -> dict:
        """
        CRITICAL ALGORITHM: Admit student from prospect.
        
        This is a complex transactional operation that integrates 3 modules:
        1. Admissions: Create Student and change prospect status
        2. Academics: Create StudentClassEnrollment
        3. Finance: Initialize FeeAccount and generate first invoice
        
        STEPS:
        1. Fetch StudentProspect, validate PENDING status
        2. Validate class_level and stream exist
        3. Generate sequential admission_number
        4. Create Student record (copy data from prospect)
        5. Update prospect status to ADMITTED
        6. Call EnrollmentService.enroll_student_in_class():
           - Creates StudentClassEnrollment
           - Auto-assigns compulsory subjects
           - Updates stream enrollment count
        7. Call FeeAccountService.initialize_account():
           - Creates FeeAccount for student
           - Linked to Student record
        8. Call BillingService.generate_initial_invoice():
           - Generates initial invoice for first term/year
           - Posts to GL
        9. COMMIT ATOMICALLY - if any step fails, entire operation rolls back
        10. Return complete admission summary
        
        CRITICAL ERROR HANDLING:
        - If FeeAccount creation fails: rollback and report
        - If invoice generation fails: rollback and report
        - If enrollment fails: rollback and report
        
        Args:
            school_id: Tenant ID
            prospect_id: StudentProspect ID
            class_level_id: ClassLevel ID
            stream_id: Stream ID (optional, will auto-select if not provided)
            boarding_status: BOARDING or DAY
            enrollment_service: Academic enrollment service
            fee_account_service: Finance fee account service
            billing_service: Finance billing service
            
        Returns:
            Dictionary with admission details (student_id, admission_number, enrollment_id, fee_account_id, invoice_id)
            
        Raises:
            NotFoundError: If prospect, class level, or stream not found
            ValidationError: If prospect not in PENDING status or validation fails
        """
        logger.info(f"Admitting student from prospect {prospect_id} into class {class_level_id}")
        
        # Step 1: Fetch StudentProspect
        prospect_query = select(StudentProspect).where(
            and_(
                StudentProspect.id == prospect_id,
                StudentProspect.school_id == school_id,
            )
        )
        prospect = await self.db.scalar(prospect_query)
        
        if not prospect:
            raise NotFoundError(f"StudentProspect {prospect_id} not found")
        
        # Validate prospect status is PENDING
        if prospect.status != ProspectStatus.PENDING:
            raise ValidationError(f"Cannot admit prospect with status {prospect.status}. Must be PENDING.")
        
        logger.info(f"✓ Found prospect: {prospect.first_name} {prospect.last_name}")
        
        # Step 2: Validate ClassLevel exists
        class_level_query = select(ClassLevel).where(
            and_(
                ClassLevel.id == class_level_id,
                ClassLevel.school_id == school_id,
            )
        ).options(
            selectinload(ClassLevel.streams),
        )
        class_level = await self.db.scalar(class_level_query)
        
        if not class_level:
            raise NotFoundError(f"ClassLevel {class_level_id} not found")
        
        logger.info(f"✓ Found class level: {class_level.name}")
        
        # If stream_id provided, validate it exists in this class
        if stream_id:
            stream_query = select(Stream).where(
                and_(
                    Stream.id == stream_id,
                    Stream.class_level_id == class_level_id,
                    Stream.school_id == school_id,
                )
            )
            stream = await self.db.scalar(stream_query)
            
            if not stream:
                raise NotFoundError(f"Stream {stream_id} not found in class {class_level.name}")
            
            logger.info(f"✓ Found stream: {stream.name}")
        else:
            # Auto-select stream with most available capacity
            available_streams = [
                s for s in class_level.streams
                if s.current_enrollment < s.max_capacity
            ]
            
            if not available_streams:
                raise ValidationError(f"No available capacity in class {class_level.name}")
            
            # Sort by available capacity (descending)
            stream = sorted(
                available_streams,
                key=lambda s: (s.max_capacity - s.current_enrollment),
                reverse=True,
            )[0]
            stream_id = stream.id
            logger.info(f"✓ Auto-selected stream: {stream.name} (capacity: {stream.current_enrollment}/{stream.max_capacity})")
        
        # Step 3: Generate admission number
        admission_number = await self.generate_admission_number(school_id, date.today().year)
        
        # Step 4: Create Student record
        student = Student(
            school_id=school_id,
            prospect_id=prospect.id,
            admission_number=admission_number,
            upi_nemis_number=prospect.email or None,  # Placeholder - would be filled from MoE
            first_name=prospect.first_name,
            last_name=prospect.last_name,
            email=prospect.email,
            phone=prospect.phone,
            gender=prospect.gender,
            date_of_birth=prospect.date_of_birth,
            boarding_status=boarding_status,
            active_status=StudentActiveStatus.ACTIVE,
            admission_date=date.today(),
            is_active=True,
        )
        
        self.db.add(student)
        await self.db.flush()  # Get student.id without committing
        
        logger.info(f"✓ Created Student record: {admission_number}")
        
        # Step 5: Update prospect status to ADMITTED
        prospect.status = ProspectStatus.ADMITTED
        
        # Step 6: Create StudentClassEnrollment via Academics service
        try:
            enrollment_result = await enrollment_service.enroll_student_in_class(
                school_id=school_id,
                student_id=student.id,
                stream_id=stream_id,
                term_id=None,  # Will use current active term
                enrollment_date=date.today(),
            )
            
            enrollment_id = enrollment_result[0].id if enrollment_result else None
            logger.info(f"✓ Created StudentClassEnrollment: {enrollment_id}")
            
        except Exception as e:
            logger.error(f"Error creating class enrollment: {e}", exc_info=True)
            await self.db.rollback()
            raise ValidationError(f"Failed to enroll student in class: {str(e)}")
        
        # Step 7: Initialize FeeAccount via Finance service
        try:
            fee_account = await fee_account_service.initialize_account(
                school_id=school_id,
                student_id=student.id,
                student_name=f"{student.first_name} {student.last_name}",
                opening_balance=Decimal("0.00"),
            )
            
            fee_account_id = fee_account.id if fee_account else None
            logger.info(f"✓ Created FeeAccount: {fee_account_id}")
            
        except Exception as e:
            logger.error(f"Error initializing fee account: {e}", exc_info=True)
            await self.db.rollback()
            raise ValidationError(f"Failed to initialize fee account: {str(e)}")
        
        # Step 8: Generate initial invoice via Billing service
        invoice_id = None
        try:
            invoice = await billing_service.generate_initial_invoice(
                school_id=school_id,
                student_id=student.id,
                fee_account_id=fee_account_id,
                boarding_status=boarding_status,
                class_level_id=class_level_id,
            )
            
            invoice_id = invoice.id if invoice else None
            logger.info(f"✓ Generated initial invoice: {invoice_id}")
            
        except Exception as e:
            logger.error(f"Error generating initial invoice: {e}", exc_info=True)
            await self.db.rollback()
            raise ValidationError(f"Failed to generate initial invoice: {str(e)}")
        
        # Step 9: Commit entire transaction atomically
        try:
            await self.db.commit()
            logger.info(f"✓ Admission transaction committed for student {admission_number}")
            
        except Exception as e:
            logger.error(f"Error committing admission transaction: {e}", exc_info=True)
            await self.db.rollback()
            raise ValidationError(f"Failed to commit admission: {str(e)}")
        
        # Step 10: Return admission summary
        return {
            "student_id": str(student.id),
            "admission_number": admission_number,
            "first_name": student.first_name,
            "last_name": student.last_name,
            "enrollment_id": str(enrollment_id),
            "fee_account_id": str(fee_account_id),
            "initial_invoice_id": str(invoice_id) if invoice_id else None,
            "class_level": class_level.name,
            "stream": stream.name,
            "boarding_status": boarding_status,
            "admission_date": student.admission_date.isoformat(),
            "message": f"Student {student.first_name} {student.last_name} successfully admitted with number {admission_number}",
        }
    
    async def get_prospect(
        self,
        school_id: UUID,
        prospect_id: UUID,
    ) -> StudentProspect:
        """Fetch prospect by ID."""
        query = select(StudentProspect).where(
            and_(
                StudentProspect.id == prospect_id,
                StudentProspect.school_id == school_id,
            )
        )
        prospect = await self.db.scalar(query)
        
        if not prospect:
            raise NotFoundError(f"StudentProspect {prospect_id} not found")
        
        return prospect
    
    async def get_student(
        self,
        school_id: UUID,
        student_id: UUID,
    ) -> Student:
        """Fetch student by ID with relationships."""
        query = select(Student).where(
            and_(
                Student.id == student_id,
                Student.school_id == school_id,
            )
        ).options(
            selectinload(Student.parent_relationships),
            selectinload(Student.class_enrollments),
            selectinload(Student.fee_account),
        )
        
        student = await self.db.scalar(query)
        
        if not student:
            raise NotFoundError(f"Student {student_id} not found")
        
        return student
    
    async def list_prospects(
        self,
        school_id: UUID,
        status: str | None = None,
        year: int | None = None,
    ) -> list[StudentProspect]:
        """List prospects with optional filters."""
        query = select(StudentProspect).where(
            StudentProspect.school_id == school_id,
        )
        
        if status:
            query = query.where(StudentProspect.status == status)
        
        if year:
            query = query.where(StudentProspect.kcpe_year == year)
        
        query = query.order_by(StudentProspect.kcpe_marks.desc())
        
        result = await self.db.execute(query)
        return result.scalars().all()
    
    async def list_students(
        self,
        school_id: UUID,
        active_only: bool = True,
        boarding_status: str | None = None,
    ) -> list[Student]:
        """List students with optional filters."""
        query = select(Student).where(
            Student.school_id == school_id,
        )
        
        if active_only:
            query = query.where(Student.is_active == True)
        
        if boarding_status:
            query = query.where(Student.boarding_status == boarding_status)
        
        query = query.order_by(Student.admission_number)
        
        result = await self.db.execute(query)
        return result.scalars().all()
    
    async def update_student_status(
        self,
        school_id: UUID,
        student_id: UUID,
        active_status: str,
    ) -> Student:
        """Update student active status."""
        student = await self.get_student(school_id, student_id)
        
        # Validate status
        valid_statuses = [s.value for s in StudentActiveStatus]
        if active_status not in valid_statuses:
            raise ValidationError(f"Invalid status: {active_status}")
        
        student.active_status = StudentActiveStatus(active_status)
        await self.db.commit()
        
        logger.info(f"Updated student {student.admission_number} status to {active_status}")
        return student
