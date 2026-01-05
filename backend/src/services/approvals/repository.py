"""
KRONOS Approval Service - Repository Layer.

Data access patterns for approval entities.
"""
import logging
from datetime import datetime, timedelta
from typing import Optional, List, Dict, Any
from uuid import UUID

from sqlalchemy import select, func, and_, or_, update, delete
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from .models import (
    WorkflowConfig,
    ApprovalRequest,
    ApprovalDecision,
    ApprovalHistory,
    ApprovalReminder,
)

logger = logging.getLogger(__name__)


class WorkflowConfigRepository:
    """Repository for workflow configurations."""
    
    def __init__(self, session: AsyncSession):
        self._session = session
    
    async def create(self, config: WorkflowConfig) -> WorkflowConfig:
        """Create a new workflow config."""
        self._session.add(config)
        await self._session.flush()
        return config
    
    async def get_by_id(self, config_id: UUID) -> Optional[WorkflowConfig]:
        """Get workflow config by ID."""
        result = await self._session.execute(
            select(WorkflowConfig).where(WorkflowConfig.id == config_id)
        )
        return result.scalar_one_or_none()
    
    async def get_active_by_entity_type(self, entity_type: str) -> List[WorkflowConfig]:
        """Get active workflows for an entity type, ordered by priority."""
        result = await self._session.execute(
            select(WorkflowConfig)
            .where(
                and_(
                    WorkflowConfig.entity_type == entity_type,
                    WorkflowConfig.is_active == True,
                )
            )
            .order_by(WorkflowConfig.priority)
        )
        return list(result.scalars().all())
    
    async def get_default_for_entity_type(self, entity_type: str) -> Optional[WorkflowConfig]:
        """Get default workflow for an entity type."""
        result = await self._session.execute(
            select(WorkflowConfig)
            .where(
                and_(
                    WorkflowConfig.entity_type == entity_type,
                    WorkflowConfig.is_active == True,
                    WorkflowConfig.is_default == True,
                )
            )
        )
        return result.scalar_one_or_none()
    
    async def list_all(
        self,
        entity_type: Optional[str] = None,
        active_only: bool = True,
        offset: int = 0,
        limit: int = 100,
    ) -> List[WorkflowConfig]:
        """List all workflow configs with filters."""
        query = select(WorkflowConfig)
        
        conditions = []
        if entity_type:
            conditions.append(WorkflowConfig.entity_type == entity_type)
        if active_only:
            conditions.append(WorkflowConfig.is_active == True)
        
        if conditions:
            query = query.where(and_(*conditions))
        
        query = query.order_by(WorkflowConfig.entity_type, WorkflowConfig.priority)
        query = query.offset(offset).limit(limit)
        
        result = await self._session.execute(query)
        return list(result.scalars().all())
    
    async def update(self, config: WorkflowConfig) -> WorkflowConfig:
        """Update workflow config."""
        await self._session.flush()
        return config
    
    async def soft_delete(self, config_id: UUID) -> bool:
        """Soft delete (deactivate) workflow config."""
        result = await self._session.execute(
            update(WorkflowConfig)
            .where(WorkflowConfig.id == config_id)
            .values(is_active=False, updated_at=datetime.utcnow())
        )
        return result.rowcount > 0


class ApprovalRequestRepository:
    """Repository for approval requests."""
    
    def __init__(self, session: AsyncSession):
        self._session = session
    
    async def create(self, request: ApprovalRequest) -> ApprovalRequest:
        """Create a new approval request."""
        self._session.add(request)
        await self._session.flush()
        return request
    
    async def get_by_id(
        self,
        request_id: UUID,
        include_decisions: bool = True,
        include_history: bool = False,
    ) -> Optional[ApprovalRequest]:
        """Get approval request by ID with optional relationships."""
        query = select(ApprovalRequest).where(ApprovalRequest.id == request_id)
        
        if include_decisions:
            query = query.options(selectinload(ApprovalRequest.decisions))
        if include_history:
            query = query.options(selectinload(ApprovalRequest.history))
        
        result = await self._session.execute(query)
        return result.scalar_one_or_none()
    
    async def get_by_entity(
        self,
        entity_type: str,
        entity_id: UUID,
    ) -> Optional[ApprovalRequest]:
        """Get approval request by entity reference."""
        result = await self._session.execute(
            select(ApprovalRequest)
            .where(
                and_(
                    ApprovalRequest.entity_type == entity_type,
                    ApprovalRequest.entity_id == entity_id,
                )
            )
            .options(selectinload(ApprovalRequest.decisions))
        )
        return result.scalar_one_or_none()
    
    async def get_pending_for_approver(
        self,
        approver_id: UUID,
        entity_type: Optional[str] = None,
        offset: int = 0,
        limit: int = 50,
    ) -> List[ApprovalRequest]:
        """Get pending approval requests assigned to an approver."""
        query = (
            select(ApprovalRequest)
            .join(ApprovalDecision)
            .where(
                and_(
                    ApprovalDecision.approver_id == approver_id,
                    ApprovalDecision.decision.is_(None),
                    ApprovalRequest.status == "PENDING",
                )
            )
        )
        
        if entity_type:
            query = query.where(ApprovalRequest.entity_type == entity_type)
        
        query = query.order_by(ApprovalRequest.created_at.desc())
        query = query.offset(offset).limit(limit)
        
        result = await self._session.execute(query)
        return list(result.scalars().unique().all())

    async def get_all_pending(
        self,
        entity_type: Optional[str] = None,
        offset: int = 0,
        limit: int = 50,
    ) -> List[ApprovalRequest]:
        """Get all pending approval requests (for admins)."""
        query = select(ApprovalRequest).where(ApprovalRequest.status == "PENDING")
        
        if entity_type:
            query = query.where(ApprovalRequest.entity_type == entity_type)
        
        # Eager load decisions so we can construct the item correctly if needed
        query = query.options(selectinload(ApprovalRequest.decisions))
        
        query = query.order_by(ApprovalRequest.created_at.desc())
        query = query.offset(offset).limit(limit)
        
        result = await self._session.execute(query)
        return list(result.scalars().all())
    
    async def count_pending_for_approver(
        self,
        approver_id: UUID,
    ) -> Dict[str, int]:
        """Count pending approvals by entity type for an approver."""
        result = await self._session.execute(
            select(
                ApprovalRequest.entity_type,
                func.count(ApprovalRequest.id),
            )
            .join(ApprovalDecision)
            .where(
                and_(
                    ApprovalDecision.approver_id == approver_id,
                    ApprovalDecision.decision.is_(None),
                    ApprovalRequest.status == "PENDING",
                )
            )
            .group_by(ApprovalRequest.entity_type)
        )
        
        counts = {"total": 0}
        for entity_type, count in result.all():
            counts[entity_type] = count
            counts["total"] += count
        
        return counts
    
    async def get_expiring_requests(
        self,
        before: datetime,
    ) -> List[ApprovalRequest]:
        """Get requests expiring before a given time."""
        result = await self._session.execute(
            select(ApprovalRequest)
            .where(
                and_(
                    ApprovalRequest.status == "PENDING",
                    ApprovalRequest.expires_at <= before,
                    ApprovalRequest.expired_action_taken == False,
                )
            )
            .options(
                selectinload(ApprovalRequest.decisions),
                selectinload(ApprovalRequest.workflow_config),
            )
        )
        return list(result.scalars().all())
    
    async def get_by_requester(
        self,
        requester_id: UUID,
        status: Optional[str] = None,
        offset: int = 0,
        limit: int = 50,
    ) -> List[ApprovalRequest]:
        """Get requests by requester."""
        query = select(ApprovalRequest).where(
            ApprovalRequest.requester_id == requester_id
        )
        
        if status:
            query = query.where(ApprovalRequest.status == status)
        
        query = query.order_by(ApprovalRequest.created_at.desc())
        query = query.offset(offset).limit(limit)
        
        result = await self._session.execute(query)
        return list(result.scalars().all())
    
    async def update(self, request: ApprovalRequest) -> ApprovalRequest:
        """Update approval request."""
        request.updated_at = datetime.utcnow()
        await self._session.flush()
        return request
    
    async def delete(self, request_id: UUID) -> bool:
        """Delete approval request and related data."""
        result = await self._session.execute(
            delete(ApprovalRequest).where(ApprovalRequest.id == request_id)
        )
        return result.rowcount > 0


class ApprovalDecisionRepository:
    """Repository for approval decisions."""
    
    def __init__(self, session: AsyncSession):
        self._session = session
    
    async def create(self, decision: ApprovalDecision) -> ApprovalDecision:
        """Create a new decision record."""
        self._session.add(decision)
        await self._session.flush()
        return decision
    
    async def create_bulk(self, decisions: List[ApprovalDecision]) -> List[ApprovalDecision]:
        """Create multiple decision records."""
        self._session.add_all(decisions)
        await self._session.flush()
        return decisions
    
    async def get_by_request_and_approver(
        self,
        request_id: UUID,
        approver_id: UUID,
    ) -> Optional[ApprovalDecision]:
        """Get decision for a specific approver on a request."""
        result = await self._session.execute(
            select(ApprovalDecision)
            .where(
                and_(
                    ApprovalDecision.approval_request_id == request_id,
                    ApprovalDecision.approver_id == approver_id,
                )
            )
        )
        return result.scalar_one_or_none()
    
    async def get_pending_by_request(
        self,
        request_id: UUID,
        level: Optional[int] = None,
    ) -> List[ApprovalDecision]:
        """Get pending decisions for a request."""
        query = select(ApprovalDecision).where(
            and_(
                ApprovalDecision.approval_request_id == request_id,
                ApprovalDecision.decision.is_(None),
            )
        )
        
        if level is not None:
            query = query.where(ApprovalDecision.approval_level == level)
        
        result = await self._session.execute(query)
        return list(result.scalars().all())
    
    async def update(self, decision: ApprovalDecision) -> ApprovalDecision:
        """Update decision."""
        await self._session.flush()
        return decision
    
    async def get_decided_by_approver(
        self,
        approver_id: UUID,
        status_filter: Optional[str] = None,
        entity_type: Optional[str] = None,
        offset: int = 0,
        limit: int = 50,
    ) -> List[ApprovalDecision]:
        """Get decided approvals for an approver (for archive view)."""
        query = (
            select(ApprovalDecision)
            .join(ApprovalRequest, ApprovalDecision.approval_request_id == ApprovalRequest.id)
            .where(
                and_(
                    ApprovalDecision.approver_id == approver_id,
                    ApprovalDecision.decision.isnot(None),
                )
            )
            .options(selectinload(ApprovalDecision.approval_request))
        )
        
        if status_filter and status_filter != 'all':
            query = query.where(ApprovalDecision.decision == status_filter.upper())
        
        if entity_type:
            query = query.where(ApprovalRequest.entity_type == entity_type)
        
        query = query.order_by(ApprovalDecision.decided_at.desc())
        query = query.offset(offset).limit(limit)
        
        result = await self._session.execute(query)
        return list(result.scalars().unique().all())


class ApprovalHistoryRepository:
    """Repository for approval history."""
    
    def __init__(self, session: AsyncSession):
        self._session = session
    
    async def create(self, history: ApprovalHistory) -> ApprovalHistory:
        """Create history entry."""
        self._session.add(history)
        await self._session.flush()
        return history
    
    async def get_by_request(
        self,
        request_id: UUID,
        limit: int = 100,
    ) -> List[ApprovalHistory]:
        """Get history for a request."""
        result = await self._session.execute(
            select(ApprovalHistory)
            .where(ApprovalHistory.approval_request_id == request_id)
            .order_by(ApprovalHistory.created_at.desc())
            .limit(limit)
        )
        return list(result.scalars().all())


class ApprovalReminderRepository:
    """Repository for approval reminders."""
    
    def __init__(self, session: AsyncSession):
        self._session = session
    
    async def create(self, reminder: ApprovalReminder) -> ApprovalReminder:
        """Create reminder."""
        self._session.add(reminder)
        await self._session.flush()
        return reminder
    
    async def create_bulk(self, reminders: List[ApprovalReminder]) -> List[ApprovalReminder]:
        """Create multiple reminders."""
        self._session.add_all(reminders)
        await self._session.flush()
        return reminders
    
    async def get_due_reminders(self, before: datetime) -> List[ApprovalReminder]:
        """Get reminders that are due to be sent."""
        result = await self._session.execute(
            select(ApprovalReminder)
            .where(
                and_(
                    ApprovalReminder.is_sent == False,
                    ApprovalReminder.scheduled_at <= before,
                )
            )
        )
        return list(result.scalars().all())
    
    async def mark_sent(self, reminder_id: UUID) -> bool:
        """Mark reminder as sent."""
        result = await self._session.execute(
            update(ApprovalReminder)
            .where(ApprovalReminder.id == reminder_id)
            .values(is_sent=True, sent_at=datetime.utcnow())
        )
        return result.rowcount > 0
    
    async def delete_for_request(self, request_id: UUID) -> int:
        """Delete all reminders for a request."""
        result = await self._session.execute(
            delete(ApprovalReminder)
            .where(ApprovalReminder.approval_request_id == request_id)
        )
        return result.rowcount
