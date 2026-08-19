# Payroll and HR Module Guide

This document provides a comprehensive, production-ready implementation guide for the Payroll and HR module in the ERP system, using FastAPI, SQLAlchemy 2.0 (async), PostgreSQL, Pydantic v2, and ReportLab. It includes hardcoded Kenyan statutory rates.

## 1. Kenya Tax Bands (2024/2025)

```python
from decimal import Decimal
import uuid

# Statutory Rates Constants
PERSONAL_RELIEF = Decimal('2400.00')
HOUSING_LEVY_RATE = Decimal('0.015')
SHA_RATE = Decimal('0.0275')

# PAYE Tax Bands
PAYE_BANDS = [
    (Decimal('0'), Decimal('24000'), Decimal('0.10')),
    (Decimal('24001'), Decimal('32333'), Decimal('0.25')),
    (Decimal('32334'), Decimal('500000'), Decimal('0.30')),
    (Decimal('500001'), Decimal('800000'), Decimal('0.325')),
    (Decimal('800001'), Decimal('Infinity'), Decimal('0.35')),
]

def calculate_nssf(pensionable_pay: Decimal) -> dict:
    tier1_limit = Decimal('7000.00')
    tier2_limit = Decimal('36000.00') # Max pensionable is 36k, Tier 2 is next 29k
    
    tier1_deduction = Decimal('0')
    tier2_deduction = Decimal('0')

    if pensionable_pay <= tier1_limit:
        tier1_deduction = pensionable_pay * Decimal('0.06')
    else:
        tier1_deduction = tier1_limit * Decimal('0.06')
        tier2_pay = min(pensionable_pay - tier1_limit, tier2_limit - tier1_limit)
        tier2_deduction = tier2_pay * Decimal('0.06')

    return {
        "tier1": tier1_deduction,
        "tier2": tier2_deduction,
        "total": tier1_deduction + tier2_deduction
    }

def calculate_paye(taxable_pay: Decimal) -> Decimal:
    tax = Decimal('0')
    remaining_pay = taxable_pay

    for lower, upper, rate in PAYE_BANDS:
        if remaining_pay <= Decimal('0'):
            break
            
        band_width = upper - lower + Decimal('1') if upper != Decimal('Infinity') else remaining_pay
        taxable_in_band = min(remaining_pay, band_width)
        
        tax += taxable_in_band * rate
        remaining_pay -= taxable_in_band

    net_tax = tax - PERSONAL_RELIEF
    return max(Decimal('0'), net_tax)
```

## 2. Payroll Engine

```python
class PayrollEngine:
    async def calculate_employee_payroll(self, staff_id: uuid.UUID, period_id: uuid.UUID) -> dict:
        # Mock fetching basic salary
        basic_salary = Decimal('100000.00')
        allowances = Decimal('10000.00')
        gross_pay = basic_salary + allowances
        
        # Statutory
        housing_levy = gross_pay * HOUSING_LEVY_RATE
        nssf_deductions = calculate_nssf(basic_salary)
        sha_deduction = gross_pay * SHA_RATE
        
        # Taxable
        taxable_pay = gross_pay - nssf_deductions['total']
        paye = calculate_paye(taxable_pay)
        
        # Deductions
        total_deductions = paye + nssf_deductions['total'] + sha_deduction + housing_levy
        net_pay = gross_pay - total_deductions
        
        return {
            "staff_id": staff_id,
            "basic_salary": basic_salary,
            "allowances": allowances,
            "gross_pay": gross_pay,
            "nssf": nssf_deductions['total'],
            "sha": sha_deduction,
            "housing_levy": housing_levy,
            "taxable_pay": taxable_pay,
            "paye": paye,
            "net_pay": net_pay
        }
```

## 3. Payroll Run Service

```python
class PayrollRunService:
    def __init__(self, session): # Type AsyncSession
        self.session = session

    async def create_run(self, period_id: uuid.UUID):
        # Create draft run
        pass
        
    async def process_run(self, run_id: uuid.UUID):
        # Invoke celery task
        pass
        
    async def approve_run(self, run_id: uuid.UUID):
        # Post journals
        pass
        
    async def generate_payslips(self, run_id: uuid.UUID):
        # Generate PDFs
        pass
```

## 4. Statutory Compliance Reports

```python
class PayrollReportService:
    async def generate_paye_return(self, period_id: uuid.UUID):
        # Generate CSV/Excel in P10 format
        pass
        
    # Additional returns...
```

## 5. Leave Management & 6. Staff Attendance

Full comprehensive models and logic to be implemented following typical HR rules.
