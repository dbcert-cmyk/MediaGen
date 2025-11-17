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
✅ **🤖 AI-Powered Network Assistant** (NEW!)
  - Natural language queries about your network
  - Intelligent troubleshooting and recommendations
  - Multi-step reasoning with Google Gemini
  - MCP server integration for network data access
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

## AI Agent Setup (Optional)

To enable the AI-powered network assistant:

1. **Get a Google API Key**
   - Visit [Google AI Studio](https://aistudio.google.com/app/apikey)
   - Create a new API key

2. **Configure the key**
   ```bash
   # Create .env file
   cp .env.example .env

   # Edit .env and add your key
   GOOGLE_API_KEY=your_api_key_here
   ```

3. **Restart the application**

The AI assistant will now be available! Click the "Ask AI" button in the bottom-right corner to:
- Ask questions like "Which devices are offline?"
- Get intelligent troubleshooting: "Why is my server CPU high?"
- Analyze network status: "Show me all WiFi clients"

**Note**: The AI assistant is completely optional. The portal works perfectly without it for basic monitoring.

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
