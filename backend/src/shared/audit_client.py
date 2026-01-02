import logging
from typing import Any, Optional
from uuid import UUID

import httpx

from src.core.config import settings

logger = logging.getLogger(__name__)


class AuditLogger:
    """Shared client for Audit Service."""
    
    def __init__(self, service_name: str = "kronos"):
        self.service_name = service_name
        self.url = settings.audit_service_url

    async def log_action(
        self,
        action: str,
        resource_type: str,
        resource_id: Optional[str] = None,
        user_id: Optional[UUID] = None,
        user_email: Optional[str] = None,
        description: Optional[str] = None,
        request_data: Optional[dict[str, Any]] = None,
        status: str = "SUCCESS",
        error_message: Optional[str] = None,
    ) -> None:
        """Log an action to the audit service (fire and forget)."""
        if not self.url or "localhost" in self.url and not settings.is_development:
             # Basic check, though in docker internal "localhost" is wrong inside containers too unless host mode.
             # Assuming settings.audit_service_url is correctly set to http://audit-service:8007
             pass

        try:
            payload = {
                "user_id": str(user_id) if user_id else None,
                "user_email": user_email,
                "action": action,
                "resource_type": resource_type,
                "resource_id": str(resource_id) if resource_id else None,
                "description": description,
                "request_data": request_data,
                "status": status,
                "error_message": error_message,
                "service_name": self.service_name,
            }
            
            # Using a short timeout to prevent blocking main flow
            async with httpx.AsyncClient() as client:
                await client.post(
                    f"{self.url}/api/v1/audit/logs",
                    json=payload,
                    timeout=2.0 
                )
        except Exception as e:
            # We don't want to crash the app if audit logging fails
            logger.error(f"Failed to send audit log: {e}")


# Singleton instance helper (optional usage)
_audit_logger: Optional[AuditLogger] = None

def get_audit_logger(service_name: str = settings.service_name) -> AuditLogger:
    return AuditLogger(service_name)
