# Guida Completa Setup e Test CheckMK con File Monitor

## Indice
1. [Compatibilità Server](#compatibilità-server)
2. [Setup Server CheckMK](#setup-server-checkmk)
3. [Setup Agent Windows](#setup-agent-windows)
4. [Test End-to-End](#test-end-to-end)
5. [Architettura Comunicazione](#architettura-comunicazione)

## Compatibilità Server

### 1. Distribuzioni Linux Supportate
```plaintext
1. Ubuntu Server
   - 20.04 LTS (raccomandato)
   - 22.04 LTS
   - Requisiti minimi:
     * 2 CPU cores
     * 4GB RAM
     * 20GB disk

2. Debian
   - Debian 10 (Buster)
   - Debian 11 (Bullseye)
   - Requisiti minimi:
     * 2 CPU cores
     * 4GB RAM
     * 20GB disk

3. Red Hat Enterprise Linux (RHEL)
   - RHEL 8
   - RHEL 9
   - Requisiti minimi:
     * 2 CPU cores
     * 4GB RAM
     * 20GB disk

4. SUSE Linux Enterprise Server (SLES)
   - SLES 15
   - Requisiti minimi:
     * 2 CPU cores
     * 4GB RAM
     * 20GB disk
```

## Setup Server CheckMK

### 1. Installazione Ubuntu Server 20.04 LTS
```bash
# 1. Update sistema
sudo apt update
sudo apt upgrade -y

# 2. Installa dipendenze
sudo apt install -y apache2 wget

# 3. Download CheckMK
wget https://download.checkmk.com/checkmk/2.0.0p1/check-mk-raw-2.0.0p1_0.focal_amd64.deb

# 4. Installa CheckMK
sudo apt install -y ./check-mk-raw-2.0.0p1_0.focal_amd64.deb

# 5. Crea primo site
sudo omd create monitoring
sudo omd start monitoring
```

### 2. Configurazione Base Server
```bash
# 1. Accedi al site
su - monitoring

# 2. Cambia password admin
htpasswd -m etc/htpasswd cmkadmin

# 3. Configura rete
# Modifica /omd/sites/monitoring/etc/check_mk/main.mk
cat >> etc/check_mk/main.mk << EOF
if not this_file_is_modified:
    ipaddresses.update({
        "windows-agent": "192.168.1.100",  # IP VM Windows
    })
EOF

# 4. Applica configurazione
cmk -R
```

### 3. Setup Notifiche
```bash
# 1. Configura email
# Modifica /omd/sites/monitoring/etc/check_mk/main.mk
cat >> etc/check_mk/main.mk << EOF
notification_rules += [
    {
        "contact_all": True,
        "contact_object": True,
        "description": "File Monitor Notifications",
        "disabled": False,
        "notify_plugin": ("mail", {}),
    },
]
EOF

# 2. Test email
omd restart
cmk -N
```

## Setup Agent Windows

### 1. Installazione Agent
```powershell
# 1. Download agent da server CheckMK
# http://your-server/monitoring/check_mk/agents/windows/check_mk_agent.msi

# 2. Installa agent
msiexec /i check_mk_agent.msi /qn

# 3. Verifica servizio
Get-Service "CheckMKService"
```

### 2. Configurazione File Monitor
```yaml
# C:\ProgramData\checkmk\config\check_mk.yml
file_monitor:
  enabled: true
  timeout: 60
  
  paths:
    - path: "C:\\TestFiles\\*.txt"
      delete: true
    
    - path: "C:\\TestFiles\\important\\*.log"
      delete: false

  settings:
    check_interval: 300
    max_file_size: 104857600
```

### 3. Setup Test Files
```batch
# 1. Crea directory test
mkdir C:\TestFiles
mkdir C:\TestFiles\important

# 2. Crea file test
echo Test file 1 > C:\TestFiles\test1.txt
echo Test file 2 > C:\TestFiles\test2.txt
echo Important log > C:\TestFiles\important\app.log
```

## Test End-to-End

### 1. Verifica Connessione
```bash
# Sul server CheckMK
# 1. Aggiungi host
cmk -N windows-agent

# 2. Verifica connessione
cmk -P windows-agent
```

### 2. Test File Monitor
```powershell
# Su Windows
# 1. Test manuale
cd "C:\Program Files\CheckMK\Agent"
.\check_mk_agent.exe -d -s file_monitor

# 2. Verifica output sul server
# http://your-server/monitoring/check_mk/
# Services > windows-agent > File Monitor
```

### 3. Test Notifiche
```batch
# 1. Crea nuovo file
echo New file > C:\TestFiles\new_file.txt

# 2. Verifica sul server
# - Check Event Console
# - Verifica email
# - Controlla log
```

## Architettura Comunicazione

### 1. Modalità Pull (Default)
```plaintext
1. Funzionamento
   - Server CheckMK interroga l'agent periodicamente
   - Intervallo default: 1 minuto
   - Agent risponde con dati attuali

2. Configurazione
   # Sul server
   # /omd/sites/monitoring/etc/check_mk/main.mk
   check_interval = 60  # secondi

3. Vantaggi
   - Controllo centralizzato
   - Facile troubleshooting
   - Monitoraggio stato agent
```

### 2. Modalità Push (Opzionale)
```plaintext
1. Attivazione
   # C:\ProgramData\checkmk\config\check_mk.yml
   global:
     push_mode: true
     server_url: "http://your-server/monitoring/check_mk"

2. Funzionamento
   - Agent invia dati quando ci sono cambiamenti
   - Riduce latenza notifiche
   - Maggior carico rete

3. Casi d'uso
   - Monitoraggio real-time
   - Eventi critici
   - Ambienti con firewall restrittivi
```

### 3. Sicurezza Comunicazione
```plaintext
1. Autenticazione
   - Agent verifica server
   - Server verifica agent
   - Certificati TLS

2. Encryption
   - Comunicazione cifrata
   - TLS 1.2/1.3
   - Chiavi personalizzabili

3. Configurazione
   # Sul server
   site_config = {
       "agent_port": 6556,
       "agent_encryption": "enforce"
   }
```

## Verifica Funzionamento

### 1. Test Completo
```plaintext
1. Creazione File
   - Crea file in C:\TestFiles
   - Verifica rilevamento
   - Controlla eliminazione

2. Monitoraggio
   - Verifica sezione File Monitor
   - Controlla metriche
   - Verifica stato

3. Notifiche
   - Verifica email
   - Check Event Console
   - Controlla log
```

### 2. Performance
```plaintext
1. Monitoraggio Risorse
   - CPU usage
   - Memory usage
   - Network traffic

2. Ottimizzazione
   - Adjust check_interval
   - Tune buffer sizes
   - Optimize patterns
```

### 3. Troubleshooting
```plaintext
1. Log Agent
   # C:\ProgramData\checkmk\logs\check_mk.log
   - Verifica errori
   - Check connessione
   - Monitor operazioni

2. Log Server
   # /omd/sites/monitoring/var/log/
   - Check access.log
   - Verifica nagios.log
   - Monitor notifications.log

3. Diagnostica
   - Test connettività
   - Verifica firewall
   - Check certificati
