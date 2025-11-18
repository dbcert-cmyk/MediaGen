"""
BigQuery Table Schema Definitions for SPO Analytics Agent

This module defines the schemas for the three core programmatic log tables:
1. impression_log_mock - Bid request and impression data
2. transaction_log_mock - Financial transaction data
3. filter_log_mock - Traffic filtering and blocking data
"""

from google.cloud import bigquery

# Schema for Impression Log Table
IMPRESSION_LOG_SCHEMA = [
    bigquery.SchemaField("impression_id", "STRING", mode="REQUIRED", description="Unique impression identifier"),
    bigquery.SchemaField("timestamp", "TIMESTAMP", mode="REQUIRED", description="Impression timestamp"),
    bigquery.SchemaField("publisher_id", "STRING", mode="REQUIRED", description="Publisher identifier"),
    bigquery.SchemaField("inventory_type", "STRING", mode="REQUIRED", description="Type of inventory (CTV, Mobile, Desktop, etc.)"),
    bigquery.SchemaField("country_geo", "STRING", mode="REQUIRED", description="Country code (ISO 3166-1 alpha-2)"),
    bigquery.SchemaField("bid_request_count", "INTEGER", mode="REQUIRED", description="Number of bid requests"),
    bigquery.SchemaField("bid_response_count", "INTEGER", mode="REQUIRED", description="Number of bid responses received"),
    bigquery.SchemaField("domain", "STRING", mode="NULLABLE", description="Publisher domain"),
    bigquery.SchemaField("device_type", "STRING", mode="NULLABLE", description="Device type"),
    bigquery.SchemaField("ad_size", "STRING", mode="NULLABLE", description="Ad size (e.g., 300x250)"),
]

# Schema for Transaction Log Table
TRANSACTION_LOG_SCHEMA = [
    bigquery.SchemaField("transaction_id", "STRING", mode="REQUIRED", description="Unique transaction identifier"),
    bigquery.SchemaField("impression_id", "STRING", mode="REQUIRED", description="Related impression ID"),
    bigquery.SchemaField("timestamp", "TIMESTAMP", mode="REQUIRED", description="Transaction timestamp"),
    bigquery.SchemaField("dsp_id", "STRING", mode="REQUIRED", description="Demand-side platform identifier"),
    bigquery.SchemaField("winning_bid", "FLOAT", mode="REQUIRED", description="Winning bid amount in USD"),
    bigquery.SchemaField("publisher_net_revenue", "FLOAT", mode="REQUIRED", description="Net revenue to publisher in USD"),
    bigquery.SchemaField("exchange_fee", "FLOAT", mode="REQUIRED", description="Exchange fee in USD"),
    bigquery.SchemaField("total_markup", "FLOAT", mode="REQUIRED", description="Total markup percentage"),
    bigquery.SchemaField("markup_fee", "FLOAT", mode="NULLABLE", description="Markup fee amount in USD"),
    bigquery.SchemaField("publisher_id", "STRING", mode="NULLABLE", description="Publisher identifier"),
    bigquery.SchemaField("country_geo", "STRING", mode="NULLABLE", description="Country code"),
]

# Schema for Filter Log Table
FILTER_LOG_SCHEMA = [
    bigquery.SchemaField("filter_id", "STRING", mode="REQUIRED", description="Unique filter event identifier"),
    bigquery.SchemaField("impression_id", "STRING", mode="REQUIRED", description="Related impression ID"),
    bigquery.SchemaField("block_timestamp", "TIMESTAMP", mode="REQUIRED", description="When the block occurred"),
    bigquery.SchemaField("filter_category", "STRING", mode="REQUIRED", description="Category of filter (IVT, Blocked_Domain, Geo_Block, etc.)"),
    bigquery.SchemaField("filter_reason_code", "STRING", mode="REQUIRED", description="Specific reason code"),
    bigquery.SchemaField("filter_reason_description", "STRING", mode="NULLABLE", description="Human-readable description"),
    bigquery.SchemaField("publisher_id", "STRING", mode="NULLABLE", description="Publisher identifier"),
    bigquery.SchemaField("country_geo", "STRING", mode="NULLABLE", description="Country code"),
    bigquery.SchemaField("severity", "STRING", mode="NULLABLE", description="Severity level (HIGH, MEDIUM, LOW)"),
]

# Table configuration
TABLE_CONFIGS = {
    "impression_log_mock": {
        "schema": IMPRESSION_LOG_SCHEMA,
        "partition_field": "timestamp",
        "partition_type": "DAY",
        "description": "Mock impression and bid request log data for SPO analytics"
    },
    "transaction_log_mock": {
        "schema": TRANSACTION_LOG_SCHEMA,
        "partition_field": "timestamp",
        "partition_type": "DAY",
        "description": "Mock transaction and financial data for supply path transparency"
    },
    "filter_log_mock": {
        "schema": FILTER_LOG_SCHEMA,
        "partition_field": "block_timestamp",
        "partition_type": "DAY",
        "description": "Mock traffic filtering and blocking events for RCA"
    }
}


def get_table_schema(table_name: str):
    """Get the schema for a specific table"""
    config = TABLE_CONFIGS.get(table_name)
    if not config:
        raise ValueError(f"Unknown table: {table_name}")
    return config["schema"]


def get_table_config(table_name: str):
    """Get the full configuration for a specific table"""
    config = TABLE_CONFIGS.get(table_name)
    if not config:
        raise ValueError(f"Unknown table: {table_name}")
    return config


def get_schema_description():
    """Get a human-readable description of all schemas for the LLM"""
    description = """
# BigQuery Schema for SPO Analytics

## Table: impression_log_mock
This table contains bid request and impression data.
Columns:
- impression_id (STRING, REQUIRED): Unique impression identifier
- timestamp (TIMESTAMP, REQUIRED): Impression timestamp
- publisher_id (STRING, REQUIRED): Publisher identifier
- inventory_type (STRING, REQUIRED): Type of inventory (CTV, Mobile, Desktop)
- country_geo (STRING, REQUIRED): Country code (e.g., US, UK, CA)
- bid_request_count (INTEGER, REQUIRED): Number of bid requests
- bid_response_count (INTEGER, REQUIRED): Number of bid responses received
- domain (STRING): Publisher domain
- device_type (STRING): Device type
- ad_size (STRING): Ad size (e.g., 300x250)

## Table: transaction_log_mock
This table contains financial transaction and revenue data.
Columns:
- transaction_id (STRING, REQUIRED): Unique transaction identifier
- impression_id (STRING, REQUIRED): Related impression ID (joins to impression_log_mock)
- timestamp (TIMESTAMP, REQUIRED): Transaction timestamp
- dsp_id (STRING, REQUIRED): Demand-side platform identifier
- winning_bid (FLOAT, REQUIRED): Winning bid amount in USD
- publisher_net_revenue (FLOAT, REQUIRED): Net revenue to publisher in USD
- exchange_fee (FLOAT, REQUIRED): Exchange fee in USD
- total_markup (FLOAT, REQUIRED): Total markup percentage
- markup_fee (FLOAT): Markup fee amount in USD
- publisher_id (STRING): Publisher identifier
- country_geo (STRING): Country code

## Table: filter_log_mock
This table contains traffic filtering and blocking events for root cause analysis.
Columns:
- filter_id (STRING, REQUIRED): Unique filter event identifier
- impression_id (STRING, REQUIRED): Related impression ID (joins to impression_log_mock)
- block_timestamp (TIMESTAMP, REQUIRED): When the block occurred
- filter_category (STRING, REQUIRED): Category of filter (IVT, Blocked_Domain, Geo_Block, Brand_Safety)
- filter_reason_code (STRING, REQUIRED): Specific reason code
- filter_reason_description (STRING): Human-readable description
- publisher_id (STRING): Publisher identifier
- country_geo (STRING): Country code
- severity (STRING): Severity level (HIGH, MEDIUM, LOW)

## Common Query Patterns:
1. Fill Rate Analysis: (bid_response_count / bid_request_count) from impression_log_mock
2. SPO Transparency: JOIN impression_log_mock with transaction_log_mock on impression_id
3. Root Cause Analysis: JOIN impression_log_mock with filter_log_mock to identify blocking reasons
4. Markup Analysis: Calculate average total_markup, exchange_fee by dimensions
"""
    return description.strip()
