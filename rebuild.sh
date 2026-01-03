#!/bin/bash
set -e # Termina se c'è un errore

# Colori per l'output
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m' # No Color

echo -e "${YELLOW}🔄 KRONOS - Full Stack Rebuild & Init${NC}"
echo "========================================"

# 1. Pulizia Totale
echo -e "\n${YELLOW}🧹  Stopping containers and removing volumes...${NC}"
docker-compose down -v --remove-orphans
echo -e "${GREEN}✓ Clean complete${NC}"

# 2. Build No Cache
echo -e "\n${YELLOW}🏗️  Building images (no cache)...${NC}"
echo "This might take a while..."
docker-compose build --no-cache
echo -e "${GREEN}✓ Build complete${NC}"

# 3. Avvio Stack
echo -e "\n${YELLOW}🚀 Starting services...${NC}"
docker-compose up -d
echo -e "${GREEN}✓ Stack started${NC}"

# 4. Attesa Healthcheck
echo -e "\n${YELLOW}⏳ Waiting for services to be ready...${NC}"
# Attesa semplice per dare tempo ai container di avviarsi
# (In produzione si userebbero healthcheck più robusti)
echo "Waiting 15 seconds for DB and Services initialization..."
sleep 15

# 5. Seed Database
echo -e "\n${YELLOW}🌱 Seeding database...${NC}"
echo "   - Creating schemas (auth, leaves, expenses, config, notifications, audit)"
echo "   - Running Alembic migrations"
echo "   - Seeding leave types, holidays, national contracts (CCNL)"
# Eseguiamo gli script python dentro il container auth-service
echo "   - Running database initialization (init_db.py)..."
if docker exec kronos-auth python scripts/init_db.py; then
    echo "   - Running enterprise calendar seed..."
    docker exec kronos-auth python scripts/seed_enterprise_calendar_data.py
    echo "   - Running enterprise data seed (users, wallets, reporting)..."
    docker exec kronos-auth python scripts/seed_enterprise_data.py
    echo -e "${GREEN}✓ Database initialized and seeded successfully!${NC}"
else
    echo -e "${RED}❌ Database initialization failed.${NC}"
    echo "Check the logs with: docker logs kronos-auth"
    exit 1
fi

echo -e "\n${GREEN}✨ KRONOS Stack is READY! ✨${NC}"
echo "========================================"
echo -e "Frontend:    ${GREEN}http://localhost:3000${NC}"
echo -e "Keycloak:    ${GREEN}http://localhost:8080${NC} (admin/admin)"
echo -e "API Docs:    ${GREEN}http://localhost:8001/docs${NC}"
echo "========================================"
