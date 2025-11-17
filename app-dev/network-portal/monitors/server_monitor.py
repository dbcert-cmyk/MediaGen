"""
Server Monitoring Module
Monitors CPU, RAM, disk, uptime, and services
Supports both local and remote (SSH) servers
"""

import psutil
import paramiko
import time
from datetime import datetime, timedelta


class ServerMonitor:
    """Monitor servers (local and remote via SSH)"""

    def __init__(self, servers_config):
        """
        Initialize server monitor

        Args:
            servers_config: List of server configurations from config.yaml
        """
        self.servers = servers_config
        self.ssh_connections = {}

    def get_local_stats(self):
        """Get stats from the local server"""
        try:
            # CPU usage
            cpu_percent = psutil.cpu_percent(interval=1)

            # Memory usage
            memory = psutil.virtual_memory()
            memory_percent = memory.percent

            # Disk usage
            disk = psutil.disk_usage('/')
            disk_percent = disk.percent

            # System uptime
            boot_time = datetime.fromtimestamp(psutil.boot_time())
            uptime = datetime.now() - boot_time
            uptime_str = str(uptime).split('.')[0]  # Remove microseconds

            # Network stats
            net_io = psutil.net_io_counters()
            bytes_sent = self._format_bytes(net_io.bytes_sent)
            bytes_recv = self._format_bytes(net_io.bytes_recv)

            # Running processes
            process_count = len(psutil.pids())

            # Load average (Linux only)
            try:
                load_avg = psutil.getloadavg()
                load_1min = round(load_avg[0], 2)
            except:
                load_1min = 0

            return {
                'status': 'online',
                'cpu': round(cpu_percent, 1),
                'memory': round(memory_percent, 1),
                'disk': round(disk_percent, 1),
                'uptime': uptime_str,
                'network_sent': bytes_sent,
                'network_recv': bytes_recv,
                'processes': process_count,
                'load_avg': load_1min,
                'timestamp': datetime.now().isoformat()
            }

        except Exception as e:
            print(f"Error getting local stats: {e}")
            return {
                'status': 'error',
                'error': str(e)
            }

    def get_remote_stats_ssh(self, server_config):
        """Get stats from remote server via SSH"""
        try:
            host = server_config['host']
            username = server_config.get('username')
            password = server_config.get('password')
            ssh_key = server_config.get('ssh_key')

            # Create SSH connection
            ssh = paramiko.SSHClient()
            ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())

            # Connect
            if ssh_key:
                ssh.connect(host, username=username, key_filename=ssh_key, timeout=5)
            else:
                ssh.connect(host, username=username, password=password, timeout=5)

            # Execute commands to get stats
            # CPU
            stdin, stdout, stderr = ssh.exec_command("top -bn1 | grep 'Cpu(s)' | sed 's/.*, *\\([0-9.]*\\)%* id.*/\\1/' | awk '{print 100 - $1}'")
            cpu = float(stdout.read().decode().strip())

            # Memory
            stdin, stdout, stderr = ssh.exec_command("free | grep Mem | awk '{print ($3/$2) * 100.0}'")
            memory = float(stdout.read().decode().strip())

            # Disk
            stdin, stdout, stderr = ssh.exec_command("df -h / | tail -1 | awk '{print $5}' | sed 's/%//'")
            disk = float(stdout.read().decode().strip())

            # Uptime
            stdin, stdout, stderr = ssh.exec_command("uptime -p")
            uptime = stdout.read().decode().strip()

            # Processes
            stdin, stdout, stderr = ssh.exec_command("ps aux | wc -l")
            processes = int(stdout.read().decode().strip())

            # Load average
            stdin, stdout, stderr = ssh.exec_command("uptime | awk -F'load average:' '{print $2}' | awk -F, '{print $1}'")
            load_avg = float(stdout.read().decode().strip())

            ssh.close()

            return {
                'status': 'online',
                'cpu': round(cpu, 1),
                'memory': round(memory, 1),
                'disk': round(disk, 1),
                'uptime': uptime,
                'processes': processes,
                'load_avg': round(load_avg, 2),
                'timestamp': datetime.now().isoformat()
            }

        except Exception as e:
            print(f"Error getting remote stats from {server_config.get('name')}: {e}")
            return {
                'status': 'offline',
                'error': str(e),
                'timestamp': datetime.now().isoformat()
            }

    def get_server_stats(self, server_config):
        """Get stats for a single server"""
        server_type = server_config.get('type', 'local')

        if server_type == 'local':
            stats = self.get_local_stats()
        elif server_type == 'ssh':
            stats = self.get_remote_stats_ssh(server_config)
        else:
            stats = {'status': 'error', 'error': f'Unknown server type: {server_type}'}

        # Add server info
        stats['name'] = server_config.get('name', 'Unknown')
        stats['host'] = server_config.get('host', 'Unknown')
        stats['type'] = server_type

        return stats

    def get_all_stats(self):
        """Get stats for all configured servers"""
        all_stats = []

        for server in self.servers:
            if not server.get('enabled', True):
                continue

            stats = self.get_server_stats(server)
            all_stats.append(stats)

        return all_stats

    def _format_bytes(self, bytes_value):
        """Format bytes to human-readable format"""
        for unit in ['B', 'KB', 'MB', 'GB', 'TB']:
            if bytes_value < 1024.0:
                return f"{bytes_value:.1f} {unit}"
            bytes_value /= 1024.0
        return f"{bytes_value:.1f} PB"
