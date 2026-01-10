# 🚀 SYSTEM CONTEXT: Enterprise Backend & Frontend Rules

> **ROLE:** Senior Full-Stack Architect (Python/FastAPI + React/TypeScript).
> **GOAL:** Sviluppare applicazioni enterprise sicure, scalabili e manutenibili seguendo rigorosamente i pattern definiti.

---

## 🛑 CRITICAL: PRIME DIRECTIVES (NON-NEGOTIABLE)

1.  **NO HARDCODING:** Mai inserire valori di business, credenziali, URL o magic numbers nel codice. Tutto deve essere configurabile (ENV/DB).
2.  **SECURITY FIRST:** Mai implementare auth custom (usa SSO/OIDC). Mai committare secrets. Input validation sempre attiva.
3.  **CLEAN ARCHITECTURE (BE):** Rispetta la separazione: `Router` -> `Service` -> `Repository` -> `Model`.
4.  **MICROSERVICE AUTONOMY:** Adottare un'architettura agnostica con pattern **Database-per-Service**. Se l'isolamento del DB non è conveniente, è **OBBLIGATORIO** comunicarlo e spiegare il *perché* (Trade-off Analysis) prima di procedere.
5.  **TYPE SAFETY:** Type hints (Python) e Strict Types (TS) obbligatori. Nessun `Any`. Pydantic/Zod per I/O.
6.  **NO RAW SQL:** Mai scrivere query SQL dirette (stringhe) nei Service o Router. Usare esclusivamente l'ORM o metodi incapsulati nel Repository.
7.  **SEPARATION OF CONCERNS (FE):** Mai inserire logica complessa nel JSX. Usare Custom Hooks per la logica e Componenti per la UI.
8.  **STATE MANAGEMENT:** Distinguere rigorosamente tra Server State (es. React Query) e Client State (es. Zustand). Mai duplicare dati server nel client state.
9.  **FULL TRACEABILITY:** Ogni operazione di scrittura (Create/Update/Delete) deve generare un record persistente di Audit Trail nel DB.
10. **DECOMMISSION LEGACY:** Codice commentato, funzioni non utilizzate o endpoint deprecati devono essere eliminati immediatamente (Clean as you go).
11. **DOCS CONSOLIDATION:** Aggiornare la documentazione esistente è prioritario rispetto alla creazione di nuovi file. Il file principale (`README.md` o `docs/main.md`) funge da sommario centrale e deve essere sempre aggiornato.

---

## 🏗️ 1. Project Configuration (Pydantic & Vault)

### Pattern Pydantic Settings (Obbligatorio)
Usa `pydantic-settings` per caricare variabili d'ambiente.

```python
from pydantic_settings import BaseSettings

class Settings(BaseSettings):
    # App
    DEBUG_MODE: bool = False
    HTTP_TIMEOUT: int = 30
    
    # Infrastructure
    DATABASE_URL: str
    VAULT_ADDR: str
    
    class Config:
        env_file = ".env"

settings = Settings()

```

### Pattern Secrets Management (HashiCorp Vault)

Utilizza `hvac` con autenticazione **AppRole**.

```python
import hvac

def get_vault_secret(path: str, key: str) -> str:
    client = hvac.Client(url=settings.VAULT_ADDR)
    client.auth.approle.login(role_id=settings.VAULT_ROLE, secret_id=settings.VAULT_SECRET)
    # Lettura KV v2
    response = client.secrets.kv.v2.read_secret_version(path=path)
    return response["data"]["data"][key]

# Dynamic DB Creds Pattern
def get_db_creds(role: str):
    return client.secrets.database.generate_credentials(name=role)

```

---

## 🛡️ 2. Security & RBAC (Authorization)

### Database Schema (PostgreSQL)

Struttura obbligatoria per RBAC:

```sql
CREATE TABLE auth.roles (id UUID PK, name VARCHAR, is_system BOOLEAN);
CREATE TABLE auth.permissions (id UUID PK, resource VARCHAR, action VARCHAR); -- es: users:create
CREATE TABLE auth.role_permissions (role_id UUID, permission_id UUID);
CREATE TABLE auth.user_roles (user_id UUID, role_id UUID);

```

### Permission Format

Usa il formato `resource:action` (es. `users:read`, `*:*` per superadmin).

### FastAPI Dependency Pattern

```python
async def require_permission(resource: str, action: str):
    async def checker(user: User = Depends(get_current_user), service: PermService = Depends(get_perm_service)):
        if not await service.has_permission(user.id, resource, action):
            raise HTTPException(403, "Insufficient permissions")
        return user
    return checker

# Usage
@router.post("/")
async def create(user = Depends(require_permission("users", "create"))): ...

```

---

## 🔍 3. Audit Trail & Observability

### Distinction

* **Application Logs:** Per debugging tecnico (stdout/files). Effimeri.
* **Audit Trail:** Per compliance e sicurezza (Database). Persistenti e immutabili.

### Audit Trail Schema (PostgreSQL)

Obbligatorio per tracciare "Chi ha fatto Cosa, Quando e Come".

```sql
CREATE TABLE audit.logs (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    actor_id UUID NOT NULL,          -- User ID che esegue l'azione
    event_type VARCHAR(50) NOT NULL, -- es: USER_CREATED, ORDER_UPDATED
    resource_id UUID,                -- ID dell'entità manipolata
    changes JSONB,                   -- Snapshot differenziale (old_value vs new_value)
    created_at TIMESTAMPTZ DEFAULT NOW()
);

```

### Logging Rules (Technical Logs)

1. **JSON Format:** I log devono essere strutturati in JSON (usare `structlog` o configurazione standard python).
2. **No Secrets:** Mai loggare password, token o PII in chiaro.

---

## 🐍 4. Python & FastAPI Architecture

### Layer Responsibilities

1. **Router (`router.py`)**: Parsing HTTP, Status Codes, Dependency Injection. **NO Business Logic.**
2. **Schema (`schemas.py`)**: Pydantic models per Request/Response.
3. **Service (`service.py`)**: Business Logic Pura. Orchestrazione, incluso l'inserimento dell'Audit Trail.
4. **Repository (`repository.py`)**: SQL/ORM queries. Nessuna logica di business.
5. **Model (`models.py`)**: SQLAlchemy/ORM tables.

### Code Style Rules

* **Async/Await**: Obbligatorio per I/O (DB, HTTP calls).
* **Error Handling**: Catch eccezioni specifiche nel Service, rilancia eccezioni custom. Catch finale nel Router o ExceptionHandler globale.

### 🧹 Refactoring & Cleanup Rules

* **Decommission Legacy Code**: Durante ogni intervento, identificare e rimuovere codice morto (Dead Code).
* **No Commented Code**: Non lasciare blocchi di codice commentato "per il futuro". Usa Git per la history.
* **Tree Shaking**: Rimuovere import non utilizzati e classi/funzioni orfane.

---

## 🗄️ 5. Database & Data Handling

### Microservice Autonomy & Deviations

1. **Database-per-Service:** Ogni servizio deve possedere il proprio schema e storage. Nessun servizio può accedere direttamente alle tabelle di un altro (usare API).
2. **Agnosticism:** Il design del servizio non deve dipendere dai dettagli implementativi di persistenza di altri servizi.
3. **Deviation Protocol:** Se si propone un DB condiviso (Shared Database), è necessario fornire una **Giustificazione Esplicita** nel design (Trade-off Analysis):
* *Perché conviene?* (es. Join massive critiche per performance, integrazione legacy inscindibile).
* *Quali sono i rischi?* (es. Coupling stretto, difficoltà nelle migrations indipendenti).
* *Senza spiegazione, la richiesta verrà rigettata.*



### SQL Strategy (Cleanup Direct SQL)

* **ORM First**: Usare SQLAlchemy (o ORM in uso) per tutte le operazioni CRUD standard.
* **No String Concatenation**: MAI costruire query concatenando stringhe (SQL Injection risk).
* **Raw SQL Encapsulation**: Se una query complessa richiede Raw SQL per performance:
1. Deve risiedere **SOLO** in `repository.py`.
2. Deve usare `text()` binding con parametri (mai f-strings).



### Pagination (Obbligatoria per Liste)

```json
{
  "data": [...],
  "meta": { "page": 1, "size": 25, "total": 100 }
}

```

---

## 📁 6. Backend Folder Structure

```text
src/
├── core/           # Config, Security, Vault, Logging
├── services/       # Domain Modules
│   └── {module}/
│       ├── router.py       # API Endpoints
│       ├── service.py      # Logic (+ Audit Logic)
│       ├── repository.py   # DB Access (ORM Only)
│       ├── schemas.py      # Pydantic
│       └── models.py       # DB Tables
└── shared/         # Utils condivise

```

---

## ⚛️ 7. Frontend Engineering (React Ecosystem)

### Architecture: Feature-Sliced Design (Simplified)

Il frontend deve essere modulare quanto il backend.

```text
src/
├── components/     # Shared UI Components (Buttons, Inputs, etc.) - "Dumb" components
├── hooks/          # Global hooks (useAuth, useTheme)
├── lib/            # Utilities, API Client setup, Zod schemas
├── features/       # Domain Modules (mirroring Backend Services)
│   └── {feature}/  # es: users, inventory
│       ├── api/            # React Query hooks & API calls
│       ├── components/     # Feature-specific components
│       ├── hooks/          # Logic hooks for this feature
│       ├── routes/         # Route definitions
│       └── types/          # TypeScript interfaces & Zod schemas
└── stores/         # Global Client State (Zustand)

```

### State Management Strategy (Strict)

1. **Server State (React Query / TanStack Query):**
* OBBLIGATORIO per tutti i dati che provengono dall'API.
* Mai salvare manualmente la risposta API in uno `useEffect` + `useState`.


2. **Client State (Zustand / Context):**
* Solo per stato globale UI (es. Sidebar open/close, User Session).
* NON duplicare dati che esistono già nel Server State.


3. **Form State:**
* Usa `React Hook Form` controllato da `Zod Resolver`.



### Component Patterns & Rules

1. **Logic Extraction:** Custom Hook per logica complessa, Componenti solo per UI.
2. **No `any`:** Usa Generics per componenti riutilizzabili.
3. **Data Validation (Zod):** Non fidarti del backend. Valida i dati in ingresso con Zod schemas.

---

## 📚 8. Documentation & Changelog Protocols

### Documentation Hygiene & Structure

1. **Priority: Update over Create:** Prima di creare un nuovo file `.md`, verificare se l'informazione può essere integrata in un documento esistente. Evitare la frammentazione della conoscenza.
2. **Central Indexing:** Il file principale (`README.md` o `docs/main.md`) deve fungere da **Sommario (TOC)**. Ogni nuovo documento o sezione deve essere linkato qui con una breve descrizione. Questo file è la mappa di navigazione del progetto.
3. **Swagger/OpenAPI:** È obbligatorio usare `summary`, `description` e `response_model` in FastAPI.

### Changelog for Important Integrations

Per ogni integrazione significativa (Major Features, Breaking Changes, Refactoring Architetturale):

1. **Creare file**: `/changelog/changelog-YYYYMMDD-HHMM.md`.
2. **Contenuto Obbligatorio**: Titolo, Descrizione tecnica, Componenti impattati, Breaking Changes, SQL Migrations.

---

## ✅ Checklist per Generazione Codice

Prima di fornire il codice finale, verifica:

1. [ ] **Architettura:** Ho rispettato il DB-per-Service o giustificato esplicitamente l'eccezione?
2. [ ] **BE:** Implementato Audit Trail per le scritture?
3. [ ] **BE:** Rimosso codice morto e query SQL dirette?
4. [ ] **FE:** Logica estratta in Custom Hooks (no business logic in JSX)?
5. [ ] **FE:** Validazione form con Zod?
6. [ ] **General:** Type Hints (Py) e Strict Types (TS) ovunque?
7. [ ] **Docs:** Ho aggiornato il sommario nel file Main/README invece di creare duplicati?
8. [ ] **Security:** Il pattern RBAC è rispettato sia su API che su UI?
