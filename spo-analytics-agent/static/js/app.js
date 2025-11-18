// SPO Analytics Agent - Frontend JavaScript

class SPOAnalyticsApp {
    constructor() {
        this.chatMessages = document.getElementById('chat-messages');
        this.queryForm = document.getElementById('query-form');
        this.queryInput = document.getElementById('query-input');
        this.sendBtn = document.getElementById('send-btn');

        this.initializeEventListeners();
        this.loadDatasetStats();
    }

    initializeEventListeners() {
        // Form submission
        this.queryForm.addEventListener('submit', (e) => {
            e.preventDefault();
            this.handleSubmit();
        });

        // Enter key handling (Enter to submit, Shift+Enter for new line)
        this.queryInput.addEventListener('keydown', (e) => {
            if (e.key === 'Enter' && !e.shiftKey) {
                e.preventDefault();
                this.handleSubmit();
            }
        });

        // Example query buttons
        document.querySelectorAll('.example-btn').forEach(btn => {
            btn.addEventListener('click', () => {
                const query = btn.getAttribute('data-query');
                this.queryInput.value = query;
                this.handleSubmit();
            });
        });
    }

    async handleSubmit() {
        const query = this.queryInput.value.trim();

        if (!query) {
            return;
        }

        // Add user message to chat
        this.addUserMessage(query);

        // Clear input
        this.queryInput.value = '';

        // Disable input while processing
        this.setInputEnabled(false);

        // Show loading indicator
        const loadingMessage = this.addLoadingMessage();

        try {
            // Send query to backend
            const response = await fetch('/api/query', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                },
                body: JSON.stringify({ query }),
            });

            const result = await response.json();

            // Remove loading indicator
            loadingMessage.remove();

            // Add assistant response
            this.addAssistantResponse(result);

        } catch (error) {
            // Remove loading indicator
            loadingMessage.remove();

            // Show error message
            this.addErrorMessage('Failed to process query: ' + error.message);
        } finally {
            // Re-enable input
            this.setInputEnabled(true);
            this.queryInput.focus();
        }
    }

    addUserMessage(text) {
        const messageDiv = document.createElement('div');
        messageDiv.className = 'message user-message';
        messageDiv.innerHTML = `
            <div class="message-icon">👤</div>
            <div class="message-content">
                <p>${this.escapeHtml(text)}</p>
            </div>
        `;
        this.chatMessages.appendChild(messageDiv);
        this.scrollToBottom();
    }

    addLoadingMessage() {
        const template = document.getElementById('loading-template');
        const loadingMessage = template.content.cloneNode(true);
        this.chatMessages.appendChild(loadingMessage);
        this.scrollToBottom();
        return this.chatMessages.lastElementChild;
    }

    addAssistantResponse(result) {
        const messageDiv = document.createElement('div');
        messageDiv.className = 'message assistant-message';

        if (result.success && result.narrative) {
            // Successful response with narrative
            messageDiv.innerHTML = `
                <div class="message-icon">🤖</div>
                <div class="message-content">
                    <p>${this.escapeHtml(result.narrative)}</p>
                    ${this.buildResponseDetails(result)}
                </div>
            `;
        } else if (result.error) {
            // Error response
            messageDiv.innerHTML = `
                <div class="message-icon">⚠️</div>
                <div class="message-content">
                    <div class="error-message">
                        <strong>Error:</strong> ${this.escapeHtml(result.error)}
                    </div>
                </div>
            `;
        } else {
            // Unexpected response
            messageDiv.innerHTML = `
                <div class="message-icon">🤖</div>
                <div class="message-content">
                    <p>I received an unexpected response. Please try again.</p>
                </div>
            `;
        }

        this.chatMessages.appendChild(messageDiv);
        this.scrollToBottom();
    }

    buildResponseDetails(result) {
        let html = '';

        // Show SQL query if available
        if (result.sql_query) {
            html += `
                <div class="response-section">
                    <h4>📝 Generated SQL Query</h4>
                    <button class="expand-btn" onclick="this.nextElementSibling.style.display = this.nextElementSibling.style.display === 'none' ? 'block' : 'none'; this.textContent = this.textContent.includes('Show') ? 'Hide SQL' : 'Show SQL'">
                        Show SQL
                    </button>
                    <div class="sql-query" style="display: none;">${this.escapeHtml(result.sql_query)}</div>
                </div>
            `;
        }

        // Show data table if available and not too large
        if (result.data && result.data.length > 0 && result.data.length <= 10) {
            html += `
                <div class="response-section">
                    <h4>📊 Data (${result.data.length} rows)</h4>
                    ${this.buildDataTable(result.data)}
                </div>
            `;
        } else if (result.data && result.data.length > 10) {
            html += `
                <div class="response-section">
                    <h4>📊 Data (${result.data.length} rows)</h4>
                    <p class="hint">First 10 rows shown:</p>
                    ${this.buildDataTable(result.data.slice(0, 10))}
                </div>
            `;
        }

        // Show metadata
        if (result.metadata && result.metadata.row_count !== undefined) {
            const rowCount = result.metadata.row_count.toLocaleString();
            html += `
                <div class="response-section">
                    <p class="hint">Query returned ${rowCount} rows</p>
                </div>
            `;
        }

        return html;
    }

    buildDataTable(data) {
        if (!data || data.length === 0) {
            return '<p class="hint">No data</p>';
        }

        const columns = Object.keys(data[0]);

        let html = '<table class="data-table"><thead><tr>';

        // Table headers
        columns.forEach(col => {
            html += `<th>${this.escapeHtml(col)}</th>`;
        });
        html += '</tr></thead><tbody>';

        // Table rows
        data.forEach(row => {
            html += '<tr>';
            columns.forEach(col => {
                const value = row[col];
                const formattedValue = this.formatValue(value);
                html += `<td>${this.escapeHtml(formattedValue)}</td>`;
            });
            html += '</tr>';
        });

        html += '</tbody></table>';
        return html;
    }

    formatValue(value) {
        if (value === null || value === undefined) {
            return '-';
        }

        // Format numbers
        if (typeof value === 'number') {
            if (Number.isInteger(value)) {
                return value.toLocaleString();
            } else {
                return value.toFixed(2);
            }
        }

        return String(value);
    }

    addErrorMessage(message) {
        const messageDiv = document.createElement('div');
        messageDiv.className = 'message assistant-message';
        messageDiv.innerHTML = `
            <div class="message-icon">⚠️</div>
            <div class="message-content">
                <div class="error-message">
                    ${this.escapeHtml(message)}
                </div>
            </div>
        `;
        this.chatMessages.appendChild(messageDiv);
        this.scrollToBottom();
    }

    setInputEnabled(enabled) {
        this.queryInput.disabled = !enabled;
        this.sendBtn.disabled = !enabled;
    }

    scrollToBottom() {
        this.chatMessages.scrollTop = this.chatMessages.scrollHeight;
    }

    escapeHtml(text) {
        const div = document.createElement('div');
        div.textContent = text;
        return div.innerHTML;
    }

    async loadDatasetStats() {
        try {
            const response = await fetch('/api/dataset/stats');
            const stats = await response.json();

            const statsDiv = document.getElementById('dataset-stats');

            if (stats.mode === 'MOCK') {
                statsDiv.innerHTML = `
                    <div class="stat-item">
                        <span class="stat-label">Mode:</span>
                        <span class="stat-value">MOCK</span>
                    </div>
                    <p class="hint" style="margin-top: 0.5rem;">
                        Using simulated data for testing
                    </p>
                `;
            } else {
                let html = `
                    <div class="stat-item">
                        <span class="stat-label">Dataset:</span>
                        <span class="stat-value">${stats.dataset}</span>
                    </div>
                `;

                if (stats.tables) {
                    Object.entries(stats.tables).forEach(([tableName, info]) => {
                        const rowCount = info.row_count ? info.row_count.toLocaleString() : '0';
                        const statusEmoji = info.status === 'ready' ? '✅' : '⚠️';

                        html += `
                            <div class="stat-item">
                                <span class="stat-label">${statusEmoji} ${tableName}:</span>
                                <span class="stat-value">${rowCount}</span>
                            </div>
                        `;
                    });
                }

                statsDiv.innerHTML = html;
            }
        } catch (error) {
            console.error('Failed to load dataset stats:', error);
            document.getElementById('dataset-stats').innerHTML = `
                <p class="hint">Failed to load stats</p>
            `;
        }
    }
}

// Initialize app when DOM is ready
document.addEventListener('DOMContentLoaded', () => {
    new SPOAnalyticsApp();
});
