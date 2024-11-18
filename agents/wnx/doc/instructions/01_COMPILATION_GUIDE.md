# Guida alla Compilazione del File Monitor Provider

## Indice
1. [Prerequisiti](#prerequisiti)
2. [Setup Ambiente](#setup-ambiente)
3. [Compilazione](#compilazione)
4. [Troubleshooting](#troubleshooting)

## Prerequisiti

### 1. Software Richiesto
```plaintext
1. Visual Studio 2019 o superiore
   - Workload "Sviluppo desktop C++"
   - Componenti singoli:
     * MSVC v142 build tools
     * Windows 10 SDK
     * C++ CMake tools

2. CMake 3.15 o superiore
   - Scaricabile da: https://cmake.org/download/
   - Aggiungere al PATH di sistema

3. Git for Windows
   - Necessario per clonare il repository
   - Configurare git con credenziali

4. Python 3.8 o superiore
   - Necessario per gli script di build
   - Aggiungere al PATH di sistema
```

### 2. Librerie Richieste
```plaintext
1. yaml-cpp
   - Versione: 0.6.3 o superiore
   - Usata per parsing configurazione

2. fmt
   - Versione: 7.0.0 o superiore
   - Usata per formattazione stringhe

3. GoogleTest
   - Versione: 1.10.0 o superiore
   - Necessario per unit testing
```

### 3. Spazio su Disco
```plaintext
- 2GB per il codice sorgente
- 5GB per la build completa
- 1GB per le dipendenze
```

## Setup Ambiente

### 1. Clonare il Repository
```batch
# 1. Creare directory di lavoro
mkdir C:\Dev
cd C:\Dev

# 2. Clonare repository
git clone https://github.com/Checkmk/checkmk.git
cd checkmk

# 3. Verificare struttura
dir agents\wnx
```

### 2. Configurare Visual Studio
```plaintext
1. Aprire Visual Studio
2. Selezionare: Strumenti -> Ottieni Strumenti e Funzionalità
3. Installare:
   - Sviluppo di Windows Desktop con C++
   - Sviluppo multipiattaforma C++
   - Strumenti CMake di Visual C++
```

### 3. Configurare Variabili Ambiente
```batch
# 1. Variabili di Sistema
setx CHECKMK_DEV C:\Dev\checkmk
setx CHECKMK_BUILD C:\Dev\checkmk\build

# 2. Variabili Build
setx CMAKE_PREFIX_PATH C:\Libraries
setx YAML_ROOT C:\Libraries\yaml-cpp
setx FMT_ROOT C:\Libraries\fmt
```

## Compilazione

### 1. Generare Soluzione Visual Studio
```batch
# 1. Creare directory build
mkdir %CHECKMK_BUILD%
cd %CHECKMK_BUILD%

# 2. Generare soluzione VS
cmake -G "Visual Studio 16 2019" -A x64 ^
    -DCMAKE_BUILD_TYPE=Release ^
    -DBUILD_TESTING=ON ^
    -DYAML_CPP_BUILD_TESTS=OFF ^
    -DFMT_DOC=OFF ^
    %CHECKMK_DEV%

# Perché questi flag:
# - Visual Studio 2019 64-bit
# - Build Release per performance
# - Testing abilitato per verifiche
# - Disabilita test yaml-cpp per velocità
# - Disabilita doc fmt per velocità
```

### 2. Compilare il Progetto
```batch
# 1. Compilare tutto
cmake --build . --config Release

# 2. Compilare solo l'agente
cmake --build . --config Release --target check_mk_agent

# 3. Compilare i test
cmake --build . --config Release --target check_mk_tests
```

### 3. Verificare la Build
```batch
# 1. Eseguire i test
ctest -C Release -R FileMonitorTest

# 2. Verificare l'output
type Testing\Temporary\LastTest.log

# 3. Verificare i file generati
dir Release\check_mk_agent.exe
dir Release\check_mk_tests.exe
```

## Troubleshooting

### 1. Errori Comuni

#### CMake non trova yaml-cpp
```plaintext
Errore: Could not find yaml-cpp

Soluzione:
1. Verificare YAML_ROOT
2. Verificare installazione yaml-cpp
3. Aggiungere manualmente in CMakeLists.txt:
   set(YAML_CPP_ROOT "C:/Libraries/yaml-cpp")
```

#### Errori di Linking
```plaintext
Errore: LNK2019: unresolved external symbol

Soluzione:
1. Verificare librerie nel path
2. Ricompilare in modalità Debug
3. Verificare versioni librerie
```

#### Errori di Compilazione
```plaintext
Errore: C2065: undeclared identifier

Soluzione:
1. Verificare include path
2. Verificare dipendenze
3. Pulire e ricompilare
```

### 2. Procedure di Recovery

#### Clean Build
```batch
# 1. Eliminare directory build
rd /s /q %CHECKMK_BUILD%

# 2. Ricreare directory
mkdir %CHECKMK_BUILD%
cd %CHECKMK_BUILD%

# 3. Rigenerare soluzione
cmake -G "Visual Studio 16 2019" -A x64 %CHECKMK_DEV%
```

#### Reset Environment
```batch
# 1. Backup configurazione
copy CMakeCache.txt CMakeCache.txt.bak

# 2. Reset cache
del CMakeCache.txt

# 3. Riconfigurare
cmake %CHECKMK_DEV%
```

### 3. Verifica Ambiente

#### Test Sistema
```batch
# 1. Verificare Visual Studio
cl.exe

# 2. Verificare CMake
cmake --version

# 3. Verificare Python
python --version
```

#### Test Librerie
```batch
# 1. Verificare yaml-cpp
dir %YAML_ROOT%\lib\yaml-cpp.lib

# 2. Verificare fmt
dir %FMT_ROOT%\lib\fmt.lib

# 3. Verificare GoogleTest
dir %GTEST_ROOT%\lib\gtest.lib
```

## Note Aggiuntive

### 1. Performance Build
```plaintext
1. Utilizzare compilazione parallela
   cmake --build . -j 8

2. Disabilitare feature non necessarie
   -DBUILD_DOCS=OFF
   -DBUILD_EXAMPLES=OFF

3. Utilizzare link-time optimization
   -DCMAKE_INTERPROCEDURAL_OPTIMIZATION=ON
```

### 2. Debug Build
```plaintext
1. Abilitare simboli debug
   cmake -DCMAKE_BUILD_TYPE=Debug

2. Abilitare sanitizers
   -DENABLE_ASAN=ON
   -DENABLE_UBSAN=ON

3. Abilitare logging dettagliato
   -DDETAILED_LOGGING=ON
```

### 3. Best Practices
```plaintext
1. Sempre pulire prima di switch branch
2. Utilizzare build incrementali
3. Verificare test dopo modifiche
4. Mantenere ambiente aggiornato
5. Documentare modifiche build
