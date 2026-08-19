"""
Pydantic v2 schemas for HR and Payroll System.

Schemas for:
- Staff creation/response
- PayrollRun creation/approval/response
- PayrollEntry with full salary breakdown
- PayrollAllowance and PayrollDeduction
"""

from decimal import Decimal
from datetime import datetime, date
from uuid import UUID
from typing import Optional

from pydantic import BaseModel, Field, field_validator

from src.modules.hr.models.hr_payroll import EmploymentType, PayrollStatus


# ============================================================================
# STAFF SCHEMAS
# ============================================================================


class StaffCreate(BaseModel):
    """Create a new staff member."""
    first_name: str = Field(..., min_length=1, max_length=100)
    last_name: str = Field(..., min_length=1, max_length=100)
    email: Optional[str] = Field(None, max_length=255)
    phone: Optional[str] = Field(None, max_length=20)
    employee_number: str = Field(..., min_length=1, max_length=50)
    employment_type: EmploymentType
    kra_pin: str = Field(..., min_length=1, max_length=20, description="KRA PIN")
    tsc_number: Optional[str] = Field(None, max_length=20, description="TSC Number for TSC staff")
    bank_account: Optional[str] = Field(None, max_length=50)
    bank_name: Optional[str] = Field(None, max_length=100)
    id_number: Optional[str] = Field(None, max_length=20)
    basic_pay: Decimal = Field(..., gt=0, decimal_places=2)
    
    @field_validator("employment_type", mode="before")
    @classmethod
    def validate_employment_type(cls, v):
        if isinstance(v, str):
            v = v.upper()
        if v not in [e.value for e in EmploymentType]:
            raise ValueError(f"Invalid employment type: {v}")
        return v


class StaffUpdate(BaseModel):
    """Update staff member."""
    first_name: Optional[str] = Field(None, min_length=1, max_length=100)
    last_name: Optional[str] = Field(None, min_length=1, max_length=100)
    email: Optional[str] = Field(None, max_length=255)
    phone: Optional[str] = Field(None, max_length=20)
    bank_account: Optional[str] = Field(None, max_length=50)
    bank_name: Optional[str] = Field(None, max_length=100)
    basic_pay: Optional[Decimal] = Field(None, gt=0, decimal_places=2)
    is_active: Optional[bool] = None


class StaffResponse(BaseModel):
    """Staff response."""
    id: UUID
    employee_number: str
    first_name: str
    last_name: str
    email: Optional[str]
    phone: Optional[str]
    employment_type: str
    kra_pin: str
    tsc_number: Optional[str]
    bank_account: Optional[str]
    bank_name: Optional[str]
    basic_pay: Decimal
    is_active: bool
    created_at: str


# ============================================================================
# PAYROLL ALLOWANCE & DEDUCTION SCHEMAS
# ============================================================================


class PayrollAllowanceInput(BaseModel):
    """Input for allowance line."""
    allowance_type: str = Field(..., min_length=1, max_length=100)
    amount: Decimal = Field(..., ge=0, decimal_places=2)
    description: Optional[str] = None


class PayrollAllowanceResponse(BaseModel):
    """Allowance line response."""
    id: UUID
    allowance_type: str
    amount: Decimal
    description: Optional[str]


class PayrollDeductionInput(BaseModel):
    """Input for deduction line."""
    deduction_type: str = Field(..., min_length=1, max_length=100)
    amount: Decimal = Field(..., ge=0, decimal_places=2)
    description: Optional[str] = None


class PayrollDeductionResponse(BaseModel):
    """Deduction line response."""
    id: UUID
    deduction_type: str
    amount: Decimal
    description: Optional[str]


# ============================================================================
# PAYROLL ENTRY SCHEMAS
# ============================================================================


class PayrollEntryInput(BaseModel):
    """Input for payroll entry (typically auto-calculated)."""
    staff_id: UUID
    allowances: list[PayrollAllowanceInput] = Field(default_factory=list)
    deductions: list[PayrollDeductionInput] = Field(default_factory=list)


class PayrollEntryResponse(BaseModel):
    """Complete payroll entry with salary breakdown."""
    id: UUID
    payroll_run_id: UUID
    staff_id: UUID
    
    # Income
    basic_pay: Decimal
    total_allowances: Decimal
    gross_pay: Decimal
    
    # Statutory deductions
    nssf_tier1: Decimal
    nssf_tier2: Decimal
    sha_nhif: Decimal
    housing_levy: Decimal
    taxable_pay: Decimal
    paye: Decimal
    total_statutory_deductions: Decimal
    
    # Other deductions
    total_other_deductions: Decimal
    
    # Net
    net_pay: Decimal
    
    # Lines
    allowance_lines: list[PayrollAllowanceResponse] = []
    deduction_lines: list[PayrollDeductionResponse] = []
    
    is_locked: bool
    created_at: str


class PayrollEntryDetailResponse(BaseModel):
    """Detailed payroll entry with staff and run info."""
    id: UUID
    payroll_run_id: UUID
    staff_id: UUID
    employee_number: str
    staff_name: str
    
    # Income
    basic_pay: Decimal
    total_allowances: Decimal
    gross_pay: Decimal
    
    # Deductions
    nssf_tier1: Decimal
    nssf_tier2: Decimal
    sha_nhif: Decimal
    housing_levy: Decimal
    taxable_pay: Decimal
    paye: Decimal
    total_statutory_deductions: Decimal
    total_other_deductions: Decimal
    
    # Net
    net_pay: Decimal
    
    # Details
    allowance_lines: list[PayrollAllowanceResponse] = []
    deduction_lines: list[PayrollDeductionResponse] = []
    
    is_locked: bool


# ============================================================================
# PAYROLL RUN SCHEMAS
# ============================================================================


class PayrollRunCreate(BaseModel):
    """Create a new payroll run."""
    period_month: int = Field(..., ge=1, le=12)
    period_year: int = Field(..., ge=2000, le=2100)
    description: Optional[str] = None


class PayrollRunApproveInput(BaseModel):
    """Approve a payroll run."""
    approved_by: UUID = Field(..., description="User ID who is approving")


class PayrollRunResponse(BaseModel):
    """Payroll run response."""
    id: UUID
    period_month: int
    period_year: int
    status: str
    description: Optional[str]
    processed_by: Optional[UUID]
    processed_at: Optional[str]
    approved_by: Optional[UUID]
    approved_at: Optional[str]
    total_gross_pay: Decimal
    total_net_pay: Decimal
    total_paye_deducted: Decimal
    total_nssf_deducted: Decimal
    total_sha_deducted: Decimal
    total_housing_levy_deducted: Decimal
    created_at: str


class PayrollRunDetailResponse(BaseModel):
    """Detailed payroll run with all entries."""
    id: UUID
    period_month: int
    period_year: int
    status: str
    description: Optional[str]
    processed_by: Optional[UUID]
    processed_at: Optional[str]
    approved_by: Optional[UUID]
    approved_at: Optional[str]
    
    # Totals
    total_gross_pay: Decimal
    total_net_pay: Decimal
    total_paye_deducted: Decimal
    total_nssf_deducted: Decimal
    total_sha_deducted: Decimal
    total_housing_levy_deducted: Decimal
    
    # Entries
    entries: list[PayrollEntryDetailResponse] = []
    entry_count: int = 0
    
    created_at: str


# ============================================================================
# BULK OPERATIONS
# ============================================================================


class PayrollRunProcessRequest(BaseModel):
    """Request to process payroll run."""
    processed_by: UUID = Field(..., description="User ID processing")


class PayrollEntryBulkResult(BaseModel):
    """Result of bulk payroll entry processing."""
    total_submitted: int
    created: int
    failed: int
    errors: Optional[list[dict]] = None


# ============================================================================
# REPORTS
# ============================================================================


class P10ReportLine(BaseModel):
    """Single line in KRA P10 report."""
    employee_number: str
    first_name: str
    last_name: str
    kra_pin: str
    tsc_number: Optional[str]
    id_number: Optional[str]
    basic_pay: Decimal
    allowances: Decimal
    gross_pay: Decimal
    nssf_deduction: Decimal
    sha_deduction: Decimal
    housing_levy: Decimal
    paye_tax: Decimal
    net_pay: Decimal


class P10Report(BaseModel):
    """KRA P10 report for payroll run."""
    payroll_run_id: UUID
    period_month: int
    period_year: int
    generated_at: str
    total_employees: int
    total_gross_pay: Decimal
    total_paye: Decimal
    total_nssf: Decimal
    lines: list[P10ReportLine] = []
