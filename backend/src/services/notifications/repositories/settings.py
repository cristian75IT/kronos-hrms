from datetime import datetime
from typing import Optional, Any
from uuid import UUID

from sqlalchemy import select, and_
from sqlalchemy.ext.asyncio import AsyncSession

from src.services.notifications.models import (
    EmailProviderSettings,
    UserNotificationPreference
)

class EmailProviderSettingsRepository:
    """Repository for email provider settings."""

    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def get_active(self, provider: str = "brevo") -> Optional[EmailProviderSettings]:
        """Get the active settings for a provider."""
        result = await self._session.execute(
            select(EmailProviderSettings)
            .where(
                and_(
                    EmailProviderSettings.provider == provider,
                    EmailProviderSettings.is_active == True,
                )
            )
        )
        return result.scalar_one_or_none()

    async def get_by_provider(self, provider: str = "brevo") -> Optional[EmailProviderSettings]:
        """Get settings for a provider (active or inactive)."""
        result = await self._session.execute(
            select(EmailProviderSettings).where(EmailProviderSettings.provider == provider)
        )
        return result.scalar_one_or_none()

    async def get(self, id: UUID) -> Optional[EmailProviderSettings]:
        """Get settings by ID."""
        result = await self._session.execute(
            select(EmailProviderSettings).where(EmailProviderSettings.id == id)
        )
        return result.scalar_one_or_none()

    async def get_all(self) -> list[EmailProviderSettings]:
        """Get all provider settings."""
        result = await self._session.execute(
            select(EmailProviderSettings).order_by(EmailProviderSettings.provider)
        )
        return list(result.scalars().all())

    async def create(self, **kwargs) -> EmailProviderSettings:
        """Create provider settings."""
        settings = EmailProviderSettings(**kwargs)
        self._session.add(settings)
        await self._session.flush()
        return settings

    async def update(self, id: UUID, **kwargs) -> Optional[EmailProviderSettings]:
        """Update provider settings."""
        settings = await self.get(id)
        if not settings:
            return None

        for field, value in kwargs.items():
            if hasattr(settings, field) and value is not None:
                setattr(settings, field, value)

        await self._session.flush()
        return settings

    async def increment_emails_sent(self, id: UUID) -> None:
        """Increment daily email counter."""
        settings = await self.get(id)
        if settings:
            today = datetime.utcnow().date()
            if settings.last_reset_date and settings.last_reset_date.date() != today:
                # Reset counter for new day
                settings.emails_sent_today = 1
                settings.last_reset_date = datetime.utcnow()
            else:
                settings.emails_sent_today = (settings.emails_sent_today or 0) + 1
                if not settings.last_reset_date:
                    settings.last_reset_date = datetime.utcnow()
            await self._session.flush()

    async def can_send_email(self, id: UUID) -> bool:
        """Check if daily limit allows sending."""
        settings = await self.get(id)
        if not settings:
            return False
        
        if not settings.daily_limit:
            return True  # No limit configured
        
        today = datetime.utcnow().date()
        if settings.last_reset_date and settings.last_reset_date.date() != today:
            return True  # New day, counter will reset
        
        return (settings.emails_sent_today or 0) < settings.daily_limit


class UserPreferenceRepository:
    """Repository for user notification preferences."""

    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def get(self, user_id: UUID) -> Optional[UserNotificationPreference]:
        """Get preferences for a user."""
        result = await self._session.execute(
            select(UserNotificationPreference)
            .where(UserNotificationPreference.user_id == user_id)
        )
        return result.scalar_one_or_none()

    async def get_or_create(self, user_id: UUID) -> UserNotificationPreference:
        """Get existing preferences or create defaults."""
        prefs = await self.get(user_id)
        if prefs:
            return prefs
        
        prefs = UserNotificationPreference(user_id=user_id)
        self._session.add(prefs)
        await self._session.flush()
        return prefs

    async def update(self, user_id: UUID, **kwargs: Any) -> UserNotificationPreference:
        """Update preferences."""
        prefs = await self.get_or_create(user_id)
        
        for field, value in kwargs.items():
            if hasattr(prefs, field) and value is not None:
                setattr(prefs, field, value)
        
        await self._session.flush()
        return prefs
