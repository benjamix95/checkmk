# Esempi di Utilizzo del File Monitor Provider

## Indice
1. [Casi d'Uso Base](#casi-duso-base)
2. [Scenari Avanzati](#scenari-avanzati)
3. [Best Practices](#best-practices)
4. [Esempi Completi](#esempi-completi)

## Casi d'Uso Base

### 1. Monitoraggio File di Log
```yaml
# Caso d'uso: Monitorare file di log senza eliminarli
file_monitor:
  enabled: true
  paths:
    - path: "C:\\logs\\*.log"
      delete: false
      recursive: false

  settings:
    check_interval: 300  # 5 minuti
    max_file_size: 104857600  # 100MB

# Perché questo esempio:
# - Pattern comune per log
# - No eliminazione per sicurezza
# - Controllo dimensione
```

### 2. Pulizia File Temporanei
```yaml
# Caso d'uso: Eliminare file temporanei vecchi
file_monitor:
  paths:
    - path: "C:\\Windows\\Temp\\*.tmp"
      delete: true
      older_than: "7d"
      
    - path: "C:\\Users\\*\\AppData\\Local\\Temp\\*.tmp"
      delete: true
      older_than: "3d"

# Perché questo esempio:
# - Manutenzione sistema
# - Pattern specifici
# - Retention policy
```

### 3. Monitoraggio Download
```yaml
# Caso d'uso: Monitorare cartella download
file_monitor:
  paths:
    - path: "C:\\Users\\*\\Downloads\\*.exe"
      delete: true
      notify: true
      
    - path: "C:\\Users\\*\\Downloads\\*.zip"
      delete: false
      notify: true

# Perché questo esempio:
# - Sicurezza sistema
# - Notifiche immediate
# - Selezione file specifici
```

## Scenari Avanzati

### 1. Monitoraggio Multi-Pattern
```yaml
# Caso d'uso: Monitoraggio complesso con pattern multipli
file_monitor:
  paths:
    # Log applicazioni
    - path: "C:\\Program Files\\App\\logs\\*.log"
      pattern: "ERROR|FATAL"
      delete: false
      notify_on_match: true
      
    # File temporanei
    - path: "C:\\Work\\temp\\**\\*.tmp"
      delete: true
      recursive: true
      exclude: ["backup", "archive"]
      
    # File di backup
    - path: "D:\\Backup\\*.bak"
      older_than: "30d"
      size_above: "1GB"
      delete: true

# Perché questa configurazione:
# - Pattern multipli
# - Esclusioni
# - Criteri complessi
```

### 2. Monitoraggio con Azioni
```yaml
# Caso d'uso: Azioni personalizzate su file
file_monitor:
  paths:
    # Report giornalieri
    - path: "C:\\Reports\\daily\\*.pdf"
      action: "archive"
      destination: "D:\\Archive\\{year}\\{month}"
      delete_after: true
      
    # Log processing
    - path: "C:\\Logs\\*.log"
      action: "compress"
      older_than: "7d"
      destination: "C:\\Logs\\archived"
      
    # File di configurazione
    - path: "C:\\Config\\*.cfg"
      action: "backup"
      on_change: true
      keep_versions: 5

# Perché queste azioni:
# - Archivio automatico
# - Compressione logs
# - Backup configurazioni
```

### 3. Monitoraggio Sicurezza
```yaml
# Caso d'uso: Monitoraggio per sicurezza
file_monitor:
  paths:
    # File eseguibili
    - path: "C:\\Program Files\\**\\*.exe"
      action: "verify_signature"
      notify_on_fail: true
      
    # File di sistema
    - path: "C:\\Windows\\System32\\*.dll"
      action: "check_hash"
      baseline: "hashes.txt"
      
    # Script potenzialmente pericolosi
    - path: "C:\\Users\\**\\*.ps1"
      action: "scan"
      notify: true

# Perché questi controlli:
# - Verifica integrità
# - Controllo malware
# - Notifiche sicurezza
```

## Best Practices

### 1. Pattern Ottimali
```yaml
# Esempio: Pattern efficienti
file_monitor:
  paths:
    # ✅ Buono: Pattern specifico
    - path: "C:\\Logs\\app-*.log"
    
    # ❌ Evitare: Pattern troppo generico
    - path: "C:\\**\\*.*"
    
    # ✅ Buono: Profondità limitata
    - path: "C:\\Data\\**\\*.dat"
      max_depth: 3
    
    # ✅ Buono: Esclusioni specifiche
    - path: "C:\\Work\\*.tmp"
      exclude: ["backup", "temp"]

# Perché questi pattern:
# - Performance migliore
# - Meno falsi positivi
# - Gestione risorse
```

### 2. Configurazione Notifiche
```yaml
# Esempio: Notifiche ottimizzate
file_monitor:
  notifications:
    # Livelli appropriati
    levels:
      file_found: info
      file_deleted: warning
      error: critical
    
    # Aggregazione
    aggregate:
      similar: true
      interval: 300
      max_items: 10
    
    # Filtri
    filters:
      - type: "size"
        min: "1MB"
      - type: "pattern"
        match: "*.log"

# Perché questa configurazione:
# - Riduce rumore
# - Prioritizza eventi
# - Ottimizza performance
```

### 3. Gestione Risorse
```yaml
# Esempio: Configurazione risorse
file_monitor:
  performance:
    # Memory limits
    max_memory: "256MB"
    buffer_size: "8KB"
    
    # Thread control
    workers: 2
    queue_size: 1000
    
    # I/O settings
    read_buffer: "64KB"
    batch_size: 100

# Perché questi limiti:
# - Previene sovraccarico
# - Ottimizza I/O
# - Bilancia risorse
```

## Esempi Completi

### 1. Server Web
```yaml
# Caso d'uso: Monitoraggio server web
file_monitor:
  paths:
    # Access logs
    - path: "C:\\inetpub\\logs\\*.log"
      delete: false
      pattern: "ERROR|WARN|500|404"
      notify_on_match: true
    
    # Temp files
    - path: "C:\\inetpub\\temp\\*.*"
      delete: true
      older_than: "1d"
    
    # Config backup
    - path: "C:\\inetpub\\wwwroot\\web.config"
      action: "backup"
      on_change: true
      keep_versions: 5

  notifications:
    email: "admin@example.com"
    teams_webhook: "https://..."
    
  performance:
    check_interval: 300
    workers: 2

# Perché questa configurazione:
# - Monitoraggio errori
# - Pulizia automatica
# - Backup configurazione
```

### 2. Development Environment
```yaml
# Caso d'uso: Ambiente sviluppo
file_monitor:
  paths:
    # Build artifacts
    - path: "C:\\Dev\\**\\bin\\*.*"
      delete: true
      older_than: "7d"
      exclude: ["release"]
    
    # VS temporary files
    - path: "C:\\Dev\\**\\.vs"
      delete: true
      recursive: true
    
    # Source backups
    - path: "C:\\Dev\\**\\*.cs"
      action: "backup"
      on_change: true
      destination: "D:\\Backups\\{year}\\{month}"

  settings:
    max_file_size: "500MB"
    check_interval: 3600

# Perché questa configurazione:
# - Pulizia build
# - Backup codice
# - Performance sviluppo
```

### 3. Log Management
```yaml
# Caso d'uso: Gestione log enterprise
file_monitor:
  paths:
    # Application logs
    - path: "D:\\Logs\\App\\**\\*.log"
      action: "rotate"
      max_size: "100MB"
      keep: 10
      compress: true
    
    # System logs
    - path: "D:\\Logs\\System\\*.evt"
      action: "archive"
      older_than: "30d"
      destination: "D:\\Archive\\{year}"
    
    # Audit logs
    - path: "D:\\Logs\\Audit\\*.aud"
      delete: false
      notify_on_access: true
      backup: true

  performance:
    workers: 4
    batch_size: 1000
    
  retention:
    default: "90d"
    audit: "365d"
    system: "180d"

# Perché questa configurazione:
# - Compliance
# - Automazione
# - Scalabilità
```

### 4. Security Monitoring
```yaml
# Caso d'uso: Monitoraggio sicurezza
file_monitor:
  paths:
    # Executable monitoring
    - path: "C:\\Program Files\\**\\*.exe"
      action: "verify"
      checks:
        - signature
        - hash
        - reputation
      notify_on_fail: true
    
    # Configuration changes
    - path: "C:\\Windows\\System32\\drivers\\etc\\*"
      action: "monitor"
      notify_on_change: true
      backup_on_change: true
    
    # Script monitoring
    - path: "C:\\Users\\**\\*.ps1"
      action: "scan"
      notify: true
      quarantine_on_detect: true

  notifications:
    siem: true
    syslog: true
    email: "security@example.com"
    
  scanning:
    engines: ["windows", "custom"]
    reputation_check: true
    sandbox_analysis: true

# Perché questa configurazione:
# - Sicurezza proattiva
# - Risposta automatica
# - Integrazione SIEM
