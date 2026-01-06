# Architettura Sistema - KRONOS HRMS

## Overview

**KRONOS** è un sistema HRMS enterprise basato su architettura a **microservizi** con:
- **Nginx + ModSecurity** come API Gateway/WAF
- **Database isolation** tramite PostgreSQL schemas
- **SSO esterno** (Keycloak) per simulare ambiente produzione
- **Audit completo** (Log + Trail) su tutte le operazioni
- **Identity Resolution** centralizzata per consistenza cross-service

---

## 🔐 Identity Resolution Architecture

### Problema
I sistemi con SSO esterno hanno due identificatori per ogni utente:
- **External ID** (Keycloak `sub`): UUID nel token JWT
- **Internal ID** (Database `id`): UUID nel database locale

### Soluzione Enterprise
La risoluzione avviene **una sola volta** per request, nel security layer:

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                         REQUEST FLOW                                         │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                              │
│  JWT Token                  get_current_user()              Business Logic   │
│  ┌───────────────┐          ┌──────────────────┐          ┌────────────────┐│
│  │ sub: e393d52a │ ───────► │ Auth Service     │ ───────► │ token.user_id  ││
│  │ (keycloak_id) │          │ GET /by-keycloak │          │ = 6d50491b     ││
│  └───────────────┘          │ {keycloak_id}    │          │ (internal)     ││
│                             └──────────────────┘          └────────────────┘│
│                                      │                                       │
│                                      ▼                                       │
│                             ┌──────────────────┐                            │
│                             │ TokenPayload     │                            │
│                             │ .internal_user_id│                            │
│                             │ .user_id (prop)  │                            │
│                             └──────────────────┘                            │
└─────────────────────────────────────────────────────────────────────────────┘
```

### Implementazione

**1. TokenPayload esteso** (`src/core/security.py`):
```python
class TokenPayload(BaseModel):
    sub: str  # Keycloak ID (external)
    internal_user_id: Optional[UUID] = None  # Resolved internal ID
    
    @property
    def user_id(self) -> UUID:
        """Use this for all database operations."""
        if self.internal_user_id is None:
            raise ValueError("Use get_current_user dependency")
        return self.internal_user_id
```

**2. Dependency get_current_user**:
```python
async def get_current_user(token: str = Depends(oauth2_scheme)) -> TokenPayload:
    payload = await decode_token(token)
    
    # Resolve keycloak_id → internal_id via auth service
    response = await httpx.get(
        f"{AUTH_SERVICE_URL}/api/v1/users/by-keycloak/{payload.keycloak_id}"
    )
    payload.internal_user_id = UUID(response.json()["id"])
    
    return payload
```

**3. Uso nei router**:
```python
# ✅ CORRETTO: usa get_current_user
@router.get("/leaves")
async def get_leaves(token: TokenPayload = Depends(get_current_user)):
    user_id = token.user_id  # ID interno, consistente

# ❌ ERRATO: usa keycloak_id direttamente  
user_id = UUID(token.keycloak_id)  # Mai fare questo!
```

### Endpoint Auth Service

```
GET /api/v1/users/by-keycloak/{keycloak_id}
```
Restituisce l'utente con tutte le relazioni (profile, location, etc.) date un keycloak_id.

---

## Nome Stack: KRONOS

> Κρόνος (Kronos) - Dio greco del tempo. Appropriato per un sistema di gestione presenze e assenze.

---

## 🏗 Microservice Internal Architecture

All KRONOS microservices strictly follow the **Enterprise Repository Pattern** with a 3-layer separation of concerns:

### 1. Layers & Responsibilities

| Layer | File(s) | Responsibility | Constraints |
|-------|---------|----------------|-------------|
| **Router** | `router.py`, `routers/*.py` | HTTP Endpoints, validation, dependency injection | **NO** business logic, **NO** direct DB queries |
| **Service** | `service.py`, `services/*.py` | Business logic, coordination between repos | **NO** direct SQL, **NO** HTTP logic |
| **Repository** | `repository.py` | Data access, CRUD, SQL queries | **ONLY** place for `.execute()`, `select()` |

### 2. Request Flow
```
Client ──► Router (FastAPI) ──► Service (Logic) ──► Repository (SQL) ──► Database
```

### 3. Standards & Best Practices
- **Zero Hardcoding**: Configuration resides in `.env` or database.
- **Type Safety**: Mandatory Pydantic models for I/O and type hints on all methods.
- **Audit Logging**: Operations are logged via `src.shared.audit_client`.
- **Inter-service Communication**: Done via specialized clients in `src.shared.clients`.

---

## 🌐 Network Architecture

---

## Nginx + ModSecurity Configuration

### Ruolo del Gateway

| Funzione | Descrizione |
|----------|-------------|
| **Reverse Proxy** | Routing verso microservizi interni |
| **SSL Termination** | HTTPS → HTTP interno |
| **Rate Limiting** | Protezione da DDoS |
| **WAF** | ModSecurity con OWASP CRS |
| **CORS** | Gestione cross-origin |
| **Logging** | Access log + Audit log |
| **Health Checks** | Monitoring servizi |

### ModSecurity Rules (OWASP CRS)

| Protezione | Descrizione |
|------------|-------------|
| SQL Injection | Blocca query malevole |
| XSS | Cross-Site Scripting |
| LFI/RFI | Local/Remote File Inclusion |
| Command Injection | Blocca comandi shell |
| Scanner Detection | Blocca tool automatici |

---

## Audit System (Completo)

### Audit Log vs Audit Trail

| Tipo | Scopo | Contenuto |
|------|-------|-----------|
| **Audit Log** | Chi ha fatto cosa quando | user_id, action, entity, timestamp, IP |
| **Audit Trail** | Storia completa modifiche | old_values, new_values, diff |

### Schema audit.audit_logs

```sql
CREATE TABLE audit.audit_logs (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    
    -- Chi
    user_id UUID,
    user_email VARCHAR(255),
    user_role VARCHAR(50),
    
    -- Cosa
    action VARCHAR(50) NOT NULL,          -- 'create', 'read', 'update', 'delete', 'login', 'logout', 'approve', 'reject'
    entity_type VARCHAR(100) NOT NULL,    -- 'leave_request', 'expense_report', 'user', 'config'
    entity_id UUID,
    entity_name VARCHAR(255),             -- Human-readable (es. "Ferie Mario Rossi 01-15 Gen")
    
    -- Dettagli
    description TEXT,                      -- Descrizione leggibile dell'azione
    old_values JSONB,                      -- Valori prima della modifica
    new_values JSONB,                      -- Valori dopo la modifica
    changes JSONB,                         -- Solo i campi modificati
    
    -- Contesto
    service_name VARCHAR(50),              -- 'auth-service', 'leave-service', etc.
    endpoint VARCHAR(255),                 -- '/api/v1/leaves/123'
    http_method VARCHAR(10),               -- 'POST', 'PUT', 'DELETE'
    request_id UUID,                       -- Correlation ID
    
    -- Client info
    ip_address INET,
    user_agent TEXT,
    session_id VARCHAR(255),
    
    -- Timing
    created_at TIMESTAMPTZ DEFAULT NOW(),
    
    -- Risultato
    status VARCHAR(20) DEFAULT 'success', -- 'success', 'failure', 'error'
    error_message TEXT
);

-- Indici per query frequenti
CREATE INDEX idx_audit_user ON audit.audit_logs(user_id);
CREATE INDEX idx_audit_entity ON audit.audit_logs(entity_type, entity_id);
CREATE INDEX idx_audit_action ON audit.audit_logs(action);
CREATE INDEX idx_audit_created ON audit.audit_logs(created_at);
CREATE INDEX idx_audit_service ON audit.audit_logs(service_name);

-- Partitioning per performance (mensile)
-- CREATE TABLE audit.audit_logs_2024_01 PARTITION OF audit.audit_logs
--     FOR VALUES FROM ('2024-01-01') TO ('2024-02-01');
```

### Schema audit.audit_trail (Entity History)

```sql
CREATE TABLE audit.audit_trail (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    
    -- Entità tracciata
    entity_type VARCHAR(100) NOT NULL,
    entity_id UUID NOT NULL,
    
    -- Versione
    version INTEGER NOT NULL,              -- Numero versione incrementale
    
    -- Snapshot completo
    snapshot JSONB NOT NULL,               -- Stato completo dell'entità
    
    -- Chi e quando
    modified_by UUID,
    modified_at TIMESTAMPTZ DEFAULT NOW(),
    modification_type VARCHAR(20),         -- 'create', 'update', 'delete', 'restore'
    
    -- Link all'audit log
    audit_log_id UUID REFERENCES audit.audit_logs(id)
);

CREATE INDEX idx_trail_entity ON audit.audit_trail(entity_type, entity_id);
CREATE INDEX idx_trail_version ON audit.audit_trail(entity_type, entity_id, version);
CREATE UNIQUE INDEX idx_trail_unique_version ON audit.audit_trail(entity_type, entity_id, version);
```

### Audit Service Implementation

```python
# audit/service.py
from datetime import datetime
from typing import Any, Optional
from uuid import UUID

from sqlalchemy.ext.asyncio import AsyncSession

class AuditService:
    """Complete audit logging and trail service."""

    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def log(
        self,
        *,
        user_id: Optional[UUID],
        user_email: Optional[str],
        user_role: Optional[str],
        action: str,
        entity_type: str,
        entity_id: Optional[UUID] = None,
        entity_name: Optional[str] = None,
        description: Optional[str] = None,
        old_values: Optional[dict] = None,
        new_values: Optional[dict] = None,
        service_name: str,
        endpoint: Optional[str] = None,
        http_method: Optional[str] = None,
        request_id: Optional[UUID] = None,
        ip_address: Optional[str] = None,
        user_agent: Optional[str] = None,
        status: str = "success",
        error_message: Optional[str] = None,
    ) -> UUID:
        """Create audit log entry."""
        
        # Calculate changes diff
        changes = None
        if old_values and new_values:
            changes = self._calculate_diff(old_values, new_values)
        
        log_entry = AuditLogModel(
            user_id=user_id,
            user_email=user_email,
            user_role=user_role,
            action=action,
            entity_type=entity_type,
            entity_id=entity_id,
            entity_name=entity_name,
            description=description,
            old_values=old_values,
            new_values=new_values,
            changes=changes,
            service_name=service_name,
            endpoint=endpoint,
            http_method=http_method,
            request_id=request_id,
            ip_address=ip_address,
            user_agent=user_agent,
            status=status,
            error_message=error_message,
        )
        
        self._session.add(log_entry)
        await self._session.flush()
        
        # If entity modified, create trail entry
        if entity_id and action in ("create", "update", "delete") and new_values:
            await self._create_trail(
                entity_type=entity_type,
                entity_id=entity_id,
                snapshot=new_values,
                modified_by=user_id,
                modification_type=action,
                audit_log_id=log_entry.id,
            )
        
        return log_entry.id

    async def _create_trail(
        self,
        entity_type: str,
        entity_id: UUID,
        snapshot: dict,
        modified_by: Optional[UUID],
        modification_type: str,
        audit_log_id: UUID,
    ) -> None:
        """Create audit trail entry with version."""
        
        # Get next version number
        result = await self._session.execute(
            select(func.max(AuditTrailModel.version))
            .where(AuditTrailModel.entity_type == entity_type)
            .where(AuditTrailModel.entity_id == entity_id)
        )
        max_version = result.scalar() or 0
        
        trail_entry = AuditTrailModel(
            entity_type=entity_type,
            entity_id=entity_id,
            version=max_version + 1,
            snapshot=snapshot,
            modified_by=modified_by,
            modification_type=modification_type,
            audit_log_id=audit_log_id,
        )
        
        self._session.add(trail_entry)

    def _calculate_diff(self, old: dict, new: dict) -> dict:
        """Calculate difference between old and new values."""
        changes = {}
        all_keys = set(old.keys()) | set(new.keys())
        
        for key in all_keys:
            old_val = old.get(key)
            new_val = new.get(key)
            if old_val != new_val:
                changes[key] = {"old": old_val, "new": new_val}
        
        return changes

    async def get_entity_history(
        self,
        entity_type: str,
        entity_id: UUID,
    ) -> list[dict]:
        """Get complete history of an entity."""
        result = await self._session.execute(
            select(AuditTrailModel)
            .where(AuditTrailModel.entity_type == entity_type)
            .where(AuditTrailModel.entity_id == entity_id)
            .order_by(AuditTrailModel.version.desc())
        )
        return result.scalars().all()
```

### Audit Decorator

```python
# shared/decorators.py
from functools import wraps

def audited(action: str, entity_type: str):
    """Decorator for automatic audit logging."""
    def decorator(func):
        @wraps(func)
        async def wrapper(*args, **kwargs):
            # Get context from request
            request = kwargs.get("request")
            current_user = kwargs.get("current_user")
            audit_service = kwargs.get("audit_service")
            
            # Get old values for update operations
            old_values = None
            if action == "update":
                entity_id = kwargs.get("id") or args[1] if len(args) > 1 else None
                if entity_id:
                    old_values = await get_entity_snapshot(entity_type, entity_id)
            
            try:
                result = await func(*args, **kwargs)
                
                # Log success
                await audit_service.log(
                    user_id=current_user.id if current_user else None,
                    user_email=current_user.email if current_user else None,
                    user_role=current_user.role if current_user else None,
                    action=action,
                    entity_type=entity_type,
                    entity_id=getattr(result, "id", None),
                    old_values=old_values,
                    new_values=result.model_dump() if hasattr(result, "model_dump") else None,
                    service_name=settings.SERVICE_NAME,
                    endpoint=str(request.url.path) if request else None,
                    http_method=request.method if request else None,
                    ip_address=request.client.host if request else None,
                    status="success",
                )
                
                return result
                
            except Exception as e:
                # Log failure
                await audit_service.log(
                    user_id=current_user.id if current_user else None,
                    action=action,
                    entity_type=entity_type,
                    service_name=settings.SERVICE_NAME,
                    status="error",
                    error_message=str(e),
                )
                raise
        
        return wrapper
    return decorator
```

---

## Nginx Configuration

```nginx
# nginx/nginx.conf

# Load ModSecurity
load_module modules/ngx_http_modsecurity_module.so;

events {
    worker_connections 1024;
}

http {
    # ModSecurity
    modsecurity on;
    modsecurity_rules_file /etc/nginx/modsec/main.conf;

    # Logging formato JSON per audit
    log_format json_combined escape=json
        '{'
            '"time":"$time_iso8601",'
            '"remote_addr":"$remote_addr",'
            '"request_id":"$request_id",'
            '"request_method":"$request_method",'
            '"request_uri":"$request_uri",'
            '"status":$status,'
            '"body_bytes_sent":$body_bytes_sent,'
            '"request_time":$request_time,'
            '"http_user_agent":"$http_user_agent",'
            '"http_x_forwarded_for":"$http_x_forwarded_for",'
            '"upstream_response_time":"$upstream_response_time"'
        '}';

    access_log /var/log/nginx/access.json json_combined;
    error_log /var/log/nginx/error.log warn;

    # Rate limiting
    limit_req_zone $binary_remote_addr zone=api_limit:10m rate=100r/s;
    limit_req_zone $binary_remote_addr zone=auth_limit:10m rate=10r/s;

    # Upstream services
    upstream auth_service {
        server auth-service:8001;
    }
    upstream leave_service {
        server leave-service:8002;
    }
    upstream expense_service {
        server expense-service:8003;
    }
    upstream config_service {
        server config-service:8004;
    }

    server {
        listen 80;
        server_name api.kronos.local;

        # Security headers
        add_header X-Request-ID $request_id always;
        add_header X-Content-Type-Options nosniff always;
        add_header X-Frame-Options DENY always;
        add_header X-XSS-Protection "1; mode=block" always;

        # CORS
        add_header Access-Control-Allow-Origin $http_origin always;
        add_header Access-Control-Allow-Methods "GET, POST, PUT, DELETE, OPTIONS" always;
        add_header Access-Control-Allow-Headers "Authorization, Content-Type, X-Request-ID" always;

        # Health check
        location /health {
            access_log off;
            return 200 "OK";
        }

        # Auth endpoints (rate limited)
        location /api/v1/auth {
            limit_req zone=auth_limit burst=20 nodelay;
            proxy_pass http://auth_service;
            include /etc/nginx/proxy_params;
        }

        # Users
        location /api/v1/users {
            limit_req zone=api_limit burst=50 nodelay;
            proxy_pass http://auth_service;
            include /etc/nginx/proxy_params;
        }

        # Leaves
        location /api/v1/leaves {
            limit_req zone=api_limit burst=50 nodelay;
            proxy_pass http://leave_service;
            include /etc/nginx/proxy_params;
        }

        location /api/v1/balances {
            proxy_pass http://leave_service;
            include /etc/nginx/proxy_params;
        }

        # Expenses
        location /api/v1/trips {
            proxy_pass http://expense_service;
            include /etc/nginx/proxy_params;
        }

        location /api/v1/expenses {
            proxy_pass http://expense_service;
            include /etc/nginx/proxy_params;
        }

        # Config
        location /api/v1/config {
            proxy_pass http://config_service;
            include /etc/nginx/proxy_params;
        }

        location /api/v1/leave-types {
            proxy_pass http://config_service;
            include /etc/nginx/proxy_params;
        }

        location /api/v1/holidays {
            proxy_pass http://config_service;
            include /etc/nginx/proxy_params;
        }
    }
}
```

---

## Docker Networks

| Network | Scope | Services |
|---------|-------|----------|
| `kronos-external` | SSO only | Keycloak |
| `kronos-internal` | App stack | Nginx, Services, DB, Redis, MinIO |

**Comunicazione:**
- Frontend → Nginx (public)
- Nginx → Services (internal)
- Services → Keycloak (cross-network per token validation)
