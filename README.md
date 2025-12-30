# KRONOS - Enterprise HRMS

> **Κρόνος** - Sistema Enterprise per Gestione Presenze, Assenze e Rimborsi

## Quick Start

```bash
# 1. Copia variabili ambiente
cp .env.example .env

# 2. Avvia lo stack completo
docker-compose up -d

# 3. Attendi che tutti i servizi siano avviati
docker-compose ps

# 4. Accedi alle applicazioni
- Frontend: http://localhost:3000
- API Gateway: http://localhost/api/v1
- Keycloak Admin: http://localhost:8080/admin (admin/admin)
- MinIO Console: http://localhost:9001 (kronos/kronos_dev)
```

## Utenti Demo

| Username | Password | Ruolo |
|----------|----------|-------|
| admin@kronos.local | admin123 | Admin + Approver |
| manager@kronos.local | manager123 | Manager + Approver |
| employee@kronos.local | employee123 | Employee |

## Architettura

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                          KRONOS Architecture                                 │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                              │
│  ┌─────────────────┐     ┌─────────────────────────────────────────────┐    │
│  │   Frontend      │────▶│           Nginx + ModSecurity              │    │
│  │   (React)       │     │              API Gateway                    │    │
│  └─────────────────┘     └─────────────────────────────────────────────┘    │
│                                           │                                  │
│         ┌─────────────────────────────────┼─────────────────────────────┐   │
│         │              │                  │               │             │   │
│         ▼              ▼                  ▼               ▼             ▼   │
│  ┌──────────┐   ┌──────────┐   ┌──────────┐   ┌──────────┐   ┌──────────┐  │
│  │  Auth    │   │  Leave   │   │ Expense  │   │  Config  │   │  Audit   │  │
│  │ Service  │   │ Service  │   │ Service  │   │ Service  │   │ Service  │  │
│  └────┬─────┘   └────┬─────┘   └────┬─────┘   └────┬─────┘   └────┬─────┘  │
│       │              │              │              │              │        │
│       └──────────────┼──────────────┼──────────────┼──────────────┘        │
│                      │              │              │                       │
│  ┌───────────────────┴──────────────┴──────────────┴───────────────────┐   │
│  │                         PostgreSQL                                   │   │
│  │   auth | leaves | expenses | config | notifications | audit          │   │
│  └─────────────────────────────────────────────────────────────────────┘   │
│                                                                              │
│  ┌─────────────┐          ┌─────────────┐          ┌─────────────┐         │
│  │    Redis    │          │   Keycloak  │          │    MinIO    │         │
│  │   (Cache)   │          │    (SSO)    │          │  (Storage)  │         │
│  └─────────────┘          └─────────────┘          └─────────────┘         │
│                                                                              │
└──────────────────────────────────────────────────────────────────────────────┘
```

## Struttura Progetto

```
kronos/
├── docker-compose.yml        # Stack Docker completo
├── .env.example              # Template variabili ambiente
├── progetto.md               # Documento analisi
│
├── backend/                  # Microservizi Python
│   ├── Dockerfile
│   ├── pyproject.toml
│   └── src/
│       ├── core/             # Configurazione, DB, Security
│       ├── shared/           # Schemas comuni
│       └── services/
│           ├── auth/         # Auth Service :8001
│           ├── config/       # Config Service :8004
│           ├── leaves/       # Leave Service :8002
│           ├── expenses/     # Expense Service :8003
│           ├── notifications/# Notification Service :8005
│           └── audit/        # Audit Service :8007
│
├── frontend/                 # React SPA
│   ├── Dockerfile.dev
│   └── src/
│
├── nginx/                    # API Gateway
│   ├── nginx.conf
│   └── proxy_params
│
├── keycloak/                 # SSO Configuration
│   └── realm-kronos.json
│
├── scripts/                  # Utility scripts
│   └── init-db.sql
│
└── docs/                     # Documentazione per AI agents
    ├── README.md
    ├── architecture.md
    ├── tech-stack.md
    └── ...
```

## Documentazione

Vedi `/docs/` per documentazione completa:
- [Architecture](docs/architecture.md)
- [Tech Stack](docs/tech-stack.md)
- [Setup](docs/setup.md)
- [Database Schema](docs/database/schema.md)
- [Modules](docs/modules/)
- [Business Rules](docs/business/)

## Sviluppo

```bash
# Backend development
cd backend
python -m venv .venv
source .venv/bin/activate
pip install -e ".[dev]"

# Migrazioni
alembic upgrade head

# Run tests
pytest

# Linting
ruff check .
mypy src
```

## License

Proprietary - All rights reserved
