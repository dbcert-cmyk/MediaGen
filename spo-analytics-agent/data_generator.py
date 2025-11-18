"""
Mock Data Generator for SPO Analytics Agent

Generates realistic programmatic advertising log data for:
- Impression logs
- Transaction logs
- Filter/blocking logs

Usage:
    python data_generator.py --rows 1000000
    python data_generator.py --rows 1000000 --days 90 --batch-size 10000
"""

import argparse
import logging
import random
import uuid
from datetime import datetime, timedelta
from typing import List, Dict, Any
import time
from config import Config
from bigquery_service import BigQueryService

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Mock data constants
PUBLISHERS = [f"PUB-{i:04d}" for i in range(1, 51)]  # 50 publishers
DSPS = ["DSP-A", "DSP-B", "DSP-C", "DSP-D", "DSP-E", "DSP-F"]
INVENTORY_TYPES = ["CTV", "Mobile", "Desktop", "Tablet"]
COUNTRIES = ["US", "UK", "CA", "DE", "FR", "JP", "AU", "BR", "IN", "MX"]
DEVICE_TYPES = ["Smart TV", "iPhone", "Android", "iPad", "Desktop", "Laptop"]
AD_SIZES = ["300x250", "728x90", "320x50", "300x600", "160x600", "970x250"]
DOMAINS = [f"publisher{i}.com" for i in range(1, 101)]

# Filter categories and reasons
FILTER_CATEGORIES = {
    "IVT": ["bot_traffic", "datacenter_ip", "suspicious_pattern", "fraud_score_high"],
    "Blocked_Domain": ["domain_blacklist", "malware_detected", "policy_violation"],
    "Geo_Block": ["restricted_region", "compliance_block", "geo_targeting"],
    "Brand_Safety": ["inappropriate_content", "brand_risk", "contextual_block"],
    "Technical": ["invalid_format", "timeout", "malformed_request"]
}

SEVERITIES = ["HIGH", "MEDIUM", "LOW"]


class DataGenerator:
    """Generate mock programmatic advertising data"""

    def __init__(self, days_back: int = 90):
        """
        Initialize data generator

        Args:
            days_back: Number of days of historical data to generate
        """
        self.days_back = days_back
        self.end_date = datetime.utcnow()
        self.start_date = self.end_date - timedelta(days=days_back)

    def generate_random_timestamp(self) -> datetime:
        """Generate a random timestamp within the date range"""
        delta = self.end_date - self.start_date
        random_seconds = random.randint(0, int(delta.total_seconds()))
        return self.start_date + timedelta(seconds=random_seconds)

    def generate_impression_log(self, impression_id: str) -> Dict[str, Any]:
        """Generate a single impression log entry"""
        publisher_id = random.choice(PUBLISHERS)
        inventory_type = random.choice(INVENTORY_TYPES)
        country = random.choice(COUNTRIES)

        # Realistic bid request/response patterns
        bid_request_count = random.randint(1, 10)

        # Fill rate varies by inventory type
        fill_rate_base = {
            "CTV": 0.82,
            "Mobile": 0.71,
            "Desktop": 0.78,
            "Tablet": 0.68
        }
        fill_rate = fill_rate_base.get(inventory_type, 0.75) + random.uniform(-0.15, 0.15)
        fill_rate = max(0, min(1, fill_rate))  # Clamp to [0, 1]

        bid_response_count = int(bid_request_count * fill_rate)

        return {
            "impression_id": impression_id,
            "timestamp": self.generate_random_timestamp().isoformat(),
            "publisher_id": publisher_id,
            "inventory_type": inventory_type,
            "country_geo": country,
            "bid_request_count": bid_request_count,
            "bid_response_count": bid_response_count,
            "domain": random.choice(DOMAINS),
            "device_type": random.choice(DEVICE_TYPES),
            "ad_size": random.choice(AD_SIZES)
        }

    def generate_transaction_log(self, impression_id: str, timestamp: str) -> Dict[str, Any]:
        """Generate a transaction log entry"""
        dsp_id = random.choice(DSPS)

        # Winning bid varies by inventory and DSP
        base_bid = {
            "CTV": 2.50,
            "Mobile": 0.80,
            "Desktop": 1.20,
            "Tablet": 0.90
        }

        inventory_type = random.choice(INVENTORY_TYPES)
        winning_bid = base_bid.get(inventory_type, 1.00) * random.uniform(0.5, 2.0)

        # Markup varies by DSP (realistic patterns)
        dsp_markup_base = {
            "DSP-A": 0.112,  # 11.2%
            "DSP-B": 0.131,  # 13.1%
            "DSP-C": 0.165,  # 16.5%
            "DSP-D": 0.145,  # 14.5%
            "DSP-E": 0.128,  # 12.8%
            "DSP-F": 0.155   # 15.5%
        }

        total_markup = dsp_markup_base.get(dsp_id, 0.138) * random.uniform(0.8, 1.2)
        exchange_fee = winning_bid * total_markup
        markup_fee = exchange_fee * 0.3  # 30% of exchange fee is pure markup
        publisher_net_revenue = winning_bid - exchange_fee

        return {
            "transaction_id": str(uuid.uuid4()),
            "impression_id": impression_id,
            "timestamp": timestamp,
            "dsp_id": dsp_id,
            "winning_bid": round(winning_bid, 4),
            "publisher_net_revenue": round(publisher_net_revenue, 4),
            "exchange_fee": round(exchange_fee, 4),
            "total_markup": round(total_markup * 100, 2),  # Store as percentage
            "markup_fee": round(markup_fee, 4),
            "publisher_id": random.choice(PUBLISHERS),
            "country_geo": random.choice(COUNTRIES)
        }

    def generate_filter_log(self, impression_id: str, timestamp: str) -> Dict[str, Any]:
        """Generate a filter/blocking log entry"""
        filter_category = random.choice(list(FILTER_CATEGORIES.keys()))
        filter_reason_code = random.choice(FILTER_CATEGORIES[filter_category])

        # Generate human-readable description
        descriptions = {
            "bot_traffic": "Detected non-human traffic pattern",
            "datacenter_ip": "Request originated from datacenter IP range",
            "suspicious_pattern": "Unusual traffic pattern detected",
            "fraud_score_high": "High fraud probability score",
            "domain_blacklist": "Domain appears on block list",
            "malware_detected": "Known malware association",
            "policy_violation": "Publisher policy violation",
            "restricted_region": "Traffic from restricted geographic region",
            "compliance_block": "Regulatory compliance block",
            "geo_targeting": "Outside target geography",
            "inappropriate_content": "Content failed brand safety check",
            "brand_risk": "High brand risk score",
            "contextual_block": "Contextual targeting mismatch",
            "invalid_format": "Invalid bid request format",
            "timeout": "Request timeout",
            "malformed_request": "Malformed bid request"
        }

        # Severity distribution
        severity_weights = {"HIGH": 0.2, "MEDIUM": 0.5, "LOW": 0.3}
        severity = random.choices(
            list(severity_weights.keys()),
            weights=list(severity_weights.values())
        )[0]

        return {
            "filter_id": str(uuid.uuid4()),
            "impression_id": impression_id,
            "block_timestamp": timestamp,
            "filter_category": filter_category,
            "filter_reason_code": filter_reason_code,
            "filter_reason_description": descriptions.get(filter_reason_code, "Blocked"),
            "publisher_id": random.choice(PUBLISHERS),
            "country_geo": random.choice(COUNTRIES),
            "severity": severity
        }

    def generate_batch(self, batch_size: int, generate_filters: bool = True) -> tuple[List, List, List]:
        """
        Generate a batch of data

        Args:
            batch_size: Number of impressions to generate
            generate_filters: Whether to generate filter logs (not all impressions have filters)

        Returns:
            Tuple of (impression_logs, transaction_logs, filter_logs)
        """
        impressions = []
        transactions = []
        filters = []

        for _ in range(batch_size):
            impression_id = str(uuid.uuid4())

            # Generate impression
            impression = self.generate_impression_log(impression_id)
            impressions.append(impression)

            # Generate transaction (70% of impressions result in transactions)
            if random.random() < 0.70:
                transaction = self.generate_transaction_log(
                    impression_id,
                    impression["timestamp"]
                )
                transactions.append(transaction)

            # Generate filter log (23% of impressions are blocked)
            if generate_filters and random.random() < 0.23:
                filter_log = self.generate_filter_log(
                    impression_id,
                    impression["timestamp"]
                )
                filters.append(filter_log)

        return impressions, transactions, filters


def main():
    """Main data generation function"""
    parser = argparse.ArgumentParser(description='Generate mock SPO analytics data')
    parser.add_argument(
        '--rows',
        type=int,
        default=100000,
        help='Total number of impression rows to generate (default: 100000)'
    )
    parser.add_argument(
        '--days',
        type=int,
        default=90,
        help='Number of days of historical data (default: 90)'
    )
    parser.add_argument(
        '--batch-size',
        type=int,
        default=10000,
        help='Batch size for BigQuery inserts (default: 10000)'
    )
    parser.add_argument(
        '--skip-filters',
        action='store_true',
        help='Skip generating filter logs'
    )

    args = parser.parse_args()

    if Config.MOCK_MODE:
        logger.error("Cannot generate data in MOCK_MODE. Set MOCK_MODE=false in .env")
        return

    logger.info("="*60)
    logger.info("SPO Analytics Data Generator")
    logger.info("="*60)
    logger.info(f"Target rows: {args.rows:,}")
    logger.info(f"Historical days: {args.days}")
    logger.info(f"Batch size: {args.batch_size:,}")
    logger.info(f"Generate filters: {not args.skip_filters}")
    logger.info("="*60)

    # Initialize services
    bq_service = BigQueryService()
    generator = DataGenerator(days_back=args.days)

    # Ensure tables exist
    logger.info("Ensuring tables exist...")
    bq_service.create_all_tables()

    # Generate and insert data in batches
    total_batches = (args.rows + args.batch_size - 1) // args.batch_size
    total_impressions = 0
    total_transactions = 0
    total_filters = 0

    start_time = time.time()

    for batch_num in range(total_batches):
        batch_start = time.time()

        # Calculate batch size (last batch might be smaller)
        current_batch_size = min(args.batch_size, args.rows - total_impressions)

        logger.info(f"Generating batch {batch_num + 1}/{total_batches} ({current_batch_size:,} rows)...")

        # Generate data
        impressions, transactions, filters = generator.generate_batch(
            current_batch_size,
            generate_filters=not args.skip_filters
        )

        # Insert into BigQuery
        try:
            if impressions:
                bq_service.insert_rows("impression_log_mock", impressions)
                total_impressions += len(impressions)

            if transactions:
                bq_service.insert_rows("transaction_log_mock", transactions)
                total_transactions += len(transactions)

            if filters:
                bq_service.insert_rows("filter_log_mock", filters)
                total_filters += len(filters)

            batch_time = time.time() - batch_start
            logger.info(f"Batch {batch_num + 1} completed in {batch_time:.2f}s")

        except Exception as e:
            logger.error(f"Error inserting batch {batch_num + 1}: {e}")
            raise

    total_time = time.time() - start_time

    # Summary
    logger.info("="*60)
    logger.info("Data Generation Complete!")
    logger.info("="*60)
    logger.info(f"Impressions generated: {total_impressions:,}")
    logger.info(f"Transactions generated: {total_transactions:,}")
    logger.info(f"Filters generated: {total_filters:,}")
    logger.info(f"Total time: {total_time:.2f}s")
    logger.info(f"Rate: {total_impressions / total_time:.0f} impressions/sec")
    logger.info("="*60)

    # Verify data
    logger.info("Verifying data in BigQuery...")
    stats = bq_service.get_dataset_stats()
    for table_name, info in stats['tables'].items():
        logger.info(f"{table_name}: {info['row_count']:,} rows ({info['status']})")


if __name__ == '__main__':
    main()
