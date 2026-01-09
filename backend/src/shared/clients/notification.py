"""
KRONOS - Notification Service Client

Enterprise-grade notification client supporting multi-channel delivery.
"""
import logging
from typing import Optional
from uuid import UUID

from src.core.config import settings
from src.shared.clients.base import BaseClient
from src.shared.clients.auth import AuthClient

logger = logging.getLogger(__name__)


class NotificationClient(BaseClient):
    """
    Client for Notification Service.
    
    Features:
    - Multi-channel support (in_app, email, push)
    - Structured result with delivery status
    - Automatic email resolution from auth service
    """
    
    def __init__(self):
        super().__init__(
            base_url=settings.notification_service_url,
            service_name="notification",
        )
        self._auth_client = AuthClient()
    
    async def send_notification(
        self,
        user_id: UUID,
        notification_type: str,
        title: str,
        message: str,
        channels: Optional[list[str]] = None,
        priority: str = "normal",
        entity_type: Optional[str] = None,
        entity_id: Optional[str] = None,
        action_url: Optional[str] = None,
        force_email_lookup: bool = True,
    ) -> dict:
        """
        Send notification through specified channels.
        
        Args:
            user_id: Target user UUID
            notification_type: Type from NotificationType enum
            title: Notification title
            message: Notification body
            channels: List of channels ["in_app", "email"]. Default: ["in_app", "email"]
            priority: Notification priority ("normal", "high", "urgent"). Default: "normal"
            entity_type: Related entity type (e.g., "LeaveRequest")
            entity_id: Related entity ID
            action_url: URL to navigate on click (relative paths auto-prefixed with FRONTEND_URL)
            force_email_lookup: Whether to fetch user email from auth service
        
        Returns:
            dict with 'success', 'notification_ids', 'email_sent', 'errors'
        """
        if channels is None:
            channels = ["in_app", "email"]
        
        result = {
            "success": False,
            "notification_ids": [],
            "email_sent": False,
            "errors": [],
        }
        
        try:
            # Resolve user email if needed
            user_email = None
            if force_email_lookup:
                user_email = await self._auth_client.get_user_email(user_id)
                if not user_email:
                    logger.warning(f"Notification skipped: No email for user {user_id}")
                    result["errors"].append(f"No email found for user {user_id}")
                    return result
            
            # Resolve relative action_url to absolute using FRONTEND_URL
            resolved_action_url = action_url
            if action_url and action_url.startswith("/"):
                resolved_action_url = f"{settings.frontend_url}{action_url}"
            
            # Send to each channel
            for channel in channels:
                try:
                    payload = {
                        "user_id": str(user_id),
                        "user_email": user_email,
                        "notification_type": notification_type,
                        "title": title,
                        "message": message,
                        "channels": channel, # Typo in original file? Original said "channel": channel.
                        "priority": priority,
                        "channel": channel,
                        "entity_type": entity_type,
                        "entity_id": str(entity_id) if entity_id else None,
                        "action_url": resolved_action_url,
                    }
                    
                    response = await self.post("/api/v1/notifications", json=payload)
                    
                    if response:
                        result["notification_ids"].append(response.get("id"))
                        if channel == "email":
                            result["email_sent"] = True
                    else:
                        result["errors"].append(f"{channel}: failed")
                        
                except Exception as e:
                    logger.error(f"NotificationClient error ({channel}): {e}")
                    result["errors"].append(f"{channel}: {str(e)}")
            
            result["success"] = len(result["notification_ids"]) > 0
            
        except Exception as e:
            logger.error(f"NotificationClient error: {e}")
            result["errors"].append(str(e))
        
        return result
    
    async def send_with_email(
        self,
        user_id: UUID,
        notification_type: str,
        title: str,
        message: str,
        entity_type: Optional[str] = None,
        entity_id: Optional[str] = None,
        action_url: Optional[str] = None,
    ) -> dict:
        """Convenience method: send both in_app and email notification."""
        return await self.send_notification(
            user_id=user_id,
            notification_type=notification_type,
            title=title,
            message=message,
            channels=["in_app", "email"],
            entity_type=entity_type,
            entity_id=entity_id,
            action_url=action_url,
        )
