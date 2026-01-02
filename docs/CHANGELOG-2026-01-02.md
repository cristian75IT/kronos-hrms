# KRONOS HRMS - Changelog 2026-01-02

## Sessione di Sviluppo: Restyling Calendari e Business Configurations

Data: 2 Gennaio 2026

---

## 📅 Restyling System Calendars (MAJOR UI)

### Problema
La gestione delle festività e chiusure era puramente testuale e poco intuitiva per un amministratore HR che deve pianificare l'intero anno.

### Soluzione Implementata
Ridisegnata completamente la pagina `SystemCalendarsPage.tsx` con un approccio "Dashboard-first":
- **Dashboard Statistica**: 4 card per il monitoraggio immediato di Festività (Nazionali/Locali), Chiusure ed Eccezioni.
- **Dual View Mode**:
  - **Vista Lista**: Ottimizzata per l'editing rapido.
  - **Vista Griglia (Month-by-month)**: Nuova visualizzazione per il controllo della distribuzione temporale degli eventi.
- **UX Migliorata**:
  - Badge dinamici sulle Tab per visualizzare i conteggi.
  - Toolbar semplificata con azioni contestuali.
  - Micro-animazioni sugli stati hover e transizioni.

---

## ⚙️ Config Service & Missing Keys

### Problema
Rilevati errori `404 Not Found` nel caricamento di alcune configurazioni critiche (es. `leaves.block_insufficient_balance`), che impedivano il corretto funzionamento della validazione policy nel Leave Service.

### Soluzione Implementata
- **Migrazione Database**: Creata migrazione `024_add_missing_business_configs.py` per popolare la tabella `config.system_config`.
- **Nuove Chiavi Aggiunte**:
  - `leaves.block_insufficient_balance` (Boolean): Blocca invio richieste se saldo insufficiente.
  - `notify_leave_request`, `notify_leave_approval` (Boolean): Flag per il motore di notifica.
  - `notify_wallet_expiry` (Boolean): Avviso scadenza ferie AP.
  - `push_approvals` (Boolean): Abilitazione push notifications per approvazioni.
- **Cache Invalidation**: Corretta la procedura di svuotamento cache via API (porta `8004`).

---

## 🧠 Logica Eccezioni Giornaliere

### Punto Chiave
Chiarita e documentata la gestione delle `working_day_exceptions`:
- **Giorno Lavorativo (Working)**: Sovrascrive il weekend, permettendo al sistema di scalare i saldi se vengono inserite ferie in questi giorni (es. Sabati di recupero).
- **Giorno Non Lavorativo (Non-Working)**: Sovrascrive i giorni feriali (es. Ponti offerti dall'azienda), impedendo al sistema di scalare i saldi ferie.
- **Integrazione**: La logica è centralizzata in `CalendarService` e utilizzata correttamente da `LeaveService` per il calcolo dei giorni richiesti.

---

## 📝 Documentazione Aggiornata

- `DOC_PROGETTO_CALENDAR.md`: Aggiornata con le nuove funzionalità UI e la logica delle eccezioni.
- `docs/modules/config.md`: Incluse le nuove chiavi di configurazione di sistema.
- Creato questo Changelog (`docs/CHANGELOG-2026-01-02.md`).

---

## 🧪 Testing Consigliato

1. **Dashboard Calendari**: Verificare che i conteggi nelle card e nelle tab siano corretti.
2. **Cambio Anno**: Verificare che le statistiche si aggiornino correttamente al variare dell'anno selezionato.
3. **Validazione Saldo**: Verificare che `leaves.block_insufficient_balance` funzioni correttamente (se `true`, impedisce l'invio).
4. **Eccezioni**: Creare un'eccezione lavorativa su un Sabato e verificare che una richiesta di ferie su quel Sabato scali effettivamente 1 giorno dal saldo.
