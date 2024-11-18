#include "pch.h"

#include "providers/file_monitor.h"
#include "tools/_misc.h"
#include "wnx/cfg.h"

using namespace std::chrono_literals;

namespace cma::provider {

class FileMonitorTest : public ::testing::Test {
protected:
    void SetUp() override {
        // Create test directory
        test_dir_ = fs::path(wtools::GetTempDir()) / L"file_monitor_test";
        fs::create_directories(test_dir_);

        // Create test files
        createTestFiles();

        // Load test configuration
        cfg::LoadConfig(L"test_files/config/check_mk_dev_file_monitor_test.yml");
    }

    void TearDown() override {
        // Clean up test files
        fs::remove_all(test_dir_);
    }

    void createTestFiles() {
        // Create single test file
        auto single_file = test_dir_ / L"test_single.txt";
        std::ofstream(single_file) << "Test content";

        // Create multiple log files
        for (int i = 1; i <= 3; ++i) {
            auto log_file = test_dir_ / fmt::format(L"test_{}.log", i);
            std::ofstream(log_file) << fmt::format("Log content {}", i);
        }

        // Create temp files in subdirectories
        auto sub_dir = test_dir_ / L"subdir";
        fs::create_directories(sub_dir);
        for (int i = 1; i <= 2; ++i) {
            auto tmp_file = sub_dir / fmt::format(L"test_{}.tmp", i);
            std::ofstream(tmp_file) << fmt::format("Temp content {}", i);
        }
    }

    bool fileExists(const std::wstring& filename) {
        return fs::exists(test_dir_ / filename);
    }

    fs::path test_dir_;
};

TEST_F(FileMonitorTest, LoadConfig) {
    auto& monitor = FileMonitor::Instance();
    monitor.loadConfig();

    // Verify configuration was loaded
    EXPECT_EQ(monitor.timeout(), 60);
    EXPECT_TRUE(monitor.isAllowedByCurrentConfig());
}

TEST_F(FileMonitorTest, MonitorSingleFile) {
    auto& monitor = FileMonitor::Instance();
    monitor.loadConfig();

    // Get initial output
    auto output = monitor.makeBody();
    EXPECT_TRUE(output.find("test_single.txt|found") != std::string::npos);

    // Delete the file and check again
    monitor.updateSectionStatus();
    output = monitor.makeBody();
    EXPECT_TRUE(output.find("test_single.txt|not_found") != std::string::npos);
}

TEST_F(FileMonitorTest, MonitorGlobPattern) {
    auto& monitor = FileMonitor::Instance();
    monitor.loadConfig();

    // Check all log files are found
    auto output = monitor.makeBody();
    EXPECT_TRUE(output.find("test_1.log|found") != std::string::npos);
    EXPECT_TRUE(output.find("test_2.log|found") != std::string::npos);
    EXPECT_TRUE(output.find("test_3.log|found") != std::string::npos);
}

TEST_F(FileMonitorTest, MonitorRecursive) {
    auto& monitor = FileMonitor::Instance();
    monitor.loadConfig();

    // Check temp files in subdirectory
    auto output = monitor.makeBody();
    EXPECT_TRUE(output.find("subdir\\test_1.tmp|found") != std::string::npos);
    EXPECT_TRUE(output.find("subdir\\test_2.tmp|found") != std::string::npos);

    // Verify files are deleted
    monitor.updateSectionStatus();
    EXPECT_FALSE(fileExists(L"subdir\\test_1.tmp"));
    EXPECT_FALSE(fileExists(L"subdir\\test_2.tmp"));
}

TEST_F(FileMonitorTest, NotificationSystem) {
    auto& monitor = FileMonitor::Instance();
    monitor.loadConfig();

    // Create a new file to trigger notification
    auto new_file = test_dir_ / L"test_new.tmp";
    std::ofstream(new_file) << "New content";

    // Update and verify notification
    monitor.updateSectionStatus();
    auto output = monitor.makeBody();
    EXPECT_TRUE(output.find("test_new.tmp|found") != std::string::npos);
    EXPECT_FALSE(fileExists(L"test_new.tmp")); // Should be deleted
}

} // namespace cma::provider
