###############################################################################
# File di configurazione CMake per i test unitari
###############################################################################

# Definizione dei file sorgente per i test
set(FILE_MONITOR_TEST_SOURCE_FILES
    providers/test_file_monitor.cpp
)

# Creazione dell'eseguibile dei test
add_executable(unit_tests
    ${FILE_MONITOR_TEST_SOURCE_FILES}
)

# Configurazione delle directory di inclusione
target_include_directories(unit_tests
    PRIVATE
        # Directory principale degli header
        ${CMAKE_SOURCE_DIR}/include
        
        # Directory dei sorgenti
        ${CMAKE_SOURCE_DIR}/src
        
        # Directory dei test
        ${CMAKE_SOURCE_DIR}/test/unit
        
        # Directory specifica dei provider
        ${CMAKE_SOURCE_DIR}/src/engine/providers
)

# Collegamento delle librerie
target_link_libraries(unit_tests
    PRIVATE
        # Libreria principale da testare
        engine
        
        # Framework di test
        GTest::gtest
        GTest::gtest_main
        GTest::gmock
        GTest::gmock_main
        
        # Librerie di supporto
        fmt::fmt
        yaml-cpp::yaml-cpp
        
        # Librerie di sistema Windows
        wsock32
        ws2_32
        psapi
        iphlpapi
        userenv
        version
        wbemuuid
        oleaut32
        ole32
        uuid
        shell32
        user32
        gdi32
        kernel32
        advapi32
        wtsapi32
        pdh
        netapi32
        shlwapi
)

# Definizioni del compilatore
target_compile_definitions(unit_tests
    PRIVATE
        # Definizioni per il supporto Unicode
        UNICODE
        _UNICODE
        
        # Ottimizzazioni Windows
        WIN32_LEAN_AND_MEAN
        NOMINMAX
        
        # Disabilita gli avvisi di sicurezza
        _CRT_SECURE_NO_WARNINGS
        
        # Definizioni per i test
        UNIT_TESTING
        
        # Definizioni condizionali per Debug/Release
        $<$<CONFIG:Debug>:
            _DEBUG
            DEBUG
        >
        $<$<CONFIG:Release>:
            NDEBUG
        >
)

# Configurazione delle opzioni del compilatore Microsoft Visual C++
if(MSVC)
    target_compile_options(unit_tests
        PRIVATE
            # Livello di avviso massimo
            /W4
            
            # Tratta gli avvisi come errori
            /WX
            
            # Disabilita avvisi specifici
            /wd4251  # class needs to have dll-interface
            /wd4275  # non dll-interface class used as base
            
            # Ottimizzazioni per la build Release
            $<$<CONFIG:Release>:
                /O2      # Ottimizzazione massima
                /Oi      # Genera funzioni intrinseche
                /Gy      # Function-level linking
                /GL      # Whole program optimization
                /Zi      # Debug info in PDB
            >
            
            # Configurazioni per la build Debug
            $<$<CONFIG:Debug>:
                /Od      # Disabilita ottimizzazioni
                /Zi      # Debug info in PDB
                /RTC1    # Runtime error checks
            >
    )
    
    # Opzioni del linker
    target_link_options(unit_tests
        PRIVATE
            # Ottimizzazioni per la build Release
            $<$<CONFIG:Release>:
                /LTCG    # Link-time code generation
                /OPT:REF # Elimina funzioni/dati non referenziati
                /OPT:ICF # Folding di funzioni identiche
            >
            
            # Genera file PDB per il debug
            /DEBUG
            
            # Genera file MAP per il debug
            /MAP
    )
endif()

# Configurazione delle proprietà dell'eseguibile dei test
set_target_properties(unit_tests PROPERTIES
    # Nome output
    OUTPUT_NAME "checkmk_file_monitor_tests"
    
    # Cartella di output
    RUNTIME_OUTPUT_DIRECTORY "${CMAKE_BINARY_DIR}/bin"
    
    # Cartella PDB
    PDB_OUTPUT_DIRECTORY "${CMAKE_BINARY_DIR}/bin"
)

# Aggiunta dei test al sistema di test di CMake
add_test(
    NAME file_monitor_tests
    COMMAND unit_tests
    WORKING_DIRECTORY ${CMAKE_BINARY_DIR}/bin
)

# Configurazione dell'ambiente di test
set_tests_properties(file_monitor_tests
    PROPERTIES
        # Timeout per i test (in secondi)
        TIMEOUT 300
        
        # Directory di lavoro per i test
        WORKING_DIRECTORY "${CMAKE_BINARY_DIR}/bin"
        
        # Variabili d'ambiente per i test
        ENVIRONMENT "PATH=${CMAKE_BINARY_DIR}/bin;$ENV{PATH}"
)

# Installazione dell'eseguibile dei test
install(TARGETS unit_tests
    RUNTIME DESTINATION bin
    CONFIGURATIONS Debug
    COMPONENT development
)

# Installazione dei file di configurazione di test
install(FILES
    ${CMAKE_SOURCE_DIR}/test_files/config/check_mk_dev_file_monitor_test.yml
    DESTINATION share/checkmk/agents/windows/test_config
)
