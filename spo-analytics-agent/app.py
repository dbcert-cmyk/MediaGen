"""
SPO Analytics Agent - Flask Application

Main web application providing:
- Conversational analytics API
- Web UI for natural language queries
- Dataset management endpoints
"""

import logging
from flask import Flask, render_template, request, jsonify
from datetime import datetime
from config import Config
from spo_agent import MockSPOAnalyticsAgent

# Conditional imports for production mode
if not Config.MOCK_MODE:
    from spo_agent import SPOAnalyticsAgent
    from bigquery_service import BigQueryService

# Configure logging
logging.basicConfig(
    level=getattr(logging, Config.LOG_LEVEL),
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Initialize Flask app
app = Flask(__name__)
app.config.from_object(Config)

# Initialize services based on mode
if Config.MOCK_MODE:
    logger.info("="*60)
    logger.info("🎭 MOCK MODE ENABLED - Testing without GCP credentials")
    logger.info("   No costs will be incurred")
    logger.info("="*60)
    agent = MockSPOAnalyticsAgent()
    bq_service = None
else:
    logger.info("="*60)
    logger.info("☁️  PRODUCTION MODE - Using Vertex AI and BigQuery")
    logger.info(f"   Project: {Config.GCP_PROJECT_ID}")
    logger.info(f"   Dataset: {Config.BIGQUERY_DATASET}")
    logger.info(f"   Model: {Config.GEMINI_MODEL}")
    logger.info("="*60)
    bq_service = BigQueryService()
    agent = SPOAnalyticsAgent(bq_service)


@app.route('/')
def index():
    """Render the main chat interface"""
    return render_template('index.html', config=Config.get_display_config())


@app.route('/health')
def health():
    """Health check endpoint"""
    return jsonify({
        'status': 'healthy',
        'timestamp': datetime.utcnow().isoformat(),
        'mode': 'MOCK' if Config.MOCK_MODE else 'PRODUCTION',
        'version': '1.0.0'
    })


@app.route('/api/config')
def get_config():
    """Get application configuration (non-sensitive)"""
    return jsonify(Config.get_display_config())


@app.route('/api/query', methods=['POST'])
def answer_query():
    """
    Main endpoint for natural language analytics queries

    Request body:
    {
        "query": "Why did my fill rate drop last week?"
    }

    Response:
    {
        "success": true,
        "user_query": "...",
        "sql_query": "...",
        "narrative": "...",
        "data": [...],
        "metadata": {...}
    }
    """
    try:
        data = request.get_json()

        if not data or 'query' not in data:
            return jsonify({
                'success': False,
                'error': 'Query is required in request body'
            }), 400

        user_query = data['query'].strip()

        if not user_query:
            return jsonify({
                'success': False,
                'error': 'Query cannot be empty'
            }), 400

        # Process the query through the agent
        result = agent.answer_query(user_query)

        # Return appropriate status code
        status_code = 200 if result['success'] else 500

        return jsonify(result), status_code

    except Exception as e:
        logger.error(f"Error processing query: {e}")
        return jsonify({
            'success': False,
            'error': str(e),
            'timestamp': datetime.utcnow().isoformat()
        }), 500


@app.route('/api/dataset/stats')
def dataset_stats():
    """
    Get dataset statistics

    Response:
    {
        "dataset": "project.dataset",
        "tables": {
            "impression_log_mock": {"row_count": 1000000, "status": "ready"},
            ...
        }
    }
    """
    if Config.MOCK_MODE:
        return jsonify({
            'mode': 'MOCK',
            'dataset': 'mock_dataset',
            'tables': {
                'impression_log_mock': {'row_count': 1000000, 'status': 'mock'},
                'transaction_log_mock': {'row_count': 800000, 'status': 'mock'},
                'filter_log_mock': {'row_count': 230000, 'status': 'mock'}
            }
        })

    try:
        stats = bq_service.get_dataset_stats()
        return jsonify(stats)

    except Exception as e:
        logger.error(f"Error getting dataset stats: {e}")
        return jsonify({
            'error': str(e),
            'timestamp': datetime.utcnow().isoformat()
        }), 500


@app.route('/api/dataset/create', methods=['POST'])
def create_dataset():
    """
    Create dataset and tables (admin endpoint)

    Response:
    {
        "success": true,
        "message": "Dataset and tables created successfully"
    }
    """
    if Config.MOCK_MODE:
        return jsonify({
            'success': False,
            'error': 'Dataset creation not available in mock mode'
        }), 400

    try:
        bq_service.create_all_tables()

        return jsonify({
            'success': True,
            'message': 'Dataset and tables created successfully',
            'dataset': bq_service.dataset_ref
        })

    except Exception as e:
        logger.error(f"Error creating dataset: {e}")
        return jsonify({
            'success': False,
            'error': str(e),
            'timestamp': datetime.utcnow().isoformat()
        }), 500


@app.route('/api/examples')
def get_examples():
    """
    Get example queries to help users get started

    Response:
    {
        "examples": [
            {
                "category": "Fill Rate Analysis",
                "queries": [...]
            },
            ...
        ]
    }
    """
    examples = [
        {
            "category": "Fill Rate Analysis",
            "queries": [
                "What's my fill rate for the last 7 days?",
                "Compare fill rates between CTV and Mobile inventory",
                "Why did my fill rate drop last week?",
                "Show me fill rate by country for the past month"
            ]
        },
        {
            "category": "SPO Transparency / Fees",
            "queries": [
                "What's the average markup across all DSPs?",
                "Compare exchange fees for different inventory types",
                "Which DSP has the highest markup?",
                "Show me total fees by publisher last month"
            ]
        },
        {
            "category": "Root Cause Analysis / Blocking",
            "queries": [
                "Why is traffic being blocked?",
                "What's the IVT block rate for US traffic?",
                "Show me the top filter categories from last week",
                "Why did my performance drop in the UK?"
            ]
        },
        {
            "category": "Revenue & Performance",
            "queries": [
                "What's my total revenue for the last 30 days?",
                "Compare revenue across different publishers",
                "Show me the top performing inventory types",
                "What's my average winning bid by geo?"
            ]
        }
    ]

    return jsonify({"examples": examples})


@app.errorhandler(404)
def not_found(error):
    """Handle 404 errors"""
    return jsonify({
        'error': 'Endpoint not found',
        'timestamp': datetime.utcnow().isoformat()
    }), 404


@app.errorhandler(500)
def internal_error(error):
    """Handle 500 errors"""
    logger.error(f"Internal server error: {error}")
    return jsonify({
        'error': 'Internal server error',
        'timestamp': datetime.utcnow().isoformat()
    }), 500


if __name__ == '__main__':
    logger.info("Starting SPO Analytics Agent...")
    logger.info(f"Access the application at: http://localhost:{Config.PORT}")

    app.run(
        host='0.0.0.0',
        port=Config.PORT,
        debug=Config.DEBUG
    )
