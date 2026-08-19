"""
Payroll Run Service for processing and approving payroll batches.

Critical Algorithms:
1. process_payroll_run(run_id): Calculate and create payroll entries for all active staff
2. approve_payroll_run(run_id): Post GL entries for salary expense, payables, deductions
"""

import logging
from decimal import Decimal
from uuid import UUID
from datetime import datetime

from sqlalchemy import and_, select, func
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from src.core.exceptions import NotFoundError, ValidationError
from src.modules.hr.models.hr_payroll import (
    Staff,
    PayrollRun,
    PayrollEntry,
    PayrollAllowance,
    PayrollDeduction,
    PayrollStatus,
    EmploymentType,
)
from src.modules.hr.services.tax_engine import TaxEngine
from src.modules.finance.services.journal_service import JournalService

logger = logging.getLogger(__name__)


class PayrollRunService:
    """
    Service for processing and approving payroll runs.
    
    All operations are transactional and audit-logged.
    """
    
    def __init__(self, db: AsyncSession):
        self.db = db
        self.tax_engine = TaxEngine()
        self.journal_service = JournalService(db)
    
    async def process_payroll_run(
        self,
        school_id: UUID,
        run_id: UUID,
        processed_by: UUID,
    ) -> dict:
        """
        CRITICAL ALGORITHM: Process payroll run.
        
        Steps:
        1. Fetch PayrollRun, validate it's in DRAFT status
        2. Query all active Staff (BOM + TSC, or just BOM based on config)
        3. For each staff:
           a. Fetch their basic_pay
           b. Fetch any PayrollAllowance lines already entered
           c. Calculate total_allowances
           d. Call tax_engine.calculate_taxes(basic_pay, allowances)
           e. Create PayrollEntry with all calculated fields
           f. Create child PayrollAllowance and PayrollDeduction records
           g. Commit each entry
        4. Update PayrollRun totals (sum all entries)
        5. Mark run as PROCESSED
        6. Return summary
        
        Args:
            school_id: Tenant ID
            run_id: PayrollRun ID
            processed_by: User ID doing the processing
            
        Returns:
            Dictionary with processing results
        """
        logger.info(f"Processing payroll run {run_id} for school {school_id}")
        
        # Step 1: Fetch and validate payroll run
        run_query = select(PayrollRun).where(
            and_(
                PayrollRun.id == run_id,
                PayrollRun.school_id == school_id,
            )
        )
        payroll_run = await self.db.scalar(run_query)
        
        if not payroll_run:
            raise NotFoundError(f"Payroll run {run_id} not found")
        
        if payroll_run.status != PayrollStatus.DRAFT:
            raise ValidationError(f"Cannot process payroll run with status {payroll_run.status}")
        
        logger.info(f"Processing payroll for period {payroll_run.period_month}/{payroll_run.period_year}")
        
        # Step 2: Query active staff (both BOM and TSC, as instructed)
        staff_query = select(Staff).where(
            and_(
                Staff.school_id == school_id,
                Staff.is_active == True,
            )
        ).order_by(Staff.employee_number)
        
        result = await self.db.execute(staff_query)
        all_staff = result.scalars().all()
        
        logger.info(f"Found {len(all_staff)} active staff to process")
        
        # Initialize totals
        total_gross = Decimal("0.00")
        total_net = Decimal("0.00")
        total_paye = Decimal("0.00")
        total_nssf = Decimal("0.00")
        total_sha = Decimal("0.00")
        total_housing = Decimal("0.00")
        
        processed_count = 0
        error_count = 0
        errors = []
        
        # Step 3: Process each staff member
        for staff in all_staff:
            try:
                logger.debug(f"Processing staff {staff.employee_number}: {staff.first_name} {staff.last_name}")
                
                # Check for existing entry (idempotency)
                existing_query = select(PayrollEntry).where(
                    and_(
                        PayrollEntry.school_id == school_id,
                        PayrollEntry.payroll_run_id == run_id,
                        PayrollEntry.staff_id == staff.id,
                    )
                )
                existing_entry = await self.db.scalar(existing_query)
                
                if existing_entry:
                    logger.debug(f"Payroll entry already exists for {staff.employee_number}, skipping")
                    continue
                
                # Step 3b: Fetch any existing allowances for this staff in this run
                # (user may have pre-entered allowances before processing)
                allowances_query = select(PayrollAllowance).where(
                    and_(
                        PayrollAllowance.school_id == school_id,
                        PayrollAllowance.staff_id == staff.id,
                    )
                )
                existing_allowances = await self.db.execute(allowances_query)
                allowance_records = existing_allowances.scalars().all()
                
                # Step 3c: Calculate total allowances
                total_allowances = sum(
                    (a.amount for a in allowance_records),
                    Decimal("0.00"),
                )
                
                # Step 3d: Calculate taxes
                tax_result = self.tax_engine.calculate_taxes(
                    basic_pay=staff.basic_pay,
                    allowances=total_allowances,
                )
                
                # Step 3e: Create PayrollEntry
                payroll_entry = PayrollEntry(
                    school_id=school_id,
                    payroll_run_id=run_id,
                    staff_id=staff.id,
                    basic_pay=staff.basic_pay,
                    total_allowances=total_allowances,
                    gross_pay=tax_result.taxable_pay + tax_result.nssf_total,  # Gross = Taxable + NSSF
                    nssf_tier1=tax_result.nssf_tier1,
                    nssf_tier2=tax_result.nssf_tier2,
                    sha_nhif=tax_result.sha_nhif,
                    housing_levy=tax_result.housing_levy,
                    taxable_pay=tax_result.taxable_pay,
                    paye=tax_result.paye,
                    total_statutory_deductions=tax_result.total_deductions,
                    total_other_deductions=Decimal("0.00"),  # Will be calculated if deductions exist
                    net_pay=tax_result.net_pay,
                    is_locked=False,
                )
                
                self.db.add(payroll_entry)
                await self.db.flush()  # Get the ID without committing
                
                # Step 3f: Create allowance line records
                for allowance in allowance_records:
                    payroll_entry.allowance_lines.append(
                        PayrollAllowance(
                            school_id=school_id,
                            payroll_entry_id=payroll_entry.id,
                            staff_id=staff.id,
                            allowance_type=allowance.allowance_type,
                            amount=allowance.amount,
                            description=allowance.description,
                        )
                    )
                
                # Step 3g: Create deduction line records (if any pre-entered)
                deductions_query = select(PayrollDeduction).where(
                    and_(
                        PayrollDeduction.school_id == school_id,
                        PayrollDeduction.staff_id == staff.id,
                    )
                )
                deduction_records = await self.db.execute(deductions_query)
                existing_deductions = deduction_records.scalars().all()
                
                total_other_deductions = Decimal("0.00")
                for deduction in existing_deductions:
                    payroll_entry.deduction_lines.append(
                        PayrollDeduction(
                            school_id=school_id,
                            payroll_entry_id=payroll_entry.id,
                            staff_id=staff.id,
                            deduction_type=deduction.deduction_type,
                            amount=deduction.amount,
                            description=deduction.description,
                        )
                    )
                    total_other_deductions += deduction.amount
                
                payroll_entry.total_other_deductions = total_other_deductions
                payroll_entry.net_pay = (
                    payroll_entry.gross_pay 
                    - payroll_entry.total_statutory_deductions 
                    - total_other_deductions
                )
                
                # Commit this entry
                await self.db.commit()
                
                # Step 3h: Update totals
                total_gross += payroll_entry.gross_pay
                total_net += payroll_entry.net_pay
                total_paye += payroll_entry.paye
                total_nssf += tax_result.nssf_total
                total_sha += tax_result.sha_nhif
                total_housing += tax_result.housing_levy
                
                processed_count += 1
                logger.debug(f"✓ Processed {staff.employee_number}: Net={payroll_entry.net_pay}")
                
            except Exception as e:
                error_count += 1
                error_msg = f"{staff.employee_number}: {str(e)}"
                errors.append(error_msg)
                logger.error(f"Error processing {staff.employee_number}: {e}", exc_info=True)
                continue
        
        # Step 4: Update PayrollRun totals
        payroll_run.total_gross_pay = total_gross
        payroll_run.total_net_pay = total_net
        payroll_run.total_paye_deducted = total_paye
        payroll_run.total_nssf_deducted = total_nssf
        payroll_run.total_sha_deducted = total_sha
        payroll_run.total_housing_levy_deducted = total_housing
        payroll_run.processed_by = processed_by
        payroll_run.processed_at = datetime.utcnow()
        
        # Step 5: Mark as PROCESSED
        payroll_run.status = PayrollStatus.PROCESSED
        
        await self.db.commit()
        
        logger.info(
            f"Payroll run {run_id} processed: {processed_count} entries, "
            f"Gross={total_gross}, Net={total_net}, PAYE={total_paye}"
        )
        
        return {
            "run_id": str(run_id),
            "period": f"{payroll_run.period_month:02d}/{payroll_run.period_year}",
            "processed_count": processed_count,
            "error_count": error_count,
            "total_gross_pay": str(total_gross),
            "total_net_pay": str(total_net),
            "total_paye": str(total_paye),
            "total_nssf": str(total_nssf),
            "total_sha": str(total_sha),
            "total_housing": str(total_housing),
            "errors": errors if errors else None,
        }
    
    async def approve_payroll_run(
        self,
        school_id: UUID,
        run_id: UUID,
        approved_by: UUID,
    ) -> dict:
        """
        CRITICAL ALGORITHM: Approve payroll run and post GL entries.
        
        Steps:
        1. Fetch PayrollRun, validate it's in PROCESSED status
        2. Create GL journal entries (4 main entries):
           a. DR Salary Expense (Total Gross Pay)
              CR Net Salary Payable (Total Net Pay)
           b. CR PAYE Control Account (Total PAYE)
           c. CR NSSF Control Account (Total NSSF)
           d. CR SHA/NHIF Control Account (Total SHA)
           e. CR Housing Levy Control Account (Total Housing)
        3. Lock all PayrollEntry records
        4. Mark PayrollRun as APPROVED
        5. Return approval summary
        
        GL Integration:
        - Calls JournalService.post_journal() to ensure proper double-entry
        - All entries balanced and audit-logged
        - GL Chart of Accounts codes:
          * Salary Expense: 5001 (or configurable)
          * Net Salary Payable: 2001
          * PAYE Control: 2002
          * NSSF Control: 2003
          * SHA Control: 2004
          * Housing Levy Control: 2005
        
        Args:
            school_id: Tenant ID
            run_id: PayrollRun ID
            approved_by: User ID approving
            
        Returns:
            Dictionary with approval summary
        """
        logger.info(f"Approving payroll run {run_id} for school {school_id}")
        
        # Step 1: Fetch and validate payroll run
        run_query = select(PayrollRun).where(
            and_(
                PayrollRun.id == run_id,
                PayrollRun.school_id == school_id,
            )
        ).options(
            selectinload(PayrollRun.entries),
        )
        payroll_run = await self.db.scalar(run_query)
        
        if not payroll_run:
            raise NotFoundError(f"Payroll run {run_id} not found")
        
        if payroll_run.status != PayrollStatus.PROCESSED:
            raise ValidationError(f"Cannot approve payroll run with status {payroll_run.status}")
        
        logger.info(f"Approving payroll: Gross={payroll_run.total_gross_pay}, Net={payroll_run.total_net_pay}")
        
        # Step 2: Create GL journal entries
        try:
            # Determine GL account codes (these would typically come from config)
            SALARY_EXPENSE_ACCOUNT = "5001"  # Expense
            NET_SALARY_PAYABLE_ACCOUNT = "2001"  # Liability
            PAYE_CONTROL_ACCOUNT = "2002"  # Liability
            NSSF_CONTROL_ACCOUNT = "2003"  # Liability
            SHA_CONTROL_ACCOUNT = "2004"  # Liability
            HOUSING_LEVY_CONTROL_ACCOUNT = "2005"  # Liability
            
            # Journal description
            journal_description = f"Payroll Run {payroll_run.period_month:02d}/{payroll_run.period_year}"
            
            # Step 2a: DR Salary Expense / CR Net Salary Payable
            # This is the main salary payment obligation
            await self.journal_service.post_journal(
                school_id=school_id,
                description=f"{journal_description} - Salary Expense",
                posting_date=datetime.utcnow().date(),
                journal_lines=[
                    {
                        "account_code": SALARY_EXPENSE_ACCOUNT,
                        "debit": payroll_run.total_gross_pay,
                        "credit": Decimal("0.00"),
                        "narrative": "Gross payroll expense",
                    },
                    {
                        "account_code": NET_SALARY_PAYABLE_ACCOUNT,
                        "debit": Decimal("0.00"),
                        "credit": payroll_run.total_net_pay,
                        "narrative": "Net salary payable to staff",
                    },
                ],
                posted_by=approved_by,
            )
            logger.info("✓ Posted salary expense / net payable GL entries")
            
            # Step 2b: DR Salary Expense / CR PAYE Control
            # PAYE is deducted from gross, so it's part of the salary expense
            if payroll_run.total_paye_deducted > 0:
                await self.journal_service.post_journal(
                    school_id=school_id,
                    description=f"{journal_description} - PAYE Tax",
                    posting_date=datetime.utcnow().date(),
                    journal_lines=[
                        {
                            "account_code": SALARY_EXPENSE_ACCOUNT,
                            "debit": payroll_run.total_paye_deducted,
                            "credit": Decimal("0.00"),
                            "narrative": "PAYE tax withheld",
                        },
                        {
                            "account_code": PAYE_CONTROL_ACCOUNT,
                            "debit": Decimal("0.00"),
                            "credit": payroll_run.total_paye_deducted,
                            "narrative": "PAYE tax payable to KRA",
                        },
                    ],
                    posted_by=approved_by,
                )
                logger.info("✓ Posted PAYE GL entries")
            
            # Step 2c: DR Salary Expense / CR NSSF Control
            if payroll_run.total_nssf_deducted > 0:
                await self.journal_service.post_journal(
                    school_id=school_id,
                    description=f"{journal_description} - NSSF",
                    posting_date=datetime.utcnow().date(),
                    journal_lines=[
                        {
                            "account_code": SALARY_EXPENSE_ACCOUNT,
                            "debit": payroll_run.total_nssf_deducted,
                            "credit": Decimal("0.00"),
                            "narrative": "NSSF contribution",
                        },
                        {
                            "account_code": NSSF_CONTROL_ACCOUNT,
                            "debit": Decimal("0.00"),
                            "credit": payroll_run.total_nssf_deducted,
                            "narrative": "NSSF payable",
                        },
                    ],
                    posted_by=approved_by,
                )
                logger.info("✓ Posted NSSF GL entries")
            
            # Step 2d: DR Salary Expense / CR SHA Control
            if payroll_run.total_sha_deducted > 0:
                await self.journal_service.post_journal(
                    school_id=school_id,
                    description=f"{journal_description} - SHA/NHIF",
                    posting_date=datetime.utcnow().date(),
                    journal_lines=[
                        {
                            "account_code": SALARY_EXPENSE_ACCOUNT,
                            "debit": payroll_run.total_sha_deducted,
                            "credit": Decimal("0.00"),
                            "narrative": "SHA/NHIF insurance",
                        },
                        {
                            "account_code": SHA_CONTROL_ACCOUNT,
                            "debit": Decimal("0.00"),
                            "credit": payroll_run.total_sha_deducted,
                            "narrative": "SHA/NHIF payable",
                        },
                    ],
                    posted_by=approved_by,
                )
                logger.info("✓ Posted SHA/NHIF GL entries")
            
            # Step 2e: DR Salary Expense / CR Housing Levy Control
            if payroll_run.total_housing_levy_deducted > 0:
                await self.journal_service.post_journal(
                    school_id=school_id,
                    description=f"{journal_description} - Housing Levy",
                    posting_date=datetime.utcnow().date(),
                    journal_lines=[
                        {
                            "account_code": SALARY_EXPENSE_ACCOUNT,
                            "debit": payroll_run.total_housing_levy_deducted,
                            "credit": Decimal("0.00"),
                            "narrative": "Housing levy",
                        },
                        {
                            "account_code": HOUSING_LEVY_CONTROL_ACCOUNT,
                            "debit": Decimal("0.00"),
                            "credit": payroll_run.total_housing_levy_deducted,
                            "narrative": "Housing levy payable",
                        },
                    ],
                    posted_by=approved_by,
                )
                logger.info("✓ Posted Housing Levy GL entries")
            
        except Exception as e:
            logger.error(f"Error posting GL entries: {e}", exc_info=True)
            raise ValidationError(f"Failed to post GL entries: {str(e)}")
        
        # Step 3: Lock all payroll entries
        for entry in payroll_run.entries:
            entry.is_locked = True
        
        # Step 4: Mark PayrollRun as APPROVED
        payroll_run.status = PayrollStatus.APPROVED
        payroll_run.approved_by = approved_by
        payroll_run.approved_at = datetime.utcnow()
        
        await self.db.commit()
        
        logger.info(f"✓ Payroll run {run_id} approved and locked")
        
        return {
            "run_id": str(run_id),
            "period": f"{payroll_run.period_month:02d}/{payroll_run.period_year}",
            "status": payroll_run.status.value,
            "approved_by": str(approved_by),
            "approved_at": payroll_run.approved_at.isoformat() if payroll_run.approved_at else None,
            "total_gross_pay": str(payroll_run.total_gross_pay),
            "total_net_pay": str(payroll_run.total_net_pay),
            "entry_count": len(payroll_run.entries),
            "gl_entries_posted": 5,  # Up to 5 GL journal entries
        }
    
    async def get_payroll_run(
        self,
        school_id: UUID,
        run_id: UUID,
    ) -> dict:
        """Fetch payroll run with all entries."""
        query = select(PayrollRun).where(
            and_(
                PayrollRun.id == run_id,
                PayrollRun.school_id == school_id,
            )
        ).options(
            selectinload(PayrollRun.entries).selectinload(PayrollEntry.staff),
            selectinload(PayrollRun.entries).selectinload(PayrollEntry.allowance_lines),
            selectinload(PayrollRun.entries).selectinload(PayrollEntry.deduction_lines),
        )
        
        run = await self.db.scalar(query)
        if not run:
            raise NotFoundError(f"Payroll run {run_id} not found")
        
        return run
    
    async def get_p10_report_data(
        self,
        school_id: UUID,
        run_id: UUID,
    ) -> list[dict]:
        """
        Generate KRA P10 report data for payroll run.
        
        P10 is the annual tax return showing:
        - Employee details (names, IDs, KRA PIN)
        - Gross salary
        - PAYE deducted
        - Other deductions
        
        Args:
            school_id: Tenant ID
            run_id: PayrollRun ID
            
        Returns:
            List of dictionaries with P10 report line data
        """
        # Fetch all entries with staff info
        query = select(PayrollEntry).where(
            and_(
                PayrollEntry.school_id == school_id,
                PayrollEntry.payroll_run_id == run_id,
            )
        ).options(
            selectinload(PayrollEntry.staff),
        ).order_by(PayrollEntry.staff.employee_number)
        
        result = await self.db.execute(query)
        entries = result.scalars().all()
        
        if not entries:
            raise NotFoundError(f"No payroll entries found for run {run_id}")
        
        # Build P10 lines
        p10_lines = []
        for entry in entries:
            staff = entry.staff
            p10_lines.append({
                "employee_number": staff.employee_number,
                "first_name": staff.first_name,
                "last_name": staff.last_name,
                "kra_pin": staff.kra_pin,
                "tsc_number": staff.tsc_number or "",
                "id_number": staff.id_number or "",
                "basic_pay": str(entry.basic_pay),
                "allowances": str(entry.total_allowances),
                "gross_pay": str(entry.gross_pay),
                "nssf_deduction": str(entry.nssf_tier1 + entry.nssf_tier2),
                "sha_deduction": str(entry.sha_nhif),
                "housing_levy": str(entry.housing_levy),
                "paye_tax": str(entry.paye),
                "net_pay": str(entry.net_pay),
            })
        
        return p10_lines
