#pragma once

#include "stdafx.h"

#include <filesystem>
#include <string>
#include <vector>
#include <chrono>
#include <optional>

#include "common/wtools.h"
#include "wnx/cfg.h"

namespace cma::provider {

class FileMonitor {
public:
    static FileMonitor& Instance() {
        static FileMonitor instance;
        return instance;
    }

    void loadConfig();
    std::string makeBody();

private:
    FileMonitor() = default;

    struct MonitoredPath {
        std::filesystem::path path;
        std::chrono::system_clock::time_point last_check;
        bool should_delete;
    };

    std::vector<MonitoredPath> monitored_paths_;
    
    void deleteFile(const std::filesystem::path& path);
    void sendNotification(const std::string& message);
    std::optional<YAML::Node> getConfiguredPaths() const;
    void checkAndNotify();
};

} // namespace cma::provider
