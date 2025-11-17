"""
Home Network Management Portal
Main Flask application with real-time monitoring
"""

import os
import yaml
from flask import Flask, render_template, jsonify, request
from flask_socketio import SocketIO, emit
from flask_cors import CORS
from threading import Thread
import time

from monitors.server_monitor import ServerMonitor
from monitors.wifi_monitor import WiFiMonitor
from monitors.switch_monitor import SwitchMonitor

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
