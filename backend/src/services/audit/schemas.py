"""KRONOS Audit Service - Pydantic Schemas."""
from datetime import datetime
from typing import Any, Optional
from uuid import UUID

from pydantic import BaseModel, Field, field_validator

from src.shared.schemas import BaseSchema, IDMixin, DataTableRequest, DataTableResponse


# ═══════════════════════════════════════════════════════════
# Audit Log Schemas
# ═══════════════════════════════════════════════════════════

class AuditLogCreate(BaseModel):
    """Schema for creating audit log entry."""
    
    user_id: Optional[UUID] = None
    user_email: Optional[str] = None
    action: str = Field(..., max_length=50)
    resource_type: str = Field(..., max_length=50)
    resource_id: Optional[str] = None
    description: Optional[str] = None
    request_data: Optional[dict] = None
    response_data: Optional[dict] = None
    ip_address: Optional[str] = None
    user_agent: Optional[str] = None
    endpoint: Optional[str] = None
    http_method: Optional[str] = None
    status: str = Field(default="SUCCESS", pattern="^(SUCCESS|FAILURE|ERROR)$")
    error_message: Optional[str] = None
    service_name: str = Field(..., max_length=50)


class AuditLogResponse(IDMixin, BaseSchema):
    """Response schema for audit log."""
    
    user_id: Optional[UUID] = None
    user_email: Optional[str] = None
    user_name: Optional[str] = None
    action: str
    resource_type: str
    resource_id: Optional[str] = None
    description: Optional[str] = None
    ip_address: Optional[str] = None
    endpoint: Optional[str] = None
    http_method: Optional[str] = None
    status: str
    error_message: Optional[str] = None
    service_name: str
    created_at: datetime

    @field_validator("ip_address", mode="before")
    @classmethod
    def serialize_ip(cls, v: Any) -> Optional[str]:
        if v is None:
            return None
        return str(v)


class AuditLogListItem(BaseModel):
    """Simplified log for lists."""
    
    id: UUID
    user_email: Optional[str]
    user_name: Optional[str] = None
    action: str
    resource_type: str
    resource_id: Optional[str]
    description: Optional[str] = None
    status: str
    service_name: str
    created_at: datetime
    
    model_config = {"from_attributes": True}


class AuditLogDataTableResponse(DataTableResponse[AuditLogListItem]):
    """DataTable response for audit logs."""
    pass


class AuditLogFilter(BaseModel):
    """Filters for audit log queries."""
    
    user_id: Optional[UUID] = None
    user_email: Optional[str] = None
    action: Optional[str] = None
    resource_type: Optional[str] = None
    resource_id: Optional[str] = None
    status: Optional[str] = None
    service_name: Optional[str] = None
    channel: Optional[str] = None
    start_date: Optional[datetime] = None
    end_date: Optional[datetime] = None


# ═══════════════════════════════════════════════════════════
# Audit Trail Schemas
# ═══════════════════════════════════════════════════════════

class AuditTrailCreate(BaseModel):
    """Schema for creating audit trail entry."""
    
    entity_type: str = Field(..., max_length=50)
    entity_id: str = Field(..., max_length=100)
    version: int = Field(default=1, ge=1)
    operation: str = Field(..., pattern="^(INSERT|UPDATE|DELETE)$")
    before_data: Optional[dict] = None
    after_data: Optional[dict] = None
    changed_fields: Optional[list[str]] = None
    changed_by: Optional[UUID] = None
    changed_by_email: Optional[str] = None
    change_reason: Optional[str] = None
    service_name: str = Field(..., max_length=50)
    request_id: Optional[str] = None


class AuditTrailResponse(IDMixin, BaseSchema):
    """Response schema for audit trail."""
    
    entity_type: str
    entity_id: str
    version: int
    operation: str
    before_data: Optional[dict] = None
    after_data: Optional[dict] = None
    changed_fields: Optional[list] = None
    changed_by: Optional[UUID] = None
    changed_by_email: Optional[str] = None
    changed_at: datetime
    change_reason: Optional[str] = None
    service_name: str


class AuditTrailListItem(BaseModel):
    """Simplified trail for lists."""
    
    id: UUID
    entity_type: str
    entity_id: str
    version: int
    operation: str
    changed_by_email: Optional[str]
    changed_at: datetime
    
    model_config = {"from_attributes": True}


class EntityHistoryResponse(BaseModel):
    """Complete history for an entity."""
    
    entity_type: str
    entity_id: str
    current_version: int
    history: list[AuditTrailResponse]


# ═══════════════════════════════════════════════════════════
# Decorator Support
# ═══════════════════════════════════════════════════════════

class AuditContext(BaseModel):
    """Context for audit decorator."""
    
    user_id: Optional[UUID] = None
    user_email: Optional[str] = None
    ip_address: Optional[str] = None
    user_agent: Optional[str] = None
    request_id: Optional[str] = None
