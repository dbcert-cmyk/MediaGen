"""
Network Query MCP Server
Provides read-only queries about network devices
"""

from mcp.server import Server
from mcp.types import Tool, TextContent
import json


# Create MCP server instance
app = Server("network-query")

# Reference to monitors (will be injected)
_monitors = None


def set_monitors(server_monitor, wifi_monitor, switch_monitor):
    """Inject monitor instances"""
    global _monitors
    _monitors = {
        'server': server_monitor,
        'wifi': wifi_monitor,
        'switch': switch_monitor
    }


@app.list_tools()
async def list_tools() -> list[Tool]:
    """List available network query tools"""
    return [
        Tool(
            name="get_server_stats",
            description="Get current CPU, RAM, disk, uptime stats for a specific server by name",
            inputSchema={
                "type": "object",
                "properties": {
                    "server_name": {
                        "type": "string",
                        "description": "Name of the server (e.g., 'Main Server', 'NAS')"
                    }
                },
                "required": ["server_name"]
            }
        ),
        Tool(
            name="get_all_servers",
            description="Get status and stats for all configured servers",
            inputSchema={
                "type": "object",
                "properties": {}
            }
        ),
        Tool(
            name="get_wifi_clients",
            description="Get count of connected WiFi clients for a specific access point",
            inputSchema={
                "type": "object",
                "properties": {
                    "ap_name": {
                        "type": "string",
                        "description": "Name of the WiFi access point"
                    }
                },
                "required": ["ap_name"]
            }
        ),
        Tool(
            name="get_all_wifi_aps",
            description="Get status and client information for all WiFi access points",
            inputSchema={
                "type": "object",
                "properties": {}
            }
        ),
        Tool(
            name="get_all_switches",
            description="Get status and port information for all network switches",
            inputSchema={
                "type": "object",
                "properties": {}
            }
        ),
        Tool(
            name="get_offline_devices",
            description="Find all devices (servers, WiFi APs, switches) that are currently offline",
            inputSchema={
                "type": "object",
                "properties": {}
            }
        ),
        Tool(
            name="get_high_usage_servers",
            description="Find servers with CPU or memory usage above specified threshold",
            inputSchema={
                "type": "object",
                "properties": {
                    "cpu_threshold": {
                        "type": "number",
                        "description": "CPU usage threshold percentage (default: 80)",
                        "default": 80
                    },
                    "memory_threshold": {
                        "type": "number",
                        "description": "Memory usage threshold percentage (default": 85)",
                        "default": 85
                    }
                }
            }
        ),
        Tool(
            name="search_devices",
            description="Search for devices by name or IP address across all device types",
            inputSchema={
                "type": "object",
                "properties": {
                    "query": {
                        "type": "string",
                        "description": "Search query (name or IP)"
                    }
                },
                "required": ["query"]
            }
        )
    ]


@app.call_tool()
async def call_tool(name: str, arguments: dict) -> list[TextContent]:
    """Handle tool calls"""
    if not _monitors:
        return [TextContent(type="text", text=json.dumps({"error": "Monitors not initialized"}))]

    try:
        if name == "get_server_stats":
            return await get_server_stats(arguments)
        elif name == "get_all_servers":
            return await get_all_servers(arguments)
        elif name == "get_wifi_clients":
            return await get_wifi_clients(arguments)
        elif name == "get_all_wifi_aps":
            return await get_all_wifi_aps(arguments)
        elif name == "get_all_switches":
            return await get_all_switches(arguments)
        elif name == "get_offline_devices":
            return await get_offline_devices(arguments)
        elif name == "get_high_usage_servers":
            return await get_high_usage_servers(arguments)
        elif name == "search_devices":
            return await search_devices(arguments)
        else:
            return [TextContent(type="text", text=json.dumps({"error": f"Unknown tool: {name}"}))]

    except Exception as e:
        return [TextContent(type="text", text=json.dumps({"error": str(e)}))]


async def get_server_stats(args):
    """Get stats for a specific server"""
    server_name = args.get('server_name', '')
    all_servers = _monitors['server'].get_all_stats()

    # Find matching server
    server = next((s for s in all_servers if s['name'].lower() == server_name.lower()), None)

    if not server:
        available = [s['name'] for s in all_servers]
        return [TextContent(
            type="text",
            text=json.dumps({
                "error": f"Server '{server_name}' not found",
                "available_servers": available
            })
        )]

    return [TextContent(type="text", text=json.dumps(server, indent=2))]


async def get_all_servers(args):
    """Get stats for all servers"""
    servers = _monitors['server'].get_all_stats()
    return [TextContent(
        type="text",
        text=json.dumps({
            "total_servers": len(servers),
            "servers": servers
        }, indent=2)
    )]


async def get_wifi_clients(args):
    """Get WiFi clients for a specific AP"""
    ap_name = args.get('ap_name', '')
    all_aps = _monitors['wifi'].get_all_stats()

    # Find matching AP
    ap = next((a for a in all_aps if a['name'].lower() == ap_name.lower()), None)

    if not ap:
        available = [a['name'] for a in all_aps]
        return [TextContent(
            type="text",
            text=json.dumps({
                "error": f"WiFi AP '{ap_name}' not found",
                "available_aps": available
            })
        )]

    return [TextContent(type="text", text=json.dumps(ap, indent=2))]


async def get_all_wifi_aps(args):
    """Get stats for all WiFi APs"""
    aps = _monitors['wifi'].get_all_stats()
    return [TextContent(
        type="text",
        text=json.dumps({
            "total_aps": len(aps),
            "access_points": aps
        }, indent=2)
    )]


async def get_all_switches(args):
    """Get stats for all switches"""
    switches = _monitors['switch'].get_all_stats()
    return [TextContent(
        type="text",
        text=json.dumps({
            "total_switches": len(switches),
            "switches": switches
        }, indent=2)
    )]


async def get_offline_devices(args):
    """Find all offline devices"""
    offline = {
        "servers": [],
        "wifi_aps": [],
        "switches": []
    }

    # Check servers
    servers = _monitors['server'].get_all_stats()
    offline['servers'] = [s for s in servers if s.get('status') == 'offline']

    # Check WiFi APs
    aps = _monitors['wifi'].get_all_stats()
    offline['wifi_aps'] = [a for a in aps if a.get('status') == 'offline']

    # Check switches
    switches = _monitors['switch'].get_all_stats()
    offline['switches'] = [s for s in switches if s.get('status') == 'offline']

    total_offline = len(offline['servers']) + len(offline['wifi_aps']) + len(offline['switches'])

    return [TextContent(
        type="text",
        text=json.dumps({
            "total_offline": total_offline,
            "offline_devices": offline
        }, indent=2)
    )]


async def get_high_usage_servers(args):
    """Find servers with high resource usage"""
    cpu_threshold = args.get('cpu_threshold', 80)
    memory_threshold = args.get('memory_threshold', 85)

    servers = _monitors['server'].get_all_stats()
    high_usage = []

    for server in servers:
        if server.get('status') != 'online':
            continue

        issues = []
        if server.get('cpu', 0) > cpu_threshold:
            issues.append(f"CPU: {server['cpu']}%")
        if server.get('memory', 0) > memory_threshold:
            issues.append(f"Memory: {server['memory']}%")

        if issues:
            high_usage.append({
                "name": server['name'],
                "host": server['host'],
                "issues": issues,
                "cpu": server.get('cpu'),
                "memory": server.get('memory'),
                "disk": server.get('disk')
            })

    return [TextContent(
        type="text",
        text=json.dumps({
            "servers_with_high_usage": len(high_usage),
            "thresholds": {
                "cpu": cpu_threshold,
                "memory": memory_threshold
            },
            "servers": high_usage
        }, indent=2)
    )]


async def search_devices(args):
    """Search for devices by name or IP"""
    query = args.get('query', '').lower()
    results = {
        "servers": [],
        "wifi_aps": [],
        "switches": []
    }

    # Search servers
    servers = _monitors['server'].get_all_stats()
    results['servers'] = [
        s for s in servers
        if query in s.get('name', '').lower() or query in s.get('host', '').lower()
    ]

    # Search WiFi APs
    aps = _monitors['wifi'].get_all_stats()
    results['wifi_aps'] = [
        a for a in aps
        if query in a.get('name', '').lower() or query in a.get('host', '').lower()
    ]

    # Search switches
    switches = _monitors['switch'].get_all_stats()
    results['switches'] = [
        s for s in switches
        if query in s.get('name', '').lower() or query in s.get('host', '').lower()
    ]

    total_results = len(results['servers']) + len(results['wifi_aps']) + len(results['switches'])

    return [TextContent(
        type="text",
        text=json.dumps({
            "query": query,
            "total_results": total_results,
            "results": results
        }, indent=2)
    )]
