# Documento di Progetto: Integrazione Wallet Microservices

## 1. Visione Architetturale
Il sistema KRONOS utilizza un'architettura a microservizi. Recentemente è stata introdotta una gestione centralizzata dei **Wallet** (portafogli) per gestire diverse entità finanziarie e di saldo:

- **Leaves Wallet (Time Wallet)**: Gestisce i saldi di Ferie, ROL e Permessi.
- **Expensive Wallet (Trip Wallet)**: Gestisce i budget e le spese legate alle trasferte aziendali.

### Scelta dello Schema e Naming Convention
Per ottimizzare la gestione dei dati e ridurre la frammentazione del database, è stata presa la decisione architetturale di **unificare entrambi i servizi sotto lo schema `wallet`**.

#### Razionale dei Nomi:
- **Schema `wallet`**: Scelto come contenitore unico per tutte le entità che gestiscono "saldi" (siano essi di tempo o di denaro). Questo semplifica le query di reporting cross-servizio.
- **Tabella `employee_wallets`**: Nonostante sia gestita dal microservizio `leaves_wallet`, si è scelto un nome più generico rispetto a `leaves_wallets`. Questo perché la tabella rappresenta il "portafoglio principale" del dipendente, che in futuro potrà ospitare altri tipi di residui (es. welfare aziendale, fringe benefits, banca ore) che non sono strettamente definibili come "leaves" (assenze). Si è data priorità all'**entità** (il dipendente e i suoi saldi fissi) piuttosto che al singolo **servizio** che la gestisce oggi.
- **Tabella `trip_wallets`**: Identifica chiaramente i portafogli transitori legati alle singole trasferte, mantenendo una netta separazione logica dai saldi annuali del dipendente.

## 2. Stato dell'Implementazione

### Migrazioni Database (Alembic)
Sono stati risolti i conflitti nelle migrazioni che impedivano l'avvio pulito dell'ambiente:
- **019_add_trip_wallets**: Crea le tabelle per il servizio `expensive_wallet` e assicura che la tabella `employee_wallets` contenga tutte le colonne richieste dal modello SQLAlchemy (aggiunte colonne: `legal_minimum_required`, `legal_minimum_taken`, `hourly_rate_snapshot`, `status`).
- **020_seed_wallet_data**: Popolamento iniziale per test e sviluppo.

### Correzioni Critiche Effettuate
1.  **Sincronizzazione Modelli/Database**: Allineati i modelli SQLAlchemy di `leaves_wallet` per puntare allo schema `wallet`.
2.  **Integrità Dati (Users)**: Corretto il seed degli utenti per includere la colonna `is_synced`, necessaria per soddisfare i vincoli NOT NULL.
3.  **Recupero Colonne Mancanti**: Ripristinate le colonne di compliance europea (`legal_minimum_required`) che erano state accidentalmente omesse durante la ristrutturazione delle migrazioni.

## 3. Guida al Ripristino Ambiente
Per applicare correttamente queste modifiche e avere un ambiente allineato, eseguire:

```bash
./rebuild.sh
```

Questo comando provvederà a:
1. Ricostruire i container.
2. Inizializzare gli schemi.
3. Applicare le migrazioni in ordine cronologico.
4. Caricare i dati di seed per testare immediatamente la `TripDetailPage` e il riepilogo saldi.

## 4. Prossimi Passi
- Verificare la corretta visualizzazione del widget budget nella `TripDetailPage`.
- Testare il processo di maturazione mensile (accrual) nel servizio portafoglio ore.
