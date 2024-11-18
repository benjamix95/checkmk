# Guida alla Configurazione dei Parametri del File Monitor

## Indice
1. [Parametri di Configurazione](#parametri-di-configurazione)
2. [Diagramma di Flusso](#diagramma-di-flusso)
3. [Dettagli Tecnici](#dettagli-tecnici)

## Parametri di Configurazione

### 1. Timer e Intervalli
```yaml
file_monitor:
  # Intervallo di controllo principale (in secondi)
  check_interval: 300  # Default: 5 minuti
  
  # Timeout operazioni (in secondi)
  timeout: 60  # Default: 1 minuto
  
  # Tentativi in caso di errore
  retry: 3  # Default: 3 tentativi
  
  # Ritardo tra tentativi (in secondi)
  retry_delay: 5  # Default: 5 secondi

# COME MODIFICARE:
# 1. Aprire: C:\ProgramData\checkmk\config\check_mk.yml
# 2. Trovare la sezione file_monitor
# 3. Modificare i valori desiderati
# 4. Salvare il file
# 5. Riavviare il servizio: net stop/start CheckMKService
```

### 2. Path e Pattern
```yaml
file_monitor:
  paths:
    # File singoli
    - path: "C:\\temp\\test.txt"  # File specifico
      delete: true
    
    # Pattern con wildcard
    - path: "C:\\logs\\*.log"     # Tutti i .log
      delete: true
    
    # Pattern ricorsivi
    - path: "C:\\Users\\**\\*.tmp" # Ricerca ricorsiva
      delete: true
    
    # Pattern multipli
    - path: "C:\\data\\{*.bak,*.tmp}"
      delete: true

# COME MODIFICARE:
# 1. Identificare il tipo di path necessario
# 2. Usare la sintassi corretta:
#    - File singolo: percorso esatto
#    - Wildcard: * per qualsiasi carattere
#    - Ricorsivo: ** per sottodirectory
#    - Multipli: {pattern1,pattern2}
```

### 3. Estensioni e Nomi File
```yaml
file_monitor:
  paths:
    # Per estensione
    - path: "C:\\temp\\*.{txt,log,tmp}"
      delete: true
    
    # Per nome parziale
    - path: "C:\\temp\\backup_*.*"
      delete: true
    
    # Combinazione nome ed estensione
    - path: "C:\\temp\\test_*.{bak,tmp}"
      delete: true
    
    # Esclusioni
    - path: "C:\\temp\\*.*"
      delete: true
      exclude: ["*.keep", "important*"]

# COME MODIFICARE:
# 1. Identificare il pattern necessario
# 2. Usare la sintassi appropriata:
#    - Estensioni: *.ext
#    - Nomi parziali: nome*
#    - Esclusioni: exclude: [pattern]
```

## Diagramma di Flusso

```plaintext
┌─────────────────┐
│  Inizio Ciclo   │
│   Monitoraggio  │
└────────┬────────┘
         │
         ▼
┌─────────────────┐
│  Leggi Config   │◄────────────────┐
│   check_mk.yml  │                 │
└────────┬────────┘                 │
         │                          │
         ▼                          │
┌─────────────────┐                 │
│  Per Ogni Path  │                 │
│  Configurato    │                 │
└────────┬────────┘                 │
         │                          │
         ▼                          │
┌─────────────────┐                 │
│ Match Pattern   │                 │
│    con Path     │                 │
└────────┬────────┘                 │
         │                          │
         ▼                          │
┌─────────────────┐     No          │
│  File Trovato?  ├─────────────────┘
└────────┬────────┘
         │ Sì
         ▼
┌─────────────────┐
│  Applica Filtri │
│   ed Esclusioni │
└────────┬────────┘
         │
         ▼
┌─────────────────┐     No
│ Delete = true?  ├─────┐
└────────┬────────┘     │
         │ Sì           │
         ▼              ▼
┌─────────────────┐  ┌──────────────┐
│  Elimina File   │  │ Solo Notifica│
└────────┬────────┘  └──────┬───────┘
         │                  │ No
         ▼                  │
┌─────────────────┐         │
│    Notifica     │◄────────┘
│   Operazione    │
└────────┬────────┘
         │
         ▼
┌─────────────────┐     No
│Tutti Path       ├─────────────┐
│Processati?      │             │
└────────┬────────┘             │
         │ Sì                   │
         ▼                      │
┌─────────────────┐             │
│  Attendi        │             │
│check_interval   │             │
└────────┬────────┘             │
         │                      │
         ▼                      │   
│check_interval   │             │
└────────┬────────┘             │
         │                      │
         ▼                      │
┌─────────────────┐             │
│ Aggiorna Cache  │             │
└────────┬────────┘             │
         │                      │
         └───────────────────────┘
```

## Dettagli Tecnici

### 1. Struttura Interna Timer
```cpp
class FileMonitor {
private:
    // Timer configuration
    struct TimerConfig {
        std::chrono::seconds check_interval;
        std::chrono::seconds timeout;
        int retry_count;
        std::chrono::seconds retry_delay;
    };
    
    TimerConfig timer_config_;
    
    // Timer implementation
    void startMonitoring() {
        while (!stop_requested_) {
            processAllPaths();
            std::this_thread::sleep_for(
                timer_config_.check_interval);
        }
    }
};

// COME FUNZIONA:
// 1. check_interval: Tempo tra scansioni
// 2. timeout: Tempo massimo per operazione
// 3. retry_count: Tentativi su errore
// 4. retry_delay: Attesa tra tentativi
```

### 2. Pattern Matching Engine
```cpp
class FileMonitor {
private:
    // Pattern configuration
    struct PathPattern {
        fs::path base_path;
        std::string pattern;
        bool recursive;
        std::vector<std::string> exclude;
    };
    
    // Pattern matching
    bool matchesPattern(
        const fs::path& file,
        const PathPattern& pattern) {
        
        // 1. Base path check
        if (!file.has_prefix(pattern.base_path))
            return false;
            
        // 2. Pattern match
        if (!glob_match(pattern.pattern, 
                       file.filename()))
            return false;
            
        // 3. Exclusion check
        for (const auto& excl : pattern.exclude) {
            if (glob_match(excl, file.filename()))
                return false;
        }
        
        return true;
    }
};

// COME FUNZIONA:
// 1. Verifica path base
// 2. Match pattern globale
// 3. Verifica esclusioni
```

### 3. File Operations
```cpp
class FileMonitor {
private:
    // File operation result
    struct OperationResult {
        bool success;
        std::string error;
        std::chrono::milliseconds duration;
    };
    
    // File deletion with retry
    OperationResult deleteFile(
        const fs::path& path) {
        
        for (int i = 0; i < timer_config_.retry_count; ++i) {
            try {
                fs::remove(path);
                return {true, "", measure_duration()};
            } catch (const std::exception& e) {
                if (i < timer_config_.retry_count - 1) {
                    std::this_thread::sleep_for(
                        timer_config_.retry_delay);
                    continue;
                }
                return {false, e.what(), measure_duration()};
            }
        }
        return {false, "Max retries exceeded", 
                measure_duration()};
    }
};

// COME FUNZIONA:
// 1. Tentativo eliminazione
// 2. Gestione errori
// 3. Retry automatico
// 4. Misurazione durata
```

### 4. Cache Management
```cpp
class FileMonitor {
private:
    // Cache entry
    struct CacheEntry {
        fs::path path;
        std::filesystem::file_time_type last_check;
        bool was_deleted;
        std::chrono::steady_clock::time_point cache_time;
    };
    
    // Cache operations
    std::unordered_map<std::string, CacheEntry> cache_;
    
    void updateCache(
        const fs::path& path,
        bool deleted) {
        
        auto now = std::chrono::steady_clock::now();
        cache_[path.string()] = {
            path,
            fs::last_write_time(path),
            deleted,
            now
        };
    }
    
    void cleanupCache() {
        auto now = std::chrono::steady_clock::now();
        std::erase_if(cache_, [&](const auto& entry) {
            return (now - entry.second.cache_time) > 
                   timer_config_.check_interval * 2;
        });
    }
};

// COME FUNZIONA:
// 1. Tracking file processati
// 2. Ottimizzazione scansioni
// 3. Pulizia automatica
// 4. Gestione memoria
```

### 5. Notifiche
```cpp
class FileMonitor {
private:
    // Notification types
    enum class NotificationType {
        FileFound,
        FileDeleted,
        Error
    };
    
    // Notification system
    void sendNotification(
        const fs::path& path,
        NotificationType type,
        const std::string& details = "") {
        
        // 1. Create notification
        Notification n{
            .path = path,
            .type = type,
            .details = details,
            .timestamp = std::chrono::system_clock::now()
        };
        
        // 2. Log notification
        XLOG::l("File Monitor: {} - {}", 
                path.string(), details);
        
        // 3. Send to CheckMK
        notifyCheckMK(n);
    }
};

// COME FUNZIONA:
// 1. Creazione notifica
// 2. Logging locale
// 3. Integrazione CheckMK
// 4. Timestamp preciso
