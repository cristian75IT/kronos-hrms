# Stack Tecnologico

## Backend

| Categoria | Tecnologia | Versione | Ruolo |
|-----------|------------|----------|-------|
| **Runtime** | Python | 3.11+ | Type hints obbligatori |
| **Framework** | FastAPI | 0.109+ | Async-first, OpenAPI |
| **ORM** | SQLAlchemy | 2.0+ | Async, schema isolation |
| **Migrations** | Alembic | 1.13+ | Per-schema migrations |
| **Validation** | Pydantic | 2.0+ | Settings, Schemas |
| **Database** | PostgreSQL | 15+ | Single container, multi-schema |
| **Cache** | Redis | 7+ | Session, Cache, Queue |
| **Task Queue** | Celery | 5.3+ | Job asincroni |
| **File Storage** | MinIO | Latest | S3-compatible |
| **API Gateway** | Traefik | 2.10+ | Load balancing, Rate limit |

## Frontend

| Categoria | Tecnologia | Versione | Ruolo |
|-----------|------------|----------|-------|
| **Framework** | React | 18+ | Strict Mode |
| **Build Tool** | Vite | 5+ | Hot reload, ESM |
| **Language** | TypeScript | 5+ | Strict mode |
| **State** | TanStack Query | 5+ | Server state |
| **UI Library** | Shadcn/ui | Latest | Radix + Tailwind |
| **Styling** | Tailwind CSS | 3+ | Utility-first |
| **DataTables** | DataTables.net | 2.0+ | ⭐ Server-side pagination/filter/sort |
| **Calendar** | FullCalendar | 6+ | ⭐ Vista calendario team |
| **Forms** | React Hook Form | 7+ | + Zod validation |
| **Router** | React Router | 6+ | Client-side routing |
| **HTTP Client** | Axios | 1.6+ | Interceptor per JWT |

## SSO & Autenticazione ⭐ ENTERPRISE

| Categoria | Tecnologia | Ruolo |
|-----------|------------|-------|
| **SSO Server** | Keycloak | Identity Provider centrale |
| **Protocol** | OpenID Connect (OIDC) | Standard OAuth2 |
| **LDAP** | Active Directory / OpenLDAP | User federation |
| **MFA** | TOTP / SMS / Email | Multi-Factor Authentication |
| **Python Client** | python-keycloak | Backend integration |
| **React Client** | @react-keycloak/web | Frontend integration |

---

## DataTables.net - Server-Side Processing

> **Principio**: MAI caricare tutti i dati in frontend. Sempre paginazione backend.

### Installazione

```bash
npm install datatables.net-react datatables.net-dt datatables.net-responsive-dt
```

### Configurazione React

```tsx
// components/DataTable.tsx
import DataTable from 'datatables.net-react';
import DT from 'datatables.net-dt';
import 'datatables.net-responsive-dt';

DataTable.use(DT);

interface ServerSideTableProps {
  apiEndpoint: string;
  columns: ColumnDef[];
}

export function ServerSideTable({ apiEndpoint, columns }: ServerSideTableProps) {
  return (
    <DataTable
      ajax={{
        url: apiEndpoint,
        type: 'POST',
        contentType: 'application/json',
        data: (d: any) => JSON.stringify(d),
      }}
      serverSide={true}
      processing={true}
      columns={columns}
      options={{
        responsive: true,
        pageLength: 25,
        lengthMenu: [10, 25, 50, 100],
        order: [[0, 'desc']],
        language: {
          url: '//cdn.datatables.net/plug-ins/2.0.0/i18n/it-IT.json',
        },
      }}
    />
  );
}
```

### Backend Endpoint per DataTables

```python
# schemas.py
from pydantic import BaseModel
from typing import Optional, List, Any

class DataTableRequest(BaseModel):
    draw: int
    start: int
    length: int
    search: dict  # {"value": "search term", "regex": false}
    order: List[dict]  # [{"column": 0, "dir": "asc"}]
    columns: List[dict]

class DataTableResponse(BaseModel):
    draw: int
    recordsTotal: int
    recordsFiltered: int
    data: List[Any]

# router.py
@router.post("/leaves/datatable", response_model=DataTableResponse)
async def get_leaves_datatable(
    request: DataTableRequest,
    current_user: User = Depends(get_current_user),
    session: AsyncSession = Depends(get_db),
) -> DataTableResponse:
    """Server-side processing for DataTables."""
    service = LeaveService(session)
    return await service.get_datatable(request, current_user.id)
```

---

## FullCalendar - Calendario

### Installazione

```bash
npm install @fullcalendar/react @fullcalendar/core @fullcalendar/daygrid @fullcalendar/timegrid @fullcalendar/interaction
```

### Configurazione

```tsx
// components/LeaveCalendar.tsx
import FullCalendar from '@fullcalendar/react';
import dayGridPlugin from '@fullcalendar/daygrid';
import timeGridPlugin from '@fullcalendar/timegrid';
import interactionPlugin from '@fullcalendar/interaction';
import itLocale from '@fullcalendar/core/locales/it';

interface LeaveCalendarProps {
  userId?: string;
  teamView?: boolean;
}

export function LeaveCalendar({ userId, teamView }: LeaveCalendarProps) {
  const fetchEvents = async (info: any) => {
    const response = await api.get('/leaves/calendar', {
      params: {
        start: info.startStr,
        end: info.endStr,
        userId,
        teamView,
      },
    });
    return response.data;
  };

  return (
    <FullCalendar
      plugins={[dayGridPlugin, timeGridPlugin, interactionPlugin]}
      initialView="dayGridMonth"
      locale={itLocale}
      headerToolbar={{
        left: 'prev,next today',
        center: 'title',
        right: 'dayGridMonth,timeGridWeek',
      }}
      events={fetchEvents}
      eventClick={(info) => {
        // Open leave detail modal
      }}
      selectable={true}
      select={(info) => {
        // Open new leave request modal with dates pre-filled
      }}
    />
  );
}
```

---

## Keycloak SSO

### Architettura

```
┌─────────────┐     ┌─────────────┐     ┌─────────────┐
│   Browser   │────▶│  Keycloak   │◀────│    LDAP     │
│  (React)    │     │   (SSO)     │     │ (AD/OpenLDAP)│
└──────┬──────┘     └──────┬──────┘     └─────────────┘
       │                   │
       │ JWT Token         │ User Federation
       ▼                   │
┌─────────────┐            │
│  API Gateway│◀───────────┘
│  (Traefik)  │  Token Validation
└──────┬──────┘
       │
       ▼
┌─────────────┐
│ Microservices│
└─────────────┘
```

### Docker Compose

```yaml
keycloak:
  image: quay.io/keycloak/keycloak:23.0
  command: start-dev
  environment:
    KEYCLOAK_ADMIN: admin
    KEYCLOAK_ADMIN_PASSWORD: admin
    KC_DB: postgres
    KC_DB_URL: jdbc:postgresql://postgres:5432/keycloak
    KC_DB_USERNAME: keycloak
    KC_DB_PASSWORD: keycloak
  ports:
    - "8080:8080"
  depends_on:
    - postgres
```

### Backend Integration

```python
# core/auth.py
from keycloak import KeycloakOpenID

keycloak_openid = KeycloakOpenID(
    server_url="http://keycloak:8080/",
    client_id="hrms-backend",
    realm_name="hrms",
    client_secret_key="your-client-secret",
)

async def validate_token(token: str) -> dict:
    """Validate JWT token with Keycloak."""
    try:
        return keycloak_openid.decode_token(
            token,
            key=keycloak_openid.public_key(),
            options={"verify_aud": False},
        )
    except Exception:
        raise HTTPException(status_code=401)

async def get_current_user(
    token: str = Depends(oauth2_scheme),
    session: AsyncSession = Depends(get_db),
) -> User:
    """Get current user from Keycloak token."""
    payload = await validate_token(token)
    
    # Sync user from Keycloak to local DB
    user = await sync_user_from_keycloak(session, payload)
    return user
```

### Frontend Integration

```tsx
// main.tsx
import { ReactKeycloakProvider } from '@react-keycloak/web';
import Keycloak from 'keycloak-js';

const keycloak = new Keycloak({
  url: 'http://localhost:8080/',
  realm: 'hrms',
  clientId: 'hrms-frontend',
});

ReactDOM.createRoot(document.getElementById('root')!).render(
  <ReactKeycloakProvider authClient={keycloak}>
    <App />
  </ReactKeycloakProvider>
);

// hooks/useAuth.ts
import { useKeycloak } from '@react-keycloak/web';

export function useAuth() {
  const { keycloak, initialized } = useKeycloak();

  return {
    isAuthenticated: keycloak.authenticated,
    user: keycloak.tokenParsed,
    login: () => keycloak.login(),
    logout: () => keycloak.logout(),
    token: keycloak.token,
    hasRole: (role: string) => keycloak.hasRealmRole(role),
  };
}
```

### MFA Configuration

In Keycloak Admin Console:
1. Authentication → Required Actions → Enable "Configure OTP"
2. Authentication → Flows → Browser → Add "OTP Form" 
3. Realm Settings → Security Defenses → Configure MFA policy

---

## Dependency Python aggiornate

```toml
# pyproject.toml
dependencies = [
    # ... previous deps ...
    
    # Keycloak SSO
    "python-keycloak>=3.7.0",
    
    # DataTables server-side
    "sqlalchemy-datatables>=2.0.0",  # Helper per parsing request
]
```

## Dipendenze Frontend aggiornate

```json
{
  "dependencies": {
    "@react-keycloak/web": "^3.4.0",
    "keycloak-js": "^23.0.0",
    "datatables.net-react": "^1.0.0",
    "datatables.net-dt": "^2.0.0",
    "datatables.net-responsive-dt": "^3.0.0",
    "@fullcalendar/react": "^6.1.0",
    "@fullcalendar/core": "^6.1.0",
    "@fullcalendar/daygrid": "^6.1.0",
    "@fullcalendar/timegrid": "^6.1.0",
    "@fullcalendar/interaction": "^6.1.0"
  }
}
```
