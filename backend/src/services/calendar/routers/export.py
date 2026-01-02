"""KRONOS Calendar Service - iCal Export Router.

Provides endpoints for exporting calendar data in iCalendar (ICS) format
for synchronization with external calendar applications.
"""
from datetime import date
from typing import Optional
from uuid import UUID

from fastapi import APIRouter, Depends, Query, Response, HTTPException, status
from fastapi.responses import StreamingResponse

from sqlalchemy.ext.asyncio import AsyncSession

from src.core.database import get_db
from src.core.security import get_current_user, TokenPayload
from ..service import CalendarService
from ..ical_export import (
    generate_holidays_ics,
    generate_closures_ics,
    generate_combined_ics,
    ICalGenerator,
)

router = APIRouter()


def ics_response(content: str, filename: str) -> Response:
    """Create an ICS file response with proper headers."""
    return Response(
        content=content,
        media_type="text/calendar; charset=utf-8",
        headers={
            "Content-Disposition": f'attachment; filename="{filename}"',
            "Cache-Control": "no-cache, no-store, must-revalidate",
        }
    )


@router.get("/holidays.ics")
async def export_holidays_ics(
    year: int = Query(..., description="Year to export"),
    scope: Optional[str] = Query(None, description="Filter by scope (national, regional, local)"),
    db: AsyncSession = Depends(get_db),
):
    """Export holidays as an ICS file.
    
    This endpoint is public to allow calendar subscription without authentication.
    Returns an iCalendar file that can be imported or subscribed to.
    """
    service = CalendarService(db)
    holidays = await service.get_holidays(year=year)
    
    # Filter by scope if provided
    if scope:
        holidays = [h for h in holidays if h.scope == scope]
    
    # Convert to dict for ICS generation
    holidays_data = [
        {
            "id": str(h.id),
            "name": h.name,
            "date": h.date,
            "scope": h.scope,
            "description": h.description,
        }
        for h in holidays
    ]
    
    ics_content = generate_holidays_ics(holidays_data, f"KRONOS Festività {year}")
    return ics_response(ics_content, f"kronos_holidays_{year}.ics")


@router.get("/closures.ics")
async def export_closures_ics(
    year: int = Query(..., description="Year to export"),
    db: AsyncSession = Depends(get_db),
):
    """Export company closures as an ICS file.
    
    This endpoint is public to allow calendar subscription.
    """
    service = CalendarService(db)
    closures = await service.get_closures(year=year)
    
    closures_data = [
        {
            "id": str(c.id),
            "name": c.name,
            "start_date": c.start_date,
            "end_date": c.end_date,
            "closure_type": c.closure_type,
            "description": c.description,
            "is_paid": c.is_paid,
        }
        for c in closures
    ]
    
    ics_content = generate_closures_ics(closures_data, f"KRONOS Chiusure {year}")
    return ics_response(ics_content, f"kronos_closures_{year}.ics")


@router.get("/combined.ics")
async def export_combined_ics(
    year: int = Query(..., description="Year to export"),
    include_holidays: bool = Query(True, description="Include holidays"),
    include_closures: bool = Query(True, description="Include closures"),
    db: AsyncSession = Depends(get_db),
):
    """Export a combined ICS file with holidays and closures.
    
    This endpoint is public to allow calendar subscription.
    Useful for subscribing to all company-wide calendar items at once.
    """
    service = CalendarService(db)
    
    holidays_data = []
    closures_data = []
    
    if include_holidays:
        holidays = await service.get_holidays(year=year)
        holidays_data = [
            {
                "id": str(h.id),
                "name": h.name,
                "date": h.date,
                "scope": h.scope,
                "description": h.description,
            }
            for h in holidays
        ]
    
    if include_closures:
        closures = await service.get_closures(year=year)
        closures_data = [
            {
                "id": str(c.id),
                "name": c.name,
                "start_date": c.start_date,
                "end_date": c.end_date,
                "closure_type": c.closure_type,
                "description": c.description,
                "is_paid": c.is_paid,
            }
            for c in closures
        ]
    
    ics_content = generate_combined_ics(
        holidays=holidays_data,
        closures=closures_data,
        calendar_name=f"KRONOS Calendario Aziendale {year}",
    )
    return ics_response(ics_content, f"kronos_calendar_{year}.ics")


@router.get("/my-events.ics")
async def export_my_events_ics(
    year: int = Query(None, description="Year to export (defaults to current year)"),
    db: AsyncSession = Depends(get_db),
    current_user: TokenPayload = Depends(get_current_user),
):
    """Export personal calendar events as an ICS file.
    
    Requires authentication. Exports only the current user's events.
    """
    if year is None:
        year = date.today().year
    
    service = CalendarService(db)
    user_id = current_user.user_id
    
    # Get user's events
    start_date = date(year, 1, 1)
    end_date = date(year, 12, 31)
    
    events = await service.get_events(
        user_id=user_id,
        start_date=start_date,
        end_date=end_date,
        include_public=False,  # Only personal events
    )
    
    events_data = [
        {
            "id": str(e.id),
            "title": e.title,
            "start_date": e.start_date,
            "end_date": e.end_date,
            "description": e.description,
            "location": e.location,
            "is_all_day": e.is_all_day,
            "event_type": e.event_type,
            "color": e.color,
        }
        for e in events
    ]
    
    ics_content = generate_combined_ics(
        events=events_data,
        calendar_name=f"I Miei Eventi KRONOS {year}",
    )
    return ics_response(ics_content, f"kronos_my_events_{year}.ics")


@router.get("/subscription-url")
async def get_subscription_urls(
    year: int = Query(..., description="Year for subscription"),
    current_user: TokenPayload = Depends(get_current_user),
):
    """Get subscription URLs for external calendar apps.
    
    Returns URLs that can be added to Google Calendar, Outlook, etc.
    for automatic synchronization.
    """
    # Base URL - in production this should be the public URL
    # For now we use a placeholder that should be configured
    base_url = "/api/v1/export"
    
    return {
        "holidays": {
            "url": f"{base_url}/holidays.ics?year={year}",
            "description": "Festività nazionali, regionali e locali",
            "refresh_interval": "weekly",
        },
        "closures": {
            "url": f"{base_url}/closures.ics?year={year}",
            "description": "Chiusure aziendali pianificate",
            "refresh_interval": "daily",
        },
        "combined": {
            "url": f"{base_url}/combined.ics?year={year}",
            "description": "Calendario aziendale completo (festività + chiusure)",
            "refresh_interval": "daily",
        },
        "instructions": {
            "google_calendar": "Aggiungi calendario > Da URL > Incolla l'URL",
            "outlook": "Importa calendario > Da web > Incolla l'URL",
            "apple_calendar": "File > Nuovo abbonamento calendario > Incolla l'URL",
        }
    }


@router.get("/subscribe/{token}")
async def calendar_subscription(
    token: str,
    db: AsyncSession = Depends(get_db),
):
    """Token-based calendar subscription endpoint.
    
    This allows authenticated access without requiring login for calendar apps.
    The token should be a secure, per-user subscription token.
    
    TODO: Implement token validation and user lookup.
    For now, returns a placeholder response.
    """
    # In production, validate the token and get user info
    # token format could be: user_id:hmac_signature
    
    return Response(
        content="Token-based subscriptions coming soon",
        media_type="text/plain",
        status_code=501,
    )
