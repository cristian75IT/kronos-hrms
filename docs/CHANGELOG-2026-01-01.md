# KRONOS HRMS - Changelog 2026-01-01

## Sessione di Sviluppo: Armonizzazione Identity e Bug Fixes

Data: 1 Gennaio 2026

---

## 🔐 Architettura Identity (MAJOR)

### Problema Risolto
L'applicazione utilizzava due identificatori diversi per lo stesso utente:
- `id` (UUID interno del database)
- `keycloak_id` (UUID di Keycloak nel token JWT)

Questo causava discrepanze tra i dati di diversi moduli (es. richieste ferie create con keycloak_id ma saldi associati all'id interno).

### Soluzione Implementata
Introdotto un pattern enterprise-grade per la risoluzione dell'identità:

```
JWT Token (Keycloak)           Auth Service Lookup         Business Logic
┌─────────────────┐            ┌──────────────────┐        ┌─────────────────┐
│ sub: keycloak_id│ ────────►  │ keycloak_id →    │ ───►   │ user_id:        │
│ (external)      │            │ internal_id      │        │ internal_id     │
└─────────────────┘            │ (DB lookup)      │        │ (consistent)    │
                               └──────────────────┘        └─────────────────┘
```

### File Modificati
- `backend/src/core/security.py`:
  - `TokenPayload` ora include `internal_user_id` e la property `user_id`
  - Nuova dependency `get_current_user` che risolve l'ID via auth service
  
- `backend/src/services/auth/router.py`:
  - Nuovo endpoint `GET /users/by-keycloak/{keycloak_id}` per lookup interno
  
- `backend/src/services/auth/repository.py`:
  - `get_by_keycloak_id()` ora usa eager loading per evitare MissingGreenlet
  
- `backend/src/services/leaves/router.py`:
  - Tutti gli endpoint ora usano `get_current_user` invece di `get_current_token`
  - Sostituito `UUID(token.keycloak_id)` con `token.user_id` ovunque

---

## 📅 Fix Calendario

### Visualizzazione Festività Cross-Anno
**Problema**: Le festività venivano mostrate solo per l'anno di inizio della vista, non per l'intero range.

**Soluzione**: 
- `backend/src/services/leaves/service.py`: Modificato `get_calendar_events` per iterare su tutti gli anni nell'intervallo e deduplicare i risultati.

### Leggibilità Eventi
**Problema**: Il testo delle festività e chiusure era bianco su sfondo chiaro, illeggibile.

**Soluzione**:
- `frontend/src/pages/CalendarPage.tsx`: Corretto uso di `classNames` invece di `className`
- `frontend/src/index.css`: Sostituiti colori hardcoded con CSS variables per supporto dark mode

---

## 💰 Fix Saldi (Balances)

### Adjustment Non Riflessi
**Problema**: Gli adjustment manuali aggiornavano `vacation_current_year` ma la UI usava `vacation_accrued`.

**Soluzione**: 
- `backend/src/services/leaves/service.py`: Modificato `field_map` in `adjust_balance`:
  - `vacation_ac` ora aggiorna `vacation_accrued` (non `vacation_current_year`)
  - `rol` ora aggiorna `rol_accrued` (non `rol_current_year`)

### Colonna DB Mancante
**Problema**: `column balance_transactions.reason does not exist`

**Soluzione**:
- Creata migrazione `017_fix_balance_tx_reason.py`:
  - Rinomina colonna `description` → `reason`
  - Aggiorna precisione `amount` da `Numeric(5,2)` a `Numeric(6,2)`

### Import Mancante
**Problema**: `NameError: name 'BalanceTransaction' is not defined`

**Soluzione**:
- `backend/src/services/leaves/service.py`: Aggiunto import di `BalanceTransaction`

---

## 👥 Pagina Approvazioni

### Nome Richiedente
**Problema**: Veniva mostrato l'UUID troncato invece del nome.

**Soluzione**:
- `backend/src/services/leaves/schemas.py`: Aggiunto campo `user_name` a `LeaveRequestListItem`
- `backend/src/services/leaves/router.py`: Endpoint `get_pending_approval` ora arricchisce le richieste con `user_name`
- `frontend/src/pages/ApprovalsPage.tsx`: Mostra `user_name` invece di `user_id`
- `frontend/src/types/index.ts`: Aggiunto `user_name` a `LeaveRequest` interface

---

## 🐛 Bug Fixes Vari

### MissingGreenlet Errors
- `backend/src/services/leaves/repository.py`: Aggiunto `refresh()` dopo `flush()` in create/update
- `backend/src/services/auth/repository.py`: Eager loading in `get_by_keycloak_id()`
- `backend/src/services/leaves/service.py`: Fix accesso a `user_info.get("profile")` quando è None

### NoneType Errors
- `backend/src/services/leaves/service.py` (linea ~1057): Fix per profilo utente nullo nel calcolo saldi

---

## 📝 Schema Changes

### Database
```sql
-- Migration 017
ALTER TABLE leaves.balance_transactions 
  RENAME COLUMN description TO reason;

ALTER TABLE leaves.balance_transactions 
  ALTER COLUMN amount TYPE NUMERIC(6,2);
```

### API Response Types
- `LeaveRequestListItem` ora include `user_name: Optional[str]`
- `LeaveRequest` (frontend) include `user_name?: string`

---

## ⚠️ Breaking Changes

1. **Endpoint Deprecati**: Gli endpoint che usavano direttamente `keycloak_id` come user identifier ora richiedono la risoluzione tramite auth service.

2. **Nuova Dependency**: I microservizi che richiedono l'ID utente interno devono ora comunicare con l'auth service via `GET /users/by-keycloak/{keycloak_id}`.

---

## 🧪 Testing Consigliato

1. **Login e navigazione**: Verificare che tutte le pagine carichino correttamente
2. **Creazione richieste ferie**: Verificare che usino l'ID interno corretto
3. **Approvazioni**: Verificare che il nome del richiedente sia visibile
4. **Saldi wallet**: Verificare che gli adjustment siano riflessi
5. **Calendario**: Verificare festività per tutto l'anno

---

## 📋 TODO Futuri

1. **Audit Log**: Integrare invio eventi audit dai servizi principali
2. **Caching Identity**: Valutare cache per ridurre chiamate auth service
3. **Test E2E**: Aggiungere test per workflow completo ferie
