"""KRONOS Calendar Service - Enterprise Schemas."""
from datetime import date, datetime, time
import datetime as dt # Explicit import as alias
from typing import Optional, List, Dict, Any, Union
from uuid import UUID
from enum import Enum
from decimal import Decimal
from pydantic import BaseModel, Field, ConfigDict, field_validator


# ═══════════════════════════════════════════════════════════
# ENUMS
# ═══════════════════════════════════════════════════════════

class CalendarType(str, Enum):
    SYSTEM = "SYSTEM"
    LOCATION = "LOCATION"
    PERSONAL = "PERSONAL"
    TEAM = "TEAM"

class CalendarPermission(str, Enum):
    READ = "READ"
    WRITE = "WRITE"
    ADMIN = "ADMIN"

class RecurrenceType(str, Enum):
    NONE = "none"
    DAILY = "daily"
    WEEKLY = "weekly"
    MONTHLY = "monthly"
    YEARLY = "yearly"
    EASTER_RELATIVE = "easter_relative" # e.g. Good Friday

class CalendarItemType(str, Enum):
    HOLIDAY = "holiday"
    CLOSURE = "closure"
    EVENT = "event"
    LEAVE = "leave"
    TRIP = "trip"
    BIRTHDAY = "birthday"


# ═══════════════════════════════════════════════════════════
# WORK WEEK PROFILES
# ═══════════════════════════════════════════════════════════

class DayConfig(BaseModel):
    is_working: bool
    hours: float = 8.0
    start_time: Optional[time] = None
    end_time: Optional[time] = None

class WorkWeekProfileBase(BaseModel):
    code: str = Field(..., max_length=50)
    name: str = Field(..., max_length=100)
    description: Optional[str] = None
    weekly_config: Dict[str, DayConfig] = Field(..., description="Map of 'monday', 'tuesday' etc to config")
    total_weekly_hours: Decimal = Field(default=40.0)
    is_default: bool = False
    is_active: bool = True

class WorkWeekProfileCreate(WorkWeekProfileBase):
    pass

class WorkWeekProfileUpdate(BaseModel):
    name: Optional[str] = None
    description: Optional[str] = None
    weekly_config: Optional[Dict[str, DayConfig]] = None
    total_weekly_hours: Optional[Decimal] = None
    is_default: Optional[bool] = None
    is_active: Optional[bool] = None

class WorkWeekProfileResponse(WorkWeekProfileBase):
    model_config = ConfigDict(from_attributes=True)
    id: UUID
    created_at: datetime
    updated_at: datetime


# ═══════════════════════════════════════════════════════════
# HOLIDAY PROFILES & HOLIDAYS
# ═══════════════════════════════════════════════════════════

class HolidayProfileBase(BaseModel):
    code: str = Field(..., max_length=50)
    name: str = Field(..., max_length=100)
    country_code: Optional[str] = Field(None, min_length=2, max_length=2)
    region_code: Optional[str] = None
    is_active: bool = True

class HolidayProfileCreate(HolidayProfileBase):
    pass

class HolidayProfileUpdate(BaseModel):
    code: Optional[str] = None
    name: Optional[str] = None
    country_code: Optional[str] = None
    region_code: Optional[str] = None
    is_active: Optional[bool] = None

class HolidayProfileResponse(HolidayProfileBase):
    model_config = ConfigDict(from_attributes=True)
    id: UUID
    calendar_id: Optional[UUID] = None
    created_at: datetime

class RecurrenceRule(BaseModel):
    type: RecurrenceType = RecurrenceType.YEARLY
    month: Optional[int] = None # 1-12
    day: Optional[int] = None # 1-31
    weekday: Optional[int] = None # 0-6 (Mon-Sun)
    position: Optional[int] = None # 1 (1st), -1 (last)
    easter_offset: Optional[int] = None # Days from Easter

class HolidayBase(BaseModel):
    name: str = Field(..., max_length=100)
    date: Optional[dt.date] = None # For fixed holidays or specific year instances
    is_recurring: bool = False
    recurrence_rule: Optional[Union[RecurrenceRule, Dict[str, Any]]] = None
    is_confirmed: bool = False
    is_active: bool = True

class HolidayCreate(HolidayBase):
    profile_id: Optional[UUID] = None

class HolidayUpdate(BaseModel):
    name: Optional[str] = None
    date: Optional[date] = None
    is_recurring: Optional[bool] = None
    recurrence_rule: Optional[Union[RecurrenceRule, Dict[str, Any]]] = None
    is_confirmed: Optional[bool] = None
    is_active: Optional[bool] = None

class HolidayResponse(HolidayBase):
    model_config = ConfigDict(from_attributes=True)
    id: UUID
    profile_id: Optional[UUID] = None
    created_at: datetime


# ═══════════════════════════════════════════════════════════
# UNIFIED CALENDAR
# ═══════════════════════════════════════════════════════════

class CalendarShareBase(BaseModel):
    user_id: UUID
    permission: CalendarPermission = CalendarPermission.READ
    is_mandatory: bool = False

class CalendarShareCreate(CalendarShareBase):
    pass

class CalendarShareResponse(CalendarShareBase):
    model_config = ConfigDict(from_attributes=True)
    id: UUID
    calendar_id: UUID
    created_at: datetime

class CalendarBase(BaseModel):
    name: str = Field(..., max_length=100)
    description: Optional[str] = None
    color: str = Field(default="#4F46E5")
    type: CalendarType = CalendarType.PERSONAL
    is_active: bool = True
    visibility: str = "private"

class CalendarCreate(CalendarBase):
    pass

class CalendarUpdate(BaseModel):
    name: Optional[str] = Field(None, max_length=100)
    description: Optional[str] = None
    color: Optional[str] = None
    is_active: Optional[bool] = None
    visibility: Optional[str] = None

class CalendarResponse(CalendarBase):
    model_config = ConfigDict(from_attributes=True)
    id: UUID
    owner_id: Optional[UUID] = None
    shared_with: List[CalendarShareResponse] = Field(default=[], alias="shares")
    created_at: datetime
    updated_at: datetime
    is_owner: bool = False
    
    # Allow alias for shares
    model_config = ConfigDict(populate_by_name=True, from_attributes=True)


# ═══════════════════════════════════════════════════════════
# LOCATION CALENDAR
# ═══════════════════════════════════════════════════════════

class LocationCalendarCreate(BaseModel):
    location_id: UUID
    work_week_profile_id: UUID
    timezone: str = "Europe/Rome"

class LocationCalendarUpdate(BaseModel):
    work_week_profile_id: Optional[UUID] = None
    timezone: Optional[str] = None

class LocationCalendarResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: UUID
    location_id: UUID
    work_week_profile_id: UUID
    timezone: str
    created_at: datetime
    updated_at: datetime


# ═══════════════════════════════════════════════════════════
# EVENTS
# ═══════════════════════════════════════════════════════════

class ParticipantResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: UUID
    user_id: UUID
    response_status: str
    is_organizer: bool

class EventBase(BaseModel):
    title: str = Field(..., max_length=200)
    description: Optional[str] = None
    start_date: date
    end_date: date
    start_time: Optional[time] = None
    end_time: Optional[time] = None
    is_all_day: bool = True
    event_type: str = Field(default="generic")
    visibility: str = Field(default="private")
    calendar_id: Optional[UUID] = None
    is_recurring: bool = False
    recurrence_rule: Optional[str] = None
    # Additional fields
    color: Optional[str] = Field(default="#3B82F6", max_length=7)
    alert_before_minutes: Optional[int] = 2880
    location: Optional[str] = None
    is_virtual: bool = False
    meeting_url: Optional[str] = None

class EventCreate(EventBase):
    participant_ids: Optional[List[UUID]] = None


class EventUpdate(BaseModel):
    title: Optional[str] = None
    description: Optional[str] = None
    start_date: Optional[date] = None
    end_date: Optional[date] = None
    start_time: Optional[time] = None
    end_time: Optional[time] = None
    is_all_day: Optional[bool] = None
    calendar_id: Optional[UUID] = None
    participant_ids: Optional[List[UUID]] = None

class EventResponse(EventBase):
    model_config = ConfigDict(from_attributes=True)
    id: UUID
    created_by: Optional[UUID] = None
    created_at: datetime
    updated_at: Optional[datetime] = None
    participants: List[ParticipantResponse] = []
    
    # Computed fields for view convenience
    color: Optional[str] = None 


# ═══════════════════════════════════════════════════════════
# VIEWS & CALCULATIONS
# ═══════════════════════════════════════════════════════════

class CalendarDayItem(BaseModel):
    """Single item in a calendar day view."""
    id: Optional[UUID] = None  # Made optional for generated items
    title: str
    type: str # Simplified from ENUM to allow flexibility
    date: date
    end_date: Optional[date] = None # Optional, defaults to date
    color: Optional[str] = None
    is_all_day: bool = True
    start_time: Optional[time] = None
    end_time: Optional[time] = None
    status: Optional[str] = None
    metadata: Optional[dict] = None

class CalendarRangeResponse(BaseModel):
    """Aggregated response for a date range with separated lists."""
    start_date: date
    end_date: date
    holidays: List[CalendarDayItem] = []
    closures: List[CalendarDayItem] = []
    events: List[CalendarDayItem] = []
    leaves: List[CalendarDayItem] = []

class CalendarDayView(BaseModel):
    """Aggregated view of a single day."""
    date: date
    is_working_day: bool
    is_holiday: bool
    holiday_name: Optional[str] = None
    items: List[CalendarDayItem] = []

class CalendarRangeView(BaseModel):
    """Aggregated calendar view for a date range."""
    start_date: date
    end_date: date
    days: List[CalendarDayView] = []
    working_days_count: int = 0

class WorkingDaysRequest(BaseModel):
    start_date: date
    end_date: date
    location_id: Optional[UUID] = None
    exclude_closures: bool = True
    exclude_holidays: bool = True

class WorkingDaysResponse(BaseModel):
    start_date: date
    end_date: date
    total_calendar_days: int
    working_days: int
    holidays: List[date] = []
    closure_days: List[date] = []
    weekend_days: List[date] = []

# Legacy support for closure routes (if kept)
class ClosureBase(BaseModel):
    name: str
    start_date: date
    end_date: date

class ClosureCreate(ClosureBase):
    pass

class ClosureUpdate(BaseModel):
    name: Optional[str] = None
    start_date: Optional[date] = None
    end_date: Optional[date] = None

class ClosureResponse(ClosureBase):
    model_config = ConfigDict(from_attributes=True)
    id: UUID
    created_at: datetime

# ═══════════════════════════════════════════════════════════
# WORKING DAY EXCEPTIONS
# ═══════════════════════════════════════════════════════════

class WorkingDayExceptionBase(BaseModel):
    date: date
    exception_type: str = Field(..., pattern="^(working|non_working)$")
    reason: Optional[str] = Field(None, max_length=200)
    location_id: Optional[UUID] = None

class WorkingDayExceptionCreate(WorkingDayExceptionBase):
    pass

class WorkingDayExceptionUpdate(BaseModel):
    exception_type: Optional[str] = Field(None, pattern="^(working|non_working)$")
    reason: Optional[str] = Field(None, max_length=200)

class WorkingDayExceptionResponse(WorkingDayExceptionBase):
    model_config = ConfigDict(from_attributes=True)
    id: UUID
    created_at: datetime
