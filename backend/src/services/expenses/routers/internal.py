from datetime import date
from uuid import UUID

from fastapi import APIRouter, Depends

from src.services.expenses.services import ExpenseService
from src.services.expenses.deps import get_expense_service
from src.services.expenses.schemas import ApprovalCallback, BusinessTripResponse # Assuming get_trips_for_date returns list of trips, but signature said: get_trips_for_date(target_date)
# I should check return type of get_trips_for_date in service. 
# Outline didn't show it. Assuming list[BusinessTrip] or mapped items.
# I will check router.py again to see decorator response_model if any.
# router.py snippet (line 284) had no response_model!
# Maybe it returns ORM objects directly? 
# If so, FastApi will try to serialize.
# I'll check strict typing or add response_model if I can guess.
# For internal use, maybe it's just a helper endpoint?
# But it is an endpoint.
# Let's look at router.py again.

# Line 284:
# @router.get(...) # No response_model??
# async def get_trips_for_date(...)
# Let me re-read step 8048.
# {"NodePath":"get_trips_for_date","ContextType":"Function","Content":"# Get all active trips for a specific date (Internal use).\nget_trips_for_date(\n    target_date: date,\n    service: ExpenseService = Depends(get_expense_service),\n)","ContentType":"signature","StartLine":284,"EndLine":292}
# No response_model.
# I'll keep it without response_model for now to match exactly.

router = APIRouter()

@router.get("/trips/internal/for-date")
async def get_trips_for_date(
    target_date: date,
    service: ExpenseService = Depends(get_expense_service),
):
    """Get all active trips for a specific date (Internal use)."""
    return await service.get_trips_for_date(target_date)


@router.post("/approvals/callback/{id}")
async def approval_callback(
    id: UUID,
    data: ApprovalCallback,
    service: ExpenseService = Depends(get_expense_service),
):
    """Handle approval callback from Approval Service."""
    return await service.approval_callback(id, data)
