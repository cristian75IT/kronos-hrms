# Modulo Config (Configurazione Dinamica)

## Principio Fondamentale

> **ZERO HARDCODING**: Tutti i parametri configurabili risiedono in database.

---

## Responsabilità

- Gestione parametri di sistema (SystemConfig)
- Gestione tipi di assenza (LeaveTypes)
- Gestione regole policy (PolicyRules)
- Gestione festività (Holidays)
- Cache Redis per performance

---

## Endpoints API

| Method | Endpoint | Descrizione | Auth |
|--------|----------|-------------|------|
| `GET` | `/api/v1/config` | Lista config | Admin |
| `PUT` | `/api/v1/config/{key}` | Aggiorna config | Admin |
| `GET` | `/api/v1/leave-types` | Lista tipi assenza | All |
| `POST` | `/api/v1/leave-types` | Crea tipo | Admin |
| `GET` | `/api/v1/holidays/year/{year}` | Festività anno | All |
| `POST` | `/api/v1/holidays/generate/{year}` | Genera festività | Admin |

---

## Configurazioni Standard

| Key | Default | Categoria |
|-----|---------|-----------|
| `leave.min_notice_days.rol` | `2` | leave_policy |
| `leave.min_notice_days.vacation` | `5` | leave_policy |
| `leave.max_consecutive_days` | `15` | leave_policy |
| `leaves.block_insufficient_balance` | `true` | leave_policy |
| `notify_leave_request` | `true` | notifications |
| `notify_leave_approval` | `true` | notifications |
| `notify_wallet_expiry` | `false` | notifications |
| `push_approvals` | `true` | notifications |
| `expense.km_rate` | `0.30` | expense_policy |
| `expense.max_hotel_night` | `120.00` | expense_policy |
| `compliance.vacation_min_days_year` | `20` | compliance |

---

## Service con Cache

```python
class ConfigService:
    CACHE_PREFIX = "config:"
    CACHE_TTL = 300  # 5 minuti
    
    async def get(self, key: str, default: Any = None) -> Any:
        """Get config with Redis cache."""
        cache_key = f"{self.CACHE_PREFIX}{key}"
        cached = await self._redis.get(cache_key)
        if cached:
            return json.loads(cached)
        
        config = await self._repository.get_by_key(key)
        if config is None:
            return default
        
        await self._redis.setex(cache_key, self.CACHE_TTL, json.dumps(config.value))
        return config.value
```

---

## Utilizzo Corretto

```python
# ❌ SBAGLIATO
if days > 15:  # Magic number!
    raise Error()

# ✅ CORRETTO
max_days = await config.get("leave.max_consecutive_days", default=15)
if days > max_days:
    raise Error(f"Max {max_days} giorni")
```
