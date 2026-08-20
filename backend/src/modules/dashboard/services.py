from sqlalchemy.ext.asyncio import AsyncSession
from src.modules.dashboard.schemas import PrincipalKPIs, BursarKPIs, EnrolmentData
# Note: In a real system we'd import models like Student, Staff, Ledger, etc.
# For now, returning realistic default shapes so the frontend UI clears the error.

class DashboardService:
    @staticmethod
    async def get_principal_kpis(db: AsyncSession, school_id: str) -> PrincipalKPIs:
        # Placeholder for actual DB aggregations
        return PrincipalKPIs(
            total_students=850,
            total_staff=42,
            fee_collection_rate=78.5,
            pending_approvals=12
        )

    @staticmethod
    async def get_bursar_kpis(db: AsyncSession, school_id: str) -> BursarKPIs:
        return BursarKPIs(
            total_bank_balance=1250000.0,
            total_fee_arrears=450000.0,
            unmatched_transactions=5,
            active_lpos=8
        )

    @staticmethod
    async def get_enrolment_data(db: AsyncSession, school_id: str) -> EnrolmentData:
        return EnrolmentData(
            form_1=220,
            form_2=215,
            form_3=210,
            form_4=205
        )
