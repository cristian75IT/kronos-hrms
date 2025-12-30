# Compliance Normativa Italiana

## Riferimenti Normativi

- **Art. 36 Costituzione**: Diritto irrinunciabile alle ferie retribuite
- **D.Lgs. 66/2003** (Art. 10): Disciplina orario di lavoro e ferie
- **Art. 2109 C.C.**: Diritto di richiamo dalle ferie
- **CCNL di Riferimento**: Regole specifiche per settore

---

## Regole D.Lgs 66/2003 Art.10

| Regola | Descrizione | Implementazione |
|--------|-------------|-----------------|
| **Minimo 4 settimane/anno** | Monte ferie annuo non inferiore a 4 settimane | Config: `compliance.vacation_min_days_year = 20` |
| **2 settimane consecutive** | Almeno 2 settimane da fruire consecutivamente | Alert se a fine anno non fruite |
| **Fruizione nell'anno** | 2 settimane nell'anno di maturazione | Alert automatico Nov/Dic |
| **Residuo entro 18 mesi** | Restanti 2 settimane entro 18 mesi | Tracciamento scadenza AP |
| **Non monetizzabilità** | Ferie non pagabili (salvo cessazione) | No eliminazione saldi |
| **Irrinunciabilità** | Dipendente non può rinunciare | No cancellazione forzata |

---

## Alert Automatici Compliance

| Alert | Trigger | Destinatario |
|-------|---------|--------------|
| Ferie AP in scadenza | 60gg prima scadenza 18 mesi | Dipendente + HR |
| Obbligo 2 settimane | 1 Novembre | Dipendente + Manager |
| Saldo elevato | Residuo > 30gg a fine anno | HR |
| Ferie non pianificate | Nessuna ferie nei prossimi 3 mesi | Manager |

---

## Diritto di Richiamo (Art. 2109 C.C.)

L'azienda può richiamare il dipendente per **esigenze aziendali eccezionali**:

1. Esigenza documentabile
2. Dipendente informato preventivamente (condizione RIC)
3. Rimborso spese sostenute obbligatorio
4. Giorni non goduti riaccreditati

**Workflow Richiamo:**
1. HR imposta `is_recalled = true` + `recall_reason`
2. Sistema calcola giorni da riaccreditare
3. Sistema crea ExpenseReport per rimborsi
4. Notifica al dipendente

---

## Gestione Saldi (Balances)

### Logica FIFO per Ferie

```python
async def deduct_vacation(user_id: UUID, hours: Decimal) -> None:
    """Scala prima da AP (anno precedente), poi da AC (anno corrente)."""
    balance = await get_balance(user_id, current_year)
    
    # Prima erodi AP
    if balance.vacation_previous_year > 0:
        from_ap = min(hours, balance.vacation_previous_year)
        hours -= from_ap
        balance.vacation_previous_year -= from_ap
    
    # Poi erodi AC
    if hours > 0:
        balance.vacation_used += hours
```

### Scadenza Residuo AP

```python
async def check_ap_expiry() -> list[Alert]:
    """Job mensile per verificare scadenze AP."""
    expiry_months = await config.get("compliance.vacation_ap_expiry_months", 18)
    alert_days = await config.get("compliance.alert_days_before_expiry", 60)
    
    # Trova utenti con AP in scadenza
    expiry_date = date.today() - timedelta(days=expiry_months * 30)
    users_at_risk = await get_users_with_ap_hired_before(expiry_date)
    
    return [
        Alert(user_id=u.id, type="AP_EXPIRING", days_remaining=...)
        for u in users_at_risk
    ]
```

---

## Piano Ferie Annuale (Best Practice)

| Periodo | Attività |
|---------|----------|
| Gennaio-Febbraio | HR sollecita piano ferie annuale |
| Marzo | Responsabili validano piano team |
| Trimestrale | Dashboard: fruizione vs pianificato |
| Novembre-Dicembre | Alert automatici saldi elevati |
