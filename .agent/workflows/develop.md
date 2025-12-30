---
description: Standard development workflow for KRONOS project
---

# KRONOS Development Workflow

**Before ANY development task, execute /read-docs first!**

---

## Pre-Development Checklist

// turbo-all

### 1. Read Documentation
Execute the `/read-docs` workflow to understand:
- Project architecture and principles
- Relevant module specifications
- Database schema
- Coding standards

### 2. Check Existing Code Structure
```bash
ls -la /Users/cristian/Desktop/app-gestione-presenze/
```

### 3. Verify Docker Services (if running)
```bash
docker-compose ps
```

---

## Development Guidelines

### Creating a New Microservice

1. Create directory structure:
```
src/services/{service_name}/
├── __init__.py
├── main.py          # FastAPI app
├── router.py        # Endpoints
├── schemas.py       # Pydantic models
├── service.py       # Business logic
├── repository.py    # Database queries
└── models.py        # SQLAlchemy models
```

2. Set correct DATABASE_SCHEMA environment variable
3. Create Alembic migrations for the service schema
4. Register routes in main.py
5. Add to docker-compose.yml
6. Configure Nginx routing

### Creating API Endpoints

1. Always use Pydantic schemas for request/response
2. Implement DataTable endpoint for list views:
   - POST `/api/v1/{entity}/datatable`
   - Accept DataTableRequest schema
   - Return DataTableResponse with server-side pagination
3. Add audit logging via decorator or service call
4. Use dependency injection for current_user, session, services

### Database Changes

1. Create migration in correct schema:
```bash
DATABASE_SCHEMA={schema} alembic revision --autogenerate -m "description"
```

2. Follow naming conventions from schema.md
3. Add indexes for frequently queried columns
4. Use UUID for all primary keys

### Frontend Components

1. Use DataTables.net for ANY table display
2. Use FullCalendar for ANY calendar view
3. Integrate with Keycloak via @react-keycloak/web
4. Use TanStack Query for server state
5. Follow Shadcn/ui component patterns

---

## Code Review Checklist

Before committing, verify:

- [ ] No hardcoded business values (use ConfigService)
- [ ] Audit logging implemented
- [ ] Type hints on all public methods
- [ ] Pydantic schemas for all I/O
- [ ] Server-side pagination for lists
- [ ] Proper error handling with HTTPException
- [ ] Tests written for service layer
