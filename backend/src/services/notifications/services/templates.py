"""
KRONOS - Notification Service - Templates Module

Handles Email Templates management and synchronization.
"""
import logging
from uuid import UUID
from typing import Optional

from src.core.exceptions import BusinessRuleError
from src.services.notifications.exceptions import TemplateNotFound, ProviderConfigurationError
from src.services.notifications.schemas import (
    EmailTemplateCreate,
    EmailTemplateUpdate,
)
from src.services.notifications.services.base import BaseNotificationService

import httpx
from src.core.config import settings

logger = logging.getLogger(__name__)


class NotificationTemplateService(BaseNotificationService):
    """
    Sub-service for Email Templates management.
    """

    async def get_templates(self, active_only: bool = True):
        """Get all templates."""
        return await self._template_repo.get_all(active_only)

    async def get_template(self, id: UUID):
        """Get template by ID."""
        template = await self._template_repo.get(id)
        if not template:
            raise TemplateNotFound("Email template not found")
        return template

    async def create_template(self, data: EmailTemplateCreate):
        """Create email template."""
        # Check code uniqueness
        existing = await self._template_repo.get_by_code(data.code)
        if existing:
            raise BusinessRuleError(f"Template with code {data.code} already exists")
            
        template = await self._template_repo.create(**data.model_dump())
        return template

    async def update_template(self, id: UUID, data: EmailTemplateUpdate, user_id: Optional[UUID] = None):
        """Update email template."""
        template = await self.get_template(id)
        
        updated = await self._template_repo.update(id, **data.model_dump(exclude_unset=True))
        
        # Audit (user_id needed to log who updated)
        # Using placeholder since original service didn't pass user_id clearly in all paths
        if user_id:
             await self._audit.log_action(
                user_id=user_id,
                action="UPDATE_TEMPLATE",
                resource_type="EMAIL_TEMPLATE",
                resource_id=str(id),
                description=f"Updated template {template.code}",
            )
            
        return updated

    async def sync_template_to_brevo(self, id: UUID, user_id: Optional[UUID] = None):
        """Sync a local template to Brevo."""
        template = await self.get_template(id)
        
        provider_settings = await self._provider_repo.get_active()
        if not provider_settings:
             raise ProviderConfigurationError("No active email provider configured")
             
        config = provider_settings.get_config_dict()
        api_key = config.get("api_key")
        sender_email = config.get("sender_email")
        sender_name = config.get("sender_name")
        
        if not api_key:
             raise ProviderConfigurationError("Missing API key")
             
        # Determine if create or update
        is_update = bool(template.brevo_template_id)
        
        payload = {
            "templateName": template.name,
            "subject": template.subject,
            "htmlContent": template.html_content,    
            "sender": {"name": sender_name, "email": sender_email},
            "isActive": True
        }
        
        url = "https://api.brevo.com/v3/smtp/templates"
        method = "POST"
        
        if is_update:
            url = f"{url}/{template.brevo_template_id}"
            method = "PUT"
            
        async with httpx.AsyncClient() as client:
            response = await client.request(
                method,
                url,
                headers={
                    "api-key": api_key,
                    "content-type": "application/json",
                    "accept": "application/json"
                },
                json=payload,
                timeout=10.0
            )
            
            if response.status_code in [201, 204, 200]:
                if not is_update:
                    # Capture ID
                   brevo_id = response.json().get("id")
                   await self._template_repo.update(id, brevo_template_id=str(brevo_id))
                return True
            else:
                raise Exception(f"Brevo Sync Failed: {response.text}")
