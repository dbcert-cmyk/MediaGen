"""
Kafka producer for generating mock transaction streams.
"""
import json
import time
import random
from datetime import datetime
from typing import Optional
from kafka import KafkaProducer
from kafka.errors import KafkaError
import structlog
from faker import Faker

from fraud_detection.config.settings import settings
from fraud_detection.database.models import TransactionData

logger = structlog.get_logger()
fake = Faker()


class TransactionProducer:
    """Produces mock transaction events to Kafka."""

    def __init__(self, bootstrap_servers: Optional[str] = None):
        self.bootstrap_servers = bootstrap_servers or settings.kafka_bootstrap_servers
        self.topic = settings.kafka_topic_transactions
        self.producer: Optional[KafkaProducer] = None
        self._connect()

    def _connect(self):
        """Connect to Kafka."""
        try:
            self.producer = KafkaProducer(
                bootstrap_servers=self.bootstrap_servers.split(','),
                value_serializer=lambda v: json.dumps(v).encode('utf-8'),
                key_serializer=lambda k: k.encode('utf-8') if k else None,
                acks='all',
                retries=3
            )
            logger.info("Connected to Kafka", bootstrap_servers=self.bootstrap_servers)
        except KafkaError as e:
            logger.error("Failed to connect to Kafka", error=str(e))
            raise

    def generate_transaction(self, user_id: Optional[str] = None, fraud_pattern: Optional[str] = None) -> TransactionData:
        """Generate a mock transaction with optional fraud patterns."""
        users = ['user_001', 'user_002', 'user_003', 'user_004', 'user_005']
        user_id = user_id or random.choice(users)
        
        # Base transaction
        transaction = {
            'transaction_id': f"txn_{fake.uuid4()[:12]}",
            'user_id': user_id,
            'amount': round(random.uniform(10, 500), 2),
            'currency': 'USD',
            'merchant': fake.company(),
            'category': random.choice(['shopping', 'food', 'electronics', 'travel', 'entertainment']),
            'location': f"{fake.city()}, {fake.state_abbr()}",
            'ip_address': fake.ipv4(),
            'device_id': f"device_{random.randint(1, 5)}",
            'transaction_type': 'purchase',
            'timestamp': datetime.utcnow().isoformat()
        }

        # Apply fraud patterns if specified
        if fraud_pattern == 'high_velocity':
            # Multiple transactions in quick succession
            transaction['amount'] = round(random.uniform(100, 1000), 2)
        elif fraud_pattern == 'unusual_amount':
            # Unusually high amount
            transaction['amount'] = round(random.uniform(5000, 15000), 2)
        elif fraud_pattern == 'geographic_anomaly':
            # Transaction from unusual location
            transaction['location'] = f"{fake.city()}, {random.choice(['AK', 'HI', 'PR'])}"
        elif fraud_pattern == 'round_amount':
            # Suspiciously round amount
            transaction['amount'] = float(random.choice([1000, 2000, 5000, 10000]))
        elif fraud_pattern == 'new_device':
            # New device
            transaction['device_id'] = f"device_{random.randint(100, 999)}"

        return TransactionData(**transaction)

    def send_transaction(self, transaction: TransactionData) -> bool:
        """Send a transaction to Kafka."""
        try:
            future = self.producer.send(
                self.topic,
                key=transaction.transaction_id,
                value=transaction.model_dump(mode='json')
            )
            # Wait for send to complete
            record_metadata = future.get(timeout=10)
            logger.info(
                "Transaction sent to Kafka",
                transaction_id=transaction.transaction_id,
                topic=record_metadata.topic,
                partition=record_metadata.partition,
                offset=record_metadata.offset
            )
            return True
        except KafkaError as e:
            logger.error("Failed to send transaction", error=str(e), transaction_id=transaction.transaction_id)
            return False

    def generate_stream(self, interval_seconds: int = 3, include_fraud: bool = True):
        """Generate a continuous stream of transactions."""
        logger.info("Starting transaction stream", interval=interval_seconds)
        
        fraud_patterns = ['high_velocity', 'unusual_amount', 'geographic_anomaly', 'round_amount', 'new_device']
        
        try:
            while True:
                # Randomly inject fraudulent transactions (20% chance)
                fraud_pattern = None
                if include_fraud and random.random() < 0.2:
                    fraud_pattern = random.choice(fraud_patterns)
                    logger.info("Generating fraudulent transaction", pattern=fraud_pattern)
                
                transaction = self.generate_transaction(fraud_pattern=fraud_pattern)
                self.send_transaction(transaction)
                
                time.sleep(interval_seconds)
        except KeyboardInterrupt:
            logger.info("Stopping transaction stream")
        finally:
            self.close()

    def close(self):
        """Close the Kafka producer."""
        if self.producer:
            self.producer.flush()
            self.producer.close()
            logger.info("Kafka producer closed")


if __name__ == "__main__":
    # For testing the producer standalone
    producer = TransactionProducer()
    producer.generate_stream(interval_seconds=2)
