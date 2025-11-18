"""
BigQuery Service Layer for SPO Analytics Agent

Handles all BigQuery operations including:
- Table creation and management
- Query execution
- Schema management
"""

import logging
from typing import List, Dict, Any, Optional
from google.cloud import bigquery
from google.api_core import exceptions
from config import Config
from schemas.bigquery_schemas import TABLE_CONFIGS, get_schema_description

logger = logging.getLogger(__name__)


class BigQueryService:
    """Service for managing BigQuery operations"""

    def __init__(self, project_id: str = None, dataset_id: str = None):
        """
        Initialize BigQuery service

        Args:
            project_id: GCP project ID (defaults to Config.GCP_PROJECT_ID)
            dataset_id: BigQuery dataset ID (defaults to Config.BIGQUERY_DATASET)
        """
        self.project_id = project_id or Config.GCP_PROJECT_ID
        self.dataset_id = dataset_id or Config.BIGQUERY_DATASET
        self.client = bigquery.Client(project=self.project_id)
        self.dataset_ref = f"{self.project_id}.{self.dataset_id}"

        logger.info(f"BigQuery service initialized for {self.dataset_ref}")

    def create_dataset(self) -> bool:
        """
        Create the BigQuery dataset if it doesn't exist

        Returns:
            True if dataset was created or already exists
        """
        try:
            dataset = bigquery.Dataset(self.dataset_ref)
            dataset.location = Config.GCP_LOCATION
            dataset.description = "SPO Analytics mock data for programmatic advertising transparency"

            dataset = self.client.create_dataset(dataset, exists_ok=True)
            logger.info(f"Dataset {self.dataset_ref} ready")
            return True

        except Exception as e:
            logger.error(f"Error creating dataset: {e}")
            raise

    def create_table(self, table_name: str) -> bool:
        """
        Create a table with partitioning

        Args:
            table_name: Name of the table to create

        Returns:
            True if table was created or already exists
        """
        try:
            config = TABLE_CONFIGS.get(table_name)
            if not config:
                raise ValueError(f"Unknown table: {table_name}")

            table_ref = f"{self.dataset_ref}.{table_name}"
            table = bigquery.Table(table_ref, schema=config["schema"])
            table.description = config["description"]

            # Configure partitioning
            if config.get("partition_field"):
                table.time_partitioning = bigquery.TimePartitioning(
                    type_=bigquery.TimePartitioningType.DAY,
                    field=config["partition_field"]
                )

            table = self.client.create_table(table, exists_ok=True)
            logger.info(f"Table {table_ref} ready")
            return True

        except Exception as e:
            logger.error(f"Error creating table {table_name}: {e}")
            raise

    def create_all_tables(self) -> bool:
        """
        Create all SPO analytics tables

        Returns:
            True if all tables were created successfully
        """
        try:
            # Create dataset first
            self.create_dataset()

            # Create all tables
            for table_name in TABLE_CONFIGS.keys():
                self.create_table(table_name)

            logger.info("All tables created successfully")
            return True

        except Exception as e:
            logger.error(f"Error creating tables: {e}")
            raise

    def execute_query(
        self,
        query: str,
        timeout: int = None
    ) -> List[Dict[str, Any]]:
        """
        Execute a BigQuery SQL query

        Args:
            query: SQL query to execute
            timeout: Query timeout in seconds (defaults to Config.QUERY_TIMEOUT_SECONDS)

        Returns:
            List of result rows as dictionaries
        """
        try:
            timeout = timeout or Config.QUERY_TIMEOUT_SECONDS

            logger.info(f"Executing query (timeout: {timeout}s)")
            logger.debug(f"Query: {query}")

            job_config = bigquery.QueryJobConfig(
                maximum_bytes_billed=10**10  # 10 GB limit
            )

            query_job = self.client.query(query, job_config=job_config)
            results = query_job.result(timeout=timeout)

            # Convert to list of dictionaries
            rows = []
            for row in results:
                rows.append(dict(row.items()))

            logger.info(f"Query returned {len(rows)} rows")
            return rows

        except exceptions.GoogleAPIError as e:
            logger.error(f"BigQuery API error: {e}")
            raise
        except Exception as e:
            logger.error(f"Error executing query: {e}")
            raise

    def insert_rows(
        self,
        table_name: str,
        rows: List[Dict[str, Any]]
    ) -> bool:
        """
        Insert rows into a table

        Args:
            table_name: Name of the table
            rows: List of row dictionaries to insert

        Returns:
            True if insertion was successful
        """
        try:
            table_ref = f"{self.dataset_ref}.{table_name}"
            table = self.client.get_table(table_ref)

            errors = self.client.insert_rows_json(table, rows)

            if errors:
                logger.error(f"Errors inserting rows: {errors}")
                raise Exception(f"Failed to insert rows: {errors}")

            logger.info(f"Inserted {len(rows)} rows into {table_name}")
            return True

        except Exception as e:
            logger.error(f"Error inserting rows into {table_name}: {e}")
            raise

    def get_table_row_count(self, table_name: str) -> int:
        """
        Get the number of rows in a table

        Args:
            table_name: Name of the table

        Returns:
            Row count
        """
        try:
            query = f"""
                SELECT COUNT(*) as count
                FROM `{self.dataset_ref}.{table_name}`
            """
            results = self.execute_query(query)
            return results[0]['count'] if results else 0

        except Exception as e:
            logger.error(f"Error getting row count for {table_name}: {e}")
            return 0

    def get_schema_context(self) -> str:
        """
        Get schema description for LLM context

        Returns:
            Schema description string
        """
        return get_schema_description()

    def validate_query(self, query: str) -> tuple[bool, Optional[str]]:
        """
        Validate a SQL query without executing it

        Args:
            query: SQL query to validate

        Returns:
            Tuple of (is_valid, error_message)
        """
        try:
            job_config = bigquery.QueryJobConfig(dry_run=True, use_query_cache=False)
            query_job = self.client.query(query, job_config=job_config)

            # Query is valid
            logger.info(f"Query validation successful. Will process {query_job.total_bytes_processed} bytes")
            return True, None

        except exceptions.GoogleAPIError as e:
            logger.warning(f"Query validation failed: {e}")
            return False, str(e)
        except Exception as e:
            logger.error(f"Error validating query: {e}")
            return False, str(e)

    def get_dataset_stats(self) -> Dict[str, Any]:
        """
        Get statistics about the dataset

        Returns:
            Dictionary with dataset statistics
        """
        stats = {
            'dataset': self.dataset_ref,
            'tables': {}
        }

        for table_name in TABLE_CONFIGS.keys():
            try:
                row_count = self.get_table_row_count(table_name)
                stats['tables'][table_name] = {
                    'row_count': row_count,
                    'status': 'ready' if row_count > 0 else 'empty'
                }
            except Exception as e:
                stats['tables'][table_name] = {
                    'row_count': 0,
                    'status': 'error',
                    'error': str(e)
                }

        return stats
