# KRONOS Calendar Service - Enterprise Architecture

## Executive Summary

The Calendar Service is the central time and scheduling authority for the entire KRONOS platform.
It provides a fully dynamic, database-driven calendar infrastructure that serves all microservices
with consistent date/time calculations, scheduling, and visualization capabilities.

---

## 🏗 Architecture Overview

```
┌───────────────────────────────────────────────────────────────────────────────┐
│                      ENTERPRISE CALENDAR SERVICE                               │
│              Central Authority for Time & Scheduling                           │
├───────────────────────────────────────────────────────────────────────────────┤
│                                                                               │
│  ┌─────────────────────────────────────────────────────────────────────────┐  │
│  │                         CONFIGURATION LAYER                             │  │
│  │                    (100% Database-Driven, No Static Data)               │  │
│  ├─────────────────────────────────────────────────────────────────────────┤  │
│  │                                                                         │  │
│  │  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐  ┌────────────┐  │  │
│  │  │ WORK WEEK    │  │   HOLIDAY    │  │   LOCATION   │  │   ZONE     │  │  │
│  │  │ PROFILES     │  │   PROFILES   │  │   SETTINGS   │  │ CALENDARS  │  │  │
│  │  ├──────────────┤  ├──────────────┤  ├──────────────┤  ├────────────┤  │  │
│  │  │ • 5-day week │  │ • National   │  │ • Per-site   │  │ Regional   │  │  │
│  │  │ • 6-day week │  │ • Regional   │  │   calendars  │  │ calendars  │  │  │
│  │  │ • Custom     │  │ • Local      │  │ • Holidays   │  │ Patronal   │  │  │
│  │  │ • Shifts     │  │ • Corporate  │  │ • Closures   │  │ feasts     │  │  │
│  │  └──────────────┘  └──────────────┘  └──────────────┘  └────────────┘  │  │
│  │                                                                         │  │
│  └─────────────────────────────────────────────────────────────────────────┘  │
│                                                                               │
│  ┌─────────────────────────────────────────────────────────────────────────┐  │
│  │                          DATA ENTITIES                                  │  │
│  ├─────────────────────────────────────────────────────────────────────────┤  │
│  │                                                                         │  │
│  │  ┌───────────────────────────────────────────────────────────────────┐  │  │
│  │  │                    calendar.work_week_profiles                    │  │  │
│  │  │  Defines working days per location/role/contract                  │  │  │
│  │  └───────────────────────────────────────────────────────────────────┘  │  │
│  │                                                                         │  │
│  │  ┌───────────────────────────────────────────────────────────────────┐  │  │
│  │  │                    calendar.holiday_profiles                      │  │  │
│  │  │  Groups of holidays (National ITA, Regional Lombardy, etc.)       │  │  │
│  │  └───────────────────────────────────────────────────────────────────┘  │  │
│  │                                                                         │  │
│  │  ┌───────────────────────────────────────────────────────────────────┐  │  │
│  │  │                    calendar.holidays                              │  │  │
│  │  │  Individual holidays with recurrence rules                        │  │  │
│  │  └───────────────────────────────────────────────────────────────────┘  │  │
│  │                                                                         │  │
│  │  ┌───────────────────────────────────────────────────────────────────┐  │  │
│  │  │                    calendar.closures                              │  │  │
│  │  │  Company-wide or location-specific closures                       │  │  │
│  │  └───────────────────────────────────────────────────────────────────┘  │  │
│  │                                                                         │  │
│  │  ┌───────────────────────────────────────────────────────────────────┐  │  │
│  │  │                    calendar.location_calendars                    │  │  │
│  │  │  Maps locations to work week + holiday profiles                   │  │  │
│  │  └───────────────────────────────────────────────────────────────────┘  │  │
│  │                                                                         │  │
│  │  ┌───────────────────────────────────────────────────────────────────┐  │  │
│  │  │                    calendar.events                                │  │  │
│  │  │  User/team events, meetings, reminders                            │  │  │
│  │  └───────────────────────────────────────────────────────────────────┘  │  │
│  │                                                                         │  │
│  └─────────────────────────────────────────────────────────────────────────┘  │
│                                                                               │
│  ┌─────────────────────────────────────────────────────────────────────────┐  │
│  │                          SERVICE APIS                                   │  │
│  ├─────────────────────────────────────────────────────────────────────────┤  │
│  │                                                                         │  │
│  │  INTERNAL (for microservices)          PUBLIC (for frontend)           │  │
│  │  ─────────────────────────             ──────────────────               │  │
│  │  • is_working_day(date, loc)           • GET /calendar/range            │  │
│  │  • calculate_working_days(range)       • GET /calendar/day/{date}       │  │
│  │  • get_holidays_for_location(loc)      • GET /holidays                  │  │
│  │  • get_next_working_day(date)          • GET /closures                  │  │
│  │  • get_work_week_profile(user)         • GET /events                    │  │
│  │  • recalculate_affected_leaves()       • Calendar CRUD                  │  │
│  │                                                                         │  │
│  └─────────────────────────────────────────────────────────────────────────┘  │
│                                                                               │
└───────────────────────────────────────────────────────────────────────────────┘
```

---

## 📊 Dynamic Configuration System

### 1. Work Week Profiles

All working day configurations are stored in the database, never hardcoded.

```sql
-- calendar.work_week_profiles
CREATE TABLE work_week_profiles (
    id UUID PRIMARY KEY,
    code VARCHAR(50) UNIQUE NOT NULL,       -- 'STANDARD_5', 'STANDARD_6', 'SHIFT_ALTERNATING'
    name VARCHAR(100) NOT NULL,             -- 'Standard 5-Day Week'
    description TEXT,
    
    -- Weekly configuration (JSON for flexibility)
    weekly_hours DECIMAL(5,2) DEFAULT 40,
    working_days JSONB NOT NULL,            -- {"mon": true, "tue": true, "wed": true, "thu": true, "fri": true, "sat": false, "sun": false}
    
    -- Half-day support
    half_days JSONB,                        -- {"sat": "morning"} for Saturday morning work
    
    -- Shift patterns (for complex schedules)
    shift_pattern JSONB,                    -- [{"week": 1, "days": ["mon", "tue", "wed"]}, {"week": 2, "days": ["thu", "fri", "sat"]}]
    
    is_default BOOLEAN DEFAULT FALSE,
    is_active BOOLEAN DEFAULT TRUE,
    created_at TIMESTAMP WITH TIME ZONE,
    updated_at TIMESTAMP WITH TIME ZONE
);
```

### 2. Holiday Profiles

Holidays are grouped into profiles for reusability.

```sql
-- calendar.holiday_profiles
CREATE TABLE holiday_profiles (
    id UUID PRIMARY KEY,
    code VARCHAR(50) UNIQUE NOT NULL,       -- 'ITA_NATIONAL', 'ITA_LOMBARDY', 'CUSTOM_COMPANY'
    name VARCHAR(100) NOT NULL,             -- 'Italy - National Holidays'
    description TEXT,
    country_code VARCHAR(2),                -- 'IT'
    region_code VARCHAR(10),                -- 'LOM' for Lombardy
    is_active BOOLEAN DEFAULT TRUE,
    created_at TIMESTAMP WITH TIME ZONE
);

-- calendar.holidays (linked to profiles)
CREATE TABLE holidays (
    id UUID PRIMARY KEY,
    profile_id UUID REFERENCES holiday_profiles(id),
    name VARCHAR(100) NOT NULL,
    date DATE,                              -- NULL if recurring
    
    -- Recurrence (for holidays like Easter Monday)
    recurrence_type VARCHAR(20),            -- 'fixed', 'easter_relative', 'nth_weekday'
    recurrence_rule JSONB,                  -- {"month": 1, "day": 1} for fixed, {"offset": 1} for Easter Monday
    
    is_active BOOLEAN DEFAULT TRUE,
    created_at TIMESTAMP WITH TIME ZONE
);
```

### 3. Location Calendars

Each location can have its own calendar configuration.

```sql
-- calendar.location_calendars
CREATE TABLE location_calendars (
    id UUID PRIMARY KEY,
    location_id UUID NOT NULL,              -- References auth.locations
    
    work_week_profile_id UUID REFERENCES work_week_profiles(id),
    
    -- Multiple holiday profiles (national + regional + company)
    holiday_profile_ids UUID[],
    
    -- Timezone
    timezone VARCHAR(50) DEFAULT 'Europe/Rome',
    
    -- Year-based configuration changes
    effective_from DATE NOT NULL,
    effective_to DATE,
    
    is_active BOOLEAN DEFAULT TRUE,
    created_at TIMESTAMP WITH TIME ZONE
);
```

---

## 🔧 Enterprise Features

### 1. Automatic Holiday Generation

The system automatically generates yearly holidays from recurrence rules:

```python
async def generate_holidays_for_year(self, year: int, profile_id: UUID) -> List[Holiday]:
    """Generate all holidays for a year based on profile rules."""
    profile = await self.get_holiday_profile(profile_id)
    holidays = []
    
    for rule in profile.holidays:
        if rule.recurrence_type == "fixed":
            # Fixed date (e.g., January 1st)
            holiday_date = date(year, rule.recurrence_rule["month"], rule.recurrence_rule["day"])
        elif rule.recurrence_type == "easter_relative":
            # Easter-relative (e.g., Easter Monday)
            easter_date = self._calculate_easter(year)
            holiday_date = easter_date + timedelta(days=rule.recurrence_rule["offset"])
        elif rule.recurrence_type == "nth_weekday":
            # Nth weekday of month (e.g., 4th Thursday of November)
            holiday_date = self._get_nth_weekday(
                year,
                rule.recurrence_rule["month"],
                rule.recurrence_rule["weekday"],
                rule.recurrence_rule["nth"]
            )
        
        holidays.append(Holiday(date=holiday_date, name=rule.name, profile_id=profile_id))
    
    return holidays
```

### 2. Cross-Service Integration

The Calendar Service provides a consistent API for all services:

```python
# Internal API endpoints (for microservices)

@router.get("/internal/is-working-day")
async def check_working_day(
    date: date,
    location_id: Optional[UUID] = None,
    user_id: Optional[UUID] = None,
):
    """Check if a date is a working day for a location/user."""
    return await service.is_working_day(date, location_id, user_id)

@router.get("/internal/calculate-working-days")
async def calculate_working_days(
    start_date: date,
    end_date: date,
    location_id: Optional[UUID] = None,
):
    """Calculate working days between two dates."""
    return await service.calculate_working_days(start_date, end_date, location_id)

@router.get("/internal/next-working-day")
async def get_next_working_day(from_date: date, location_id: Optional[UUID] = None):
    """Get the next working day after a given date."""
    return await service.get_next_working_day(from_date, location_id)

@router.get("/internal/excluded-days")
async def get_excluded_days(
    start_date: date,
    end_date: date,
    location_id: Optional[UUID] = None,
):
    """Get all non-working days in a range (for leave calculations)."""
    return await service.get_excluded_days(start_date, end_date, location_id)
```

### 3. Visualization & Analytics

Enterprise-grade calendar visualization:

```json
// GET /api/v1/calendar/analytics/year/2026
{
    "year": 2026,
    "summary": {
        "total_days": 365,
        "working_days": 252,
        "holidays": 12,
        "weekends": 104,
        "closures": 5
    },
    "by_quarter": [
        {"q": 1, "working_days": 64, "holidays": 3},
        {"q": 2, "working_days": 62, "holidays": 3},
        {"q": 3, "working_days": 66, "holidays": 2},
        {"q": 4, "working_days": 60, "holidays": 4}
    ],
    "by_month": [
        {"month": 1, "working_days": 21, "holidays": 2, "closures": 0}
        // ...
    ],
    "holiday_list": [
        {"date": "2026-01-01", "name": "Capodanno", "type": "national"},
        {"date": "2026-01-06", "name": "Epifania", "type": "national"}
        // ...
    ]
}
```

### 4. Admin Dashboard Data

Real-time calendar administration:

```json
// GET /api/v1/calendar/admin/dashboard
{
    "current_status": {
        "today": "2026-01-03",
        "is_working_day": true,
        "next_holiday": {"date": "2026-01-06", "name": "Epifania"},
        "next_closure": null,
        "days_until_next_holiday": 3
    },
    "upcoming_closures": [
        {"start": "2026-08-08", "end": "2026-08-16", "name": "Chiusura estiva"}
    ],
    "configuration": {
        "active_work_week_profiles": 3,
        "active_holiday_profiles": 5,
        "locations_configured": 8,
        "pending_approvals": 0
    },
    "statistics": {
        "holidays_this_year": 12,
        "closures_this_year": 15,
        "working_days_remaining": 249
    }
}
```

---

## 🔄 Data Flow

```
                                    ┌─────────────────────────┐
                                    │      ADMIN PORTAL       │
                                    │  Configure calendars    │
                                    └───────────┬─────────────┘
                                                │
                                                ▼
┌─────────────────────────────────────────────────────────────────────────────┐
│                           CALENDAR SERVICE                                   │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                             │
│  ┌─────────────────┐     ┌─────────────────┐     ┌─────────────────┐       │
│  │ Work Week       │     │ Holiday         │     │ Location        │       │
│  │ Profiles        │────▶│ Profiles        │────▶│ Calendars       │       │
│  └─────────────────┘     └─────────────────┘     └────────┬────────┘       │
│                                                           │                 │
│                                                           ▼                 │
│                                              ┌─────────────────────┐        │
│                                              │ CALCULATION ENGINE  │        │
│                                              │ - Working days calc │        │
│                                              │ - Holiday detection │        │
│                                              │ - Closure checking  │        │
│                                              └──────────┬──────────┘        │
│                                                         │                   │
└─────────────────────────────────────────────────────────┼───────────────────┘
                                                          │
        ┌─────────────────────────┬───────────────────────┼───────────────────┐
        │                         │                       │                   │
        ▼                         ▼                       ▼                   ▼
┌───────────────┐        ┌───────────────┐       ┌───────────────┐   ┌───────────────┐
│ LEAVE SERVICE │        │EXPENSE SERVICE│       │  HR REPORTING │   │   FRONTEND    │
│ - Request days│        │ - Trip days   │       │ - Analytics   │   │ - Calendars   │
│ - Calculations│        │ - Allowances  │       │ - Reports     │   │ - Schedule    │
└───────────────┘        └───────────────┘       └───────────────┘   └───────────────┘
```

---

## 📁 Implementation Files

### New/Enhanced Files

```
backend/src/services/calendar/
├── models.py                    # ENHANCED - Enterprise models
│   ├── WorkWeekProfile         # NEW
│   ├── HolidayProfile          # NEW
│   ├── LocationCalendar        # NEW
│   ├── CalendarHoliday         # ENHANCED (linked to profiles)
│   ├── CalendarClosure         # EXISTING
│   ├── CalendarEvent           # EXISTING
│   └── WorkingDayException     # EXISTING
│
├── schemas.py                   # ENHANCED - Enterprise schemas
│   ├── WorkWeekProfileCreate/Response
│   ├── HolidayProfileCreate/Response
│   ├── LocationCalendarCreate/Response
│   ├── CalendarAnalytics
│   └── AdminDashboard
│
├── service.py                   # ENHANCED - Enterprise logic
│   ├── Profile Management
│   ├── Holiday Generation
│   ├── Location Calendars
│   └── Analytics & Reporting
│
├── routers/
│   ├── profiles.py             # NEW - Work week & holiday profiles
│   ├── locations.py            # NEW - Location calendar config
│   ├── analytics.py            # NEW - Calendar analytics
│   ├── admin.py                # NEW - Admin dashboard
│   └── internal.py             # NEW - Internal API for services
│
└── utils/
    ├── easter.py               # Easter calculation algorithm
    └── recurrence.py           # Holiday recurrence engine
```

---

## 🇮🇹 Italian Calendar Compliance

### National Holidays (Preset Profile)

```python
ITALIAN_NATIONAL_HOLIDAYS = [
    {"name": "Capodanno", "recurrence_type": "fixed", "rule": {"month": 1, "day": 1}},
    {"name": "Epifania", "recurrence_type": "fixed", "rule": {"month": 1, "day": 6}},
    {"name": "Pasqua", "recurrence_type": "easter_relative", "rule": {"offset": 0}},
    {"name": "Lunedì dell'Angelo", "recurrence_type": "easter_relative", "rule": {"offset": 1}},
    {"name": "Festa della Liberazione", "recurrence_type": "fixed", "rule": {"month": 4, "day": 25}},
    {"name": "Festa del Lavoro", "recurrence_type": "fixed", "rule": {"month": 5, "day": 1}},
    {"name": "Festa della Repubblica", "recurrence_type": "fixed", "rule": {"month": 6, "day": 2}},
    {"name": "Ferragosto", "recurrence_type": "fixed", "rule": {"month": 8, "day": 15}},
    {"name": "Tutti i Santi", "recurrence_type": "fixed", "rule": {"month": 11, "day": 1}},
    {"name": "Immacolata Concezione", "recurrence_type": "fixed", "rule": {"month": 12, "day": 8}},
    {"name": "Natale", "recurrence_type": "fixed", "rule": {"month": 12, "day": 25}},
    {"name": "Santo Stefano", "recurrence_type": "fixed", "rule": {"month": 12, "day": 26}},
]
```

### Regional/Local Patron Saints

Patron saint days are configurable per location via `location_calendars` table.

---

## ✅ Implementation Phases

### Phase 1: Core Enterprise Models ⬅️ CURRENT
- [ ] Work Week Profiles table + CRUD
- [ ] Holiday Profiles table + CRUD  
- [ ] Location Calendars table + CRUD
- [ ] Migration from static to dynamic

### Phase 2: Calculation Engine
- [ ] Holiday generation from rules
- [ ] Easter calculation algorithm
- [ ] Profile-based working day calc
- [ ] Timezone support

### Phase 3: Integration & Analytics
- [ ] Internal API for microservices
- [ ] Calendar analytics endpoints
- [ ] Admin dashboard data
- [ ] Audit trail integration

### Phase 4: Visualization
- [ ] Year overview endpoint
- [ ] Department/team calendars
- [ ] Export enhancements
- [ ] Real-time updates
