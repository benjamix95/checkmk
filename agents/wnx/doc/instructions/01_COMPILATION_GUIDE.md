# Guida alla Compilazione del File Monitor Provider

## Indice
1. [Prerequisiti](#prerequisiti)
2. [Setup Ambiente](#setup-ambiente)
3. [Compilazione](#compilazione)
4. [Troubleshooting](#troubleshooting)

## Prerequisiti

### Software Richiesto
1. Microsoft Visual Studio 2022
   - Versione Professional o Enterprise
   - Workload "Sviluppo desktop C++"
   - Componenti singoli:
     - MSVC v143 build tools
     - Windows 10 SDK (10.0.22621.0)
     - C++ CMake tools
     - C++ ATL per build tools v143
     - Test Adapter per Google Test

2. CMake
   - Versione minima: 3.20
   - Installazione completa con aggiunta al PATH di sistema

3. Git per Windows
   - Versione recente con supporto LFS
   - Configurazione per gestione line-ending Windows

4. Python
   - Versione 3.8 o superiore
   - Pip package manager
   - Virtualenv (opzionale ma consigliato)

### Librerie di Sviluppo
1. vcpkg
   - Installazione in C:\dev\tools\vcpkg
   - Integrazione con Visual Studio
   - Librerie richieste:
     - yaml-cpp:x64-windows
     - fmt:x64-windows
     - gtest:x64-windows

2. Windows SDK
   - Componenti di sviluppo Windows
   - Header di sistema
   - Librerie di sistema

### Ambiente di Sviluppo
1. Variabili d'Ambiente
   - VCPKG_ROOT=C:\dev\tools\vcpkg
   - CMAKE_TOOLCHAIN_FILE=%VCPKG_ROOT%\scripts\buildsystems\vcpkg.cmake
   - PATH aggiornato per includere:
     - Visual Studio build tools
     - CMake
     - Git
     - Python

2. Configurazione Visual Studio
   - Estensioni installate:
     - CMake Tools
     - C++ Tools
     - Git Tools
     - Test Explorer UI

## Procedura di Compilazione

### 1. Preparazione dell'Ambiente

1.1. Clonazione del Repository
```batch
mkdir C:\Dev\Projects
cd C:\Dev\Projects
git clone https://github.com/Checkmk/checkmk.git
cd checkmk
```

1.2. Installazione Dipendenze
```batch
cd C:\dev\tools\vcpkg
vcpkg install yaml-cpp:x64-windows
vcpkg install fmt:x64-windows
vcpkg install gtest:x64-windows
vcpkg integrate install
```

1.3. Creazione Directory di Build
```batch
cd C:\Dev\Projects\checkmk\agents\wnx
mkdir build
cd build
```

### 2. Configurazione del Progetto

2.1. Generazione File di Progetto Visual Studio
```batch
cmake -G "Visual Studio 17 2022" -A x64 ^
    -DCMAKE_BUILD_TYPE=Release ^
    -DCMAKE_TOOLCHAIN_FILE=C:/dev/tools/vcpkg/scripts/buildsystems/vcpkg.cmake ^
    -DCMAKE_PREFIX_PATH=C:/dev/tools/vcpkg/installed/x64-windows ^
    -DBUILD_TESTING=ON ^
    ..
```

2.2. Verifica Configurazione
- Controllare il file CMakeCache.txt
- Verificare le dipendenze trovate
- Controllare i percorsi configurati
- Verificare le opzioni di build

### 3. Compilazione

3.1. Build Completo
```batch
cmake --build . --config Release
```

3.2. Build dei Componenti Specifici
```batch
cmake --build . --config Release --target engine
cmake --build . --config Release --target file_monitor
cmake --build . --config Release --target unit_tests
```

3.3. Verifica della Compilazione
- Controllare i file di output
- Verificare i log di compilazione
- Controllare le dipendenze
- Verificare i simboli esportati

### 4. Test

4.1. Esecuzione Test Unitari
```batch
ctest -C Release -V
```

4.2. Verifica dei Risultati
- Analizzare i report dei test
- Verificare la copertura
- Controllare i log di errore
- Validare le funzionalità

### 5. Installazione

5.1. Creazione Pacchetto di Installazione
```batch
cmake --build . --config Release --target package
```

5.2. Verifica del Pacchetto
- Controllare i file inclusi
- Verificare le dipendenze
- Testare l'installazione
- Validare la configurazione

## Risoluzione Problemi

### Problemi Comuni

1. Errori di Compilazione
   - Verificare i prerequisiti
   - Controllare le versioni delle dipendenze
   - Aggiornare gli strumenti di sviluppo
   - Pulire la directory di build

2. Errori di Linking
   - Verificare le librerie
   - Controllare i path
   - Aggiornare vcpkg
   - Ricostruire le dipendenze

3. Errori di Test
   - Verificare l'ambiente di test
   - Controllare i file di configurazione
   - Analizzare i log dettagliati
   - Ricostruire i test

### Procedure di Debug

1. Build Debug
```batch
cmake --build . --config Debug
```

2. Analisi dei Log
- CMake output
- Compiler output
- Linker output
- Test output

3. Strumenti di Diagnostica
- Visual Studio Debugger
- Process Explorer
- Dependency Walker
- Event Viewer

## Manutenzione

### Aggiornamenti

1. Aggiornamento Dipendenze
```batch
vcpkg upgrade
vcpkg update
```

2. Pulizia Build
```batch
cmake --build . --target clean
rmdir /S /Q build
mkdir build
```

3. Ricostruzione Completa
- Eliminare la directory build
- Riconfigurare CMake
- Ricompilare tutto
- Rieseguire i test

### Backup

1. Source Code
- Commit regolari
- Push su repository
- Backup locali
- Documentazione modifiche

2. Build Artifacts
- Backup binari
- Backup configurazioni
- Backup log
- Backup test results

## Note Aggiuntive

### Ottimizzazioni

1. Compilazione
- Parallel build
- Precompiled headers
- Link-time optimization
- Profile-guided optimization

2. Performance
- Debug symbols
- Release flags
- Optimization levels
- Memory management

### Sicurezza

1. Codice
- Code signing
- Verifica integrità
- Scanning vulnerabilità
- Analisi statica

2. Build
- Ambiente isolato
- Controllo accessi
- Logging sicuro
- Audit trail

### Documentazione

1. Build System
- CMake files
- Build scripts
- Dependency management
- Configuration options

2. Processo
- Step-by-step guide
- Troubleshooting
- Best practices
- Known issues
