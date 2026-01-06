"""
KRONOS - Expense Service - Allowances Module

Handles Daily Allowance generation and management.
"""
import logging
from datetime import timedelta
from decimal import Decimal
from typing import Optional
from uuid import UUID

from src.core.exceptions import NotFoundError
from src.services.expenses.models import DestinationType
from src.services.expenses.schemas import DailyAllowanceCreate
from src.services.expenses.services.base import BaseExpenseService

logger = logging.getLogger(__name__)


class ExpenseAllowanceService(BaseExpenseService):
    """
    Sub-service for Daily Allowance management.
    """

    async def get_trip_allowances(self, trip_id: UUID):
        """Get allowances for a trip."""
        return await self._allowance_repo.get_by_trip(trip_id)

    async def generate_allowances(self, trip_id: UUID):
        """Auto-generate daily allowances for a trip."""
        trip = await self._trip_repo.get(trip_id)
        if not trip:
             raise NotFoundError("Business trip not found")
        
        # Delete existing
        await self._allowance_repo.delete_by_trip(trip_id)
        
        # Get rate from config (via base helper)
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
        if not allowance:
             raise NotFoundError("Allowance not found")

        trip = await self._trip_repo.get(allowance.trip_id)
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
        # This was in base but might be specific here. But base had _get_expense_type. 
        # Actually I didn't put _get_allowance_rate in base.py because it seemed specific. 
        # I'll re-implement it here using ConfigClient.
        
        try:
             # We can use the ConfigClient directly if it has a method, otherwise HTTP call like in original code
             # Based on code, it used raw HTTP request to config service URL.
             # Ideally ConfigClient should have this. Assuming it doesn't, we'll keep the logic but use settings properly.
             # Actually I should check ConfigClient capabilities. 
             # For now I will replicate the logic but maybe clean it up.
             
             # Replicating original logic:
             import httpx
             from src.core.config import settings
             
             async with httpx.AsyncClient() as client:
                response = await client.get(
                    f"{settings.CONFIG_SERVICE_URL}/api/v1/allowance-rules", # Using env var
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
