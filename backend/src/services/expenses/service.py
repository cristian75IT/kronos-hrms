"""KRONOS Expense Service - Business Logic."""
from datetime import date, datetime, timedelta
from decimal import Decimal
from typing import Optional
from uuid import UUID

import httpx
from sqlalchemy.ext.asyncio import AsyncSession

from src.core.config import settings
from src.core.exceptions import NotFoundError, BusinessRuleError, ValidationError
from src.services.expenses.models import (
    TripStatus,
    ExpenseReportStatus,
    DestinationType,
)
from src.services.expenses.repository import (
    BusinessTripRepository,
    DailyAllowanceRepository,
    ExpenseReportRepository,
    ExpenseItemRepository,
)
from src.services.expenses.schemas import (
    BusinessTripCreate,
    BusinessTripUpdate,
    DailyAllowanceCreate,
    ExpenseReportCreate,
    ExpenseItemCreate,
    ExpenseItemUpdate,
    ApproveTripRequest,
    RejectTripRequest,
    ApproveReportRequest,
    RejectReportRequest,
    MarkPaidRequest,
)
from src.shared.schemas import DataTableRequest


class ExpenseService:
    """Service for expense management."""

    def __init__(self, session: AsyncSession) -> None:
        self._session = session
        self._trip_repo = BusinessTripRepository(session)
        self._allowance_repo = DailyAllowanceRepository(session)
        self._report_repo = ExpenseReportRepository(session)
        self._item_repo = ExpenseItemRepository(session)

    # ═══════════════════════════════════════════════════════════
    # Business Trip Operations
    # ═══════════════════════════════════════════════════════════

    async def get_trip(self, id: UUID):
        """Get trip by ID."""
        trip = await self._trip_repo.get(id)
        if not trip:
            raise NotFoundError("Business trip not found", entity_type="BusinessTrip", entity_id=str(id))
        return trip

    async def get_user_trips(
        self,
        user_id: UUID,
        status: Optional[list[TripStatus]] = None,
        year: Optional[int] = None,
    ):
        """Get trips for a user."""
        return await self._trip_repo.get_by_user(user_id, status, year)

    async def get_pending_trips(self):
        """Get trips pending approval."""
        return await self._trip_repo.get_pending_approval()

    async def get_trips_datatable(
        self,
        request: DataTableRequest,
        user_id: Optional[UUID] = None,
        status: Optional[list[TripStatus]] = None,
    ):
        """Get trips for DataTable."""
        return await self._trip_repo.get_datatable(request, user_id, status)

    async def create_trip(self, user_id: UUID, data: BusinessTripCreate):
        """Create new business trip."""
        return await self._trip_repo.create(
            user_id=user_id,
            status=TripStatus.DRAFT,
            **data.model_dump(),
        )

    async def update_trip(self, id: UUID, user_id: UUID, data: BusinessTripUpdate):
        """Update trip (draft only)."""
        trip = await self.get_trip(id)
        
        if trip.status != TripStatus.DRAFT:
            raise BusinessRuleError("Only draft trips can be updated")
        
        if trip.user_id != user_id:
            raise BusinessRuleError("Cannot update another user's trip")
        
        return await self._trip_repo.update(id, **data.model_dump(exclude_unset=True))

    async def submit_trip(self, id: UUID, user_id: UUID):
        """Submit trip for approval."""
        trip = await self.get_trip(id)
        
        if trip.status != TripStatus.DRAFT:
            raise BusinessRuleError("Only draft trips can be submitted")
        
        if trip.user_id != user_id:
            raise BusinessRuleError("Cannot submit another user's trip")
        
        await self._trip_repo.update(id, status=TripStatus.PENDING)
        
        # Send notification to approvers
        await self._send_notification(
            user_id=user_id,
            notification_type="trip_submitted",
            title="Trasferta sottomessa",
            message=f"Trasferta '{trip.title}' sottomessa per approvazione",
            entity_type="BusinessTrip",
            entity_id=str(id),
        )
        
        return await self.get_trip(id)

    async def approve_trip(self, id: UUID, approver_id: UUID, data: ApproveTripRequest):
        """Approve trip."""
        trip = await self.get_trip(id)
        
        if trip.status != TripStatus.PENDING:
            raise BusinessRuleError("Only pending trips can be approved")
        
        await self._trip_repo.update(
            id,
            status=TripStatus.APPROVED,
            approver_id=approver_id,
            approved_at=datetime.utcnow(),
            approver_notes=data.notes,
        )
        
        # Auto-generate daily allowances
        await self.generate_allowances(id)
        
        # Send notification to employee
        await self._send_notification(
            user_id=trip.user_id,
            notification_type="trip_approved",
            title="Trasferta approvata",
            message=f"La tua trasferta '{trip.title}' è stata approvata",
            entity_type="BusinessTrip",
            entity_id=str(id),
        )
        
        return await self.get_trip(id)

    async def reject_trip(self, id: UUID, approver_id: UUID, data: RejectTripRequest):
        """Reject trip."""
        trip = await self.get_trip(id)
        
        if trip.status != TripStatus.PENDING:
            raise BusinessRuleError("Only pending trips can be rejected")
        
        await self._trip_repo.update(
            id,
            status=TripStatus.REJECTED,
            approver_id=approver_id,
            approver_notes=data.reason,
        )
        
        return await self.get_trip(id)

    async def complete_trip(self, id: UUID, user_id: UUID):
        """Mark trip as completed."""
        trip = await self.get_trip(id)
        
        if trip.status != TripStatus.APPROVED:
            raise BusinessRuleError("Only approved trips can be completed")
        
        if trip.user_id != user_id:
            raise BusinessRuleError("Cannot complete another user's trip")
        
        await self._trip_repo.update(id, status=TripStatus.COMPLETED)
        return await self.get_trip(id)

    # ═══════════════════════════════════════════════════════════
    # Daily Allowance Operations
    # ═══════════════════════════════════════════════════════════

    async def get_trip_allowances(self, trip_id: UUID):
        """Get allowances for a trip."""
        return await self._allowance_repo.get_by_trip(trip_id)

    async def generate_allowances(self, trip_id: UUID):
        """Auto-generate daily allowances for a trip."""
        trip = await self.get_trip(trip_id)
        
        # Delete existing
        await self._allowance_repo.delete_by_trip(trip_id)
        
        # Get rate from config
        rate = await self._get_allowance_rate(trip.destination_type)
        
        # Generate for each day
        current = trip.start_date
        allowances = []
        
        while current <= trip.end_date:
            # First and last day are typically half days unless single-day trip
            is_first = current == trip.start_date
            is_last = current == trip.end_date
            is_single_day = trip.start_date == trip.end_date
            
            # Full day if: middle of trip OR single day trip
            is_full = (not is_first and not is_last) or is_single_day
            
            base_amount = rate["full_day"] if is_full else rate["half_day"]
            
            allowance = await self._allowance_repo.create(
                trip_id=trip_id,
                date=current,
                is_full_day=is_full,
                base_amount=Decimal(str(base_amount)),
                meals_deduction=Decimal(0),
                final_amount=Decimal(str(base_amount)),
            )
            allowances.append(allowance)
            current += timedelta(days=1)
        
        return allowances

    async def update_allowance(
        self,
        id: UUID,
        data: DailyAllowanceCreate,
    ):
        """Update daily allowance."""
        # Get allowance to retrieve trip info
        allowance = await self._allowance_repo.get_by_id(id)
        trip = await self.get_trip(allowance.trip_id) if allowance else None
        destination_type = trip.destination_type if trip else DestinationType.NATIONAL
        
        # Recalculate based on meals
        rate = await self._get_allowance_rate(destination_type)
        
        meals_deduction = Decimal(0)
        if data.breakfast_provided:
            meals_deduction += Decimal(str(rate.get("meals_deduction", 0))) / 3
        if data.lunch_provided:
            meals_deduction += Decimal(str(rate.get("meals_deduction", 0))) / 3
        if data.dinner_provided:
            meals_deduction += Decimal(str(rate.get("meals_deduction", 0))) / 3
        
        base_amount = Decimal(str(rate["full_day"] if data.is_full_day else rate["half_day"]))
        final_amount = base_amount - meals_deduction
        
        return await self._allowance_repo.update(
            id,
            is_full_day=data.is_full_day,
            breakfast_provided=data.breakfast_provided,
            lunch_provided=data.lunch_provided,
            dinner_provided=data.dinner_provided,
            meals_deduction=meals_deduction,
            final_amount=final_amount,
            notes=data.notes,
        )

    async def _get_allowance_rate(self, destination_type: DestinationType) -> dict:
        """Get allowance rate from config service."""
        try:
            async with httpx.AsyncClient() as client:
                response = await client.get(
                    f"{settings.config_service_url}/api/v1/allowance-rules",
                    timeout=5.0,
                )
                if response.status_code == 200:
                    rules = response.json()
                    for rule in rules:
                        if rule.get("destination_type") == destination_type.value:
                            return {
                                "full_day": rule.get("full_day_amount", 50),
                                "half_day": rule.get("half_day_amount", 25),
                                "meals_deduction": rule.get("meals_deduction", 15),
                            }
        except Exception:
            pass
        
        # Default values
        return {"full_day": 50, "half_day": 25, "meals_deduction": 15}

    # ═══════════════════════════════════════════════════════════
    # Expense Report Operations
    # ═══════════════════════════════════════════════════════════

    async def get_report(self, id: UUID):
        """Get expense report by ID."""
        report = await self._report_repo.get(id)
        if not report:
            raise NotFoundError("Expense report not found", entity_type="ExpenseReport", entity_id=str(id))
        return report

    async def get_user_reports(
        self,
        user_id: UUID,
        status: Optional[list[ExpenseReportStatus]] = None,
    ):
        """Get reports for a user."""
        return await self._report_repo.get_by_user(user_id, status)

    async def get_pending_reports(self):
        """Get reports pending approval."""
        return await self._report_repo.get_pending_approval()

    async def create_report(self, user_id: UUID, data: ExpenseReportCreate):
        """Create expense report."""
        # Verify trip exists and belongs to user
        trip = await self.get_trip(data.trip_id)
        if trip.user_id != user_id:
            raise BusinessRuleError("Cannot create report for another user's trip")
        
        # Generate report number
        report_number = await self._report_repo.generate_report_number(
            date.today().year
        )
        
        return await self._report_repo.create(
            trip_id=data.trip_id,
            user_id=user_id,
            report_number=report_number,
            title=data.title,
            period_start=data.period_start,
            period_end=data.period_end,
            employee_notes=data.employee_notes,
            status=ExpenseReportStatus.DRAFT,
            total_amount=Decimal(0),
        )

    async def submit_report(self, id: UUID, user_id: UUID):
        """Submit report for approval."""
        report = await self.get_report(id)
        
        if report.status != ExpenseReportStatus.DRAFT:
            raise BusinessRuleError("Only draft reports can be submitted")
        
        if report.user_id != user_id:
            raise BusinessRuleError("Cannot submit another user's report")
        
        # Recalculate total
        await self._report_repo.recalculate_total(id)
        
        await self._report_repo.update(id, status=ExpenseReportStatus.SUBMITTED)
        
        return await self.get_report(id)

    async def approve_report(self, id: UUID, approver_id: UUID, data: ApproveReportRequest):
        """Approve expense report."""
        report = await self.get_report(id)
        
        if report.status != ExpenseReportStatus.SUBMITTED:
            raise BusinessRuleError("Only submitted reports can be approved")
        
        # Handle item-level approvals
        if data.item_approvals:
            for item_id, approved in data.item_approvals.items():
                await self._item_repo.update(
                    UUID(item_id),
                    is_approved=approved,
                )
        
        approved_amount = data.approved_amount or report.total_amount
        
        await self._report_repo.update(
            id,
            status=ExpenseReportStatus.APPROVED,
            approved_amount=approved_amount,
            approver_id=approver_id,
            approved_at=datetime.utcnow(),
            approver_notes=data.notes,
        )
        
        return await self.get_report(id)

    async def reject_report(self, id: UUID, approver_id: UUID, data: RejectReportRequest):
        """Reject expense report."""
        report = await self.get_report(id)
        
        if report.status != ExpenseReportStatus.SUBMITTED:
            raise BusinessRuleError("Only submitted reports can be rejected")
        
        await self._report_repo.update(
            id,
            status=ExpenseReportStatus.REJECTED,
            approver_notes=data.reason,
        )
        
        return await self.get_report(id)

    async def mark_paid(self, id: UUID, data: MarkPaidRequest):
        """Mark report as paid."""
        report = await self.get_report(id)
        
        if report.status != ExpenseReportStatus.APPROVED:
            raise BusinessRuleError("Only approved reports can be marked as paid")
        
        await self._report_repo.update(
            id,
            status=ExpenseReportStatus.PAID,
            paid_at=datetime.utcnow(),
            payment_reference=data.payment_reference,
        )
        
        return await self.get_report(id)

    # ═══════════════════════════════════════════════════════════
    # Expense Item Operations
    # ═══════════════════════════════════════════════════════════

    async def add_item(self, user_id: UUID, data: ExpenseItemCreate):
        """Add expense item to report."""
        report = await self.get_report(data.report_id)
        
        if report.user_id != user_id:
            raise BusinessRuleError("Cannot add items to another user's report")
        
        if report.status != ExpenseReportStatus.DRAFT:
            raise BusinessRuleError("Can only add items to draft reports")
        
        # Get expense type
        expense_type = await self._get_expense_type(data.expense_type_id)
        if not expense_type:
            raise ValidationError("Expense type not found", field="expense_type_id")
        
        # Calculate EUR amount
        amount_eur = data.amount * data.exchange_rate
        
        # Handle mileage
        km_rate = None
        if expense_type.get("code") == "AUT" and data.km_distance:
            km_rate = Decimal(str(expense_type.get("km_reimbursement_rate", 0.30)))
            amount_eur = km_rate * data.km_distance
        
        item = await self._item_repo.create(
            report_id=data.report_id,
            expense_type_id=data.expense_type_id,
            expense_type_code=expense_type.get("code", ""),
            date=data.date,
            description=data.description,
            amount=data.amount,
            currency=data.currency,
            exchange_rate=data.exchange_rate,
            amount_eur=amount_eur,
            km_distance=data.km_distance,
            km_rate=km_rate,
            merchant_name=data.merchant_name,
            receipt_number=data.receipt_number,
        )
        
        # Recalculate total
        await self._report_repo.recalculate_total(data.report_id)
        
        return item

    async def update_item(self, id: UUID, user_id: UUID, data: ExpenseItemUpdate):
        """Update expense item."""
        item = await self._item_repo.get(id)
        if not item:
            raise NotFoundError("Expense item not found")
        
        report = await self.get_report(item.report_id)
        
        if report.user_id != user_id:
            raise BusinessRuleError("Cannot update another user's items")
        
        if report.status != ExpenseReportStatus.DRAFT:
            raise BusinessRuleError("Can only update items in draft reports")
        
        update_data = data.model_dump(exclude_unset=True)
        
        # Recalculate EUR if amount changed
        if "amount" in update_data or "exchange_rate" in update_data:
            amount = update_data.get("amount", item.amount)
            rate = update_data.get("exchange_rate", item.exchange_rate)
            update_data["amount_eur"] = amount * rate
        
        await self._item_repo.update(id, **update_data)
        
        # Recalculate total
        await self._report_repo.recalculate_total(item.report_id)
        
        return await self._item_repo.get(id)

    async def delete_item(self, id: UUID, user_id: UUID) -> bool:
        """Delete expense item."""
        item = await self._item_repo.get(id)
        if not item:
            raise NotFoundError("Expense item not found")
        
        report = await self.get_report(item.report_id)
        
        if report.user_id != user_id:
            raise BusinessRuleError("Cannot delete another user's items")
        
        if report.status != ExpenseReportStatus.DRAFT:
            raise BusinessRuleError("Can only delete items from draft reports")
        
        report_id = item.report_id
        await self._item_repo.delete(id)
        
        # Recalculate total
        await self._report_repo.recalculate_total(report_id)
        
        return True

    async def _get_expense_type(self, expense_type_id: UUID) -> Optional[dict]:
        """Get expense type from config service."""
        try:
            async with httpx.AsyncClient() as client:
                response = await client.get(
                    f"{settings.config_service_url}/api/v1/expense-types",
                    timeout=5.0,
                )
                if response.status_code == 200:
                    types = response.json()
                    for t in types:
                        if t.get("id") == str(expense_type_id):
                            return t
        except Exception:
            pass
        return None

    async def _send_notification(
        self,
        user_id: UUID,
        notification_type: str,
        title: str,
        message: str,
        entity_type: str = None,
        entity_id: str = None,
    ) -> None:
        """Send notification via notification-service."""
        try:
            # Get user email from auth service
            user_email = await self._get_user_email(user_id)
            if not user_email:
                return
            
            async with httpx.AsyncClient() as client:
                await client.post(
                    f"{settings.notification_service_url}/api/v1/notifications",
                    json={
                        "user_id": str(user_id),
                        "user_email": user_email,
                        "notification_type": notification_type,
                        "title": title,
                        "message": message,
                        "channel": "in_app",
                        "entity_type": entity_type,
                        "entity_id": entity_id,
                    },
                    timeout=5.0,
                )
        except Exception:
            # Notifications are not critical - fail silently
            pass

    async def _get_user_email(self, user_id: UUID) -> Optional[str]:
        """Get user email from auth service."""
        try:
            async with httpx.AsyncClient() as client:
                response = await client.get(
                    f"{settings.auth_service_url}/api/v1/users/{user_id}",
                    timeout=5.0,
                )
                if response.status_code == 200:
                    return response.json().get("email")
        except Exception:
            pass
        return None
