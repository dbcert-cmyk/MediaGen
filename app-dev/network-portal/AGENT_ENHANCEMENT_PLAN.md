# Adding Agentic Capabilities to Network Portal

## Vision
Transform the network portal from a monitoring dashboard into an **intelligent network assistant** that can:

1. **Answer questions** about your network
   - "Why is server CPU high?"
   - "Which devices are offline?"
   - "How many WiFi clients are connected?"

2. **Take actions** on your behalf
   - Restart services
   - Change WiFi channels
   - Reboot devices
   - Optimize configurations

3. **Provide insights** automatically
   - "High CPU on server X is due to backup job"
   - "WiFi AP in living room needs channel change due to interference"
   - "Switch port 12 has been flapping for 2 hours"

## Architecture

```
User Query
    ↓
Google Gemini Agent
    ↓
MCP Servers (Tools)
    ├── Network Query MCP (read-only queries)
    ├── Device Control MCP (actions: restart, reboot)
    ├── Analytics MCP (insights, trends)
    └── Configuration MCP (change settings)
    ↓
Network Devices (servers, WiFi, switches)
```

## MCP Servers to Create

### 1. Network Query MCP Server
**Read-only queries about current state**
- `get_server_stats(server_name)` - Get CPU/RAM/disk for a server
- `get_all_servers()` - List all servers and their status
- `get_wifi_clients(ap_name)` - Get connected clients
- `get_offline_devices()` - Find all offline devices
- `get_high_usage_devices()` - Find devices over threshold
- `search_devices(query)` - Find devices by name/IP

### 2. Device Control MCP Server
**Actions on devices**
- `restart_service(server, service_name)` - Restart a service
- `reboot_device(device_name)` - Reboot server/AP/switch
- `change_wifi_channel(ap_name, channel)` - Change WiFi channel
- `enable_port(switch, port)` - Enable switch port
- `disable_port(switch, port)` - Disable switch port

### 3. Analytics MCP Server
**Historical analysis and insights**
- `get_cpu_trend(server, hours)` - CPU usage over time
- `find_anomalies()` - Detect unusual patterns
- `compare_devices()` - Compare performance
- `get_bandwidth_usage(hours)` - Network traffic analysis

### 4. Configuration MCP Server
**View and modify configurations**
- `get_config(device)` - View device config
- `update_alert_threshold(metric, value)` - Change thresholds
- `add_device(type, config)` - Add new device to monitor
- `remove_device(name)` - Remove device

## Integration Points

1. **Add Agent UI to Dashboard**
   - Chat interface at bottom/side of dashboard
   - Voice input option
   - Quick action buttons

2. **Real-time Agent Updates**
   - Agent can trigger dashboard updates
   - Show agent actions in activity log
   - Highlight affected devices

3. **Proactive Alerts**
   - Agent monitors for issues
   - Sends natural language alerts
   - Suggests fixes automatically

## Example Interactions

**User:** "Why is my main server's CPU at 95%?"

**Agent:** "Analyzing main server... The high CPU usage (95%) is caused by:
1. Backup process (backup.sh) - 45% CPU
2. Docker container 'web-app' - 30% CPU
3. System processes - 20% CPU

The backup job started 15 minutes ago and should complete in ~10 minutes. This is normal behavior."

---

**User:** "Show me all devices that are offline"

**Agent:** "Found 2 offline devices:
1. WiFi AP 'Guest Network' (192.168.1.15) - Offline for 2 hours
2. Switch 'Basement Switch' (192.168.1.25) - Offline for 15 minutes

Would you like me to attempt to reconnect or check their status?"

---

**User:** "Restart nginx on web server"

**Agent:** "I'll restart the nginx service on 'Web Server' (192.168.1.100)...

✓ Connected via SSH
✓ Stopping nginx... Done
✓ Starting nginx... Done
✓ Service is healthy

Nginx has been successfully restarted. The web server is responding normally."

## Implementation Steps

1. ✅ Create MCP server modules
2. ✅ Integrate Google Gemini agent
3. ✅ Add chat UI to dashboard
4. ✅ Connect MCP servers to monitoring backend
5. ✅ Add agent-triggered actions
6. ✅ Implement proactive monitoring

## Benefits

✅ **Hands-free management** - Ask questions instead of clicking
✅ **Faster troubleshooting** - Agent analyzes and explains issues
✅ **Automation** - Common tasks done with natural language
✅ **Learning** - Agent teaches you about your network
✅ **Proactive** - Agent alerts you before problems occur

Ready to implement this?
