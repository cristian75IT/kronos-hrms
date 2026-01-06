# Changelog - 2026-01-06

## [v1.3.0] - Global Repository Pattern & Architecture Refactor

### Added
- **Enterprise Repository Pattern**: Standardized 3-layer architecture (Router -> Service -> Repository) across all microservices.
- **LocationCalendarRepository.get_default**: For retrieving the default calendar configuration.
- **CalendarExternalRepository**: Dedicated repository in Notifications service for safe cross-module calendar data access.
- **ContractRepository.get_user_by_keycloak_id**: Optimized user lookup for accrual logic.

### Changed
- **Modular Services**: Split monolithic `CalendarService` and `ConfigService` into domain-specific sub-services (Calendars, Events, Profiles, Contracts) orchestrated by a Facade.
- **Service Layer Cleanliness**: Removed all direct SQLAlchemy queries (`session.execute`, `select`, `session.add`) from service and router layers.
- **Accrual Service**: Optimized leave accrual previews to use repository methods.
- **Notifications & Approvals**: Refactored Celery tasks to use repository layer exclusively.

### Removed
- **Legacy Code**: Decommissioned and deleted 8 legacy service files:
    - `backend/src/services/leaves/service_legacy.py`
    - `backend/src/services/calendar/service.py`
    - `backend/src/services/config/service.py`
    - `backend/src/services/notifications/service_legacy.py`
    - `backend/src/services/approvals/service_legacy.py`
    - `backend/src/services/expenses/service_legacy.py`
    - and others.

---
**Note**: This refactor significantly improves system maintainability, audatibility, and adherence to Enterprise standards.
