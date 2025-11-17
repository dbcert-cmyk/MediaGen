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
        this.demoMode = false;

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
                // Format message with step number if available
                const stepPrefix = data.step ? `[Step ${data.step}] ` : '';
                this.addActivityLog('tool_call', `${stepPrefix}Calling ${data.tool} on ${data.server} MCP server`);
                this.stats.totalToolCalls++;

                // Update service map with step number
                if (window.serviceMap && data.tool) {
                    window.serviceMap.handleToolCall(data.tool, data.step);
                }
            }
        });

        this.socket.on('query_complete', (data) => {
            const duration = this.currentQueryStartTime
                ? ((Date.now() - this.currentQueryStartTime) / 1000).toFixed(2)
                : 0;

            // Display workflow summary if multi-step
            if (data.total_steps && data.total_steps > 1) {
                this.addActivityLog('tool_response', `✓ Completed ${data.total_steps}-step workflow in ${duration}s`);
            } else {
                this.addActivityLog('tool_response', `Query completed in ${duration}s`);
            }

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

        // Demo mode toggle
        document.getElementById('demoModeToggle').addEventListener('change', (e) => {
            this.demoMode = e.target.checked;
            const statusText = this.demoMode ? 'Demo Mode (Local)' : 'Live Mode';
            this.addActivityLog('system', `Switched to ${statusText}`);
        });
    }

    submitQuery() {
        const queryInput = document.getElementById('queryInput');
        const query = queryInput.value.trim();

        if (!query) {
            alert('Please enter a query');
            return;
        }

        // Check if demo mode is enabled
        if (this.demoMode) {
            this.simulateQuery(query);
        } else {
            // Send query via WebSocket
            this.socket.emit('query', { query });
        }

        // Clear input
        // queryInput.value = '';
    }

    simulateQuery(query) {
        // Simulate the entire query workflow locally
        this.currentQueryStartTime = Date.now();
        this.addActivityLog('user_query', `Query: ${query}`);
        this.setQueryButtonState(true);

        // Reset service map
        if (window.serviceMap) {
            window.serviceMap.reset();
            window.serviceMap.setServiceStatus('agent', 'active');
        }

        // Determine which services to activate based on query
        const services = this.getServicesForQuery(query);

        // Simulate tool calls
        let delay = 800;
        let stepNumber = 0;

        services.forEach((service, index) => {
            setTimeout(() => {
                stepNumber++;
                const stepPrefix = services.length > 1 ? `[Step ${stepNumber}] ` : '';
                this.addActivityLog('tool_call', `${stepPrefix}Calling ${service.tool} on ${service.server} MCP server`);
                this.stats.totalToolCalls++;

                if (window.serviceMap) {
                    window.serviceMap.handleToolCall(service.tool, stepNumber);
                }

                // If this is the last service, complete the query
                if (index === services.length - 1) {
                    setTimeout(() => {
                        const duration = ((Date.now() - this.currentQueryStartTime) / 1000).toFixed(2);
                        const response = this.getMockResponse(query, services);

                        if (services.length > 1) {
                            this.addActivityLog('tool_response', `✓ Completed ${services.length}-step workflow in ${duration}s`);
                        } else {
                            this.addActivityLog('tool_response', `Query completed in ${duration}s`);
                        }

                        this.displayAgentResponse(response);
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
                    }, 1000);
                }
            }, delay);

            delay += 1500;
        });
    }

    getServicesForQuery(query) {
        const lowerQuery = query.toLowerCase();
        const services = [];

        // Detect database queries
        if (lowerQuery.includes('order') || lowerQuery.includes('database') ||
            lowerQuery.includes('table') || lowerQuery.includes('statistics') ||
            lowerQuery.includes('customer')) {
            services.push({ tool: 'query_database', server: 'database' });
        }

        // Detect file operations
        if (lowerQuery.includes('file') || lowerQuery.includes('json') ||
            lowerQuery.includes('log') || lowerQuery.includes('search')) {
            services.push({ tool: 'list_files', server: 'filesystem' });
        }

        // Detect API calls
        if (lowerQuery.includes('weather') || lowerQuery.includes('stock') ||
            lowerQuery.includes('price') || lowerQuery.includes('sensor')) {
            services.push({ tool: 'get_weather', server: 'api' });
        }

        // If multi-step query, add additional service
        if ((lowerQuery.includes('and') || lowerQuery.includes('then')) && services.length > 0) {
            if (lowerQuery.includes('count') || lowerQuery.includes('reading')) {
                services.push({ tool: 'count_json_records', server: 'filesystem' });
            } else if (lowerQuery.includes('list') && lowerQuery.includes('table')) {
                services.push({ tool: 'list_tables', server: 'database' });
            }
        }

        // Default to database if nothing matched
        if (services.length === 0) {
            services.push({ tool: 'query_database', server: 'database' });
        }

        return services;
    }

    getMockResponse(query, services) {
        const lowerQuery = query.toLowerCase();

        // Database responses
        if (lowerQuery.includes('how many order')) {
            return 'Based on the database query, there are 150 orders in the database.';
        }
        if (lowerQuery.includes('customer')) {
            return 'Found 8 customers in the database. The top customers by order value are: Alice Johnson, Bob Smith, and Carol Davis.';
        }
        if (lowerQuery.includes('statistics')) {
            return 'Database Statistics: 8 customers, 12 products, 150 orders, 500 analytics events. Total database size: 2.4 MB.';
        }

        // File responses
        if (lowerQuery.includes('json file')) {
            return 'Found 3 JSON files: sensor_data.json (245 KB), user_analytics.json (189 KB), and api_logs.json (156 KB).';
        }
        if (lowerQuery.includes('log file')) {
            return 'Found 2 log files: server.log (1.2 MB) and error.log (45 KB).';
        }
        if (lowerQuery.includes('temperature')) {
            return 'Counted 720 temperature readings in sensor_data.json. Average temperature: 22.3°C.';
        }

        // Weather responses
        if (lowerQuery.includes('weather')) {
            if (lowerQuery.includes('san francisco')) {
                return 'San Francisco weather: Partly cloudy, 18°C (64°F), 65% humidity, wind 12 km/h W.';
            }
            if (lowerQuery.includes('new york')) {
                return 'Multi-city weather report:\n• San Francisco: 18°C, partly cloudy\n• New York: 12°C, overcast';
            }
            return 'San Francisco weather: Partly cloudy, 18°C (64°F), 65% humidity.';
        }

        // Multi-step responses
        if (services.length > 1) {
            return `Completed ${services.length}-step workflow successfully. Data retrieved from ${services.map(s => s.server).join(' and ')} services.`;
        }

        // Default response
        return 'Query processed successfully using demo mode. All visualizations are simulated locally without API calls.';
    }

    runDemo() {
        const demoQueries = [
            "How many orders are in the database?",
            "List all JSON files in the data folder and then count the temperature readings in sensor_data.json",
            "What's the weather in San Francisco and New York?",
            "Show me database statistics and list the available tables",
            "Search for log files and tell me about the database schema"
        ];

        let index = 0;
        const queryInput = document.getElementById('queryInput');

        const runNext = () => {
            if (index < demoQueries.length) {
                queryInput.value = demoQueries[index];
                this.submitQuery();
                index++;
                setTimeout(runNext, 10000); // Wait 10 seconds between queries to avoid rate limits
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
            responseDiv.appendChild(content);
        } catch (e) {
            // Not JSON, display as text with typing animation
            const p = document.createElement('p');
            content.appendChild(p);
            responseDiv.appendChild(content);

            // Typing animation
            this.typeText(p, response, 15); // 15ms per character
        }
    }

    typeText(element, text, speed = 15) {
        let index = 0;
        element.textContent = '';

        const typeChar = () => {
            if (index < text.length) {
                element.textContent += text.charAt(index);
                index++;
                setTimeout(typeChar, speed);
            }
        };

        typeChar();
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
