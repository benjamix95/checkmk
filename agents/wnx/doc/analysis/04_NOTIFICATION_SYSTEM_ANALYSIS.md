# Analisi Dettagliata del Sistema di Notifiche e Logging

## 1. Sistema di Logging

### 1.1 XLOG Framework
```cpp
// File: include/wnx/logger.h
namespace XLOG {
    class Logger {
    public:
        enum class Level {
            Trace,
            Debug,
            Info,
            Warning,
            Error,
            Critical
        };
        
        void log(Level level, const char* fmt, ...);
        static Logger& instance();
    };
    
    // Singleton instances
    extern Logger l;  // Info
    extern Logger d;  // Debug
    extern Logger t;  // Trace
}

Analisi dettagliata:
1. Livelli di Log
   - Trace: Debugging dettagliato
   - Debug: Informazioni sviluppo
   - Info: Operazioni normali
   - Warning: Problemi non critici
   - Error: Errori recuperabili
   - Critical: Errori fatali

2. Pattern di Utilizzo
   ```cpp
   // Esempi trovati nel codice
   XLOG::l("Info message");           // Info
   XLOG::d("Debug details");          // Debug
   XLOG::t("Trace data: {}", value);  // Trace
   XLOG::l.e("Error: {}", error);     // Error
   XLOG::l.crit("Critical!");         // Critical
   ```

3. Funzionalità
   - Formattazione fmt
   - Thread safety
   - File rotation
   - Console output
```

### 1.2 Log File Management
```cpp
// File: src/engine/logger.cpp
class LogManager {
private:
    std::ofstream file_;
    std::mutex mutex_;
    size_t max_size_;
    int max_files_;
    
    void rotateFiles();
    void checkSize();
    
public:
    void write(const std::string& message);
};

Analisi implementazione:
1. File Management
   - Rotazione automatica
   - Limiti dimensione
   - Backup files

2. Thread Safety
   - Mutex per scrittura
   - Buffer thread-local
   - Flush periodico

3. Performance
   - Buffer I/O
   - Batch writing
   - Async flush
```

## 2. Sistema di Notifiche

### 2.1 Event System
```cpp
// File: include/wnx/events.h
namespace cma::events {

class Event {
public:
    enum class Type {
        FileFound,
        FileDeleted,
        Error,
        Warning,
        Info
    };
    
    Type type;
    std::string message;
    std::map<std::string, std::string> metadata;
};

class EventSystem {
public:
    void notify(const Event& event);
    void subscribe(EventHandler* handler);
    void unsubscribe(EventHandler* handler);
};

Analisi componenti:
1. Eventi
   - Tipizzati
   - Metadata flessibile
   - Priorità

2. Handlers
   - Subscription based
   - Filtri eventi
   - Async handling
```

### 2.2 CheckMK Notification Integration
```cpp
// File: src/engine/notification.cpp
namespace cma::notification {

class NotificationManager {
private:
    carrier::Carrier carrier_;
    std::queue<Notification> queue_;
    
public:
    void sendNotification(const Notification& n);
    void processQueue();
};

Analisi sistema:
1. Notification Types
   - Service status
   - Performance data
   - Custom messages

2. Routing
   - Priority based
   - Target selection
   - Delivery guarantee
```

## 3. Analisi dei Provider Esistenti

### 3.1 LogWatch Notifications
```cpp
// File: src/engine/providers/logwatch_event.cpp
void LogWatchEvent::notifyMatch(const LogMatch& match) {
    // 1. Create event
    Event event{
        .type = Event::Type::LogMatch,
        .message = match.line,
        .metadata = {
            {"file", match.file},
            {"pattern", match.pattern},
            {"timestamp", match.time}
        }
    };
    
    // 2. Log event
    XLOG::l("Log match: {} in {}", 
            match.pattern, match.file);
    
    // 3. Send notification
    notificationManager_.send(event);
}

Pattern identificati:
1. Event Creation
   - Dati strutturati
   - Metadata completo
   - Timestamp preciso

2. Logging
   - Contesto completo
   - Livello appropriato
   - Formattazione chiara

3. Notification
   - Routing corretto
   - Priority handling
   - Error recovery
```

### 3.2 Process Monitor Notifications
```cpp
// File: src/engine/providers/ps.cpp
void ProcessMonitor::notifyProcessChange(
    const ProcessInfo& proc, 
    ChangeType type) {
    
    // 1. Log change
    XLOG::l("Process {} {}", 
            proc.name,
            toString(type));
    
    // 2. Create notification
    Notification n{
        .level = type == ChangeType::Started 
                 ? Level::Info 
                 : Level::Warning,
        .message = formatMessage(proc, type),
        .context = buildContext(proc)
    };
    
    // 3. Send
    sendNotification(n);
}

Pattern identificati:
1. Logging Context
   - Processo info
   - Tipo cambio
   - Timestamp

2. Notification Levels
   - Based on change
   - Configurabile
   - Default appropriate

3. Context Building
   - Dati rilevanti
   - Formato standard
   - Estensibile
```

## 4. Design per FileMonitor

### 4.1 Logging Strategy
```cpp
class FileMonitor {
private:
    void logFileOperation(
        const fs::path& path, 
        OperationType op) {
        
        // 1. Debug logging
        XLOG::d("File operation {} on {}", 
                toString(op), 
                wtools::ToUtf8(path.wstring()));
        
        // 2. Operation logging
        switch (op) {
            case OperationType::Found:
                XLOG::l("Found file: {}", path);
                break;
            case OperationType::Deleted:
                XLOG::l.w("Deleted file: {}", path);
                break;
            case OperationType::Error:
                XLOG::l.e("Error with file: {}", path);
                break;
        }
    }
};

Implementazione:
1. Log Levels
   - Debug: Operazioni dettagliate
   - Info: File trovati
   - Warning: File eliminati
   - Error: Problemi operazioni

2. Context
   - Path completo
   - Tipo operazione
   - Timestamp
   - Metadata rilevante

3. Performance
   - Log buffering
   - Async writing
   - Size limits
```

### 4.2 Notification System
```cpp
class FileMonitor {
private:
    struct FileEvent {
        fs::path path;
        EventType type;
        std::chrono::system_clock::time_point time;
        std::map<std::string, std::string> metadata;
    };
    
    void notifyFileEvent(const FileEvent& event) {
        // 1. Create notification
        Notification n{
            .level = determineLevel(event.type),
            .message = formatMessage(event),
            .context = buildContext(event)
        };
        
        // 2. Send to CheckMK
        sendNotification(n);
        
        // 3. Log event
        logFileEvent(event);
    }
};

Design:
1. Event Structure
   - Path info
   - Event type
   - Timestamp preciso
   - Metadata estensibile

2. Notification Levels
   - Found: Info
   - Deleted: Warning
   - Error: Error/Critical

3. Context Building
   - File metadata
   - Operation context
   - System state
```

### 4.3 Integration Points
```cpp
class FileMonitor {
private:
    // 1. Configuration
    struct NotificationConfig {
        bool notify_on_found;
        bool notify_on_delete;
        Level min_level;
    };
    
    // 2. Event Processing
    void processFile(const fs::path& path) {
        try {
            if (shouldProcess(path)) {
                FileEvent event = createEvent(path);
                if (shouldNotify(event)) {
                    notifyFileEvent(event);
                }
            }
        } catch (const std::exception& e) {
            handleError(path, e);
        }
    }
    
    // 3. Error Handling
    void handleError(
        const fs::path& path, 
        const std::exception& e) {
        
        XLOG::l.e("Error processing {}: {}", 
                  path, e.what());
        
        if (isRecoverableError(e)) {
            scheduleRetry(path);
        } else {
            notifyError(path, e);
        }
    }
};

Implementazione:
1. Configuration
   - YAML driven
   - Default values
   - Runtime updates

2. Event Flow
   - Validation
   - Processing
   - Notification

3. Error Management
   - Categorization
   - Recovery
   - Notification
```

## 5. Conclusioni

### 5.1 Best Practices Identificate
1. Logging
   - Livelli appropriati
   - Contesto completo
   - Performance ottimizzata

2. Notifications
   - Eventi strutturati
   - Routing intelligente
   - Error handling robusto

3. Integration
   - Sistema esistente
   - Pattern comuni
   - Estensibilità

### 5.2 Implementation Guidelines
1. Logging
   - Usa XLOG framework
   - Mantieni contesto
   - Gestisci performance

2. Notifications
   - Segui pattern esistenti
   - Struttura eventi
   - Gestisci errori

3. Integration
   - Usa carrier system
   - Segui convenzioni
   - Documenta interfacce

### 5.3 Future Considerations
1. Extensibility
   - Custom events
   - Filtri notification
   - Routing avanzato

2. Performance
   - Batch processing
   - Async notifications
   - Log optimization

3. Maintenance
   - Monitoring
   - Debugging
   - Updates
