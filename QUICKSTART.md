# Quick Start Guide

Get your Home Network Portal running in 5 minutes!

## Prerequisites

- Linux machine (VM or physical)
- Docker & Docker Compose installed
- 8GB+ RAM (16GB recommended)
- Network access to your devices

## Installation

### 1. Start the Portal

```bash
./start-network-portal.sh
```

That's it! The script will:
- Create configuration file
- Start all Docker services
- Display access URLs

### 2. Download AI Model (First Time Only)

```bash
docker exec -it dxb-ollama-1 ollama pull llama3.2
```

Wait for the download to complete (~2GB).

### 3. Access the Portal

Open your browser to: **http://localhost:8000**

## First Steps

### Add Your First Device

1. Click **"Devices"** tab
2. Click **"Add Device"** button
3. Fill in:
   - Name: `My Server`
   - Type: `server`
   - IP: `192.168.1.100`
4. Click **"Add Device"**

### Scan Your Network

1. Click **"Network Ops"** tab
2. Enter your subnet: `192.168.1.0/24`
3. Click **"Start Scan"**
4. Wait for results (~30 seconds)
5. Devices are auto-discovered!

### Try the AI Assistant

1. Click **"AI Assistant"** tab
2. Type: "Show me all offline devices"
3. Press Enter
4. AI will respond with device status

## Common Tasks

### Check Device Status
1. Go to **"Devices"** tab
2. Click **"Ping"** next to any device

### Execute SSH Command
1. Go to **"Network Ops"** tab
2. Enter SSH credentials
3. Type command (e.g., `uptime`)
4. Click **"Execute"**

### View Real-time Metrics
- Click **"Monitoring"** tab
- Click **"Open Netdata"**
- View live system metrics

## Troubleshooting

### Services not starting?
```bash
docker-compose logs -f
```

### Need to restart?
```bash
docker-compose restart
```

### Fresh start?
```bash
docker-compose down -v
./start-network-portal.sh
```

## Next Steps

- Read full documentation: `NETWORK-PORTAL-README.md`
- Configure Netbox for IPAM: http://localhost:8080
- Set up LibreNMS monitoring: http://localhost:8001
- Customize your dashboard

## Support

- Full docs: See `NETWORK-PORTAL-README.md`
- API docs: http://localhost:8000/docs
- Service health: http://localhost:8000/health

---

**You're all set! Happy network managing! 🚀**
