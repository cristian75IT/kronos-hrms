# Setup Ambiente di Sviluppo - KRONOS

## Prerequisiti

- Python 3.11+
- Node.js 18+
- Docker & Docker Compose
- Git

---

## Quick Start

```bash
# 1. Clone repository
git clone <repo-url>
cd kronos

# 2. Avvia infrastruttura Docker
# Questo avvia tutti i servizi, database e frontend
docker-compose up -d

# Nota: Al primo avvio, i servizi backend creeranno automaticamente le tabelle necessarie nel database.
#       Keycloak verrà importato automaticamente con realm e utenti preconfigurati.

# 3. Accesso
# Frontend: http://localhost
# Keycloak: http://localhost:8080/admin (user: admin / pass: admin)
# MinIO:    http://localhost:9001 (user: kronos / pass: kronos_dev)

# 4. Utenti Demo
# Admin:    admin@kronos.local    / admin123
# Manager:  manager@kronos.local  / manager123
# Employee: employee@kronos.local / employee123
```

---

## Docker Compose Completo

```yaml
# docker-compose.yml
version: "3.8"

# ============ NETWORKS ============
networks:
  kronos-internal:
    driver: bridge
    name: kronos-internal
  kronos-external:
    driver: bridge
    name: kronos-external

# ============ VOLUMES ============
volumes:
  postgres_data:
  redis_data:
  minio_data:
  nginx_logs:

services:
  # ═══════════════════════════════════════════════════════════
  # API GATEWAY - NGINX + MODSECURITY (WAF)
  # ═══════════════════════════════════════════════════════════
  nginx:
    image: owasp/modsecurity-crs:nginx-alpine
    container_name: kronos-gateway
    ports:
      - "80:80"
      - "443:443"
    volumes:
      - ./nginx/nginx.conf:/etc/nginx/nginx.conf:ro
      - ./nginx/proxy_params:/etc/nginx/proxy_params:ro
      - ./nginx/modsec:/etc/nginx/modsec:ro
      - nginx_logs:/var/log/nginx
    networks:
      - kronos-internal
    depends_on:
      - auth-service
      - leave-service
      - config-service
    healthcheck:
      test: ["CMD", "curl", "-f", "http://localhost/health"]
      interval: 30s
      timeout: 10s
      retries: 3

  # ═══════════════════════════════════════════════════════════
  # MICROSERVICES
  # ═══════════════════════════════════════════════════════════
  auth-service:
    build:
      context: ./backend
      dockerfile: Dockerfile
    container_name: kronos-auth
    environment:
      - SERVICE_NAME=auth-service
      - DATABASE_URL=postgresql+asyncpg://kronos:kronos_dev@postgres:5432/kronos
      - DATABASE_SCHEMA=auth
      - REDIS_URL=redis://redis:6379/0
      - KEYCLOAK_URL=http://keycloak:8080/
      - KEYCLOAK_REALM=kronos
    command: uvicorn src.services.auth.main:app --host 0.0.0.0 --port 8001
    networks:
      - kronos-internal
    depends_on:
      postgres:
        condition: service_healthy
      redis:
        condition: service_healthy

  leave-service:
    build:
      context: ./backend
      dockerfile: Dockerfile
    container_name: kronos-leaves
    environment:
      - SERVICE_NAME=leave-service
      - DATABASE_URL=postgresql+asyncpg://kronos:kronos_dev@postgres:5432/kronos
      - DATABASE_SCHEMA=leaves
      - REDIS_URL=redis://redis:6379/1
      - CONFIG_SERVICE_URL=http://config-service:8004
    command: uvicorn src.services.leaves.main:app --host 0.0.0.0 --port 8002
    networks:
      - kronos-internal
    depends_on:
      - postgres
      - redis
      - config-service

  expense-service:
    build:
      context: ./backend
      dockerfile: Dockerfile
    container_name: kronos-expenses
    environment:
      - SERVICE_NAME=expense-service
      - DATABASE_URL=postgresql+asyncpg://kronos:kronos_dev@postgres:5432/kronos
      - DATABASE_SCHEMA=expenses
      - REDIS_URL=redis://redis:6379/2
      - MINIO_ENDPOINT=minio:9000
    command: uvicorn src.services.expenses.main:app --host 0.0.0.0 --port 8003
    networks:
      - kronos-internal
    depends_on:
      - postgres
      - minio

  config-service:
    build:
      context: ./backend
      dockerfile: Dockerfile
    container_name: kronos-config
    environment:
      - SERVICE_NAME=config-service
      - DATABASE_URL=postgresql+asyncpg://kronos:kronos_dev@postgres:5432/kronos
      - DATABASE_SCHEMA=config
      - REDIS_URL=redis://redis:6379/3
    command: uvicorn src.services.config.main:app --host 0.0.0.0 --port 8004
    networks:
      - kronos-internal
    depends_on:
      - postgres
      - redis

  notification-service:
    build:
      context: ./backend
      dockerfile: Dockerfile
    container_name: kronos-notifications
    environment:
      - SERVICE_NAME=notification-service
      - DATABASE_URL=postgresql+asyncpg://kronos:kronos_dev@postgres:5432/kronos
      - DATABASE_SCHEMA=notifications
      - REDIS_URL=redis://redis:6379/4
    command: uvicorn src.services.notifications.main:app --host 0.0.0.0 --port 8005
    networks:
      - kronos-internal
    depends_on:
      - postgres
      - redis

  audit-service:
    build:
      context: ./backend
      dockerfile: Dockerfile
    container_name: kronos-audit
    environment:
      - SERVICE_NAME=audit-service
      - DATABASE_URL=postgresql+asyncpg://kronos:kronos_dev@postgres:5432/kronos
      - DATABASE_SCHEMA=audit
      - REDIS_URL=redis://redis:6379/5
    command: uvicorn src.services.audit.main:app --host 0.0.0.0 --port 8007
    networks:
      - kronos-internal
    depends_on:
      - postgres

  # ═══════════════════════════════════════════════════════════
  # DATA LAYER
  # ═══════════════════════════════════════════════════════════
  postgres:
    image: postgres:15
    container_name: kronos-db
    environment:
      POSTGRES_USER: kronos
      POSTGRES_PASSWORD: kronos_dev
      POSTGRES_DB: kronos
    ports:
      - "5432:5432"
    volumes:
      - postgres_data:/var/lib/postgresql/data
      - ./scripts/init-schemas.sql:/docker-entrypoint-initdb.d/01-schemas.sql
    networks:
      - kronos-internal
    healthcheck:
      test: ["CMD-SHELL", "pg_isready -U kronos"]
      interval: 5s
      timeout: 5s
      retries: 5

  redis:
    image: redis:7-alpine
    container_name: kronos-redis
    ports:
      - "6379:6379"
    volumes:
      - redis_data:/data
    networks:
      - kronos-internal
    healthcheck:
      test: ["CMD", "redis-cli", "ping"]
      interval: 5s
      timeout: 5s
      retries: 5

  minio:
    image: minio/minio
    container_name: kronos-storage
    command: server /data --console-address ":9001"
    environment:
      MINIO_ROOT_USER: kronos
      MINIO_ROOT_PASSWORD: kronos_dev
    ports:
      - "9000:9000"
      - "9001:9001"
    volumes:
      - minio_data:/data
    networks:
      - kronos-internal

  # ═══════════════════════════════════════════════════════════
  # SSO - KEYCLOAK (RETE ESTERNA)
  # ═══════════════════════════════════════════════════════════
  keycloak:
    image: quay.io/keycloak/keycloak:23.0
    container_name: kronos-sso
    command: start-dev --import-realm
    environment:
      KEYCLOAK_ADMIN: admin
      KEYCLOAK_ADMIN_PASSWORD: admin
      KC_DB: postgres
      KC_DB_URL: jdbc:postgresql://keycloak-db:5432/keycloak
      KC_DB_USERNAME: keycloak
      KC_DB_PASSWORD: keycloak_dev
    ports:
      - "8080:8080"
    volumes:
      - ./keycloak/realm-export.json:/opt/keycloak/data/import/realm.json
    networks:
      - kronos-external
      - kronos-internal  # Per comunicazione interna con services
    depends_on:
      keycloak-db:
        condition: service_healthy

  keycloak-db:
    image: postgres:15
    container_name: kronos-sso-db
    environment:
      POSTGRES_USER: keycloak
      POSTGRES_PASSWORD: keycloak_dev
      POSTGRES_DB: keycloak
    volumes:
      - keycloak_data:/var/lib/postgresql/data
    networks:
      - kronos-external
    healthcheck:
      test: ["CMD-SHELL", "pg_isready -U keycloak"]
      interval: 5s
      timeout: 5s
      retries: 5

  # ═══════════════════════════════════════════════════════════
  # FRONTEND
  # ═══════════════════════════════════════════════════════════
  frontend:
    build:
      context: ./frontend
      dockerfile: Dockerfile
    container_name: kronos-frontend
    ports:
      - "3000:3000"
    environment:
      - VITE_API_URL=http://localhost/api/v1
      - VITE_KEYCLOAK_URL=http://localhost:8080/
      - VITE_KEYCLOAK_REALM=kronos
      - VITE_KEYCLOAK_CLIENT_ID=kronos-frontend
    networks:
      - kronos-internal

# Additional volume for keycloak
volumes:
  keycloak_data:
```

---

## Init Schemas SQL

```sql
-- scripts/init-schemas.sql
-- Crea schema separati per ogni microservizio

CREATE SCHEMA IF NOT EXISTS auth;
CREATE SCHEMA IF NOT EXISTS leaves;
CREATE SCHEMA IF NOT EXISTS expenses;
CREATE SCHEMA IF NOT EXISTS config;
CREATE SCHEMA IF NOT EXISTS notifications;
CREATE SCHEMA IF NOT EXISTS audit;

-- Grant permissions
GRANT ALL ON SCHEMA auth TO kronos;
GRANT ALL ON SCHEMA leaves TO kronos;
GRANT ALL ON SCHEMA expenses TO kronos;
GRANT ALL ON SCHEMA config TO kronos;
GRANT ALL ON SCHEMA notifications TO kronos;
GRANT ALL ON SCHEMA audit TO kronos;

-- Enable pg_trgm for search
CREATE EXTENSION IF NOT EXISTS pg_trgm;

-- Enable uuid-ossp
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";
```

---

## Nginx Files

### proxy_params

```nginx
# nginx/proxy_params
proxy_set_header Host $host;
proxy_set_header X-Real-IP $remote_addr;
proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
proxy_set_header X-Forwarded-Proto $scheme;
proxy_set_header X-Request-ID $request_id;

proxy_connect_timeout 60s;
proxy_send_timeout 60s;
proxy_read_timeout 60s;
```

### ModSecurity Main Config

```conf
# nginx/modsec/main.conf
Include /etc/nginx/modsec/modsecurity.conf
Include /etc/nginx/modsec/crs-setup.conf
Include /etc/nginx/modsec/rules/*.conf

# Custom rules
SecRule REQUEST_URI "@beginsWith /api/v1/" "id:1000,phase:1,pass,nolog,setvar:tx.paranoia_level=1"
```

---

## Endpoints per Servizio

| Service | Port | Endpoints |
|---------|------|-----------|
| auth-service | 8001 | /auth, /users |
| leave-service | 8002 | /leaves, /balances |
| expense-service | 8003 | /trips, /expenses |
| config-service | 8004 | /config, /leave-types, /holidays |
| notification-service | 8005 | /notifications |
| audit-service | 8007 | /audit-logs, /audit-trail |

---

## Comandi Utili

```bash
# Start stack
docker-compose up -d

# Logs specifico servizio
docker-compose logs -f leave-service

# Shell nel container
docker exec -it kronos-auth bash

# Accesso diretto PostgreSQL
docker exec -it kronos-db psql -U kronos -d kronos

# Check network
docker network inspect kronos-internal

# Rebuild singolo servizio
docker-compose build --no-cache leave-service
docker-compose up -d leave-service

# Cleanup completo
docker-compose down -v --remove-orphans
```

---

## URLs

| API Gateway | http://localhost |
| Frontend | http://localhost:3000 |
| Keycloak Admin | http://localhost:8080/admin |
| MinIO Console | http://localhost:9001 |
| PostgreSQL | localhost:5432 |

---

## Note Importanti su Configurazione e Troubleshooting

### 1. Autenticazione & Keycloak
Tutti i microservizi backend ora richiedono la connessione a Keycloak per validare i token JWT delle richieste.
Assicurarsi che le seguenti variabili d'ambiente siano presenti in `docker-compose.yml` per ogni servizio (auth, leave, config, etc.):

```yaml
    environment:
      - KEYCLOAK_URL=http://keycloak:8080/  # Richiede slash finale per il backend
      - KEYCLOAK_REALM=kronos
      - KEYCLOAK_CLIENT_ID=kronos-backend
```

Per il **Frontend**, la variabile `VITE_KEYCLOAK_URL` deve essere `http://localhost:8080/` (o senza slash, ma coerente). Se si verificano doppi slash nei log (es. `//realms/...`), rimuovere lo slash finale dalla configurazione.

### 2. Database e Tabelle
I servizi sono configurati per creare automaticamente le tabelle all'avvio (`init_db` in `src/core/database.py`).
Se si vedono errori `Relation "..." does not exist`, provare a riavviare il servizio specifico:
```bash
docker-compose restart <service-name>
```

### 3. Errori Comuni
- **401 Unauthorized**: Token scaduto o servizio non in grado di validarlo (controllare logs backend per errori di connessione a Keycloak).
- **500 Internal Server Error su Leave Types**: Assicurarsi che i valori nel database per `balance_type` corrispondano ai valori validi (`vacation`, `rol`, `permits`). Valori come `days` o `hours` causeranno errori di validazione Pydantic.

