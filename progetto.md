# KRONOS - Enterprise HRMS

> **Κρόνος** - Sistema Enterprise per Gestione Presenze, Assenze e Rimborsi

**Versione**: 1.0.0  
**Data**: 2024-12-30  
**Stack**: FastAPI + React + PostgreSQL

---

## 1. Introduzione e Obiettivi

KRONOS è una piattaforma web Enterprise-grade per la digitalizzazione dei processi HR:
- Gestione Assenze (Ferie, Permessi, ROL, Malattia, Altri Congedi)
- Gestione Trasferte e Rimborsi Spese
- Workflow Approvativo multi-livello
- Compliance Normativa Italiana (D.Lgs 66/2003)

### Principi Architetturali

| # | Principio | Descrizione |
|---|-----------|-------------|
| 1 | **Zero Hardcoding** | Tutti i parametri in database (`system_config`) |
| 2 | **Database Isolation** | PostgreSQL unico, schema separati per microservizio |
| 3 | **SSO Enterprise** | Keycloak con LDAP/OAuth2/MFA |
| 4 | **API Gateway WAF** | Nginx + ModSecurity (OWASP CRS) |
| 5 | **DataTables Backend** | Sempre paginazione/filter/sort server-side |
| 6 | **Librerie Standard** | DataTables.net, FullCalendar, Brevo - MAI custom |
| 7 | **Clean Architecture** | Router → Service → Repository → Model |
| 8 | **Audit Completo** | Log + Trail su tutte le operazioni |
| 9 | **Async First** | SQLAlchemy 2.0 async, FastAPI async |

---

## 2. Architettura

### 2.1 Network Architecture

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                          EXTERNAL NETWORK (kronos-external)                  │
│  ┌─────────────────────────────────────────────────────────────────────┐    │
│  │                         KEYCLOAK SSO                                  │    │
│  │                    (Identity Provider)                                │    │
│  │              http://keycloak.local:8080                               │    │
│  └─────────────────────────────────────────────────────────────────────┘    │
└─────────────────────────────────────────────────────────────────────────────┘
                                     │ OIDC / JWT
┌────────────────────────────────────┼─────────────────────────────────────────┐
│                          INTERNAL NETWORK (kronos-internal)                  │
│                                                                              │
│  ┌─────────────────────────────────────────────────────────────────────┐    │
│  │                    NGINX + MODSECURITY (API Gateway)                  │    │
│  │  • Rate Limiting  • WAF (OWASP CRS)  • SSL  • Routing  • Logging     │    │
│  └─────────────────────────────────────────────────────────────────────┘    │
│                                    │                                         │
│  ┌──────────┬──────────┬──────────┬──────────┬──────────┬──────────┐        │
│  │ Auth     │ Leave    │ Expense  │ Config   │ Notif.   │ Audit    │        │
│  │ :8001    │ :8002    │ :8003    │ :8004    │ :8005    │ :8007    │        │
│  └────┬─────┴────┬─────┴────┬─────┴────┬─────┴────┬─────┴────┬─────┘        │
│       │          │          │          │          │          │              │
│  ┌────┴──────────┴──────────┴──────────┴──────────┴──────────┴────┐         │
│  │                        PostgreSQL :5432                         │         │
│  │   auth | leaves | expenses | config | notifications | audit     │         │
│  └────────────────────────────────────────────────────────────────┘         │
│                                                                              │
│  ┌─────────────┐          ┌─────────────┐          ┌─────────────┐         │
│  │    Redis    │          │    MinIO    │          │   Frontend  │         │
│  │   :6379     │          │  :9000/9001 │          │   :3000     │         │
│  └─────────────┘          └─────────────┘          └─────────────┘         │
└──────────────────────────────────────────────────────────────────────────────┘
```

### 2.2 Microservizi

| Servizio | Porta | Schema DB | Responsabilità |
|----------|-------|-----------|----------------|
| **auth-service** | 8001 | auth | User sync da Keycloak, ruoli, aree, sedi |
| **leave-service** | 8002 | leaves | Richieste assenze, saldi, workflow |
| **expense-service** | 8003 | expenses | Trasferte, note spese, diarie |
| **config-service** | 8004 | config | Parametri sistema, leave types, holidays |
| **notification-service** | 8005 | notifications | Email via Brevo, in-app, queue |
| **audit-service** | 8007 | audit | Audit log, audit trail, retention |

### 2.3 Database Schema Isolation

Ogni microservizio opera su uno schema PostgreSQL dedicato:

```sql
CREATE SCHEMA auth;
CREATE SCHEMA leaves;
CREATE SCHEMA expenses;
CREATE SCHEMA config;
CREATE SCHEMA notifications;
CREATE SCHEMA audit;
```

---

## 3. Stack Tecnologico

### Backend

| Categoria | Tecnologia | Versione |
|-----------|------------|----------|
| Runtime | Python | 3.11+ |
| Framework | FastAPI | 0.109+ |
| ORM | SQLAlchemy | 2.0+ (async) |
| Migrations | Alembic | 1.13+ |
| Validation | Pydantic | 2.0+ |
| Database | PostgreSQL | 15+ |
| Cache | Redis | 7+ |
| Task Queue | Celery | 5.3+ |
| File Storage | MinIO | Latest |
| API Gateway | Nginx + ModSecurity | Latest |

### Frontend

| Categoria | Tecnologia | Versione |
|-----------|------------|----------|
| Framework | React | 18+ |
| Build Tool | Vite | 5+ |
| Language | TypeScript | 5+ |
| State | TanStack Query | 5+ |
| UI | Shadcn/ui | Latest |
| **DataTables** | DataTables.net | 2.0+ |
| **Calendar** | FullCalendar | 6+ |
| Forms | React Hook Form + Zod | 7+ |

### Integrazioni

| Servizio | Provider | Scopo |
|----------|----------|-------|
| **SSO** | Keycloak | OIDC, LDAP, MFA |
| **Email** | Brevo | Transactional email, templates |
| **Storage** | MinIO | Allegati, ricevute |

---

## 4. Modello Organizzativo (RBAC)

### 4.1 Ruoli (Gestiti in Keycloak)

| Ruolo | Descrizione |
|-------|-------------|
| `admin` | Amministratore HR - accesso completo |
| `manager` | Responsabile Area - vede team |
| `employee` | Dipendente - solo propri dati |

### 4.2 Capabilities

| Capability | Descrizione |
|------------|-------------|
| `approver` | Può approvare richieste (assegnabile a manager) |

### 4.3 Struttura Organizzativa

- **Users**: Sincronizzati da Keycloak/LDAP
- **Areas**: Dipartimenti/Team (N:M con users)
- **Locations**: Sedi con Santo Patrono
- **ContractTypes**: Full-Time, Part-Time con percentuali
- **WorkSchedules**: Profili orari settimanali

---

## 5. Gestione Assenze

### 5.1 Tipi di Assenza (Configurabili da DB)

| Codice | Nome | Scala Saldo | Approv. | Preavviso |
|--------|------|-------------|---------|-----------|
| FER | Ferie | Sì (vacation) | Sì | 5gg |
| ROL | Riduzione Orario | Sì (rol) | Sì | 2gg |
| PER | Permessi Ex Festività | Sì (permits) | Sì | - |
| MAL | Malattia | No | No | 0 (retroattivo) |
| LUT | Lutto | No | Sì | - |
| MAT | Matrimonio | No | Sì | 15gg |
| L104 | Legge 104 | No | Sì | - |
| DON | Donazione Sangue | No | No | - |

### 5.2 Gestione Saldi

| Tipo | Logica |
|------|--------|
| Ferie AP | Anno Precedente - eroso per primo (FIFO) |
| Ferie AC | Anno Corrente - maturazione mensile |
| ROL | Ore accumulate mensili |
| Permessi | Ore Ex Festività annuali |

### 5.3 Workflow Stati

```
DRAFT → PENDING → APPROVED → COMPLETED
           ↓           ↓
     REJECTED    APPROVED_CONDITIONAL → (accept) → APPROVED
                       ↓
                   CANCELLED
                       ↓
                   RECALLED
```

### 5.4 Condizioni Approvazione

| Codice | Condizione |
|--------|------------|
| RIC | Riserva di Richiamo |
| REP | Reperibilità |
| PAR | Approvazione Parziale |
| MOD | Modifica Date |
| ALT | Altra Condizione |

---

## 6. Gestione Trasferte e Rimborsi

### 6.1 Trasferte (BusinessTrip)

| Campo | Descrizione |
|-------|-------------|
| destination | Luogo destinazione |
| purpose | Motivo trasferta |
| start_date / end_date | Periodo |
| daily_allowance | Diaria calcolata automaticamente |

### 6.2 Regole Diaria

| Destinazione | Giorno Intero | Mezza Giornata |
|--------------|---------------|----------------|
| Italia | €46.48 | €25.00 |
| UE | €77.47 | €40.00 |
| Extra-UE | Configurabile | Configurabile |

### 6.3 Tipologie Spesa Rimborsabile

| Codice | Categoria | Limite | Ricevuta |
|--------|-----------|--------|----------|
| TRA | Trasporti | - | Sì |
| AUT | Auto Propria | €0.30/km | No |
| PED | Pedaggi | - | Sì |
| ALB | Alloggio | €120/notte | Sì |
| PAS | Pasti | €30/pasto | Sì |
| TEL | Telefono/Internet | €20/giorno | Sì |

### 6.4 Workflow Rimborsi

```
ExpenseReport: DRAFT → SUBMITTED → APPROVED → PAID
                          ↓
                     REJECTED / PARTIALLY_APPROVED
```

---

## 7. Compliance Normativa Italiana

### Riferimenti Normativi

- **D.Lgs 66/2003** Art. 10: Disciplina ferie
- **Art. 36 Costituzione**: Irrinunciabilità ferie
- **Art. 2109 C.C.**: Diritto di richiamo

### Regole Automatiche Implementate

| Regola | Normativa | Implementazione |
|--------|-----------|-----------------|
| Minimo 4 settimane/anno | D.Lgs 66/2003 | Validazione monte ferie |
| 2 settimane consecutive | D.Lgs 66/2003 | Alert se non fruite entro anno |
| Residuo entro 18 mesi | D.Lgs 66/2003 | Tracking scadenza AP |
| Non monetizzabilità | D.Lgs 66/2003 | No eliminazione saldi |
| Diritto di richiamo | Art. 2109 C.C. | Workflow RECALLED + rimborso |

### Alert Automatici Compliance

| Alert | Trigger | Destinatario |
|-------|---------|--------------|
| Ferie AP in scadenza | 60gg prima scadenza | Dipendente + HR |
| Obbligo 2 settimane | 1 Novembre | Dipendente + Manager |
| Saldo elevato | >30gg fine anno | HR |
| Ferie non pianificate | Nessuna nei 3 mesi | Manager |

---

## 8. Sistema Notifiche

### 8.1 Provider: Brevo (ex Sendinblue)

Integrazione API v3 per email transazionali con template.

### 8.2 Template Email

| ID | Template | Trigger |
|----|----------|---------|
| 1 | leave_request_pending | Nuova richiesta assenza |
| 2 | leave_request_approved | Approvazione |
| 3 | leave_request_rejected | Rifiuto |
| 4 | leave_request_conditional | Approvazione con condizioni |
| 5 | leave_request_recalled | Richiamo dalle ferie |
| 6 | expense_submitted | Nota spese inviata |
| 7 | expense_approved | Nota spese approvata |
| 8 | expense_paid | Pagamento effettuato |
| 9 | approval_reminder | Reminder approvazioni pendenti |
| 10 | balance_alert | Saldo in scadenza |

### 8.3 Canali

| Canale | Descrizione |
|--------|-------------|
| Email | Via Brevo API con template |
| In-App | Notifiche real-time (bell icon) |
| Daily Digest | Riepilogo giornaliero (opzionale) |

### 8.4 Preferenze Utente

Ogni utente può configurare:
- Abilitazione email/in-app per categoria
- Orario digest giornaliero
- Opt-out per tipologia notifica

---

## 9. Audit System

### 9.1 Audit Log

Traccia tutte le azioni utente:

| Campo | Descrizione |
|-------|-------------|
| user_id, email, role | Chi |
| action, entity_type, entity_id | Cosa |
| old_values, new_values, changes | Modifiche |
| service_name, endpoint, method | Dove |
| ip_address, user_agent | Client |
| status, error_message | Risultato |

### 9.2 Audit Trail

History completa con versioning per ogni entità:

| Campo | Descrizione |
|-------|-------------|
| entity_type, entity_id | Entità tracciata |
| version | Numero versione incrementale |
| snapshot | Stato completo dell'entità |
| modified_by, modification_type | Chi e come |

---

## 10. Configurazione Dinamica

### Principio Zero Hardcoding

> Nessun valore di business può essere hardcoded nel codice.
> Tutti i parametri risiedono in database e sono modificabili da Admin.

### Tabella system_config

| Campo | Tipo | Descrizione |
|-------|------|-------------|
| key | VARCHAR | Chiave univoca (es. `leave.min_notice_days.rol`) |
| value | JSONB | Valore (supporta tipi complessi) |
| value_type | VARCHAR | string, integer, boolean, float, json |
| category | VARCHAR | Categoria per raggruppamento UI |

### Configurazioni Principali

| Key | Default | Categoria |
|-----|---------|-----------|
| leave.min_notice_days.rol | 2 | leave_policy |
| leave.min_notice_days.vacation | 5 | leave_policy |
| leave.max_consecutive_days | 15 | leave_policy |
| leave.allow_negative_balance | false | leave_policy |
| expense.km_rate | 0.30 | expense_policy |
| expense.max_hotel_night | 120.00 | expense_policy |
| compliance.vacation_min_days_year | 20 | compliance |
| compliance.vacation_consecutive_required | 10 | compliance |
| notification.email_enabled | true | notification |
| notification.reminder_days | 3 | notification |

---

## 11. Frontend Components

### 11.1 DataTables.net (Server-Side)

Tutte le tabelle dati utilizzano DataTables.net con:
- **Paginazione backend**: Endpoint `/datatable` per ogni entità
- **Filtri backend**: Search su colonne specifiche
- **Sorting backend**: Order by colonna
- **Export**: Excel, PDF, CSV

### 11.2 FullCalendar

Calendari implementati:
- **Personal Calendar**: Vista assenze personali
- **Team Calendar**: Vista team per manager
- **Date Picker**: Selezione date per nuova richiesta

---

## 12. API Gateway (Nginx + ModSecurity)

### Funzionalità

| Feature | Descrizione |
|---------|-------------|
| Reverse Proxy | Routing verso microservizi interni |
| WAF | ModSecurity con OWASP Core Rule Set |
| Rate Limiting | 100r/s API, 10r/s Auth |
| SSL Termination | HTTPS → HTTP interno |
| Logging | JSON format per correlazione audit |
| Security Headers | X-Request-ID, CSP, XSS Protection |

### Protezioni WAF

- SQL Injection
- XSS (Cross-Site Scripting)
- LFI/RFI (File Inclusion)
- Command Injection
- Scanner Detection

---

## 13. Roadmap Implementazione

| Fase | Modulo | Priorità |
|------|--------|----------|
| 1 | Docker Compose + Networking | Alta |
| 2 | Keycloak realm + client setup | Alta |
| 3 | auth-service (user sync) | Alta |
| 4 | config-service (system_config) | Alta |
| 5 | Database migrations (tutti gli schema) | Alta |
| 6 | leave-service (core business) | Alta |
| 7 | notification-service (Brevo) | Alta |
| 8 | audit-service | Media |
| 9 | expense-service | Media |
| 10 | Frontend base (React + Keycloak) | Media |
| 11 | Frontend DataTables + Calendar | Media |
| 12 | Nginx + ModSecurity | Media |
| 13 | Report service | Bassa |
| 14 | Integrazioni (export paghe) | Bassa |

---

## 14. Documentazione Tecnica

Documentazione dettagliata per sviluppatori e agenti AI disponibile in `/docs/`:

| File | Contenuto |
|------|-----------|
| architecture.md | Architettura, networking, database isolation |
| tech-stack.md | Stack tecnologico con versioni e librerie |
| setup.md | Docker Compose, setup ambiente dev |
| database/schema.md | DDL completo tutte le tabelle |
| modules/auth.md | Keycloak SSO, LDAP, MFA |
| modules/leaves.md | Modulo assenze con workflow |
| modules/expenses.md | Trasferte e rimborsi |
| modules/config.md | Configurazione dinamica |
| modules/notifications.md | Email Brevo e in-app |
| business/leave-policies.md | Policy engine |
| business/compliance-italy.md | Normativa italiana |
| development/coding-standards.md | Best practices Python/FastAPI |
