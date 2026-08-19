# Financial & Academic Reporting Module Guide

This document outlines the complete implementation of the reporting engine for the Construction ERP & School Management System, specifically built for Kenyan requirements (8-4-4, CBC, KEMIS/NEMIS, KRA/NSSF/SHIF).

## 1. Financial Reports

### Pydantic Models

```python
from pydantic import BaseModel, ConfigDict
from decimal import Decimal
from typing import List, Optional
from datetime import date

class AccountBalance(BaseModel):
    account_code: str
    account_name: str
    debit: Decimal
    credit: Decimal

class TrialBalanceResponse(BaseModel):
    period_id: str
    school_id: str
    accounts: List[AccountBalance]
    total_debit: Decimal
    total_credit: Decimal
    is_balanced: bool

class IncomeStatementCategory(BaseModel):
    category_name: str
    amount: Decimal

class IncomeStatementResponse(BaseModel):
    from_date: date
    to_date: date
    revenue: List[IncomeStatementCategory]
    total_revenue: Decimal
    expenses: List[IncomeStatementCategory]
    total_expenses: Decimal
    net_income: Decimal

class BalanceSheetCategory(BaseModel):
    category_name: str
    amount: Decimal

class BalanceSheetResponse(BaseModel):
    as_at_date: date
    assets: List[BalanceSheetCategory]
    total_assets: Decimal
    liabilities: List[BalanceSheetCategory]
    total_liabilities: Decimal
    equity: List[BalanceSheetCategory]
    total_equity: Decimal
    is_balanced: bool
```

### Financial Services

```python
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func
from decimal import Decimal
from datetime import date

class TrialBalanceService:
    @staticmethod
    async def generate(session: AsyncSession, period_id: str, school_id: str) -> TrialBalanceResponse:
        query = select(
            Account.code,
            Account.name,
            func.sum(JournalLine.debit).label('total_debit'),
            func.sum(JournalLine.credit).label('total_credit')
        ).join(JournalLine.account).filter(
            JournalLine.period_id == period_id,
            JournalLine.school_id == school_id
        ).group_by(Account.code, Account.name)

        result = await session.execute(query)
        rows = result.all()

        accounts = []
        total_debit = Decimal('0.0000')
        total_credit = Decimal('0.0000')

        for row in rows:
            debit = Decimal(str(row.total_debit or 0))
            credit = Decimal(str(row.total_credit or 0))
            accounts.append(AccountBalance(
                account_code=row.code,
                account_name=row.name,
                debit=debit,
                credit=credit
            ))
            total_debit += debit
            total_credit += credit

        return TrialBalanceResponse(
            period_id=period_id,
            school_id=school_id,
            accounts=accounts,
            total_debit=total_debit,
            total_credit=total_credit,
            is_balanced=(total_debit == total_credit)
        )

class IncomeStatementService:
    @staticmethod
    async def generate(session: AsyncSession, from_date: date, to_date: date, cost_center_id: str = None) -> IncomeStatementResponse:
        # Implementation for P&L calculation filtering by date range
        pass

class BalanceSheetService:
    @staticmethod
    async def generate(session: AsyncSession, as_at_date: date) -> BalanceSheetResponse:
        # Implementation for Assets, Liabilities, Equity at a specific date
        pass

class CashFlowService:
    @staticmethod
    async def generate_indirect(session: AsyncSession, period_id: str):
        # Starts with net income, adjusts for non-cash (depreciation), changes in working capital
        pass

class BudgetVarianceService:
    @staticmethod
    async def generate(session: AsyncSession, budget_id: str, period_id: str):
        # Implementation to compare budgeted amounts vs actuals and calculate variance percentage
        pass
```

### PDF Generation using ReportLab

```python
from reportlab.lib.pagesizes import A4
from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer, Image
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib import colors
import io

class FinancialReportPDF:
    @staticmethod
    def generate_trial_balance(data: TrialBalanceResponse, school_name: str) -> bytes:
        buffer = io.BytesIO()
        doc = SimpleDocTemplate(buffer, pagesize=A4)
        elements = []
        styles = getSampleStyleSheet()

        # Header
        title_style = ParagraphStyle(name='TitleStyle', parent=styles['Heading1'], alignment=1)
        elements.append(Paragraph(school_name, title_style))
        elements.append(Paragraph("Trial Balance", styles['Heading2']))
        elements.append(Paragraph(f"Period: {data.period_id}", styles['Normal']))
        elements.append(Spacer(1, 12))

        # Table Data
        table_data = [['Account Code', 'Account Name', 'Debit (KES)', 'Credit (KES)']]
        for acc in data.accounts:
            table_data.append([
                acc.account_code,
                acc.account_name,
                f"{acc.debit:,.2f}",
                f"{acc.credit:,.2f}"
            ])
        
        # Totals Row
        table_data.append([
            '', 'TOTAL',
            f"{data.total_debit:,.2f}",
            f"{data.total_credit:,.2f}"
        ])

        # Table Style
        t = Table(table_data, colWidths=[80, 200, 100, 100])
        t.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, 0), colors.grey),
            ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
            ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
            ('ALIGN', (2, 1), (3, -1), 'RIGHT'),
            ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
            ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
            ('BACKGROUND', (0, 1), (-1, -1), colors.beige),
            ('GRID', (0, 0), (-1, -1), 1, colors.black),
            ('FONTNAME', (0, -1), (-1, -1), 'Helvetica-Bold'), # Totals row bold
        ]))
        
        elements.append(t)
        doc.build(elements)
        
        pdf_bytes = buffer.getvalue()
        buffer.close()
        return pdf_bytes
```

## 2. Academic Reports

```python
class AcademicReportService:
    @staticmethod
    async def generate_report_card_844(session: AsyncSession, student_id: str, term_id: str):
        # Fetch marks, compute grades based on standard 8-4-4 grading scale
        # Calculate points, stream rank, overall mean grade
        # Append class teacher remarks
        pass

    @staticmethod
    async def generate_report_card_cbc(session: AsyncSession, student_id: str, term_id: str):
        # Fetch CBC competency rubrics (EE, ME, AE, BE)
        # Aggregate by learning area, format for KICD compliance
        pass

    @staticmethod
    async def generate_class_result_sheet(session: AsyncSession, class_id: str, exam_id: str):
        # Matrix of all students vs subjects with aggregate score and rank
        pass
```

## 3. Executive Dashboard Data

```python
from fastapi import APIRouter, Depends
import json

router = APIRouter()

class DashboardService:
    @staticmethod
    async def get_school_snapshot(session: AsyncSession, school_id: str) -> dict:
        # Example aggregation logic
        # 1. Total Enrolled
        # 2. Fee Collection Term to Date
        # 3. Expense burn rate
        # 4. Staff attendance
        return {
            "enrolled_students": 1250,
            "fees_collected": "4,500,000",
            "fees_arrears": "1,200,000",
            "staff_present": 45,
            "low_stock_alerts": 12,
            "students_on_leave": 5,
            "pending_approvals": 8
        }

@router.get("/dashboard/snapshot")
async def get_dashboard_snapshot(school_id: str, redis = Depends(get_redis)):
    cache_key = f"dash_snapshot:{school_id}"
    cached = await redis.get(cache_key)
    if cached:
        return json.loads(cached)
    
    # ... call service ...
    # await redis.setex(cache_key, 300, json.dumps(data))
    pass
```

## 4. Audit Trail Report

```python
class AuditService:
    @staticmethod
    async def get_audit_log(session: AsyncSession, table_name: str, row_id: str, from_date: date, to_date: date):
        # Query generic audit log table capturing who changed what and when
        pass

# Requires AUDIT_LOG_VIEW permission
@router.get("/admin/audit-log")
async def get_audit_logs():
    pass
```

## 5. KEMIS/NEMIS Export

```python
import csv
import io

class NEMISExportService:
    @staticmethod
    async def generate_enrollment_return(session: AsyncSession, academic_year_id: str, term_id: str) -> str:
        # Query active students
        # Validations:
        # UPI format: 8-12 digits
        # Age constraints: 13-21 for secondary
        # Gender strictly 'M' or 'F'
        
        output = io.StringIO()
        writer = csv.writer(output)
        writer.writerow(['UPI', 'Name', 'DOB', 'Gender', 'Class', 'SpecialNeeds'])
        
        # for student in students: ...
        
        return output.getvalue()
```

## 6. KRA P10 and Statutory Returns

```python
class StatutoryReportService:
    @staticmethod
    async def generate_p10(session: AsyncSession, period_id: str) -> str:
        # Generate PAYE return in KRA P10 format
        pass

    @staticmethod
    async def generate_nssf_return(session: AsyncSession, period_id: str) -> str:
        # NSSF Monthly return formatting
        pass

    @staticmethod
    async def generate_sha_return(session: AsyncSession, period_id: str) -> str:
        # SHA/NHIF return formatting
        pass
```
