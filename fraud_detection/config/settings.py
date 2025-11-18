"""
Configuration settings for the Multi-Agent Fraud Detection System.
"""
from pydantic_settings import BaseSettings
from typing import Optional


class Settings(BaseSettings):
    """Application settings loaded from environment variables."""

    # Google Cloud / Vertex AI
    google_api_key: Optional[str] = None
    gcp_project_id: Optional[str] = None
    gcp_location: str = "us-central1"

    # Database
    database_url: str = "postgresql://fraud_user:fraud_pass_dev_only@localhost:5432/fraud_detection"

    # Kafka/Redpanda
    kafka_bootstrap_servers: str = "localhost:9092"
    kafka_topic_transactions: str = "transactions"
    kafka_topic_alerts: str = "fraud_alerts"

    # Redis
    redis_url: str = "redis://localhost:6379"

    # Agent Models
    transaction_monitor_model: str = "gemini-2.0-flash-exp"
    investigator_model: str = "gemini-2.0-flash-exp"
    remediation_model: str = "gemini-2.0-flash-exp"

    # Fraud Detection Thresholds
    suspicious_amount_threshold: float = 5000.00
    velocity_check_window_seconds: int = 300
    max_transactions_per_window: int = 10

    # Notification
    alert_email: str = "security@example.com"
    smtp_server: str = "smtp.gmail.com"
    smtp_port: int = 587

    # Demo Mode
    demo_mode: bool = True
    generate_mock_transactions: bool = True
    mock_transaction_interval_seconds: int = 3

    class Config:
        env_file = ".env"
        case_sensitive = False


# Global settings instance
settings = Settings()
