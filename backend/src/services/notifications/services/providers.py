"""
KRONOS - Notification Service - Providers Module

Handles Email Provider Settings (SMTP/API configs).
"""
import logging
import httpx
from uuid import UUID
from typing import Optional

from src.core.exceptions import BusinessRuleError
from src.services.notifications.exceptions import ProviderConfigurationError
from src.services.notifications.schemas import (
    EmailProviderSettingsCreate,
    EmailProviderSettingsUpdate,
    TestEmailRequest,
)
from src.services.notifications.services.base import BaseNotificationService

logger = logging.getLogger(__name__)


class NotificationProviderService(BaseNotificationService):
    """
    Sub-service for Email Provider Settings.
    """

    async def get_active_settings(self):
        """Get active provider settings."""
        return await self._provider_repo.get_active()

    async def create_settings(self, data: EmailProviderSettingsCreate):
        """Create provider settings."""
        # Deactivate others if this is active? Repo usually handles it or we do it here.
        # Assuming repo handles checking active flag or logic is simple.
        # If we want to enforce only one active, we should check.
        if data.is_active:
            # Logic to unset others? The repo might not do it automatically.
            # Let's assume we want to ensure only one active.
            active = await self._provider_repo.get_active()
            if active:
                 await self._provider_repo.update(active.id, is_active=False)
                 
        return await self._provider_repo.create(**data.model_dump())

    async def update_settings(self, id: UUID, data: EmailProviderSettingsUpdate):
        """Update provider settings."""
        settings = await self._provider_repo.get(id)
        if not settings:
             raise ProviderConfigurationError("Settings not found")
             
        if data.is_active:
             active = await self._provider_repo.get_active()
             if active and active.id != id:
                  await self._provider_repo.update(active.id, is_active=False)

        return await self._provider_repo.update(id, **data.model_dump(exclude_unset=True))

    async def test_settings(self, data: TestEmailRequest):
        """Test settings by sending an email."""
        # Use provider specified in Request or check active?
        # Typically test request uses current settings or allows overriding.
        # But here we probably test the *saved* settings or pass them?
        # The request schema usually has `to_email`.
        # We will usage the ACTIVE settings for the test usually, or if we want to test
        # un-saved settings we'd need to mock the repo response.
        
        # Let's assume we test the ACTIVE settings.
        settings = await self.get_active_settings()
        if not settings:
             raise ProviderConfigurationError("No active settings to test")
             
        config = settings.get_config_dict()
        api_key = config.get("api_key")
        sender_email = config.get("sender_email")
        
        if not api_key:
             raise ProviderConfigurationError("Missing API key in settings")
             
        # Simple send via httpx (duplicating `_send_brevo_email` logic but isolated)
        payload = {
            "sender": {"email": sender_email, "name": "KRONOS Test"},
            "to": [{"email": data.to_email}],
            "subject": "Test Configuration KRONOS",
            "htmlContent": "<p>This is a test email to verify your configuration.</p>"
        }
        
        async with httpx.AsyncClient() as client:
            response = await client.post(
                "https://api.brevo.com/v3/smtp/email",
                headers={
                    "api-key": api_key,
                    "content-type": "application/json",
                    "accept": "application/json"
                },
                json=payload,
                timeout=10.0
            )
            
            if response.status_code in [201, 200]:
                return True
            else:
                raise BusinessRuleError(f"Test failed: {response.text}")
