"""
KRONOS - Leave Query Service

Read-only operations for retrieving leave requests.
"""
from datetime import date
from decimal import Decimal
from typing import Optional
from uuid import UUID

from src.core.exceptions import NotFoundError
from src.services.leaves.models import LeaveRequest, LeaveRequestStatus
from src.services.leaves.schemas import DaysCalculationRequest, DaysCalculationResponse
from src.services.leaves.services.base import BaseLeaveService
from src.shared.schemas import DataTableRequest


class LeaveQueryService(BaseLeaveService):
    """
    Query operations for leave requests.
    
    Handles read-only operations:
    - Get single request
    - Get requests by user
    - Get pending approvals
    - DataTable queries
    - Date range queries
    - Day calculations
    """
    
    # ═══════════════════════════════════════════════════════════════════════
    # Single Request Queries
    # ═══════════════════════════════════════════════════════════════════════
    
    async def get_request(self, id: UUID) -> LeaveRequest:
        """Get leave request by ID."""
        request = await self._request_repo.get(id)
        if not request:
            raise NotFoundError("Leave request not found", entity_type="LeaveRequest", entity_id=str(id))
        return request
    
    # ═══════════════════════════════════════════════════════════════════════
    # User Request Queries
    # ═══════════════════════════════════════════════════════════════════════
    
    async def get_user_requests(
        self,
        user_id: UUID,
        year: Optional[int] = None,
        status: Optional[list[LeaveRequestStatus]] = None,
    ) -> list[LeaveRequest]:
        """Get requests for a user."""
        return await self._request_repo.get_by_user(user_id, year, status)
    
    async def get_pending_approval(
        self,
        approver_id: Optional[UUID] = None,
    ) -> list[LeaveRequest]:
        """Get requests pending approval."""
        return await self._request_repo.get_pending_approval(approver_id)
    
    async def get_delegated_pending_requests(self, delegate_id: UUID) -> list[LeaveRequest]:
        """
        Get pending requests that a delegate can approve on behalf of others.
        
        Finds all active delegations where this user is the delegate,
        then finds pending requests for those delegators' subordinates.
        """
        return await self._request_repo.get_delegated_pending(delegate_id)
    
    # ═══════════════════════════════════════════════════════════════════════
    # DataTable & Pagination Queries
    # ═══════════════════════════════════════════════════════════════════════
    
    async def get_requests_datatable(
        self,
        request: DataTableRequest,
        user_id: Optional[UUID] = None,
        status: Optional[list[LeaveRequestStatus]] = None,
        year: Optional[int] = None,
    ):
        """Get requests for DataTable."""
        return await self._request_repo.get_datatable(request, user_id, status, year)
    
    async def get_pending_datatable(
        self,
        request: DataTableRequest,
        approver_id: UUID,
        include_delegated: bool = True,
    ):
        """Get pending requests for DataTable with pagination."""
        return await self._request_repo.get_pending_datatable(
            request, approver_id, include_delegated
        )
    
    async def get_all_requests(
        self,
        status: Optional[list[LeaveRequestStatus]] = None,
        year: Optional[int] = None,
        limit: int = 50,
    ) -> list[LeaveRequest]:
        """Get all requests with optional filters (for approval history)."""
        return await self._request_repo.get_all(status=status, year=year, limit=limit)
    
    # ═══════════════════════════════════════════════════════════════════════
    # Date Range Queries
    # ═══════════════════════════════════════════════════════════════════════
    
    async def get_requests_by_range(
        self,
        start_date: date,
        end_date: date,
        user_ids: Optional[list[UUID]] = None,
        status: Optional[list[LeaveRequestStatus]] = None,
    ) -> list[LeaveRequest]:
        """Get requests overlapping a date range."""
        return await self._request_repo.get_by_date_range(
            start_date, end_date, user_ids, status
        )
    
    # ═══════════════════════════════════════════════════════════════════════
    # Days Calculation & Exclusions
    # ═══════════════════════════════════════════════════════════════════════
    
    async def calculate_preview(self, request: DaysCalculationRequest) -> DaysCalculationResponse:
        """Calculate days for a preview (no persistence)."""
        days = await self._calculate_days(
            request.start_date,
            request.end_date,
            request.start_half_day,
            request.end_half_day,
        )
        return DaysCalculationResponse(
            days=days,
            hours=days * Decimal("8"),  # Approximation
            message=f"Calcolati {days} giorni lavorativi escludendo festività e chiusure."
        )
    
    async def _calculate_days(
        self,
        start_date: date,
        end_date: date,
        start_half: bool,
        end_half: bool,
        user_id: Optional[UUID] = None,
    ) -> Decimal:
        """Calculate working days between dates."""
        return await self._calendar_utils.calculate_working_days(
            start_date, end_date, start_half, end_half, user_id=user_id
        )
    
    async def get_excluded_days(
        self,
        start_date: date,
        end_date: date,
        user_id: Optional[UUID] = None,
    ) -> dict:
        """Get list of excluded days (holidays/weekends) for UI."""
        return await self._calendar_utils.get_excluded_list(start_date, end_date, user_id=user_id)
    
    # ═══════════════════════════════════════════════════════════════════════
    # Interruption Queries
    # ═══════════════════════════════════════════════════════════════════════
    
    async def get_request_interruptions(self, request_id: UUID) -> list:
        """Get all interruptions for a leave request."""
        return await self._request_repo.get_interruptions(request_id)
    
    async def get_voluntary_work_requests(self, request_id: UUID) -> list:
        """Get all voluntary work requests for a leave request."""
        return await self._request_repo.get_voluntary_work_requests(request_id)
    
    async def get_pending_voluntary_work_requests(self, manager_id: UUID) -> list:
        """Get all pending voluntary work requests for manager's subordinates."""
        return await self._request_repo.get_pending_voluntary_work(manager_id)
