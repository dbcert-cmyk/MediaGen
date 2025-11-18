"""
SPO Analytics Agent - Core NLQ-to-SQL and Data Synthesis Engine

This module implements the conversational analytics agent that:
1. Converts natural language queries to BigQuery SQL
2. Executes the SQL against BigQuery
3. Synthesizes results into conversational Root Cause Analysis narratives
"""

import logging
import json
from typing import Dict, Any, List, Optional
from datetime import datetime
from config import Config

# Conditional imports for production mode
if not Config.MOCK_MODE:
    import vertexai
    from vertexai.generative_models import GenerativeModel, GenerationConfig
    from bigquery_service import BigQueryService

logger = logging.getLogger(__name__)


class SPOAnalyticsAgent:
    """
    Conversational agent for SPO analytics using Gemini Enterprise
    """

    def __init__(self, bigquery_service: "BigQueryService"):
        """
        Initialize the SPO Analytics Agent

        Args:
            bigquery_service: BigQueryService instance for data access
        """
        self.bq_service = bigquery_service

        # Initialize Vertex AI
        vertexai.init(
            project=Config.GCP_PROJECT_ID,
            location=Config.GCP_LOCATION
        )

        # Initialize Gemini model
        self.model = GenerativeModel(Config.GEMINI_MODEL)

        # Get schema context for the model
        self.schema_context = self.bq_service.get_schema_context()

        logger.info(f"SPO Analytics Agent initialized with model: {Config.GEMINI_MODEL}")

    def _build_nlq_to_sql_prompt(self, user_query: str) -> str:
        """
        Build the prompt for converting NLQ to SQL

        Args:
            user_query: Natural language query from the user

        Returns:
            Formatted prompt for Gemini
        """
        prompt = f"""You are an expert SQL analyst for programmatic advertising supply path optimization (SPO).

Your task is to convert natural language questions into optimized BigQuery SQL queries.

# Database Schema Context:
{self.schema_context}

# Dataset Information:
- Dataset: `{self.bq_service.dataset_ref}`
- All tables are in this dataset
- Tables are partitioned by timestamp fields for performance

# Instructions:
1. Generate ONLY valid BigQuery SQL (GoogleSQL dialect)
2. Use fully qualified table names: `{self.bq_service.dataset_ref}.table_name`
3. Optimize queries with appropriate WHERE clauses, especially on partition fields
4. Include relevant JOINs when questions span multiple tables
5. Use appropriate aggregations (COUNT, AVG, SUM) based on the question
6. Format numbers appropriately (use ROUND for percentages and monetary values)
7. Add ORDER BY and LIMIT clauses when appropriate
8. NEVER include markdown formatting, explanations, or comments - ONLY the SQL query

# Common Query Patterns:
- Fill Rate: `(SUM(bid_response_count) / NULLIF(SUM(bid_request_count), 0)) * 100 AS fill_rate_pct`
- Markup %: `AVG(total_markup) AS avg_markup_pct`
- Join for RCA: `FROM impression_log_mock i LEFT JOIN filter_log_mock f ON i.impression_id = f.impression_id`
- Time filtering: `WHERE timestamp >= TIMESTAMP_SUB(CURRENT_TIMESTAMP(), INTERVAL 7 DAY)`

# User Question:
{user_query}

# SQL Query:
"""
        return prompt

    def _build_synthesis_prompt(
        self,
        user_query: str,
        sql_query: str,
        query_results: List[Dict[str, Any]]
    ) -> str:
        """
        Build the prompt for synthesizing data into conversational response

        Args:
            user_query: Original natural language query
            sql_query: The SQL query that was executed
            query_results: Results from BigQuery

        Returns:
            Formatted prompt for Gemini
        """
        # Format results as a readable table
        results_text = self._format_results_as_text(query_results)

        prompt = f"""You are a programmatic advertising analyst providing Root Cause Analysis (RCA) insights.

Your task is to convert raw data into a clear, conversational explanation that helps the user understand their programmatic performance.

# Original Question:
{user_query}

# Data Retrieved:
{results_text}

# Instructions for Response:
1. Provide a concise, conversational narrative (2-4 sentences)
2. Focus on the "WHY" and implications, not just the "WHAT"
3. Highlight key metrics with specific numbers
4. If problems are identified (IVT blocks, low fill rates, high markups), explain the likely cause
5. Use programmatic advertising terminology naturally (DSP, SSP, fill rate, IVT, markup, etc.)
6. Be direct and actionable - what does this data mean for the partner?
7. If there's no data or zero results, acknowledge it clearly

# Examples of Good Responses:
- "Your fill rate dropped to 45% last week primarily due to a 40% spike in Invalid Traffic (IVT) blocks from US inventory, which our system automatically filtered to protect brand safety."
- "The average exchange markup for CTV inventory is 12.5%, which is within normal range. Mobile inventory shows a slightly higher markup at 15.2%, driven mainly by DSP-XYZ's bidding patterns."
- "Performance looks healthy: you're seeing an average fill rate of 78% across all geos with consistent revenue. The slight dip in UK traffic is due to increased brand safety filtering, not a supply issue."

# Your Response:
"""
        return prompt

    def _format_results_as_text(self, results: List[Dict[str, Any]]) -> str:
        """
        Format query results as readable text for the LLM

        Args:
            results: Query results

        Returns:
            Formatted text representation
        """
        if not results:
            return "No data found."

        # Limit to first 20 rows to avoid token limits
        limited_results = results[:20]

        # Format as a simple table
        text = f"Total rows: {len(results)}\n\n"

        if limited_results:
            # Get column names
            columns = list(limited_results[0].keys())
            text += "Results:\n"

            for i, row in enumerate(limited_results, 1):
                text += f"\nRow {i}:\n"
                for col in columns:
                    value = row.get(col)
                    # Format timestamps and floats nicely
                    if isinstance(value, datetime):
                        value = value.strftime('%Y-%m-%d %H:%M:%S')
                    elif isinstance(value, float):
                        value = f"{value:.2f}"
                    text += f"  {col}: {value}\n"

            if len(results) > 20:
                text += f"\n... and {len(results) - 20} more rows"

        return text

    def generate_sql_from_nlq(self, user_query: str) -> tuple[str, Optional[str]]:
        """
        Convert natural language query to SQL

        Args:
            user_query: Natural language query

        Returns:
            Tuple of (sql_query, error_message)
        """
        try:
            prompt = self._build_nlq_to_sql_prompt(user_query)

            generation_config = GenerationConfig(
                temperature=Config.GEMINI_TEMPERATURE,
                max_output_tokens=Config.GEMINI_MAX_TOKENS,
            )

            logger.info("Generating SQL from NLQ...")
            response = self.model.generate_content(
                prompt,
                generation_config=generation_config
            )

            sql_query = response.text.strip()

            # Clean up the SQL (remove markdown code blocks if present)
            if sql_query.startswith("```sql"):
                sql_query = sql_query[6:]
            if sql_query.startswith("```"):
                sql_query = sql_query[3:]
            if sql_query.endswith("```"):
                sql_query = sql_query[:-3]

            sql_query = sql_query.strip()

            logger.info(f"Generated SQL query: {sql_query[:200]}...")
            return sql_query, None

        except Exception as e:
            logger.error(f"Error generating SQL from NLQ: {e}")
            return "", str(e)

    def synthesize_response(
        self,
        user_query: str,
        sql_query: str,
        query_results: List[Dict[str, Any]]
    ) -> tuple[str, Optional[str]]:
        """
        Synthesize query results into conversational response

        Args:
            user_query: Original natural language query
            sql_query: The SQL query that was executed
            query_results: Results from BigQuery

        Returns:
            Tuple of (narrative_response, error_message)
        """
        try:
            prompt = self._build_synthesis_prompt(user_query, sql_query, query_results)

            generation_config = GenerationConfig(
                temperature=0.7,  # Higher temperature for more natural responses
                max_output_tokens=1024,
            )

            logger.info("Synthesizing conversational response...")
            response = self.model.generate_content(
                prompt,
                generation_config=generation_config
            )

            narrative = response.text.strip()
            logger.info("Response synthesized successfully")
            return narrative, None

        except Exception as e:
            logger.error(f"Error synthesizing response: {e}")
            return "", str(e)

    def answer_query(self, user_query: str) -> Dict[str, Any]:
        """
        Main method to answer a natural language query end-to-end

        Args:
            user_query: Natural language query from the user

        Returns:
            Dictionary containing the response and metadata
        """
        result = {
            'user_query': user_query,
            'timestamp': datetime.utcnow().isoformat(),
            'success': False,
            'sql_query': None,
            'data': None,
            'narrative': None,
            'error': None,
            'metadata': {}
        }

        try:
            # Step 1: Convert NLQ to SQL
            logger.info(f"Processing query: {user_query}")
            sql_query, error = self.generate_sql_from_nlq(user_query)

            if error:
                result['error'] = f"Failed to generate SQL: {error}"
                return result

            result['sql_query'] = sql_query

            # Step 2: Validate SQL
            is_valid, validation_error = self.bq_service.validate_query(sql_query)
            if not is_valid:
                result['error'] = f"Invalid SQL generated: {validation_error}"
                return result

            # Step 3: Execute query
            query_results = self.bq_service.execute_query(sql_query)
            result['data'] = query_results
            result['metadata']['row_count'] = len(query_results)

            # Step 4: Synthesize conversational response
            narrative, error = self.synthesize_response(
                user_query,
                sql_query,
                query_results
            )

            if error:
                result['error'] = f"Failed to synthesize response: {error}"
                return result

            result['narrative'] = narrative
            result['success'] = True

            logger.info("Query answered successfully")
            return result

        except Exception as e:
            logger.error(f"Error answering query: {e}")
            result['error'] = str(e)
            return result


class MockSPOAnalyticsAgent:
    """
    Mock version of SPO Analytics Agent for testing without GCP
    """

    def __init__(self):
        logger.info("Mock SPO Analytics Agent initialized")

    def answer_query(self, user_query: str) -> Dict[str, Any]:
        """
        Mock query response

        Args:
            user_query: Natural language query

        Returns:
            Mock response dictionary
        """
        # Simple mock responses based on keywords
        query_lower = user_query.lower()

        if 'fill rate' in query_lower:
            mock_narrative = (
                "Based on the mock data, your average fill rate is 76.3% across all inventory types. "
                "CTV inventory shows the strongest performance at 82.1%, while mobile inventory is "
                "slightly lower at 71.2% due to increased Invalid Traffic filtering in the US region."
            )
            mock_data = [
                {'inventory_type': 'CTV', 'fill_rate_pct': 82.1, 'impressions': 125000},
                {'inventory_type': 'Mobile', 'fill_rate_pct': 71.2, 'impressions': 89000},
                {'inventory_type': 'Desktop', 'fill_rate_pct': 78.5, 'impressions': 43000}
            ]
        elif 'markup' in query_lower or 'fee' in query_lower:
            mock_narrative = (
                "Your average exchange markup is 13.8% across all DSPs. DSP-A shows the lowest markup "
                "at 11.2%, while DSP-C has a slightly higher markup at 16.5%, primarily due to additional "
                "data enrichment services included in the transaction path."
            )
            mock_data = [
                {'dsp_id': 'DSP-A', 'avg_markup_pct': 11.2, 'avg_exchange_fee': 0.045},
                {'dsp_id': 'DSP-B', 'avg_markup_pct': 13.1, 'avg_exchange_fee': 0.052},
                {'dsp_id': 'DSP-C', 'avg_markup_pct': 16.5, 'avg_exchange_fee': 0.067}
            ]
        elif 'block' in query_lower or 'filter' in query_lower or 'ivt' in query_lower:
            mock_narrative = (
                "You're seeing a 23% block rate, with Invalid Traffic (IVT) being the primary reason at 67% "
                "of all blocks. This spike occurred last week primarily in US inventory and is within normal "
                "ranges for brand safety protection. The IVT detection successfully protected your supply path quality."
            )
            mock_data = [
                {'filter_category': 'IVT', 'block_count': 15420, 'percentage': 67.2},
                {'filter_category': 'Blocked_Domain', 'block_count': 4850, 'percentage': 21.1},
                {'filter_category': 'Geo_Block', 'block_count': 2680, 'percentage': 11.7}
            ]
        else:
            mock_narrative = (
                f"Mock response for: '{user_query}'. In production, this would analyze your programmatic "
                "data using Gemini and BigQuery to provide detailed insights on supply path performance, "
                "fill rates, markup transparency, and root cause analysis."
            )
            mock_data = [
                {'metric': 'sample_metric', 'value': 42.5},
                {'metric': 'another_metric', 'value': 78.3}
            ]

        return {
            'user_query': user_query,
            'timestamp': datetime.utcnow().isoformat(),
            'success': True,
            'sql_query': f"-- Mock SQL for: {user_query}\nSELECT * FROM mock_table LIMIT 10",
            'data': mock_data,
            'narrative': mock_narrative,
            'error': None,
            'metadata': {
                'mode': 'MOCK',
                'row_count': len(mock_data)
            }
        }
