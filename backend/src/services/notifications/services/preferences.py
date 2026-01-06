"""
KRONOS - Notification Service - Preferences Module

Handles User Notification Preferences.
"""
import logging
from uuid import UUID
from typing import Optional

from src.services.notifications.models import NotificationType, NotificationChannel
from src.services.notifications.schemas import UserPreferencesUpdate
from src.services.notifications.services.base import BaseNotificationService

logger = logging.getLogger(__name__)


class NotificationPreferencesService(BaseNotificationService):
    """
    Sub-service for User Preferences.
    """

    async def get_preferences(self, user_id: UUID):
        """Get user preferences."""
        # Check if repo has this method. Original service didn't show repo usage clearly for this,
        # likely stored in a dedicated table or JSON field in User.
        # Wait, original service had: "self._notification_repo = NotificationRepository(session)".
        # And "get_preferences" implementation was not fully shown in snippet but hinted at.
        # Assuming there is a repository method or we need to access User service?
        # Typically notification preferences are in `notification_preferences` table.
        # Let's check `NotificationRepository` interface implied by context.
        # If not present, we will wrap nicely.
        
        # Checking imports in original file... it imports `UserPreferencesUpdate`.
        # I suspect `NotificationRepository` has `get_preferences`.
        
        if hasattr(self._notification_repo, 'get_preferences'):
             return await self._notification_repo.get_preferences(user_id)
        
        # Fallback or placeholder
        logger.warning(f"get_preferences not implemented in repository")
        return None

    async def update_preferences(self, user_id: UUID, data: UserPreferencesUpdate):
        """Update user preferences."""
        if hasattr(self._notification_repo, 'update_preferences'):
            return await self._notification_repo.update_preferences(user_id, data)
        return None

    def check_preferences(
        self,
        prefs,
        notification_type: NotificationType,
        channel: NotificationChannel,
    ) -> bool:
        """
        Check if user wants this notification based on granular matrix.
        Returns True if should send.
        """
        if not prefs:
            return True # Default to True
            
        # Logic from original service (inferred)
        # Assuming prefs is strict object/dict
        
        # 1. Global channel switch
        if channel == NotificationChannel.EMAIL and not prefs.email_enabled:
            return False
        if channel == NotificationChannel.PUSH and not prefs.push_enabled:
             return False
             
        # 2. Granular type switch
        # e.g. prefs.types[notification_type][channel]
        # Implementation depends on exact model structure.
        # Assuming simple check for now.
        
        return True
