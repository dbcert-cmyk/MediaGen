/**
 * Service Map Visualization
 * Animated SVG visualization of the agent and MCP servers
 */

class ServiceMap {
    constructor(svgId) {
        this.svg = document.getElementById(svgId);
        this.width = this.svg.clientWidth;
        this.height = 500;

        // Service definitions - keys must match IDs for lookup
        this.services = {
            'agent': {
                id: 'agent',
                name: 'Agent Kit',
                x: this.width / 2,
                y: 100,
                status: 'idle',
                type: 'agent'
            },
            'mcp-db': {
                id: 'mcp-db',
                name: 'MCP: Database',
                x: this.width / 4,
                y: 250,
                status: 'idle',
                type: 'mcp'
            },
            'mcp-fs': {
                id: 'mcp-fs',
                name: 'MCP: Filesystem',
                x: this.width / 2,
                y: 250,
                status: 'idle',
                type: 'mcp'
            },
            'mcp-api': {
                id: 'mcp-api',
                name: 'MCP: API',
                x: (this.width * 3) / 4,
                y: 250,
                status: 'idle',
                type: 'mcp'
            },
            'sqlite': {
                id: 'sqlite',
                name: 'SQLite DB',
                x: this.width / 4,
                y: 400,
                status: 'idle',
                type: 'data'
            },
            'filesystem': {
                id: 'filesystem',
                name: 'Filesystem',
                x: this.width / 2,
                y: 400,
                status: 'idle',
                type: 'data'
            },
            'mock-api': {
                id: 'mock-api',
                name: 'Mock API',
                x: (this.width * 3) / 4,
                y: 400,
                status: 'idle',
                type: 'data'
            }
        };

        // Connections
        this.connections = [
            { from: 'agent', to: 'mcp-db' },
            { from: 'agent', to: 'mcp-fs' },
            { from: 'agent', to: 'mcp-api' },
            { from: 'mcp-db', to: 'sqlite' },
            { from: 'mcp-fs', to: 'filesystem' },
            { from: 'mcp-api', to: 'mock-api' }
        ];

        this.init();
    }

    init() {
        // Clear SVG
        this.svg.innerHTML = '';

        // Create definitions for effects
        this.createDefs();

        // Draw connections
        this.drawConnections();

        // Draw services
        this.drawServices();
    }

    createDefs() {
        const defs = document.createElementNS('http://www.w3.org/2000/svg', 'defs');

        // Glow filter for active state
        const filter = document.createElementNS('http://www.w3.org/2000/svg', 'filter');
        filter.setAttribute('id', 'glow');
        filter.innerHTML = `
            <feGaussianBlur stdDeviation="4" result="coloredBlur"/>
            <feMerge>
                <feMergeNode in="coloredBlur"/>
                <feMergeNode in="SourceGraphic"/>
            </feMerge>
        `;
        defs.appendChild(filter);

        // Arrow marker
        const marker = document.createElementNS('http://www.w3.org/2000/svg', 'marker');
        marker.setAttribute('id', 'arrowhead');
        marker.setAttribute('markerWidth', '10');
        marker.setAttribute('markerHeight', '10');
        marker.setAttribute('refX', '5');
        marker.setAttribute('refY', '3');
        marker.setAttribute('orient', 'auto');
        marker.innerHTML = '<polygon points="0 0, 10 3, 0 6" fill="#999" />';
        defs.appendChild(marker);

        this.svg.appendChild(defs);
    }

    drawConnections() {
        const connectionsGroup = document.createElementNS('http://www.w3.org/2000/svg', 'g');
        connectionsGroup.setAttribute('id', 'connections');

        this.connections.forEach(conn => {
            const from = this.services[conn.from];
            const to = this.services[conn.to];

            // Skip if services don't exist
            if (!from || !to) return;

            // Create line
            const line = document.createElementNS('http://www.w3.org/2000/svg', 'line');
            line.setAttribute('id', `line-${conn.from}-${conn.to}`);
            line.setAttribute('x1', from.x);
            line.setAttribute('y1', from.y + 30);
            line.setAttribute('x2', to.x);
            line.setAttribute('y2', to.y - 30);
            line.setAttribute('stroke', '#ccc');
            line.setAttribute('stroke-width', '2');
            line.setAttribute('stroke-dasharray', '5,5');
            line.classList.add('connection-line');

            connectionsGroup.appendChild(line);
        });

        this.svg.appendChild(connectionsGroup);
    }

    drawServices() {
        const servicesGroup = document.createElementNS('http://www.w3.org/2000/svg', 'g');
        servicesGroup.setAttribute('id', 'services');

        Object.values(this.services).forEach(service => {
            const group = document.createElementNS('http://www.w3.org/2000/svg', 'g');
            group.setAttribute('id', `service-${service.id}`);
            group.setAttribute('transform', `translate(${service.x}, ${service.y})`);

            // Background rectangle
            const rect = document.createElementNS('http://www.w3.org/2000/svg', 'rect');
            rect.setAttribute('x', '-60');
            rect.setAttribute('y', '-25');
            rect.setAttribute('width', '120');
            rect.setAttribute('height', '50');
            rect.setAttribute('rx', '8');
            rect.setAttribute('fill', this.getServiceColor(service.status));
            rect.setAttribute('stroke', '#333');
            rect.setAttribute('stroke-width', '2');
            rect.classList.add('service-box');

            // Text
            const text = document.createElementNS('http://www.w3.org/2000/svg', 'text');
            text.setAttribute('text-anchor', 'middle');
            text.setAttribute('y', '5');
            text.setAttribute('fill', 'white');
            text.setAttribute('font-weight', 'bold');
            text.setAttribute('font-size', '12');
            text.textContent = service.name;

            group.appendChild(rect);
            group.appendChild(text);
            servicesGroup.appendChild(group);
        });

        this.svg.appendChild(servicesGroup);
    }

    getServiceColor(status) {
        const colors = {
            idle: '#ff9800',      // Orange
            active: '#2196F3',    // Blue
            success: '#00FF00',   // Bright green
            error: '#f44336'      // Red
        };
        return colors[status] || colors.idle;
    }

    setServiceStatus(serviceId, status) {
        const service = this.services[serviceId];
        if (!service) return;

        service.status = status;

        // Update visual
        const serviceElement = document.querySelector(`#service-${serviceId} .service-box`);
        if (serviceElement) {
            serviceElement.setAttribute('fill', this.getServiceColor(status));

            // Add strong pulse and glow animation for active state
            if (status === 'active') {
                serviceElement.style.filter = 'drop-shadow(0 0 15px ' + this.getServiceColor(status) + ')';
                serviceElement.style.animation = 'pulse 0.8s infinite';
            } else if (status === 'success') {
                serviceElement.style.filter = 'drop-shadow(0 0 20px #00FF00)';  // Bright green glow
                setTimeout(() => {
                    serviceElement.style.filter = '';
                    this.setServiceStatus(serviceId, 'idle');
                }, 1500);  // Longer success state
            } else {
                serviceElement.style.filter = '';
                serviceElement.style.animation = '';
            }
        }
    }

    activateConnection(fromId, toId, duration = 2000) {
        const line = document.getElementById(`line-${fromId}-${toId}`);
        if (!line) return;

        // Animate the connection with bright green
        line.setAttribute('stroke', '#00FF00');  // Bright green
        line.setAttribute('stroke-width', '6');  // Thicker line
        line.setAttribute('stroke-dasharray', '0');
        line.style.filter = 'drop-shadow(0 0 8px #00FF00)';  // Add glow

        // Create multiple flowing particles for better visibility
        for (let i = 0; i < 3; i++) {
            setTimeout(() => {
                this.createFlowingParticle(fromId, toId);
            }, i * 300);
        }

        // Reset after duration
        setTimeout(() => {
            line.setAttribute('stroke', '#ccc');
            line.setAttribute('stroke-width', '2');
            line.setAttribute('stroke-dasharray', '5,5');
            line.style.filter = '';
        }, duration);
    }

    createFlowingParticle(fromId, toId) {
        const from = this.services[fromId];
        const to = this.services[toId];

        const circle = document.createElementNS('http://www.w3.org/2000/svg', 'circle');
        circle.setAttribute('r', '8');  // Larger particle
        circle.setAttribute('fill', '#00FF00');  // Bright green
        circle.style.filter = 'drop-shadow(0 0 10px #00FF00)';  // Stronger glow

        // Animate from start to end
        const animate = document.createElementNS('http://www.w3.org/2000/svg', 'animate');
        animate.setAttribute('attributeName', 'cx');
        animate.setAttribute('from', from.x);
        animate.setAttribute('to', to.x);
        animate.setAttribute('dur', '1.2s');  // Slower animation
        animate.setAttribute('repeatCount', '1');

        const animate2 = document.createElementNS('http://www.w3.org/2000/svg', 'animate');
        animate2.setAttribute('attributeName', 'cy');
        animate2.setAttribute('from', from.y + 30);
        animate2.setAttribute('to', to.y - 30);
        animate2.setAttribute('dur', '1.2s');  // Slower animation
        animate2.setAttribute('repeatCount', '1');

        circle.appendChild(animate);
        circle.appendChild(animate2);
        this.svg.appendChild(circle);

        // Remove after animation
        setTimeout(() => {
            circle.remove();
        }, 1200);
    }

    simulateQuery(servicesToActivate) {
        // Reset all services
        Object.keys(this.services).forEach(id => {
            this.setServiceStatus(id, 'idle');
        });

        // Activate agent first
        this.setServiceStatus('agent', 'active');

        // Activate requested services in sequence
        let delay = 500;
        servicesToActivate.forEach(serviceId => {
            setTimeout(() => {
                // Activate the service
                this.setServiceStatus(serviceId, 'active');

                // Activate connection from agent
                this.activateConnection('agent', serviceId);

                // If it's an MCP server, also activate connection to data source
                const dataSourceMap = {
                    'mcp-db': 'sqlite',
                    'mcp-fs': 'filesystem',
                    'mcp-api': 'mock-api'
                };

                if (dataSourceMap[serviceId]) {
                    setTimeout(() => {
                        this.activateConnection(serviceId, dataSourceMap[serviceId]);
                        this.setServiceStatus(dataSourceMap[serviceId], 'active');

                        setTimeout(() => {
                            this.setServiceStatus(dataSourceMap[serviceId], 'success');
                        }, 500);
                    }, 300);
                }

                // Mark as success after processing
                setTimeout(() => {
                    this.setServiceStatus(serviceId, 'success');
                }, 800);
            }, delay);

            delay += 1000;
        });

        // Mark agent as success at the end
        setTimeout(() => {
            this.setServiceStatus('agent', 'success');
        }, delay + 500);
    }

    handleToolCall(toolName) {
        // Map tool names to services
        const toolToService = {
            // Database tools
            'query_database': 'mcp-db',
            'get_table_schema': 'mcp-db',
            'list_tables': 'mcp-db',
            'get_statistics': 'mcp-db',
            'insert_record': 'mcp-db',

            // Filesystem tools
            'list_files': 'mcp-fs',
            'read_file': 'mcp-fs',
            'search_files': 'mcp-fs',
            'get_file_info': 'mcp-fs',
            'count_json_records': 'mcp-fs',

            // API tools
            'get_weather': 'mcp-api',
            'get_stock_price': 'mcp-api',
            'get_sensor_reading': 'mcp-api',
            'search_products': 'mcp-api',
            'get_exchange_rate': 'mcp-api'
        };

        const serviceId = toolToService[toolName];
        if (serviceId) {
            this.setServiceStatus('agent', 'active');
            this.setServiceStatus(serviceId, 'active');
            this.activateConnection('agent', serviceId);

            // Activate data source
            const dataSourceMap = {
                'mcp-db': 'sqlite',
                'mcp-fs': 'filesystem',
                'mcp-api': 'mock-api'
            };

            const dataSource = dataSourceMap[serviceId];
            if (dataSource) {
                setTimeout(() => {
                    this.activateConnection(serviceId, dataSource);
                    this.setServiceStatus(dataSource, 'active');
                }, 400);
            }
        }
    }

    reset() {
        Object.keys(this.services).forEach(id => {
            this.setServiceStatus(id, 'idle');
        });
    }
}

// Initialize on page load
document.addEventListener('DOMContentLoaded', () => {
    window.serviceMap = new ServiceMap('serviceMap');

    // Handle window resize
    window.addEventListener('resize', () => {
        window.serviceMap.init();
    });
});
