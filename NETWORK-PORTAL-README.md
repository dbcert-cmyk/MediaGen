# Home Network Management Portal

A comprehensive, AI-powered network management portal for home labs and small businesses. Completely free and open-source!

## Features

### 🌐 Network Management
- **Device Discovery**: Automatically scan and discover devices on your network
- **Device Monitoring**: Track device status, uptime, and connectivity
- **SSH Management**: Execute commands remotely on Linux servers
- **IPAM**: IP address management via Netbox integration
- **Network Monitoring**: Real-time monitoring with LibreNMS

### 🤖 AI Assistant
- **Local LLM**: Powered by Ollama (runs locally, no cloud required)
- **Natural Language**: Ask questions about your network in plain English
- **Automated Tasks**: AI agent can perform network operations for you
- **MCP Integration**: Model Context Protocol for tool integration

### 📊 Monitoring & Metrics
- **Netdata**: Real-time performance monitoring
- **LibreNMS**: Network device monitoring (SNMP, etc.)
- **Netbox**: Network documentation and IPAM
- **Custom Metrics**: Track custom device metrics

### 🔧 Network Operations
- **Network Scanning**: Discovery and port scanning
- **SSH Execution**: Remote command execution
- **Device Management**: CRUD operations for network devices
- **Configuration Management**: (Coming soon)

## Tech Stack

All components are **100% free and open-source**:

- **Backend**: FastAPI (Python)
- **Database**: PostgreSQL
- **Frontend**: Vanilla JavaScript (no framework lock-in)
- **AI**: Ollama (local LLM runtime)
- **Monitoring**: Netdata, LibreNMS, Netbox
- **Deployment**: Docker Compose

## Quick Start

### Prerequisites

- Linux VM or server (Ubuntu 22.04+ recommended)
- Docker & Docker Compose installed
- Minimum 8GB RAM (16GB recommended for AI features)
- GPU optional but recommended for faster AI responses

### Installation

1. **Clone or navigate to the repository**:
   ```bash
   cd /path/to/dxb
   ```

2. **Copy environment file**:
   ```bash
   cp .env.network-portal .env
   ```

3. **Edit configuration** (optional):
   ```bash
   nano .env
   ```

4. **Start all services**:
   ```bash
   docker-compose up -d
   ```

5. **Wait for services to initialize** (first time takes ~2 minutes):
   ```bash
   docker-compose logs -f network-portal
   ```

6. **Download AI model** (first time only):
   ```bash
   docker exec -it dxb-ollama-1 ollama pull llama3.2
   ```

### Access the Portal

- **Main Portal**: http://localhost:8000
- **Netdata**: http://localhost:19999
- **LibreNMS**: http://localhost:8001
- **Netbox**: http://localhost:8080

### Default Credentials

**Netbox**:
- Username: `admin`
- Password: `admin`

**LibreNMS**: First-time setup wizard will run automatically

## Usage Guide

### 1. Dashboard

The dashboard provides an overview of your network:
- Total devices
- Online/offline status
- Device types breakdown
- Quick actions

### 2. Adding Devices

Two ways to add devices:

**Manual**:
1. Go to "Devices" tab
2. Click "Add Device"
3. Fill in device details
4. Click "Add Device"

**Automatic (Network Scan)**:
1. Go to "Network Ops" tab
2. Enter your subnet (e.g., `192.168.1.0/24`)
3. Click "Start Scan"
4. Discovered devices are automatically added

### 3. Network Operations

**Ping Devices**:
- In Devices tab, click "Ping" next to any device

**SSH Commands**:
1. Go to "Network Ops" tab
2. Scroll to "SSH Command Execution"
3. Enter host, username, password
4. Enter command (e.g., `uptime`, `df -h`)
5. Click "Execute"

**Network Scanning**:
- Discovery scan: Find active hosts
- Port scan: Find open ports on hosts

### 4. AI Assistant

The AI assistant can help with network tasks:

**Example queries**:
- "Scan my network for new devices"
- "Show me all offline devices"
- "What is the status of my network?"
- "Execute 'uptime' on 192.168.1.100"

**Note**: AI features require Ollama model to be downloaded (see installation step 6)

### 5. Monitoring

**Netdata** (http://localhost:19999):
- Real-time system metrics
- CPU, memory, disk, network
- Beautiful visualizations

**LibreNMS** (http://localhost:8001):
- Add network devices (switches, routers, APs)
- SNMP monitoring
- Alerting

**Netbox** (http://localhost:8080):
- Document your network
- IP address management
- Rack layouts, cables, etc.

## MCP Servers

The portal includes built-in MCP (Model Context Protocol) servers:

### network_scanner
- `scan_network(subnet, scan_type)`: Scan network for devices
- Supports discovery and port scanning

### ssh_manager
- `execute_ssh_command(...)`: Execute commands via SSH
- `test_ssh_connection(...)`: Test SSH connectivity
- `get_system_info(...)`: Gather system information

### device_info
- `get_device_info(device_id)`: Get device details
- `get_all_devices()`: List all devices
- `update_device_status(...)`: Update device status

## API Documentation

Once running, visit http://localhost:8000/docs for interactive API documentation.

### Key Endpoints

**Devices**:
- `GET /api/devices/`: List all devices
- `POST /api/devices/`: Add new device
- `DELETE /api/devices/{id}`: Delete device
- `POST /api/devices/{id}/ping`: Ping device

**Network Operations**:
- `POST /api/network/scan`: Start network scan
- `GET /api/network/scans`: List scans
- `POST /api/network/ssh/execute`: Execute SSH command

**Monitoring**:
- `GET /api/monitoring/dashboard/summary`: Dashboard stats
- `GET /api/monitoring/metrics/{device_id}`: Device metrics

**AI Agent**:
- `POST /api/ai/query`: Query AI assistant
- `GET /api/ai/tasks`: List AI tasks

## Architecture

```
┌─────────────────────────────────────────┐
│   Web Dashboard (HTML/CSS/JS)          │
├─────────────────────────────────────────┤
│   FastAPI Backend                       │
│   ├─ Device Management                 │
│   ├─ Network Operations                │
│   ├─ Monitoring APIs                   │
│   └─ AI Agent Integration              │
├─────────────────────────────────────────┤
│   MCP Server Layer                      │
│   ├─ Network Scanner                   │
│   ├─ SSH Manager                       │
│   └─ Device Info                       │
├─────────────────────────────────────────┤
│   AI Agent (Ollama + LangChain)        │
├─────────────────────────────────────────┤
│   Supporting Services                   │
│   ├─ PostgreSQL (Database)             │
│   ├─ Netbox (IPAM)                     │
│   ├─ LibreNMS (Monitoring)             │
│   └─ Netdata (Metrics)                 │
└─────────────────────────────────────────┘
```

## Supported Network Devices

### Servers
- Linux (any distro with SSH)
- Windows (with OpenSSH)

### Network Equipment
- UniFi (AP, switches)
- Mikrotik
- Cisco
- TP-Link
- Any device with SNMP support

### Requirements for Monitoring
- **SSH**: Linux/Unix servers
- **SNMP**: Network switches, APs, routers
- **ICMP**: Basic ping monitoring (all devices)

## Troubleshooting

### Services won't start
```bash
# Check logs
docker-compose logs

# Restart services
docker-compose restart

# Full reset
docker-compose down -v
docker-compose up -d
```

### Ollama model not working
```bash
# Check if model is downloaded
docker exec -it dxb-ollama-1 ollama list

# Download model
docker exec -it dxb-ollama-1 ollama pull llama3.2

# Try a smaller model if RAM limited
docker exec -it dxb-ollama-1 ollama pull llama3.2:1b
```

### Network scan not finding devices
- Ensure you're using correct subnet CIDR notation
- Check firewall rules allow ICMP
- Try port scan instead of discovery
- Verify docker container has network access

### SSH commands failing
- Verify SSH is enabled on target device
- Check username/password are correct
- Ensure SSH port is not blocked
- Try manual SSH from command line first

### Database errors
```bash
# Recreate database
docker-compose down postgres
docker volume rm dxb_postgres_data
docker-compose up -d postgres
```

## Security Considerations

### Change Default Passwords
```bash
# Edit .env file
nano .env
```

Change:
- `SECRET_KEY`
- `API_KEY`
- Database passwords in docker-compose.yml
- Netbox admin password

### Network Security
- Run on isolated management VLAN
- Use firewall rules to restrict access
- Enable authentication on all services
- Use SSH keys instead of passwords
- Keep services updated

### Credentials Storage
- Credentials are encrypted in database
- Never commit .env file to git
- Use SSH keys when possible
- Rotate passwords regularly

## Advanced Configuration

### Custom AI Model

Edit `.env`:
```bash
OLLAMA_MODEL=mistral  # or codellama, neural-chat, etc.
```

Then:
```bash
docker exec -it dxb-ollama-1 ollama pull mistral
docker-compose restart network-portal
```

### Add GPU Support

Ensure NVIDIA Docker runtime is installed, then GPU support is already configured in docker-compose.yml.

### Scale for Larger Networks

Edit docker-compose.yml to increase resources:
```yaml
services:
  network-portal:
    deploy:
      resources:
        limits:
          cpus: '4'
          memory: 8G
```

## Development

### Project Structure
```
network-portal/
├── main.py              # FastAPI application
├── database.py          # Database models
├── routers/             # API endpoints
│   ├── devices.py
│   ├── monitoring.py
│   ├── network_ops.py
│   └── ai_agent.py
├── mcp_servers/         # MCP server implementations
│   ├── network_scanner.py
│   ├── ssh_manager.py
│   └── device_info.py
├── ai/                  # AI agent
│   └── agent_manager.py
├── static/              # Frontend assets
│   ├── styles.css
│   └── app.js
└── templates/
    └── index.html       # Main UI
```

### Adding New Features

1. Create new router in `routers/`
2. Add MCP server in `mcp_servers/` if needed
3. Include router in `main.py`
4. Update UI in `templates/index.html`

## Roadmap

- [ ] Configuration management (Ansible integration)
- [ ] WiFi controller integration (UniFi, OpenWrt)
- [ ] Advanced alerting and notifications
- [ ] Network topology visualization
- [ ] Backup and restore functionality
- [ ] Multi-user support with RBAC
- [ ] Mobile-responsive UI improvements
- [ ] Plugin system for extensibility

## Contributing

This is a starter project. Feel free to:
- Report issues
- Submit pull requests
- Suggest features
- Share your customizations

## License

MIT License - Free for personal and commercial use

## Support

- GitHub Issues: Report bugs and request features
- Documentation: This README
- API Docs: http://localhost:8000/docs

## Acknowledgments

Built with these amazing open-source projects:
- FastAPI
- Ollama
- Netbox
- LibreNMS
- Netdata
- PostgreSQL
- LangChain
- Paramiko
- And many more!

---

**Happy Network Managing! 🎉**
