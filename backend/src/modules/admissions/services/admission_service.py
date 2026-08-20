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

from src.modules.admissions.models.students import StudentTransfer, ClearanceStatus
from src.modules.admissions.services.clearance_service import ClearanceService
from datetime import datetime
from src.modules.settings.models import SchoolSettings
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
        Generate sequential admission number with atomic locks (BR-ADM-002, FRD-ADM005).
        Format uses customizable setting from SchoolSettings.
        """
        # Query settings with FOR UPDATE to prevent race conditions
        query = select(SchoolSettings).where(
            SchoolSettings.id == school_id
        ).with_for_update()
        
        settings = await self.db.scalar(query)
        if not settings:
            raise NotFoundError("School settings not found")
            
        # Increment sequence safely
        settings.last_admission_sequence += 1
        seq = settings.last_admission_sequence
        
        # Format string e.g. "ADM-{YYYY}-{NNNN}"
        fmt = settings.admission_number_format or "ADM-{YYYY}-{NNNN}"
        
        adm_number = fmt.replace("{YYYY}", str(year)).replace("{NNNN}", f"{seq:04d}").replace("{NNN}", f"{seq:03d}")
        
        logger.debug(f"Generated robust admission number: {adm_number}")
        # Not committing here because this should be part of the larger transaction in admit_student
        return adm_number
    
    async def admit_student(
        self,
        school_id: UUID,
        prospect_id: UUID,
        class_level_id: UUID,
        stream_id: UUID | None,
        boarding_status: str,
        enrollment_service: "EnrollmentService",
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
        
        # BR-ADM-002: Zero duplicate UPIs (Validate UPI Uniqueness)
        target_upi = prospect.email or None  # TODO: Replace prospect.email with actual UPI when MoE integration is ready
        if target_upi:
            existing_upi = await self.db.scalar(
                select(Student).where(
                    and_(
                        Student.school_id == school_id,
                        Student.upi_nemis_number == target_upi
                    )
                )
            )
            if existing_upi:
                raise ValidationError(f"A student with UPI/NEMIS number {target_upi} is already registered.")
        
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
            active_status=StudentActiveStatus.PENDING_APPROVAL,
            admission_date=date.today(),
            is_active=False,
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

    async def approve_admission(
        self,
        school_id: UUID,
        student_id: UUID,
        approved_by_id: UUID,
        fee_account_service: "FeeAccountService",
        billing_service: "BillingService",
    ) -> dict:
        """
        FRD-ADM006 and FRD-ADM007: Principal Approval Workflow and Auto-Billing.
        Moves student from PENDING_APPROVAL to ACTIVE and triggers billing.
        """
        student = await self.get_student(school_id, student_id)
        
        if student.active_status != StudentActiveStatus.PENDING_APPROVAL:
            raise ValidationError(f"Cannot approve student with status {student.active_status}")
            
        # BR/FRD-ADM009: Checklist Completion Enforced
        from src.modules.settings.models import AdmissionChecklistItem
        from src.modules.admissions.models.students import StudentChecklistRecord
        
        # 1. Fetch mandatory checklist criteria for this student's boarding status
        mandatory_criteria = await self.db.scalars(
            select(AdmissionChecklistItem).where(
                and_(
                    AdmissionChecklistItem.school_id == str(school_id),
                    AdmissionChecklistItem.is_mandatory == True,
                    AdmissionChecklistItem.target_status.in_([student.boarding_status, "ALL"])
                )
            )
        )
        mandatory_items = mandatory_criteria.all()
        
        # 2. Fetch student's submitted checklist records
        submitted_records = await self.db.scalars(
            select(StudentChecklistRecord).where(
                and_(
                    StudentChecklistRecord.student_id == student_id,
                    StudentChecklistRecord.is_submitted == True
                )
            )
        )
        submitted_item_ids = {str(record.checklist_item_id) for record in submitted_records.all()}
        
        # 3. Cross-reference
        missing_items = []
        for item in mandatory_items:
            if str(item.id) not in submitted_item_ids:
                missing_items.append(item.item_name)
                
        if missing_items:
            raise ValidationError(
                f"Cannot approve admission. Missing mandatory checklist items for {student.boarding_status} student: " + 
                ", ".join(missing_items)
            )

            
        student.active_status = StudentActiveStatus.ACTIVE
        student.is_active = True
        
        # FRD-ADM007: Trigger Term 1 Fee Invoice upon Active status transition
        try:
            # 1. Initialize Fee Account
            fee_account = await fee_account_service.initialize_account(
                school_id=school_id,
                student_id=student.id,
                student_name=f"{student.first_name} {student.last_name}",
                opening_balance=Decimal("0.00"),
            )
            fee_account_id = fee_account.id if fee_account else None
            
            # Get the enrollment to know which class to bill
            class_level_id = None
            if student.class_enrollments:
                class_level_id = student.class_enrollments[0].class_level_id
                
            if not class_level_id:
                raise ValidationError("Cannot bill a student with no class enrollment")

            # 2. Generate Initial Invoice
            invoice = await billing_service.generate_initial_invoice(
                school_id=school_id,
                student_id=student.id,
                fee_account_id=fee_account_id,
                boarding_status=student.boarding_status,
                class_level_id=class_level_id,
            )
            invoice_id = invoice.id if invoice else None
            
        except Exception as e:
            logger.error(f"Error during approval auto-billing: {e}", exc_info=True)
            await self.db.rollback()
            raise ValidationError(f"Failed to generate fee invoice: {str(e)}")
            
        await self.db.commit()
        await self.db.refresh(student)
        
        logger.info(f"Student {student.admission_number} approved by {approved_by_id} and billed.")
        return {
            "student_id": str(student.id),
            "status": student.active_status.value,
            "fee_account_id": str(fee_account_id) if fee_account_id else None,
            "invoice_id": str(invoice_id) if invoice_id else None,
        }

    async def transfer_student(
        self,
        school_id: UUID,
        student_id: UUID,
        transfer_to_school: str,
        transfer_date: date,
        reason: str,
        clearance_service: ClearanceService,
        performed_by_id: UUID,
    ) -> StudentTransfer:
        """
        FRD-ADM008: Process student transfer.
        """
        student = await self.get_student(school_id, student_id)
        
        # Check clearance status
        clearances = await clearance_service.get_student_clearances(school_id, student_id)
        if not clearances or clearances[0].status != ClearanceStatus.CLEARED:
            raise ValidationError(f"Student {student.admission_number} must be fully cleared before transfer.")
            
        # Create transfer record
        transfer = StudentTransfer(
            school_id=school_id,
            student_id=student_id,
            transfer_to_school=transfer_to_school,
            transfer_date=transfer_date,
            reason=reason,
            status="APPROVED",
            created_by_id=performed_by_id,
        )
        self.db.add(transfer)
        
        # Update student status to halt billing
        student.active_status = StudentActiveStatus.WITHDRAWN
        student.is_active = False
        
        await self.db.commit()
        await self.db.refresh(transfer)
        logger.info(f"Student {student.admission_number} transferred to {transfer_to_school}")
        
        return transfer

    async def generate_leaving_certificate(
        self,
        school_id: UUID,
        student_id: UUID,
        enrollment_service: "EnrollmentService",
    ) -> dict:
        """
        FRD-ADM008: Generate leaving certificate with transcript.
        """
        student = await self.get_student(school_id, student_id)
        
        # Get transfer record
        query = select(StudentTransfer).where(
            and_(
                StudentTransfer.school_id == school_id,
                StudentTransfer.student_id == student_id,
            )
        ).order_by(StudentTransfer.created_at.desc())
        transfer = await self.db.scalar(query)
        
        if not transfer:
            raise ValidationError(f"No transfer record found for student {student.admission_number}")
            
        # Get transcript summary
        transcript = await enrollment_service.get_student_transcript(school_id, student_id)
        
        return {
            "certificate_id": f"LC-{student.admission_number}",
            "issue_date": datetime.utcnow().date().isoformat(),
            "student_name": f"{student.first_name} {student.last_name}",
            "admission_number": student.admission_number,
            "upi_nemis_number": student.upi_nemis_number,
            "admission_date": student.admission_date.isoformat(),
            "leaving_date": transfer.transfer_date.isoformat(),
            "destination_school": transfer.transfer_to_school,
            "reason_for_leaving": transfer.reason,
            "academic_transcript": transcript,
            "status": "VALID",
        }
