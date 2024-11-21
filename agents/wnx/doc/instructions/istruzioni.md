# Istruzioni per l'Installazione del File Monitor

## 1. Prerequisiti
- Windows VM con Visual Studio 2022 installato
- CheckMK Agent installato sulla VM

## 2. Struttura Directory Standard di CheckMK Agent
Dopo l'installazione dell'agente CheckMK su Windows, troverai questa struttura:
```
C:\Program Files\CheckMK\Agent\           # Directory principale dell'agente
    |- check_mk_agent.exe                 # Eseguibile principale
    |- plugins\                           # Directory per i plugin
    |- providers\                         # Directory per i provider (qui va la nostra DLL)
    
C:\ProgramData\checkmk\                   # Directory dati dell'agente
    |- config\                            # Directory configurazione
        |- check_mk.yml                   # File configurazione principale
    |- logs\                              # Directory log
        |- file_monitor.log               # Log del nostro provider
```

## 3. Passi per l'Installazione

### 3.1. Copiare la DLL
```batch
# La DLL compilata si trova in:
C:\Users\b.stoica\Documenti\checkmk\checkmk\agents\wnx\build\bin\Release\checkmk_file_monitor.dll

# Copiarla in:
C:\Program Files\CheckMK\Agent\providers\checkmk_file_monitor.dll
```

### 3.2. Configurare il Monitor
```batch
# Creare/modificare il file:
C:\ProgramData\checkmk\config\check_mk.yml

# Aggiungere questa configurazione:
file_monitor:
    # Intervallo di controllo in secondi
    check_interval: 300

    # Lista dei percorsi da monitorare
    paths:
        # Esempio: monitoraggio file temporanei
        - path: "C:\\Temp\\Files"           # Directory da monitorare
          is_directory: true                # È una directory
          delete: true                      # Elimina i file trovati
          pattern: "*.tmp"                  # Monitora solo file .tmp

    # Configurazione logging
    logging:
        enabled: true
        level: "DEBUG"
        file: "C:\\ProgramData\\checkmk\\logs\\file_monitor.log"
```

### 3.3. Creare Directory da Monitorare
```batch
# Esempio: creare directory per file temporanei
mkdir "C:\Temp\Files"

# Creare alcuni file di test
echo "test" > "C:\Temp\Files\test1.tmp"
echo "test" > "C:\Temp\Files\test2.tmp"
```

### 3.4. Riavviare il Servizio
```batch
# Fermare il servizio
net stop CheckMKService

# Avviare il servizio
net start CheckMKService
```

## 4. Verifica dell'Installazione

### 4.1. Controllare i Log
```batch
# Aprire il file di log
notepad "C:\ProgramData\checkmk\logs\file_monitor.log"

# Dovrebbe mostrare messaggi di inizializzazione e monitoraggio
```

### 4.2. Testare il Monitoraggio
```batch
# Creare un nuovo file temporaneo
echo "test" > "C:\Temp\Files\test_new.tmp"

# Aspettare l'intervallo di controllo (default 5 minuti)
# Verificare che il file sia stato eliminato
dir "C:\Temp\Files\test_new.tmp"
```

### 4.3. Verificare l'Output dell'Agente
```batch
# Eseguire l'agente manualmente
"C:\Program Files\CheckMK\Agent\check_mk_agent.exe"

# Cercare la sezione <<<file_monitor>>> nell'output
# Dovrebbe mostrare informazioni sui file monitorati
```

## 5. Troubleshooting

### 5.1. Se la DLL non si carica
- Verificare che la DLL sia nella directory corretta
- Controllare i permessi della directory providers
- Verificare eventuali errori nel log eventi di Windows

### 5.2. Se il monitoraggio non funziona
- Controllare il file di configurazione per errori di sintassi
- Verificare i permessi delle directory monitorate
- Aumentare il livello di log a "DEBUG"
- Controllare il file di log per errori specifici

### 5.3. Se i file non vengono eliminati
- Verificare i permessi dell'account di servizio
- Controllare se i file sono in uso
- Verificare la configurazione delete: true


Per l'utilizzo quotidiano, puoi modificare solo il file di configurazione:

C:\ProgramData\checkmk\config\check_mk.yml

In questo file, nella sezione file_monitor, puoi specificare:


I pattern dei file da monitorare, per esempio:
file_monitor:
    paths:
        # Monitora file .log
        - path: "C:\\Logs"
          pattern: "*.log"
          delete: false

        # Monitora file temporanei
        - path: "C:\\Temp"
          pattern: "temp_*.tmp"
          delete: true

        # Monitora file specifici
        - path: "C:\\Data"
          pattern: "backup_*.{bak,old}"  # monitora file .bak e .old
          delete: true

        # Monitora con esclusioni
        - path: "C:\\Downloads"
          pattern: "*.tmp"
          exclude_patterns:
            - "important_*.tmp"
            - "keep_*.tmp"
Non devi modificare nessun altro file - tutte le configurazioni si fanno in questo unico file YAML. Il pattern supporta:

= qualsiasi sequenza di caratteri
? = un singolo carattere
[abc] = uno dei caratteri specificati
{pattern1,pattern2} = uno dei pattern specificati
exclude_patterns = file da non monitorare/eliminare