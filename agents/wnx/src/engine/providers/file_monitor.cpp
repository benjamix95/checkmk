#include "stdafx.h"
#include "providers/file_monitor.h"

#include <fmt/format.h>
#include <filesystem>
#include <chrono>

#include "common/wtools.h"
#include "wnx/cfg.h"
#include "wnx/logger.h"
#include "wnx/section_header.h"

namespace fs = std::filesystem;
using namespace std::chrono_literals;

namespace cma::provider {

void FileMonitor::loadConfig() {
    // Load standard configuration from base class
    loadStandardConfig();

    auto paths = getConfiguredPaths();
    if (!paths) {
        XLOG::l("No file monitoring paths configured");
        return;
    }

    monitored_paths_.clear();
    for (const auto& path_node : *paths) {
        try {
            auto path_str = path_node["path"].as<std::string>();
            auto should_delete = path_node["delete"].as<bool>(false);
            
            MonitoredPath mp{
                fs::path(wtools::ConvertToUtf16(path_str)),
                std::chrono::system_clock::now(),
                should_delete
            };
            
            monitored_paths_.push_back(std::move(mp));
            XLOG::t("Added monitoring path '{}' with delete={}", path_str, should_delete);
        } catch (const std::exception& e) {
            XLOG::l.e("Error parsing file monitor config: {}", e.what());
        }
    }

    // Load check interval from config
    const auto monitor_section = cfg::GetLoadedConfig()["file_monitor"];
    if (monitor_section && monitor_section["check_interval"]) {
        check_interval_ = monitor_section["check_interval"].as<int>();
        XLOG::t("Set check interval to {} seconds", check_interval_);
    }
}

std::optional<YAML::Node> FileMonitor::getConfiguredPaths() const {
    try {
        const auto& config = cfg::GetLoadedConfig();
        const auto monitor_section = config["file_monitor"];
        
        if (!monitor_section || !monitor_section.IsMap()) {
            XLOG::t("'file_monitor' section absent or malformed");
            return {};
        }

        const auto paths = monitor_section["paths"];
        if (!paths || !paths.IsSequence()) {
            XLOG::t("'file_monitor.paths' section absent or malformed");
            return {};
        }

        return paths;
    } catch (const std::exception& e) {
        XLOG::l("CONFIG for 'file_monitor.paths' isn't valid: {}", e.what());
        return {};
    }
}

void FileMonitor::deleteFile(const std::filesystem::path& path) {
    try {
        if (fs::remove(path)) {
            sendNotification(fmt::format("File '{}' was successfully deleted", 
                wtools::ToUtf8(path.wstring())));
        }
    } catch (const std::exception& e) {
        XLOG::l.e("Error deleting file '{}': {}", 
            wtools::ToUtf8(path.wstring()), e.what());
    }
}

void FileMonitor::sendNotification(const std::string& message) {
    // Integrazione con il sistema di notifiche esistente
    XLOG::l(message);
}

void FileMonitor::checkAndNotify() {
    for (auto& mp : monitored_paths_) {
        try {
            std::error_code ec;
            if (fs::exists(mp.path, ec)) {
                // Se il file esiste, controlliamo se è un pattern glob
                if (cma::tools::GlobMatch(mp.path.wstring(), mp.path.wstring())) {
                    // Se è un pattern glob, cerchiamo tutti i file che corrispondono
                    for (const auto& entry : fs::directory_iterator(mp.path.parent_path())) {
                        if (cma::tools::GlobMatch(mp.path.wstring(), entry.path().wstring())) {
                            sendNotification(fmt::format("File '{}' found", 
                                wtools::ToUtf8(entry.path().wstring())));
                            
                            if (mp.should_delete) {
                                deleteFile(entry.path());
                            }
                        }
                    }
                } else {
                    // Se non è un pattern glob, processiamo direttamente il file
                    sendNotification(fmt::format("File '{}' found", 
                        wtools::ToUtf8(mp.path.wstring())));
                    
                    if (mp.should_delete) {
                        deleteFile(mp.path);
                    }
                }
            }
        } catch (const std::exception& e) {
            XLOG::l.e("Error checking file '{}': {}", 
                wtools::ToUtf8(mp.path.wstring()), e.what());
        }
    }
}

void FileMonitor::updateSectionStatus() {
    checkAndNotify();
    
    std::string output = section::MakeHeader("file_monitor");
    output += fmt::format("CheckInterval: {} seconds\n", check_interval_);
    
    for (const auto& mp : monitored_paths_) {
        std::error_code ec;
        bool exists = fs::exists(mp.path, ec);
        output += fmt::format("{}|{}|{}\n",
            wtools::ToUtf8(mp.path.wstring()),
            exists ? "found" : "not_found",
            mp.should_delete ? "will_delete" : "keep");
    }
    
    last_output_ = output;
}

std::string FileMonitor::makeBody() {
    return last_output_;
}

} // namespace cma::provider
