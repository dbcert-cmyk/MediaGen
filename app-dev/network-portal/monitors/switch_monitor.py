"""
Network Switch Monitoring Module
Monitors port status, traffic, and VLANs
Uses SNMP for managed switches
"""

from datetime import datetime
import random


class SwitchMonitor:
    """Monitor network switches"""

    def __init__(self, switch_config):
        """
        Initialize switch monitor

        Args:
            switch_config: List of switch configurations from config.yaml
        """
        self.switches = switch_config

    def get_snmp_stats(self, switch_config):
        """Get stats from SNMP-enabled switch"""
        try:
            host = switch_config['host']
            community = switch_config.get('community', 'public')
            port_count = switch_config.get('port_count', 24)

            # For now, return mock data with realistic port statuses
            # TODO: Implement actual SNMP queries

            ports = []
            for i in range(1, port_count + 1):
                # Simulate some ports up, some down
                is_up = random.random() > 0.2  # 80% of ports up

                ports.append({
                    'port': i,
                    'status': 'up' if is_up else 'down',
                    'speed': '1000 Mbps' if is_up else 'N/A',
                    'duplex': 'full' if is_up else 'N/A',
                    'vlan': random.choice([1, 10, 20, 30]) if is_up else None,
                    'rx_bytes': f"{random.randint(100, 9999)} MB" if is_up else '0 MB',
                    'tx_bytes': f"{random.randint(100, 9999)} MB" if is_up else '0 MB',
                })

            return {
                'status': 'online',
                'model': 'Generic Managed Switch',
                'ports_total': port_count,
                'ports_up': sum(1 for p in ports if p['status'] == 'up'),
                'ports_down': sum(1 for p in ports if p['status'] == 'down'),
                'ports': ports,
                'uptime': '15 days, 8 hours',
                'temperature': f"{random.randint(35, 50)}°C",
                'timestamp': datetime.now().isoformat()
            }

        except Exception as e:
            print(f"Error getting SNMP stats from {switch_config.get('name')}: {e}")
            return {
                'status': 'offline',
                'error': str(e),
                'timestamp': datetime.now().isoformat()
            }

    def get_switch_stats(self, switch_config):
        """Get stats for a single switch"""
        switch_type = switch_config.get('type', 'snmp')

        if switch_type == 'snmp':
            stats = self.get_snmp_stats(switch_config)
        else:
            stats = {'status': 'error', 'error': f'Unknown switch type: {switch_type}'}

        # Add switch info
        stats['name'] = switch_config.get('name', 'Unknown')
        stats['host'] = switch_config.get('host', 'Unknown')
        stats['type'] = switch_type

        return stats

    def get_all_stats(self):
        """Get stats for all configured switches"""
        all_stats = []

        for switch in self.switches:
            if not switch.get('enabled', True):
                continue

            stats = self.get_switch_stats(switch)
            all_stats.append(stats)

        return all_stats
