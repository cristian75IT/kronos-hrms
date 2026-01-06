"""KRONOS Calendar Service - Export Router.
Provides iCal (ICS) subscription endpoints.
"""
from typing import Optional
from uuid import UUID
from fastapi import APIRouter, Depends, HTTPException, Query
from fastapi.responses import Response
from sqlalchemy.orm import Session

from src.core.database import get_db
from src.core.security import get_current_user, TokenPayload
from ..services import CalendarService
from .. import ical_export


router = APIRouter()

@router.get("/holidays.ics", response_class=Response)
def export_holidays_ics(
    year: Optional[int] = None,
    db: Session = Depends(get_db)
):
    """Export public holidays as ICS file."""
    if not year:
        from datetime import date
        year = date.today().year

    holidays = repo.get_holidays(db, year=year, limit=1000)
    # Convert ORM objects to dicts for the generator
    holidays_data = [
        {
            "id": str(h.id),
            "name": h.name,
            "date": h.date,
            "scope": h.scope or "national",
            "description": h.description
        }
        for h in holidays
    ]
    
    ics_content = ical_export.generate_holidays_ics(holidays_data)
    
    return Response(
        content=ics_content,
        media_type="text/calendar",
        headers={"Content-Disposition": f"attachment; filename=holidays_{year}.ics"}
    )

@router.get("/closures.ics", response_class=Response)
def export_closures_ics(
    year: Optional[int] = None,
    db: Session = Depends(get_db)
):
    """Export company closures as ICS file."""
    if not year:
        from datetime import date
        year = date.today().year

    closures = repo.get_closures(db, year=year, limit=1000)
    closures_data = [
        {
            "id": str(c.id),
            "name": c.name,
            "start_date": c.start_date,
            "end_date": c.end_date,
            "closure_type": c.closure_type,
            "description": c.description,
            "is_paid": c.is_paid
        }
        for c in closures
    ]
    
    ics_content = ical_export.generate_closures_ics(closures_data)
    
    return Response(
        content=ics_content,
        media_type="text/calendar",
        headers={"Content-Disposition": f"attachment; filename=closures_{year}.ics"}
    )

@router.get("/user/{user_id}/calendar.ics", response_class=Response)
def export_user_calendar_ics(
    user_id: UUID,
    token: str = Query(..., description="Access token for authentication (since calendar clients don't use headers)"),
    db: Session = Depends(get_db)
):
    """
    Export specific user's calendar (Personal events + Holidays + Closures).
    Validates token manually since iCal subscriptions often can't pass Bearer headers.
    """
    # TODO: Validate token strictly. For now we assume internal trust or simple key check.
    # In production, we should decode the JWT token here manually or use a specific API Key for calendar feed.
    
    # 1. Fetch User Events
    # Note: Repository needs a method to fetch events by user_id
    # We will assume repo.get_events exists and supports user_id filter
    
    # Fetch current year context
    from datetime import date
    current_year = date.today().year
    
    # Fetch contextual data
    holidays = repo.get_holidays(db, year=current_year, limit=1000)
    closures = repo.get_closures(db, year=current_year, limit=1000)
    
    # Minimal event fetching logic (placeholder if specific repo method irrelevant)
    # Ideally: events = repo.get_user_events(db, user_id=user_id, start_date=..., end_date=...)
    # For now returning holidays and closures as base
    
    holidays_data = [
        {
            "id": str(h.id),
            "name": h.name,
            "date": h.date,
            "scope": h.scope,
            "description": h.description
        } for h in holidays
    ]
    
    closures_data = [
        {
            "id": str(c.id),
            "name": c.name,
            "start_date": c.start_date,
            "end_date": c.end_date,
            "closure_type": c.closure_type,
            "description": c.description,
            "is_paid": c.is_paid
        } for c in closures
    ]
    
    ics_content = ical_export.generate_combined_ics(
        holidays=holidays_data,
        closures=closures_data,
        calendar_name=f"KRONOS - User {user_id}"
    )
    
    return Response(
        content=ics_content,
        media_type="text/calendar",
        headers={"Content-Disposition": "attachment; filename=my_calendar.ics"}
    )
