from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from src.modules.settings.models import SchoolSettings
from src.modules.settings.schemas import SchoolSettingsUpdate

class SettingsService:
    @staticmethod
    async def get_settings(db: AsyncSession) -> SchoolSettings:
        result = await db.execute(select(SchoolSettings).limit(1))
        settings = result.scalars().first()
        if not settings:
            # Create default settings if none exist
            settings = SchoolSettings(
                school_name="Demo High School",
                current_academic_year="2026",
                current_term="Term 1"
            )
            db.add(settings)
            await db.commit()
            await db.refresh(settings)
        return settings

    @staticmethod
    async def update_settings(db: AsyncSession, settings_data: SchoolSettingsUpdate) -> SchoolSettings:
        settings = await SettingsService.get_settings(db)
        
        update_data = settings_data.dict(exclude_unset=True)
        for key, value in update_data.items():
            setattr(settings, key, value)
            
        await db.commit()
        await db.refresh(settings)
        return settings
