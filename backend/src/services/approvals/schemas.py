"""
KRONOS Approval Service - Pydantic Schemas.

Request/Response schemas for the approval service API.
"""
from datetime import datetime, date
from decimal import Decimal
from typing import Optional, List, Dict, Any
from uuid import UUID

from pydantic import BaseModel, Field


# ═══════════════════════════════════════════════════════════
# Enums (as string literals for frontend compatibility)
# ═══════════════════════════════════════════════════════════

ENTITY_TYPES = ["LEAVE", "TRIP", "EXPENSE", "DOCUMENT", "CONTRACT", "OVERTIME"]
APPROVAL_MODES = ["ANY", "ALL", "SEQUENTIAL", "MAJORITY"]
EXPIRATION_ACTIONS = ["REJECT", "ESCALATE", "AUTO_APPROVE", "NOTIFY_ONLY"]
APPROVAL_STATUSES = ["PENDING", "APPROVED", "REJECTED", "EXPIRED", "CANCELLED", "ESCALATED"]
DECISION_TYPES = ["APPROVED", "REJECTED", "DELEGATED"]


# ═══════════════════════════════════════════════════════════
# Workflow Configuration Schemas
# ═══════════════════════════════════════════════════════════

class WorkflowCondition(BaseModel):
    """Conditional rules for workflow matching."""
    min_amount: Optional[float] = None
    max_amount: Optional[float] = None
    min_days: Optional[int] = None
    max_days: Optional[int] = None
    entity_subtypes: Optional[List[str]] = None  # e.g., ["VACATION", "SICK_LEAVE"]
    departments: Optional[List[str]] = None
    locations: Optional[List[str]] = None


class WorkflowConfigBase(BaseModel):
    """Base workflow configuration."""
    entity_type: str = Field(..., description="Entity type: LEAVE, TRIP, EXPENSE, etc.")
    name: str = Field(..., max_length=200)
    description: Optional[str] = None
    
    # Approval requirements
    min_approvers: int = Field(default=1, ge=1, le=10)
    max_approvers: Optional[int] = Field(default=None, ge=1, le=20)
    approval_mode: str = Field(default="ANY", description="ANY, ALL, SEQUENTIAL, MAJORITY")
    
    # Approver selection
    approver_role_ids: List[str] = Field(default_factory=list, description="Role IDs that can approve")
    auto_assign_approvers: bool = Field(default=False)
    allow_self_approval: bool = Field(default=False)
    
    # Expiration
    expiration_hours: Optional[int] = Field(default=None, ge=1, le=8760)  # Max 1 year
    expiration_action: str = Field(default="REJECT")
    escalation_role_id: Optional[str] = None
    
    # Reminders
    reminder_hours_before: Optional[int] = Field(default=24, ge=1, le=168)
    send_reminders: bool = Field(default=True)
    
    # Conditions
    conditions: Optional[WorkflowCondition] = None
    
    # Priority
    priority: int = Field(default=100, ge=1, le=1000)
    
    # Status
    is_active: bool = Field(default=True)
    is_default: bool = Field(default=False)
    
    # Target roles - workflow applies only to users with these roles
    target_role_ids: List[str] = Field(default_factory=list, description="Role IDs this workflow applies to (empty = all)")


class WorkflowConfigCreate(WorkflowConfigBase):
    """Create workflow configuration request."""
    pass


class WorkflowConfigUpdate(BaseModel):
    """Update workflow configuration request."""
    entity_type: Optional[str] = None
    name: Optional[str] = None
    description: Optional[str] = None
    min_approvers: Optional[int] = None
    max_approvers: Optional[int] = None
    approval_mode: Optional[str] = None
    approver_role_ids: Optional[List[str]] = None
    auto_assign_approvers: Optional[bool] = None
    allow_self_approval: Optional[bool] = None
    expiration_hours: Optional[int] = None
    expiration_action: Optional[str] = None
    escalation_role_id: Optional[str] = None
    reminder_hours_before: Optional[int] = None
    send_reminders: Optional[bool] = None
    conditions: Optional[WorkflowCondition] = None
    priority: Optional[int] = None
    is_active: Optional[bool] = None
    is_default: Optional[bool] = None
    target_role_ids: Optional[List[str]] = None


class WorkflowConfigResponse(WorkflowConfigBase):
    """Workflow configuration response."""
    id: UUID
    created_at: datetime
    updated_at: datetime
    created_by: Optional[UUID] = None

    class Config:
        from_attributes = True


# ═══════════════════════════════════════════════════════════
# Approval Request Schemas
# ═══════════════════════════════════════════════════════════

class ApprovalRequestCreate(BaseModel):
    """Create approval request (from other services)."""
    entity_type: str = Field(..., description="Entity type: LEAVE, TRIP, EXPENSE")
    entity_id: UUID = Field(..., description="ID of the entity being approved")
    entity_ref: Optional[str] = Field(None, description="Human-readable reference")
    
    requester_id: UUID = Field(..., description="User requesting approval")
    requester_name: Optional[str] = None
    
    title: str = Field(..., max_length=300)
    description: Optional[str] = None
    metadata: Optional[Dict[str, Any]] = Field(default_factory=dict)
    
    callback_url: Optional[str] = Field(None, description="URL to call when resolved")
    
    # Optional: override workflow
    workflow_config_id: Optional[UUID] = None
    # Optional: specify approvers directly
    approver_ids: Optional[List[UUID]] = None


class ApprovalRequestResponse(BaseModel):
    """Approval request response."""
    id: UUID
    entity_type: str
    entity_id: UUID
    entity_ref: Optional[str] = None
    
    workflow_config_id: Optional[UUID] = None
    
    requester_id: UUID
    requester_name: Optional[str] = None
    
    title: str
    description: Optional[str] = None
    metadata: Optional[Dict[str, Any]] = Field(default=None, alias="request_metadata")
    
    status: str
    required_approvals: int
    received_approvals: int
    received_rejections: int
    
    current_level: int
    max_level: int
    
    expires_at: Optional[datetime] = None
    resolved_at: Optional[datetime] = None
    resolution_notes: Optional[str] = None
    
    created_at: datetime
    updated_at: datetime
    
    # Include decisions
    decisions: Optional[List["ApprovalDecisionResponse"]] = None

    class Config:
        from_attributes = True
        populate_by_name = True


class ApprovalRequestSummary(BaseModel):
    """Summary for list views."""
    id: UUID
    entity_type: str
    entity_id: UUID
    entity_ref: Optional[str] = None
    title: str
    requester_name: Optional[str] = None
    status: str
    required_approvals: int
    received_approvals: int
    expires_at: Optional[datetime] = None
    created_at: datetime

    class Config:
        from_attributes = True


# ═══════════════════════════════════════════════════════════
# Approval Decision Schemas
# ═══════════════════════════════════════════════════════════

class ApprovalDecisionCreate(BaseModel):
    """Approve or reject request."""
    decision: str = Field(..., description="APPROVED, REJECTED, or DELEGATED")
    decision_notes: Optional[str] = None
    delegated_to_id: Optional[UUID] = None


class ApprovalDecisionResponse(BaseModel):
    """Approval decision response."""
    id: UUID
    approval_request_id: UUID
    
    approver_id: UUID
    approver_name: Optional[str] = None
    approver_role: Optional[str] = None
    approval_level: int
    
    decision: Optional[str] = None
    decision_notes: Optional[str] = None
    
    delegated_to_id: Optional[UUID] = None
    delegated_to_name: Optional[str] = None
    
    assigned_at: datetime
    decided_at: Optional[datetime] = None

    class Config:
        from_attributes = True


# ═══════════════════════════════════════════════════════════
# History Schemas
# ═══════════════════════════════════════════════════════════

class ApprovalHistoryResponse(BaseModel):
    """Approval history entry."""
    id: UUID
    approval_request_id: UUID
    action: str
    actor_id: Optional[UUID] = None
    actor_name: Optional[str] = None
    actor_type: Optional[str] = None
    details: Optional[Dict[str, Any]] = None
    created_at: datetime

    class Config:
        from_attributes = True


# ═══════════════════════════════════════════════════════════
# Pending Approvals (for approvers)
# ═══════════════════════════════════════════════════════════

class PendingApprovalItem(BaseModel):
    """Pending approval for an approver."""
    request_id: UUID
    entity_type: str
    entity_id: UUID
    entity_ref: Optional[str] = None
    
    title: str
    description: Optional[str] = None
    requester_name: Optional[str] = None
    
    approval_level: int
    is_urgent: bool = False
    expires_at: Optional[datetime] = None
    days_pending: int
    
    created_at: datetime


class PendingApprovalsResponse(BaseModel):
    """List of pending approvals for current user."""
    total: int
    urgent_count: int
    items: List[PendingApprovalItem]


class PendingCountResponse(BaseModel):
    """Quick count of pending approvals."""
    total: int
    urgent: int
    by_type: Dict[str, int]


class ArchivedApprovalItem(BaseModel):
    """Archived approval decision for an approver."""
    request_id: UUID
    entity_type: str
    entity_id: UUID
    entity_ref: Optional[str] = None
    
    title: str
    description: Optional[str] = None
    requester_name: Optional[str] = None
    
    decision: str  # APPROVED, REJECTED, DELEGATED
    decision_notes: Optional[str] = None
    decided_at: datetime
    
    created_at: datetime


class ArchivedApprovalsResponse(BaseModel):
    """List of archived approvals for current user."""
    total: int
    items: List[ArchivedApprovalItem]


# ═══════════════════════════════════════════════════════════
# Internal / Callback Schemas
# ═══════════════════════════════════════════════════════════

class ApprovalCallbackPayload(BaseModel):
    """Payload sent to callback URL when resolved."""
    approval_request_id: UUID
    entity_type: str
    entity_id: UUID
    status: str  # APPROVED, REJECTED, EXPIRED, etc.
    resolved_at: datetime
    resolution_notes: Optional[str] = None
    final_decision_by: Optional[UUID] = None
    decisions: List[ApprovalDecisionResponse]


class ApprovalStatusCheck(BaseModel):
    """Check approval status response."""
    entity_type: str
    entity_id: UUID
    has_pending_request: bool
    approval_request_id: Optional[UUID] = None
    status: Optional[str] = None
    required_approvals: Optional[int] = None
    received_approvals: Optional[int] = None


# ═══════════════════════════════════════════════════════════
# Admin / Config Schemas
# ═══════════════════════════════════════════════════════════

class EntityTypeInfo(BaseModel):
    """Information about an entity type."""
    code: str
    name: str
    description: str


class ApprovalModeInfo(BaseModel):
    """Information about an approval mode."""
    code: str
    name: str
    description: str


class ExpirationActionInfo(BaseModel):
    """Information about an expiration action."""
    code: str
    name: str
    description: str


# ═══════════════════════════════════════════════════════════
# DataTable Schemas
# ═══════════════════════════════════════════════════════════

class DataTableRequest(BaseModel):
    """DataTable server-side request."""
    draw: int = 1
    start: int = 0
    length: int = 25
    search_value: Optional[str] = None
    order_column: Optional[str] = None
    order_dir: str = "desc"
    filters: Dict[str, Any] = Field(default_factory=dict)


class DataTableResponse(BaseModel):
    """DataTable server-side response."""
    draw: int
    recordsTotal: int
    recordsFiltered: int
    data: List[Any]


# Update forward references
ApprovalRequestResponse.model_rebuild()
