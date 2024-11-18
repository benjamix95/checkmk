# Analisi e Sviluppo del File Monitor Provider

## Indice
1. [Analisi Iniziale](#analisi-iniziale)
2. [Analisi del Sistema Esistente](#analisi-del-sistema-esistente)
3. [Decisioni di Design](#decisioni-di-design)
4. [Modifiche Effettuate](#modifiche-effettuate)
5. [Analisi dei Componenti](#analisi-dei-componenti)

## Analisi Iniziale

### Requisiti del Progetto
1. Monitoraggio di file e cartelle su Windows
2. Notifiche al sistema esistente
3. Eliminazione automatica dei file
4. Controllo periodico
5. Integrazione con CheckMK

### Analisi delle Funzionalità Richieste
1. **Monitoraggio File**
   - Monitoraggio di file specifici
   - Supporto per pattern glob
   - Monitoraggio ricorsivo
   - Gestione dei permessi

2. **Sistema di Notifiche**
   - Integrazione con CheckMK
   - Notifiche per file trovati
   - Notifiche per file eliminati
   - Log delle operazioni

3. **Gestione File**
   - Eliminazione automatica
   - Verifica dei permessi
   - Gestione errori
   - Logging delle operazioni

## Analisi del Sistema Esistente

### 1. Struttura dei Provider
Ho analizzato il sistema dei provider esistente in CheckMK:

```cpp
// providers/internal.h
class Basic {
    // Classe base per tutti i provider
    virtual void loadConfig() = 0;
    virtual std::string makeBody() = 0;
};

class Synchronous : public Basic {
    // Provider sincrono
    bool startExecution(...);
};

class Asynchronous : public Basic {
    // Provider asincrono
    bool startExecution(...);
    void threadProc(...);
};
```

Questa analisi ha rivelato che:
- I provider possono essere sincroni o asincroni
- Devono implementare loadConfig() e makeBody()
- Utilizzano un sistema di logging comune
- Si integrano con il sistema di notifiche

### 2. Sistema di Configurazione
Analisi del sistema di configurazione YAML:

```cpp
// wnx/cfg.h
namespace cfg {
    YAML::Node GetLoadedConfig();
    template<typename T>
    T GetVal(const std::string& section, 
             const std::string& key, 
             const T& default_value);
}
```

Questo ha mostrato:
- Uso di YAML per la configurazione
- Sistema di configurazione gerarchico
- Supporto per valori di default
- Validazione dei tipi

### 3. Sistema di Notifiche
Analisi del sistema di notifiche:

```cpp
// wnx/logger.h
namespace XLOG {
    void l(const char* fmt, ...);  // Info
    void d(const char* fmt, ...);  // Debug
    void t(const char* fmt, ...);  // Trace
}
```

Caratteristiche chiave:
- Livelli di log multipli
- Integrazione con Event Log di Windows
- Formattazione messaggi
- Rotazione dei log

## Decisioni di Design

### 1. Scelta del Tipo di Provider
```cpp
// Decisione: Utilizzare Synchronous invece di Asynchronous
class FileMonitor final : public Synchronous {
    // Motivazione:
    // 1. Operazioni file sono I/O bound
    // 2. Più semplice gestione degli errori
    // 3. Migliore integrazione con il sistema esistente
};
```

### 2. Struttura della Configurazione
```yaml
# Decisione: Struttura gerarchica per la configurazione
file_monitor:
  # Configurazione globale al livello superiore
  enabled: true
  timeout: 60
  
  # Configurazione dei percorsi in una sottosezione
  paths:
    - path: "..."
      delete: true
      
  # Motivazione:
  # 1. Coerente con altri provider
  # 2. Facile da estendere
  # 3. Chiara separazione delle responsabilità
```

### 3. Gestione degli Errori
```cpp
// Decisione: Uso di RAII e logging dettagliato
class ScopedOperation {
    // RAII per garantire pulizia delle risorse
    ~ScopedOperation() {
        try {
            cleanup();
        } catch (...) {
            XLOG::l.e("Cleanup failed");
        }
    }
};

// Motivazione:
// 1. Gestione robusta degli errori
// 2. Nessuna perdita di risorse
// 3. Logging completo per debug
```

## Modifiche Effettuate

### 1. Creazione dei File Core
```plaintext
include/providers/
  └── file_monitor.h     # Definizione dell'interfaccia
src/engine/providers/
  └── file_monitor.cpp   # Implementazione
test/unit/providers/
  └── test_file_monitor.cpp  # Test unitari
```

Motivazione per ogni file:
- file_monitor.h: Interfaccia pubblica del provider
- file_monitor.cpp: Implementazione separata per migliore manutenibilità
- test_file_monitor.cpp: Test completi per validazione

### 2. Modifiche al Sistema di Build
```cmake
# Aggiunta al CMakeLists.txt
set(PROVIDER_SOURCES
    ${PROVIDER_SOURCES}
    providers/file_monitor.cpp
)

set(PROVIDER_HEADERS
    ${PROVIDER_HEADERS}
    include/providers/file_monitor.h
)
```

Motivazione:
- Integrazione con il sistema di build esistente
- Supporto per test automatici
- Gestione corretta delle dipendenze

### 3. Configurazione di Esempio
```yaml
# Creazione di configurazioni di esempio
file_monitor:
  enabled: true
  paths:
    - path: "C:\\temp\\test.txt"
      delete: true
```

Motivazione:
- Esempio chiaro per gli utenti
- Copertura delle funzionalità principali
- Base per la documentazione

## Analisi dei Componenti

### 1. FileMonitor Class
```cpp
class FileMonitor : public Synchronous {
    // Componenti principali:
    
    // 1. Gestione Configurazione
    void loadConfig() override {
        // Carica configurazione YAML
        // Converte i path
        // Valida i parametri
    }
    
    // 2. Monitoraggio File
    void checkAndNotify() {
        // Scansiona i file
        // Applica i pattern
        // Gestisce le notifiche
    }
    
    // 3. Output
    std::string makeBody() override {
        // Genera output per CheckMK
        // Formatta i risultati
        // Aggiunge metadati
    }
};
```

Analisi delle responsabilità:
1. Configurazione
   - Parsing YAML
   - Validazione input
   - Conversione path

2. Monitoraggio
   - Scansione filesystem
   - Pattern matching
   - Gestione errori

3. Output
   - Formattazione dati
   - Integrazione CheckMK
   - Logging

### 2. Sistema di Pattern Matching
```cpp
// Evoluzione del sistema di matching
// Versione 1: Semplice exact match
bool matchFile(const path& p) {
    return p == target_;
}

// Versione 2: Basic glob
bool matchFile(const path& p) {
    return GlobMatch(pattern_, p);
}

// Versione 3: Full featured
bool matchFile(const path& p) {
    if (!matchesPattern(p)) return false;
    if (!checkSize(p)) return false;
    if (!checkPermissions(p)) return false;
    return true;
}
```

Motivazioni dell'evoluzione:
1. Inizialmente solo match esatto
2. Aggiunto supporto glob per flessibilità
3. Sistema completo per requisiti avanzati

### 3. Sistema di Notifiche
```cpp
// Evoluzione del sistema di notifiche
// Fase 1: Log semplice
void notify(const std::string& msg) {
    XLOG::l(msg);
}

// Fase 2: Integrazione CheckMK
void notify(const std::string& msg) {
    XLOG::l(msg);
    sendToCheckMK(msg);
}

// Fase 3: Sistema completo
void notify(const Notification& n) {
    // Log locale
    XLOG::l(n.message);
    
    // CheckMK
    if (n.level >= NotificationLevel::Warning) {
        sendToCheckMK(n);
    }
    
    // Event Log
    if (n.level >= NotificationLevel::Error) {
        logToEventLog(n);
    }
}
```

Analisi dell'evoluzione:
1. Sistema base per debugging
2. Integrazione con monitoring
3. Sistema completo multi-livello

### 4. Gestione File
```cpp
// Evoluzione della gestione file
// Versione 1: Operazioni base
void handleFile(const path& p) {
    if (shouldDelete(p)) {
        deleteFile(p);
    }
}

// Versione 2: Con error handling
void handleFile(const path& p) {
    try {
        if (shouldDelete(p)) {
            ScopedOperation op(p);
            deleteFile(p);
        }
    } catch (const fs::error& e) {
        XLOG::l.e("File error: {}", e.what());
    }
}

// Versione 3: Sistema completo
void handleFile(const path& p) {
    FileContext ctx(p);
    
    if (!ctx.checkAccess()) {
        notify(AccessDenied{p});
        return;
    }
    
    if (!ctx.checkConditions()) {
        notify(ConditionsFailed{p});
        return;
    }
    
    try {
        ScopedOperation op(ctx);
        executeAction(ctx);
        notify(ActionSuccess{p});
    } catch (const Exception& e) {
        notify(ActionFailed{p, e});
    }
}
```

Analisi dell'evoluzione:
1. Operazioni file di base
2. Aggiunta gestione errori
3. Sistema completo con contesto

### 5. Testing Strategy
```cpp
// Evoluzione dei test
// Fase 1: Test base
TEST(FileMonitor, BasicTest) {
    FileMonitor fm;
    EXPECT_TRUE(fm.init());
}

// Fase 2: Test funzionali
TEST_F(FileMonitorTest, FileOperations) {
    createTestFiles();
    monitor_.scan();
    EXPECT_TRUE(fileWasFound());
}

// Fase 3: Test completi
class FileMonitorTest : public ::testing::Test {
    void SetUp() override {
        setupTestEnvironment();
        createTestFiles();
        loadTestConfig();
    }
    
    void TearDown() override {
        cleanupTestFiles();
    }
};

TEST_F(FileMonitorTest, ComplexOperations) {
    // Test pattern matching
    EXPECT_TRUE(monitor_.matchesPattern("test.txt"));
    
    // Test file operations
    EXPECT_TRUE(monitor_.handleFile(testFile()));
    
    // Test notifications
    EXPECT_EQ(getNotifications().size(), 1);
}
```

Analisi dell'evoluzione dei test:
1. Test unitari base
2. Aggiunta test funzionali
3. Suite completa con fixtures

## Conclusioni

L'analisi ha portato a:
1. Un design robusto e manutenibile
2. Integrazione efficace con CheckMK
3. Sistema estensibile per future modifiche
4. Documentazione completa
5. Test esaustivi

Le scelte implementative sono state guidate da:
1. Requisiti di performance
2. Manutenibilità del codice
3. Integrazione con il sistema esistente
4. Robustezza e gestione errori
5. Facilità d'uso per gli utenti finali
