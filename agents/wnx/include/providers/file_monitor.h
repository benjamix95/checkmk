#pragma once

#include <string>
#include <vector>
#include <filesystem>
#include <chrono>
#include <optional>

#include "providers/plugins.h"
#include "wnx/cfg.h"

namespace cma::provider {

class FileMonitor final : public Synchronous {
public:
    static FileMonitor& Instance() {
        static FileMonitor instance;
        return instance;
    }

    void loadConfig() override;
    std::string makeBody() override;
    void updateSectionStatus() override;

private:
    FileMonitor() : Synchronous("file_monitor") {
        setupDelayOnFail();
    }

    struct MonitoredPath {
        std::filesystem::path path;
        std::chrono::system_clock::time_point last_check;
        bool should_delete;
    };

    std::vector<MonitoredPath> monitored_paths_;
    int check_interval_{300}; // Default 5 minutes
    std::string last_output_;
    
    void deleteFile(const std::filesystem::path& path);
    void sendNotification(const std::string& message);
    std::optional<YAML::Node> getConfiguredPaths() const;
    void checkAndNotify();

    // Prevent copying
    FileMonitor(const FileMonitor&) = delete;
    FileMonitor& operator=(const FileMonitor&) = delete;
    FileMonitor(FileMonitor&&) = delete;
    FileMonitor& operator=(FileMonitor&&) = delete;
};

} // namespace cma::provider
