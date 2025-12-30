# Modulo Expenses (Trasferte e Rimborsi)

## Responsabilità

- CRUD Trasferte (Business Trips)
- Calcolo diarie automatico
- CRUD Note Spese (Expense Reports)
- Gestione voci di spesa (Expense Items)
- Upload allegati (ricevute)

---

## Endpoints

### Trasferte

| Method | Endpoint | Descrizione |
|--------|----------|-------------|
| `GET` | `/api/v1/trips` | Lista trasferte utente |
| `POST` | `/api/v1/trips` | Crea trasferta |
| `POST` | `/api/v1/trips/{id}/approve` | Approva trasferta |
| `POST` | `/api/v1/trips/{id}/reject` | Rifiuta trasferta |

### Note Spese

| Method | Endpoint | Descrizione |
|--------|----------|-------------|
| `GET` | `/api/v1/expenses` | Lista note spese |
| `POST` | `/api/v1/expenses` | Crea nota spese |
| `POST` | `/api/v1/expenses/{id}/submit` | Invia per approvazione |
| `POST` | `/api/v1/expenses/{id}/approve` | Approva (anche parziale) |
| `POST` | `/api/v1/expenses/{id}/pay` | Marca come pagata |

### Voci di Spesa

| Method | Endpoint | Descrizione |
|--------|----------|-------------|
| `POST` | `/api/v1/expenses/{id}/items` | Aggiungi voce |
| `PUT` | `/api/v1/expenses/{id}/items/{item_id}` | Modifica voce |
| `DELETE` | `/api/v1/expenses/{id}/items/{item_id}` | Rimuovi voce |

---

## Workflow

```
TRASFERTA                    NOTA SPESE
[DRAFT] → [PENDING] → [APPROVED]    [DRAFT] → [SUBMITTED] → [APPROVED]
            ↓                                     ↓            ↓
        [REJECTED]   [COMPLETED]             [REJECTED]     [PAID]
                          ↓                                   ↓
                          └───────── Collegate ───────────────┘
```

---

## Tipologie Spesa

| Codice | Categoria | Limite | Ricevuta |
|--------|-----------|--------|----------|
| TRA | Trasporti | - | Sì |
| AUT | Auto Propria | €0.30/km | No |
| PED | Pedaggi | - | Sì |
| ALB | Alloggio | €120/notte | Sì |
| PAS | Pasti | €30/pasto | Sì |

---

## Calcolo Diaria

```python
async def calculate_daily_allowance(
    trip: BusinessTrip,
    config: ConfigService,
) -> Decimal:
    """Calcola diaria per trasferta."""
    rule = await get_allowance_rule(trip.destination_type)
    
    days = 0
    for day in date_range(trip.start_date, trip.end_date):
        hours = calculate_hours_for_day(trip, day)
        
        if hours >= rule.threshold_hours:
            days += 1  # Diaria intera
        elif hours >= rule.threshold_hours / 2:
            days += 0.5  # Mezza diaria
    
    return days * rule.full_day_amount
```

---

## Upload Ricevute

- Storage: MinIO (S3-compatible)
- Path: `receipts/{user_id}/{expense_id}/{filename}`
- Formati: PDF, JPG, PNG
- Max size: 5MB
- Presigned URL per download
