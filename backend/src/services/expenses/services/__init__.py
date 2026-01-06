"""
KRONOS - Expenses Services Package

Modular expense service architecture.

This package splits the monolithic ExpenseService into focused modules:
- base.py: Shared utilities
- trips.py: Business Trip management
- allowances.py: Daily Allowance management
- reports.py: Expense Report management
- items.py: Expense Items management

Usage:
    from src.services.expenses.services import ExpenseService
"""
from typing import Optional, List
from uuid import UUID
from datetime import date

from sqlalchemy.ext.asyncio import AsyncSession

from src.services.expenses.models import TripStatus, ExpenseReportStatus, DestinationType
from src.services.expenses.schemas import (
    BusinessTripCreate, BusinessTripUpdate,
    ApproveTripRequest, RejectTripRequest,
    DailyAllowanceCreate,
    ExpenseReportCreate,
    ApproveReportRequest, RejectReportRequest, MarkPaidRequest,
    ExpenseItemCreate, ExpenseItemUpdate,
    TripDataTableRequest, ApprovalCallback
)
from src.shared.schemas import DataTableRequest

# Import sub-services
from src.services.expenses.services.base import BaseExpenseService
from src.services.expenses.services.trips import ExpenseTripService
from src.services.expenses.services.allowances import ExpenseAllowanceService
from src.services.expenses.services.reports import ExpenseReportService
from src.services.expenses.services.items import ExpenseItemService

import logging
logger = logging.getLogger(__name__)


class ExpenseService(BaseExpenseService):
    """
    Unified Expense Service façade.
    
    Delegates to specialized sub-services.
    """
    
    def __init__(self, session: AsyncSession):
        super().__init__(session)
        
        self._trips = ExpenseTripService(session)
        self._allowances = ExpenseAllowanceService(session)
        self._reports = ExpenseReportService(session)
        self._items = ExpenseItemService(session)
    
    # ═══════════════════════════════════════════════════════════════════════
    # Business Trips (delegated to ExpenseTripService)
    # ═══════════════════════════════════════════════════════════════════════
    
    async def get_trip(self, id: UUID):
        return await self._trips.get_trip(id)

    async def get_user_trips(self, user_id: UUID, status: Optional[list[TripStatus]] = None, year: Optional[int] = None):
        return await self._trips.get_user_trips(user_id, status, year)

    async def get_pending_trips(self):
        return await self._trips.get_pending_trips()

    async def get_trips_datatable(self, request: DataTableRequest, user_id: Optional[UUID] = None, status: Optional[list[TripStatus]] = None):
        return await self._trips.get_trips_datatable(request, user_id, status)

    async def get_admin_trips_datatable(self, request: TripDataTableRequest):
        return await self._trips.get_admin_trips_datatable(request)
        
    async def get_active_trips_for_date(self, target_date: date):
        return await self._trips.get_active_trips_for_date(target_date)

    async def create_trip(self, user_id: UUID, data: BusinessTripCreate):
        return await self._trips.create_trip(user_id, data)

    async def update_trip(self, id: UUID, user_id: UUID, data: BusinessTripUpdate):
        return await self._trips.update_trip(id, user_id, data)

    async def submit_trip(self, id: UUID, user_id: UUID):
        return await self._trips.submit_trip(id, user_id)

    async def approve_trip(self, id: UUID, approver_id: UUID, data: ApproveTripRequest):
        # Pass callback for allowance generation to break circular dependency
        return await self._trips.approve_trip(
            id, 
            approver_id, 
            data, 
            generate_allowances_callback=self._allowances.generate_allowances
        )

    async def reject_trip(self, id: UUID, approver_id: UUID, data: RejectTripRequest):
        return await self._trips.reject_trip(id, approver_id, data)

    async def complete_trip(self, id: UUID, user_id: UUID):
        return await self._trips.complete_trip(id, user_id)

    async def delete_trip(self, id: UUID, user_id: UUID):
        return await self._trips.delete_trip(id, user_id)

    async def cancel_trip(self, id: UUID, user_id: UUID, reason: str):
        return await self._trips.cancel_trip(id, user_id, reason)

    async def update_trip_attachment(self, id: UUID, user_id: UUID, content: bytes, filename: str, content_type: str):
        return await self._trips.update_trip_attachment(id, user_id, content, filename, content_type)

    async def handle_approval_callback(self, data: ApprovalCallback):
        """Handle approval callback routing."""
        logger.info(f"Received approval callback for {data.entity_type} {data.entity_id}: {data.status}")
        
        from uuid import uuid4
        approver_id = data.final_decision_by or uuid4() # Fallback if system auto-approved
        
        if data.entity_type == "TRIP":
            if data.status == "APPROVED":
                await self.approve_trip(
                    data.entity_id, 
                    approver_id, 
                    ApproveTripRequest(notes=data.resolution_notes)
                )
            elif data.status == "REJECTED":
                await self.reject_trip(
                    data.entity_id, 
                    approver_id, 
                    RejectTripRequest(reason=data.resolution_notes or "Rejected via workflow")
                )
            elif data.status == "CANCELLED":
                pass # Already handled or no action
                
        elif data.entity_type == "EXPENSE":
            if data.status == "APPROVED":
                await self.approve_report(
                    data.entity_id,
                    approver_id,
                    ApproveReportRequest(notes=data.resolution_notes)
                )
            elif data.status == "REJECTED":
                await self.reject_report(
                    data.entity_id,
                    approver_id,
                    RejectReportRequest(reason=data.resolution_notes or "Rejected via workflow")
                )

    # ═══════════════════════════════════════════════════════════════════════
    # Daily Allowances (delegated to ExpenseAllowanceService)
    # ═══════════════════════════════════════════════════════════════════════
    
    async def get_trip_allowances(self, trip_id: UUID):
        return await self._allowances.get_trip_allowances(trip_id)

    async def generate_allowances(self, trip_id: UUID):
        return await self._allowances.generate_allowances(trip_id)

    async def update_allowance(self, id: UUID, data: DailyAllowanceCreate):
        return await self._allowances.update_allowance(id, data)
    
    # Internal usage: _get_allowance_rate exposed if needed, or used internally by allowances service

    # ═══════════════════════════════════════════════════════════════════════
    # Expense Reports (delegated to ExpenseReportService)
    # ═══════════════════════════════════════════════════════════════════════

    async def get_report(self, id: UUID):
        return await self._reports.get_report(id)

    async def get_user_reports(self, user_id: UUID, status: Optional[list[ExpenseReportStatus]] = None):
        return await self._reports.get_user_reports(user_id, status)

    async def get_pending_reports(self):
        return await self._reports.get_pending_reports()
    
    async def get_standalone_reports(self, user_id: UUID, status: Optional[list[ExpenseReportStatus]] = None):
        return await self._reports.get_standalone_reports(user_id, status)

    async def get_admin_expenses_datatable(self, request: DataTableRequest, status: Optional[str] = None):
        return await self._reports.get_admin_expenses_datatable(request, status)

    async def create_report(self, user_id: UUID, data: ExpenseReportCreate):
        return await self._reports.create_report(user_id, data)

    async def submit_report(self, id: UUID, user_id: UUID):
        return await self._reports.submit_report(id, user_id)
        
    async def approve_report(self, id: UUID, approver_id: UUID, data: ApproveReportRequest):
        return await self._reports.approve_report(id, approver_id, data)

    async def reject_report(self, id: UUID, approver_id: UUID, data: RejectReportRequest):
        return await self._reports.reject_report(id, approver_id, data)

    async def mark_paid(self, id: UUID, data: MarkPaidRequest):
        return await self._reports.mark_paid(id, data)

    async def delete_report(self, id: UUID, user_id: UUID):
        return await self._reports.delete_report(id, user_id)

    async def cancel_report(self, id: UUID, user_id: UUID, reason: str):
        return await self._reports.cancel_report(id, user_id, reason)

    async def update_report_attachment(self, id: UUID, user_id: UUID, content: bytes, filename: str, content_type: str):
        return await self._reports.update_report_attachment(id, user_id, content, filename, content_type)

    # ═══════════════════════════════════════════════════════════════════════
    # Expense Items (delegated to ExpenseItemService)
    # ═══════════════════════════════════════════════════════════════════════

    async def add_item(self, user_id: UUID, data: ExpenseItemCreate):
        return await self._items.add_item(user_id, data)

    async def update_item(self, id: UUID, user_id: UUID, data: ExpenseItemUpdate):
        return await self._items.update_item(id, user_id, data)

    async def delete_item(self, id: UUID, user_id: UUID):
        return await self._items.delete_item(id, user_id)
    
    # Internal helpers like _get_expense_type, _map_expense_category are available in all services via BaseExpenseService
    # but the external router calls typically don't access them directly. If they do, we'd expose them.
    # Looking at original service, they were internal (_) methods.

# Export for usage
__all__ = ["ExpenseService"]
