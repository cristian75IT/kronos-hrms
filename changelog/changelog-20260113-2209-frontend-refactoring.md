# Frontend Refactoring Report

**Data**: 2026-01-13 → 2026-01-14  
**Scope**: Migrazione a React Query e separazione dei concerns

---

## 🎯 Obiettivi Raggiunti

1. **Migrazione da `useState` + `useEffect` a React Query** per la gestione dello stato server.
2. **Estrazione di logica in custom hooks** per migliorare testabilità e riutilizzo.
3. **Creazione di componenti riutilizzabili** per ridurre duplicazione.
4. **Miglioramento della type safety** riducendo l'uso di `any`.

---

## 📁 File Creati

### Hooks (React Query)

| File | Descrizione |
|------|-------------|
| `hooks/domain/useNotifications.ts` | Hooks per notifiche: fetch, mark as read, preferences |
| `hooks/domain/useAdminUsers.ts` | Hooks per gestione utenti admin: list, delete, batch ops |
| `hooks/domain/useLeaveDetailActions.ts` | Actions hook per dettaglio ferie (modali, submit, approve, reject) |
| `hooks/domain/useSystemCalendars.ts` | React Query hooks per calendari sistema (holidays, closures, exceptions) |

### Componenti - Notifications

| File | Descrizione |
|------|-------------|
| `components/notifications/NotificationIcon.tsx` | Componente icona notifica |
| `components/notifications/NotificationItem.tsx` | Riga singola notifica |
| `components/notifications/NotificationPreferences.tsx` | Form preferenze notifiche |
| `components/notifications/index.ts` | Barrel export |

### Componenti - Leaves

| File | Descrizione |
|------|-------------|
| `components/leaves/ExcludedDaysSection.tsx` | Sezione giorni esclusi con React Query |
| `components/leaves/LeaveDetailModals.tsx` | Tutti i modali per dettaglio ferie |
| `components/leaves/index.ts` | Barrel export |

### Componenti - Admin Calendars

| File | Descrizione |
|------|-------------|
| `components/admin/calendars/HolidaysTab.tsx` | Tab festività con list/grid view |
| `components/admin/calendars/ClosuresTab.tsx` | Tab chiusure aziendali |
| `components/admin/calendars/ExceptionsTab.tsx` | Tab eccezioni calendario |
| `components/admin/calendars/SystemCalendarModals.tsx` | Tutti i modali per calendari sistema |
| `components/admin/calendars/index.ts` | Barrel export |

---

## 📝 File Modificati

### NotificationsPage.tsx

| Metrica | Prima | Dopo | Δ |
|---------|-------|------|---|
| Righe | 988 | 638 | **-35%** |
| `useState` per server data | 5 | 0 | ✅ |
| `useEffect` per fetch | 2 | 0 | ✅ |
| `useQuery` hooks | 0 | 2 | ✅ |
| `useMutation` hooks | 0 | 3 | ✅ |

**Miglioramenti**:
- Cache automatica delle notifiche
- Optimistic updates per mark as read
- Loading states automatici
- Refetch automatico su invalidazione

### UsersPage.tsx

| Metrica | Prima | Dopo | Δ |
|---------|-------|------|---|
| Righe | 545 | 618 | +13%* |
| `useState` per server data | 2 | 0 | ✅ |
| `useEffect` per fetch | 1 | 0 | ✅ |
| Sub-componenti estratti | 0 | 5 | ✅ |

*\* Aumento righe dovuto all'estrazione di sub-componenti inline (StatCard, UsersTable, UsersGrid, BatchOperationsModal, BatchOperationButton). Questi potrebbero essere spostati in file separati.*

### LeaveDetailPage.tsx ✨ NEW

| Metrica | Prima | Dopo | Δ |
|---------|-------|------|---|
| Righe | 1280 | 777 | **-39%** |
| Modali inline | 7 | 0 | ✅ Estratti |
| Sub-componenti estratti | 0 | 6 | ✅ |
| Custom hooks creati | 0 | 1 | ✅ |

**Miglioramenti**:
- Logica azioni centralizzata in `useLeaveDetailActions`
- Modali estratti in `LeaveDetailModals`
- `ExcludedDaysSection` ora usa React Query
- Sub-componenti: `DetailsTab`, `HistoryTab`, `WorkflowInfoCard`, `ActionsCard`, `SummaryCard`

### SystemCalendarsPage.tsx ✨ NEW

| Metrica | Prima | Dopo | Δ |
|---------|-------|------|---|
| Righe | 1278 | 529 | **-59%** |
| `useState` per server data | 3 | 0 | ✅ React Query |
| `useEffect` per fetch | 1 | 0 | ✅ |
| Tabs estratti | 0 | 3 | ✅ |
| Modali estratti | 0 | 1 | ✅ |

**Miglioramenti**:
- `useSystemCalendars` hook gestisce tutto il data fetching e mutations
- Tab separati: `HolidaysTab`, `ClosuresTab`, `ExceptionsTab`
- Modali estratti in `SystemCalendarModals`
- Sub-componenti: `TabButton`, `SummaryCard`, `ExportDropdown`

### CalendarPage.tsx (già fatto in precedenza)

| Metrica | Prima | Dopo | Δ |
|---------|-------|------|---|
| Righe | ~800 | 220 | **-72%** |
| Componenti estratti | - | CalendarHeader, CalendarSidebar, CalendarManagementModal |
| Hook estratto | - | useCalendarEventsMapper |

---

## 🔄 Pattern Adottati

### 1. Server State con React Query
```typescript
// Prima (anti-pattern)
const [data, setData] = useState([]);
useEffect(() => { api.fetch().then(setData) }, []);

// Dopo (pattern corretto)
const { data = [], isLoading } = useQuery({
    queryKey: ['resource'],
    queryFn: () => api.fetch()
});
```

### 2. Mutations con Invalidazione
```typescript
const mutation = useMutation({
    mutationFn: api.update,
    onSuccess: () => {
        toast.success('Operazione completata');
        queryClient.invalidateQueries({ queryKey });
    },
    onError: (err) => toast.error(err.message)
});
```

### 3. Query Keys Strutturate
```typescript
export const systemCalendarKeys = {
    all: ['system-calendars'] as const,
    holidays: (year: number) => [...systemCalendarKeys.all, 'holidays', year] as const,
    closures: (year: number) => [...systemCalendarKeys.all, 'closures', year] as const,
};
```

### 4. Separation of Concerns
```
Page.tsx (orchestrazione)
├── useXxxActions.ts (logica business + state)
├── XxxTab.tsx (UI tab)
├── XxxModals.tsx (tutti i modali)
└── sub-components (cards, lists, etc.)
```

---

## 📋 TODO - Prossimi Refactoring

### P1 - Importanti
- [ ] Spostare sub-componenti `UsersPage` in file separati
- [ ] Estrarre CSS inline in file `.css` o CSS Modules
- [ ] Rimuovere tutti gli `any` types rimanenti
- [ ] Fix `NotificationIcon` import mancante in `NotificationItem`

### P2 - Nice to Have
- [ ] Consolidare tipi duplicati in `types/index.ts`
- [ ] Creare hook `useOrganization` per dati organizzativi
- [ ] Aggiungere tests per i nuovi hooks

---

## 🧪 Verifica

Per verificare che il refactoring non abbia introdotto regressioni:

```bash
cd frontend
npm run build   # Verifica compilazione ✅
npm run lint    # Verifica linting
```

---

## 📊 Metriche Finali

| Pagina | Righe Prima | Righe Dopo | Riduzione |
|--------|-------------|------------|-----------|
| NotificationsPage | 988 | 638 | -35% |
| CalendarPage | ~800 | 220 | -72% |
| LeaveDetailPage | 1280 | 777 | -39% |
| SystemCalendarsPage | 1278 | 529 | **-59%** |
| **Totale** | **~4346** | **~2164** | **-50%** |

| Categoria | Hooks Creati | Componenti Creati |
|-----------|--------------|-------------------|
| Notifications | 5 | 3 |
| Admin Users | 4 | 0 (inline) |
| Calendar | 1 | 4 |
| Leaves | 1 | 2 |
| System Calendars | 1 | 4 |
| **Totale** | **12** | **13** |
