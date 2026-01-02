"""KRONOS Calendar Service - iCal/ICS Export Utilities.

Provides functionality to export calendar data in iCalendar (ICS) format
for synchronization with Google Calendar, Outlook, Apple Calendar, etc.
"""
from datetime import date, datetime, timedelta
from typing import List, Optional
from uuid import UUID, uuid4


def escape_ics_text(text: str) -> str:
    """Escape special characters for ICS format."""
    if not text:
        return ""
    # Escape backslashes, semicolons, commas, and newlines
    text = text.replace("\\", "\\\\")
    text = text.replace(";", "\\;")
    text = text.replace(",", "\\,")
    text = text.replace("\n", "\\n")
    return text


def format_ics_date(d: date) -> str:
    """Format a date for ICS (all-day event)."""
    return d.strftime("%Y%m%d")


def format_ics_datetime(dt: datetime) -> str:
    """Format a datetime for ICS with UTC."""
    return dt.strftime("%Y%m%dT%H%M%SZ")


def generate_uid(prefix: str = "kronos") -> str:
    """Generate a unique UID for an ICS event."""
    return f"{prefix}-{uuid4()}@kronos.local"


class ICalGenerator:
    """Generator for iCalendar (ICS) format files."""
    
    def __init__(self, calendar_name: str = "KRONOS Calendar"):
        self.calendar_name = calendar_name
        self.events: List[str] = []
        
    def add_event(
        self,
        uid: str,
        summary: str,
        start_date: date,
        end_date: Optional[date] = None,
        description: Optional[str] = None,
        location: Optional[str] = None,
        categories: Optional[List[str]] = None,
        all_day: bool = True,
        start_time: Optional[datetime] = None,
        end_time: Optional[datetime] = None,
        color: Optional[str] = None,
        status: str = "CONFIRMED",
        transparency: str = "OPAQUE",  # OPAQUE = busy, TRANSPARENT = free
    ) -> None:
        """Add an event to the calendar."""
        lines = []
        lines.append("BEGIN:VEVENT")
        lines.append(f"UID:{uid}")
        lines.append(f"DTSTAMP:{format_ics_datetime(datetime.utcnow())}")
        
        if all_day:
            lines.append(f"DTSTART;VALUE=DATE:{format_ics_date(start_date)}")
            # End date for all-day events is exclusive, so add 1 day
            actual_end = (end_date or start_date) + timedelta(days=1)
            lines.append(f"DTEND;VALUE=DATE:{format_ics_date(actual_end)}")
        else:
            if start_time:
                lines.append(f"DTSTART:{format_ics_datetime(start_time)}")
            if end_time:
                lines.append(f"DTEND:{format_ics_datetime(end_time)}")
        
        lines.append(f"SUMMARY:{escape_ics_text(summary)}")
        
        if description:
            lines.append(f"DESCRIPTION:{escape_ics_text(description)}")
        
        if location:
            lines.append(f"LOCATION:{escape_ics_text(location)}")
        
        if categories:
            lines.append(f"CATEGORIES:{','.join(escape_ics_text(c) for c in categories)}")
        
        lines.append(f"STATUS:{status}")
        lines.append(f"TRANSP:{transparency}")
        
        # Add color hint (supported by some clients)
        if color:
            # Remove # from hex color for X-APPLE-CALENDAR-COLOR
            hex_color = color.lstrip("#")
            lines.append(f"X-APPLE-CALENDAR-COLOR:#{hex_color}")
        
        lines.append("END:VEVENT")
        
        self.events.append("\r\n".join(lines))
    
    def add_holiday(
        self,
        holiday_id: str,
        name: str,
        holiday_date: date,
        scope: str = "national",
        description: Optional[str] = None,
    ) -> None:
        """Add a holiday event."""
        scope_emoji = {
            "national": "🇮🇹",
            "regional": "🏛️",
            "local": "📍",
            "company": "🏢",
        }
        emoji = scope_emoji.get(scope, "🗓️")
        
        self.add_event(
            uid=f"holiday-{holiday_id}@kronos.local",
            summary=f"{emoji} {name}",
            start_date=holiday_date,
            description=description or f"Festività {scope}",
            categories=["Holiday", scope.capitalize()],
            transparency="TRANSPARENT",  # Holidays don't block time
            color="#EF4444",  # Red
        )
    
    def add_closure(
        self,
        closure_id: str,
        name: str,
        start_date: date,
        end_date: date,
        closure_type: str = "total",
        description: Optional[str] = None,
        is_paid: bool = True,
    ) -> None:
        """Add a company closure event."""
        type_label = "Chiusura Totale" if closure_type == "total" else "Chiusura Parziale"
        paid_label = " (Retribuita)" if is_paid else ""
        
        self.add_event(
            uid=f"closure-{closure_id}@kronos.local",
            summary=f"🏢 {name}",
            start_date=start_date,
            end_date=end_date,
            description=f"{type_label}{paid_label}\n{description or ''}".strip(),
            categories=["CompanyClosure", closure_type.capitalize()],
            transparency="OPAQUE",  # Closures block time
            color="#8B5CF6",  # Purple
        )
    
    def add_leave_request(
        self,
        request_id: str,
        employee_name: str,
        leave_type: str,
        start_date: date,
        end_date: date,
        status: str = "approved",
        days: float = 1.0,
    ) -> None:
        """Add a leave request event."""
        status_map = {
            "approved": "CONFIRMED",
            "pending": "TENTATIVE",
            "rejected": "CANCELLED",
        }
        ics_status = status_map.get(status, "CONFIRMED")
        
        color_map = {
            "approved": "#22C55E",  # Green
            "pending": "#F59E0B",   # Orange
            "rejected": "#EF4444", # Red
        }
        color = color_map.get(status, "#3B82F6")
        
        self.add_event(
            uid=f"leave-{request_id}@kronos.local",
            summary=f"🌴 {employee_name} - {leave_type}",
            start_date=start_date,
            end_date=end_date,
            description=f"Tipo: {leave_type}\nGiorni: {days}\nStato: {status}",
            categories=["Leave", leave_type],
            status=ics_status,
            transparency="OPAQUE",
            color=color,
        )
    
    def add_generic_event(
        self,
        event_id: str,
        title: str,
        start_date: date,
        end_date: Optional[date] = None,
        start_time: Optional[datetime] = None,
        end_time: Optional[datetime] = None,
        description: Optional[str] = None,
        location: Optional[str] = None,
        is_all_day: bool = True,
        event_type: str = "generic",
        color: Optional[str] = None,
    ) -> None:
        """Add a generic calendar event."""
        self.add_event(
            uid=f"event-{event_id}@kronos.local",
            summary=title,
            start_date=start_date,
            end_date=end_date,
            start_time=start_time if not is_all_day else None,
            end_time=end_time if not is_all_day else None,
            description=description,
            location=location,
            all_day=is_all_day,
            categories=[event_type.capitalize()],
            color=color or "#3B82F6",
        )
    
    def generate(self) -> str:
        """Generate the complete ICS file content."""
        lines = [
            "BEGIN:VCALENDAR",
            "VERSION:2.0",
            "PRODID:-//KRONOS HR//Calendar Service//IT",
            f"X-WR-CALNAME:{escape_ics_text(self.calendar_name)}",
            "CALSCALE:GREGORIAN",
            "METHOD:PUBLISH",
        ]
        
        # Add all events
        for event in self.events:
            lines.append(event)
        
        lines.append("END:VCALENDAR")
        
        return "\r\n".join(lines)
    
    def clear(self) -> None:
        """Clear all events."""
        self.events = []


def generate_holidays_ics(
    holidays: List[dict],
    calendar_name: str = "KRONOS Festività",
) -> str:
    """Generate ICS file for holidays."""
    generator = ICalGenerator(calendar_name)
    
    for holiday in holidays:
        holiday_date = holiday.get("date")
        if isinstance(holiday_date, str):
            holiday_date = date.fromisoformat(holiday_date)
        
        generator.add_holiday(
            holiday_id=str(holiday.get("id", uuid4())),
            name=holiday.get("name", "Festività"),
            holiday_date=holiday_date,
            scope=holiday.get("scope", "national"),
            description=holiday.get("description"),
        )
    
    return generator.generate()


def generate_closures_ics(
    closures: List[dict],
    calendar_name: str = "KRONOS Chiusure Aziendali",
) -> str:
    """Generate ICS file for company closures."""
    generator = ICalGenerator(calendar_name)
    
    for closure in closures:
        start_date = closure.get("start_date")
        end_date = closure.get("end_date")
        
        if isinstance(start_date, str):
            start_date = date.fromisoformat(start_date)
        if isinstance(end_date, str):
            end_date = date.fromisoformat(end_date)
        
        generator.add_closure(
            closure_id=str(closure.get("id", uuid4())),
            name=closure.get("name", "Chiusura"),
            start_date=start_date,
            end_date=end_date,
            closure_type=closure.get("closure_type", "total"),
            description=closure.get("description"),
            is_paid=closure.get("is_paid", True),
        )
    
    return generator.generate()


def generate_leaves_ics(
    leaves: List[dict],
    calendar_name: str = "KRONOS Assenze",
) -> str:
    """Generate ICS file for leave requests."""
    generator = ICalGenerator(calendar_name)
    
    for leave in leaves:
        start_date = leave.get("start_date")
        end_date = leave.get("end_date")
        
        if isinstance(start_date, str):
            start_date = date.fromisoformat(start_date)
        if isinstance(end_date, str):
            end_date = date.fromisoformat(end_date)
        
        generator.add_leave_request(
            request_id=str(leave.get("id", uuid4())),
            employee_name=leave.get("employee_name", "Dipendente"),
            leave_type=leave.get("leave_type_name", leave.get("leave_type", "Assenza")),
            start_date=start_date,
            end_date=end_date,
            status=leave.get("status", "approved"),
            days=float(leave.get("days_requested", 1)),
        )
    
    return generator.generate()


def generate_combined_ics(
    holidays: List[dict] = None,
    closures: List[dict] = None,
    events: List[dict] = None,
    leaves: List[dict] = None,
    calendar_name: str = "KRONOS Calendar",
) -> str:
    """Generate a combined ICS file with all calendar items."""
    generator = ICalGenerator(calendar_name)
    
    # Add holidays
    if holidays:
        for holiday in holidays:
            holiday_date = holiday.get("date")
            if isinstance(holiday_date, str):
                holiday_date = date.fromisoformat(holiday_date)
            
            generator.add_holiday(
                holiday_id=str(holiday.get("id", uuid4())),
                name=holiday.get("name", "Festività"),
                holiday_date=holiday_date,
                scope=holiday.get("scope", "national"),
                description=holiday.get("description"),
            )
    
    # Add closures
    if closures:
        for closure in closures:
            start_date = closure.get("start_date")
            end_date = closure.get("end_date")
            
            if isinstance(start_date, str):
                start_date = date.fromisoformat(start_date)
            if isinstance(end_date, str):
                end_date = date.fromisoformat(end_date)
            
            generator.add_closure(
                closure_id=str(closure.get("id", uuid4())),
                name=closure.get("name", "Chiusura"),
                start_date=start_date,
                end_date=end_date,
                closure_type=closure.get("closure_type", "total"),
                description=closure.get("description"),
                is_paid=closure.get("is_paid", True),
            )
    
    # Add generic events
    if events:
        for event in events:
            start_date = event.get("start_date")
            end_date = event.get("end_date")
            
            if isinstance(start_date, str):
                start_date = date.fromisoformat(start_date)
            if isinstance(end_date, str):
                end_date = date.fromisoformat(end_date)
            
            generator.add_generic_event(
                event_id=str(event.get("id", uuid4())),
                title=event.get("title", "Evento"),
                start_date=start_date,
                end_date=end_date,
                description=event.get("description"),
                location=event.get("location"),
                is_all_day=event.get("is_all_day", True),
                event_type=event.get("event_type", "generic"),
                color=event.get("color"),
            )
    
    # Add leaves
    if leaves:
        for leave in leaves:
            start_date = leave.get("start_date")
            end_date = leave.get("end_date")
            
            if isinstance(start_date, str):
                start_date = date.fromisoformat(start_date)
            if isinstance(end_date, str):
                end_date = date.fromisoformat(end_date)
            
            generator.add_leave_request(
                request_id=str(leave.get("id", uuid4())),
                employee_name=leave.get("employee_name", "Dipendente"),
                leave_type=leave.get("leave_type_name", leave.get("leave_type", "Assenza")),
                start_date=start_date,
                end_date=end_date,
                status=leave.get("status", "approved"),
                days=float(leave.get("days_requested", 1)),
            )
    
    return generator.generate()
