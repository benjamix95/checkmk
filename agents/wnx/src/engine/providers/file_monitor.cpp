/**
 * @file file_monitor.cpp
 * @brief Implementazione del provider per il monitoraggio dei file in Windows
 */

#include "stdafx.h"
#include "providers/file_monitor.h"
#include <yaml-cpp/yaml.h>
#include <regex>
#include <sstream>
#include <fstream>
#include <iomanip>
#include <ctime>

namespace checkmk_agent {
namespace provider {

void FileMonitorProvider::Initialize() {
    // Acquisisce il lock per l'accesso thread-safe
    std::lock_guard<std::recursive_mutex> lockGuard(mutex_);

    // Verifica se il provider è già stato inizializzato
    if (!initialized_) {
        // Carica la configurazione dal file
        LoadConfiguration();

        // Imposta il timestamp dell'ultimo controllo globale
        lastGlobalCheck_ = std::chrono::system_clock::now();

        // Marca il provider come inizializzato
        initialized_ = true;

        // Log dell'inizializzazione completata
        std::stringstream initMessage;
        initMessage << "File Monitor Provider inizializzato con successo. ";
        initMessage << "Intervallo di controllo: " << config_.checkInterval.count() << " secondi. ";
        initMessage << "Numero di percorsi monitorati: " << config_.paths.size();
        SendNotification(initMessage.str(), "info");
    }
}

void FileMonitorProvider::LoadConfiguration() {
    try {
        // Percorso del file di configurazione
        const std::string configPath = "check_mk_dev_file_monitor.yml";

        // Verifica se il file di configurazione esiste
        if (!std::filesystem::exists(configPath)) {
            throw std::runtime_error("File di configurazione non trovato: " + configPath);
        }

        // Carica e parsa il file YAML
        YAML::Node configRoot = YAML::LoadFile(configPath);
        
        // Verifica la presenza della sezione file_monitor
        if (!configRoot["file_monitor"]) {
            throw std::runtime_error("Sezione 'file_monitor' mancante nella configurazione");
        }

        // Ottiene il nodo di configurazione principale
        YAML::Node monitorConfig = configRoot["file_monitor"];
        
        // Carica l'intervallo di controllo
        if (monitorConfig["check_interval"]) {
            int intervalSeconds = monitorConfig["check_interval"].as<int>();
            if (intervalSeconds <= 0) {
                throw std::runtime_error("L'intervallo di controllo deve essere positivo");
            }
            config_.checkInterval = std::chrono::seconds(intervalSeconds);
        }

        // Carica i percorsi da monitorare
        if (monitorConfig["paths"]) {
            YAML::Node pathsNode = monitorConfig["paths"];
            if (!pathsNode.IsSequence()) {
                throw std::runtime_error("La sezione 'paths' deve essere una sequenza");
            }

            // Itera su tutti i percorsi configurati
            for (const YAML::Node& pathNode : pathsNode) {
                // Verifica i campi obbligatori
                if (!pathNode["path"]) {
                    throw std::runtime_error("Campo 'path' mancante nella configurazione del percorso");
                }

                // Crea una nuova configurazione di percorso
                MonitoredPath monitoredPath;

                // Imposta il percorso
                std::string pathString = pathNode["path"].as<std::string>();
                monitoredPath.path = std::filesystem::path(pathString);

                // Imposta se è una directory
                monitoredPath.isDirectory = pathNode["is_directory"].as<bool>(false);

                // Imposta se il file deve essere eliminato dopo essere stato trovato
                monitoredPath.deleteAfterFound = pathNode["delete"].as<bool>(false);

                // Imposta il pattern di ricerca
                monitoredPath.pattern = pathNode["pattern"].as<std::string>("*");

                // Imposta il timestamp dell'ultimo controllo
                monitoredPath.lastCheck = std::chrono::system_clock::now();

                // Verifica che il percorso sia valido
                if (!std::filesystem::exists(monitoredPath.path)) {
                    std::stringstream warning;
                    warning << "Attenzione: il percorso configurato non esiste: " << pathString;
                    SendNotification(warning.str(), "warning");
                }

                // Aggiunge il percorso alla configurazione
                config_.paths.push_back(monitoredPath);

                // Log della configurazione del percorso
                std::stringstream pathConfig;
                pathConfig << "Configurato monitoraggio per: " << pathString << " ";
                pathConfig << "(Directory: " << (monitoredPath.isDirectory ? "Sì" : "No") << ", ";
                pathConfig << "Elimina: " << (monitoredPath.deleteAfterFound ? "Sì" : "No") << ", ";
                pathConfig << "Pattern: " << monitoredPath.pattern << ")";
                SendNotification(pathConfig.str(), "info");
            }
        } else {
            throw std::runtime_error("Sezione 'paths' mancante nella configurazione");
        }
    }
    catch (const std::exception& error) {
        std::stringstream errorMessage;
        errorMessage << "Errore durante il caricamento della configurazione: " << error.what();
        SendNotification(errorMessage.str(), "error");
        throw; // Propaga l'errore
    }
}

void FileMonitorProvider::UpdateMonitoringStatus() {
    // Acquisisce il lock per l'accesso thread-safe
    std::lock_guard<std::recursive_mutex> lockGuard(mutex_);
    
    // Verifica se il provider è stato inizializzato
    if (!initialized_) {
        Initialize();
    }

    // Ottiene il timestamp corrente
    auto currentTime = std::chrono::system_clock::now();
    
    // Calcola il tempo trascorso dall'ultimo controllo
    auto elapsedTime = std::chrono::duration_cast<std::chrono::seconds>(
        currentTime - lastGlobalCheck_);
    
    // Verifica se è necessario eseguire un nuovo controllo
    if (elapsedTime < config_.checkInterval) {
        return;
    }

    // Inizializza il report
    std::stringstream reportStream;
    reportStream << "<<<file_monitor>>>\n";
    auto timeT = std::chrono::system_clock::to_time_t(currentTime);
    std::tm tmBuf;
    localtime_s(&tmBuf, &timeT);
    reportStream << "Timestamp: " << std::put_time(&tmBuf, "%Y-%m-%d %H:%M:%S") << "\n";
    reportStream << "Intervallo di controllo: " << config_.checkInterval.count() << " secondi\n";
    reportStream << "Percorsi monitorati: " << config_.paths.size() << "\n\n";

    // Controlla ogni percorso configurato
    for (auto& monitoredPath : config_.paths) {
        reportStream << "Controllo percorso: " << monitoredPath.path.string() << "\n";
        reportStream << "Tipo: " << (monitoredPath.isDirectory ? "Directory" : "File") << "\n";
        reportStream << "Pattern: " << monitoredPath.pattern << "\n";

        try {
            // Esegue il controllo appropriato in base al tipo
            if (monitoredPath.isDirectory) {
                MonitorDirectory(monitoredPath);
            } else {
                MonitorFile(monitoredPath);
            }

            // Aggiorna il timestamp dell'ultimo controllo per questo percorso
            monitoredPath.lastCheck = currentTime;
        }
        catch (const std::exception& error) {
            std::stringstream errorMessage;
            errorMessage << "Errore durante il monitoraggio di " << monitoredPath.path.string();
            errorMessage << ": " << error.what();
            SendNotification(errorMessage.str(), "error");
            reportStream << "Stato: Errore - " << error.what() << "\n";
        }

        reportStream << "\n";
    }

    // Aggiorna il timestamp dell'ultimo controllo globale
    lastGlobalCheck_ = currentTime;

    // Salva il report
    lastReport_ = reportStream.str();
}

void FileMonitorProvider::MonitorFile(const MonitoredPath& monitoredPath) {
    try {
        // Verifica se il file esiste
        if (!std::filesystem::exists(monitoredPath.path)) {
            std::stringstream message;
            message << "File non trovato: " << monitoredPath.path.string();
            SendNotification(message.str(), "info");
            return;
        }

        // Verifica se il file corrisponde al pattern
        if (MatchesPattern(monitoredPath.path, monitoredPath.pattern)) {
            // Notifica il rilevamento del file
            std::stringstream message;
            message << "File trovato: " << monitoredPath.path.string();
            SendNotification(message.str(), "info");

            // Se configurato, elimina il file
            if (monitoredPath.deleteAfterFound) {
                DeleteFile(monitoredPath.path);
            }
        }
    }
    catch (const std::exception& error) {
        std::stringstream errorMessage;
        errorMessage << "Errore durante il monitoraggio del file " << monitoredPath.path.string();
        errorMessage << ": " << error.what();
        SendNotification(errorMessage.str(), "error");
        throw; // Propaga l'errore
    }
}

void FileMonitorProvider::MonitorDirectory(const MonitoredPath& monitoredPath) {
    try {
        // Verifica se la directory esiste
        if (!std::filesystem::exists(monitoredPath.path)) {
            std::stringstream message;
            message << "Directory non trovata: " << monitoredPath.path.string();
            SendNotification(message.str(), "info");
            return;
        }

        // Verifica che sia effettivamente una directory
        if (!std::filesystem::is_directory(monitoredPath.path)) {
            std::stringstream errorMessage;
            errorMessage << "Il percorso non è una directory: " << monitoredPath.path.string();
            SendNotification(errorMessage.str(), "error");
            return;
        }

        // Conta i file trovati
        int filesFound = 0;
        int filesDeleted = 0;

        // Opzioni per la ricerca ricorsiva
        std::filesystem::directory_options options = 
            std::filesystem::directory_options::skip_permission_denied |
            std::filesystem::directory_options::follow_directory_symlink;

        // Usa recursive_directory_iterator per la scansione ricorsiva
        for (const auto& entry : std::filesystem::recursive_directory_iterator(
                monitoredPath.path, options)) {
            // Salta le directory
            if (!entry.is_regular_file()) {
                continue;
            }

            // Verifica se è nell'intervallo orario configurato
            if (!IsWithinTimeRange(entry.path())) {
                continue;
            }

            // Verifica se il file corrisponde al pattern
            if (MatchesPattern(entry.path(), monitoredPath.pattern)) {
                filesFound++;

                // Notifica il rilevamento del file
                std::stringstream message;
                message << "File trovato: " << entry.path().string();
                SendNotification(message.str(), "info");

                // Se configurato, elimina il file
                if (monitoredPath.deleteAfterFound) {
                    if (DeleteFile(entry.path())) {
                        filesDeleted++;
                        
                        // Invia notifica di eliminazione attraverso CheckMK
                        SendCheckMKNotification(
                            "file_deleted",
                            entry.path().string(),
                            "File eliminato con successo"
                        );
                    }
                }
            }
        }

        // Notifica il riepilogo
        std::stringstream summary;
        summary << "Riepilogo directory " << monitoredPath.path.string() << ": ";
        summary << filesFound << " file trovati, ";
        summary << filesDeleted << " file eliminati";
        SendNotification(summary.str(), "info");

        // Se non sono stati trovati file, invia una notifica principale
        if (filesFound == 0) {
            SendCheckMKNotification(
                "no_files_found",
                monitoredPath.path.string(),
                "Nessun file trovato durante la scansione"
            );
        }
    }
    catch (const std::exception& error) {
        std::stringstream errorMessage;
        errorMessage << "Errore durante il monitoraggio della directory " 
                    << monitoredPath.path.string();
        errorMessage << ": " << error.what();
        SendNotification(errorMessage.str(), "error");
        throw; // Propaga l'errore
    }
}

bool FileMonitorProvider::MatchesPattern(
    const std::filesystem::path& filePath,
    const std::string& pattern) const {
    try {
        // Ottiene il nome del file
        std::string filename = filePath.filename().string();

        // Converte il pattern glob in espressione regolare
        std::string regexPattern = pattern;

        // Sostituisce i caratteri speciali del glob con i loro equivalenti regex
        regexPattern = std::regex_replace(regexPattern, std::regex("\\*"), ".*");
        regexPattern = std::regex_replace(regexPattern, std::regex("\\?"), ".");
        regexPattern = std::regex_replace(regexPattern, std::regex("\\["), "\\[");
        regexPattern = std::regex_replace(regexPattern, std::regex("\\]"), "\\]");
        regexPattern = std::regex_replace(regexPattern, std::regex("\\{"), "\\{");
        regexPattern = std::regex_replace(regexPattern, std::regex("\\}"), "\\}");

        // Crea l'oggetto regex con flag case-insensitive
        std::regex regex(regexPattern, 
            std::regex_constants::icase | 
            std::regex_constants::ECMAScript);

        // Esegue il matching
        return std::regex_match(filename, regex);
    }
    catch (const std::exception& error) {
        std::stringstream errorMessage;
        errorMessage << "Errore durante il matching del pattern '" << pattern << "' ";
        errorMessage << "per il file '" << filePath.string() << "': " << error.what();
        SendNotification(errorMessage.str(), "error");
        return false;
    }
}

bool FileMonitorProvider::DeleteFile(const std::filesystem::path& filePath) {
    try {
        // Verifica se il file esiste
        if (!std::filesystem::exists(filePath)) {
            std::stringstream message;
            message << "Impossibile eliminare il file (non esiste): " << filePath.string();
            SendNotification(message.str(), "warning");
            return false;
        }

        // Verifica i permessi di accesso
        std::error_code errorCode;

        // Prova a eliminare il file
        if (std::filesystem::remove(filePath, errorCode)) {
            // Notifica il successo
            std::stringstream message;
            message << "File eliminato con successo: " << filePath.string();
            SendNotification(message.str(), "info");
            return true;
        } else {
            // Notifica l'errore
            std::stringstream message;
            message << "Impossibile eliminare il file: " << filePath.string();
            message << " (" << errorCode.message() << ")";
            SendNotification(message.str(), "error");
            return false;
        }
    }
    catch (const std::exception& error) {
        std::stringstream errorMessage;
        errorMessage << "Errore durante l'eliminazione del file " << filePath.string();
        errorMessage << ": " << error.what();
        SendNotification(errorMessage.str(), "error");
        return false;
    }
}

bool FileMonitorProvider::IsWithinTimeRange(const std::filesystem::path& path) const {
    try {
        // Ottiene l'ora corrente
        auto now = std::chrono::system_clock::now();
        auto currentTime = std::chrono::system_clock::to_time_t(now);
        std::tm tmBuf;
        localtime_s(&tmBuf, &currentTime);

        // Ottiene l'ora come numero (0-23)
        int currentHour = tmBuf.tm_hour;

        // Ottiene l'intervallo di tempo dalla configurazione
        auto config = GetTimeRangeConfig();
        
        // Se non è configurato un intervallo, considera sempre valido
        if (!config.has_value()) {
            return true;
        }

        // Verifica se l'ora corrente è nell'intervallo
        int startHour = config->first;
        int endHour = config->second;

        // Gestisce il caso in cui l'intervallo attraversa la mezzanotte
        if (startHour <= endHour) {
            return currentHour >= startHour && currentHour <= endHour;
        } else {
            return currentHour >= startHour || currentHour <= endHour;
        }
    }
    catch (const std::exception& error) {
        std::stringstream errorMessage;
        errorMessage << "Errore durante la verifica dell'intervallo orario per "
                    << path.string() << ": " << error.what();
        SendNotification(errorMessage.str(), "error");
        return true; // In caso di errore, permette il controllo
    }
}

std::optional<std::pair<int, int>> FileMonitorProvider::GetTimeRangeConfig() const {
    std::lock_guard<std::recursive_mutex> lock(mutex_);
    try {
        // Carica la configurazione
        YAML::Node config = YAML::LoadFile("check_mk_dev_file_monitor.yml");
        
        // Verifica la presenza della sezione time_range
        if (!config["file_monitor"] || !config["file_monitor"]["time_range"]) {
            return std::nullopt;
        }

        auto timeRange = config["file_monitor"]["time_range"];
        
        // Verifica la presenza di start_hour e end_hour
        if (!timeRange["start_hour"] || !timeRange["end_hour"]) {
            return std::nullopt;
        }

        // Ottiene e valida le ore
        int startHour = timeRange["start_hour"].as<int>();
        int endHour = timeRange["end_hour"].as<int>();

        // Valida l'intervallo
        if (startHour < 0 || startHour > 23 || endHour < 0 || endHour > 23) {
            throw std::runtime_error("Ore non valide nell'intervallo orario");
        }

        return std::make_pair(startHour, endHour);
    }
    catch (const std::exception& error) {
        std::stringstream errorMessage;
        errorMessage << "Errore durante la lettura della configurazione "
                    << "dell'intervallo orario: " << error.what();
        SendNotification(errorMessage.str(), "error");
        return std::nullopt;
    }
}

void FileMonitorProvider::SendCheckMKNotification(
    const std::string& type,
    const std::string& path,
    const std::string& message) const {
    try {
        // Formatta il messaggio nel formato CheckMK
        std::stringstream notification;
        notification << "<<<local>>>\n";
        
        // Determina lo stato in base al tipo
        std::string status;
        if (type == "file_deleted") {
            status = "1"; // WARNING
        } else if (type == "no_files_found") {
            status = "0"; // OK
        } else {
            status = "2"; // CRITICAL
        }

        // Aggiunge i dettagli
        notification << status << " FileMonitor_" << type << " ";
        notification << "path=" << path << "|";
        notification << "message=" << message << "\n";

        // Scrive nel file di output di CheckMK
        std::ofstream output("check_mk_agent.out", std::ios::app);
        output << notification.str();
        output.close();
    }
    catch (const std::exception& error) {
        std::stringstream errorMessage;
        errorMessage << "Errore durante l'invio della notifica CheckMK: "
                    << error.what();
        SendNotification(errorMessage.str(), "error");
    }
}

void FileMonitorProvider::SendNotification(
    const std::string& message,
    const std::string& status) const {
    // Ottiene il timestamp corrente
    auto now = std::chrono::system_clock::now();
    auto timeT = std::chrono::system_clock::to_time_t(now);
    std::tm tmBuf;
    localtime_s(&tmBuf, &timeT);

    // Formatta il messaggio
    std::stringstream notificationStream;
    notificationStream << std::put_time(&tmBuf, "%Y-%m-%d %H:%M:%S");
    notificationStream << " [" << status << "] " << message << "\n";

    // Aggiorna il report in modo thread-safe
    std::lock_guard<std::recursive_mutex> lock(mutex_);
    lastReport_ += notificationStream.str();
}

} // namespace provider
} // namespace checkmk_agent
