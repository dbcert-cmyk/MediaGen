/**
 * Dashboard Main Logic
 * Handles WebSocket connection, user interactions, and UI updates
 */

class Dashboard {
    constructor() {
        this.socket = null;
        this.stats = {
            totalQueries: 0,
            totalToolCalls: 0,
            totalTime: 0,
            successCount: 0
        };
        this.currentQueryStartTime = null;

        this.init();
    }

    init() {
        // Initialize WebSocket
        this.initWebSocket();

        // Set up event listeners
        this.setupEventListeners();

        // Initialize UI
        this.updateConnectionStatus('connecting', 'Connecting...');
    }

    initWebSocket() {
        this.socket = io();

        this.socket.on('connect', () => {
            console.log('Connected to server');
            this.updateConnectionStatus('connected', 'Connected');
            this.addActivityLog('system', 'Connected to server');
        });

        this.socket.on('disconnect', () => {
            console.log('Disconnected from server');
            this.updateConnectionStatus('error', 'Disconnected');
            this.addActivityLog('system', 'Disconnected from server');
        });

        this.socket.on('connection_response', (data) => {
            console.log('Connection response:', data);
            if (data.agent_ready) {
                this.addActivityLog('system', 'Agent is ready!');
            } else {
                this.addActivityLog('system', 'Warning: Agent not initialized. Check API key.');
            }
        });

        this.socket.on('query_started', (data) => {
            this.currentQueryStartTime = Date.now();
            this.addActivityLog('user_query', `Query: ${data.query}`);
            this.setQueryButtonState(true);

            // Reset service map
            if (window.serviceMap) {
                window.serviceMap.reset();
                window.serviceMap.setServiceStatus('agent', 'active');
            }
        });

        this.socket.on('progress', (data) => {
            console.log('Progress:', data);

            if (data.type === 'tool_call') {
                this.addActivityLog('tool_call', `Calling ${data.tool} on ${data.server} MCP server`);
                this.stats.totalToolCalls++;

                // Update service map
                if (window.serviceMap && data.tool) {
                    window.serviceMap.handleToolCall(data.tool);
                }
            }
        });

        this.socket.on('query_complete', (data) => {
            const duration = this.currentQueryStartTime
                ? ((Date.now() - this.currentQueryStartTime) / 1000).toFixed(2)
                : 0;

            this.addActivityLog('tool_response', `Query completed in ${duration}s`);
            this.displayAgentResponse(data.response);
            this.setQueryButtonState(false);

            // Update stats
            this.stats.totalQueries++;
            this.stats.successCount++;
            this.stats.totalTime += parseFloat(duration);
            this.updateStats();

            // Update service map
            if (window.serviceMap) {
                window.serviceMap.setServiceStatus('agent', 'success');
            }
        });

        this.socket.on('query_error', (data) => {
            this.addActivityLog('error', `Error: ${data.error}`);
            this.displayAgentResponse(`Error: ${data.error}`, true);
            this.setQueryButtonState(false);

            // Update stats
            this.stats.totalQueries++;
            this.updateStats();

            // Update service map
            if (window.serviceMap) {
                window.serviceMap.setServiceStatus('agent', 'error');
            }
        });
    }

    setupEventListeners() {
        // Submit button
        const submitBtn = document.getElementById('submitBtn');
        const queryInput = document.getElementById('queryInput');

        submitBtn.addEventListener('click', () => this.submitQuery());
        queryInput.addEventListener('keypress', (e) => {
            if (e.key === 'Enter' && e.ctrlKey) {
                this.submitQuery();
            }
        });

        // Quick action buttons
        document.querySelectorAll('.quick-btn').forEach(btn => {
            btn.addEventListener('click', (e) => {
                const query = e.target.getAttribute('data-query');
                queryInput.value = query;
                this.submitQuery();
            });
        });

        // Demo button
        document.getElementById('demoBtn').addEventListener('click', () => {
            this.runDemo();
        });

        // Clear button
        document.getElementById('clearBtn').addEventListener('click', () => {
            this.clearLog();
        });
    }

    submitQuery() {
        const queryInput = document.getElementById('queryInput');
        const query = queryInput.value.trim();

        if (!query) {
            alert('Please enter a query');
            return;
        }

        // Send query via WebSocket
        this.socket.emit('query', { query });

        // Clear input
        // queryInput.value = '';
    }

    runDemo() {
        const demoQueries = [
            "How many orders are in the database?",
            "List all JSON files in the data folder",
            "What's the weather in San Francisco?",
            "Find all orders over $100"
        ];

        let index = 0;
        const queryInput = document.getElementById('queryInput');

        const runNext = () => {
            if (index < demoQueries.length) {
                queryInput.value = demoQueries[index];
                this.submitQuery();
                index++;
                setTimeout(runNext, 5000); // Wait 5 seconds between queries
            }
        };

        runNext();
    }

    updateConnectionStatus(status, text) {
        const statusDot = document.querySelector('.status-dot');
        const statusText = document.querySelector('.status-text');

        statusDot.className = `status-dot ${status}`;
        statusText.textContent = text;
    }

    addActivityLog(type, message) {
        const activityLog = document.getElementById('activityLog');

        // Remove placeholder if exists
        const placeholder = activityLog.querySelector('.activity-item.system');
        if (placeholder && placeholder.querySelector('.activity-text').textContent.includes('System ready')) {
            placeholder.remove();
        }

        const item = document.createElement('div');
        item.className = `activity-item ${type}`;

        const icon = this.getActivityIcon(type);
        const iconSpan = document.createElement('span');
        iconSpan.className = 'activity-icon';
        iconSpan.textContent = icon;

        const textSpan = document.createElement('span');
        textSpan.className = 'activity-text';
        textSpan.textContent = message;

        item.appendChild(iconSpan);
        item.appendChild(textSpan);

        activityLog.appendChild(item);

        // Auto-scroll to bottom
        activityLog.scrollTop = activityLog.scrollHeight;

        // Limit log size
        while (activityLog.children.length > 50) {
            activityLog.removeChild(activityLog.firstChild);
        }
    }

    getActivityIcon(type) {
        const icons = {
            system: 'ℹ️',
            user_query: '❓',
            tool_call: '🔧',
            tool_response: '✅',
            error: '❌'
        };
        return icons[type] || 'ℹ️';
    }

    displayAgentResponse(response, isError = false) {
        const responseDiv = document.getElementById('agentResponse');

        // Clear placeholder
        responseDiv.innerHTML = '';

        const content = document.createElement('div');
        content.className = isError ? 'error-response' : 'success-response';

        // Try to parse as JSON for better formatting
        try {
            const jsonData = JSON.parse(response);
            const pre = document.createElement('pre');
            pre.textContent = JSON.stringify(jsonData, null, 2);
            content.appendChild(pre);
        } catch (e) {
            // Not JSON, display as text
            const p = document.createElement('p');
            p.textContent = response;
            content.appendChild(p);
        }

        responseDiv.appendChild(content);
    }

    setQueryButtonState(isLoading) {
        const submitBtn = document.getElementById('submitBtn');
        const btnText = submitBtn.querySelector('.btn-text');
        const btnLoader = submitBtn.querySelector('.btn-loader');

        if (isLoading) {
            submitBtn.disabled = true;
            btnText.style.display = 'none';
            btnLoader.style.display = 'inline';
            btnLoader.innerHTML = '<span class="spinner"></span> Processing...';
        } else {
            submitBtn.disabled = false;
            btnText.style.display = 'inline';
            btnLoader.style.display = 'none';
        }
    }

    updateStats() {
        document.getElementById('statQueries').textContent = this.stats.totalQueries;
        document.getElementById('statToolCalls').textContent = this.stats.totalToolCalls;

        const avgTime = this.stats.totalQueries > 0
            ? (this.stats.totalTime / this.stats.totalQueries).toFixed(1)
            : 0;
        document.getElementById('statAvgTime').textContent = `${avgTime}s`;

        const successRate = this.stats.totalQueries > 0
            ? Math.round((this.stats.successCount / this.stats.totalQueries) * 100)
            : 100;
        document.getElementById('statSuccess').textContent = `${successRate}%`;
    }

    clearLog() {
        const activityLog = document.getElementById('activityLog');
        activityLog.innerHTML = `
            <div class="activity-item system">
                <span class="activity-icon">ℹ️</span>
                <span class="activity-text">Activity log cleared</span>
            </div>
        `;
    }
}

// Initialize dashboard on page load
let dashboard;
document.addEventListener('DOMContentLoaded', () => {
    dashboard = new Dashboard();
});
