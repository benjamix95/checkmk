# Documentazione del File Monitor Provider per Check_MK Windows Agent

## Indice
1. [Introduzione](#introduzione)
2. [Funzionalità](#funzionalità)
3. [Configurazione](#configurazione)
4. [Monitoraggio](#monitoraggio)
5. [Notifiche](#notifiche)
6. [Risoluzione Problemi](#risoluzione-problemi)
7. [Manutenzione](#manutenzione)

## Introduzione

Il File Monitor Provider è un componente aggiuntivo per l'agente Windows di Check_MK che fornisce funzionalità avanzate per il monitoraggio e la gestione dei file nel sistema operativo Windows. Questo provider è stato progettato per automatizzare le operazioni di monitoraggio dei file, consentendo agli amministratori di sistema di mantenere sotto controllo file e directory specifici, con la possibilità di eseguire azioni automatiche come l'eliminazione di file temporanei o obsoleti.

## Funzionalità

### Funzionalità Principali
1. Monitoraggio di file e directory specifici
2. Eliminazione automatica di file in base a pattern configurabili
3. Controllo periodico configurabile
4. Monitoraggio in intervalli orari specifici
5. Notifiche integrate con il sistema Check_MK
6. Supporto per pattern di file complessi
7. Gestione delle esclusioni
8. Logging dettagliato delle operazioni

### Caratteristiche Avanzate
1. Monitoraggio ricorsivo delle directory
2. Filtri basati su dimensione dei file
3. Filtri basati su età dei file
4. Pattern di esclusione per proteggere file specifici
5. Integrazione con il registro eventi di Windows
6. Sistema di notifiche multilivello
7. Gestione degli errori robusta
8. Supporto per operazioni concorrenti

## Configurazione

### File di Configurazione
Il provider utilizza un file di configurazione in formato YAML denominato "check_mk_dev_file_monitor.yml". Questo file deve essere posizionato nella directory di configurazione dell'agente Check_MK.

### Struttura della Configurazione

La configurazione è organizzata nelle seguenti sezioni principali:

1. Impostazioni Globali
   - Intervallo di controllo
   - Intervallo orario di monitoraggio
   - Configurazioni di logging
   - Impostazioni delle notifiche

2. Configurazione dei Percorsi
   - Percorsi da monitorare
   - Tipo di monitoraggio (file o directory)
   - Pattern di ricerca
   - Azioni da eseguire
   - Filtri e esclusioni

3. Configurazione del Logging
   - Livello di dettaglio
   - Destinazione dei log
   - Rotazione dei file di log
   - Formato dei messaggi

4. Configurazione delle Notifiche
   - Canali di notifica
   - Livelli di severità
   - Formato dei messaggi
   - Destinatari delle notifiche

### Parametri di Configurazione

1. Intervallo di Controllo
   - Unità: secondi
   - Valore minimo consigliato: 60 secondi
   - Valore predefinito: 300 secondi (5 minuti)
   - Valore massimo consigliato: 3600 secondi (1 ora)

2. Intervallo Orario
   - Formato: 24 ore
   - Ora di inizio: 0-23
   - Ora di fine: 0-23
   - Esempio: 9-17 per orario lavorativo

3. Dimensioni File
   - Unità: bytes
   - 1 Kilobyte = 1024 bytes
   - 1 Megabyte = 1048576 bytes
   - 1 Gigabyte = 1073741824 bytes

4. Età File
   - Unità: secondi
   - 1 ora = 3600 secondi
   - 1 giorno = 86400 secondi
   - 1 settimana = 604800 secondi
   - 30 giorni = 2592000 secondi

## Monitoraggio

### Tipi di Monitoraggio

1. Monitoraggio File Singolo
   - Verifica esistenza file
   - Controllo dimensione
   - Controllo età
   - Applicazione pattern

2. Monitoraggio Directory
   - Scansione contenuto
   - Ricerca ricorsiva
   - Filtri multipli
   - Gestione esclusioni

### Pattern di Ricerca

1. Pattern Base
   - Estensione specifica
   - Prefisso specifico
   - Suffisso specifico
   - Combinazione di criteri

2. Pattern Avanzati
   - Espressioni regolari
   - Pattern numerici
   - Pattern data/ora
   - Pattern compositi

### Azioni Automatiche

1. Eliminazione File
   - Verifica preliminare
   - Backup opzionale
   - Logging operazione
   - Gestione errori

2. Notifiche
   - Generazione evento
   - Invio notifica
   - Aggiornamento log
   - Aggiornamento stato

## Notifiche

### Sistema di Notifiche

1. Registro Eventi Windows
   - Categoria: Applicazione
   - Sorgente: Check_MK File Monitor
   - Livelli: Informazione, Avviso, Errore
   - Dettagli operazione

2. Sistema Check_MK
   - Integrazione nativa
   - Stati: OK, Warning, Critical
   - Metriche performance
   - Dettagli monitoraggio

### Livelli di Severità

1. Informazione (OK)
   - Operazioni normali
   - File trovati
   - Scansioni completate
   - Aggiornamenti stato

2. Avviso (Warning)
   - File eliminati
   - Spazio insufficiente
   - Performance ridotta
   - Errori non critici

3. Errore (Critical)
   - Errori di accesso
   - Operazioni fallite
   - Configurazione invalida
   - Errori di sistema

## Risoluzione Problemi

### Problemi Comuni

1. Accesso File
   - Permessi insufficienti
   - File in uso
   - Path non valido
   - Restrizioni sistema

2. Performance
   - Scansione lenta
   - Utilizzo elevato risorse
   - Timeout operazioni
   - Congestione sistema

3. Configurazione
   - Sintassi non valida
   - Pattern non corretto
   - Parametri invalidi
   - Conflitti impostazioni

### Strumenti Diagnostici

1. Log Sistema
   - Eventi Windows
   - Log applicazione
   - Log debug
   - Trace operazioni

2. Monitoraggio
   - Stato servizio
   - Utilizzo risorse
   - Tempi risposta
   - Code operazioni

## Manutenzione

### Operazioni Periodiche

1. Verifica Log
   - Analisi errori
   - Trend operazioni
   - Spazio utilizzato
   - Rotazione file

2. Ottimizzazione
   - Aggiornamento pattern
   - Tuning performance
   - Pulizia cache
   - Verifica configurazione

3. Backup
   - Configurazione
   - Log storici
   - File eliminati
   - Stato sistema

### Best Practices

1. Sicurezza
   - Verifica permessi
   - Protezione file critici
   - Monitoraggio accessi
   - Backup regolari

2. Performance
   - Ottimizzazione pattern
   - Gestione intervalli
   - Limitazione ricorsione
   - Monitoraggio risorse

3. Manutenzione
   - Aggiornamenti regolari
   - Verifica integrità
   - Pulizia periodica
   - Documentazione modifiche

## Supporto e Assistenza

### Canali di Supporto

1. Documentazione
   - Manuale utente
   - Guide tecniche
   - FAQ
   - Knowledge base

2. Supporto Tecnico
   - Email supporto
   - Portal web
   - Telefono
   - Chat tecnica

### Procedure di Escalation

1. Livello 1
   - Problemi base
   - Configurazione
   - Domande generali
   - Assistenza utente

2. Livello 2
   - Problemi tecnici
   - Performance
   - Integrazioni
   - Personalizzazioni

3. Livello 3
   - Problemi critici
   - Bug sistema
   - Sviluppo soluzioni
   - Consulenza avanzata
