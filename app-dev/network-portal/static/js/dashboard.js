/**
 * Network Management Portal Dashboard
 * Handles real-time updates via WebSocket
 */

class NetworkDashboard {
    constructor() {
        this.socket = null;
        this.init();
    }

    init() {
        // Initialize WebSocket
        this.initWebSocket();

        // Set up event listeners
        this.setupEventListeners();

        // Update connection status
        this.updateConnectionStatus('connecting', 'Connecting...');
    }

    initWebSocket() {
        this.socket = io();

        this.socket.on('connect', () => {
            console.log('Connected to server');
            this.updateConnectionStatus('connected', 'Connected');
            // Request initial data
            this.socket.emit('request_update');
        });

        this.socket.on('disconnect', () => {
            console.log('Disconnected from server');
            this.updateConnectionStatus('error', 'Disconnected');
        });

        this.socket.on('connection_response', (data) => {
            console.log('Connection response:', data);
        });

        // Listen for server updates
        this.socket.on('server_update', (data) => {
            this.updateServers(data);
        });

        // Listen for WiFi updates
        this.socket.on('wifi_update', (data) => {
            this.updateWiFi(data);
        });

        // Listen for switch updates
        this.socket.on('switch_update', (data) => {
            this.updateSwitches(data);
        });

        // Listen for alerts
        this.socket.on('alerts', (alerts) => {
            this.showAlerts(alerts);
        });
    }

    setupEventListeners() {
        // Refresh button
        document.getElementById('refreshBtn').addEventListener('click', () => {
            this.socket.emit('request_update');
        });
    }

    updateConnectionStatus(status, text) {
        const statusDot = document.querySelector('.status-dot');
        const statusText = document.querySelector('.status-text');

        statusDot.className = `status-dot ${status}`;
        statusText.textContent = text;
    }

    updateServers(servers) {
        const grid = document.getElementById('serversGrid');
        grid.innerHTML = '';

        if (servers.length === 0) {
            grid.innerHTML = '<div class="loading">No servers configured</div>';
            return;
        }

        servers.forEach(server => {
            const card = this.createServerCard(server);
            grid.appendChild(card);
        });
    }

    createServerCard(server) {
        const card = document.createElement('div');
        card.className = `device-card ${server.status === 'offline' ? 'offline' : ''}`;

        const statusClass = server.status === 'online' ? 'online' : 'offline';
        const cpuClass = server.cpu > 80 ? 'high' : server.cpu > 60 ? 'medium' : 'low';
        const memClass = server.memory > 85 ? 'high' : server.memory > 70 ? 'medium' : 'low';
        const diskClass = server.disk > 90 ? 'high' : server.disk > 75 ? 'medium' : 'low';

        card.innerHTML = `
            <div class="device-header">
                <div class="device-name">${server.name}</div>
                <div class="device-status ${statusClass}">${server.status.toUpperCase()}</div>
            </div>
            <div class="device-info">
                <p style="color: #666; font-size: 0.9rem; margin-bottom: 10px;">
                    ${server.host} • ${server.type}
                </p>
            </div>
            ${server.status === 'online' ? `
                <div class="stats-grid">
                    <div class="stat-item">
                        <div class="stat-label">CPU Usage</div>
                        <div class="stat-value ${cpuClass}">${server.cpu}%</div>
                        <div class="progress-bar">
                            <div class="progress-fill ${cpuClass}" style="width: ${server.cpu}%"></div>
                        </div>
                    </div>
                    <div class="stat-item">
                        <div class="stat-label">Memory</div>
                        <div class="stat-value ${memClass}">${server.memory}%</div>
                        <div class="progress-bar">
                            <div class="progress-fill ${memClass}" style="width: ${server.memory}%"></div>
                        </div>
                    </div>
                    <div class="stat-item">
                        <div class="stat-label">Disk Usage</div>
                        <div class="stat-value ${diskClass}">${server.disk}%</div>
                        <div class="progress-bar">
                            <div class="progress-fill ${diskClass}" style="width: ${server.disk}%"></div>
                        </div>
                    </div>
                    <div class="stat-item">
                        <div class="stat-label">Uptime</div>
                        <div class="stat-value" style="font-size: 0.95rem;">${server.uptime}</div>
                    </div>
                    <div class="stat-item">
                        <div class="stat-label">Processes</div>
                        <div class="stat-value">${server.processes || 0}</div>
                    </div>
                    <div class="stat-item">
                        <div class="stat-label">Load Average</div>
                        <div class="stat-value">${server.load_avg || '0.0'}</div>
                    </div>
                </div>
            ` : `
                <div style="padding: 20px; text-align: center; color: #f44336;">
                    ⚠️ Server is offline or unreachable
                    ${server.error ? `<br><small>${server.error}</small>` : ''}
                </div>
            `}
        `;

        return card;
    }

    updateWiFi(aps) {
        const grid = document.getElementById('wifiGrid');
        grid.innerHTML = '';

        if (aps.length === 0) {
            grid.innerHTML = '<div class="loading">No WiFi APs configured</div>';
            return;
        }

        aps.forEach(ap => {
            const card = this.createWiFiCard(ap);
            grid.appendChild(card);
        });
    }

    createWiFiCard(ap) {
        const card = document.createElement('div');
        card.className = `device-card ${ap.status === 'offline' ? 'offline' : ''}`;

        const statusClass = ap.status === 'online' ? 'online' : 'offline';

        card.innerHTML = `
            <div class="device-header">
                <div class="device-name">${ap.name}</div>
                <div class="device-status ${statusClass}">${ap.status.toUpperCase()}</div>
            </div>
            <div class="device-info">
                <p style="color: #666; font-size: 0.9rem; margin-bottom: 10px;">
                    ${ap.host} • ${ap.type}
                </p>
            </div>
            ${ap.status === 'online' ? `
                <div class="stats-grid">
                    <div class="stat-item">
                        <div class="stat-label">Total Clients</div>
                        <div class="stat-value">${ap.total_clients || 0}</div>
                    </div>
                    <div class="stat-item">
                        <div class="stat-label">2.4 GHz Clients</div>
                        <div class="stat-value">${ap.clients_2ghz || 0}</div>
                    </div>
                    <div class="stat-item">
                        <div class="stat-label">5 GHz Clients</div>
                        <div class="stat-value">${ap.clients_5ghz || 0}</div>
                    </div>
                    <div class="stat-item">
                        <div class="stat-label">Signal Strength</div>
                        <div class="stat-value">${ap.signal_strength || 'N/A'} dBm</div>
                    </div>
                    <div class="stat-item">
                        <div class="stat-label">Channel 2.4G</div>
                        <div class="stat-value">${ap.channel_2ghz || 'N/A'}</div>
                    </div>
                    <div class="stat-item">
                        <div class="stat-label">Channel 5G</div>
                        <div class="stat-value">${ap.channel_5ghz || 'N/A'}</div>
                    </div>
                </div>
            ` : `
                <div style="padding: 20px; text-align: center; color: #f44336;">
                    ⚠️ Access Point is offline or unreachable
                </div>
            `}
        `;

        return card;
    }

    updateSwitches(switches) {
        const grid = document.getElementById('switchesGrid');
        grid.innerHTML = '';

        if (switches.length === 0) {
            grid.innerHTML = '<div class="loading">No switches configured</div>';
            return;
        }

        switches.forEach(sw => {
            const card = this.createSwitchCard(sw);
            grid.appendChild(card);
        });
    }

    createSwitchCard(sw) {
        const card = document.createElement('div');
        card.className = `device-card ${sw.status === 'offline' ? 'offline' : ''}`;

        const statusClass = sw.status === 'online' ? 'online' : 'offline';

        card.innerHTML = `
            <div class="device-header">
                <div class="device-name">${sw.name}</div>
                <div class="device-status ${statusClass}">${sw.status.toUpperCase()}</div>
            </div>
            <div class="device-info">
                <p style="color: #666; font-size: 0.9rem; margin-bottom: 10px;">
                    ${sw.host} • ${sw.type}
                </p>
            </div>
            ${sw.status === 'online' ? `
                <div class="stats-grid">
                    <div class="stat-item">
                        <div class="stat-label">Total Ports</div>
                        <div class="stat-value">${sw.ports_total || 0}</div>
                    </div>
                    <div class="stat-item">
                        <div class="stat-label">Ports Up</div>
                        <div class="stat-value low">${sw.ports_up || 0}</div>
                    </div>
                    <div class="stat-item">
                        <div class="stat-label">Ports Down</div>
                        <div class="stat-value">${sw.ports_down || 0}</div>
                    </div>
                    <div class="stat-item">
                        <div class="stat-label">Temperature</div>
                        <div class="stat-value">${sw.temperature || 'N/A'}</div>
                    </div>
                </div>
                ${sw.ports && sw.ports.length > 0 ? `
                    <details style="margin-top: 15px;">
                        <summary style="cursor: pointer; font-weight: 600; margin-bottom: 10px;">
                            Port Details (${sw.ports_up}/${sw.ports_total} up)
                        </summary>
                        <div style="max-height: 300px; overflow-y: auto;">
                            <table class="port-table">
                                <thead>
                                    <tr>
                                        <th>Port</th>
                                        <th>Status</th>
                                        <th>Speed</th>
                                        <th>VLAN</th>
                                    </tr>
                                </thead>
                                <tbody>
                                    ${sw.ports.map(port => `
                                        <tr>
                                            <td>${port.port}</td>
                                            <td>
                                                <span class="port-status ${port.status}"></span>
                                                ${port.status}
                                            </td>
                                            <td>${port.speed}</td>
                                            <td>${port.vlan || 'N/A'}</td>
                                        </tr>
                                    `).join('')}
                                </tbody>
                            </table>
                        </div>
                    </details>
                ` : ''}
            ` : `
                <div style="padding: 20px; text-align: center; color: #f44336;">
                    ⚠️ Switch is offline or unreachable
                </div>
            `}
        `;

        return card;
    }

    showAlerts(alerts) {
        const banner = document.getElementById('alertBanner');

        if (alerts.length === 0) {
            banner.style.display = 'none';
            return;
        }

        const critical = alerts.some(a => a.type === 'critical');
        banner.className = `alert-banner ${critical ? 'critical' : ''}`;

        banner.innerHTML = alerts.map(alert => `
            <div style="margin-bottom: 5px;">
                <strong>${alert.device}:</strong> ${alert.message}
            </div>
        `).join('');

        banner.style.display = 'block';
    }
}

// Initialize dashboard on page load
let dashboard;
document.addEventListener('DOMContentLoaded', () => {
    dashboard = new NetworkDashboard();
});
