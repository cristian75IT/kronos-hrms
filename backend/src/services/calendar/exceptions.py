"""
KRONOS - Calendar Service Exceptions

Domain-specific exceptions for the calendar microservice.
Inherits from shared enterprise exceptions to ensure consistent error handling.
"""
from typing import Optional
from uuid import UUID

from src.shared.exceptions import (
    NotFoundError,
    ForbiddenError,
    BusinessRuleError
)


class CalendarNotFound(NotFoundError):
    """Raised when a specific calendar is not found."""
    def __init__(self, calendar_id: Optional[UUID] = None):
        super().__init__(
            resource_type="Calendar",
            resource_id=calendar_id
        )


class EventNotFound(NotFoundError):
    """Raised when a specific calendar event is not found."""
    def __init__(self, event_id: Optional[UUID] = None):
        super().__init__(
            resource_type="CalendarEvent",
            resource_id=event_id
        )


class HolidayProfileNotFound(NotFoundError):
    """Raised when a holiday profile is not found."""
    def __init__(self, profile_id: Optional[UUID] = None):
        super().__init__(
            resource_type="HolidayProfile",
            resource_id=profile_id
        )


class WorkWeekProfileNotFound(NotFoundError):
    """Raised when a work week profile is not found."""
    def __init__(self, profile_id: Optional[UUID] = None):
        super().__init__(
            resource_type="WorkWeekProfile",
            resource_id=profile_id
        )


class HolidayNotFound(NotFoundError):
    """Raised when a specific holiday entry is not found."""
    def __init__(self, holiday_id: Optional[UUID] = None):
        super().__init__(
            resource_type="CalendarHoliday",
            resource_id=holiday_id
        )


class CalendarAccessDenied(ForbiddenError):
    """Raised when user does not have required permissions on a calendar."""
    def __init__(self, calendar_id: Optional[UUID], user_id: UUID, required_permission: str = "read"):
        super().__init__(
            message=f"Access denied to calendar {calendar_id} for user {user_id}",
            resource_type="Calendar",
            resource_id=calendar_id,
            required_permission=required_permission
        )


class EventAccessDenied(ForbiddenError):
    """Raised when user does not have required permissions on an event."""
    def __init__(self, event_id: Optional[UUID], user_id: UUID, required_permission: str = "read"):
        super().__init__(
            message=f"Access denied to event {event_id} for user {user_id}",
            resource_type="CalendarEvent",
            resource_id=event_id,
            required_permission=required_permission
        )
