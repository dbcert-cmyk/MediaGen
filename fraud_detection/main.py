"""
Main entry point for the Multi-Agent Fraud Detection System.
Runs the transaction consumer and processes transactions through the workflow.
"""
import asyncio
import structlog
from fraud_detection.config.settings import settings
from fraud_detection.streaming.consumer import TransactionConsumer
from fraud_detection.workflows.orchestrator import FraudDetectionOrchestrator
from fraud_detection.database.models import TransactionData

# Configure structured logging
structlog.configure(
    processors=[
        structlog.processors.TimeStamper(fmt="iso"),
        structlog.processors.add_log_level,
        structlog.dev.ConsoleRenderer()
    ]
)

logger = structlog.get_logger()


class FraudDetectionSystem:
    """Main fraud detection system that ties everything together."""

    def __init__(self):
        self.orchestrator = FraudDetectionOrchestrator()
        self.consumer = TransactionConsumer(
            group_id="fraud-detection-main",
            auto_offset_reset='latest'
        )

    def process_transaction_callback(self, transaction: TransactionData):
        """
        Callback function for processing transactions from Kafka.
        
        This is called for each transaction received from the stream.
        """
        logger.info(
            "Processing new transaction",
            transaction_id=transaction.transaction_id,
            user_id=transaction.user_id,
            amount=transaction.amount
        )
        
        # Run the transaction through the multi-agent workflow
        final_state = self.orchestrator.process_transaction(transaction)
        
        # Get and log the summary
        summary = self.orchestrator.get_workflow_summary(final_state)
        
        logger.info(
            "Transaction processing complete",
            summary=summary
        )
        
        # Print a nice summary
        self._print_summary(summary)

    def _print_summary(self, summary: dict):
        """Print a nice summary of the processing."""
        print("\n" + "="*80)
        print(f"TRANSACTION PROCESSED: {summary['transaction_id']}")
        print(f"User: {summary['user_id']} | Amount: ${summary['amount']}")
        print("-"*80)
        
        if 'monitor' in summary:
            mon = summary['monitor']
            print(f"✓ Monitor: {'SUSPICIOUS' if mon['is_suspicious'] else 'CLEAN'} "
                  f"(Confidence: {mon['confidence']:.1f}%, Severity: {mon['severity']})")
        
        if 'investigation' in summary:
            inv = summary['investigation']
            print(f"✓ Investigation: {'FRAUD DETECTED' if inv['is_fraudulent'] else 'NO FRAUD'} "
                  f"(Confidence: {inv['confidence']:.1f}%)")
            print(f"  Action: {inv['recommended_action']}")
        
        if 'remediation' in summary:
            rem = summary['remediation']
            print(f"✓ Remediation: {rem['action_type']} "
                  f"({'SUCCESS' if rem['success'] else 'FAILED'})")
            print(f"  Details: {rem['details']}")
        
        print("="*80 + "\n")

    def run(self):
        """Start the fraud detection system."""
        logger.info("Starting Multi-Agent Fraud Detection System")
        print("\n" + "="*80)
        print("MULTI-AGENT FRAUD DETECTION SYSTEM")
        print("="*80)
        print("System Status: ONLINE")
        print(f"Kafka: {settings.kafka_bootstrap_servers}")
        print(f"Database: {settings.database_url.split('@')[1] if '@' in settings.database_url else 'configured'}")
        print("="*80 + "\n")
        
        # Start consuming transactions
        self.consumer.consume(self.process_transaction_callback)


def main():
    """Main entry point."""
    system = FraudDetectionSystem()
    
    try:
        system.run()
    except KeyboardInterrupt:
        logger.info("Shutting down fraud detection system")
        print("\nSystem shutdown complete.")


if __name__ == "__main__":
    main()
