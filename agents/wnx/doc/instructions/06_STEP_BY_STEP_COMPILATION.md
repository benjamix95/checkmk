# Guida Passo-Passo alla Compilazione del File Monitor

## Indice
1. [Setup Ambiente di Sviluppo](#setup-ambiente-di-sviluppo)
2. [Installazione Dipendenze](#installazione-dipendenze)
3. [Compilazione](#compilazione)
4. [Verifica](#verifica)

## Setup Ambiente di Sviluppo

### 1. Installazione Visual Studio 2019
```plaintext
1. Scarica Visual Studio 2019 Community
   - Vai a: https://visualstudio.microsoft.com/vs/older-downloads/
   - Scarica "Visual Studio 2019 Community"

2. Esegui l'installer
   - Doppio click su "vs_community_2019.exe"
   - Seleziona "Nuova installazione"

3. Seleziona i componenti:
   ✓ Sviluppo di Windows Desktop con C++
   ✓ Sviluppo multipiattaforma C++
   ✓ Strumenti CMake di Visual C++
   ✓ Windows 10 SDK

4. Completa l'installazione
   - Clicca "Installa"
   - Attendi il completamento
   - Riavvia il computer
```

### 2. Installazione Git
```plaintext
1. Scarica Git for Windows
   - Vai a: https://git-scm.com/download/win
   - Scarica la versione 64-bit

2. Esegui l'installer
   - Doppio click su "Git-X.XX.X-64-bit.exe"
   - Usa le opzioni predefinite
   - Seleziona "Use Visual Studio Code as default editor"

3. Configura Git
   git config --global user.name "Il tuo nome"
   git config --global user.email "tua@email.com"
```

### 3. Installazione Python
```plaintext
1. Scarica Python
   - Vai a: https://www.python.org/downloads/
   - Scarica Python 3.8 o superiore

2. Esegui l'installer
   - Seleziona "Add Python to PATH"
   - Clicca "Install Now"

3. Verifica installazione
   - Apri cmd
   - Digita: python --version
   - Dovrebbe mostrare la versione installata
```

## Installazione Dipendenze

### 1. Creazione Directory di Lavoro
```batch
# 1. Crea directory base
mkdir C:\Dev
cd C:\Dev

# 2. Crea directory librerie
mkdir C:\Dev\libs
cd C:\Dev\libs
```

### 2. Installazione yaml-cpp
```batch
# 1. Clone repository
git clone https://github.com/jbeder/yaml-cpp.git
cd yaml-cpp

# 2. Crea directory build
mkdir build
cd build

# 3. Configura CMake
cmake -G "Visual Studio 16 2019" -A x64 ^
    -DCMAKE_BUILD_TYPE=Release ^
    -DYAML_CPP_BUILD_TESTS=OFF ^
    ..

# 4. Compila
cmake --build . --config Release

# 5. Copia file necessari
mkdir C:\Dev\libs\yaml-cpp-install
xcopy /E /I include C:\Dev\libs\yaml-cpp-install\include
xcopy /E /I Release\*.lib C:\Dev\libs\yaml-cpp-install\lib
```

### 3. Installazione fmt
```batch
# 1. Clone repository
cd C:\Dev\libs
git clone https://github.com/fmtlib/fmt.git
cd fmt

# 2. Crea directory build
mkdir build
cd build

# 3. Configura CMake
cmake -G "Visual Studio 16 2019" -A x64 ^
    -DCMAKE_BUILD_TYPE=Release ^
    -DFMT_DOC=OFF ^
    -DFMT_TEST=OFF ^
    ..

# 4. Compila
cmake --build . --config Release

# 5. Copia file necessari
mkdir C:\Dev\libs\fmt-install
xcopy /E /I include C:\Dev\libs\fmt-install\include
xcopy /E /I Release\*.lib C:\Dev\libs\fmt-install\lib
```

### 4. Setup Variabili Ambiente
```batch
# 1. Apri Variabili di Sistema
# Start > Cerca "Variabili di ambiente" > "Modifica variabili di ambiente di sistema"

# 2. Aggiungi Nuove Variabili
setx CHECKMK_DEV C:\Dev\checkmk
setx YAML_CPP_ROOT C:\Dev\libs\yaml-cpp-install
setx FMT_ROOT C:\Dev\libs\fmt-install

# 3. Aggiorna Path
# Aggiungi alla variabile Path:
# - C:\Dev\libs\yaml-cpp-install\bin
# - C:\Dev\libs\fmt-install\bin
```

## Compilazione

### 1. Clone Repository CheckMK
```batch
# 1. Clone repository
cd C:\Dev
git clone https://github.com/Checkmk/checkmk.git
cd checkmk

# 2. Crea directory build
mkdir build
cd build
```

### 2. Configurazione Build
```batch
# 1. Configura CMake
cmake -G "Visual Studio 16 2019" -A x64 ^
    -DCMAKE_BUILD_TYPE=Release ^
    -DBUILD_TESTING=ON ^
    -DYAML_CPP_ROOT=%YAML_CPP_ROOT% ^
    -DFMT_ROOT=%FMT_ROOT% ^
    ..

# 2. Verifica configurazione
type CMakeCache.txt | findstr "YAML_CPP"
type CMakeCache.txt | findstr "FMT"
```

### 3. Compilazione Progetto
```batch
# 1. Compila tutto
cmake --build . --config Release

# 2. Compila solo l'agente
cmake --build . --config Release --target check_mk_agent

# 3. Compila i test
cmake --build . --config Release --target check_mk_tests
```

## Verifica

### 1. Verifica File Compilati
```batch
# 1. Controlla file agente
dir Release\check_mk_agent.exe

# 2. Controlla file test
dir Release\check_mk_tests.exe

# 3. Verifica dimensioni
dir Release\*.exe /s
```

### 2. Test Base
```batch
# 1. Esegui test unitari
cd Release
check_mk_tests.exe --gtest_filter="FileMonitorTest.*"

# 2. Verifica output test
type Testing\Temporary\LastTest.log
```

### 3. Verifica Provider
```batch
# 1. Test provider
check_mk_agent.exe -d -s file_monitor

# 2. Verifica output
# Dovrebbe mostrare la sezione file_monitor
```

## Troubleshooting Compilazione

### 1. Errori Comuni

#### CMake non trova yaml-cpp
```plaintext
Errore: Could not find yaml-cpp

Soluzione:
1. Verifica YAML_CPP_ROOT
   echo %YAML_CPP_ROOT%
   
2. Verifica file
   dir %YAML_CPP_ROOT%\lib\*.lib
   
3. Riprova configurazione
   cmake .. -DYAML_CPP_ROOT=%YAML_CPP_ROOT%
```

#### Errori di Linking
```plaintext
Errore: LNK2019: unresolved external symbol

Soluzione:
1. Verifica librerie
   dir %YAML_CPP_ROOT%\lib
   dir %FMT_ROOT%\lib
   
2. Pulisci e ricompila
   rmdir /s /q CMakeFiles
   cmake ..
   cmake --build . --config Release
```

#### Errori di Compilazione
```plaintext
Errore: C2065: undeclared identifier

Soluzione:
1. Verifica include
   dir %YAML_CPP_ROOT%\include
   dir %FMT_ROOT%\include
   
2. Aggiorna CMake
   cmake .. -DCMAKE_PREFIX_PATH="C:\Dev\libs"
```

### 2. Verifica Ambiente

#### Test Sistema
```batch
# 1. Visual Studio
cl.exe /?

# 2. CMake
cmake --version

# 3. Python
python --version

# 4. Git
git --version
```

#### Test Librerie
```batch
# 1. yaml-cpp
dir %YAML_CPP_ROOT%\lib\*.lib

# 2. fmt
dir %FMT_ROOT%\lib\*.lib
```

### 3. Clean Build
```batch
# 1. Pulisci directory build
cd %CHECKMK_DEV%\build
rmdir /s /q *

# 2. Riconfigura
cmake -G "Visual Studio 16 2019" -A x64 ..

# 3. Ricompila
cmake --build . --config Release
```

## Note Aggiuntive

### 1. Performance Build
```batch
# 1. Compilazione parallela
cmake --build . --config Release -j 8

# 2. Ottimizzazioni
cmake -DCMAKE_CXX_FLAGS="/O2" ..
```

### 2. Debug Build
```batch
# 1. Build debug
cmake --build . --config Debug

# 2. Test debug
devenv check_mk_agent.exe /debugexe
```

### 3. Best Practices
```plaintext
1. Mantieni ambiente aggiornato
2. Usa build incrementali
3. Verifica test dopo modifiche
4. Documenta problemi/soluzioni
