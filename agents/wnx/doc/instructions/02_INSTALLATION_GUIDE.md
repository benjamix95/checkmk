# Guida all'Installazione del File Monitor Provider

## Indice
1. [Prerequisiti](#prerequisiti)
2. [Installazione](#installazione)
3. [Configurazione](#configurazione)
4. [Verifica](#verifica)
5. [Troubleshooting](#troubleshooting)

## Prerequisiti

### 1. Ambiente CheckMK
```plaintext
1. CheckMK Server
   - Versione: 2.0.0 o superiore
   - Accesso amministrativo
   - Site configurato

2. Windows Agent
   - Versione: 1.7.0 o superiore
   - Permessi amministrativi
   - Servizio installato

3. Permessi Windows
   - Amministratore locale
   - Accesso file system
   - Gestione servizi
```

### 2. File Necessari
```plaintext
1. Agente compilato
   - check_mk_agent.exe
   - Librerie dipendenti

2. File configurazione
   - check_mk.yml
   - file_monitor.yml

3. Documentazione
   - README.md
   - Esempi configurazione
```

## Installazione

### 1. Backup Sistema Esistente
```batch
# 1. Backup agente esistente
cd "C:\Program Files\CheckMK\Agent"
ren check_mk_agent.exe check_mk_agent.exe.bak

# 2. Backup configurazione
cd "C:\ProgramData\checkmk\config"
copy check_mk.yml check_mk.yml.bak

# 3. Stop servizio
net stop CheckMKService

# Perché questi step:
# - Sicurezza in caso di problemi
# - Possibilità di rollback
# - Evitare conflitti servizio
```

### 2. Installazione File
```batch
# 1. Copiare agente
copy "%CHECKMK_BUILD%\Release\check_mk_agent.exe" ^
     "C:\Program Files\CheckMK\Agent\"

# 2. Copiare configurazione
copy "check_mk_dev_file_monitor.yml" ^
     "C:\ProgramData\checkmk\config\check_mk.yml"

# 3. Creare directory log
mkdir "C:\ProgramData\checkmk\logs"

# Perché questi path:
# - Path standard CheckMK
# - Separazione config/logs
# - Permessi corretti
```

### 3. Configurazione Permessi
```batch
# 1. Permessi directory agent
icacls "C:\Program Files\CheckMK\Agent" /grant:r "NT AUTHORITY\SYSTEM:(OI)(CI)F"
icacls "C:\Program Files\CheckMK\Agent" /grant:r "Administrators:(OI)(CI)F"

# 2. Permessi configurazione
icacls "C:\ProgramData\checkmk\config" /grant:r "NT AUTHORITY\SYSTEM:(OI)(CI)F"

# 3. Permessi logs
icacls "C:\ProgramData\checkmk\logs" /grant:r "NT AUTHORITY\SYSTEM:(OI)(CI)F"

# Perché questi permessi:
# - Sicurezza sistema
# - Accesso servizio
# - Gestione logs
```

## Configurazione

### 1. Configurazione Base
```yaml
# File: C:\ProgramData\checkmk\config\check_mk.yml
global:
  enabled: true
  sections:
    - file_monitor  # Abilitare il provider

file_monitor:
  enabled: true
  timeout: 60
  retry: 3
  
  # Directory da monitorare
  paths:
    - path: "C:\\temp\\*.txt"
      delete: true
    - path: "C:\\logs\\*.log"
      delete: false

  # Impostazioni
  settings:
    max_file_size: 104857600  # 100MB
    check_interval: 300       # 5 minuti

# Perché questa configurazione:
# - Abilitazione esplicita
# - Timeout ragionevole
# - Pattern comuni
# - Limiti sicuri
```

### 2. Configurazione Avanzata
```yaml
file_monitor:
  # Configurazione notifiche
  notifications:
    event_log: true
    checkmk: true
    levels:
      found: info
      deleted: warning
      error: critical

  # Configurazione performance
  performance:
    buffer_size: 8192
    max_files_per_check: 1000
    worker_threads: 2

  # Pattern avanzati
  paths:
    - path: "C:\\Users\\**\\Downloads\\*.exe"
      delete: true
      recursive: true
      max_depth: 3
      
    - path: "C:\\Program Files\\*.tmp"
      delete: true
      older_than: 7d
      size_above: 10MB

# Perché queste opzioni:
# - Controllo granulare
# - Performance ottimizzata
# - Sicurezza sistema
```

### 3. Configurazione Logging
```yaml
logging:
  # Log provider
  file_monitor:
    level: debug
    file: "C:\\ProgramData\\checkmk\\logs\\file_monitor.log"
    max_size: 10MB
    rotate: 5

  # Log sistema
  system:
    event_log: true
    facility: application
    source: CheckMK_FileMonitor

# Perché questa configurazione:
# - Debug dettagliato
# - Rotazione log
# - Integrazione sistema
```

## Verifica

### 1. Verifica Installazione
```batch
# 1. Verifica file
dir "C:\Program Files\CheckMK\Agent\check_mk_agent.exe"
dir "C:\ProgramData\checkmk\config\check_mk.yml"

# 2. Verifica permessi
icacls "C:\Program Files\CheckMK\Agent\check_mk_agent.exe"
icacls "C:\ProgramData\checkmk\config\check_mk.yml"

# 3. Verifica servizio
sc query CheckMKService
```

### 2. Test Funzionalità
```batch
# 1. Creare file test
echo test > C:\temp\test.txt
echo log > C:\logs\test.log

# 2. Eseguire check
"C:\Program Files\CheckMK\Agent\check_mk_agent.exe" -s file_monitor

# 3. Verificare log
type "C:\ProgramData\checkmk\logs\file_monitor.log"
```

### 3. Verifica Monitoraggio
```batch
# 1. Start servizio
net start CheckMKService

# 2. Verifica output
"C:\Program Files\CheckMK\Agent\check_mk_agent.exe"

# 3. Verifica CheckMK
# - Accedere alla GUI CheckMK
# - Verificare sezione file_monitor
# - Controllare notifiche
```

## Troubleshooting

### 1. Problemi Comuni

#### Servizio non parte
```plaintext
Problema: Il servizio non si avvia

Soluzioni:
1. Verificare log eventi
   eventvwr.msc -> Windows Logs -> Application

2. Verificare permessi
   icacls "C:\Program Files\CheckMK\Agent"

3. Verificare configurazione
   check_mk.yml syntax
```

#### File non monitorati
```plaintext
Problema: File non vengono rilevati

Soluzioni:
1. Verificare pattern
   - Sintassi corretta
   - Path esistenti
   - Permessi accesso

2. Verificare log
   - Livello debug
   - Error messages
   - Access denied

3. Test manuale
   check_mk_agent.exe -s file_monitor
```

#### Errori Eliminazione
```plaintext
Problema: File non vengono eliminati

Soluzioni:
1. Verificare permessi
   - Account servizio
   - ACL file
   - ACL directory

2. Verificare file
   - File in uso
   - File system readonly
   - Attributi file

3. Test manuale
   - Stop servizio
   - Test delete
   - Verifica permessi
```

### 2. Procedure Recovery

#### Reset Configurazione
```batch
# 1. Backup attuale
copy "C:\ProgramData\checkmk\config\check_mk.yml" ^
     "C:\ProgramData\checkmk\config\check_mk.yml.bak"

# 2. Ripristino default
copy "check_mk_dev_file_monitor.yml" ^
     "C:\ProgramData\checkmk\config\check_mk.yml"

# 3. Restart servizio
net stop CheckMKService
net start CheckMKService
```

#### Clean Start
```batch
# 1. Stop servizio
net stop CheckMKService

# 2. Clean logs
del "C:\ProgramData\checkmk\logs\*.*" /q

# 3. Reset config
copy "check_mk.yml.bak" "check_mk.yml"

# 4. Start servizio
net start CheckMKService
```

#### Rollback
```batch
# 1. Stop servizio
net stop CheckMKService

# 2. Restore agent
cd "C:\Program Files\CheckMK\Agent"
ren check_mk_agent.exe check_mk_agent.exe.new
ren check_mk_agent.exe.bak check_mk_agent.exe

# 3. Restore config
cd "C:\ProgramData\checkmk\config"
copy check_mk.yml.bak check_mk.yml

# 4. Start servizio
net start CheckMKService
```

### 3. Diagnostica

#### Log Collection
```batch
# 1. Collect logs
mkdir C:\Temp\checkmk_logs
copy "C:\ProgramData\checkmk\logs\*.*" C:\Temp\checkmk_logs

# 2. Collect config
copy "C:\ProgramData\checkmk\config\*.*" C:\Temp\checkmk_logs

# 3. Collect system info
systeminfo > C:\Temp\checkmk_logs\sysinfo.txt
```

#### Test Provider
```batch
# 1. Test diretto
check_mk_agent.exe -d -s file_monitor > test.log

# 2. Verifica output
type test.log

# 3. Analisi problemi
findstr "ERROR WARN" test.log
```

#### Debug Mode
```batch
# 1. Enable debug
notepad "C:\ProgramData\checkmk\config\check_mk.yml"
# Set debug: true

# 2. Increase log level
# Set level: debug

# 3. Restart service
net stop CheckMKService
net start CheckMKService
```

## Note Aggiuntive

### 1. Sicurezza
```plaintext
1. Permessi minimi necessari
   - Lettura configurazione
   - Scrittura logs
   - Accesso file monitorati

2. Account servizio dedicato
   - Permessi limitati
   - Audit enabled
   - Password policy

3. File system security
   - ACL appropriate
   - Monitoring paths
   - Delete permissions
```

### 2. Performance
```plaintext
1. Ottimizzazione scan
   - Pattern specifici
   - Profondità limitata
   - Esclusioni appropriate

2. Resource usage
   - Buffer size
   - Thread count
   - Memory limits

3. Logging
   - Rotation policy
   - Disk space
   - Cleanup policy
```

### 3. Manutenzione
```plaintext
1. Backup regolare
   - Configurazione
   - Logs
   - State files

2. Monitoring
   - Performance
   - Errors
   - Disk space

3. Updates
   - Test updates
   - Backup prima
   - Verifica dopo
