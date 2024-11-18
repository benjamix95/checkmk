# Guida alla Configurazione VM e Testing

## Indice
1. [Setup VMware Workstation](#setup-vmware-workstation)
2. [Creazione VM Windows](#creazione-vm-windows)
3. [Configurazione Ambiente](#configurazione-ambiente)
4. [Test FileMonitor](#test-filemonitor)

## Setup VMware Workstation

### 1. Installazione VMware
```plaintext
1. Download VMware Workstation Pro
   - Vai a: https://www.vmware.com/products/workstation-pro/workstation-pro-evaluation.html
   - Scarica la versione più recente

2. Installazione
   - Esegui installer come amministratore
   - Accetta licenza
   - Installazione tipica
   - Riavvia il computer dopo l'installazione

3. Attivazione
   - Avvia VMware Workstation
   - Inserisci la licenza
   - Completa attivazione
```

### 2. Configurazione VMware
```plaintext
1. Impostazioni Globali
   - Edit > Preferences
   - Memory: Alloca almeno 8GB per VM
   - Processors: Almeno 2 core per VM
   - Default VM location: C:\VMs

2. Configurazione Rete
   - Edit > Virtual Network Editor
   - Configura NAT network
   - Assegna range IP
   - Abilita DHCP
```

## Creazione VM Windows

### 1. Creazione Nuova VM
```plaintext
1. File > New Virtual Machine
   - Seleziona "Custom (advanced)"
   - Next

2. Hardware Compatibility
   - Seleziona versione più recente
   - Next

3. Install OS
   - "I will install the OS later"
   - Next

4. Guest OS
   - Microsoft Windows
   - Windows 10 x64
   - Next

5. Name and Location
   - Name: CheckMK-Dev
   - Location: C:\VMs\CheckMK-Dev
   - Next
```

### 2. Configurazione Hardware
```plaintext
1. Processors
   - Number of processors: 2
   - Number of cores: 2
   - Next

2. Memory
   - 8192 MB (8GB)
   - Next

3. Network
   - Use NAT
   - Next

4. Hard Disk
   - Create new virtual disk
   - 100 GB
   - Store as single file
   - Next

5. Customize Hardware
   - Add USB Controller
   - Add Sound Card
   - Add Printer port
```

### 3. Installazione Windows
```plaintext
1. Preparazione
   - Scarica ISO Windows 10
   - Mount ISO nella VM
   - Start VM

2. Installazione Windows
   - Boot da ISO
   - Seleziona "Custom Install"
   - Formatta disco virtuale
   - Installa Windows

3. Post-Installazione
   - Installa VMware Tools
   - Configura Windows Updates
   - Attiva Windows
```

## Configurazione Ambiente

### 1. Setup Base
```batch
# 1. Crea struttura directory
mkdir C:\Dev
mkdir C:\Dev\libs
mkdir C:\Dev\checkmk

# 2. Installa software base
# PowerShell come amministratore
Set-ExecutionPolicy Bypass -Scope Process -Force
iex ((New-Object System.Net.WebClient).DownloadString('https://chocolatey.org/install.ps1'))

# Installa software necessario
choco install -y git visualstudio2019community python cmake
```

### 2. Configurazione Visual Studio
```plaintext
1. Avvia Visual Studio Installer
   - Modifica installazione
   - Aggiungi componenti:
     * Sviluppo C++
     * CMake
     * Windows SDK

2. Riavvia VS
   - Chiudi Visual Studio
   - Riavvia applicazione
```

### 3. Clone e Build
```batch
# 1. Clone repository
cd C:\Dev
git clone https://github.com/Checkmk/checkmk.git

# 2. Setup dipendenze
# Segui la guida di compilazione precedente per:
# - yaml-cpp
# - fmt

# 3. Build CheckMK
cd checkmk
mkdir build
cd build
cmake -G "Visual Studio 16 2019" -A x64 ..
cmake --build . --config Release
```

## Test FileMonitor

### 1. Setup Test Environment
```batch
# 1. Crea directory test
mkdir C:\TestFiles
cd C:\TestFiles

# 2. Crea file test
echo Test1 > test1.txt
echo Test2 > test2.txt
copy test1.txt C:\TestFiles\Subfolder\
copy test2.txt C:\TestFiles\Subfolder\

# 3. Crea configurazione
mkdir C:\ProgramData\checkmk\config
```

### 2. Configurazione Test
```yaml
# File: C:\ProgramData\checkmk\config\check_mk.yml
file_monitor:
  enabled: true
  timeout: 60
  retry: 3
  
  paths:
    - path: "C:\\TestFiles\\*.txt"
      delete: true
      
    - path: "C:\\TestFiles\\Subfolder\\*.txt"
      delete: false

  settings:
    check_interval: 30
    max_file_size: 1048576
```

### 3. Test Funzionale
```batch
# 1. Test manuale
cd C:\Program Files\CheckMK\Agent
check_mk_agent.exe -d -s file_monitor

# 2. Verifica output
# Dovrebbe mostrare:
# <<<file_monitor>>>
# C:\TestFiles\test1.txt|found|will_delete
# C:\TestFiles\test2.txt|found|will_delete
# C:\TestFiles\Subfolder\test1.txt|found|keep
# C:\TestFiles\Subfolder\test2.txt|found|keep

# 3. Verifica eliminazione
dir C:\TestFiles\*.txt
dir C:\TestFiles\Subfolder\*.txt
```

### 4. Test Automatizzati
```batch
# 1. Esegui test suite
cd C:\Dev\checkmk\build\Release
check_mk_tests.exe --gtest_filter="FileMonitorTest.*"

# 2. Verifica risultati
type Testing\Temporary\LastTest.log
```

### 5. Test Performance
```batch
# 1. Crea molti file
for /L %i in (1,1,1000) do echo Test > test%i.txt

# 2. Monitor CPU/Memory
perfmon.exe
# Aggiungi contatori:
# - Process\% Processor Time
# - Process\Private Bytes
# - Process\Handle Count

# 3. Esegui test carico
check_mk_agent.exe -d -s file_monitor
```

## Verifica Integrazione

### 1. Setup CheckMK Server
```plaintext
1. Installa CheckMK Server
   - Scarica RAW edition
   - Installa in altra VM
   - Configura site

2. Configura Agent
   - Registra agent con server
   - Verifica connessione
   - Controlla output
```

### 2. Monitor Output
```plaintext
1. CheckMK Web UI
   - Accedi interface
   - Vai a Host > Services
   - Verifica sezione File Monitor

2. Verifica Notifiche
   - Controlla Event Console
   - Verifica notifiche email
   - Controlla log server
```

### 3. Test Scenari
```plaintext
1. File Creation
   - Crea nuovi file
   - Verifica rilevamento
   - Controlla eliminazione

2. Pattern Matching
   - Test diversi pattern
   - Verifica esclusioni
   - Test ricorsione

3. Error Handling
   - File locked
   - Permission denied
   - Network issues
```

## Troubleshooting

### 1. VM Issues
```plaintext
1. Performance
   - Aumenta RAM VM
   - Aggiungi CPU cores
   - Ottimizza disk

2. Network
   - Verifica NAT
   - Check firewall
   - Test connectivity
```

### 2. Test Issues
```plaintext
1. File Access
   - Check permissions
   - Verify paths
   - Test file locks

2. Agent Issues
   - Verify service
   - Check logs
   - Test connectivity
```

### 3. Integration Issues
```plaintext
1. Server Connection
   - Check firewall
   - Verify agent config
   - Test network

2. Data Flow
   - Monitor agent output
   - Check server logs
   - Verify processing
