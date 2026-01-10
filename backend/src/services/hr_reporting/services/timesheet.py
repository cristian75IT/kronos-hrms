"""
Timesheet Service.

Handles generation, retrieval, and confirmation of Monthly Timesheets.
"""
import logging
from datetime import date, datetime, timedelta
from uuid import UUID
from typing import Optional, List, Any, Tuple

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from fastapi import HTTPException

from ..models import MonthlyTimesheet, TimesheetStatus
from ..schemas import TimesheetConfirmation, MonthlyTimesheetResponse
from .settings import HRSettingsService
from ..aggregator import HRDataAggregator
from src.shared.audit_client import get_audit_logger

logger = logging.getLogger(__name__)

class TimesheetService:
    """Service for Monthly Timesheet operations."""
    
    def __init__(self, session: AsyncSession):
        self.session = session
        self.settings_service = HRSettingsService(session)
        self.aggregator = HRDataAggregator()
        self.audit_logger = get_audit_logger("hr-reporting-service")

    async def get_or_create_timesheet(
        self, 
        employee_id: UUID, 
        year: int, 
        month: int
    ) -> MonthlyTimesheet:
        """
        Get existing timesheet or generate a new draft.
        """
        stmt = select(MonthlyTimesheet).where(
            MonthlyTimesheet.employee_id == employee_id,
            MonthlyTimesheet.year == year,
            MonthlyTimesheet.month == month
        )
        result = await self.session.execute(stmt)
        timesheet = result.scalar_one_or_none()
        
        if timesheet:
            # Optionally refresh data if in draft?
            # For now, we return as is.
            return timesheet
            
        # Create new
        logger.info(f"Generating new timesheet for {employee_id} - {year}/{month}")
        timesheet = await self._generate_timesheet_data(employee_id, year, month)
        self.session.add(timesheet)
        await self.session.flush()
        return timesheet
        
    async def get_timesheet_for_user(
        self, 
        user_id: UUID, 
        year: int, 
        month: int
    ) -> MonthlyTimesheetResponse:
        """Get timesheet with context info."""
        timesheet = await self.get_or_create_timesheet(user_id, year, month)
        
        # Check confirmation window
        can_confirm, deadline = await self.check_confirmation_window(year, month)
        
        # Map to response manually to inject computed fields
        response = MonthlyTimesheetResponse.model_validate(timesheet)
        response.can_confirm = can_confirm and timesheet.status in (TimesheetStatus.DRAFT, TimesheetStatus.PENDING_CONFIRMATION)
        response.confirmation_deadline = deadline
        
        return response

    async def confirm_timesheet(
        self, 
        user_id: UUID, 
        year: int, 
        month: int, 
        data: TimesheetConfirmation
    ) -> MonthlyTimesheet:
        """User confirms their timesheet."""
        timesheet = await self.get_or_create_timesheet(user_id, year, month)
        
        if timesheet.employee_id != user_id:
            # Should be shielded by router, but safety check
            raise HTTPException(403, "Not your timesheet")
            
        if timesheet.status == TimesheetStatus.CONFIRMED:
            raise HTTPException(400, "Timesheet already confirmed")
            
        can_confirm, deadline = await self.check_confirmation_window(year, month)
        if not can_confirm:
            # Strict check?
            today = date.today()
            if today > deadline:
                 raise HTTPException(400, f"Confirmation deadline passed ({deadline})")
            # If too early, maybe allow?
                 
        timesheet.status = TimesheetStatus.CONFIRMED
        timesheet.confirmed_at = datetime.utcnow()
        timesheet.confirmed_by = user_id
        if data.notes:
            timesheet.employee_notes = data.notes
            
        await self.session.commit()
        
        # Audit log
        await self.audit_logger.log_action(
            user_id=user_id,
            action="CONFIRM_TIMESHEET",
            resource_type="TIMESHEET",
            resource_id=str(timesheet.id),
            description=f"Confirmed timesheet for {year}/{month}",
            details={"notes": data.notes}
        )
        
        return timesheet

    async def update_timesheet_data(
        self,
        employee_id: UUID,
        year: int,
        month: int
    ) -> MonthlyTimesheet:
        """Force update of timesheet data from aggregator."""
        timesheet = await self.get_or_create_timesheet(employee_id, year, month)
        
        # Don't update if confirmed/approved (unless admin override needed?)
        if timesheet.status in (TimesheetStatus.CONFIRMED, TimesheetStatus.APPROVED):
            logger.info(f"Skipping update for confirmed/approved timesheet {timesheet.id}")
            return timesheet
            
        start_date = date(year, month, 1)
        if month == 12:
            next_month = date(year + 1, 1, 1)
        else:
            next_month = date(year, month + 1, 1)
        end_date = next_month - timedelta(days=1)
        
        # Get fresh daily data
        daily_items = await self.aggregator.get_employee_daily_attendance_range(
            employee_id, start_date, end_date
        )
        
        # Serialize
        serialized_days = []
        for item in daily_items:
            item_copy = item.copy()
            if isinstance(item_copy.get("date"), date):
                item_copy["date"] = item_copy["date"].isoformat()
            serialized_days.append(item_copy)
            
        # Update model
        timesheet.days = serialized_days
        timesheet.summary = self._calculate_summary(daily_items)
        timesheet.updated_at = datetime.utcnow()
        
        await self.session.commit()
        return timesheet

    async def _generate_timesheet_data(
        self, 
        employee_id: UUID, 
        year: int, 
        month: int
    ) -> MonthlyTimesheet:
        """Call aggregator and build model."""
        start_date = date(year, month, 1)
        # End date calculation
        if month == 12:
            next_month = date(year + 1, 1, 1)
        else:
            next_month = date(year, month + 1, 1)
        end_date = next_month - timedelta(days=1)
        
        # Get daily data
        daily_items = await self.aggregator.get_employee_daily_attendance_range(
            employee_id, start_date, end_date
        )
        
        # Serialize dates for JSONB
        serialized_days = []
        for item in daily_items:
            item_copy = item.copy()
            if isinstance(item_copy.get("date"), date):
                item_copy["date"] = item_copy["date"].isoformat()
            serialized_days.append(item_copy)
        
        # Calculate summary
        summary = self._calculate_summary(daily_items)
        
        return MonthlyTimesheet(
            employee_id=employee_id,
            year=year,
            month=month,
            status=TimesheetStatus.DRAFT,
            days=serialized_days,
            summary=summary
        )

    def _calculate_summary(self, days: List[dict]) -> dict:
        total = len(days)
        worked = 0
        hours_worked = 0.0
        sickness = 0.0
        vacation = 0.0
        other = 0.0
        days_absent = 0.0
        
        for d in days:
            status = d.get("status", "")
            h = d.get("hours_worked", 0)
            
            hours_worked += h
            if h > 0 or status in ("Presente", "Trasferta"):
                worked += 1
            
            if "Malattia" in status:
                sickness += 1
                days_absent += 1
            elif "Ferie" in status:
                vacation += 1
                days_absent += 1
            elif "Assente" in status or "ROL" in status:
                other += 1
                days_absent += 1
        
        return {
            "total_days": total,
            "days_worked": float(worked),
            "days_absent": float(days_absent),
            "hours_worked": float(hours_worked),
            "hours_absence": float(days_absent * 8.0), # Approx
            "sickness_days": float(sickness),
            "vacation_days": float(vacation),
            "other_days": float(other)
        }

    async def check_confirmation_window(self, year: int, month: int) -> Tuple[bool, date]:
        """Check if confirmation is allowed for the given period."""
        settings = await self.settings_service.get_settings()
        day = settings.timesheet_confirmation_day
        offset = settings.timesheet_confirmation_month_offset
        
        # Calculate deadline: (Day) of (Timesheet Month + Offset)
        deadline_month = month + offset
        deadline_year = year
        
        while deadline_month > 12:
            deadline_month -= 12
            deadline_year += 1
            
        try:
            deadline = date(deadline_year, deadline_month, day)
        except ValueError:
            # Handle invalid dates (e.g. Feb 30) -> fallback to last day of month
            if deadline_month == 12:
                last_day = date(deadline_year + 1, 1, 1) - timedelta(days=1)
            else:
                last_day = date(deadline_year, deadline_month + 1, 1) - timedelta(days=1)
            deadline = last_day
             
        today = date.today()
        
        # Block future confirmation
        period_start = date(year, month, 1)
        if today < period_start:
             return False, deadline
             
        # Allow confirmation basically until deadline
        # And potentially forbid if too early?
        # User requirement implies "deadline" is the END.
        is_open = today <= deadline
        
        return is_open, deadline
