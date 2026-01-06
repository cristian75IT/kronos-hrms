"""
KRONOS - Leave Services Package

Modular leave service architecture for enterprise maintainability.

This package splits the monolithic LeaveService (~1800 lines) into focused modules:
- query.py: Read-only operations (~160 lines)
- crud.py: Create/Update/Delete (~230 lines)
- workflow.py: Approval state transitions (~480 lines)
- enterprise.py: Italian Labor Law compliance (~530 lines)

Usage:
    from src.services.leaves.services import LeaveService
    
    service = LeaveService(session)
    request = await service.create_request(user_id, data)
"""
from datetime import date
from decimal import Decimal
from typing import Optional
from uuid import UUID

from sqlalchemy.ext.asyncio import AsyncSession

from src.services.leaves.models import LeaveRequest, LeaveRequestStatus, LeaveInterruption
from src.services.leaves.schemas import (
    LeaveRequestCreate,
    LeaveRequestUpdate,
    ApproveRequest,
    ApproveConditionalRequest,
    RejectRequest,
    AcceptConditionRequest,
    CancelRequest,
    RecallRequest,
    PartialRecallRequest,
    SicknessInterruptionRequest,
    ModifyApprovedRequest,
    VoluntaryWorkRequest,
    DaysCalculationRequest,
    DaysCalculationResponse,
    CalendarResponse,
)
from src.shared.schemas import DataTableRequest

if False:  # TYPE_CHECKING
    from src.shared.clients import ApprovalClient

# Import sub-services
from src.services.leaves.services.query import LeaveQueryService
from src.services.leaves.services.crud import LeaveCrudService
from src.services.leaves.services.workflow import LeaveWorkflowService
from src.services.leaves.services.enterprise import LeaveEnterpriseService


class LeaveService:
    """
    Unified Leave Service façade.
    
    This class provides a single interface for all leave operations while
    delegating to specialized sub-services for maintainability.
    
    Sub-services:
    - _query: Read operations (get, list, search)
    - _crud: Create, update, delete operations
    - _workflow: Approval workflow (submit, approve, reject, etc.)
    - _enterprise: Italian Labor Law features (recall, sickness, etc.)
    """
    
    def __init__(self, session: AsyncSession, approval_client: "ApprovalClient" = None) -> None:
        self._session = session
        
        # Initialize sub-services
        self._query = LeaveQueryService(session)
        self._crud = LeaveCrudService(session)
        self._workflow = LeaveWorkflowService(session, approval_client)
        self._enterprise = LeaveEnterpriseService(session)

    @property
    def _approval_client(self) -> "ApprovalClient":
        """Access the approval client via workflow service."""
        return self._workflow._approval_client

    async def _get_user_info(self, user_id: UUID) -> Optional[dict]:
        """Delegate user info fetch to query service."""
        return await self._query._get_user_info(user_id)
    
    # ═══════════════════════════════════════════════════════════════════════
    # Query Operations (delegated to LeaveQueryService)
    # ═══════════════════════════════════════════════════════════════════════
    
    async def get_request(self, id: UUID) -> LeaveRequest:
        """Get leave request by ID."""
        return await self._query.get_request(id)
    
    async def get_user_requests(
        self,
        user_id: UUID,
        year: Optional[int] = None,
        status: Optional[list[LeaveRequestStatus]] = None,
    ) -> list[LeaveRequest]:
        """Get requests for a user."""
        return await self._query.get_user_requests(user_id, year, status)
    
    async def get_pending_approval(
        self,
        approver_id: Optional[UUID] = None,
    ) -> list[LeaveRequest]:
        """Get requests pending approval."""
        return await self._query.get_pending_approval(approver_id)
    
    async def get_delegated_pending_requests(self, delegate_id: UUID) -> list[LeaveRequest]:
        """Get pending requests that a delegate can approve."""
        return await self._query.get_delegated_pending_requests(delegate_id)
    
    async def get_requests_datatable(
        self,
        request: DataTableRequest,
        user_id: Optional[UUID] = None,
        status: Optional[list[LeaveRequestStatus]] = None,
        year: Optional[int] = None,
    ):
        """Get requests for DataTable."""
        return await self._query.get_requests_datatable(request, user_id, status, year)
    
    async def get_pending_datatable(
        self,
        request: DataTableRequest,
        approver_id: UUID,
        include_delegated: bool = True,
    ):
        """Get pending requests for DataTable."""
        return await self._query.get_pending_datatable(request, approver_id, include_delegated)
    
    async def get_all_requests(
        self,
        status: Optional[list[LeaveRequestStatus]] = None,
        year: Optional[int] = None,
        limit: int = 50,
    ) -> list[LeaveRequest]:
        """Get all requests with optional filters."""
        return await self._query.get_all_requests(status, year, limit)
    
    async def get_requests_by_range(
        self,
        start_date: date,
        end_date: date,
        user_ids: Optional[list[UUID]] = None,
        status: Optional[list[LeaveRequestStatus]] = None,
    ) -> list[LeaveRequest]:
        """Get requests overlapping a date range."""
        return await self._query.get_requests_by_range(start_date, end_date, user_ids, status)
    
    async def calculate_preview(self, request: DaysCalculationRequest) -> DaysCalculationResponse:
        """Calculate days for a preview."""
        return await self._query.calculate_preview(request)
    
    async def get_excluded_days(
        self,
        start_date: date,
        end_date: date,
        user_id: Optional[UUID] = None,
    ) -> dict:
        """Get list of excluded days (holidays/weekends) for UI."""
        return await self._query.get_excluded_days(start_date, end_date, user_id)
    
    async def get_request_interruptions(self, request_id: UUID) -> list:
        """Get all interruptions for a leave request."""
        return await self._query.get_request_interruptions(request_id)
    
    async def get_voluntary_work_requests(self, request_id: UUID) -> list:
        """Get all voluntary work requests for a leave request."""
        return await self._query.get_voluntary_work_requests(request_id)
    
    async def get_pending_voluntary_work_requests(self, manager_id: UUID) -> list:
        """Get pending voluntary work requests for manager's subordinates."""
        return await self._query.get_pending_voluntary_work_requests(manager_id)
    
    # ═══════════════════════════════════════════════════════════════════════
    # CRUD Operations (delegated to LeaveCrudService)
    # ═══════════════════════════════════════════════════════════════════════
    
    async def create_request(
        self,
        user_id: UUID,
        data: LeaveRequestCreate,
    ) -> LeaveRequest:
        """Create a new leave request (as draft)."""
        return await self._crud.create_request(user_id, data)
    
    async def update_request(
        self,
        id: UUID,
        user_id: UUID,
        data: LeaveRequestUpdate,
    ) -> LeaveRequest:
        """Update a draft request."""
        return await self._crud.update_request(id, user_id, data)
    
    async def delete_request(
        self,
        id: UUID,
        user_id: UUID,
    ) -> None:
        """Delete a draft request."""
        return await self._crud.delete_request(id, user_id)
    
    # ═══════════════════════════════════════════════════════════════════════
    # Workflow Operations (delegated to LeaveWorkflowService)
    # ═══════════════════════════════════════════════════════════════════════
    
    async def submit_request(
        self,
        id: UUID,
        user_id: UUID,
    ) -> LeaveRequest:
        """Submit a draft request for approval."""
        return await self._workflow.submit_request(id, user_id)
    
    async def approve_request(
        self,
        id: UUID,
        approver_id: UUID,
        data: ApproveRequest,
        metadata: Optional[dict] = None,
    ) -> LeaveRequest:
        """Approve a pending request."""
        return await self._workflow.approve_request(id, approver_id, data, metadata)
    
    async def approve_conditional(
        self,
        id: UUID,
        approver_id: UUID,
        data: ApproveConditionalRequest,
    ) -> LeaveRequest:
        """Approve with conditions."""
        return await self._workflow.approve_conditional(id, approver_id, data)
    
    async def accept_condition(
        self,
        id: UUID,
        user_id: UUID,
        data: AcceptConditionRequest,
    ) -> LeaveRequest:
        """Employee accepts or rejects conditions."""
        return await self._workflow.accept_condition(id, user_id, data)
    
    async def reject_request(
        self,
        id: UUID,
        approver_id: UUID,
        data: RejectRequest,
    ) -> LeaveRequest:
        """Reject a pending request."""
        return await self._workflow.reject_request(id, approver_id, data)
    
    async def revoke_approval(
        self,
        id: UUID,
        approver_id: UUID,
        reason: str,
    ) -> LeaveRequest:
        """Revoke an approved request."""
        return await self._workflow.revoke_approval(id, approver_id, reason)
    
    async def reopen_request(
        self,
        id: UUID,
        approver_id: UUID,
        notes: Optional[str] = None,
    ) -> LeaveRequest:
        """Reopen a rejected/cancelled request."""
        return await self._workflow.reopen_request(id, approver_id, notes)
    
    async def cancel_request(
        self,
        id: UUID,
        user_id: UUID,
        data: CancelRequest,
    ) -> LeaveRequest:
        """Cancel own request."""
        return await self._workflow.cancel_request(id, user_id, data)
    
    # ═══════════════════════════════════════════════════════════════════════
    # Enterprise Operations (delegated to LeaveEnterpriseService)
    # ═══════════════════════════════════════════════════════════════════════
    
    async def recall_request(
        self,
        id: UUID,
        manager_id: UUID,
        data: RecallRequest,
    ) -> LeaveRequest:
        """Recall an employee from approved leave."""
        return await self._enterprise.recall_request(id, manager_id, data)
    
    async def create_partial_recall(
        self,
        request_id: UUID,
        manager_id: UUID,
        data: PartialRecallRequest,
    ) -> LeaveInterruption:
        """Create a partial recall for specific days."""
        return await self._enterprise.create_partial_recall(request_id, manager_id, data)
    
    async def create_sickness_interruption(
        self,
        request_id: UUID,
        user_id: UUID,
        data: SicknessInterruptionRequest,
    ) -> LeaveInterruption:
        """Record sickness during vacation."""
        return await self._enterprise.create_sickness_interruption(request_id, user_id, data)
    
    async def report_user_sickness(
        self,
        request_id: UUID,
        user_id: UUID,
        data: SicknessInterruptionRequest,
    ) -> LeaveInterruption:
        """Employee reports sickness during their own vacation."""
        return await self._enterprise.report_user_sickness(request_id, user_id, data)
    
    async def request_voluntary_work(
        self,
        request_id: UUID,
        user_id: UUID,
        data: VoluntaryWorkRequest,
    ) -> LeaveInterruption:
        """Employee requests to work during vacation."""
        return await self._enterprise.request_voluntary_work(request_id, user_id, data)
    
    async def approve_voluntary_work(
        self,
        interruption_id: UUID,
        approver_id: UUID,
        notes: Optional[str] = None,
    ) -> LeaveInterruption:
        """Manager approves voluntary work request."""
        return await self._enterprise.approve_voluntary_work(interruption_id, approver_id, notes)
    
    async def reject_voluntary_work(
        self,
        interruption_id: UUID,
        approver_id: UUID,
        reason: str,
    ) -> LeaveInterruption:
        """Manager rejects voluntary work request."""
        return await self._enterprise.reject_voluntary_work(interruption_id, approver_id, reason)
    
    async def modify_approved_request(
        self,
        request_id: UUID,
        modifier_id: UUID,
        data: ModifyApprovedRequest,
    ) -> LeaveRequest:
        """Modify an already approved request."""
        return await self._enterprise.modify_approved_request(request_id, modifier_id, data)
    
    async def recalculate_for_closure(
        self,
        closure_start: date,
        closure_end: date,
    ) -> list[dict]:
        """Recalculate leave requests for a new closure."""
        return await self._enterprise.recalculate_for_closure(closure_start, closure_end)
    
    # ═══════════════════════════════════════════════════════════════════════
    # Calendar Operations (uses query and enterprise services)
    # ═══════════════════════════════════════════════════════════════════════
    
    async def get_user_calendar(
        self,
        user_id: UUID,
        start_date: date,
        end_date: date,
        include_holidays: bool = True,
    ) -> CalendarResponse:
        """Get calendar for a specific user."""
        # This method exists in the query service, re-export it
        # For now, implement directly using sub-services
        from src.services.leaves.schemas import CalendarEvent, CalendarResponse
        
        requests = await self._query.get_user_requests(
            user_id,
            year=start_date.year,
            status=[LeaveRequestStatus.APPROVED, LeaveRequestStatus.PENDING, LeaveRequestStatus.APPROVED_CONDITIONAL],
        )
        
        events = [
            CalendarEvent(
                id=str(r.id),
                title=f"{r.leave_type_code} - {r.status.value}",
                start=r.start_date,
                end=r.end_date,
                allDay=True,
                color=self._get_event_color(r.status, r.leave_type_code),
                extendedProps={"status": r.status.value, "type": r.leave_type_code},
            )
            for r in requests
            if r.start_date <= end_date and r.end_date >= start_date
        ]
        
        return CalendarResponse(events=events, holidays=[], closures=[])
    
    async def get_team_calendar(
        self,
        manager_id: UUID,
        start_date: date,
        end_date: date,
    ) -> dict:
        """Get calendar view for manager's team."""
        subordinates = await self._query._get_subordinates(manager_id)
        
        all_events = []
        for sub_id in subordinates:
            sub_calendar = await self.get_user_calendar(sub_id, start_date, end_date, include_holidays=False)
            for event in sub_calendar.events:
                event.extendedProps["user_id"] = str(sub_id)
            all_events.extend(sub_calendar.events)
        
        return {
            "events": all_events,
            "team_size": len(subordinates),
            "period": {"start": start_date.isoformat(), "end": end_date.isoformat()},
        }
    
    def _get_event_color(self, status: LeaveRequestStatus, leave_type: str) -> str:
        """Get color for calendar event."""
        status_colors = {
            LeaveRequestStatus.APPROVED: "#22C55E",
            LeaveRequestStatus.PENDING: "#F59E0B",
            LeaveRequestStatus.APPROVED_CONDITIONAL: "#EAB308",
        }
        return status_colors.get(status, "#3B82F6")


# Export for backward compatibility
__all__ = [
    "LeaveService",
    "LeaveQueryService",
    "LeaveCrudService", 
    "LeaveWorkflowService",
    "LeaveEnterpriseService",
]
