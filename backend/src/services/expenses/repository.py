"""KRONOS Expense Service - Repository Layer."""
from datetime import date
from decimal import Decimal
from typing import Any, Optional
from uuid import UUID

from sqlalchemy import select, func, and_, desc
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from src.services.expenses.models import (
    BusinessTrip,
    TripStatus,
    DailyAllowance,
    ExpenseReport,
    ExpenseReportStatus,
    ExpenseItem,
)
from src.shared.schemas import DataTableRequest


class BusinessTripRepository:
    """Repository for business trips."""

    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def get(self, id: UUID) -> Optional[BusinessTrip]:
        """Get trip by ID."""
        result = await self._session.execute(
            select(BusinessTrip)
            .options(
                selectinload(BusinessTrip.daily_allowances),
                selectinload(BusinessTrip.expense_reports),
                selectinload(BusinessTrip.attachments),
            )
            .where(BusinessTrip.id == id)
        )
        return result.scalar_one_or_none()

    async def get_by_user(
        self,
        user_id: UUID,
        status: Optional[list[TripStatus]] = None,
        year: Optional[int] = None,
    ) -> list[BusinessTrip]:
        """Get trips by user."""
        query = select(BusinessTrip).where(BusinessTrip.user_id == user_id)
        
        if status:
            query = query.where(BusinessTrip.status.in_(status))
        
        if year:
            query = query.where(func.extract("year", BusinessTrip.start_date) == year)
        
        query = query.order_by(desc(BusinessTrip.start_date))
        result = await self._session.execute(query)
        return list(result.scalars().all())

    async def get_pending_approval(self) -> list[BusinessTrip]:
        """Get trips pending approval."""
        result = await self._session.execute(
            select(BusinessTrip)
            .where(BusinessTrip.status == TripStatus.PENDING)
            .order_by(BusinessTrip.created_at)
        )
        return list(result.scalars().all())

    async def get_active_trips_for_date(self, target_date: date) -> list[BusinessTrip]:
        """Get all approved/completed/ongoing trips for a specific date across all users."""
        active_statuses = [TripStatus.APPROVED, TripStatus.COMPLETED, TripStatus.ONGOING]
        
        result = await self._session.execute(
            select(BusinessTrip)
            .where(
                and_(
                    BusinessTrip.status.in_(active_statuses),
                    BusinessTrip.start_date <= target_date,
                    BusinessTrip.end_date >= target_date
                )
            )
        )
        return list(result.scalars().all())

    async def get_datatable(
        self,
        request: DataTableRequest,
        user_id: Optional[UUID] = None,
        status: Optional[list[TripStatus]] = None,
    ) -> tuple[list[BusinessTrip], int, int]:
        """Get trips for DataTable."""
        query = select(BusinessTrip)
        count_query = select(func.count(BusinessTrip.id))
        
        if user_id:
            query = query.where(BusinessTrip.user_id == user_id)
            count_query = count_query.where(BusinessTrip.user_id == user_id)
        
        if status:
            query = query.where(BusinessTrip.status.in_(status))
            count_query = count_query.where(BusinessTrip.status.in_(status))
        
        total_result = await self._session.execute(count_query)
        total = total_result.scalar() or 0
        
        query = query.order_by(desc(BusinessTrip.start_date))
        query = query.offset(request.start).limit(request.length)
        
        result = await self._session.execute(query)
        return list(result.scalars().all()), total, total

    async def create(self, **kwargs: Any) -> BusinessTrip:
        """Create trip."""
        trip = BusinessTrip(**kwargs)
        self._session.add(trip)
        await self._session.flush()
        return trip

    async def update(self, id: UUID, **kwargs: Any) -> Optional[BusinessTrip]:
        """Update trip."""
        trip = await self.get(id)
        if not trip:
            return None
        
        for field, value in kwargs.items():
            if hasattr(trip, field) and value is not None:
                setattr(trip, field, value)
        
        await self._session.flush()
        return trip

    async def delete(self, id: UUID) -> bool:
        """Delete trip."""
        trip = await self.get(id)
        if not trip:
            return False
        
        await self._session.delete(trip)
        await self._session.flush()
        return True


class DailyAllowanceRepository:
    """Repository for daily allowances."""

    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def get_by_trip(self, trip_id: UUID) -> list[DailyAllowance]:
        """Get allowances for a trip."""
        result = await self._session.execute(
            select(DailyAllowance)
            .where(DailyAllowance.trip_id == trip_id)
            .order_by(DailyAllowance.date)
        )
        return list(result.scalars().all())

    async def get_by_id(self, id: UUID) -> Optional[DailyAllowance]:
        """Get allowance by ID."""
        result = await self._session.execute(
            select(DailyAllowance).where(DailyAllowance.id == id)
        )
        return result.scalar_one_or_none()

    async def create(self, **kwargs: Any) -> DailyAllowance:
        """Create allowance."""
        allowance = DailyAllowance(**kwargs)
        self._session.add(allowance)
        await self._session.flush()
        return allowance

    async def update(self, id: UUID, **kwargs: Any) -> Optional[DailyAllowance]:
        """Update allowance."""
        result = await self._session.execute(
            select(DailyAllowance).where(DailyAllowance.id == id)
        )
        allowance = result.scalar_one_or_none()
        if not allowance:
            return None
        
        for field, value in kwargs.items():
            if hasattr(allowance, field) and value is not None:
                setattr(allowance, field, value)
        
        await self._session.flush()
        return allowance

    async def delete_by_trip(self, trip_id: UUID) -> int:
        """Delete all allowances for a trip."""
        result = await self._session.execute(
            select(DailyAllowance).where(DailyAllowance.trip_id == trip_id)
        )
        allowances = result.scalars().all()
        count = len(allowances)
        
        for a in allowances:
            await self._session.delete(a)
        
        await self._session.flush()
        return count


class ExpenseReportRepository:
    """Repository for expense reports."""

    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def get(self, id: UUID) -> Optional[ExpenseReport]:
        """Get report by ID."""
        result = await self._session.execute(
            select(ExpenseReport)
            .options(
                selectinload(ExpenseReport.items),
                selectinload(ExpenseReport.attachments),
            )
            .where(ExpenseReport.id == id)
        )
        return result.scalar_one_or_none()

    async def get_by_trip(self, trip_id: UUID) -> list[ExpenseReport]:
        """Get reports for a trip."""
        result = await self._session.execute(
            select(ExpenseReport)
            .where(ExpenseReport.trip_id == trip_id)
            .order_by(desc(ExpenseReport.created_at))
        )
        return list(result.scalars().all())

    async def get_by_user(
        self,
        user_id: UUID,
        status: Optional[list[ExpenseReportStatus]] = None,
    ) -> list[ExpenseReport]:
        """Get reports by user."""
        query = select(ExpenseReport).where(ExpenseReport.user_id == user_id)
        
        if status:
            query = query.where(ExpenseReport.status.in_(status))
        
        query = query.order_by(desc(ExpenseReport.created_at))
        result = await self._session.execute(query)
        return list(result.scalars().all())

    async def get_pending_approval(self) -> list[ExpenseReport]:
        """Get reports pending approval."""
        result = await self._session.execute(
            select(ExpenseReport)
            .where(ExpenseReport.status == ExpenseReportStatus.SUBMITTED)
            .order_by(ExpenseReport.created_at)
        )
        return list(result.scalars().all())

    async def get_datatable(
        self,
        request: DataTableRequest,
        user_id: Optional[UUID] = None,
        status: Optional[list[ExpenseReportStatus]] = None,
    ) -> tuple[list[ExpenseReport], int, int]:
        """Get reports for DataTable."""
        query = select(ExpenseReport).options(
            selectinload(ExpenseReport.trip),
            selectinload(ExpenseReport.items)
        )
        count_query = select(func.count(ExpenseReport.id))
        
        if user_id:
            query = query.where(ExpenseReport.user_id == user_id)
            count_query = count_query.where(ExpenseReport.user_id == user_id)
        
        if status:
            query = query.where(ExpenseReport.status.in_(status))
            count_query = count_query.where(ExpenseReport.status.in_(status))
        
        total_result = await self._session.execute(count_query)
        total = total_result.scalar() or 0
        
        query = query.order_by(desc(ExpenseReport.created_at))
        query = query.offset(request.start).limit(request.length)
        
        result = await self._session.execute(query)
        return list(result.scalars().all()), total, total

    async def generate_report_number(self, year: int) -> str:
        """Generate unique report number."""
        # Get count of reports for this year
        result = await self._session.execute(
            select(func.count(ExpenseReport.id))
            .where(func.extract("year", ExpenseReport.created_at) == year)
        )
        count = (result.scalar() or 0) + 1
        return f"NS-{year}-{count:05d}"

    async def create(self, **kwargs: Any) -> ExpenseReport:
        """Create report."""
        report = ExpenseReport(**kwargs)
        self._session.add(report)
        await self._session.flush()
        return report

    async def update(self, id: UUID, **kwargs: Any) -> Optional[ExpenseReport]:
        """Update report."""
        report = await self.get(id)
        if not report:
            return None
        
        for field, value in kwargs.items():
            if hasattr(report, field) and value is not None:
                setattr(report, field, value)
        
        await self._session.flush()
        return report

    async def recalculate_total(self, id: UUID) -> Decimal:
        """Recalculate report total from items."""
        result = await self._session.execute(
            select(func.sum(ExpenseItem.amount_eur))
            .where(ExpenseItem.report_id == id)
        )
        total = result.scalar() or Decimal(0)
        
        await self.update(id, total_amount=total)
        return total

    async def delete(self, id: UUID) -> bool:
        """Delete report."""
        report = await self.get(id)
        if not report:
            return False
        
        await self._session.delete(report)
        await self._session.flush()
        return True


class ExpenseItemRepository:
    """Repository for expense items."""

    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def get(self, id: UUID) -> Optional[ExpenseItem]:
        """Get item by ID."""
        result = await self._session.execute(
            select(ExpenseItem).where(ExpenseItem.id == id)
        )
        return result.scalar_one_or_none()

    async def get_by_report(self, report_id: UUID) -> list[ExpenseItem]:
        """Get items for a report."""
        result = await self._session.execute(
            select(ExpenseItem)
            .where(ExpenseItem.report_id == report_id)
            .order_by(ExpenseItem.date)
        )
        return list(result.scalars().all())

    async def create(self, **kwargs: Any) -> ExpenseItem:
        """Create item."""
        item = ExpenseItem(**kwargs)
        self._session.add(item)
        await self._session.flush()
        return item

    async def update(self, id: UUID, **kwargs: Any) -> Optional[ExpenseItem]:
        """Update item."""
        item = await self.get(id)
        if not item:
            return None
        
        for field, value in kwargs.items():
            if hasattr(item, field) and value is not None:
                setattr(item, field, value)
        
        await self._session.flush()
        return item

    async def delete(self, id: UUID) -> bool:
        """Delete item."""
        item = await self.get(id)
        if not item:
            return False
        
        await self._session.delete(item)
        await self._session.flush()
        return True
