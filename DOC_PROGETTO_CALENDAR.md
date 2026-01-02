# Documento di Progetto: Calendar Microservice

## 1. Visione Architetturale

Il **Calendar Service** è un microservizio dedicato alla gestione centralizzata di tutti gli eventi temporali nel sistema KRONOS HR. Nasce dalla necessità di avere un'unica fonte di verità per le query temporali e per il calcolo dei giorni lavorativi.

### Migrazione
Le seguenti entità sono state migrate dallo schema `config`:
- **holidays** → `calendar.holidays`
- **company_closures** → `calendar.closures`

La migrazione `021_create_calendar_schema.py` copia automaticamente i dati esistenti.

---

## 2. Schema Database: `calendar`

| Tabella | Descrizione |
|---------|-------------|
| `holidays` | Festività nazionali, regionali, locali e aziendali |
| `closures` | Chiusure aziendali (totali o parziali) |
| `events` | Eventi generici (meeting, reminder, training) |
| `event_participants` | Partecipanti agli eventi con stato risposta |
| `working_day_exceptions` | Eccezioni ai giorni lavorativi standard |

---

## 3. API Endpoints

### Holidays
| Metodo | Endpoint | Descrizione |
|--------|----------|-------------|
| GET | `/api/v1/holidays` | Lista festività con filtri |
| GET | `/api/v1/holidays/{id}` | Dettaglio festività |
| POST | `/api/v1/holidays` | Crea festività (admin) |
| PUT | `/api/v1/holidays/{id}` | Modifica festività (admin) |
| DELETE | `/api/v1/holidays/{id}` | Elimina festività (admin) |

### Closures
| Metodo | Endpoint | Descrizione |
|--------|----------|-------------|
| GET | `/api/v1/closures` | Lista chiusure |
| GET | `/api/v1/closures/{id}` | Dettaglio chiusura |
| POST | `/api/v1/closures` | Crea chiusura (admin) |
| PUT | `/api/v1/closures/{id}` | Modifica chiusura (admin) |
| DELETE | `/api/v1/closures/{id}` | Elimina chiusura (admin) |

### Events
| Metodo | Endpoint | Descrizione |
|--------|----------|-------------|
| GET | `/api/v1/events` | Lista eventi dell'utente |
| GET | `/api/v1/events/{id}` | Dettaglio evento |
| POST | `/api/v1/events` | Crea evento |
| PUT | `/api/v1/events/{id}` | Modifica evento (solo owner) |
| DELETE | `/api/v1/events/{id}` | Cancella evento (solo owner) |
| POST | `/api/v1/events/{id}/respond` | Rispondi a invito |

### Calendar Views
| Metodo | Endpoint | Descrizione |
|--------|----------|-------------|
| GET | `/api/v1/calendar/range` | Vista aggregata per range di date |
| GET | `/api/v1/calendar/date/{date}` | Info su data specifica |
| POST | `/api/v1/calendar/working-days` | Calcola giorni lavorativi |
| GET | `/api/v1/calendar/working-days/check/{date}` | Verifica se è giorno lavorativo |
| GET | `/api/v1/calendar/exceptions` | Lista eccezioni giorni lavorativi |
| POST | `/api/v1/calendar/exceptions` | Crea eccezione |

---

## 4. Funzionalità Chiave

### Calcolo Giorni Lavorativi
Il servizio calcola i giorni lavorativi considerando:
1. **Weekend** - Configurabile (5 o 6 giorni/settimana)
2. **Festività** - Nazionali, regionali, locali
3. **Chiusure aziendali** - Totali o parziali
4. **Eccezioni** - Giorni speciali (recuperi, emergenze)

### Vista Aggregata
L'endpoint `/api/v1/calendar/range` restituisce una vista unificata che include:
- Festività
- Chiusure aziendali
- Eventi personali
- Informazione su working day per ogni giorno

---

## 5. Configurazione Docker

```yaml
calendar-service:
  container_name: kronos-calendar
  environment:
    - SERVICE_NAME=calendar-service
    - DATABASE_SCHEMA=calendar
    - REDIS_URL=redis://redis:6379/7
  ports:
    - "8009:8009"
```

---

## 6. Integrazione con Altri Servizi

| Servizio | Uso del Calendar Service |
|----------|--------------------------|
| Leave Service | Calcolo giorni lavorativi per richieste ferie |
| Expense Service | Verifica date trasferte vs chiusure |
| Frontend | Visualizzazione calendario unificato |

---

## 7. iCal Export (Implementato ✅)

### Endpoint Export

| Metodo | Endpoint | Descrizione |
|--------|----------|-------------|
| GET | `/api/v1/export/holidays.ics` | Esporta festività come file ICS |
| GET | `/api/v1/export/closures.ics` | Esporta chiusure come file ICS |
| GET | `/api/v1/export/combined.ics` | Esporta calendario completo |
| GET | `/api/v1/export/my-events.ics` | Esporta eventi personali (auth) |
| GET | `/api/v1/export/subscription-url` | URL per abbonamento calendario |

### Parametri

- `year` (required): Anno da esportare
- `scope`: Filter per scope (`national`, `regional`, `local`)
- `include_holidays`: Includi festività (default: true)
- `include_closures`: Includi chiusure (default: true)

### Formato ICS

I file generati sono conformi allo standard RFC 5545 (iCalendar) e includono:

- **VCALENDAR**: Container principale con metadata
- **VEVENT**: Eventi singoli con:
  - UID univoco
  - DTSTART/DTEND
  - SUMMARY (titolo)
  - DESCRIPTION
  - CATEGORIES
  - COLOR (per Apple Calendar)
  - STATUS (CONFIRMED, TENTATIVE, CANCELLED)
  - TRANSP (OPAQUE per impegni, TRANSPARENT per festività)

### Sincronizzazione Esterna

**Google Calendar:**
1. Vai su calendar.google.com
2. Impostazioni → "Aggiungi calendario" → "Da URL"
3. Incolla l'URL: `https://your-domain/api/v1/export/combined.ics?year=2026`

**Microsoft Outlook:**
1. Apri Outlook
2. Calendario → Importa → Abbonati da web
3. Incolla l'URL e conferma

**Apple Calendar (macOS/iOS):**
1. File → Nuovo abbonamento calendario
2. Incolla l'URL
3. Imposta frequenza di aggiornamento

### Frontend

La pagina `/admin/holidays` include un dropdown "Esporta iCal" con:
- Download festività
- Download chiusure
- Download calendario completo

---

## 8. Estensioni Future

1. **Token-based Subscriptions** - URL personalizzati con token per abbonamenti sicuri
2. **Recurring Events** - Supporto RRULE per eventi ricorrenti
3. **Room Booking** - Prenotazione sale riunioni
4. **Shift Planning** - Pianificazione turni
5. **Notifiche Proattive** - Avvisi su giorni speciali imminenti
6. **CalDAV Server** - Supporto completo CalDAV per sincronizzazione bidirezionale
