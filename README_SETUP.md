# KRONOS - Setup Guide

## Prerequisiti
- Docker & Docker Compose
- Node.js 20+ (per sviluppo locale frontend)
- Python 3.11+ (per sviluppo locale backend)

## Primo Avvio (Docker)

1. **Avviare lo stack completo:**
   ```bash
   docker-compose up --build -d
   ```

2. **Inizializzare il Database (Migrazioni e Seed Data):**
   Una volta che i container sono attivi, esegui lo script di inizializzazione da uno dei container backend (es. auth-service):
   ```bash
   docker exec -it kronos-auth python scripts/init_db.py
   ```
   *Questo creerà gli schemi, le tabelle e inserirà i dati di base (tipi ferie, utenti admin, ecc).*

3. **Accesso:**
   - **Frontend:** http://localhost:3000
   - **Keycloak:** http://localhost:8080 (admin/admin)
   - **MinIO Console:** http://localhost:9001 (kronos/kronos_dev)
   - **API Docs:**
     - Auth: http://localhost:8001/docs
     - Leaves: http://localhost:8002/docs
     - Expenses: http://localhost:8003/docs
     - Config: http://localhost:8004/docs
     - Notifications: http://localhost:8005/docs

## Sviluppo Locale (Frontend)

1. Spostarsi nella cartella frontend:
   ```bash
   cd frontend
   ```
2. Installare dipendenze:
   ```bash
   npm install
   ```
3. Avviare server dev:
   ```bash
   npm run dev
   ```

## Credenziali Default
- **Keycloak Admin:** admin / admin
- **Utente Test (creato dal seed):** admin@kronos.local / admin123 (verificare in Keycloak se creato, altrimenti crearlo manualmente nel realm "kronos")
