"""
HR Reporting Settings Service.
"""
from uuid import UUID
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from ..models import HRReportingSettings
from ..schemas import HRReportingSettingsUpdate

class HRSettingsService:
    """Service for managing HR global settings."""
    
    def __init__(self, session: AsyncSession):
        self.session = session
        
    async def get_settings(self) -> HRReportingSettings:
        """Get current settings, creating default if not exists."""
        stmt = select(HRReportingSettings).limit(1)
        result = await self.session.execute(stmt)
        settings = result.scalar_one_or_none()
        
        if not settings:
            settings = HRReportingSettings()
            self.session.add(settings)
            await self.session.flush()
            
        return settings
        
    async def update_settings(self, data: HRReportingSettingsUpdate, user_id: UUID) -> HRReportingSettings:
        """Update settings."""
        settings = await self.get_settings()
        
        settings.timesheet_confirmation_day = data.timesheet_confirmation_day
        settings.timesheet_confirmation_month_offset = data.timesheet_confirmation_month_offset
        settings.updated_by = user_id
        
        return settings
