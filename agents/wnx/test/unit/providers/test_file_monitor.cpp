/**
 * @file test_file_monitor.cpp
 * @brief Test unitari per il File Monitor Provider
 */

#include "stdafx.h"
#include "providers/file_monitor.h"
#include <gtest/gtest.h>
#include <gmock/gmock.h>
#include <filesystem>
#include <fstream>
#include <thread>
#include <chrono>

using namespace checkmk_agent::provider;
using namespace testing;
namespace fs = std::filesystem;

class FileMonitorTest : public ::testing::Test {
protected:
    void SetUp() override {
        // Crea la directory temporanea per i test
        testDirectory = fs::temp_directory_path() / "checkmk_test";
        fs::create_directories(testDirectory);

        // Crea il file di configurazione di test
        configPath = testDirectory / "check_mk_dev_file_monitor.yml";
        CreateTestConfiguration();

        // Inizializza il provider
        provider = &FileMonitorProvider::GetInstance();
        provider->Initialize();
    }

    void TearDown() override {
        try {
            // Rimuove tutti i file e le directory di test
            fs::remove_all(testDirectory);
        }
        catch (const std::exception& e) {
            std::cerr << "Errore durante la pulizia: " << e.what() << std::endl;
        }
    }

    void CreateTestConfiguration() {
        std::ofstream config(configPath);
        config << R"(
file_monitor:
    check_interval: 1
    paths:
        - path: )" << (testDirectory / "test_files").string() << R"(
          is_directory: true
          delete: true
          pattern: "*.tmp"

        - path: )" << (testDirectory / "test.log").string() << R"(
          is_directory: false
          delete: false
          pattern: "*.log"
)";
        config.close();
    }

    void CreateTestFile(const fs::path& path, const std::string& content = "test") {
        std::ofstream file(path);
        file << content;
        file.close();
    }

    bool FileExists(const fs::path& path) {
        return fs::exists(path);
    }

    void WaitForNextCheck() {
        std::this_thread::sleep_for(std::chrono::seconds(2));
    }

protected:
    fs::path testDirectory;
    fs::path configPath;
    FileMonitorProvider* provider;
};

// Test di inizializzazione
TEST_F(FileMonitorTest, InitializationTest) {
    EXPECT_NO_THROW({
        FileMonitorProvider::GetInstance().Initialize();
    });
}

// Test del monitoraggio di un singolo file
TEST_F(FileMonitorTest, SingleFileMonitoringTest) {
    // Crea un file di test
    auto testFile = testDirectory / "test.log";
    CreateTestFile(testFile);

    // Verifica che il file esista
    EXPECT_TRUE(FileExists(testFile));

    // Esegue il monitoraggio
    provider->UpdateMonitoringStatus();

    // Verifica che il file sia ancora presente (non deve essere eliminato)
    EXPECT_TRUE(FileExists(testFile));

    // Verifica il report
    auto report = provider->GenerateReport();
    EXPECT_THAT(report, HasSubstr("test.log"));
}

// Test del monitoraggio di una directory
TEST_F(FileMonitorTest, DirectoryMonitoringTest) {
    // Crea una directory di test con alcuni file
    auto testFilesDir = testDirectory / "test_files";
    fs::create_directories(testFilesDir);

    // Crea file temporanei
    auto tempFile1 = testFilesDir / "test1.tmp";
    auto tempFile2 = testFilesDir / "test2.tmp";
    auto nonTempFile = testFilesDir / "test.txt";

    CreateTestFile(tempFile1);
    CreateTestFile(tempFile2);
    CreateTestFile(nonTempFile);

    // Verifica che i file esistano
    EXPECT_TRUE(FileExists(tempFile1));
    EXPECT_TRUE(FileExists(tempFile2));
    EXPECT_TRUE(FileExists(nonTempFile));

    // Esegue il monitoraggio
    provider->UpdateMonitoringStatus();
    WaitForNextCheck();

    // Verifica che i file temporanei siano stati eliminati
    EXPECT_FALSE(FileExists(tempFile1));
    EXPECT_FALSE(FileExists(tempFile2));
    
    // Verifica che il file non temporaneo sia ancora presente
    EXPECT_TRUE(FileExists(nonTempFile));

    // Verifica il report
    auto report = provider->GenerateReport();
    EXPECT_THAT(report, HasSubstr("test1.tmp"));
    EXPECT_THAT(report, HasSubstr("test2.tmp"));
    EXPECT_THAT(report, Not(HasSubstr("test.txt")));
}

// Test del pattern matching
TEST_F(FileMonitorTest, PatternMatchingTest) {
    auto testFilesDir = testDirectory / "test_files";
    fs::create_directories(testFilesDir);

    // Crea file con diversi pattern
    std::vector<fs::path> filesToMatch = {
        testFilesDir / "test1.tmp",
        testFilesDir / "test2.tmp",
        testFilesDir / "test.temp",
        testFilesDir / "test.txt"
    };

    for (const auto& file : filesToMatch) {
        CreateTestFile(file);
        EXPECT_TRUE(FileExists(file));
    }

    // Esegue il monitoraggio
    provider->UpdateMonitoringStatus();
    WaitForNextCheck();

    // Verifica che solo i file .tmp siano stati eliminati
    EXPECT_FALSE(FileExists(filesToMatch[0])); // test1.tmp
    EXPECT_FALSE(FileExists(filesToMatch[1])); // test2.tmp
    EXPECT_TRUE(FileExists(filesToMatch[2]));  // test.temp
    EXPECT_TRUE(FileExists(filesToMatch[3]));  // test.txt

    // Verifica il report
    auto report = provider->GenerateReport();
    EXPECT_THAT(report, HasSubstr("test1.tmp"));
    EXPECT_THAT(report, HasSubstr("test2.tmp"));
    EXPECT_THAT(report, Not(HasSubstr("test.temp")));
    EXPECT_THAT(report, Not(HasSubstr("test.txt")));
}

// Test dell'intervallo di controllo
TEST_F(FileMonitorTest, CheckIntervalTest) {
    auto testFile = testDirectory / "test_files" / "interval_test.tmp";
    fs::create_directories(testFile.parent_path());

    // Primo controllo
    CreateTestFile(testFile);
    EXPECT_TRUE(FileExists(testFile));
    
    provider->UpdateMonitoringStatus();
    WaitForNextCheck();
    
    EXPECT_FALSE(FileExists(testFile));

    // Secondo controllo - crea un nuovo file
    CreateTestFile(testFile);
    EXPECT_TRUE(FileExists(testFile));
    
    // Attende meno dell'intervallo di controllo
    std::this_thread::sleep_for(std::chrono::milliseconds(500));
    provider->UpdateMonitoringStatus();
    
    // Il file dovrebbe ancora esistere
    EXPECT_TRUE(FileExists(testFile));

    // Attende l'intervallo completo
    WaitForNextCheck();
    provider->UpdateMonitoringStatus();
    
    // Il file dovrebbe essere stato eliminato
    EXPECT_FALSE(FileExists(testFile));
}

// Test della gestione degli errori
TEST_F(FileMonitorTest, ErrorHandlingTest) {
    // Test con directory inesistente
    auto nonExistentDir = testDirectory / "non_existent";
    
    EXPECT_NO_THROW({
        provider->UpdateMonitoringStatus();
    });

    // Test con file bloccato
    auto lockedFile = testDirectory / "test_files" / "locked.tmp";
    fs::create_directories(lockedFile.parent_path());
    
    // Crea e mantiene aperto il file
    std::ofstream lockFile(lockedFile, std::ios::out | std::ios::binary);
    EXPECT_TRUE(FileExists(lockedFile));

    EXPECT_NO_THROW({
        provider->UpdateMonitoringStatus();
    });

    // Chiude il file
    lockFile.close();
}

// Test del report di monitoraggio
TEST_F(FileMonitorTest, MonitoringReportTest) {
    auto testFilesDir = testDirectory / "test_files";
    fs::create_directories(testFilesDir);

    // Crea alcuni file di test
    CreateTestFile(testFilesDir / "report1.tmp", "test content 1");
    CreateTestFile(testFilesDir / "report2.tmp", "test content 2");
    CreateTestFile(testFilesDir / "report.txt", "test content 3");

    // Esegue il monitoraggio
    provider->UpdateMonitoringStatus();
    WaitForNextCheck();

    // Ottiene il report
    auto report = provider->GenerateReport();

    // Verifica il contenuto del report
    EXPECT_THAT(report, HasSubstr("<<<file_monitor>>>"));
    EXPECT_THAT(report, HasSubstr("report1.tmp"));
    EXPECT_THAT(report, HasSubstr("report2.tmp"));
    EXPECT_THAT(report, Not(HasSubstr("report.txt")));
    EXPECT_THAT(report, HasSubstr("File eliminato"));
}

// Test della concorrenza
TEST_F(FileMonitorTest, ConcurrencyTest) {
    auto testFilesDir = testDirectory / "test_files";
    fs::create_directories(testFilesDir);

    // Funzione per creare file in un thread separato
    auto fileCreator = [&]() {
        for (int i = 0; i < 10; ++i) {
            CreateTestFile(testFilesDir / ("concurrent" + std::to_string(i) + ".tmp"));
            std::this_thread::sleep_for(std::chrono::milliseconds(100));
        }
    };

    // Funzione per eseguire il monitoraggio in un thread separato
    auto monitor = [&]() {
        for (int i = 0; i < 5; ++i) {
            provider->UpdateMonitoringStatus();
            std::this_thread::sleep_for(std::chrono::milliseconds(200));
        }
    };

    // Avvia i thread
    std::thread creatorThread(fileCreator);
    std::thread monitorThread(monitor);

    // Attende il completamento dei thread
    creatorThread.join();
    monitorThread.join();

    // Verifica finale
    provider->UpdateMonitoringStatus();
    WaitForNextCheck();

    // Verifica che tutti i file .tmp siano stati eliminati
    int remainingTmpFiles = 0;
    for (const auto& entry : fs::directory_iterator(testFilesDir)) {
        if (entry.path().extension() == ".tmp") {
            remainingTmpFiles++;
        }
    }
    EXPECT_EQ(remainingTmpFiles, 0);
}

// Test di stress
TEST_F(FileMonitorTest, StressTest) {
    auto testFilesDir = testDirectory / "test_files";
    fs::create_directories(testFilesDir);

    // Crea molti file
    const int numFiles = 1000;
    for (int i = 0; i < numFiles; ++i) {
        CreateTestFile(testFilesDir / ("stress" + std::to_string(i) + ".tmp"));
    }

    // Esegue il monitoraggio
    provider->UpdateMonitoringStatus();
    WaitForNextCheck();

    // Verifica che tutti i file siano stati elaborati
    int remainingFiles = 0;
    for (const auto& entry : fs::directory_iterator(testFilesDir)) {
        if (entry.path().extension() == ".tmp") {
            remainingFiles++;
        }
    }
    EXPECT_EQ(remainingFiles, 0);

    // Verifica il report
    auto report = provider->GenerateReport();
    EXPECT_THAT(report, HasSubstr("File trovati: " + std::to_string(numFiles)));
}

int main(int argc, char** argv) {
    testing::InitGoogleTest(&argc, argv);
    return RUN_ALL_TESTS();
}
