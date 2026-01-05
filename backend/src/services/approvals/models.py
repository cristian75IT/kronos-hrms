"""
KRONOS Approval Service - SQLAlchemy Models.

Enterprise-grade approval workflow engine models.
"""
from datetime import datetime
from decimal import Decimal
from typing import Optional, List
from uuid import UUID, uuid4
import enum

from sqlalchemy import (
    Boolean,
    Date,
    DateTime,
    ForeignKey,
    Integer,
    String,
    Text,
    Numeric,
    func,
    ARRAY,
)
from sqlalchemy.dialects.postgresql import UUID as PG_UUID, JSONB
from sqlalchemy.orm import Mapped, mapped_column, relationship

from src.core.database import Base


# ═══════════════════════════════════════════════════════════
# Enums
# ═══════════════════════════════════════════════════════════

class EntityType(str, enum.Enum):
    """Types of entities that can be approved."""
    LEAVE = "LEAVE"
    TRIP = "TRIP"
    EXPENSE = "EXPENSE"
    DOCUMENT = "DOCUMENT"
    CONTRACT = "CONTRACT"
    OVERTIME = "OVERTIME"


class ApprovalMode(str, enum.Enum):
    """How approvals are counted."""
    ANY = "ANY"              # First approval = approved
    ALL = "ALL"              # All assigned approvers must approve
    SEQUENTIAL = "SEQUENTIAL"  # Approvers in order
    MAJORITY = "MAJORITY"    # More approvals than rejections


class ExpirationAction(str, enum.Enum):
    """Action to take when approval expires."""
    REJECT = "REJECT"           # Auto-reject
    ESCALATE = "ESCALATE"       # Escalate to higher role
    AUTO_APPROVE = "AUTO_APPROVE"  # Auto-approve
    NOTIFY_ONLY = "NOTIFY_ONLY"    # Just send reminder


class ApprovalStatus(str, enum.Enum):
    """Status of an approval request."""
    PENDING = "PENDING"
    APPROVED = "APPROVED"
    REJECTED = "REJECTED"
    EXPIRED = "EXPIRED"
    CANCELLED = "CANCELLED"
    ESCALATED = "ESCALATED"
    APPROVED_CONDITIONAL = "APPROVED_CONDITIONAL"


class DecisionType(str, enum.Enum):
    """Type of approver decision."""
    APPROVED = "APPROVED"
    REJECTED = "REJECTED"
    DELEGATED = "DELEGATED"
    APPROVED_CONDITIONAL = "APPROVED_CONDITIONAL"


class HistoryAction(str, enum.Enum):
    """Actions in approval history."""
    CREATED = "CREATED"
    SUBMITTED = "SUBMITTED"
    ASSIGNED = "ASSIGNED"
    APPROVED = "APPROVED"
    REJECTED = "REJECTED"
    DELEGATED = "DELEGATED"
    ESCALATED = "ESCALATED"
    EXPIRED = "EXPIRED"
    CANCELLED = "CANCELLED"
    REMINDER_SENT = "REMINDER_SENT"
    RESUBMITTED = "RESUBMITTED"
    APPROVED_CONDITIONAL = "APPROVED_CONDITIONAL"


# ═══════════════════════════════════════════════════════════
# Models
# ═══════════════════════════════════════════════════════════

class WorkflowConfig(Base):
    """
    Workflow configuration for approval rules.
    
    Defines how approvals work for different entity types.
    """
    __tablename__ = "workflow_configs"
    __table_args__ = {"schema": "approvals"}
    
    id: Mapped[UUID] = mapped_column(
        PG_UUID(as_uuid=True),
        primary_key=True,
        default=uuid4,
    )
    
    # Entity type this workflow applies to
    entity_type: Mapped[str] = mapped_column(String(50), nullable=False, index=True)
    
    # Workflow identification
    name: Mapped[str] = mapped_column(String(200), nullable=False)
    description: Mapped[Optional[str]] = mapped_column(Text)
    
    # Approval requirements
    min_approvers: Mapped[int] = mapped_column(Integer, default=1)
    max_approvers: Mapped[Optional[int]] = mapped_column(Integer)
    approval_mode: Mapped[str] = mapped_column(String(30), default="ANY")
    
    # Approver selection - stored as array of UUID strings
    approver_role_ids: Mapped[Optional[list]] = mapped_column(JSONB, default=list)
    auto_assign_approvers: Mapped[bool] = mapped_column(Boolean, default=False)
    allow_self_approval: Mapped[bool] = mapped_column(Boolean, default=False)
    
    # Expiration settings
    expiration_hours: Mapped[Optional[int]] = mapped_column(Integer)
    expiration_action: Mapped[str] = mapped_column(String(30), default="REJECT")
    escalation_role_id: Mapped[Optional[UUID]] = mapped_column(PG_UUID(as_uuid=True))
    
    # Reminder settings
    reminder_hours_before: Mapped[Optional[int]] = mapped_column(Integer, default=24)
    send_reminders: Mapped[bool] = mapped_column(Boolean, default=True)
    
    # Conditional rules (JSON)
    conditions: Mapped[Optional[dict]] = mapped_column(JSONB)
    
    # Priority (lower = higher priority)
    priority: Mapped[int] = mapped_column(Integer, default=100)
    
    # Status
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, index=True)
    is_default: Mapped[bool] = mapped_column(Boolean, default=False)
    
    # Target roles - workflow applies only to users with these roles (empty = all)
    target_role_ids: Mapped[Optional[list]] = mapped_column(JSONB, default=list)
    
    # Audit
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        onupdate=func.now(),
    )
    created_by: Mapped[Optional[UUID]] = mapped_column(PG_UUID(as_uuid=True))
    
    # Relationships
    approval_requests: Mapped[List["ApprovalRequest"]] = relationship(
        back_populates="workflow_config"
    )


class ApprovalRequest(Base):
    """
    Instance of an approval request.
    
    Created when an entity needs approval.
    """
    __tablename__ = "approval_requests"
    __table_args__ = {"schema": "approvals"}
    
    id: Mapped[UUID] = mapped_column(
        PG_UUID(as_uuid=True),
        primary_key=True,
        default=uuid4,
    )
    
    # Reference to the entity being approved
    entity_type: Mapped[str] = mapped_column(String(50), nullable=False, index=True)
    entity_id: Mapped[UUID] = mapped_column(PG_UUID(as_uuid=True), nullable=False)
    entity_ref: Mapped[Optional[str]] = mapped_column(String(100))  # Human-readable ref
    
    # Workflow used
    workflow_config_id: Mapped[Optional[UUID]] = mapped_column(
        PG_UUID(as_uuid=True),
        ForeignKey("approvals.workflow_configs.id"),
    )
    
    # Requester
    requester_id: Mapped[UUID] = mapped_column(PG_UUID(as_uuid=True), nullable=False, index=True)
    requester_name: Mapped[Optional[str]] = mapped_column(String(200))
    
    # Request details
    title: Mapped[str] = mapped_column(String(300), nullable=False)
    description: Mapped[Optional[str]] = mapped_column(Text)
    request_metadata: Mapped[Optional[dict]] = mapped_column(JSONB)
    
    # Callback URL for notifying the originating service
    callback_url: Mapped[Optional[str]] = mapped_column(String(500))
    
    # Status
    status: Mapped[str] = mapped_column(String(30), default="PENDING", index=True)
    
    # Approval tracking
    required_approvals: Mapped[int] = mapped_column(Integer, default=1)
    received_approvals: Mapped[int] = mapped_column(Integer, default=0)
    received_rejections: Mapped[int] = mapped_column(Integer, default=0)
    
    # Current level (for sequential approvals)
    current_level: Mapped[int] = mapped_column(Integer, default=1)
    max_level: Mapped[int] = mapped_column(Integer, default=1)
    
    # Expiration
    expires_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), index=True)
    expired_action_taken: Mapped[bool] = mapped_column(Boolean, default=False)
    
    # Resolution
    resolved_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True))
    resolution_notes: Mapped[Optional[str]] = mapped_column(Text)
    final_decision_by: Mapped[Optional[UUID]] = mapped_column(PG_UUID(as_uuid=True))
    
    # Audit
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        onupdate=func.now(),
    )
    
    # Relationships
    workflow_config: Mapped[Optional["WorkflowConfig"]] = relationship(
        back_populates="approval_requests"
    )
    decisions: Mapped[List["ApprovalDecision"]] = relationship(
        back_populates="approval_request",
        cascade="all, delete-orphan",
    )
    history: Mapped[List["ApprovalHistory"]] = relationship(
        back_populates="approval_request",
        cascade="all, delete-orphan",
    )
    reminders: Mapped[List["ApprovalReminder"]] = relationship(
        back_populates="approval_request",
        cascade="all, delete-orphan",
    )


class ApprovalDecision(Base):
    """
    Individual approval decision by an approver.
    """
    __tablename__ = "approval_decisions"
    __table_args__ = {"schema": "approvals"}
    
    id: Mapped[UUID] = mapped_column(
        PG_UUID(as_uuid=True),
        primary_key=True,
        default=uuid4,
    )
    
    approval_request_id: Mapped[UUID] = mapped_column(
        PG_UUID(as_uuid=True),
        ForeignKey("approvals.approval_requests.id", ondelete="CASCADE"),
        nullable=False,
    )
    
    # Approver
    approver_id: Mapped[UUID] = mapped_column(PG_UUID(as_uuid=True), nullable=False, index=True)
    approver_name: Mapped[Optional[str]] = mapped_column(String(200))
    approver_role: Mapped[Optional[str]] = mapped_column(String(100))
    
    # Level in sequential approval
    approval_level: Mapped[int] = mapped_column(Integer, default=1)
    
    # Decision
    decision: Mapped[Optional[str]] = mapped_column(String(20))  # NULL = pending
    decision_notes: Mapped[Optional[str]] = mapped_column(Text)
    
    # Delegation
    delegated_to_id: Mapped[Optional[UUID]] = mapped_column(PG_UUID(as_uuid=True))
    delegated_to_name: Mapped[Optional[str]] = mapped_column(String(200))
    
    # Timing
    assigned_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
    )
    decided_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True))
    
    # Relationship
    approval_request: Mapped["ApprovalRequest"] = relationship(
        back_populates="decisions"
    )


class ApprovalHistory(Base):
    """
    Full audit trail of approval actions.
    """
    __tablename__ = "approval_history"
    __table_args__ = {"schema": "approvals"}
    
    id: Mapped[UUID] = mapped_column(
        PG_UUID(as_uuid=True),
        primary_key=True,
        default=uuid4,
    )
    
    approval_request_id: Mapped[UUID] = mapped_column(
        PG_UUID(as_uuid=True),
        ForeignKey("approvals.approval_requests.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    
    action: Mapped[str] = mapped_column(String(50), nullable=False)
    
    actor_id: Mapped[Optional[UUID]] = mapped_column(PG_UUID(as_uuid=True))
    actor_name: Mapped[Optional[str]] = mapped_column(String(200))
    actor_type: Mapped[Optional[str]] = mapped_column(String(30))  # USER, SYSTEM, SCHEDULER
    
    details: Mapped[Optional[dict]] = mapped_column(JSONB)
    
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
    )
    
    # Relationship
    approval_request: Mapped["ApprovalRequest"] = relationship(
        back_populates="history"
    )


class ApprovalReminder(Base):
    """
    Scheduled reminders for pending approvals.
    """
    __tablename__ = "approval_reminders"
    __table_args__ = {"schema": "approvals"}
    
    id: Mapped[UUID] = mapped_column(
        PG_UUID(as_uuid=True),
        primary_key=True,
        default=uuid4,
    )
    
    approval_request_id: Mapped[UUID] = mapped_column(
        PG_UUID(as_uuid=True),
        ForeignKey("approvals.approval_requests.id", ondelete="CASCADE"),
        nullable=False,
    )
    
    approver_id: Mapped[UUID] = mapped_column(PG_UUID(as_uuid=True), nullable=False)
    
    reminder_type: Mapped[str] = mapped_column(String(30), nullable=False)  # FIRST, SECOND, FINAL, EXPIRING
    scheduled_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False, index=True)
    sent_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True))
    
    is_sent: Mapped[bool] = mapped_column(Boolean, default=False)
    
    # Relationship
    approval_request: Mapped["ApprovalRequest"] = relationship(
        back_populates="reminders"
    )
