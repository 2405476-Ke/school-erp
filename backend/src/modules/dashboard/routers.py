from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession
from src.core.database import get_db
from src.modules.dashboard.schemas import PrincipalKPIs, BursarKPIs, EnrolmentData
from src.modules.dashboard.services import DashboardService

router = APIRouter(prefix="/dashboard", tags=["Dashboard"])

@router.get("/principal/kpis", response_model=PrincipalKPIs)
async def get_principal_kpis(school_id: str = "default", db: AsyncSession = Depends(get_db)):
    return await DashboardService.get_principal_kpis(db, school_id)

@router.get("/principal/enrolment", response_model=EnrolmentData)
async def get_principal_enrolment(school_id: str = "default", db: AsyncSession = Depends(get_db)):
    return await DashboardService.get_enrolment_data(db, school_id)

@router.get("/bursar/kpis", response_model=BursarKPIs)
async def get_bursar_kpis(school_id: str = "default", db: AsyncSession = Depends(get_db)):
    return await DashboardService.get_bursar_kpis(db, school_id)

# Adding the placeholders for other requested endpoints
@router.get("/principal/alerts")
async def get_principal_alerts(school_id: str = "default"):
    return []

@router.get("/principal/pending-approvals")
async def get_principal_approvals(school_id: str = "default"):
    return []

@router.get("/principal/fee-collection")
async def get_fee_collection(school_id: str = "default"):
    return {"status": "ok"}

@router.get("/bursar/vote-heads")
async def get_vote_heads(school_id: str = "default"):
    return []

@router.get("/bursar/unmatched-transactions")
async def get_unmatched_transactions(school_id: str = "default"):
    return []
