# Policy Assenze (Leave Policies)

## Policy Engine

Il sistema valida le richieste assenza contro regole configurabili in database.

---

## Regole per Leave Type

Ogni tipo di assenza ha parametri configurabili nella tabella `leave_types`:

| Parametro | Tipo | Descrizione |
|-----------|------|-------------|
| `min_notice_days` | int | Preavviso minimo richiesto |
| `max_consecutive_days` | int | Max giorni per singola richiesta |
| `max_per_month` | int | Limite mensile (es. L.104) |
| `allow_past_dates` | bool | Ammette date passate (solo malattia) |
| `allow_negative_balance` | bool | Ammette scoperto saldo |
| `requires_attachment` | bool | Allegato obbligatorio |
| `requires_protocol` | bool | Protocollo INPS obbligatorio |

---

## Tipi Assenza Standard

| Codice | Nome | Preavviso | Max gg | Saldo | Approvazione |
|--------|------|-----------|--------|-------|--------------|
| FER | Ferie | 5gg | 15 | vacation | Sì |
| ROL | ROL | 2gg | - | rol | Sì |
| PER | Permessi | - | - | permits | Sì |
| MAL | Malattia | 0 | - | - | No (presa d'atto) |
| LUT | Lutto | - | 3 | - | Sì |
| MAT | Matrimonio | 15gg | 15 | - | Sì |
| L104 | Legge 104 | - | 3/mese | - | Sì |
| DON | Donazione Sangue | - | 1 | - | No |

---

## Validazioni

```python
class PolicyEngine:
    async def validate_request(
        self,
        user_id: UUID,
        leave_type: LeaveType,
        start_date: date,
        end_date: date,
    ) -> None:
        """Esegue tutte le validazioni policy."""
        
        # 1. Date valide
        if start_date > end_date:
            raise ValidationError("Data inizio > data fine")
        
        # 2. Preavviso minimo
        if leave_type.min_notice_days:
            min_start = date.today() + timedelta(days=leave_type.min_notice_days)
            if start_date < min_start:
                raise ValidationError(
                    f"Preavviso minimo {leave_type.min_notice_days} giorni"
                )
        
        # 3. Max giorni consecutivi
        if leave_type.max_consecutive_days:
            days = (end_date - start_date).days + 1
            if days > leave_type.max_consecutive_days:
                raise ValidationError(
                    f"Max {leave_type.max_consecutive_days} giorni"
                )
        
        # 4. Date passate
        if start_date < date.today() and not leave_type.allow_past_dates:
            raise ValidationError("Date passate non ammesse")
        
        # 5. Limite mensile
        if leave_type.max_per_month:
            used = await self._get_monthly_usage(user_id, leave_type.id, start_date)
            if used + days > leave_type.max_per_month:
                raise ValidationError(
                    f"Limite mensile {leave_type.max_per_month} superato"
                )
```

---

## Condizioni Approvazione

| Codice | Condizione | Descrizione |
|--------|------------|-------------|
| RIC | Riserva Richiamo | Azienda può richiamare |
| REP | Reperibilità | Dipendente reperibile |
| PAR | Parziale | Solo parte giorni approvata |
| MOD | Modifica Date | Date diverse da richiesta |
| ALT | Altra | Condizione custom |

---

## Workflow Stati

```
DRAFT → PENDING → APPROVED → COMPLETED
           ↓           ↓
       REJECTED    CANCELLED
                       ↓
                   RECALLED
```

---

## Calcolo Giorni Lavorativi

```python
async def calculate_working_days(
    user_id: UUID,
    start_date: date,
    end_date: date,
) -> Decimal:
    """Calcola giorni/ore lavorativi escludendo festivi e weekend."""
    
    user = await get_user(user_id)
    schedule = user.work_schedule
    holidays = await get_holidays(start_date.year, user.location_id)
    
    working_hours = Decimal(0)
    current = start_date
    
    while current <= end_date:
        # Skip festivi
        if current in holidays:
            current += timedelta(days=1)
            continue
        
        # Ore per giorno da profilo orario
        day_hours = getattr(schedule, f"{current.strftime('%A').lower()}_hours")
        working_hours += Decimal(day_hours)
        
        current += timedelta(days=1)
    
    return working_hours
```
