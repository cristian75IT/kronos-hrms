# KRONOS - Enterprise HRMS

> **Κρόνος** - Sistema Enterprise per Gestione Presenze, Assenze e Rimborsi

Documentazione tecnica per agenti AI (Antigravity) per implementare il sistema in modo autonomo.

---


## 📋 Indice Documentazione

### Architettura e Setup
| File | Descrizione |
|------|-------------|
| [architecture.md](./architecture.md) | Architettura microservizi, database schema isolation |
| [tech-stack.md](./tech-stack.md) | Stack con DataTables.net, FullCalendar, Keycloak SSO |
| [project-structure.md](./project-structure.md) | Struttura directory e convenzioni file |
| [setup.md](./setup.md) | Guida setup ambiente di sviluppo |

### Database
| File | Descrizione |
|------|-------------|
| [database/schema.md](./database/schema.md) | Schema ERD completo con tutte le tabelle |

### Moduli Backend
| File | Descrizione |
|------|-------------|
| [modules/auth.md](./modules/auth.md) | **Keycloak SSO, LDAP, OAuth2, MFA** |
| [modules/leaves.md](./modules/leaves.md) | Richieste assenze, saldi, workflow |
| [modules/expenses.md](./modules/expenses.md) | Trasferte e rimborsi spese |
| [modules/config.md](./modules/config.md) | Configurazione dinamica (zero hardcoding) |
| [modules/notifications.md](./modules/notifications.md) | **Email via Brevo, template, in-app** |

### Business Rules
| File | Descrizione |
|------|-------------|
| [business/leave-policies.md](./business/leave-policies.md) | Regole policy engine per assenze |
| [business/compliance-italy.md](./business/compliance-italy.md) | Normativa italiana D.Lgs 66/2003 |

### Development
| File | Descrizione |
|------|-------------|
| [development/coding-standards.md](./development/coding-standards.md) | Best practices Python/FastAPI |

---

## 🎯 Principi Fondamentali

| # | Principio | Descrizione |
|---|-----------|-------------|
| 1 | **Zero Hardcoding** | Tutti i parametri in database (`system_config`) |
| 2 | **Database Isolation** | PostgreSQL unico, schema separati per microservizio |
| 3 | **SSO Enterprise** | Keycloak con LDAP/OAuth2/MFA |
| 4 | **DataTables Backend** | Sempre paginazione/filter/sort server-side |
| 5 | **Librerie Standard** | DataTables.net, FullCalendar, MAI custom |
| 6 | **Clean Architecture** | Router → Service → Repository → Model |
| 7 | **Type Safety** | Type hints obbligatori, Pydantic |
| 8 | **Async First** | SQLAlchemy 2.0 async, FastAPI async |
| 9 | **Identity Resolution** | `keycloak_id` → `internal_id` via auth service |

---

## 📝 Changelog

| Data | Versione | Descrizione |
|------|----------|-------------|
| 2026-01-01 | v1.1.0 | [Identity Resolution, Bug Fixes](./CHANGELOG-2026-01-01.md) |

## ⚡ Quick Start per Agenti

### Ordine di Implementazione
1. `setup.md` → Docker Compose (Postgres, Redis, Keycloak, MinIO)
2. `modules/auth.md` → Keycloak config + sync user
3. `database/schema.md` → Migrazioni per ogni schema
4. `modules/config.md` → ConfigService con cache
5. `modules/leaves.md` → Core business
6. `modules/expenses.md` → Modulo secondario
7. Frontend con DataTables.net e FullCalendar

---

## 🔗 Link Rapidi

- **Documento Originale**: [../progetto.md](../progetto.md)
- **Schema Database**: [database/schema.md](./database/schema.md)
- **SSO/Auth**: [modules/auth.md](./modules/auth.md)
- **Regole Business**: [business/leave-policies.md](./business/leave-policies.md)
