"""
KRONOS - Enterprise Audit Client

Centralized audit logging client for inter-service communication.
Provides both synchronous and async methods for audit logging.
"""
import logging
import functools
from typing import Any, Optional
from uuid import UUID

import httpx

from src.core.config import settings

logger = logging.getLogger(__name__)


# ═══════════════════════════════════════════════════════════════════
# Audit Constants
# ═══════════════════════════════════════════════════════════════════

class AuditAction:
    """Standard audit action names for consistency."""
    
    # CRUD
    CREATE = "CREATE"
    READ = "READ"
    UPDATE = "UPDATE"
    DELETE = "DELETE"
    LIST = "LIST"
    
    # Authentication
    LOGIN = "LOGIN"
    LOGOUT = "LOGOUT"
    LOGIN_FAILED = "LOGIN_FAILED"
    PASSWORD_CHANGE = "PASSWORD_CHANGE"
    TOKEN_REFRESH = "TOKEN_REFRESH"
    
    # Workflow
    SUBMIT = "SUBMIT"
    APPROVE = "APPROVE"
    REJECT = "REJECT"
    CANCEL = "CANCEL"
    RECALL = "RECALL"
    COMPLETE = "COMPLETE"
    
    # System
    EXPORT = "EXPORT"
    IMPORT = "IMPORT"
    CONFIG_CHANGE = "CONFIG_CHANGE"
    SYNC = "SYNC"
    BATCH_PROCESS = "BATCH_PROCESS"
    
    # Security
    ACCESS_DENIED = "ACCESS_DENIED"
    PERMISSION_GRANT = "PERMISSION_GRANT"
    PERMISSION_REVOKE = "PERMISSION_REVOKE"
    
    # Email
    EMAIL_SENT = "EMAIL_SENT"
    EMAIL_FAILED = "EMAIL_FAILED"


class AuditResourceType:
    """Standard resource types for consistency."""
    
    USER = "User"
    LEAVE_REQUEST = "LeaveRequest"
    LEAVE_BALANCE = "LeaveBalance"
    BUSINESS_TRIP = "BusinessTrip"
    EXPENSE_REPORT = "ExpenseReport"
    EXPENSE_ITEM = "ExpenseItem"
    NOTIFICATION = "Notification"
    HOLIDAY = "Holiday"
    CLOSURE = "Closure"
    CONTRACT = "Contract"
    LOCATION = "Location"
    CONFIG = "SystemConfig"
    CALENDAR = "Calendar"
    CALENDAR_EVENT = "CalendarEvent"
    WALLET = "Wallet"
    WALLET_TRANSACTION = "WalletTransaction"
    EMAIL = "Email"
    EMAIL_TEMPLATE = "EmailTemplate"


# ═══════════════════════════════════════════════════════════════════
# Sensitive Data Patterns
# ═══════════════════════════════════════════════════════════════════

SENSITIVE_FIELDS = {
    'password', 'password_hash', 'token', 'access_token', 
    'refresh_token', 'api_key', 'secret', 'client_secret',
    'credit_card', 'ssn', 'card_number', 'cvv', 'pin',
    'private_key', 'authorization'
}


# ═══════════════════════════════════════════════════════════════════
# Enterprise Audit Logger
# ═══════════════════════════════════════════════════════════════════

class AuditLogger:
    """
    Enterprise Audit Client for inter-service audit logging.
    
    Features:
    - Automatic context enrichment (IP, endpoint, method)
    - Sensitive data sanitization
    - Fire-and-forget with error resilience
    - Entity change tracking (audit trail)
    
    Usage:
        audit = get_audit_logger("leaves-service")
        
        # Log an action
        await audit.log_action(
            action=AuditAction.CREATE,
            resource_type=AuditResourceType.LEAVE_REQUEST,
            resource_id=str(request.id),
            description="Created leave request for 5 days",
            user_id=current_user.id,
            user_email=current_user.email,
        )
        
        # Track entity changes
        await audit.track_entity(
            entity_type=AuditResourceType.LEAVE_REQUEST,
            entity_id=str(request.id),
            operation="UPDATE",
            before_data=old_data,
            after_data=new_data,
            changed_by=current_user.id,
        )
    """
    
    def __init__(self, service_name: str = "kronos"):
        self.service_name = service_name
        self.url = settings.audit_service_url
        self._timeout = 2.0

    # ─────────────────────────────────────────────────────────────
    # Audit Log Methods
    # ─────────────────────────────────────────────────────────────

    async def log_action(
        self,
        action: str,
        resource_type: str,
        resource_id: Optional[str] = None,
        user_id: Optional[UUID] = None,
        user_email: Optional[str] = None,
        description: Optional[str] = None,
        request_data: Optional[dict[str, Any]] = None,
        response_data: Optional[dict[str, Any]] = None,
        status: str = "SUCCESS",
        error_message: Optional[str] = None,
        endpoint: Optional[str] = None,
        http_method: Optional[str] = None,
        ip_address: Optional[str] = None,
        user_agent: Optional[str] = None,
    ) -> bool:
        """
        Log an action to the audit service (fire and forget).
        
        Returns True if logged successfully, False otherwise.
        """
        # Try to fill missing data from context
        try:
            from src.core.context import get_request_context
            ctx = get_request_context()
            if ctx:
                if not endpoint:
                    endpoint = ctx.get("path")
                if not http_method:
                    http_method = ctx.get("method")
                if not ip_address:
                    ip_address = ctx.get("client_ip")
                if not user_agent:
                    user_agent = ctx.get("user_agent")
        except ImportError:
            pass

        try:
            payload = {
                "user_id": str(user_id) if user_id else None,
                "user_email": user_email,
                "action": action,
                "resource_type": resource_type,
                "resource_id": str(resource_id) if resource_id else None,
                "description": description,
                "request_data": self._sanitize_data(request_data),
                "response_data": self._sanitize_data(response_data),
                "status": status,
                "error_message": error_message,
                "service_name": self.service_name,
                "endpoint": endpoint,
                "http_method": http_method,
                "ip_address": ip_address,
                "user_agent": user_agent,
            }
            
            async with httpx.AsyncClient() as client:
                response = await client.post(
                    f"{self.url}/api/v1/audit/logs",
                    json=payload,
                    timeout=self._timeout
                )
                return response.status_code == 201
                
        except Exception as e:
            logger.error(f"Failed to send audit log: {e}")
            return False

    async def log_success(
        self,
        action: str,
        resource_type: str,
        resource_id: Optional[str] = None,
        description: Optional[str] = None,
        **kwargs
    ) -> bool:
        """Convenience method for logging successful actions."""
        return await self.log_action(
            action=action,
            resource_type=resource_type,
            resource_id=resource_id,
            description=description,
            status="SUCCESS",
            **kwargs
        )
    
    async def log_failure(
        self,
        action: str,
        resource_type: str,
        error_message: str,
        resource_id: Optional[str] = None,
        description: Optional[str] = None,
        **kwargs
    ) -> bool:
        """Convenience method for logging failed actions."""
        return await self.log_action(
            action=action,
            resource_type=resource_type,
            resource_id=resource_id,
            description=description,
            status="FAILURE",
            error_message=error_message,
            **kwargs
        )
    
    async def log_error(
        self,
        action: str,
        resource_type: str,
        error_message: str,
        resource_id: Optional[str] = None,
        description: Optional[str] = None,
        **kwargs
    ) -> bool:
        """Convenience method for logging errors."""
        return await self.log_action(
            action=action,
            resource_type=resource_type,
            resource_id=resource_id,
            description=description,
            status="ERROR",
            error_message=error_message,
            **kwargs
        )

    # ─────────────────────────────────────────────────────────────
    # Audit Trail Methods
    # ─────────────────────────────────────────────────────────────

    async def track_entity(
        self,
        entity_type: str,
        entity_id: str,
        operation: str,
        before_data: Optional[dict] = None,
        after_data: Optional[dict] = None,
        changed_by: Optional[UUID] = None,
        changed_by_email: Optional[str] = None,
        change_reason: Optional[str] = None,
        request_id: Optional[str] = None,
    ) -> bool:
        """
        Track entity changes for audit trail.
        
        Returns True if tracked successfully, False otherwise.
        """
        try:
            # Calculate changed fields automatically
            changed_fields = None
            if before_data and after_data and operation == "UPDATE":
                changed_fields = [
                    key for key in set(before_data.keys()) | set(after_data.keys())
                    if before_data.get(key) != after_data.get(key)
                ]
            
            payload = {
                "entity_type": entity_type,
                "entity_id": entity_id,
                "operation": operation,
                "before_data": self._sanitize_data(before_data),
                "after_data": self._sanitize_data(after_data),
                "changed_fields": changed_fields,
                "changed_by": str(changed_by) if changed_by else None,
                "changed_by_email": changed_by_email,
                "change_reason": change_reason,
                "service_name": self.service_name,
                "request_id": request_id,
            }
            
            async with httpx.AsyncClient() as client:
                response = await client.post(
                    f"{self.url}/api/v1/audit/trail",
                    json=payload,
                    timeout=self._timeout,
                )
                return response.status_code == 201
                
        except Exception as e:
            logger.error(f"Failed to track entity change: {e}")
            return False
    
    async def track_create(
        self,
        entity_type: str,
        entity_id: str,
        data: dict,
        changed_by: Optional[UUID] = None,
        changed_by_email: Optional[str] = None,
        change_reason: Optional[str] = None,
    ) -> bool:
        """Track entity creation."""
        return await self.track_entity(
            entity_type=entity_type,
            entity_id=entity_id,
            operation="INSERT",
            after_data=data,
            changed_by=changed_by,
            changed_by_email=changed_by_email,
            change_reason=change_reason,
        )
    
    async def track_update(
        self,
        entity_type: str,
        entity_id: str,
        before_data: dict,
        after_data: dict,
        changed_by: Optional[UUID] = None,
        changed_by_email: Optional[str] = None,
        change_reason: Optional[str] = None,
    ) -> bool:
        """Track entity update."""
        return await self.track_entity(
            entity_type=entity_type,
            entity_id=entity_id,
            operation="UPDATE",
            before_data=before_data,
            after_data=after_data,
            changed_by=changed_by,
            changed_by_email=changed_by_email,
            change_reason=change_reason,
        )
    
    async def track_delete(
        self,
        entity_type: str,
        entity_id: str,
        data: dict,
        changed_by: Optional[UUID] = None,
        changed_by_email: Optional[str] = None,
        change_reason: Optional[str] = None,
    ) -> bool:
        """Track entity deletion."""
        return await self.track_entity(
            entity_type=entity_type,
            entity_id=entity_id,
            operation="DELETE",
            before_data=data,
            changed_by=changed_by,
            changed_by_email=changed_by_email,
            change_reason=change_reason,
        )

    # ─────────────────────────────────────────────────────────────
    # Helper Methods
    # ─────────────────────────────────────────────────────────────

    def _sanitize_data(self, data: Optional[dict]) -> Optional[dict]:
        """
        Sanitize sensitive data before logging.
        
        Removes or masks sensitive fields like passwords, tokens, etc.
        """
        if not data:
            return None
        
        sanitized = dict(data)
        
        for key in list(sanitized.keys()):
            key_lower = key.lower()
            if any(sf in key_lower for sf in SENSITIVE_FIELDS):
                sanitized[key] = "***REDACTED***"
            elif isinstance(sanitized[key], dict):
                sanitized[key] = self._sanitize_data(sanitized[key])
        
        return sanitized


# ═══════════════════════════════════════════════════════════════════
# Audit Decorator
# ═══════════════════════════════════════════════════════════════════

def audited(
    action: str,
    resource_type: str,
    service_name: str = "unknown",
    include_request: bool = True,
    include_response: bool = False,
    description_template: Optional[str] = None,
):
    """
    Decorator for automatic audit logging.
    
    Usage:
        @audited(
            action=AuditAction.CREATE,
            resource_type=AuditResourceType.LEAVE_REQUEST,
            service_name="leaves",
            description_template="Created leave request {leave_type_code}"
        )
        async def create_leave_request(...):
            ...
    """
    def decorator(func):
        @functools.wraps(func)
        async def wrapper(*args, **kwargs):
            audit = get_audit_logger(service_name)
            
            # Extract context from kwargs if available
            user_id = kwargs.get('user_id') or kwargs.get('current_user_id')
            user_email = kwargs.get('user_email')
            
            try:
                result = await func(*args, **kwargs)
                
                # Build description
                description = None
                if description_template:
                    try:
                        description = description_template.format(**kwargs)
                    except KeyError:
                        description = description_template
                
                # Log success
                await audit.log_success(
                    action=action,
                    resource_type=resource_type,
                    description=description,
                    user_id=user_id,
                    user_email=user_email,
                    request_data=dict(kwargs) if include_request else None,
                    response_data=result if include_response and isinstance(result, dict) else None,
                )
                
                return result
                
            except Exception as e:
                # Log failure
                await audit.log_error(
                    action=action,
                    resource_type=resource_type,
                    user_id=user_id,
                    user_email=user_email,
                    error_message=str(e),
                    request_data=dict(kwargs) if include_request else None,
                )
                raise
        
        return wrapper
    return decorator


# ═══════════════════════════════════════════════════════════════════
# Factory / Singleton
# ═══════════════════════════════════════════════════════════════════

_audit_logger: Optional[AuditLogger] = None

def get_audit_logger(service_name: str = settings.service_name) -> AuditLogger:
    """Factory function to get an audit logger for a specific service."""
    return AuditLogger(service_name)
