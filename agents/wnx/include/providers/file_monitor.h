/**
 * @file file_monitor.h
 * @brief Header file per il provider di monitoraggio file in Windows
 */

#pragma once

#include <string>
#include <vector>
#include <chrono>
#include <filesystem>
#include <memory>
#include <mutex>
#include <optional>
#include <yaml-cpp/yaml.h>

// Definizione dell'API per l'esportazione/importazione DLL
#ifdef ENGINE_EXPORTS
    #define ENGINE_API __declspec(dllexport)
#else
    #define ENGINE_API __declspec(dllimport)
#endif

namespace checkmk_agent {
namespace provider {

/**
 * @class FileMonitorProvider
 * @brief Provider per il monitoraggio dei file in Windows
 */
class ENGINE_API FileMonitorProvider final {
public:
    /**
     * @brief Ottiene l'istanza singleton del provider
     * @return Riferimento all'istanza del provider
     */
    static FileMonitorProvider& GetInstance() {
        static FileMonitorProvider instance;
        return instance;
    }

    /**
     * @brief Inizializza il provider con la configurazione
     */
    void Initialize();

    /**
     * @brief Aggiorna lo stato del monitoraggio
     */
    void UpdateMonitoringStatus();

    /**
     * @brief Genera l'output per il report
     * @return Stringa contenente il report
     */
    std::string GenerateReport() const;

private:
    /**
     * @struct MonitoredPath
     * @brief Struttura per la configurazione di un percorso monitorato
     */
    struct MonitoredPath {
        std::filesystem::path path;                      ///< Percorso da monitorare
        bool isDirectory{false};                         ///< Indica se è una directory
        bool deleteAfterFound{false};                    ///< Indica se eliminare i file trovati
        std::string pattern;                            ///< Pattern per il matching dei file
        std::chrono::system_clock::time_point lastCheck; ///< Timestamp dell'ultimo controllo
        bool recursive{false};                          ///< Indica se eseguire la ricerca ricorsiva
        std::optional<size_t> minSize;                  ///< Dimensione minima del file
        std::optional<std::chrono::seconds> minAge;     ///< Età minima del file
        std::vector<std::string> excludePatterns;       ///< Pattern da escludere
    };

    /**
     * @struct MonitoringConfig
     * @brief Struttura per la configurazione del monitoraggio
     */
    struct MonitoringConfig {
        std::vector<MonitoredPath> paths;               ///< Lista dei percorsi da monitorare
        std::chrono::seconds checkInterval{300};        ///< Intervallo tra i controlli
        std::optional<std::pair<int, int>> timeRange;  ///< Intervallo orario per il monitoraggio
        bool logOperations{true};                      ///< Indica se loggare le operazioni
        size_t maxFilesPerCheck{1000};                 ///< Numero massimo di file per controllo
    };

    // Costruttore e distruttore privati per il singleton
    FileMonitorProvider() = default;
    ~FileMonitorProvider() = default;

    // Disabilita copia e assegnamento
    FileMonitorProvider(const FileMonitorProvider&) = delete;
    FileMonitorProvider& operator=(const FileMonitorProvider&) = delete;
    FileMonitorProvider(FileMonitorProvider&&) = delete;
    FileMonitorProvider& operator=(FileMonitorProvider&&) = delete;

    /**
     * @brief Carica la configurazione dal file
     */
    void LoadConfiguration();

    /**
     * @brief Monitora un singolo file
     * @param config Configurazione del percorso da monitorare
     */
    void MonitorFile(const MonitoredPath& config);

    /**
     * @brief Monitora una directory
     * @param config Configurazione del percorso da monitorare
     */
    void MonitorDirectory(const MonitoredPath& config);

    /**
     * @brief Verifica se un file corrisponde al pattern
     * @param path Percorso del file
     * @param pattern Pattern da verificare
     * @return true se il file corrisponde al pattern
     */
    bool MatchesPattern(const std::filesystem::path& path, const std::string& pattern) const;

    /**
     * @brief Elimina un file
     * @param path Percorso del file da eliminare
     * @return true se l'eliminazione è riuscita
     */
    bool DeleteFile(const std::filesystem::path& path);

    /**
     * @brief Invia una notifica
     * @param message Messaggio della notifica
     * @param status Stato della notifica (info, warning, error)
     */
    void SendNotification(const std::string& message, const std::string& status = "info") const;

    /**
     * @brief Invia una notifica attraverso CheckMK
     * @param type Tipo di notifica
     * @param path Percorso del file
     * @param message Messaggio della notifica
     */
    void SendCheckMKNotification(
        const std::string& type,
        const std::string& path,
        const std::string& message) const;

    /**
     * @brief Verifica se è il momento di eseguire un controllo
     * @param config Configurazione del percorso
     * @return true se è necessario eseguire un controllo
     */
    bool IsCheckDue(const MonitoredPath& config) const;

    /**
     * @brief Verifica se l'ora corrente è nell'intervallo configurato
     * @param path Percorso del file (per il logging)
     * @return true se l'ora è nell'intervallo
     */
    bool IsWithinTimeRange(const std::filesystem::path& path) const;

    /**
     * @brief Ottiene la configurazione dell'intervallo orario
     * @return Coppia di valori (ora inizio, ora fine) se configurato
     */
    std::optional<std::pair<int, int>> GetTimeRangeConfig() const;

    // Membri privati
    MonitoringConfig config_;                          ///< Configurazione del monitoraggio
    mutable std::recursive_mutex mutex_;               ///< Mutex per l'accesso thread-safe
    mutable std::string lastReport_;                   ///< Ultimo report generato
    std::chrono::system_clock::time_point lastGlobalCheck_; ///< Timestamp dell'ultimo controllo globale
    bool initialized_{false};                          ///< Flag di inizializzazione
};

} // namespace provider
} // namespace checkmk_agent
