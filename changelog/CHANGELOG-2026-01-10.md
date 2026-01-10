# Changelog: HR Reporting Service & Timesheets

**Data:** 2026-01-10
**Versione:** v1.4.0
**Autore:** Antigravity AI

---

## 🌟 Summary

Rilascio completo del microservizio **HR Reporting** e integrazione della feature **Monthly Timesheet** (Giornaliero Presenze).
Questo aggiornamento introduce un'architettura dedicata per analytics, compliance D.Lgs 81/08 e gestione fogli presenza, separando queste logiche dai servizi operativi (Leaves/Expenses).

## 🏙️ New Microservice: HR Reporting

È stato creato il nuovo servizio `hr-reporting` seguendo i pattern architetturali Clean Architecture e Database-per-Service.

### 🏗️ Architecture
- **Path:** `backend/src/services/hr_reporting/`
- **Schema:** `hr_reporting` (PostgreSQL)
- **Key Models:**
  - `MonthlyTimesheet`: Gestione presenze mensili
  - `HRReportingSettings`: Configurazioni (deadline, finestre conferma)
  - `DailySnapshot`: Metriche giornaliere (workforce, assenze)
  - `TrainingRecord`: Formazione sicurezza (D.Lgs 81/08)
  - `SafetyCompliance`: Stato conformità dipendente

### 🔌 API Endpoints
- `GET /api/v1/hr/timesheets/me`: Lista timesheet utente corrente
- `GET /api/v1/hr/timesheets/me/{year}/{month}`: Dettaglio timesheet
- `GET /api/v1/hr/dashboard/overview`: HR Dashboard data
- `POST /api/v1/hr/admin/snapshots/create-daily`: Job snapshot giornaliero

---

## 📅 Feature: Monthly Timesheet

Implementazione completa del flusso di visualizzazione e conferma presenze.

### Backend
- **Data Aggregation:** `HRDataAggregator` colleziona dati da `leaves-service` e `expense-service` per comporre il quadro mensile.
- **Audit Logging:** Ogni conferma di timesheet genera un record in **Audit Trail** (`CONFIRM_TIMESHEET`).
- **Persistence:** Risolto bug critico di persistenza (schema mancante) tramite fix migrazione (`20260109_...`).

### Frontend
- **Page:** `TimesheetPage.tsx`
- **Route:** `/timesheets`
- **UI:** Visualizzazione "Calendario" con stati color-coded (Presenza, Ferie, Malattia, Trasferta).
- **Interactions:** Bottone di conferma sbloccato solo nella finestra temporale configurata.

---

## 🔒 Compliance & Security

- **RBAC:** Endpoints Admin protetti da permessi `reports:advanced`.
- **Database Migrations:** Consolidato schema `hr_reporting` e rimosse dipendenze errate da altri schemi.
- **Rules Refinement:** Aggiornata documentazione interna (`.agent/RULES.md`) per garantire standard su Audit e Migrazioni.

## 🐛 Bug Fixes

1.  **500 Persistence Error:** Risolto errore Alembic che impediva la creazione della tabella `monthly_timesheets`.
2.  **API Routing:** Corretta base URL frontend (`/hr/timesheets` invece di `/timesheets`).
3.  **Frontend Imports:** Fixati import mancanti in `TimesheetPage.tsx` e `PendingApprovalsPage.tsx`.

---

## 📝 Impacted Components

- `backend/src/services/hr_reporting/` (NEW)
- `frontend/src/pages/TimesheetPage.tsx` (NEW)
- `frontend/src/services/timesheet.service.ts` (NEW)
- `docs/HR_REPORTING_ARCHITECTURE.md` (NEW)
- `backend/alembic/versions/` (UPDATED)

---
