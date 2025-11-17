/**
 * Network Management Portal Dashboard
 * Handles real-time updates via WebSocket
 */

class NetworkDashboard {
    constructor() {
        this.socket = null;
        this.agentAvailable = false;
        this.chatOpen = false;
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

        // Listen for agent status
        this.socket.on('agent_status', (data) => {
            this.agentAvailable = data.available;
            this.updateAgentStatus(data.available);
        });

        // Listen for agent responses
        this.socket.on('agent_response', (data) => {
            this.displayAgentResponse(data);
        });

        // Listen for agent progress
        this.socket.on('agent_progress', (data) => {
            this.displayAgentProgress(data);
        });

        // Listen for agent errors
        this.socket.on('agent_error', (data) => {
            this.displayAgentError(data.error);
        });
    }

    setupEventListeners() {
        // Refresh button
        document.getElementById('refreshBtn').addEventListener('click', () => {
            this.socket.emit('request_update');
        });

        // Chat toggle button
        document.getElementById('chatToggleBtn').addEventListener('click', () => {
            this.toggleChat();
        });

        // Close chat button
        document.getElementById('closeChatBtn').addEventListener('click', () => {
            this.toggleChat();
        });

        // Send chat message
        document.getElementById('sendChatBtn').addEventListener('click', () => {
            this.sendChatMessage();
        });

        // Enter key to send message
        document.getElementById('chatInput').addEventListener('keypress', (e) => {
            if (e.key === 'Enter') {
                this.sendChatMessage();
            }
        });

        // Check agent status on connect
        this.socket.on('connect', () => {
            this.socket.emit('get_agent_status');
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

    // Agent Chat Methods

    toggleChat() {
        this.chatOpen = !this.chatOpen;
        const chatPanel = document.getElementById('agentChat');
        const toggleBtn = document.getElementById('chatToggleBtn');

        if (this.chatOpen) {
            chatPanel.classList.add('open');
            toggleBtn.classList.add('hidden');
        } else {
            chatPanel.classList.remove('open');
            toggleBtn.classList.remove('hidden');
        }
    }

    updateAgentStatus(available) {
        const statusDot = document.querySelector('.agent-status-dot');
        const statusText = document.querySelector('.agent-status-text');
        const toggleBtn = document.getElementById('chatToggleBtn');

        if (available) {
            statusDot.className = 'agent-status-dot online';
            statusText.textContent = 'AI Assistant Ready';
            toggleBtn.style.display = 'flex';
        } else {
            statusDot.className = 'agent-status-dot offline';
            statusText.textContent = 'AI Assistant Unavailable';
            toggleBtn.style.display = 'none';
        }
    }

    sendChatMessage() {
        const input = document.getElementById('chatInput');
        const query = input.value.trim();

        if (!query) return;

        // Display user message
        this.addChatMessage('user', query);

        // Clear input
        input.value = '';

        // Show typing indicator
        this.showTypingIndicator();

        // Send to agent
        this.socket.emit('agent_query', { query });
    }

    addChatMessage(role, content) {
        const messagesContainer = document.getElementById('chatMessages');
        const messageDiv = document.createElement('div');
        messageDiv.className = `agent-message ${role}-message`;

        if (role === 'agent') {
            // Type out agent messages with animation
            const contentP = document.createElement('p');
            messageDiv.appendChild(contentP);
            messagesContainer.appendChild(messageDiv);
            this.typeText(contentP, content);
        } else {
            messageDiv.innerHTML = `<p>${this.escapeHtml(content)}</p>`;
            messagesContainer.appendChild(messageDiv);
        }

        // Scroll to bottom
        messagesContainer.scrollTop = messagesContainer.scrollHeight;
    }

    typeText(element, text, speed = 15) {
        let index = 0;
        const typeChar = () => {
            if (index < text.length) {
                element.textContent += text.charAt(index);
                index++;
                setTimeout(typeChar, speed);
            }
        };
        typeChar();
    }

    escapeHtml(text) {
        const div = document.createElement('div');
        div.textContent = text;
        return div.innerHTML;
    }

    showTypingIndicator() {
        const messagesContainer = document.getElementById('chatMessages');
        const typingDiv = document.createElement('div');
        typingDiv.className = 'agent-message typing-indicator';
        typingDiv.id = 'typingIndicator';
        typingDiv.innerHTML = '<p><span></span><span></span><span></span></p>';
        messagesContainer.appendChild(typingDiv);
        messagesContainer.scrollTop = messagesContainer.scrollHeight;
    }

    hideTypingIndicator() {
        const indicator = document.getElementById('typingIndicator');
        if (indicator) {
            indicator.remove();
        }
    }

    displayAgentProgress(data) {
        console.log('[AGENT PROGRESS]', data);
        // Could add visual progress indicators here
        if (data.type === 'tool_call') {
            console.log(`Using tool: ${data.tool} from ${data.server} server`);
        }
    }

    displayAgentResponse(data) {
        this.hideTypingIndicator();

        const response = data.response || 'No response';
        this.addChatMessage('agent', response);

        // Log workflow steps
        if (data.workflow_steps && data.workflow_steps.length > 0) {
            console.log(`[AGENT] Completed ${data.total_steps} steps:`, data.workflow_steps);
        }
    }

    displayAgentError(error) {
        this.hideTypingIndicator();

        const messagesContainer = document.getElementById('chatMessages');
        const errorDiv = document.createElement('div');
        errorDiv.className = 'agent-message error-message';
        errorDiv.innerHTML = `<p>⚠️ ${this.escapeHtml(error)}</p>`;
        messagesContainer.appendChild(errorDiv);
        messagesContainer.scrollTop = messagesContainer.scrollHeight;
    }
}

// Initialize dashboard on page load
let dashboard;
document.addEventListener('DOMContentLoaded', () => {
    dashboard = new NetworkDashboard();
});
