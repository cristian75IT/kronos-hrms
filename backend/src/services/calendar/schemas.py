"""KRONOS Calendar Service - Pydantic Schemas."""
from datetime import date, datetime, time
from typing import Optional, List
from uuid import UUID
from pydantic import BaseModel, Field, ConfigDict


# ═══════════════════════════════════════════════════════════
# HOLIDAY SCHEMAS
# ═══════════════════════════════════════════════════════════

class HolidayBase(BaseModel):
    """Base schema for holidays."""
    name: str = Field(..., max_length=100)
    description: Optional[str] = None
    date: date
    year: int
    scope: str = Field(default="national", pattern="^(national|regional|local|company)$")
    location_id: Optional[UUID] = None
    region_code: Optional[str] = Field(None, max_length=10)
    is_recurring: bool = False
    recurrence_rule: Optional[str] = None


class HolidayCreate(HolidayBase):
    """Schema for creating a holiday."""
    pass


class HolidayUpdate(BaseModel):
    """Schema for updating a holiday."""
    name: Optional[str] = Field(None, max_length=100)
    description: Optional[str] = None
    date: Optional[date] = None
    scope: Optional[str] = None
    location_id: Optional[UUID] = None
    region_code: Optional[str] = None
    is_recurring: Optional[bool] = None
    recurrence_rule: Optional[str] = None
    is_confirmed: Optional[bool] = None
    is_active: Optional[bool] = None


class HolidayResponse(HolidayBase):
    """Schema for holiday response."""
    model_config = ConfigDict(from_attributes=True)
    
    id: UUID
    is_confirmed: bool = True
    is_active: bool = True
    created_at: datetime
    updated_at: datetime


# ═══════════════════════════════════════════════════════════
# CLOSURE SCHEMAS
# ═══════════════════════════════════════════════════════════

class ClosureBase(BaseModel):
    """Base schema for company closures."""
    name: str = Field(..., max_length=200)
    description: Optional[str] = None
    start_date: date
    end_date: date
    year: int
    closure_type: str = Field(default="total", pattern="^(total|partial)$")
    affected_departments: Optional[List[str]] = None
    affected_locations: Optional[List[UUID]] = None
    is_paid: bool = True
    consumes_leave_balance: bool = False
    leave_type_code: Optional[str] = None


class ClosureCreate(ClosureBase):
    """Schema for creating a closure."""
    pass


class ClosureUpdate(BaseModel):
    """Schema for updating a closure."""
    name: Optional[str] = Field(None, max_length=200)
    description: Optional[str] = None
    start_date: Optional[date] = None
    end_date: Optional[date] = None
    closure_type: Optional[str] = None
    affected_departments: Optional[List[str]] = None
    affected_locations: Optional[List[UUID]] = None
    is_paid: Optional[bool] = None
    consumes_leave_balance: Optional[bool] = None
    leave_type_code: Optional[str] = None
    is_active: Optional[bool] = None


class ClosureResponse(ClosureBase):
    """Schema for closure response."""
    model_config = ConfigDict(from_attributes=True)
    
    id: UUID
    is_active: bool = True
    created_by: Optional[UUID] = None
    created_at: datetime
    updated_at: datetime


# ═══════════════════════════════════════════════════════════
# EVENT SCHEMAS
# ═══════════════════════════════════════════════════════════

class EventBase(BaseModel):
    """Base schema for calendar events."""
    title: str = Field(..., max_length=200)
    description: Optional[str] = None
    start_date: date
    end_date: date
    start_time: Optional[time] = None
    end_time: Optional[time] = None
    is_all_day: bool = True
    event_type: str = Field(default="generic")
    visibility: str = Field(default="private", pattern="^(private|team|public)$")
    location: Optional[str] = None
    is_virtual: bool = False
    meeting_url: Optional[str] = None
    is_recurring: bool = False
    recurrence_rule: Optional[str] = None
    color: str = Field(default="#3B82F6", pattern="^#[0-9A-Fa-f]{6}$")


class EventCreate(EventBase):
    """Schema for creating an event."""
    participant_ids: Optional[List[UUID]] = None


class EventUpdate(BaseModel):
    """Schema for updating an event."""
    title: Optional[str] = Field(None, max_length=200)
    description: Optional[str] = None
    start_date: Optional[date] = None
    end_date: Optional[date] = None
    start_time: Optional[time] = None
    end_time: Optional[time] = None
    is_all_day: Optional[bool] = None
    event_type: Optional[str] = None
    visibility: Optional[str] = None
    location: Optional[str] = None
    is_virtual: Optional[bool] = None
    meeting_url: Optional[str] = None
    is_recurring: Optional[bool] = None
    recurrence_rule: Optional[str] = None
    color: Optional[str] = None
    status: Optional[str] = None


class ParticipantResponse(BaseModel):
    """Schema for event participant."""
    model_config = ConfigDict(from_attributes=True)
    
    id: UUID
    user_id: UUID
    response_status: str
    is_organizer: bool
    is_optional: bool
    responded_at: Optional[datetime] = None


class EventResponse(EventBase):
    """Schema for event response."""
    model_config = ConfigDict(from_attributes=True)
    
    id: UUID
    user_id: Optional[UUID] = None
    status: str = "confirmed"
    parent_event_id: Optional[UUID] = None
    created_by: Optional[UUID] = None
    created_at: datetime
    updated_at: datetime
    participants: List[ParticipantResponse] = []


# ═══════════════════════════════════════════════════════════
# WORKING DAY EXCEPTION SCHEMAS
# ═══════════════════════════════════════════════════════════

class WorkingDayExceptionCreate(BaseModel):
    """Schema for creating a working day exception."""
    date: date
    year: int
    exception_type: str = Field(..., pattern="^(working|non_working)$")
    reason: Optional[str] = Field(None, max_length=200)
    location_id: Optional[UUID] = None
    department_code: Optional[str] = None


class WorkingDayExceptionResponse(BaseModel):
    """Schema for working day exception response."""
    model_config = ConfigDict(from_attributes=True)
    
    id: UUID
    date: date
    year: int
    exception_type: str
    reason: Optional[str] = None
    location_id: Optional[UUID] = None
    department_code: Optional[str] = None
    created_at: datetime


# ═══════════════════════════════════════════════════════════
# AGGREGATED CALENDAR VIEW
# ═══════════════════════════════════════════════════════════

class CalendarDayItem(BaseModel):
    """Single item in a calendar day view."""
    id: UUID
    title: str
    item_type: str  # holiday, closure, event, leave, trip
    start_date: date
    end_date: date
    color: str
    metadata: Optional[dict] = None


class CalendarDayView(BaseModel):
    """Aggregated view of a single day."""
    date: date
    is_working_day: bool
    is_holiday: bool
    items: List[CalendarDayItem] = []


class CalendarRangeView(BaseModel):
    """Aggregated calendar view for a date range."""
    start_date: date
    end_date: date
    days: List[CalendarDayView] = []
    working_days_count: int = 0


class WorkingDaysRequest(BaseModel):
    """Request for calculating working days."""
    start_date: date
    end_date: date
    location_id: Optional[UUID] = None
    exclude_closures: bool = True
    exclude_holidays: bool = True


class WorkingDaysResponse(BaseModel):
    """Response for working days calculation."""
    start_date: date
    end_date: date
    total_calendar_days: int
    working_days: int
    holidays: List[date] = []
    closure_days: List[date] = []
    weekend_days: List[date] = []
