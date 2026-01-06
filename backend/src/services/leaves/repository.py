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
    LeaveInterruption,
    ApprovalDelegation,
)
from src.services.auth.models import User, EmployeeContract
from src.services.config.models import NationalContractVersion
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

    async def get_delegated_pending(self, delegate_id: UUID) -> list[LeaveRequest]:
        """
        Get pending requests that a delegate can approve based on active delegations.
        """
        # 1. Find active delegations for this delegate
        delegations_query = select(ApprovalDelegation.delegator_id).where(
            and_(
                ApprovalDelegation.delegate_id == delegate_id,
                ApprovalDelegation.is_active == True,
                ApprovalDelegation.start_date <= date.today(),
                ApprovalDelegation.end_date >= date.today(),
            )
        )
        delegation_result = await self._session.execute(delegations_query)
        delegator_ids = delegation_result.scalars().all()
        
        if not delegator_ids:
            return []
            
        # 2. Return pending requests where approver is one of the delegators
        # Note: In a real system, we might need more complex logic based on team scope,
        # but for now we follow the existing pattern in service_legacy.
        query = select(LeaveRequest).where(
            and_(
                LeaveRequest.status == LeaveRequestStatus.PENDING,
                LeaveRequest.approver_id.in_(delegator_ids)
            )
        )
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

    async def get_pending_datatable(
        self,
        request: DataTableRequest,
        approver_id: UUID,
        include_delegated: bool = True,
    ) -> tuple[list[LeaveRequest], int, int]:
        """Get pending requests for DataTable with optional delegated requests."""
        # 1. Base filter: strictly pending
        base_filter = LeaveRequest.status == LeaveRequestStatus.PENDING
        
        # 2. Approver filter
        approver_filter = LeaveRequest.approver_id == approver_id
        
        if include_delegated:
            # Find active delegations
            delegations_query = select(ApprovalDelegation.delegator_id).where(
                and_(
                    ApprovalDelegation.delegate_id == approver_id,
                    ApprovalDelegation.is_active == True,
                    ApprovalDelegation.start_date <= date.today(),
                    ApprovalDelegation.end_date >= date.today(),
                )
            )
            delegation_result = await self._session.execute(delegations_query)
            delegator_ids = delegation_result.scalars().all()
            
            if delegator_ids:
                approver_filter = or_(
                    approver_filter,
                    LeaveRequest.approver_id.in_(delegator_ids)
                )

        final_filter = and_(base_filter, approver_filter)
        
        # 3. Construct query
        query = select(LeaveRequest).where(final_filter)
        count_query = select(func.count(LeaveRequest.id)).where(final_filter)
        
        # Total count
        total_result = await self._session.execute(count_query)
        total = total_result.scalar() or 0
        
        # Search
        if request.search_value:
            search = f"%{request.search_value}%"
            query = query.where(
                or_(
                    LeaveRequest.leave_type_code.ilike(search),
                    LeaveRequest.employee_notes.ilike(search),
                )
            )
        
        # Count after filter
        filtered = total # Simplified
        
        # Ordering and pagination
        order_by = request.get_order_by()
        for col_name, direction in order_by:
            if hasattr(LeaveRequest, col_name):
                col = getattr(LeaveRequest, col_name)
                query = query.order_by(col.desc() if direction == "desc" else col.asc())
        
        query = query.offset(request.start).limit(request.length)
        
        result = await self._session.execute(query)
        return list(result.scalars().all()), total, filtered

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

    async def get_interruptions(self, request_id: UUID) -> list[LeaveInterruption]:
        """Get all interruptions for a leave request."""
        result = await self._session.execute(
            select(LeaveInterruption)
            .where(LeaveInterruption.leave_request_id == request_id)
            .order_by(LeaveInterruption.start_date.asc())
        )
        return list(result.scalars().all())

    async def get_voluntary_work_requests(self, request_id: UUID) -> list[LeaveInterruption]:
        """Get all voluntary work requests for a leave request."""
        result = await self._session.execute(
            select(LeaveInterruption)
            .where(
                and_(
                    LeaveInterruption.leave_request_id == request_id,
                    LeaveInterruption.interruption_type == "VOLUNTARY_WORK"
                )
            )
        )
        return list(result.scalars().all())

    async def get_pending_voluntary_work(self, manager_id: UUID) -> list[LeaveInterruption]:
        """Get pending voluntary work requests for manager's subordinates."""
        # Note: manager_id check usually requires auth client data which is in service layer.
        # This repo method only returns by status and manager_id if it's stored, 
        # but in our model 'approver_id' for interruption might not be set yet.
        # Following the pattern in service_legacy, we'd need to join with LeaveRequest to know who is the manager.
        query = (
            select(LeaveInterruption)
            .join(LeaveRequest)
            .where(
                and_(
                    LeaveInterruption.interruption_type == "VOLUNTARY_WORK",
                    LeaveInterruption.status == "PENDING_APPROVAL",
                    LeaveRequest.approver_id == manager_id
                )
            )
        )
        result = await self._session.execute(query)
        return list(result.scalars().all())

    async def get_pending_by_user_and_year(self, user_id: UUID, year: int) -> list[LeaveRequest]:
        """Get pending or conditionally approved requests for a user in a specific year."""
        from datetime import date
        stmt = select(LeaveRequest).where(
            and_(
                LeaveRequest.user_id == user_id,
                LeaveRequest.status.in_(['PENDING', 'APPROVED_CONDITIONAL']),
                LeaveRequest.start_date >= date(year, 1, 1),
                LeaveRequest.start_date <= date(year, 12, 31)
            )
        )
        result = await self._session.execute(stmt)
        return list(result.scalars().all())

    async def get_attendance_data(self, day: date, department: Optional[str] = None) -> tuple[list[User], list[LeaveRequest]]:
        """Fetch users and their leave requests for a specific date (for reporting)."""
        from src.services.auth.models import UserProfile
        from sqlalchemy.orm import selectinload, contains_eager
        
        # 1. Fetch active users
        user_stmt = select(User).where(User.is_active == True)
        if department:
            user_stmt = user_stmt.join(User.profile).where(UserProfile.department == department).options(contains_eager(User.profile))
        else:
            user_stmt = user_stmt.options(selectinload(User.profile))
        
        user_result = await self._session.execute(user_stmt)
        users = list(user_result.scalars().all())
        
        # 2. Fetch leave requests for the date
        leave_stmt = select(LeaveRequest).where(
            and_(
                LeaveRequest.start_date <= day,
                LeaveRequest.end_date >= day,
                LeaveRequest.status.in_([
                    LeaveRequestStatus.APPROVED, 
                    LeaveRequestStatus.APPROVED_CONDITIONAL
                ])
            )
        )
        leave_result = await self._session.execute(leave_stmt)
        leaves = list(leave_result.scalars().all())
        
        return users, leaves

    async def get_aggregate_attendance_data(
        self, 
        start_date: date, 
        end_date: date, 
        department: Optional[str] = None
    ) -> tuple[list[User], list[LeaveRequest]]:
        """Fetch users and their leave requests for an aggregate period."""
        from src.services.auth.models import UserProfile
        from sqlalchemy.orm import selectinload, contains_eager
        
        # 1. Fetch users
        user_stmt = select(User).where(User.is_active == True)
        if department:
            user_stmt = user_stmt.join(User.profile).where(UserProfile.department == department).options(contains_eager(User.profile))
        else:
            user_stmt = user_stmt.options(selectinload(User.profile))
        
        user_result = await self._session.execute(user_stmt)
        users = list(user_result.scalars().all())
        
        if not users:
            return [], []
            
        user_ids = [u.id for u in users]
        
        # 2. Fetch all approved leave requests in range for these users
        leave_stmt = select(LeaveRequest).where(
            and_(
                LeaveRequest.user_id.in_(user_ids),
                LeaveRequest.status.in_([
                    LeaveRequestStatus.APPROVED, 
                    LeaveRequestStatus.APPROVED_CONDITIONAL
                ]),
                or_(
                    (LeaveRequest.start_date <= end_date) & (LeaveRequest.end_date >= start_date)
                )
            )
        )
        leave_result = await self._session.execute(leave_stmt)
        leaves = list(leave_result.scalars().all())
        
        return users, leaves


class LeaveInterruptionRepository:
    """Repository for leave interruptions."""

    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def get(self, id: UUID) -> Optional[LeaveInterruption]:
        """Get interruption by ID."""
        result = await self._session.execute(
            select(LeaveInterruption).where(LeaveInterruption.id == id)
        )
        return result.scalar_one_or_none()

    async def create(self, **kwargs: Any) -> LeaveInterruption:
        """Create new interruption."""
        interruption = LeaveInterruption(**kwargs)
        self._session.add(interruption)
        await self._session.flush()
        await self._session.refresh(interruption)
        return interruption

    async def update(self, id: UUID, **kwargs: Any) -> Optional[LeaveInterruption]:
        """Update interruption."""
        interruption = await self.get(id)
        if not interruption:
            return None
        for field, value in kwargs.items():
            if hasattr(interruption, field):
                setattr(interruption, field, value)
        await self._session.flush()
        await self._session.refresh(interruption)
        return interruption

    async def check_overlap(
        self,
        request_id: UUID,
        interruption_type: str,
        start_date: date,
        end_date: date,
    ) -> Optional[LeaveInterruption]:
        """Check for overlapping interruptions of the same type."""
        query = select(LeaveInterruption).where(
            and_(
                LeaveInterruption.leave_request_id == request_id,
                LeaveInterruption.interruption_type == interruption_type,
                LeaveInterruption.status == "ACTIVE",
                LeaveInterruption.start_date <= end_date,
                LeaveInterruption.end_date >= start_date,
            )
        )
        result = await self._session.execute(query)
        return result.scalar_one_or_none()


class ApprovalDelegationRepository:
    """Repository for approval delegations."""

    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def get(self, id: UUID) -> Optional[ApprovalDelegation]:
        """Get delegation by ID."""
        result = await self._session.execute(
            select(ApprovalDelegation).where(ApprovalDelegation.id == id)
        )
        return result.scalar_one_or_none()

    async def get_active_for_delegate(self, delegate_id: UUID) -> list[ApprovalDelegation]:
        """Get active delegations for a delegate."""
        query = select(ApprovalDelegation).where(
            and_(
                ApprovalDelegation.delegate_id == delegate_id,
                ApprovalDelegation.is_active == True,
                ApprovalDelegation.start_date <= date.today(),
                ApprovalDelegation.end_date >= date.today(),
            )
        )
        result = await self._session.execute(query)
        return list(result.scalars().all())

    async def create(self, **kwargs: Any) -> ApprovalDelegation:
        """Create new delegation."""
        delegation = ApprovalDelegation(**kwargs)
        self._session.add(delegation)
        await self._session.flush()
        await self._session.refresh(delegation)
        return delegation

    async def get_by_delegator(self, delegator_id: UUID, active_only: bool = True) -> list[ApprovalDelegation]:
        """Get delegations created by a user."""
        query = select(ApprovalDelegation).where(ApprovalDelegation.delegator_id == delegator_id)
        if active_only:
             query = query.where(ApprovalDelegation.is_active == True)
        result = await self._session.execute(query.order_by(ApprovalDelegation.created_at.desc()))
        return list(result.scalars().all())

    async def get_received(self, delegate_id: UUID, active_only: bool = True) -> list[ApprovalDelegation]:
        """Get delegations received by a user."""
        from datetime import date
        today = date.today()
        query = select(ApprovalDelegation).where(ApprovalDelegation.delegate_id == delegate_id)
        if active_only:
            query = query.where(
                and_(
                    ApprovalDelegation.is_active == True,
                    ApprovalDelegation.start_date <= today,
                    ApprovalDelegation.end_date >= today,
                )
            )
        result = await self._session.execute(query.order_by(ApprovalDelegation.created_at.desc()))
        return list(result.scalars().all())

    async def check_overlap(self, delegator_id: UUID, delegate_id: UUID, start_date: date, end_date: date) -> Optional[ApprovalDelegation]:
        """Check for overlapping active delegations."""
        overlap_stmt = select(ApprovalDelegation).where(
            and_(
                ApprovalDelegation.delegator_id == delegator_id,
                ApprovalDelegation.delegate_id == delegate_id,
                ApprovalDelegation.is_active == True,
                ApprovalDelegation.start_date <= end_date,
                ApprovalDelegation.end_date >= start_date,
            )
        )
        result = await self._session.execute(overlap_stmt)
        return result.scalar_one_or_none()

    async def delete(self, id: UUID) -> bool:
        """Delete a delegation."""
        delegation = await self.get(id)
        if delegation:
            await self._session.delete(delegation)
            await self._session.flush()
            return True
        return False


class ContractRepository:
    """Repository for employee contracts and national contract versions."""

    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def get_distinct_user_ids(self) -> list[UUID]:
        """Get distinct user IDs from employee contracts."""
        query = select(EmployeeContract.user_id).distinct()
        result = await self._session.execute(query)
        return list(result.scalars().all())

    async def get_user_contracts(self, user_id: UUID) -> list[EmployeeContract]:
        """Get all contracts for a user."""
        from sqlalchemy.orm import selectinload
        query = (
            select(EmployeeContract)
            .options(selectinload(EmployeeContract.contract_type))
            .where(EmployeeContract.user_id == user_id)
            .order_by(EmployeeContract.start_date)
        )
        result = await self._session.execute(query)
        return list(result.scalars().all())

    async def get_national_contract_version(self, contract_id: UUID, reference_date: date) -> Optional[NationalContractVersion]:
        """Get national contract version valid at a specific date."""
        from sqlalchemy import or_
        from sqlalchemy.orm import selectinload
        query = (
            select(NationalContractVersion)
            .where(
                and_(
                    NationalContractVersion.national_contract_id == contract_id,
                    NationalContractVersion.valid_from <= reference_date,
                    or_(
                        NationalContractVersion.valid_to >= reference_date,
                        NationalContractVersion.valid_to == None
                    )
                )
            )
            .options(
                selectinload(NationalContractVersion.contract_type_configs),
                selectinload(NationalContractVersion.vacation_calc_mode),
                selectinload(NationalContractVersion.rol_calc_mode)
            )
            .order_by(NationalContractVersion.valid_from.desc())
            .limit(1)
        )
        result = await self._session.execute(query)
        return result.scalar_one_or_none()

    async def get_contracts_in_month(self, user_id: UUID, month_start: date, month_end: date) -> list[EmployeeContract]:
        """Get contracts overlapping a month."""
        from sqlalchemy import or_
        query = (
            select(EmployeeContract)
            .where(
                and_(
                    EmployeeContract.user_id == user_id,
                    EmployeeContract.start_date <= month_end,
                    or_(EmployeeContract.end_date >= month_start, EmployeeContract.end_date == None)
                )
            )
            .order_by(EmployeeContract.start_date.desc())
        )
        res = await self._session.execute(query)
        return list(res.scalars().all())
