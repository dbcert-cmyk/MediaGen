# Getting Started with Network Management Portal

## Quick Start (Easiest)

```bash
./start.sh
```

This will:
1. Create a Python virtual environment
2. Install all dependencies
3. Create a default config.yaml
4. Start the application

Then open your browser to: **http://localhost:5001**

---

## Manual Setup

### 1. Install Dependencies

```bash
# Create virtual environment
python3 -m venv venv
source venv/bin/activate

# Install requirements
pip install -r requirements.txt
```

### 2. Configure Your Network Devices

Edit `config.yaml` to add your servers, WiFi APs, and switches:

#### Monitor Local Server

```yaml
servers:
  - name: "Local Server"
    host: "localhost"
    type: "local"
    enabled: true
```

#### Monitor Remote Servers (SSH)

```yaml
servers:
  - name: "Remote Server"
    host: "192.168.1.100"
    type: "ssh"
    username: "admin"
    ssh_key: "/home/user/.ssh/id_rsa"  # Recommended
    # password: "password"  # Or use password (less secure)
    enabled: true
```

**Set up SSH keys (recommended):**
```bash
# Generate SSH key if you don't have one
ssh-keygen -t rsa -b 4096

# Copy to remote server
ssh-copy-id admin@192.168.1.100
```

#### Monitor WiFi Access Points (SNMP)

```yaml
wifi_aps:
  - name: "Living Room AP"
    host: "192.168.1.10"
    type: "snmp"
    community: "public"  # Your SNMP community string
    enabled: true
```

**Enable SNMP on your AP:**
- Most APs: Web UI → System → SNMP → Enable
- Community String: Use a secure string (not "public" in production)
- SNMP Version: v2c recommended

#### Monitor Network Switches (SNMP)

```yaml
switches:
  - name: "Main Switch"
    host: "192.168.1.1"
    type: "snmp"
    community: "public"
    enabled: true
```

### 3. Run the Application

```bash
python app.py
```

Access at: http://localhost:5001

---

## AI-Powered Network Assistant (Optional)

### Enabling the AI Agent

The portal includes an optional AI assistant that can answer questions about your network in natural language.

**Prerequisites:**
- Google API Key (free tier available)

**Setup Steps:**

1. **Get your Google API Key**
   ```bash
   # Visit Google AI Studio
   open https://aistudio.google.com/app/apikey

   # Create a new API key
   # Copy the key
   ```

2. **Configure the environment**
   ```bash
   # Create .env file from example
   cp .env.example .env

   # Edit .env and add your key
   echo "GOOGLE_API_KEY=your_actual_key_here" >> .env
   ```

3. **Restart the application**
   ```bash
   # If running manually
   python app.py

   # If using Docker
   docker-compose restart
   ```

### Using the AI Assistant

Once configured, you'll see an "Ask AI" button in the bottom-right corner of the dashboard.

**Example Queries:**
- "Which devices are offline?"
- "Why is my server's CPU usage so high?"
- "How many WiFi clients are connected?"
- "Show me all servers with high disk usage"
- "What's the status of my network switches?"

The AI assistant uses:
- **Google Gemini 2.5 Flash** for intelligent responses
- **MCP (Model Context Protocol)** servers for network data access
- **Multi-step reasoning** to gather and analyze information

**Privacy Note**: All network queries are processed through Google's Gemini API. Network data is only sent when you explicitly ask questions. The assistant is completely optional and can be disabled by not setting the GOOGLE_API_KEY.

---

## Docker Deployment

### Quick Start with Docker

```bash
# Build and run
docker-compose up -d

# View logs
docker-compose logs -f

# Stop
docker-compose down
```

---

## Configuring Specific Devices

### UniFi Access Points

```yaml
wifi_aps:
  - name: "UniFi AP"
    host: "192.168.1.10"
    type: "unifi"
    controller: "192.168.1.2"  # UniFi Controller IP
    username: "admin"
    password: "password"
    enabled: true
```

### TP-Link Omada APs

```yaml
wifi_aps:
  - name: "Omada AP"
    host: "192.168.1.10"
    type: "snmp"
    community: "public"
    enabled: true
```

### Managed Switches with VLANs

```yaml
switches:
  - name: "Core Switch"
    host: "192.168.1.1"
    type: "snmp"
    community: "public"
    vlan_support: true
    port_count: 48  # Number of ports
    enabled: true
```

---

## Alert Configuration

Set thresholds for automatic alerts:

```yaml
alerts:
  cpu_threshold: 80      # Alert if CPU > 80%
  memory_threshold: 85   # Alert if memory > 85%
  disk_threshold: 90     # Alert if disk > 90%
  email_enabled: false   # Set to true for email alerts
  # email_to: "admin@example.com"
  # email_from: "network@example.com"
```

---

## Troubleshooting

### Server Monitoring Issues

**Local server not showing stats:**
- Ensure `psutil` is installed: `pip install psutil`
- Check permissions for disk/network monitoring

**Remote server SSH connection fails:**
```bash
# Test SSH connection manually
ssh -i /path/to/key user@host

# Check SSH key permissions
chmod 600 /path/to/key
chmod 700 ~/.ssh
```

### SNMP Monitoring Issues

**WiFi AP/Switch not responding:**
1. Enable SNMP on the device
2. Check SNMP community string matches config
3. Test SNMP manually:
   ```bash
   snmpwalk -v2c -c public 192.168.1.10
   ```
4. Check firewall allows UDP port 161

**Common SNMP OIDs for testing:**
- System Description: `.1.3.6.1.2.1.1.1.0`
- Uptime: `.1.3.6.1.2.1.1.3.0`
- Interfaces: `.1.3.6.1.2.1.2.2.1`

### Port Already in Use

Change the port in `config.yaml`:
```yaml
dashboard:
  port: 5002  # Change from 5001
```

---

## Security Best Practices

1. **Use SSH keys** instead of passwords for remote servers
2. **Change SNMP community strings** from default "public"
3. **Run behind a reverse proxy** with HTTPS (nginx, Caddy)
4. **Restrict access** to your local network only
5. **Use strong passwords** for device credentials
6. **Keep software updated** regularly

---

## Adding More Devices

Just edit `config.yaml` and add more entries under `servers`, `wifi_aps`, or `switches`. The dashboard updates automatically!

Example adding multiple devices:

```yaml
servers:
  - name: "Main Server"
    host: "localhost"
    type: "local"
    enabled: true

  - name: "NAS"
    host: "192.168.1.10"
    type: "ssh"
    username: "admin"
    ssh_key: "/home/user/.ssh/id_rsa"
    enabled: true

  - name: "Raspberry Pi"
    host: "192.168.1.20"
    type: "ssh"
    username: "pi"
    ssh_key: "/home/user/.ssh/id_rsa"
    enabled: true
```

---

## Next Steps

- Customize alert thresholds
- Add email notifications
- Set up historical data logging
- Create custom dashboards for different views
- Integrate with other monitoring tools

Need help? Check the README.md or create an issue on GitHub!
