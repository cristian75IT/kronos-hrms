---
description: Enterprise DevOps & Infrastructure Agent
---

# Enterprise DevOps Agent Workflow

This workflow manages the **containerized infrastructure**, **Nginx routing**, and **service health**.

**Role:** DevOps Engineer / SRE
**Goal:** Stable, observable, and secure infrastructure.

---

## 🛑 PRIME DIRECTIVES

1.  **INFRASTRUCTURE AS CODE**: All changes via `docker-compose.yml` or config files.
2.  **NO MANUAL FIXES**: If you fix something manually, codify it.
3.  **OBSERVABILITY**: Logs must be accessible and meaningful.

---

## 1. Service Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                      NGINX (Gateway)                        │
│                    Port 80/443 (external)                   │
└──────────────────────────┬──────────────────────────────────┘
                           │
              ┌────────────┼────────────┐
              │            │            │
        ┌─────▼─────┐ ┌────▼────┐ ┌─────▼─────┐
        │ auth:8001 │ │leave:8002│ │expense:8003│
        └───────────┘ └─────────┘ └───────────┘
              │            │            │
              └────────────┼────────────┘
                           │
              ┌────────────▼────────────┐
              │  PostgreSQL / Redis     │
              │  (kronos-internal net)  │
              └─────────────────────────┘
```

---

## 2. Common Operations

### Service Health Check
// turbo
```bash
# Check all services
docker-compose ps

# Check specific service logs
docker-compose logs -f {service_name}
```

### Restart Service
```bash
# Graceful restart
docker-compose restart {service_name}

# Rebuild and restart (after code changes)
docker-compose up -d --build {service_name}
```

### Full Stack Reset
```bash
# Use project rebuild script
./rebuild.sh
```

---

## 3. Nginx Configuration

### Routing Config
**Location**: `nginx/conf.d/`

### Add New Service Route
```nginx
# nginx/conf.d/api.conf
location /api/v1/newservice {
    proxy_pass http://new-service:8014/api/v1/newservice;
    include /etc/nginx/proxy_params;
}
```

### Reload Nginx
```bash
docker-compose exec nginx nginx -s reload
```

---

## 4. Troubleshooting Guide

| Symptom | Likely Cause | Action |
|---------|--------------|--------|
| 502 Bad Gateway | Service not running | `docker-compose ps` → restart service |
| 504 Gateway Timeout | Service unresponsive | Check service logs for deadlock/crash |
| Connection Refused | Wrong internal URL | Verify `docker-compose.yml` service name |
| Health check failing | DB not ready | Check `depends_on` conditions |

### Log Analysis
// turbo
```bash
# Tail all service logs
docker-compose logs -f --tail=100

# Filter for errors
docker-compose logs 2>&1 | grep -i "error\|exception\|critical"
```

---

## 5. Adding a New Service

### Checklist

1.  [ ] Add service to `docker-compose.yml`:
    -   Set `SERVICE_NAME` and `DATABASE_SCHEMA`.
    -   Configure `depends_on` with health checks.
    -   Set correct port.

2.  [ ] Add Nginx route in `nginx/conf.d/`.

3.  [ ] Create database schema:
    ```bash
    # In PostgreSQL
    CREATE SCHEMA IF NOT EXISTS new_service;
    ```

4.  [ ] Run migrations:
    ```bash
    DATABASE_SCHEMA=new_service alembic upgrade head
    ```

5.  [ ] Verify service is healthy:
    ```bash
    curl http://localhost/api/v1/newservice/health
    ```

---

## 6. Security Considerations

| Item | Check |
|------|-------|
| **Secrets** | Verify all secrets in `.env`, not in code. |
| **ModSecurity** | WAF rules in `nginx/modsecurity_custom.conf`. |
| **Network Isolation** | Internal services on `kronos-internal` only. |
| **Port Exposure** | Only expose 80/443. No direct service ports. |

---

## 7. Final Checklist

- [ ] All services healthy (`docker-compose ps`).
- [ ] Logs are clean of critical errors.
- [ ] Nginx routing correct for new services.
- [ ] Secrets not exposed in code.
- [ ] Networks properly isolated.
