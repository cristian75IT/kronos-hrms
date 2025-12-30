# Modulo Auth (SSO/LDAP/MFA)

## Architettura Autenticazione

Il sistema utilizza **Keycloak** come Identity Provider centralizzato per:
- Single Sign-On (SSO)
- Federazione LDAP/Active Directory
- Multi-Factor Authentication (MFA/2FA)
- Gestione ruoli e permessi centralizzata

---

## Architettura

```
┌─────────────┐     ┌─────────────┐     ┌─────────────┐
│   Browser   │────▶│  Keycloak   │◀────│    LDAP     │
│  (React)    │     │   (SSO)     │     │ (AD/OpenLDAP)│
└──────┬──────┘     └──────┬──────┘     └─────────────┘
       │                   │
       │ JWT (OIDC)        │ User Federation
       ▼                   │
┌─────────────┐            │
│  API Gateway│◀───────────┘
│  (Traefik)  │  Token Introspection
└──────┬──────┘
       │
       ▼
┌─────────────────────────────────────┐
│           Microservices             │
│  (Token validation + local sync)    │
└─────────────────────────────────────┘
```

---

## Keycloak Configuration

### Realm: `hrms`

### Clients:
| Client ID | Type | Descrizione |
|-----------|------|-------------|
| `hrms-frontend` | Public | React SPA |
| `hrms-backend` | Confidential | FastAPI services |

### Realm Roles:
| Role | Descrizione |
|------|-------------|
| `admin` | Amministratore HR |
| `manager` | Responsabile Area |
| `employee` | Dipendente |
| `approver` | Capability approvazione |

### User Federation (LDAP):
- Vendor: Active Directory / OpenLDAP
- Edit Mode: READ_ONLY (users managed in LDAP)
- Sync: Full sync + Changed users sync

### MFA Policy:
- OTP (TOTP via app): Obbligatorio per admin
- Email OTP: Opzionale per altri ruoli
- Conditional: Richiesto se IP non trusted

---

## Endpoints

Il modulo Auth NON espone endpoint di login diretto.
L'autenticazione avviene tramite Keycloak.

| Method | Endpoint | Descrizione |
|--------|----------|-------------|
| `GET` | `/api/v1/auth/me` | Info utente corrente (da token) |
| `POST` | `/api/v1/auth/sync` | Forza sync utente da Keycloak |
| `GET` | `/api/v1/users` | Lista utenti (Admin) |
| `GET` | `/api/v1/users/{id}` | Dettaglio utente |
| `PUT` | `/api/v1/users/{id}` | Modifica dati locali (non LDAP) |

---

## Backend Integration

```python
# core/security.py
from keycloak import KeycloakOpenID
from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="token")

keycloak = KeycloakOpenID(
    server_url=settings.KEYCLOAK_URL,
    client_id=settings.KEYCLOAK_CLIENT_ID,
    realm_name=settings.KEYCLOAK_REALM,
    client_secret_key=settings.KEYCLOAK_CLIENT_SECRET,
)

async def get_current_user(
    token: str = Depends(oauth2_scheme),
    session: AsyncSession = Depends(get_db),
) -> User:
    """Validate token and get/sync user."""
    try:
        # Decode and validate token
        payload = keycloak.decode_token(
            token,
            key=keycloak.public_key(),
            options={"verify_aud": False, "verify_exp": True},
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid token",
        )
    
    # Get or create local user record
    user = await sync_user_from_token(session, payload)
    
    if not user.is_active:
        raise HTTPException(status_code=403, detail="User disabled")
    
    return user


async def sync_user_from_token(
    session: AsyncSession,
    payload: dict,
) -> User:
    """Sync Keycloak user to local database."""
    keycloak_id = payload["sub"]
    email = payload.get("email")
    
    repo = UserRepository(session)
    user = await repo.get_by_keycloak_id(keycloak_id)
    
    if not user:
        # Create new user from Keycloak data
        user = await repo.create(
            keycloak_id=keycloak_id,
            email=email,
            full_name=payload.get("name", ""),
            role=extract_role_from_token(payload),
            is_approver="approver" in payload.get("realm_roles", []),
        )
    else:
        # Update role if changed in Keycloak
        new_role = extract_role_from_token(payload)
        if user.role != new_role:
            user = await repo.update(user.id, role=new_role)
    
    return user


def extract_role_from_token(payload: dict) -> str:
    """Extract highest role from Keycloak roles."""
    roles = payload.get("realm_access", {}).get("roles", [])
    
    if "admin" in roles:
        return "admin"
    elif "manager" in roles:
        return "manager"
    else:
        return "employee"
```

---

## Frontend Integration

```tsx
// lib/keycloak.ts
import Keycloak from 'keycloak-js';

export const keycloak = new Keycloak({
  url: import.meta.env.VITE_KEYCLOAK_URL,
  realm: import.meta.env.VITE_KEYCLOAK_REALM,
  clientId: import.meta.env.VITE_KEYCLOAK_CLIENT_ID,
});

// main.tsx
import { ReactKeycloakProvider } from '@react-keycloak/web';
import { keycloak } from './lib/keycloak';

const initOptions = {
  onLoad: 'login-required',
  checkLoginIframe: false,
};

ReactDOM.createRoot(document.getElementById('root')!).render(
  <ReactKeycloakProvider authClient={keycloak} initOptions={initOptions}>
    <QueryClientProvider client={queryClient}>
      <App />
    </QueryClientProvider>
  </ReactKeycloakProvider>
);

// hooks/useAuth.ts
import { useKeycloak } from '@react-keycloak/web';

export function useAuth() {
  const { keycloak, initialized } = useKeycloak();

  const user = keycloak.tokenParsed;

  return {
    initialized,
    isAuthenticated: !!keycloak.authenticated,
    user: user ? {
      id: user.sub,
      email: user.email,
      name: user.name,
      role: extractRole(user.realm_access?.roles || []),
      isApprover: user.realm_access?.roles?.includes('approver'),
    } : null,
    token: keycloak.token,
    login: () => keycloak.login(),
    logout: () => keycloak.logout({ redirectUri: window.location.origin }),
    hasRole: (role: string) => keycloak.hasRealmRole(role),
  };
}

// api/client.ts - Axios interceptor
import axios from 'axios';
import { keycloak } from '../lib/keycloak';

const api = axios.create({
  baseURL: import.meta.env.VITE_API_URL,
});

api.interceptors.request.use(async (config) => {
  // Refresh token if needed
  await keycloak.updateToken(30);
  
  config.headers.Authorization = `Bearer ${keycloak.token}`;
  return config;
});

export default api;
```

---

## Schema Database (auth schema)

```sql
-- Minimal local user table (synced from Keycloak)
CREATE TABLE auth.users (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    keycloak_id VARCHAR(255) UNIQUE NOT NULL,  -- sub from JWT
    email VARCHAR(255) UNIQUE NOT NULL,
    full_name VARCHAR(255) NOT NULL,
    employee_id VARCHAR(50),                    -- Matricola (local only)
    
    -- Role (synced from Keycloak)
    role VARCHAR(20) NOT NULL DEFAULT 'employee',
    is_approver BOOLEAN DEFAULT FALSE,
    is_active BOOLEAN DEFAULT TRUE,
    
    -- Local extensions (not in Keycloak)
    line_manager_id UUID REFERENCES auth.users(id),
    location_id UUID REFERENCES auth.locations(id),
    contract_type_id UUID REFERENCES auth.contract_types(id),
    work_schedule_id UUID REFERENCES auth.work_schedules(id),
    hire_date DATE,
    
    -- Audit
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW(),
    last_login_at TIMESTAMPTZ
);

CREATE INDEX idx_users_keycloak ON auth.users(keycloak_id);
```

---

## Dependency Injection

```python
# dependencies.py

from fastapi import Depends

# Auth dependencies
async def get_current_user(token: str = Depends(oauth2_scheme)) -> User:
    """Validate token, return user."""
    ...

async def require_active(user: User = Depends(get_current_user)) -> User:
    """Require active user."""
    if not user.is_active:
        raise HTTPException(403)
    return user

async def require_admin(user: User = Depends(require_active)) -> User:
    """Require admin role."""
    if user.role != "admin":
        raise HTTPException(403)
    return user

async def require_manager(user: User = Depends(require_active)) -> User:
    """Require manager or admin role."""
    if user.role not in ("admin", "manager"):
        raise HTTPException(403)
    return user

async def require_approver(user: User = Depends(require_active)) -> User:
    """Require approver capability."""
    if not user.is_approver and user.role != "admin":
        raise HTTPException(403)
    return user
```

---

## Environment Variables

```bash
# Keycloak
KEYCLOAK_URL=http://keycloak:8080/
KEYCLOAK_REALM=hrms
KEYCLOAK_CLIENT_ID=hrms-backend
KEYCLOAK_CLIENT_SECRET=your-secret

# Frontend (.env)
VITE_KEYCLOAK_URL=http://localhost:8080/
VITE_KEYCLOAK_REALM=hrms
VITE_KEYCLOAK_CLIENT_ID=hrms-frontend
```
