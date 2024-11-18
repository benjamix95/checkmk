# Implementazione Dettagliata del File Monitor Provider per CheckMK

## Indice
1. [Architettura](#architettura)
2. [Componenti](#componenti)
3. [Implementazione](#implementazione)
4. [Configurazione](#configurazione)
5. [Compilazione](#compilazione)
6. [Test](#test)
7. [Esempi Pratici](#esempi-pratici)
8. [Troubleshooting](#troubleshooting)
9. [Estensioni Future](#estensioni-future)

## Architettura

### Overview del Sistema
Il File Monitor Provider è integrato nell'agente CheckMK Windows come provider sincrono. Si basa sull'architettura esistente dei provider e utilizza il sistema di notifiche di CheckMK.

### Flusso di Esecuzione
1. L'agente CheckMK carica la configurazione
2. Il FileMonitor viene inizializzato come provider sincrono
3. Il provider esegue il monitoraggio periodico:
   - Scansiona i file configurati
   - Verifica le corrispondenze con i pattern
   - Esegue le azioni configurate (eliminazione)
   - Invia notifiche al sistema CheckMK

### Diagramma dei Componenti
```
┌─────────────────┐
│  CheckMK Agent  │
└────────┬────────┘
         │
┌────────▼────────┐
│  File Monitor   │
│    Provider     │
└────────┬────────┘
         │
    ┌────▼────┐
    │  YAML   │
    │ Config  │
    └────┬────┘
         │
    ┌────▼────┐
    │ Windows │
    │ File    │
    │ System  │
    └─────────┘
```

## Componenti

### 1. Header File (file_monitor.h)
```cpp
namespace cma::provider {

// Costanti del provider
constexpr const char* kFileMonitorSection = "file_monitor";
constexpr int kDefaultCheckInterval = 300;  // 5 minuti
constexpr int kDefaultTimeout = 60;
constexpr int kDefaultRetry = 3;

class FileMonitor final : public Synchronous {
public:
    // Singleton pattern per l'istanza del provider
    static FileMonitor& Instance() {
        static FileMonitor instance;
        return instance;
    }

    // Interfaccia del provider
    void loadConfig() override;
    std::string makeBody() override;
    void updateSectionStatus() override;

private:
    // Struttura per i percorsi monitorati
    struct MonitoredPath {
        std::filesystem::path path;
        std::chrono::system_clock::time_point last_check;
        bool should_delete;
        
        // Metadati aggiuntivi
        size_t max_size;
        bool recursive;
        std::string pattern;
    };

    // Membri privati
    std::vector<MonitoredPath> monitored_paths_;
    int check_interval_{kDefaultCheckInterval};
    std::string last_output_;
    
    // Metodi privati di utilità
    void deleteFile(const std::filesystem::path& path);
    void sendNotification(const std::string& message);
    std::optional<YAML::Node> getConfiguredPaths() const;
    void checkAndNotify();
    bool matchesPattern(const std::filesystem::path& file, const MonitoredPath& config);
    void processDirectory(const std::filesystem::path& dir, const MonitoredPath& config);
};

} // namespace cma::provider
```

### 2. Implementazione (file_monitor.cpp)
```cpp
namespace cma::provider {

void FileMonitor::loadConfig() {
    // Carica la configurazione standard
    loadStandardConfig();

    // Carica la configurazione specifica
    auto paths = getConfiguredPaths();
    if (!paths) {
        XLOG::l("No file monitoring paths configured");
        return;
    }

    monitored_paths_.clear();
    for (const auto& path_node : *paths) {
        try {
            MonitoredPath mp{
                .path = fs::path(wtools::ConvertToUtf16(
                    path_node["path"].as<std::string>())),
                .last_check = std::chrono::system_clock::now(),
                .should_delete = path_node["delete"].as<bool>(false),
                .max_size = path_node["max_size"].as<size_t>(
                    std::numeric_limits<size_t>::max()),
                .recursive = path_node["recursive"].as<bool>(false),
                .pattern = path_node["pattern"].as<std::string>("*")
            };
            
            monitored_paths_.push_back(std::move(mp));
            XLOG::t("Added monitoring path '{}' with delete={}, recursive={}", 
                wtools::ToUtf8(mp.path.wstring()), 
                mp.should_delete,
                mp.recursive);
        } catch (const std::exception& e) {
            XLOG::l.e("Error parsing file monitor config: {}", e.what());
        }
    }

    // Carica l'intervallo di controllo
    const auto monitor_section = cfg::GetLoadedConfig()[kFileMonitorSection];
    if (monitor_section && monitor_section["check_interval"]) {
        check_interval_ = monitor_section["check_interval"].as<int>();
    }
}

void FileMonitor::checkAndNotify() {
    for (auto& mp : monitored_paths_) {
        try {
            if (mp.recursive) {
                processDirectory(mp.path, mp);
            } else {
                if (matchesPattern(mp.path, mp)) {
                    std::error_code ec;
                    if (fs::exists(mp.path, ec)) {
                        sendNotification(fmt::format(
                            "File '{}' found", 
                            wtools::ToUtf8(mp.path.wstring())));
                        
                        if (mp.should_delete) {
                            deleteFile(mp.path);
                        }
                    }
                }
            }
        } catch (const std::exception& e) {
            XLOG::l.e("Error checking path '{}': {}", 
                wtools::ToUtf8(mp.path.wstring()), e.what());
        }
    }
}

bool FileMonitor::matchesPattern(
    const std::filesystem::path& file, 
    const MonitoredPath& config) {
    
    return cma::tools::GlobMatch(
        wtools::ConvertToUtf16(config.pattern), 
        file.wstring());
}

void FileMonitor::processDirectory(
    const std::filesystem::path& dir, 
    const MonitoredPath& config) {
    
    try {
        for (const auto& entry : 
             fs::recursive_directory_iterator(
                 dir, 
                 fs::directory_options::skip_permission_denied)) {
            
            if (!entry.is_regular_file()) continue;

            if (matchesPattern(entry.path(), config)) {
                auto file_size = fs::file_size(entry.path());
                
                if (file_size > config.max_size) {
                    XLOG::l.w("File '{}' exceeds size limit", 
                        wtools::ToUtf8(entry.path().wstring()));
                    continue;
                }

                sendNotification(fmt::format(
                    "File '{}' found", 
                    wtools::ToUtf8(entry.path().wstring())));
                
                if (config.should_delete) {
                    deleteFile(entry.path());
                }
            }
        }
    } catch (const std::exception& e) {
        XLOG::l.e("Error processing directory '{}': {}", 
            wtools::ToUtf8(dir.wstring()), e.what());
    }
}

std::string FileMonitor::makeBody() {
    std::string output = section::MakeHeader(kFileMonitorSection);
    output += fmt::format("CheckInterval: {} seconds\n", check_interval_);
    
    for (const auto& mp : monitored_paths_) {
        std::error_code ec;
        bool exists = fs::exists(mp.path, ec);
        
        output += fmt::format("{}|{}|{}|{}|{}\n",
            wtools::ToUtf8(mp.path.wstring()),
            exists ? "found" : "not_found",
            mp.should_delete ? "will_delete" : "keep",
            mp.recursive ? "recursive" : "single",
            mp.pattern);
    }
    
    return output;
}

} // namespace cma::provider
```

## Configurazione

### File di Configurazione Completo
```yaml
# Configurazione globale
global:
  enabled: true
  sections:
    - file_monitor

# Configurazione del File Monitor
file_monitor:
  enabled: true
  timeout: 60
  retry: 3
  async: false
  cache_age: 300
  check_interval: 300

  # Lista dei percorsi da monitorare
  paths:
    # File singolo
    - path: "C:\\temp\\test.txt"
      delete: true
      max_size: 1048576  # 1MB

    # Pattern glob per file di log
    - path: "C:\\logs"
      pattern: "*.log"
      delete: false
      recursive: true
      max_size: 104857600  # 100MB

    # Monitoraggio ricorsivo di file temporanei
    - path: "C:\\Users"
      pattern: "*.tmp"
      delete: true
      recursive: true
      max_size: 52428800  # 50MB

  # Impostazioni avanzate
  settings:
    max_file_size: 104857600  # 100MB default
    max_files_per_check: 1000
    log_operations: true

    # Configurazione delle notifiche
    notifications:
      event_log: true
      checkmk: true
      levels:
        file_found: info
        file_deleted: warning
        error: critical

# Configurazione del logging
logging:
  level: debug
  console: true
  file: true
  filename: "C:\\ProgramData\\checkmk\\logs\\file_monitor.log"
  format: "[{timestamp}] [{level}] {message}"
  rotation:
    max_size: 10485760  # 10MB
    keep_files: 5
```

### Parametri di Configurazione Dettagliati

#### Parametri Globali
| Parametro | Tipo | Default | Descrizione |
|-----------|------|---------|-------------|
| enabled | bool | true | Abilita/disabilita il provider |
| timeout | int | 60 | Timeout in secondi per le operazioni |
| retry | int | 3 | Numero di tentativi per operazione |
| check_interval | int | 300 | Intervallo tra i controlli |

#### Parametri dei Percorsi
| Parametro | Tipo | Default | Descrizione |
|-----------|------|---------|-------------|
| path | string | - | Percorso da monitorare |
| delete | bool | false | Se eliminare i file trovati |
| pattern | string | * | Pattern glob per il match |
| recursive | bool | false | Ricerca ricorsiva |
| max_size | int | - | Dimensione massima file |

## Compilazione

### Prerequisiti Dettagliati
- Visual Studio 2019 o superiore
  - Workload "Sviluppo desktop C++"
  - Componenti singoli:
    - MSVC v142 build tools
    - Windows 10 SDK
    - C++ CMake tools
- CMake 3.15 o superiore
- Git per Windows
- Python 3.8 o superiore (per gli script di build)

### Procedura di Compilazione Dettagliata

1. Preparazione dell'Ambiente
```batch
:: Clona il repository
git clone https://github.com/Checkmk/checkmk.git
cd checkmk

:: Configura le variabili d'ambiente
set CHECKMK_BUILD_DIR=build
set CHECKMK_SOURCE_DIR=%CD%
```

2. Configurazione del Progetto
```batch
:: Crea la directory di build
mkdir %CHECKMK_BUILD_DIR%
cd %CHECKMK_BUILD_DIR%

:: Configura CMake
cmake -G "Visual Studio 16 2019" -A x64 ^
    -DCMAKE_BUILD_TYPE=Release ^
    -DBUILD_TESTING=ON ^
    %CHECKMK_SOURCE_DIR%
```

3. Compilazione
```batch
:: Compila il progetto
cmake --build . --config Release

:: Compila solo l'agente Windows
cmake --build . --config Release --target check_mk_agent
```

4. Test
```batch
:: Esegui i test
ctest -C Release -R FileMonitorTest
```

### Verifica dell'Installazione

1. Copia i File
```batch
:: Copia l'agente compilato
copy Release\check_mk_agent.exe "C:\Program Files\CheckMK\Agent"

:: Copia la configurazione
copy config\check_mk_dev_file_monitor_config.yml ^
    "C:\ProgramData\checkmk\config"
```

2. Verifica il Servizio
```batch
:: Riavvia il servizio
net stop CheckMKService
net start CheckMKService

:: Verifica i log
type "C:\ProgramData\checkmk\logs\file_monitor.log"
```

## Test

### Test Unitari Dettagliati
```cpp
TEST_F(FileMonitorTest, ConfigurationLoading) {
    // Prepara la configurazione di test
    std::string config = R"(
        file_monitor:
          enabled: true
          check_interval: 60
          paths:
            - path: "C:\\temp\\test.txt"
              delete: true
    )";
    
    // Scrivi la configurazione
    writeConfig(config);
    
    // Carica la configurazione
    auto& monitor = FileMonitor::Instance();
    monitor.loadConfig();
    
    // Verifica i parametri
    EXPECT_TRUE(monitor.isEnabled());
    EXPECT_EQ(monitor.checkInterval(), 60);
    EXPECT_EQ(monitor.getMonitoredPaths().size(), 1);
}

TEST_F(FileMonitorTest, FileDetection) {
    // Crea file di test
    createTestFile("test.txt", "content");
    createTestFile("test.log", "log content");
    
    // Configura il monitor
    auto& monitor = FileMonitor::Instance();
    monitor.addPath("test.txt", true);
    
    // Esegui il controllo
    monitor.updateSectionStatus();
    
    // Verifica l'output
    auto output = monitor.makeBody();
    EXPECT_TRUE(output.find("test.txt|found") != std::string::npos);
}

TEST_F(FileMonitorTest, FileDeletion) {
    // Crea file di test
    auto test_file = createTestFile("delete_me.txt", "content");
    
    // Configura il monitor
    auto& monitor = FileMonitor::Instance();
    monitor.addPath("delete_me.txt", true);
    
    // Esegui il controllo
    monitor.updateSectionStatus();
    
    // Verifica che il file sia stato eliminato
    EXPECT_FALSE(fs::exists(test_file));
}
```

### Test Manuali Dettagliati

1. Test di Base
```batch
:: Crea file di test
echo test > C:\temp\test.txt
echo log > C:\temp\test.log

:: Verifica il monitoraggio
check_mk_agent.exe -s file_monitor
```

2. Test dei Pattern Glob
```batch
:: Crea diversi file
for %i in (1,2,3) do echo test%i > C:\temp\test%i.log

:: Verifica il match del pattern
check_mk_agent.exe -s file_monitor
```

3. Test dell'Eliminazione
```batch
:: Crea file da eliminare
echo delete > C:\temp\delete_me.txt

:: Esegui il monitor e verifica
check_mk_agent.exe -s file_monitor
dir C:\temp\delete_me.txt
```

## Esempi Pratici

### 1. Monitoraggio File di Log
```yaml
file_monitor:
  paths:
    - path: "C:\\logs"
      pattern: "*.log"
      delete: false
      recursive: true
      max_size: 100MB
```

### 2. Pulizia File Temporanei
```yaml
file_monitor:
  paths:
    - path: "C:\\Windows\\Temp"
      pattern: "*.tmp"
      delete: true
      max_size: 10MB
```

### 3. Monitoraggio Download
```yaml
file_monitor:
  paths:
    - path: "C:\\Users\\**\\Downloads"
      pattern: "*.exe"
      delete: true
      recursive: true
```

## Troubleshooting

### Diagnostica Dettagliata

1. Verifica del Provider
```batch
:: Esegui con debug
check_mk_agent.exe -d -s file_monitor

:: Verifica lo stato
check_mk_agent.exe -D
```

2. Log Dettagliati
```batch
:: Abilita logging dettagliato
echo "debug_log: true" >> check_mk.yml

:: Analizza i log
type C:\ProgramData\checkmk\logs\file_monitor.log
```

3. Verifica Configurazione
```batch
:: Valida la configurazione
check_mk_agent.exe -t

:: Mostra configurazione attiva
check_mk_agent.exe -c
```

### Errori Comuni e Soluzioni

1. **File Non Trovati**
```
Problema: I file non vengono rilevati
Soluzioni:
- Verifica i permessi (icacls C:\path\to\files)
- Controlla i pattern glob
- Usa percorsi assoluti
```

2. **Errori di Eliminazione**
```
Problema: I file non vengono eliminati
Soluzioni:
- Verifica i permessi di scrittura
- Controlla se i file sono in uso
- Usa Process Explorer per verificare i lock
```

3. **Performance**
```
Problema: Scansione lenta
Soluzioni:
- Riduci i pattern ricorsivi
- Aumenta check_interval
- Limita max_files_per_check
```

## Estensioni Future

### 1. Filtri Avanzati
```cpp
// file_monitor.h
struct FileFilter {
    std::string pattern;
    std::function<bool(const fs::path&)> predicate;
    int age_days;
    std::string owner;
};

// Implementazione
bool FileMonitor::matchesFilter(
    const fs::path& file, 
    const FileFilter& filter) {
    // Verifica pattern
    if (!matchesPattern(file, filter.pattern))
        return false;
        
    // Verifica età
    if (filter.age_days > 0) {
        auto ftime = fs::last_write_time(file);
        auto age = std::chrono::system_clock::now() - ftime;
        if (std::chrono::duration_cast<std::chrono::hours>
            (age).count() < filter.age_days * 24)
            return false;
    }
    
    // Verifica proprietario
    if (!filter.owner.empty()) {
        auto owner = getFileOwner(file);
        if (owner != filter.owner)
            return false;
    }
    
    // Verifica predicato custom
    if (filter.predicate && !filter.predicate(file))
        return false;
        
    return true;
}
```

### 2. Azioni Personalizzate
```cpp
// file_monitor.h
struct FileAction {
    enum class Type {
        Delete,
        Move,
        Copy,
        Compress,
        Custom
    };
    
    Type type;
    std::string destination;
    std::function<void(const fs::path&)> custom_action;
};

// Implementazione
void FileMonitor::executeAction(
    const fs::path& file, 
    const FileAction& action) {
    switch (action.type) {
        case FileAction::Type::Delete:
            deleteFile(file);
            break;
            
        case FileAction::Type::Move:
            fs::rename(file, action.destination);
            break;
            
        case FileAction::Type::Copy:
            fs::copy(file, action.destination);
            break;
            
        case FileAction::Type::Compress:
            compressFile(file, action.destination);
            break;
            
        case FileAction::Type::Custom:
            if (action.custom_action)
                action.custom_action(file);
            break;
    }
}
```

### 3. Notifiche Avanzate
```cpp
// file_monitor.h
struct Notification {
    enum class Level {
        Info,
        Warning,
        Critical
    };
    
    Level level;
    std::string message;
    std::map<std::string, std::string> metadata;
};

// Implementazione
void FileMonitor::sendNotification(
    const Notification& notification) {
    // Formatta il messaggio
    std::string formatted = fmt::format(
        "[{}] {}\nMetadata:\n",
        toString(notification.level),
        notification.message);
        
    for (const auto& [key, value] : notification.metadata) {
        formatted += fmt::format("  {}: {}\n", key, value);
    }
    
    // Invia attraverso i canali configurati
    if (config_.notifications.event_log)
        sendToEventLog(formatted, notification.level);
        
    if (config_.notifications.checkmk)
        sendToCheckMK(formatted, notification.level);
}
```

## Note per i Colleghi

### Best Practices

1. **Gestione degli Errori**
```cpp
// Usa RAII per le risorse
class ScopedFile {
public:
    explicit ScopedFile(const fs::path& path) 
        : path_(path) {}
    ~ScopedFile() {
        try {
            if (fs::exists(path_))
                fs::remove(path_);
        } catch (...) {
            // Log error
        }
    }
private:
    fs::path path_;
};

// Gestione eccezioni
try {
    // Operazione file
} catch (const fs::filesystem_error& e) {
    XLOG::l.e("File system error: {}", e.what());
} catch (const std::exception& e) {
    XLOG::l.e("General error: {}", e.what());
}
```

2. **Logging**
```cpp
// Usa i livelli appropriati
XLOG::t("Debug info: {}", value);     // Trace
XLOG::d("Status: {}", status);        // Debug
XLOG::l("Operation: {}", op);         // Info
XLOG::l.w("Warning: {}", warning);    // Warning
XLOG::l.e("Error: {}", error);        // Error
XLOG::l.crit("Critical: {}", crit);   // Critical
```

3. **Testing**
```cpp
// Usa fixture per setup/teardown
class TestFixture : public ::testing::Test {
protected:
    void SetUp() override {
        // Setup
    }
    void TearDown() override {
        // Cleanup
    }
};

// Test parametrici
class ParameterizedTest : 
    public ::testing::TestWithParam<TestParams> {
};

INSTANTIATE_TEST_SUITE_P(
    FileMonitor,
    ParameterizedTest,
    ::testing::Values(
        TestParams{...},
        TestParams{...}
    ));
```

### Manutenzione

1. **Aggiornamenti**
- Verifica compatibilità con nuove versioni di CheckMK
- Aggiorna la documentazione
- Esegui la suite di test completa

2. **Monitoraggio**
- Controlla i log regolarmente
- Monitora l'uso delle risorse
- Verifica le performance

3. **Backup**
- Mantieni backup delle configurazioni
- Documenta le modifiche
- Usa il controllo versione

## Supporto

### Canali di Supporto
1. Documentazione interna
2. Issue tracker
3. Team di sviluppo
4. Community CheckMK

### Procedure di Escalation
1. Consulta la documentazione
2. Verifica i log
3. Apri ticket di supporto
4. Escalation al team di sviluppo
