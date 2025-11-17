"""
Flask Backend for Agent Data Flow Visualizer

Main application server with WebSocket support for real-time updates.
"""

import os
import asyncio
from flask import Flask, render_template, request, jsonify
from flask_socketio import SocketIO, emit
from flask_cors import CORS
from dotenv import load_dotenv

from agent_service import get_agent_service

# Load environment
load_dotenv()

# Create Flask app
app = Flask(__name__)
app.config['SECRET_KEY'] = os.getenv('SECRET_KEY', 'dev-secret-key-change-in-production')
CORS(app)

# Initialize SocketIO
socketio = SocketIO(app, cors_allowed_origins="*", async_mode='threading')

# Get agent service
agent_service = None


def init_agent():
    """Initialize agent service"""
    global agent_service
    try:
        agent_service = get_agent_service()
        print("✓ Agent service initialized")
        return True
    except Exception as e:
        print(f"✗ Failed to initialize agent: {e}")
        print("\nMake sure you have:")
        print("  1. Created a .env file with GOOGLE_API_KEY")
        print("  2. Get your API key from: https://aistudio.google.com")
        return False


@app.route('/')
def index():
    """Serve the main dashboard"""
    return render_template('index.html')


@app.route('/health')
def health():
    """Health check endpoint"""
    return jsonify({
        'status': 'healthy',
        'agent_initialized': agent_service is not None
    })


@app.route('/api/tools')
def get_tools():
    """Get available tools"""
    if not agent_service:
        return jsonify({'error': 'Agent not initialized'}), 500

    tools = agent_service.get_available_tools()
    return jsonify({'tools': tools})


@app.route('/api/query', methods=['POST'])
def query():
    """Handle agent query (REST endpoint)"""
    if not agent_service:
        return jsonify({'error': 'Agent not initialized'}), 500

    data = request.get_json()
    query_text = data.get('query', '')

    if not query_text:
        return jsonify({'error': 'No query provided'}), 400

    # Run async query in sync context
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)
    result = loop.run_until_complete(agent_service.query(query_text))
    loop.close()

    return jsonify(result)


@socketio.on('connect')
def handle_connect():
    """Handle client connection"""
    print('Client connected')
    emit('connection_response', {
        'status': 'connected',
        'agent_ready': agent_service is not None
    })


@socketio.on('disconnect')
def handle_disconnect():
    """Handle client disconnection"""
    print('Client disconnected')


@socketio.on('query')
def handle_query(data):
    """Handle agent query via WebSocket with real-time updates"""
    query_text = data.get('query', '')

    if not agent_service:
        emit('error', {'message': 'Agent not initialized'})
        return

    if not query_text:
        emit('error', {'message': 'No query provided'})
        return

    # Clear previous activity log
    agent_service.clear_activity_log()

    # Emit query started
    emit('query_started', {'query': query_text})

    def progress_callback(progress_data):
        """Send progress updates to client"""
        emit('progress', progress_data)

    # Run async query
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)
    result = loop.run_until_complete(
        agent_service.query(query_text, on_progress=progress_callback)
    )
    loop.close()

    # Send final result
    if result['success']:
        emit('query_complete', {
            'response': result['response'],
            'activity_log': result['activity_log'],
            'turns': result.get('turns', 0),
            'workflow_steps': result.get('workflow_steps', []),
            'total_steps': result.get('total_steps', 0)
        })
    else:
        emit('query_error', {
            'error': result.get('error', 'Unknown error'),
            'activity_log': result['activity_log']
        })


@socketio.on('demo_scenario')
def handle_demo_scenario(data):
    """Run a pre-defined demo scenario"""
    scenario_name = data.get('scenario', 'basic')

    scenarios = {
        'basic': "How many orders are in the database?",
        'files': "List all JSON files in the data folder",
        'weather': "What's the weather in San Francisco?",
        'cross_service': "Find all orders over $100",
        'analytics': "Count how many temperature readings are in sensor_data.json",
        'multi_step': "Get the weather for New York and tell me the temperature"
    }

    query = scenarios.get(scenario_name, scenarios['basic'])

    # Process as regular query
    handle_query({'query': query})


def main():
    """Main entry point"""
    print("=" * 60)
    print("Agent Data Flow Visualizer")
    print("=" * 60)
    print()

    # Check if data exists
    if not os.path.exists('data/demo.db'):
        print("⚠️  Database not found!")
        print("Please run: python setup_data.py")
        print()
        return

    # Initialize agent
    print("Initializing agent service...")
    if not init_agent():
        print()
        print("⚠️  Failed to initialize agent service")
        print("The server will start but queries will not work.")
        print()

    # Start server
    port = int(os.getenv('PORT', 5000))
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

    socketio.run(
        app,
        host='0.0.0.0',
        port=port,
        debug=os.getenv('FLASK_DEBUG', 'False').lower() == 'true'
    )


if __name__ == '__main__':
    main()
