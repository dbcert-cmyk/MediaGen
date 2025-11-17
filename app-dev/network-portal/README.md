# Home Network Management Portal

A comprehensive, open-source network management dashboard for monitoring and managing:
- Linux servers (CPU, RAM, disk, services, uptime)
- WiFi Access Points (clients, signal strength, bandwidth)
- Network switches (port status, traffic, VLANs)

## Features

✅ Real-time server monitoring
✅ WiFi client tracking and bandwidth usage
✅ Switch port status and traffic graphs
✅ Service health monitoring
✅ Alert system for issues
✅ Beautiful, responsive dashboard
✅ 100% free and open source

## Tech Stack

- **Backend**: Flask (Python)
- **Monitoring**: SNMP, SSH, psutil
- **Frontend**: HTML/CSS/JS with Chart.js
- **Database**: SQLite
- **Deployment**: Docker or Linux VM

## Quick Start

### Option 1: Docker (Recommended)
```bash
docker-compose up -d
```

### Option 2: Manual Installation
```bash
# Create virtual environment
python3 -m venv venv
source venv/bin/activate

# Install dependencies
pip install -r requirements.txt

# Configure devices
cp config.example.yaml config.yaml
# Edit config.yaml with your device details

# Run the application
python app.py
```

Access the dashboard at: http://localhost:5001

## Configuration

Edit `config.yaml` to add your devices:

```yaml
servers:
  - name: "Main Server"
    host: "192.168.1.100"
    type: "ssh"  # or "local" for the server running this app
    username: "admin"
    ssh_key: "/path/to/key"  # optional, for SSH

wifi_aps:
  - name: "Living Room AP"
    host: "192.168.1.10"
    type: "snmp"  # or "unifi", "omada"
    community: "public"

switches:
  - name: "Main Switch"
    host: "192.168.1.1"
    type: "snmp"
    community: "public"
```

## Screenshots

[Dashboard showing real-time server stats, WiFi clients, and switch ports]

## License

MIT License - 100% Free and Open Source
