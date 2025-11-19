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
        scan_type: Type of scan ("discovery", "port_scan", or "smart")

    Returns:
        Dict with scan results
    """
    try:
        if scan_type == "discovery":
            return await _discovery_scan(subnet)
        elif scan_type == "port_scan":
            return await _port_scan(subnet)
        elif scan_type == "smart":
            return await _smart_scan(subnet)
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

async def _smart_scan(subnet: str) -> Dict:
    """
    Smart scan with MAC detection, hostname resolution, and device type identification
    """
    try:
        # Use nmap with -sn (ping scan) and get hostnames and MACs
        # Note: MAC detection requires the scan to be run with appropriate permissions
        cmd = ["nmap", "-sn", "-R", subnet]
        result = subprocess.run(
            cmd,
            capture_output=True,
            text=True,
            timeout=120
        )

        hosts = []
        current_host = None

        for line in result.stdout.split('\n'):
            line = line.strip()

            # Check for host line: "Nmap scan report for hostname (ip)" or "Nmap scan report for ip"
            if line.startswith("Nmap scan report for"):
                if current_host:
                    hosts.append(current_host)

                # Extract hostname and IP
                hostname = None
                ip = None

                if '(' in line and ')' in line:
                    # Format: "Nmap scan report for hostname (192.168.1.1)"
                    parts = line.replace("Nmap scan report for ", "").split('(')
                    hostname = parts[0].strip()
                    ip = parts[1].replace(')', '').strip()
                else:
                    # Format: "Nmap scan report for 192.168.1.1"
                    ip = line.replace("Nmap scan report for ", "").strip()

                current_host = {
                    "ip": ip,
                    "hostname": hostname if hostname and hostname != ip else None,
                    "status": "up",
                    "mac": None,
                    "vendor": None,
                    "device_type": "unknown"
                }

            # Check for MAC address line: "MAC Address: AA:BB:CC:DD:EE:FF (Vendor Name)"
            elif line.startswith("MAC Address:") and current_host:
                mac_match = re.search(r"MAC Address: ([0-9A-F:]+)", line, re.IGNORECASE)
                if mac_match:
                    current_host["mac"] = mac_match.group(1)

                # Extract vendor from parentheses
                vendor_match = re.search(r"\(([^)]+)\)", line)
                if vendor_match:
                    current_host["vendor"] = vendor_match.group(1)

        # Don't forget the last host
        if current_host:
            hosts.append(current_host)

        # Now do device type detection for each host
        for host in hosts:
            host["device_type"] = await _detect_device_type(host["ip"], host.get("vendor"))

        return {
            "subnet": subnet,
            "scan_type": "smart",
            "hosts_found": len(hosts),
            "hosts": hosts
        }

    except FileNotFoundError:
        return {"error": "nmap not installed"}
    except Exception as e:
        logger.error(f"Smart scan error: {e}")
        return {"error": str(e)}

async def _detect_device_type(ip: str, vendor: str = None) -> str:
    """
    Detect device type based on open ports and vendor information
    """
    try:
        # Scan common ports to identify device type
        cmd = ["nmap", "-p", "22,23,80,443,161,3389,8080,8443,9100",
               "--open", "-T4", ip]
        result = subprocess.run(
            cmd,
            capture_output=True,
            text=True,
            timeout=30
        )

        # Parse open ports
        open_ports = []
        for line in result.stdout.split('\n'):
            if '/tcp' in line and 'open' in line:
                port_match = re.match(r'(\d+)/tcp', line.strip())
                if port_match:
                    open_ports.append(int(port_match.group(1)))

        # Vendor-based detection
        if vendor:
            vendor_lower = vendor.lower()
            if 'ubiquiti' in vendor_lower or 'ubnt' in vendor_lower:
                return 'ap'
            if 'cisco' in vendor_lower and 161 in open_ports:
                return 'switch'
            if 'netgear' in vendor_lower and 80 in open_ports:
                return 'switch'
            if 'tp-link' in vendor_lower:
                return 'ap'
            if 'hp' in vendor_lower or 'hewlett' in vendor_lower:
                if 9100 in open_ports:
                    return 'printer'

        # Port-based detection
        if 3389 in open_ports:  # RDP
            return 'workstation'

        if 22 in open_ports and (80 in open_ports or 443 in open_ports):
            return 'server'

        if 161 in open_ports and (not 80 in open_ports):  # SNMP only
            return 'switch'

        if 9100 in open_ports:  # Printer port
            return 'printer'

        # Default based on any services
        if len(open_ports) > 0:
            if 80 in open_ports or 443 in open_ports:
                return 'server'
            if 22 in open_ports:
                return 'server'

        return 'unknown'

    except Exception as e:
        logger.error(f"Device type detection error for {ip}: {e}")
        return 'unknown'

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
