# KRONOS HR Reporting Service - Enterprise Architecture

## Executive Summary

The HR Reporting Service is the central hub for workforce analytics, compliance reporting, and management dashboards. It aggregates data from all KRONOS microservices to provide actionable insights for HR professionals.

---

## 🏗 Architecture Overview

```
┌───────────────────────────────────────────────────────────────────────────┐
│                         HR REPORTING SERVICE                              │
│                     Enterprise Workforce Analytics                        │
├───────────────────────────────────────────────────────────────────────────┤
│                                                                           │
│  ┌─────────────────────────────────────────────────────────────────────┐  │
│  │                         DATA SOURCES                                │  │
│  ├─────────────────────────────────────────────────────────────────────┤  │
│  │  ┌─────────┐ ┌─────────┐ ┌─────────┐ ┌─────────┐ ┌─────────┐       │  │
│  │  │ LEAVES  │ │EXPENSES │ │CALENDAR │ │  AUTH   │ │  AUDIT  │       │  │
│  │  │ SERVICE │ │ SERVICE │ │ SERVICE │ │(USERS)  │ │ SERVICE │       │  │
│  │  └────┬────┘ └────┬────┘ └────┬────┘ └────┬────┘ └────┬────┘       │  │
│  │       │           │           │           │           │            │  │
│  │       └───────────┴───────────┴───────────┴───────────┘            │  │
│  │                               │                                     │  │
│  │                       ┌───────▼───────┐                            │  │
│  │                       │  AGGREGATION  │                            │  │
│  │                       │    ENGINE     │                            │  │
│  │                       └───────┬───────┘                            │  │
│  └───────────────────────────────┼─────────────────────────────────────┘  │
│                                  │                                        │
│  ┌───────────────────────────────▼─────────────────────────────────────┐  │
│  │                         REPORT TYPES                                │  │
│  ├─────────────────────────────────────────────────────────────────────┤  │
│  │                                                                     │  │
│  │  ┌─────────────────┐  ┌─────────────────┐  ┌─────────────────┐     │  │
│  │  │   DASHBOARDS    │  │ PERIODIC REPORTS│  │   COMPLIANCE    │     │  │
│  │  ├─────────────────┤  ├─────────────────┤  ├─────────────────┤     │  │
│  │  │ • HR Overview   │  │ • Monthly Recap │  │ • Legal Minimum │     │  │
│  │  │ • Team Stats    │  │ • Quarterly     │  │ • Audit Trail   │     │  │
│  │  │ • Absence Trend │  │ • Annual Summary│  │ • Policy Check  │     │  │
│  │  │ • Budget Monitor│  │ • Custom Range  │  │ • Anomaly Alert │     │  │
│  │  │ • Real-time KPIs│  │ • Export (PDF)  │  │ • LUL Export    │     │  │
│  │  └─────────────────┘  └─────────────────┘  └─────────────────┘     │  │
│  │                                                                     │  │
│  └─────────────────────────────────────────────────────────────────────┘  │
│                                                                           │
└───────────────────────────────────────────────────────────────────────────┘
```

---

## 🎯 Italian HR Standards Compliance

### Legal Requirements (D.Lgs. 66/2003, L. 300/1970)

| Requirement | Report Type | Frequency |
|-------------|-------------|-----------|
| Minimo legale ferie (2 settimane) | Compliance Report | Monthly |
| Ferie anno precedente (scadenza 30/06) | Alert & Status | Daily check |
| Straordinari massimi | Work Hours Report | Weekly |
| Riposo giornaliero/settimanale | Anomaly Detection | Real-time |
| ROL residue non godute | Balance Report | Monthly |

### CCNL Integration

- Support for multiple CCNL configurations
- Per-diem rates by destination type
- Leave accrual rules by contract type
- Overtime calculation by role

---

## 📊 Report Categories

### 1. Real-Time Dashboards

```python
# HR Overview Dashboard
{
    "date": "2026-01-03",
    "workforce": {
        "total_employees": 150,
        "on_leave_today": 12,
        "on_trip_today": 5,
        "working_remotely": 25,
        "absent_rate": 8.0
    },
    "pending_approvals": {
        "leave_requests": 8,
        "expense_reports": 3,
        "trip_requests": 2
    },
    "alerts": [
        {"type": "VACATION_EXPIRING", "count": 5, "severity": "warning"},
        {"type": "POLICY_VIOLATION", "count": 1, "severity": "critical"}
    ]
}
```

### 2. Monthly Absence Report (LUL Compatible)

```python
# Per-employee monthly summary
{
    "period": "2026-01",
    "employee": {
        "id": "uuid",
        "fiscal_code": "RSSMRA85...",
        "full_name": "Mario Rossi"
    },
    "absences": {
        "vacation": {"days": 3, "hours": 24},
        "rol": {"days": 0.5, "hours": 4},
        "permits": {"days": 0, "hours": 2},
        "sick_leave": {"days": 2, "hours": 16},
        "other": {"days": 0, "hours": 0}
    },
    "balances": {
        "vacation_remaining": {"ap": 5, "ac": 12},
        "rol_remaining": 20,
        "permits_remaining": 30
    },
    "trips": {
        "count": 1,
        "total_days": 3,
        "total_expenses": 450.00,
        "total_allowances": 150.00
    },
    "payroll_codes": {
        "FERIE": 24,  # hours
        "ROL": 4,
        "PERM": 2,
        "MALATTIA": 16
    }
}
```

### 3. Compliance Report

```python
{
    "period": "2026-01",
    "compliance_status": "WARNING",
    "issues": [
        {
            "employee_id": "uuid",
            "type": "VACATION_LEGAL_MINIMUM",
            "description": "Dipendente non ha usufruito del minimo legale di ferie",
            "deadline": "2026-06-30",
            "days_missing": 3
        }
    ],
    "statistics": {
        "employees_compliant": 145,
        "employees_at_risk": 5,
        "compliance_rate": 96.7
    }
}
```

### 4. Budget Report

```python
{
    "period": "2026-01",
    "expenses": {
        "trips_budget": 50000.00,
        "trips_spent": 12500.00,
        "trips_utilization": 25.0,
        "by_department": [
            {"department": "Sales", "budget": 20000, "spent": 8500},
            {"department": "Tech", "budget": 15000, "spent": 3000}
        ]
    },
    "leave_cost": {
        "vacation_days_taken": 250,
        "estimated_cost": 75000.00,  # Avg daily cost × days
        "sick_leave_days": 45,
        "sick_leave_cost": 13500.00
    }
}
```

---

## 🔧 Technical Implementation

### Service Structure

```
backend/src/services/hr_reporting/
├── models.py               # ORM Models (Report, Snapshot, Alert)
├── repository.py           # NEW - Central data access with specialized repositories
├── schemas.py              # Pydantic models for I/O
├── service.py              # Business logic (coordinates repos)
├── routers/                # HTTP Endpoints (Router Layer)
│   ├── dashboard.py        # Real-time metrics
│   ├── reports.py          # Report management
│   └── training.py         # Specialized training reporting
```

### Key APIs

| Endpoint | Method | Description |
|----------|--------|-------------|
| `/dashboard/overview` | GET | Real-time HR dashboard |
| `/dashboard/team/{id}` | GET | Team-specific metrics |
| `/reports/monthly` | GET | Monthly absence report |
| `/reports/compliance` | GET | Legal compliance status |
| `/reports/budget` | GET | Expense budget report |
| `/reports/custom` | POST | Custom date range report |
| `/export/lul/{month}` | GET | LUL-compatible export (XML) |
| `/export/excel/{type}` | GET | Excel export |
| `/alerts/active` | GET | Active alerts list |

---

## 🔐 Security & Access Control

### Role-Based Access

| Role | Dashboard | Reports | Export | Admin |
|------|-----------|---------|--------|-------|
| HR Manager | ✅ Full | ✅ Full | ✅ Full | ✅ |
| Manager | ✅ Team only | ✅ Team | ✅ Team | ❌ |
| Finance | ❌ | ✅ Budget | ✅ Budget | ❌ |
| Employee | ❌ | ❌ | ❌ | ❌ |

### Audit Trail

All report generation and data access is logged:
- Who requested the report
- What data was accessed
- When and from where
- Export file hashes

---

## 📈 Performance Considerations

### Caching Strategy

```python
CACHE_TTL = {
    "dashboard_overview": 60,      # 1 minute
    "team_stats": 300,             # 5 minutes
    "monthly_report": 3600,        # 1 hour (invalidate on data change)
    "compliance_report": 86400,    # 24 hours
}
```

### Data Snapshots

For historical reporting, we maintain periodic snapshots:
- Daily employee status snapshot
- Monthly balance snapshot
- Annual summary snapshot

---

## 🚀 Implementation Phases

### Phase 1: Core (Current)
- [ ] Service skeleton
- [ ] Dashboard endpoints
- [ ] Basic monthly report
- [ ] Client integration

### Phase 2: Advanced
- [ ] PDF export
- [ ] LUL XML export
- [ ] Custom reports builder
- [ ] Scheduled report generation

### Phase 3: Analytics
- [ ] Trend analysis
- [ ] Predictive alerts
- [ ] Cost projections
- [ ] Benchmark reports
