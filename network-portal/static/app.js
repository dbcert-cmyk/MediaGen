// Home Network Portal - Frontend JavaScript

// Global state
let devices = [];
let websocket = null;

// Initialize on page load
document.addEventListener('DOMContentLoaded', function() {
    console.log('Home Network Portal loaded');

    // Setup tab navigation
    setupTabs();

    // Load initial data
    refreshDashboard();
    loadDevices();
    checkSystemHealth();

    // Connect WebSocket for AI chat
    // connectWebSocket();

    // Refresh data periodically
    setInterval(checkSystemHealth, 30000); // Every 30 seconds
});

// Tab Navigation
function setupTabs() {
    const tabs = document.querySelectorAll('.nav-tab');
    tabs.forEach(tab => {
        tab.addEventListener('click', () => {
            const tabName = tab.dataset.tab;
            showTab(tabName);
        });
    });
}

function showTab(tabName) {
    // Hide all tabs
    document.querySelectorAll('.tab-pane').forEach(pane => {
        pane.classList.remove('active');
    });

    // Remove active from all nav tabs
    document.querySelectorAll('.nav-tab').forEach(tab => {
        tab.classList.remove('active');
    });

    // Show selected tab
    document.getElementById(tabName).classList.add('active');

    // Activate nav tab
    document.querySelector(`[data-tab="${tabName}"]`).classList.add('active');
}

// Dashboard Functions
async function refreshDashboard() {
    try {
        const response = await fetch('/api/monitoring/dashboard/summary');
        const data = await response.json();

        document.getElementById('total-devices').textContent = data.total_devices || 0;
        document.getElementById('online-devices').textContent = data.online_devices || 0;
        document.getElementById('offline-devices').textContent = data.offline_devices || 0;

        const unknown = data.total_devices - data.online_devices - data.offline_devices;
        document.getElementById('unknown-devices').textContent = unknown;

        // Update device types chart
        updateDeviceTypesChart(data.devices_by_type);

    } catch (error) {
        console.error('Error refreshing dashboard:', error);
    }
}

function updateDeviceTypesChart(deviceTypes) {
    const chartDiv = document.getElementById('device-types-chart');

    if (!deviceTypes || Object.keys(deviceTypes).length === 0) {
        chartDiv.innerHTML = '<p class="text-muted">No devices categorized yet</p>';
        return;
    }

    let html = '<div style="display: flex; flex-direction: column; gap: 10px;">';
    for (const [type, count] of Object.entries(deviceTypes)) {
        const percentage = 100; // Could calculate percentage if needed
        html += `
            <div>
                <div style="display: flex; justify-content: space-between; margin-bottom: 5px;">
                    <span>${type}</span>
                    <span>${count}</span>
                </div>
                <div style="background: var(--surface-light); height: 8px; border-radius: 4px;">
                    <div style="background: var(--primary-color); width: ${percentage}%; height: 100%; border-radius: 4px;"></div>
                </div>
            </div>
        `;
    }
    html += '</div>';

    chartDiv.innerHTML = html;
}

// Device Management
async function loadDevices() {
    try {
        const response = await fetch('/api/devices/');
        devices = await response.json();

        const tbody = document.getElementById('devices-table-body');

        if (devices.length === 0) {
            tbody.innerHTML = '<tr><td colspan="7" class="text-center">No devices found. Add a device or run a network scan.</td></tr>';
            return;
        }

        tbody.innerHTML = devices.map(device => `
            <tr>
                <td>
                    <span class="status-dot ${device.status}"></span>
                    ${device.status}
                </td>
                <td>${device.name}</td>
                <td>${device.device_type || '-'}</td>
                <td>${device.ip_address}</td>
                <td>${device.mac_address || '-'}</td>
                <td>${device.last_seen ? new Date(device.last_seen).toLocaleString() : 'Never'}</td>
                <td>
                    <button class="btn btn-secondary" style="padding: 5px 10px; font-size: 0.875rem;" onclick="pingDevice(${device.id})">Ping</button>
                    <button class="btn btn-danger" style="padding: 5px 10px; font-size: 0.875rem;" onclick="deleteDevice(${device.id})">Delete</button>
                </td>
            </tr>
        `).join('');

        // Also refresh dashboard
        refreshDashboard();

    } catch (error) {
        console.error('Error loading devices:', error);
    }
}

async function addDevice() {
    const name = document.getElementById('device-name').value;
    const type = document.getElementById('device-type').value;
    const ip = document.getElementById('device-ip').value;
    const mac = document.getElementById('device-mac').value;

    if (!name || !ip) {
        alert('Please fill in required fields');
        return;
    }

    try {
        const response = await fetch('/api/devices/', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify({
                name: name,
                device_type: type,
                ip_address: ip,
                mac_address: mac || null
            })
        });

        if (response.ok) {
            closeAddDeviceModal();
            loadDevices();
            alert('Device added successfully');
        } else {
            alert('Failed to add device');
        }
    } catch (error) {
        console.error('Error adding device:', error);
        alert('Error adding device');
    }
}

async function deleteDevice(deviceId) {
    if (!confirm('Are you sure you want to delete this device?')) {
        return;
    }

    try {
        const response = await fetch(`/api/devices/${deviceId}`, {
            method: 'DELETE'
        });

        if (response.ok) {
            loadDevices();
            alert('Device deleted successfully');
        } else {
            alert('Failed to delete device');
        }
    } catch (error) {
        console.error('Error deleting device:', error);
        alert('Error deleting device');
    }
}

async function pingDevice(deviceId) {
    try {
        const response = await fetch(`/api/devices/${deviceId}/ping`, {
            method: 'POST'
        });

        const data = await response.json();

        if (data.status === 'online') {
            alert('Device is online!');
        } else {
            alert('Device is offline or unreachable');
        }

        loadDevices();
    } catch (error) {
        console.error('Error pinging device:', error);
        alert('Error pinging device');
    }
}

// Network Operations
async function scanNetwork() {
    const subnet = document.getElementById('scan-subnet').value;
    const scanType = document.getElementById('scan-type').value;

    if (!subnet) {
        alert('Please enter a subnet');
        return;
    }

    const resultsDiv = document.getElementById('scan-results');
    resultsDiv.innerHTML = '<p>Scanning network... This may take a few moments.</p>';

    try {
        const response = await fetch('/api/network/scan', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify({
                subnet: subnet,
                scan_type: scanType
            })
        });

        const scan = await response.json();

        // Poll for results
        pollScanResults(scan.id);

    } catch (error) {
        console.error('Error starting scan:', error);
        resultsDiv.innerHTML = `<p class="text-danger">Error: ${error.message}</p>`;
    }
}

async function pollScanResults(scanId) {
    const resultsDiv = document.getElementById('scan-results');

    const checkResults = async () => {
        try {
            const response = await fetch(`/api/network/scans/${scanId}`);
            const scan = await response.json();

            if (scan.status === 'completed') {
                displayScanResults(scan);
            } else if (scan.status === 'failed') {
                resultsDiv.innerHTML = `<p class="text-danger">Scan failed: ${scan.results?.error || 'Unknown error'}</p>`;
            } else {
                // Still running, check again
                setTimeout(checkResults, 2000);
            }
        } catch (error) {
            console.error('Error polling scan results:', error);
        }
    };

    checkResults();
}

function displayScanResults(scan) {
    const resultsDiv = document.getElementById('scan-results');

    if (!scan.results || !scan.results.hosts) {
        resultsDiv.innerHTML = '<p>No hosts found</p>';
        return;
    }

    let html = `
        <h4>Scan Results</h4>
        <p>Found ${scan.results.hosts_found} hosts</p>
        <table class="device-table" style="margin-top: 10px;">
            <thead>
                <tr>
                    <th>IP Address</th>
                    <th>MAC Address</th>
                    <th>Vendor</th>
                    <th>Status</th>
                </tr>
            </thead>
            <tbody>
    `;

    scan.results.hosts.forEach(host => {
        html += `
            <tr>
                <td>${host.ip}</td>
                <td>${host.mac || '-'}</td>
                <td>${host.vendor || '-'}</td>
                <td>${host.status || 'up'}</td>
            </tr>
        `;
    });

    html += '</tbody></table>';
    resultsDiv.innerHTML = html;

    // Reload devices to show auto-discovered ones
    loadDevices();
}

async function executeSSH() {
    const host = document.getElementById('ssh-host').value;
    const username = document.getElementById('ssh-username').value;
    const password = document.getElementById('ssh-password').value;
    const command = document.getElementById('ssh-command').value;

    if (!host || !username || !command) {
        alert('Please fill in all required fields');
        return;
    }

    const resultsDiv = document.getElementById('ssh-results');
    resultsDiv.innerHTML = '<p>Executing command...</p>';

    try {
        const response = await fetch('/api/network/ssh/execute', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify({
                device_id: 0, // Not using device_id for direct execution
                command: command,
                username: username,
                password: password
            })
        });

        const result = await response.json();

        if (result.success) {
            resultsDiv.innerHTML = `
                <h4>Command Output</h4>
                <pre>${result.stdout}</pre>
                ${result.stderr ? `<h4>Errors</h4><pre>${result.stderr}</pre>` : ''}
            `;
        } else {
            resultsDiv.innerHTML = `<p class="text-danger">Error: ${result.error}</p>`;
        }

    } catch (error) {
        console.error('Error executing SSH command:', error);
        resultsDiv.innerHTML = `<p class="text-danger">Error: ${error.message}</p>`;
    }
}

// AI Assistant
function sendChatMessage() {
    const input = document.getElementById('chat-input');
    const message = input.value.trim();

    if (!message) return;

    addChatMessage('user', message);
    input.value = '';

    // Send to AI agent
    queryAIAgent(message);
}

function setChatMessage(message) {
    document.getElementById('chat-input').value = message;
    showTab('ai-assistant');
}

async function queryAIAgent(message) {
    try {
        const response = await fetch('/api/ai/query', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify({
                query: message
            })
        });

        const data = await response.json();

        if (data.response) {
            addChatMessage('assistant', data.response);
        } else {
            addChatMessage('assistant', 'Sorry, I encountered an error processing your request.');
        }

    } catch (error) {
        console.error('Error querying AI agent:', error);
        addChatMessage('assistant', 'Error: Unable to reach AI agent. Make sure Ollama is running.');
    }
}

function addChatMessage(role, content) {
    const messagesDiv = document.getElementById('chat-messages');

    const messageDiv = document.createElement('div');
    messageDiv.className = `chat-message ${role}`;
    messageDiv.textContent = content;

    messagesDiv.appendChild(messageDiv);
    messagesDiv.scrollTop = messagesDiv.scrollHeight;
}

// System Health
async function checkSystemHealth() {
    try {
        const response = await fetch('/health');
        const health = await response.json();

        const indicator = document.getElementById('status-indicator');

        if (health.status === 'healthy') {
            indicator.className = 'status-badge status-online';
            indicator.textContent = 'System Ready';
        } else {
            indicator.className = 'status-badge status-offline';
            indicator.textContent = 'System Issues';
        }

    } catch (error) {
        console.error('Error checking health:', error);
        const indicator = document.getElementById('status-indicator');
        indicator.className = 'status-badge status-offline';
        indicator.textContent = 'System Offline';
    }
}

// Modal Functions
function showAddDeviceModal() {
    document.getElementById('add-device-modal').classList.add('active');
}

function closeAddDeviceModal() {
    document.getElementById('add-device-modal').classList.remove('active');
    // Clear form
    document.getElementById('device-name').value = '';
    document.getElementById('device-ip').value = '';
    document.getElementById('device-mac').value = '';
}

// WebSocket for real-time updates (optional)
function connectWebSocket() {
    const protocol = window.location.protocol === 'https:' ? 'wss:' : 'ws:';
    const wsUrl = `${protocol}//${window.location.host}/ws/agent`;

    websocket = new WebSocket(wsUrl);

    websocket.onopen = () => {
        console.log('WebSocket connected');
    };

    websocket.onmessage = (event) => {
        const data = JSON.parse(event.data);
        if (data.response) {
            addChatMessage('assistant', data.response);
        }
    };

    websocket.onerror = (error) => {
        console.error('WebSocket error:', error);
    };

    websocket.onclose = () => {
        console.log('WebSocket disconnected');
    };
}
