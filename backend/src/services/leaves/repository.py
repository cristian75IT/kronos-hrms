"""KRONOS Leave Service - Repository Layer."""
from datetime import date
from decimal import Decimal
from typing import Any, Optional
from uuid import UUID

from sqlalchemy import select, func, and_, or_
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from src.services.leaves.models import (
    LeaveRequest,
    LeaveRequestStatus,
    LeaveRequestHistory,
)
from src.shared.schemas import DataTableRequest


class LeaveRequestRepository:
    """Repository for leave requests."""

    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def get(self, id: UUID) -> Optional[LeaveRequest]:
        """Get leave request by ID."""
        result = await self._session.execute(
            select(LeaveRequest)
            .options(selectinload(LeaveRequest.history))
            .where(LeaveRequest.id == id)
        )
        return result.scalar_one_or_none()

    async def get_by_user(
        self,
        user_id: UUID,
        year: Optional[int] = None,
        status: Optional[list[LeaveRequestStatus]] = None,
    ) -> list[LeaveRequest]:
        """Get requests by user."""
        query = select(LeaveRequest).where(LeaveRequest.user_id == user_id)
        
        if year:
            query = query.where(
                func.extract("year", LeaveRequest.start_date) == year
            )
        
        if status:
            query = query.where(LeaveRequest.status.in_(status))
        
        query = query.order_by(LeaveRequest.start_date.desc())
        result = await self._session.execute(query)
        return list(result.scalars().all())

    async def get_pending_approval(
        self,
        approver_id: Optional[UUID] = None,
    ) -> list[LeaveRequest]:
        """Get requests pending approval."""
        query = (
            select(LeaveRequest)
            .where(LeaveRequest.status == LeaveRequestStatus.PENDING)
            .order_by(LeaveRequest.created_at.asc())
        )
        
        result = await self._session.execute(query)
        return list(result.scalars().all())

    async def get_all(
        self,
        status: Optional[list[LeaveRequestStatus]] = None,
        year: Optional[int] = None,
        limit: int = 50,
    ) -> list[LeaveRequest]:
        """Get all requests with optional filters."""
        query = select(LeaveRequest)
        
        if status:
            query = query.where(LeaveRequest.status.in_(status))
        
        if year:
            query = query.where(
                func.extract("year", LeaveRequest.start_date) == year
            )
        
        query = query.order_by(LeaveRequest.updated_at.desc()).limit(limit)
        result = await self._session.execute(query)
        return list(result.scalars().all())

    async def get_datatable(
        self,
        request: DataTableRequest,
        user_id: Optional[UUID] = None,
        status: Optional[list[LeaveRequestStatus]] = None,
        year: Optional[int] = None,
    ) -> tuple[list[LeaveRequest], int, int]:
        """Get requests for DataTable."""
        # Base query
        query = select(LeaveRequest)
        count_query = select(func.count(LeaveRequest.id))
        
        # Apply filters
        if user_id:
            query = query.where(LeaveRequest.user_id == user_id)
            count_query = count_query.where(LeaveRequest.user_id == user_id)
        
        if status:
            query = query.where(LeaveRequest.status.in_(status))
            count_query = count_query.where(LeaveRequest.status.in_(status))
        
        if year:
            query = query.where(func.extract("year", LeaveRequest.start_date) == year)
            count_query = count_query.where(func.extract("year", LeaveRequest.start_date) == year)
        
        # Total count
        total_result = await self._session.execute(count_query)
        total = total_result.scalar() or 0
        
        # Search filter
        if request.search_value:
            search = f"%{request.search_value}%"
            query = query.where(
                or_(
                    LeaveRequest.leave_type_code.ilike(search),
                    LeaveRequest.employee_notes.ilike(search),
                )
            )
        
        # Count after filter (simplified - same as total for now)
        filtered = total
        
        # Ordering
        order_by = request.get_order_by()
        for col_name, direction in order_by:
            if hasattr(LeaveRequest, col_name):
                col = getattr(LeaveRequest, col_name)
                query = query.order_by(col.desc() if direction == "desc" else col.asc())
        
        if not order_by:
            query = query.order_by(LeaveRequest.created_at.desc())
        
        # Pagination
        query = query.offset(request.start).limit(request.length)
        
        result = await self._session.execute(query)
        return list(result.scalars().all()), total, filtered

    async def get_by_date_range(
        self,
        start_date: date,
        end_date: date,
        user_ids: Optional[list[UUID]] = None,
        status: Optional[list[LeaveRequestStatus]] = None,
    ) -> list[LeaveRequest]:
        """Get requests overlapping a date range."""
        query = select(LeaveRequest).where(
            and_(
                LeaveRequest.start_date <= end_date,
                LeaveRequest.end_date >= start_date,
            )
        )
        
        if user_ids:
            query = query.where(LeaveRequest.user_id.in_(user_ids))
        
        if status:
            query = query.where(LeaveRequest.status.in_(status))
        
        query = query.order_by(LeaveRequest.start_date)
        result = await self._session.execute(query)
        return list(result.scalars().all())

    async def check_overlap(
        self,
        user_id: UUID,
        start_date: date,
        end_date: date,
        exclude_id: Optional[UUID] = None,
    ) -> list[LeaveRequest]:
        """Check for overlapping requests."""
        query = select(LeaveRequest).where(
            and_(
                LeaveRequest.user_id == user_id,
                LeaveRequest.start_date <= end_date,
                LeaveRequest.end_date >= start_date,
                LeaveRequest.status.not_in([
                    LeaveRequestStatus.REJECTED,
                    LeaveRequestStatus.CANCELLED,
                    LeaveRequestStatus.DRAFT,  # Drafts shouldn't block submissions
                ]),
            )
        )
        
        if exclude_id:
            query = query.where(LeaveRequest.id != exclude_id)
        
        result = await self._session.execute(query)
        return list(result.scalars().all())

    async def create(self, **kwargs: Any) -> LeaveRequest:
        """Create new leave request."""
        request = LeaveRequest(**kwargs)
        self._session.add(request)
        await self._session.flush()
        await self._session.refresh(request)
        return request

    async def update(self, id: UUID, **kwargs: Any) -> Optional[LeaveRequest]:
        """Update leave request."""
        request = await self.get(id)
        if not request:
            return None
        
        for field, value in kwargs.items():
            if hasattr(request, field) and value is not None:
                setattr(request, field, value)
        
        await self._session.flush()
        await self._session.refresh(request)
        return request

    async def delete(self, id: UUID) -> bool:
        """Delete leave request."""
        result = await self._session.execute(
            select(LeaveRequest).where(LeaveRequest.id == id)
        )
        request = result.scalar_one_or_none()
        
        if request:
            await self._session.delete(request)
            await self._session.flush()
            return True
        return False

    async def add_history(
        self,
        leave_request_id: UUID,
        from_status: Optional[LeaveRequestStatus],
        to_status: LeaveRequestStatus,
        changed_by: UUID,
        reason: Optional[str] = None,
    ) -> LeaveRequestHistory:
        """Add history entry."""
        history = LeaveRequestHistory(
            leave_request_id=leave_request_id,
            from_status=from_status,
            to_status=to_status,
            changed_by=changed_by,
            reason=reason,
        )
        self._session.add(history)
        await self._session.flush()
        return history


# LeaveBalanceRepository removed. All balance operations are now delegated to LeavesWalletClient via LeaveBalanceService.
