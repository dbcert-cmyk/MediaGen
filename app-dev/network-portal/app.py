"""
Home Network Management Portal
Main Flask application with real-time monitoring
"""

import os
import yaml
import asyncio
from flask import Flask, render_template, jsonify, request
from flask_socketio import SocketIO, emit
from flask_cors import CORS
from threading import Thread
import time

from monitors.server_monitor import ServerMonitor
from monitors.wifi_monitor import WiFiMonitor
from monitors.switch_monitor import SwitchMonitor

# Import network agent (optional - graceful degradation)
try:
    from network_agent import NetworkAgent
    AGENT_AVAILABLE = True
except ImportError as e:
    print(f"⚠️  Network agent not available: {e}")
    AGENT_AVAILABLE = False
    NetworkAgent = None

# Create Flask app
app = Flask(__name__)
app.config['SECRET_KEY'] = os.getenv('SECRET_KEY', 'network-portal-secret-key')
CORS(app)

# Initialize SocketIO for real-time updates
socketio = SocketIO(app, cors_allowed_origins="*", async_mode='threading')

# Load configuration
def load_config():
    """Load configuration from config.yaml"""
    config_file = 'config.yaml'
    if not os.path.exists(config_file):
        config_file = 'config.example.yaml'

    with open(config_file, 'r') as f:
        return yaml.safe_load(f)

config = load_config()

# Initialize monitors
server_monitor = ServerMonitor(config.get('servers', []))
wifi_monitor = WiFiMonitor(config.get('wifi_aps', []))
switch_monitor = SwitchMonitor(config.get('switches', []))

# Initialize network agent (if available)
network_agent = None
if AGENT_AVAILABLE and NetworkAgent:
    try:
        network_agent = NetworkAgent(server_monitor, wifi_monitor, switch_monitor)
        print("✓ Network agent initialized with AI capabilities")
    except Exception as e:
        print(f"⚠️  Could not initialize network agent: {e}")
        print("   Dashboard will work without AI features")

# Background monitoring thread
monitoring_active = False

def background_monitoring():
    """Background task to continuously monitor devices"""
    global monitoring_active

    while monitoring_active:
        try:
            # Get latest stats from all monitors
            server_stats = server_monitor.get_all_stats()
            wifi_stats = wifi_monitor.get_all_stats()
            switch_stats = switch_monitor.get_all_stats()

            # Emit updates to all connected clients
            socketio.emit('server_update', server_stats)
            socketio.emit('wifi_update', wifi_stats)
            socketio.emit('switch_update', switch_stats)

            # Check for alerts
            alerts = check_alerts(server_stats, wifi_stats, switch_stats)
            if alerts:
                socketio.emit('alerts', alerts)

        except Exception as e:
            print(f"Error in monitoring loop: {e}")

        # Sleep based on configured refresh interval
        time.sleep(config.get('dashboard', {}).get('refresh_interval', 5))

def check_alerts(server_stats, wifi_stats, switch_stats):
    """Check if any metrics exceed alert thresholds"""
    alerts = []
    thresholds = config.get('alerts', {})

    # Check server alerts
    for server in server_stats:
        if server['status'] == 'online':
            if server['cpu'] > thresholds.get('cpu_threshold', 80):
                alerts.append({
                    'type': 'warning',
                    'device': server['name'],
                    'message': f"CPU usage is {server['cpu']}%"
                })

            if server['memory'] > thresholds.get('memory_threshold', 85):
                alerts.append({
                    'type': 'warning',
                    'device': server['name'],
                    'message': f"Memory usage is {server['memory']}%"
                })

            if server['disk'] > thresholds.get('disk_threshold', 90):
                alerts.append({
                    'type': 'critical',
                    'device': server['name'],
                    'message': f"Disk usage is {server['disk']}%"
                })

    return alerts


# Routes
@app.route('/')
def index():
    """Serve the main dashboard"""
    return render_template('index.html', config=config)

@app.route('/api/servers')
def api_servers():
    """Get current server stats"""
    return jsonify(server_monitor.get_all_stats())

@app.route('/api/wifi')
def api_wifi():
    """Get current WiFi stats"""
    return jsonify(wifi_monitor.get_all_stats())

@app.route('/api/switches')
def api_switches():
    """Get current switch stats"""
    return jsonify(switch_monitor.get_all_stats())

@app.route('/api/config')
def api_config():
    """Get current configuration"""
    return jsonify(config)

@app.route('/health')
def health():
    """Health check endpoint"""
    return jsonify({
        'status': 'healthy',
        'monitoring_active': monitoring_active
    })


# WebSocket events
@socketio.on('connect')
def handle_connect():
    """Handle client connection"""
    print('Client connected')
    emit('connection_response', {
        'status': 'connected',
        'message': 'Connected to Network Management Portal'
    })

@socketio.on('disconnect')
def handle_disconnect():
    """Handle client disconnection"""
    print('Client disconnected')

@socketio.on('request_update')
def handle_update_request():
    """Handle manual update request"""
    server_stats = server_monitor.get_all_stats()
    wifi_stats = wifi_monitor.get_all_stats()
    switch_stats = switch_monitor.get_all_stats()

    emit('server_update', server_stats)
    emit('wifi_update', wifi_stats)
    emit('switch_update', switch_stats)

@socketio.on('agent_query')
def handle_agent_query(data):
    """Handle AI agent query"""
    if not network_agent:
        emit('agent_error', {
            'error': 'AI agent not available. Please set GOOGLE_API_KEY in .env file.'
        })
        return

    query_text = data.get('query', '').strip()
    if not query_text:
        emit('agent_error', {'error': 'Empty query'})
        return

    print(f"[AGENT] Processing query: {query_text}")

    # Progress callback for real-time updates
    def progress_callback(progress_data):
        emit('agent_progress', progress_data)

    # Run async query in new event loop
    try:
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        result = loop.run_until_complete(
            network_agent.query(query_text, on_progress=progress_callback)
        )
        loop.close()

        if result.get('success'):
            emit('agent_response', {
                'response': result.get('response', ''),
                'workflow_steps': result.get('workflow_steps', []),
                'total_steps': result.get('total_steps', 0),
                'turns': result.get('turns', 0)
            })
        else:
            emit('agent_error', {
                'error': result.get('error', 'Unknown error occurred')
            })

    except Exception as e:
        print(f"[AGENT ERROR] {str(e)}")
        emit('agent_error', {
            'error': f'Error processing query: {str(e)}'
        })

@socketio.on('get_agent_status')
def handle_agent_status():
    """Check if agent is available"""
    emit('agent_status', {
        'available': network_agent is not None,
        'tools': network_agent.get_available_tools() if network_agent else []
    })


def main():
    """Main entry point"""
    global monitoring_active

    print("=" * 60)
    print("Home Network Management Portal")
    print("=" * 60)
    print()

    # Start background monitoring thread
    monitoring_active = True
    monitor_thread = Thread(target=background_monitoring, daemon=True)
    monitor_thread.start()
    print("✓ Background monitoring started")

    # Get port from config
    port = config.get('dashboard', {}).get('port', 5001)

    print()
    print("=" * 60)
    print(f"Server starting on http://localhost:{port}")
    print("=" * 60)
    print()
    print("Open your browser and navigate to:")
    print(f"  → http://localhost:{port}")
    print()
    print("Press Ctrl+C to stop")
    print()

    # Run Flask app with SocketIO
    try:
        socketio.run(
            app,
            host='0.0.0.0',
            port=port,
            debug=os.getenv('FLASK_DEBUG', 'False').lower() == 'true'
        )
    finally:
        monitoring_active = False


if __name__ == '__main__':
    main()
