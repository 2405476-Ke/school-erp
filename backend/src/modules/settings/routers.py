from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession
from src.core.database import get_db
from src.modules.settings.schemas import SchoolSettingsResponse, SchoolSettingsUpdate
from src.modules.settings.services import SettingsService

router = APIRouter(prefix="/settings", tags=["Settings"])

@router.get("/", response_model=SchoolSettingsResponse)
async def get_school_settings(db: AsyncSession = Depends(get_db)):
    """Retrieve global school configuration."""
    return await SettingsService.get_settings(db)

@router.put("/", response_model=SchoolSettingsResponse)
async def update_school_settings(
    settings_data: SchoolSettingsUpdate, 
    db: AsyncSession = Depends(get_db)
):
    """Update global school configuration."""
    return await SettingsService.update_settings(db, settings_data)
