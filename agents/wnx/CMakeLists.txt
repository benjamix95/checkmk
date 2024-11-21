###############################################################################
# File di configurazione CMake principale
###############################################################################

cmake_minimum_required(VERSION 3.20)
project(checkmk_agent_windows VERSION 2.0.0)

# Imposta le opzioni di compilazione
set(CMAKE_CXX_STANDARD 17)
set(CMAKE_CXX_STANDARD_REQUIRED ON)
set(CMAKE_CXX_EXTENSIONS OFF)

# Configurazione di vcpkg
if(DEFINED ENV{VCPKG_ROOT} AND NOT DEFINED CMAKE_TOOLCHAIN_FILE)
    set(CMAKE_TOOLCHAIN_FILE "$ENV{VCPKG_ROOT}/scripts/buildsystems/vcpkg.cmake"
        CACHE STRING "")
endif()

# Definizioni del compilatore
if(MSVC)
    add_definitions(
        -D_UNICODE 
        -DUNICODE 
        -DWIN32_LEAN_AND_MEAN 
        -DNOMINMAX
        -D_CRT_SECURE_NO_WARNINGS
        -DYAML_CPP_DLL
        -DFMT_SHARED
    )
    
    # Opzioni del compilatore MSVC
    set(CMAKE_CXX_FLAGS "${CMAKE_CXX_FLAGS} /W4 /WX /wd4251 /wd4275")
    set(CMAKE_CXX_FLAGS_RELEASE "${CMAKE_CXX_FLAGS_RELEASE} /O2")
    set(CMAKE_CXX_FLAGS_DEBUG "${CMAKE_CXX_FLAGS_DEBUG} /Od /Zi")

    # Abilita il supporto multi-processo
    set(CMAKE_CXX_FLAGS "${CMAKE_CXX_FLAGS} /MP")
endif()

# Opzioni di build
option(BUILD_TESTING "Build tests" OFF)
option(BUILD_DOCS "Build documentation" OFF)

# Trova le dipendenze
find_package(fmt CONFIG REQUIRED)
find_package(yaml-cpp CONFIG REQUIRED)

if(BUILD_TESTING)
    enable_testing()
    find_package(GTest CONFIG REQUIRED)
endif()

# Aggiungi le directory degli include
include_directories(
    ${CMAKE_SOURCE_DIR}/include
    ${CMAKE_SOURCE_DIR}/src
    ${CMAKE_SOURCE_DIR}/src/engine  # Aggiunto per stdafx.h
    ${CMAKE_SOURCE_DIR}/test/unit
    ${YAML_CPP_INCLUDE_DIR}
    ${FMT_INCLUDE_DIRS}
)

# Definisci i file sorgente per il modulo engine
set(ENGINE_SOURCES
    src/engine/stdafx.cpp
    src/engine/providers/file_monitor.cpp
)

# Crea la libreria engine
add_library(engine SHARED ${ENGINE_SOURCES})

# Imposta le opzioni del compilatore per il precompiled header
if(MSVC)
    # Imposta stdafx.h come header precompilato
    set_source_files_properties(
        src/engine/stdafx.cpp
        PROPERTIES
        COMPILE_FLAGS "/Yc\"stdafx.h\""
    )
    
    # Usa l'header precompilato per tutti gli altri file
    set_source_files_properties(
        src/engine/providers/file_monitor.cpp
        PROPERTIES
        COMPILE_FLAGS "/Yu\"stdafx.h\" /FI\"stdafx.h\""
    )
endif()

# Configura la libreria engine
target_compile_definitions(engine
    PRIVATE
        ENGINE_EXPORTS
        $<$<CONFIG:Debug>:_DEBUG>
        $<$<CONFIG:Release>:NDEBUG>
)

# Collega le dipendenze usando i target corretti
target_link_libraries(engine
    PRIVATE
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

# Configura le directory di output
set_target_properties(engine PROPERTIES
    RUNTIME_OUTPUT_DIRECTORY "${CMAKE_BINARY_DIR}/bin"
    LIBRARY_OUTPUT_DIRECTORY "${CMAKE_BINARY_DIR}/lib"
    ARCHIVE_OUTPUT_DIRECTORY "${CMAKE_BINARY_DIR}/lib"
    PDB_OUTPUT_DIRECTORY "${CMAKE_BINARY_DIR}/bin"
)

# Aggiungi le sottodirectory
add_subdirectory(src/engine/providers)

if(BUILD_TESTING)
    add_subdirectory(test/unit)
endif()

# Installa i file necessari
install(TARGETS engine
    RUNTIME DESTINATION bin
    LIBRARY DESTINATION lib
    ARCHIVE DESTINATION lib
)

# Installa gli header
install(DIRECTORY include/
    COMPONENT development
    DESTINATION include
    FILES_MATCHING PATTERN "*.h"
)

# Installa i file di configurazione
install(FILES
    test_files/config/check_mk_dev_file_monitor_example.yml
    DESTINATION share/check_mk/agents/windows/config_examples
)

# Installa la documentazione
install(FILES
    doc/file_monitor.md
    DESTINATION share/check_mk/agents/windows/docs
)

# Configura il pacchetto
set(CPACK_PACKAGE_NAME "checkmk-agent-windows")
set(CPACK_PACKAGE_VENDOR "tribe29 GmbH")
set(CPACK_PACKAGE_DESCRIPTION_SUMMARY "Check_MK Windows Agent with File Monitoring")
set(CPACK_PACKAGE_VERSION ${PROJECT_VERSION})
set(CPACK_PACKAGE_INSTALL_DIRECTORY "CheckMK")

# Configurazione specifica per Windows
if(WIN32)
    set(CPACK_GENERATOR "WIX")
    set(CPACK_WIX_UPGRADE_GUID "12345678-1234-1234-1234-123456789012")
    set(CPACK_WIX_PRODUCT_GUID "87654321-4321-4321-4321-210987654321")
endif()

include(CPack)

# Configurazione per il debug
if(CMAKE_BUILD_TYPE STREQUAL "Debug")
    add_definitions(-D_DEBUG)
endif()

# Configurazione per il rilascio
if(CMAKE_BUILD_TYPE STREQUAL "Release")
    add_definitions(-DNDEBUG)
endif()

# Configurazione per i test
if(BUILD_TESTING)
    enable_testing()
    add_definitions(-DUNIT_TESTING)
endif()

# Configurazione per la documentazione
if(BUILD_DOCS)
    find_package(Doxygen)
    if(DOXYGEN_FOUND AND EXISTS "${CMAKE_SOURCE_DIR}/docs/Doxyfile.in")
        set(DOXYGEN_IN ${CMAKE_SOURCE_DIR}/docs/Doxyfile.in)
        set(DOXYGEN_OUT ${CMAKE_CURRENT_BINARY_DIR}/Doxyfile)
        configure_file(${DOXYGEN_IN} ${DOXYGEN_OUT} @ONLY)
        
        add_custom_target(docs
            COMMAND ${DOXYGEN_EXECUTABLE} ${DOXYGEN_OUT}
            WORKING_DIRECTORY ${CMAKE_CURRENT_BINARY_DIR}
            COMMENT "Generating API documentation with Doxygen"
            VERBATIM
        )
    endif()
endif()

# Messaggio di configurazione completata
message(STATUS "Configurazione CMake completata per ${PROJECT_NAME} v${PROJECT_VERSION}")
message(STATUS "Generator: ${CMAKE_GENERATOR}")
message(STATUS "Build Type: ${CMAKE_BUILD_TYPE}")
message(STATUS "C++ Standard: ${CMAKE_CXX_STANDARD}")
message(STATUS "Compiler ID: ${CMAKE_CXX_COMPILER_ID}")
message(STATUS "Compiler Version: ${CMAKE_CXX_COMPILER_VERSION}")
