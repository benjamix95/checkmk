# Setup Ambiente di Test Completo

## Indice
1. [Setup VM Network](#setup-vm-network)
2. [VM Linux Server](#vm-linux-server)
3. [VM Windows Client](#vm-windows-client)
4. [Test Integrazione](#test-integrazione)

## Setup VM Network

### 1. Configurazione VMware Network
```plaintext
1. Crea Network Privata
   - VMware Workstation > Edit > Virtual Network Editor
   - Add Network
   - Nome: VMnet2
   - Type: Host-only
   
2. Configurazione IP
   - Subnet IP: 192.168.100.0
   - Subnet mask: 255.255.255.0
   - Gateway: 192.168.100.1
   
3. DHCP Settings
   - Range start: 192.168.100.128
   - Range end: 192.168.100.254
```

### 2. Firewall Rules
```plaintext
1. Regole Windows
   - Inbound: TCP 6556 (Agent)
   - Outbound: TCP 80/443 (Web UI)
   
2. Regole Linux
   - Inbound: TCP 80/443 (Web UI)
   - Outbound: TCP 6556 (Agent)
```

## VM Linux Server

### 1. Creazione VM Ubuntu Server
```plaintext
1. New Virtual Machine
   - Guest OS: Ubuntu 20.04 LTS Server
   - Memory: 4GB
   - Processors: 2
   - Hard Disk: 40GB
   - Network: VMnet2
   
2. Settings Aggiuntivi
   - Enable virtualization
   - Enable PAE/NX
   - Enable HPET
```

### 2. Installazione Ubuntu
```bash
# 1. Setup base
sudo apt update
sudo apt upgrade -y

# 2. Setup rete statica
sudo nano /etc/netplan/00-installer-config.yaml
```
```yaml
network:
  ethernets:
    ens33:
      addresses:
        - 192.168.100.10/24
      gateway4: 192.168.100.1
      nameservers:
        addresses: [8.8.8.8, 8.8.4.4]
  version: 2
```
```bash
# Applica configurazione
sudo netplan apply
```

### 3. Installazione CheckMK
```bash
# 1. Download CheckMK
wget https://download.checkmk.com/checkmk/2.0.0p1/check-mk-raw-2.0.0p1_0.focal_amd64.deb

# 2. Installa
sudo apt install -y ./check-mk-raw-2.0.0p1_0.focal_amd64.deb

# 3. Crea site
sudo omd create monitoring
sudo omd start monitoring

# 4. Setup firewall
sudo ufw allow 80/tcp
sudo ufw allow 443/tcp
sudo ufw enable
```

### 4. Configurazione CheckMK
```bash
# 1. Accedi al site
su - monitoring

# 2. Setup base
# File: ~/etc/check_mk/main.mk
cat > etc/check_mk/main.mk << EOF
# Global settings
check_mk_web_service = {
    'socket': 'tcp://0.0.0.0:6556',
    'allowed_networks': ['192.168.100.0/24'],
}

# File Monitor settings
extra_service_conf.update({
    'check_interval': [
        ( "1", [], ["File Monitor"] ),
    ],
})

# Notification settings
notification_rules += [
    {
        "description": "File Monitor Events",
        "comment": "Notify on file events",
        "disabled": False,
        "contact_all": True,
        "contact_object": True,
        "contact_users": ["cmkadmin"],
        "match_sl": (10, 999999),
        "match_host_tags": [],
        "match_hostgroups": [],
        "match_servicegroups": [],
        "match_services": ["File Monitor"],
        "match_contacts": ["all"],
        "notify_plugin": ("mail", {}),
    },
]
EOF

# 3. Riavvia servizi
omd restart
```

## VM Windows Client

### 1. Creazione VM Windows
```plaintext
1. New Virtual Machine
   - Guest OS: Windows 10 Pro x64
   - Memory: 4GB
   - Processors: 2
   - Hard Disk: 60GB
   - Network: VMnet2
   
2. Settings Aggiuntivi
   - Enable virtualization
   - Enable 3D acceleration
   - Enable sound card
```

### 2. Configurazione Windows
```powershell
# 1. Setup IP Statico
# Network Settings > Ethernet > IP Settings
# IP: 192.168.100.20
# Mask: 255.255.255.0
# Gateway: 192.168.100.1
# DNS: 8.8.8.8, 8.8.4.4

# 2. Hostname
Rename-Computer -NewName "WIN-FILEMON"

# 3. Firewall
New-NetFirewallRule -DisplayName "CheckMK Agent" `
    -Direction Inbound `
    -Action Allow `
    -Protocol TCP `
    -LocalPort 6556
```

### 3. Setup Test Environment
```batch
# 1. Crea struttura directory
mkdir C:\TestFiles
mkdir C:\TestFiles\important
mkdir C:\TestFiles\temp

# 2. Crea file test
echo File to delete > C:\TestFiles\delete_me.txt
echo Important file > C:\TestFiles\important\keep_me.txt
echo Temp file > C:\TestFiles\temp\temp.txt

# 3. Setup permessi
icacls C:\TestFiles /grant "NT AUTHORITY\SYSTEM:(OI)(CI)F"
icacls C:\TestFiles /grant "Administrators:(OI)(CI)F"
```

### 4. Installazione Agent
```powershell
# 1. Download agent
# Da browser: http://192.168.100.10/monitoring/check_mk/agents/windows/check_mk_agent.msi

# 2. Installa
msiexec /i check_mk_agent.msi /qn

# 3. Configura
# File: C:\ProgramData\checkmk\config\check_mk.yml
```
```yaml
file_monitor:
  enabled: true
  timeout: 60
  retry: 3
  
  paths:
    - path: "C:\\TestFiles\\*.txt"
      delete: true
      
    - path: "C:\\TestFiles\\important\\*.txt"
      delete: false
      
    - path: "C:\\TestFiles\\temp\\*.txt"
      delete: true
      older_than: "1h"

  settings:
    check_interval: 300
    max_file_size: 104857600
    
  notifications:
    on_found: true
    on_delete: true
    levels:
      found: info
      deleted: warning
      error: critical
```

## Test Integrazione

### 1. Verifica Connettività
```bash
# Su Linux Server
# 1. Test ping
ping 192.168.100.20

# 2. Test porta agent
nc -zv 192.168.100.20 6556

# 3. Aggiungi host
cmk -N WIN-FILEMON
```

### 2. Test File Monitor
```powershell
# Su Windows Client
# 1. Test manuale
cd "C:\Program Files\CheckMK\Agent"
.\check_mk_agent.exe -d -s file_monitor

# 2. Crea nuovi file
echo Test1 > C:\TestFiles\test1.txt
echo Test2 > C:\TestFiles\test2.txt
```

### 3. Verifica Notifiche
```plaintext
1. CheckMK Web UI
   - Accedi: http://192.168.100.10/monitoring
   - Vai a: Services > WIN-FILEMON
   - Verifica: File Monitor status
   
2. Event Console
   - Verifica eventi file trovati
   - Controlla eventi eliminazione
   - Check errori
   
3. Email Notifications
   - Controlla inbox admin
   - Verifica formato notifiche
   - Check tempi risposta
```

### 4. Test Performance
```plaintext
1. Creazione File Massivi
   # Su Windows
   for /L %i in (1,1,1000) do echo Test > C:\TestFiles\file%i.txt
   
2. Monitor Risorse
   - CPU Usage
   - Memory Usage
   - Network Traffic
   
3. Verifica Tempi
   - Rilevamento file
   - Eliminazione file
   - Invio notifiche
```

### 5. Troubleshooting
```plaintext
1. Log Agent
   # Windows Event Viewer
   - Application Log
   - System Log
   
2. Log Server
   # /omd/sites/monitoring/var/log/
   - nagios.log
   - check_mk.log
   
3. Network
   # Wireshark su VMnet2
   - Traffico agent
   - Pacchetti notifiche
   - Latenza rete
