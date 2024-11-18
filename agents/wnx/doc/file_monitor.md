# File Monitor Provider

Il File Monitor Provider è un componente di CheckMK che permette di monitorare file e directory su sistemi Windows, con la capacità di eliminare automaticamente i file indesiderati.

## Funzionalità

- Monitoraggio di file specifici
- Supporto per pattern glob (*.txt, *.log, ecc.)
- Monitoraggio ricorsivo di directory
- Eliminazione automatica dei file
- Integrazione con il sistema di notifiche di CheckMK

## Configurazione

La configurazione viene effettuata attraverso il file YAML. Esempio:

```yaml
file_monitor:
  enabled: true
  timeout: 60
  retry: 3
  async: false
  cache_age: 300

  # Lista dei percorsi da monitorare
  paths:
    # Monitoraggio di un file specifico
    - path: "C:\\temp\\test.txt"
      delete: true

    # Monitoraggio di file di log
    - path: "C:\\logs\\*.log"
      delete: false

    # Monitoraggio ricorsivo
    - path: "C:\\Users\\**\\Downloads\\*.exe"
      delete: true

  # Impostazioni avanzate
  settings:
    max_file_size: 104857600  # 100MB
    max_files_per_check: 1000
    log_operations: true
```

## Output

Il provider genera output nel seguente formato:

```
<<<file_monitor>>>
CheckInterval: 300 seconds
C:\temp\test.txt|found|will_delete
C:\logs\app.log|found|keep
C:\logs\error.log|not_found|keep
C:\Users\user\Downloads\setup.exe|found|will_delete
```

Ogni riga contiene:
- Percorso del file
- Stato (found/not_found)
- Azione (will_delete/keep)

## Integrazione con CheckMK

Il provider si integra con il sistema di notifiche di CheckMK, inviando avvisi quando:
- Vengono trovati nuovi file
- I file vengono eliminati
- Si verificano errori durante il monitoraggio

## Requisiti di Sistema

- Windows 10/11 o Windows Server 2016+
- CheckMK Agent per Windows
- Permessi di lettura/scrittura nelle directory monitorate

## Risoluzione dei Problemi

### Log

Il provider registra le sue attività nel log di sistema di CheckMK. Per abilitare il logging dettagliato:

```yaml
logging:
  level: debug
  console: true
  file: true
  filename: "C:\\ProgramData\\checkmk\\logs\\file_monitor.log"
```

### Errori Comuni

1. **Permessi Insufficienti**
   - Verificare che l'utente del servizio CheckMK abbia i permessi necessari

2. **Pattern Glob Non Validi**
   - Verificare la sintassi dei pattern
   - Usare doppi backslash nei percorsi Windows

3. **Timeout**
   - Aumentare il valore di timeout se si monitorano molti file
   - Ridurre il numero di file monitorati

## Best Practices

1. **Performance**
   - Limitare il numero di pattern ricorsivi
   - Impostare limiti appropriati per max_files_per_check
   - Usare pattern specifici invece di pattern generici

2. **Sicurezza**
   - Evitare di monitorare directory di sistema
   - Verificare attentamente i pattern prima di abilitare l'eliminazione automatica
   - Testare in un ambiente di sviluppo prima della produzione

3. **Manutenzione**
   - Controllare regolarmente i log
   - Aggiornare i pattern quando cambiano le esigenze
   - Mantenere una documentazione dei pattern utilizzati
