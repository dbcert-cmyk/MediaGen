"""
Kafka consumer for processing transaction streams.
"""
import json
from typing import Callable, Optional
from kafka import KafkaConsumer
from kafka.errors import KafkaError
import structlog

from fraud_detection.config.settings import settings
from fraud_detection.database.models import TransactionData

logger = structlog.get_logger()


class TransactionConsumer:
    """Consumes transaction events from Kafka and processes them."""

    def __init__(
        self, 
        group_id: str = "fraud-detection-group",
        bootstrap_servers: Optional[str] = None,
        auto_offset_reset: str = 'latest'
    ):
        self.bootstrap_servers = bootstrap_servers or settings.kafka_bootstrap_servers
        self.topic = settings.kafka_topic_transactions
        self.group_id = group_id
        self.consumer: Optional[KafkaConsumer] = None
        self.auto_offset_reset = auto_offset_reset
        self._connect()

    def _connect(self):
        """Connect to Kafka consumer."""
        try:
            self.consumer = KafkaConsumer(
                self.topic,
                bootstrap_servers=self.bootstrap_servers.split(','),
                group_id=self.group_id,
                value_deserializer=lambda m: json.loads(m.decode('utf-8')),
                key_deserializer=lambda k: k.decode('utf-8') if k else None,
                auto_offset_reset=self.auto_offset_reset,
                enable_auto_commit=True,
                max_poll_records=10
            )
            logger.info(
                "Connected to Kafka consumer",
                bootstrap_servers=self.bootstrap_servers,
                topic=self.topic,
                group_id=self.group_id
            )
        except KafkaError as e:
            logger.error("Failed to connect to Kafka consumer", error=str(e))
            raise

    def consume(self, callback: Callable[[TransactionData], None], timeout_ms: int = 1000):
        """
        Consume messages from Kafka and process them with the callback.
        
        Args:
            callback: Function to call with each transaction
            timeout_ms: Polling timeout in milliseconds
        """
        logger.info("Starting to consume transactions")
        
        try:
            for message in self.consumer:
                try:
                    # Parse the transaction
                    transaction_data = TransactionData(**message.value)
                    
                    logger.info(
                        "Received transaction",
                        transaction_id=transaction_data.transaction_id,
                        user_id=transaction_data.user_id,
                        amount=transaction_data.amount
                    )
                    
                    # Process the transaction with the callback
                    callback(transaction_data)
                    
                except Exception as e:
                    logger.error(
                        "Error processing transaction",
                        error=str(e),
                        message_key=message.key,
                        partition=message.partition,
                        offset=message.offset
                    )
        except KeyboardInterrupt:
            logger.info("Stopping transaction consumer")
        finally:
            self.close()

    def close(self):
        """Close the Kafka consumer."""
        if self.consumer:
            self.consumer.close()
            logger.info("Kafka consumer closed")


class AlertProducer:
    """Produces fraud alerts to a separate Kafka topic."""

    def __init__(self, bootstrap_servers: Optional[str] = None):
        from kafka import KafkaProducer
        
        self.bootstrap_servers = bootstrap_servers or settings.kafka_bootstrap_servers
        self.topic = settings.kafka_topic_alerts
        
        self.producer = KafkaProducer(
            bootstrap_servers=self.bootstrap_servers.split(','),
            value_serializer=lambda v: json.dumps(v).encode('utf-8'),
            key_serializer=lambda k: k.encode('utf-8') if k else None,
            acks='all'
        )
        logger.info("Alert producer connected", topic=self.topic)

    def send_alert(self, alert_data: dict) -> bool:
        """Send a fraud alert."""
        try:
            future = self.producer.send(
                self.topic,
                key=alert_data.get('transaction_id', ''),
                value=alert_data
            )
            future.get(timeout=10)
            logger.info("Alert sent", transaction_id=alert_data.get('transaction_id'))
            return True
        except KafkaError as e:
            logger.error("Failed to send alert", error=str(e))
            return False

    def close(self):
        """Close the producer."""
        if self.producer:
            self.producer.flush()
            self.producer.close()
