"""
Configuration Management for SPO Analytics Agent
"""

import os
from dotenv import load_dotenv

# Load environment variables
load_dotenv()


class Config:
    """Application configuration"""

    # Flask configuration
    SECRET_KEY = os.getenv('SECRET_KEY', 'dev-secret-key-change-in-production')
    DEBUG = os.getenv('DEBUG', 'true').lower() == 'true'
    PORT = int(os.getenv('PORT', 5001))

    # GCP Configuration
    GCP_PROJECT_ID = os.getenv('GCP_PROJECT_ID')
    GCP_LOCATION = os.getenv('GCP_LOCATION', 'us-central1')
    BIGQUERY_DATASET = os.getenv('BIGQUERY_DATASET', 'spo_analytics')

    # Vertex AI / Gemini Configuration
    GEMINI_MODEL = os.getenv('GEMINI_MODEL', 'gemini-2.0-flash-exp')
    GEMINI_TEMPERATURE = float(os.getenv('GEMINI_TEMPERATURE', '0.2'))
    GEMINI_MAX_TOKENS = int(os.getenv('GEMINI_MAX_TOKENS', '8192'))

    # Mock Mode (for testing without GCP)
    MOCK_MODE = os.getenv('MOCK_MODE', 'false').lower() == 'true'

    # Query execution limits
    MAX_QUERY_RESULTS = int(os.getenv('MAX_QUERY_RESULTS', '10000'))
    QUERY_TIMEOUT_SECONDS = int(os.getenv('QUERY_TIMEOUT_SECONDS', '30'))

    # Application settings
    ENABLE_QUERY_CACHE = os.getenv('ENABLE_QUERY_CACHE', 'true').lower() == 'true'
    LOG_LEVEL = os.getenv('LOG_LEVEL', 'INFO')

    @classmethod
    def validate(cls):
        """Validate required configuration"""
        if not cls.MOCK_MODE:
            if not cls.GCP_PROJECT_ID:
                raise ValueError(
                    "GCP_PROJECT_ID is required when MOCK_MODE is disabled. "
                    "Set MOCK_MODE=true to test without GCP credentials."
                )
        return True

    @classmethod
    def get_display_config(cls):
        """Get configuration for display (without sensitive data)"""
        return {
            'mode': 'MOCK' if cls.MOCK_MODE else 'PRODUCTION',
            'project_id': cls.GCP_PROJECT_ID or 'N/A (Mock Mode)',
            'location': cls.GCP_LOCATION,
            'dataset': cls.BIGQUERY_DATASET,
            'model': cls.GEMINI_MODEL,
            'debug': cls.DEBUG,
        }


# Validate configuration on import
Config.validate()
