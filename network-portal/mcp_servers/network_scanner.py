"""
MCP Server for Network Scanning
"""
import asyncio
import logging
from typing import Dict, List
import subprocess
import re

logger = logging.getLogger(__name__)

async def scan_network(subnet: str, scan_type: str = "discovery") -> Dict:
    """
    Scan a network subnet for devices

    Args:
        subnet: Network subnet in CIDR notation (e.g., "192.168.1.0/24")
        scan_type: Type of scan ("discovery" or "port_scan")

    Returns:
        Dict with scan results
    """
    try:
        if scan_type == "discovery":
            return await _discovery_scan(subnet)
        elif scan_type == "port_scan":
            return await _port_scan(subnet)
        else:
            return {"error": f"Unknown scan type: {scan_type}"}

    except Exception as e:
        logger.error(f"Scan error: {e}")
        return {"error": str(e)}

async def _discovery_scan(subnet: str) -> Dict:
    """
    Perform basic host discovery using ping sweep
    """
    hosts = []

    # Extract network address and CIDR
    match = re.match(r"(\d+\.\d+\.\d+)\.(\d+)/(\d+)", subnet)
    if not match:
        return {"error": "Invalid subnet format"}

    base_ip = match.group(1)
    cidr = int(match.group(3))

    # For /24 networks, scan all 254 hosts
    if cidr == 24:
        # Use fping for faster scanning
        try:
            cmd = ["fping", "-a", "-g", subnet, "-q"]
            result = subprocess.run(
                cmd,
                capture_output=True,
                text=True,
                timeout=30
            )

            # fping outputs alive hosts to stdout
            for line in result.stdout.strip().split('\n'):
                if line:
                    hosts.append({
                        "ip": line.strip(),
                        "status": "up",
                        "mac": None,  # Would need ARP for this
                        "vendor": None
                    })

        except FileNotFoundError:
            # fping not available, fall back to nmap or ping
            logger.warning("fping not found, using nmap")
            return await _nmap_discovery(subnet)
        except Exception as e:
            logger.error(f"Discovery scan error: {e}")
            return {"error": str(e)}

    else:
        # For other CIDR ranges, use nmap
        return await _nmap_discovery(subnet)

    return {
        "subnet": subnet,
        "scan_type": "discovery",
        "hosts_found": len(hosts),
        "hosts": hosts
    }

async def _nmap_discovery(subnet: str) -> Dict:
    """
    Use nmap for host discovery (requires nmap to be installed)
    """
    try:
        cmd = ["nmap", "-sn", subnet, "-oG", "-"]
        result = subprocess.run(
            cmd,
            capture_output=True,
            text=True,
            timeout=60
        )

        hosts = []
        for line in result.stdout.split('\n'):
            if "Host:" in line and "Status: Up" in line:
                # Extract IP address
                ip_match = re.search(r"Host: (\d+\.\d+\.\d+\.\d+)", line)
                if ip_match:
                    hosts.append({
                        "ip": ip_match.group(1),
                        "status": "up",
                        "mac": None,
                        "vendor": None
                    })

        return {
            "subnet": subnet,
            "scan_type": "discovery",
            "hosts_found": len(hosts),
            "hosts": hosts
        }

    except FileNotFoundError:
        return {"error": "nmap not installed"}
    except Exception as e:
        logger.error(f"Nmap discovery error: {e}")
        return {"error": str(e)}

async def _port_scan(subnet: str) -> Dict:
    """
    Perform port scanning on subnet (basic version)
    """
    try:
        cmd = ["nmap", "-p", "22,80,443,3389,8080", subnet, "-oG", "-"]
        result = subprocess.run(
            cmd,
            capture_output=True,
            text=True,
            timeout=120
        )

        hosts = []
        current_host = None

        for line in result.stdout.split('\n'):
            if "Host:" in line:
                ip_match = re.search(r"Host: (\d+\.\d+\.\d+\.\d+)", line)
                if ip_match:
                    current_host = {
                        "ip": ip_match.group(1),
                        "ports": []
                    }

                # Extract open ports
                ports_match = re.search(r"Ports: ([^)]+)", line)
                if ports_match and current_host:
                    ports_str = ports_match.group(1)
                    for port_info in ports_str.split(','):
                        if "open" in port_info:
                            port_num = port_info.split('/')[0].strip()
                            current_host["ports"].append(port_num)

                if current_host:
                    hosts.append(current_host)

        return {
            "subnet": subnet,
            "scan_type": "port_scan",
            "hosts_found": len(hosts),
            "hosts": hosts
        }

    except FileNotFoundError:
        return {"error": "nmap not installed"}
    except Exception as e:
        logger.error(f"Port scan error: {e}")
        return {"error": str(e)}

async def scan_single_host(host: str) -> Dict:
    """
    Detailed scan of a single host
    """
    try:
        cmd = ["nmap", "-A", "-T4", host]
        result = subprocess.run(
            cmd,
            capture_output=True,
            text=True,
            timeout=60
        )

        return {
            "host": host,
            "scan_output": result.stdout,
            "status": "completed"
        }

    except Exception as e:
        return {"error": str(e)}
