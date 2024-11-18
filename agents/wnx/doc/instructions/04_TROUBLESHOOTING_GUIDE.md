# Guida al Troubleshooting del File Monitor Provider

## Indice
1. [Diagnostica](#diagnostica)
2. [Problemi Comuni](#problemi-comuni)
3. [Debug Avanzato](#debug-avanzato)
4. [Recovery](#recovery)

## Diagnostica

### 1. Strumenti di Diagnostica
```batch
# 1. Check Status Provider
check_mk_agent.exe -d -s file_monitor

# 2. Verifica Log
type "C:\ProgramData\checkmk\logs\file_monitor.log"

# 3. Event Viewer
eventvwr.msc
# -> Windows Logs -> Application
# -> Source: CheckMK_FileMonitor

# Perché questi strumenti:
# - Verifica immediata stato
# - Log dettagliati
# - Eventi sistema
```

### 2. Log Collection
```batch
# Script di raccolta log
@echo off
set LOG_DIR=C:\Temp\checkmk_debug
mkdir %LOG_DIR%

# 1. File Monitor Logs
copy "C:\ProgramData\checkmk\logs\file_monitor*.log" %LOG_DIR%

# 2. Configurazione
copy "C:\ProgramData\checkmk\config\*.yml" %LOG_DIR%

# 3. System Info
systeminfo > %LOG_DIR%\sysinfo.txt
wmic process list > %LOG_DIR%\processes.txt
wmic service where "name like 'CheckMK%%'" list full > %LOG_DIR%\service.txt

# Perché questi dati:
# - Contesto completo
# - Stato sistema
# - Configurazione attuale
```

### 3. Verifica Stato
```powershell
# PowerShell script di diagnostica
$status = @{
    "Service" = Get-Service "CheckMKService"
    "Process" = Get-Process "check_mk_agent" -ErrorAction SilentlyContinue
    "Config" = Test-Path "C:\ProgramData\checkmk\config\check_mk.yml"
    "Logs" = Get-ChildItem "C:\ProgramData\checkmk\logs\file_monitor*.log"
}

# Output formattato
$status | ConvertTo-Json

# Perché questo check:
# - Stato servizio
# - Processo attivo
# - File necessari
```

## Problemi Comuni

### 1. Provider Non Carica
```yaml
# Sintomo: Provider non appare nell'output dell'agente

# 1. Verifica Configurazione
file_monitor:
  enabled: true  # Deve essere true
  
global:
  sections:
    - file_monitor  # Deve essere presente

# 2. Verifica Log
# Cerca in file_monitor.log:
ERRO: Failed to load configuration
WARN: Provider disabled

# 3. Soluzioni
- Verifica sintassi YAML
- Controlla permessi file
- Riavvia servizio

# Perché questi check:
# - Configurazione corretta
# - Permessi appropriati
# - Stato servizio
```

### 2. File Non Rilevati
```yaml
# Sintomo: File non vengono trovati/monitorati

# 1. Verifica Pattern
paths:
  - path: "C:\\temp\\*.txt"  # Usa doppio backslash
    delete: true

# 2. Debug Pattern
check_mk_agent.exe -d -s file_monitor > pattern_debug.log
# Cerca:
DEBUG: Scanning path: ...
DEBUG: Pattern match: ...

# 3. Test Manuale
dir "C:\temp\*.txt" /s /b > files.txt
# Confronta con output provider

# Perché questa procedura:
# - Verifica pattern
# - Test diretto
# - Confronto risultati
```

### 3. Errori di Eliminazione
```yaml
# Sintomo: File non vengono eliminati

# 1. Verifica Permessi
icacls "C:\temp\test.txt"
# Deve mostrare:
# NT AUTHORITY\SYSTEM:(F)

# 2. Check Process
handle.exe -a -p check_mk_agent.exe
# Verifica handle aperti

# 3. Test Manuale
del "C:\temp\test.txt" /f
# Verifica errori

# Perché questi test:
# - Permessi file
# - Lock file
# - Accesso diretto
```

## Debug Avanzato

### 1. Debug Logging
```yaml
# Configurazione debug dettagliato
logging:
  file_monitor:
    level: debug
    format: "{timestamp} [{level}] {file}:{line} - {message}"
    output:
      - file: "C:\\ProgramData\\checkmk\\logs\\file_monitor_debug.log"
        max_size: "100MB"
        rotate: 5
      - console: true
        color: true

# Debug specifici
debug:
  pattern_matching: true
  file_operations: true
  notifications: true
  performance: true

# Perché questo livello:
# - Informazioni complete
# - Tracciamento operazioni
# - Performance metrics
```

### 2. Performance Analysis
```powershell
# PowerShell script analisi performance
$log = Get-Content "file_monitor_debug.log"

# 1. Tempi operazioni
$operations = $log | Select-String "Operation took (\d+) ms"
$operations | Measure-Object {$_.Matches[0].Groups[1].Value} -Average -Maximum -Minimum

# 2. Pattern matching
$patterns = $log | Select-String "Pattern match took (\d+) ms"
$patterns | Measure-Object {$_.Matches[0].Groups[1].Value} -Average -Maximum -Minimum

# 3. File operations
$fileOps = $log | Select-String "File operation took (\d+) ms"
$fileOps | Measure-Object {$_.Matches[0].Groups[1].Value} -Average -Maximum -Minimum

# Perché questa analisi:
# - Bottleneck identification
# - Performance trends
# - Resource usage
```

### 3. Memory Analysis
```batch
# 1. Process Explorer
proexp.exe
# - Monitora handle
# - Memory usage
# - Thread activity

# 2. Performance Monitor
perfmon.exe
# Counter da monitorare:
# - Process\Private Bytes
# - Process\Handle Count
# - Process\Thread Count

# 3. Debug Viewer
dbgview.exe
# - Real-time debug output
# - System messages
# - Application logs

# Perché questi tool:
# - Memory leaks
# - Handle leaks
# - Performance issues
```

## Recovery

### 1. Reset Provider
```batch
# 1. Stop Service
net stop CheckMKService

# 2. Clean State
del "C:\ProgramData\checkmk\logs\file_monitor*.log"
del "C:\ProgramData\checkmk\cache\file_monitor*"

# 3. Reset Config
copy "check_mk_dev_file_monitor.yml" ^
     "C:\ProgramData\checkmk\config\check_mk.yml"

# 4. Start Service
net start CheckMKService

# Perché questa procedura:
# - Stato pulito
# - Configurazione default
# - Restart pulito
```

### 2. Emergency Recovery
```batch
# 1. Backup Current State
mkdir C:\Temp\checkmk_backup
xcopy "C:\ProgramData\checkmk\*.*" ^
      "C:\Temp\checkmk_backup\" /s /e

# 2. Stop All
net stop CheckMKService
taskkill /f /im check_mk_agent.exe

# 3. Clean Install
# - Rimuovi agent
# - Installa versione pulita
# - Ripristina config base

# Perché questi step:
# - Backup sicuro
# - Stop completo
# - Install pulita
```

### 3. Data Recovery
```powershell
# PowerShell script recovery
# 1. Find deleted files
$deletedFiles = Get-Content "file_monitor.log" |
    Select-String "Deleted file: (.+)" |
    ForEach-Object { $_.Matches[0].Groups[1].Value }

# 2. Check backup
foreach ($file in $deletedFiles) {
    $backup = "$file.bak"
    if (Test-Path $backup) {
        Copy-Item $backup $file
        Write-Host "Restored: $file"
    }
}

# 3. Verify
Get-Content "file_monitor.log" -Tail 100

# Perché questo recovery:
# - Traccia file eliminati
# - Restore da backup
# - Verifica risultato
```

## Best Practices

### 1. Monitoring Setup
```yaml
# Configurazione monitoraggio ottimale
file_monitor:
  # 1. Performance
  performance:
    batch_size: 100
    max_files_per_scan: 1000
    worker_threads: 2

  # 2. Error Handling
  error_handling:
    retry_count: 3
    retry_delay: 5
    ignore_errors: false

  # 3. Logging
  logging:
    level: info
    performance_metrics: true
    operation_tracking: true

# Perché queste impostazioni:
# - Performance bilanciata
# - Error recovery robusto
# - Logging appropriato
```

### 2. Maintenance
```batch
# 1. Log Rotation
forfiles /p "C:\ProgramData\checkmk\logs" ^
        /m file_monitor*.log ^
        /d -30 ^
        /c "cmd /c del @path"

# 2. Cache Cleanup
forfiles /p "C:\ProgramData\checkmk\cache" ^
        /m file_monitor* ^
        /d -7 ^
        /c "cmd /c del @path"

# 3. Config Backup
robocopy "C:\ProgramData\checkmk\config" ^
         "D:\Backup\checkmk\config" ^
         /MIR /R:3 /W:5

# Perché questa manutenzione:
# - Gestione spazio
# - Performance
# - Backup sicuro
```

### 3. Monitoring
```powershell
# PowerShell monitoring script
# 1. Check Health
$health = @{
    "Service" = (Get-Service "CheckMKService").Status
    "Memory" = (Get-Process "check_mk_agent").WorkingSet64
    "CPU" = (Get-Process "check_mk_agent").CPU
    "Handles" = (Get-Process "check_mk_agent").HandleCount
    "Threads" = (Get-Process "check_mk_agent").Threads.Count
}

# 2. Check Logs
$errors = Get-Content "file_monitor.log" |
    Select-String "ERROR|WARN" |
    Select-Object -Last 10

# 3. Performance
$perf = Get-Counter "\Process(check_mk_agent)\*" |
    Select-Object -ExpandProperty CounterSamples

# Output
$result = @{
    "Health" = $health
    "Errors" = $errors
    "Performance" = $perf
}
$result | ConvertTo-Json | Out-File "monitor_report.json"

# Perché questo monitoring:
# - Health check completo
# - Error tracking
# - Performance metrics
