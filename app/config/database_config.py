"""
Database configuration for MotherDuck
"""
import os
from typing import Dict, List
import duckdb
import logging
import pandas as pd
from datetime import datetime, date
import streamlit as st

# Get logger for this module
logger = logging.getLogger(__name__)

# Table templates
TRANSFORMER_TABLE_TEMPLATE = "Transformer Feeder {}"
CUSTOMER_TABLE_TEMPLATE = "Customer Feeder {}"

# Available feeder numbers
FEEDER_NUMBERS = [1, 2, 3, 4, 5]

# Decimal places for numeric columns
DECIMAL_PLACES = {
    'voltage_v': 0,
    'size_kva': 0,
    'loading_percentage': 0,
    'current_a': 2,
    'power_kw': 2,
    'power_kva': 2,
    'power_factor': 3
}

# Query templates with different precision for transformer vs customer data
TRANSFORMER_DATA_QUERY = """
WITH RECURSIVE hours AS (
    SELECT DATE_TRUNC('hour', ?::timestamp) as hour
    UNION ALL
    SELECT hour + INTERVAL '1 hour'
    FROM hours
    WHERE hour < DATE_TRUNC('hour', ?::timestamp + INTERVAL '1 day')
)
SELECT 
    hours.hour as "timestamp",
    COALESCE(t."voltage_v", LAG(t."voltage_v") OVER (ORDER BY hours.hour)) as "voltage_v",
    t."size_kva",
    CAST(COALESCE(t."loading_percentage", LAG(t."loading_percentage") OVER (ORDER BY hours.hour)) AS DECIMAL(3,0)) as "loading_percentage",
    CAST(COALESCE(t."current_a", LAG(t."current_a") OVER (ORDER BY hours.hour)) AS DECIMAL(5,2)) as "current_a",
    CAST(COALESCE(t."power_kw", LAG(t."power_kw") OVER (ORDER BY hours.hour)) AS DECIMAL(5,2)) as "power_kw",
    CAST(COALESCE(t."power_kva", LAG(t."power_kva") OVER (ORDER BY hours.hour)) AS DECIMAL(5,2)) as "power_kva",
    CAST(COALESCE(t."power_factor", LAG(t."power_factor") OVER (ORDER BY hours.hour)) AS DECIMAL(4,3)) as "power_factor",
    t."transformer_id",
    t."load_range"
FROM hours
LEFT JOIN {table_name} t ON t."timestamp" = hours.hour AND t."transformer_id" = ?
ORDER BY hours.hour
"""

TRANSFORMER_DATA_RANGE_QUERY = """
WITH RECURSIVE hours AS (
    SELECT DATE_TRUNC('hour', ?::timestamp) as hour
    UNION ALL
    SELECT hour + INTERVAL '1 hour'
    FROM hours
    WHERE hour < DATE_TRUNC('hour', ?::timestamp + INTERVAL '1 day')
)
SELECT 
    hours.hour as "timestamp",
    t."transformer_id",
    CAST(COALESCE(t."power_kw", LAG(t."power_kw") OVER (ORDER BY hours.hour)) AS DECIMAL(5,2)) as "power_kw",
    CAST(COALESCE(t."loading_percentage", LAG(t."loading_percentage") OVER (ORDER BY hours.hour)) AS DECIMAL(3,0)) as "loading_percentage"
FROM hours
LEFT JOIN {table_name} t ON t."timestamp" = hours.hour AND t."transformer_id" = ?
WHERE hours.hour::DATE BETWEEN ?::DATE AND ?::DATE
ORDER BY hours.hour
"""

TRANSFORMER_LIST_QUERY = """
SELECT DISTINCT transformer_id 
FROM {table_name}
ORDER BY transformer_id
"""

CUSTOMER_DATA_QUERY_NEW = """
SELECT 
    c."timestamp",
    c."customer_id",
    c."consumption_kwh",
    c."demand_kw",
    c."power_factor",
    c."transformer_id"
FROM {table_name} c
WHERE c."transformer_id" = ?
  AND c."timestamp" >= ?
  AND c."timestamp" <= ?
ORDER BY c."timestamp", c."customer_id"
"""

CUSTOMER_AGGREGATION_QUERY_NEW = """
SELECT 
    DATE_TRUNC('hour', c."timestamp") as hour,
    COUNT(DISTINCT c."customer_id") as customer_count,
    SUM(c."consumption_kwh") as total_consumption_kwh,
    AVG(c."demand_kw") as avg_demand_kw,
    AVG(c."power_factor") as avg_power_factor
FROM {table_name} c
WHERE c."transformer_id" = ?
  AND c."timestamp" >= ?
  AND c."timestamp" <= ?
GROUP BY DATE_TRUNC('hour', c."timestamp")
ORDER BY hour
"""

CUSTOMER_AGGREGATION_QUERY = """
WITH RECURSIVE hours AS (
    SELECT DATE_TRUNC('hour', ?::timestamp) as hour
    UNION ALL
    SELECT hour + INTERVAL '1 hour'
    FROM hours
    WHERE hour < DATE_TRUNC('hour', ?::timestamp + INTERVAL '1 day')
)
SELECT 
    hours.hour::DATE as date,
    c."customer_id",
    CAST(AVG(c."power_kw") AS DECIMAL(4,3)) as avg_power_kw,
    CAST(MAX(c."power_kw") AS DECIMAL(4,3)) as max_power_kw,
    CAST(MIN(c."power_kw") AS DECIMAL(4,3)) as min_power_kw,
    CAST(AVG(c."power_factor") AS DECIMAL(4,3)) as avg_power_factor
FROM hours
LEFT JOIN {table_name} c ON c."timestamp" = hours.hour AND c."transformer_id" = ?
WHERE hours.hour::DATE BETWEEN ?::DATE AND ?::DATE
GROUP BY hours.hour::DATE, c."customer_id"
ORDER BY hours.hour::DATE, c."customer_id"
"""

CUSTOMER_DATA_QUERY = """
WITH RECURSIVE hours AS (
    SELECT DATE_TRUNC('hour', ?::timestamp) as hour
    UNION ALL
    SELECT hour + INTERVAL '1 hour'
    FROM hours
    WHERE hour < DATE_TRUNC('hour', ?::timestamp + INTERVAL '1 day')
)
SELECT 
    hours.hour as "timestamp",
    c."customer_id",
    CAST(COALESCE(cr."power_kw", LAG(cr."power_kw") OVER (ORDER BY hours.hour)) AS DECIMAL(5,2)) as "power_kw",
    CAST(COALESCE(cr."current_a", LAG(cr."current_a") OVER (ORDER BY hours.hour)) AS DECIMAL(5,2)) as "current_a",
    CAST(COALESCE(cr."power_factor", LAG(cr."power_factor") OVER (ORDER BY hours.hour)) AS DECIMAL(4,3)) as "power_factor",
    c."service_type"
FROM hours
LEFT JOIN {customer_table} c ON c."transformer_id" = ?
LEFT JOIN {reading_table} cr ON cr."customer_id" = c."customer_id" AND cr."timestamp" = hours.hour
WHERE hours.hour::DATE BETWEEN ?::DATE AND ?::DATE
ORDER BY hours.hour, c."customer_id"
"""

# Query to get feeder names
FEEDER_LIST_QUERY = """
SELECT DISTINCT table_name 
FROM information_schema.tables 
WHERE table_schema = 'main'
AND table_name LIKE 'Transformer Feeder %'
AND table_catalog = 'ModApp4DB'
ORDER BY table_name;
"""

# Database connection
_connection = None

def init_db_pool():
    """Initialize database connection pool"""
    global _connection
    try:
        # Connect to MotherDuck
        token = None
        if hasattr(st, 'secrets'):
            token = st.secrets.get('MOTHERDUCK_TOKEN')
        if not token:
            token = os.getenv('MOTHERDUCK_TOKEN')
        if not token:
            raise ValueError("MotherDuck token not found in secrets or environment")
            
        _connection = duckdb.connect(f'md:ModApp4DB?motherduck_token={token}')
        return True
    except Exception as e:
        logger.error(f"Error initializing database: {str(e)}")
        return False

def execute_query(query: str, params: tuple = None) -> List[Dict]:
    """Execute a query with optional parameters"""
    global _connection
    try:
        if not _connection:
            init_db_pool()
            
        if not _connection:
            raise ValueError("No database connection")
            
        # Execute query
        if params:
            result = _connection.execute(query, params).fetchall()
        else:
            result = _connection.execute(query).fetchall()
            
        # Convert to list of dicts
        if result:
            columns = [desc[0] for desc in _connection.description]
            return [dict(zip(columns, row)) for row in result]
        return []
        
    except Exception as e:
        logger.error(f"Error executing query: {str(e)}")
        return []

def get_transformer_data(transformer_id: str, query_date: date, hour: int = None, feeder: int = None) -> pd.DataFrame:
    """Get transformer data for a specific transformer and date"""
    try:
        if feeder not in FEEDER_NUMBERS:
            logger.error(f"Invalid feeder number: {feeder}")
            return pd.DataFrame()
            
        # Use the correct table name format
        table = f'"Transformer Feeder {feeder}"'
        
        # Build query parameters
        if hour is not None:
            query_time = datetime.combine(query_date, datetime.min.time().replace(hour=hour))
        else:
            query_time = datetime.combine(query_date, datetime.min.time())
            
        # Execute query
        query = TRANSFORMER_DATA_QUERY.format(table_name=table)
        results = execute_query(query, (transformer_id, query_time))
        
        if not results:
            logger.warning(f"No data found for transformer {transformer_id}")
            return pd.DataFrame()
            
        return pd.DataFrame(results)
        
    except Exception as e:
        logger.error(f"Error getting transformer data: {str(e)}")
        return pd.DataFrame()

def get_transformer_data_range(transformer_id: str, start_date: date, end_date: date, feeder: int = None) -> pd.DataFrame:
    """Get transformer data for a date range"""
    try:
        # Extract feeder number if not provided
        if feeder is None:
            try:
                feeder = int(transformer_id[3])
            except (IndexError, ValueError):
                logger.error(f"Could not extract feeder number from transformer ID: {transformer_id}")
                return pd.DataFrame()

        # Validate feeder number
        if feeder not in FEEDER_NUMBERS:
            logger.error(f"Invalid feeder number: Feeder {feeder}")
            return pd.DataFrame()

        # Get table name
        table = f'"{TRANSFORMER_TABLE_TEMPLATE.format(feeder)}"'
        
        # Execute query with all required parameters
        query = TRANSFORMER_DATA_RANGE_QUERY.format(table_name=table)
        params = (
            start_date,  # First timestamp for hours CTE
            end_date,    # Second timestamp for hours CTE
            transformer_id,  # For JOIN condition
            start_date,  # For WHERE clause start
            end_date     # For WHERE clause end
        )
        
        results = execute_query(query, params)
        
        if not results:
            logger.warning(f"No data found for transformer {transformer_id}")
            return pd.DataFrame()
            
        return pd.DataFrame(results)
        
    except Exception as e:
        logger.error(f"Error getting transformer data: {str(e)}")
        return pd.DataFrame()

def get_transformer_ids(feeder: int) -> List[str]:
    """Get list of transformer IDs for a specific feeder"""
    try:
        if feeder not in FEEDER_NUMBERS:
            logger.error(f"Invalid feeder number: {feeder}")
            return []
            
        # Use the correct table name format
        table = f'"Transformer Feeder {feeder}"'
        
        # Execute query
        query = TRANSFORMER_LIST_QUERY.format(table_name=table)
        results = execute_query(query)
        
        if not results:
            logger.warning(f"No transformers found for feeder {feeder}")
            return []
            
        return sorted([r['transformer_id'] for r in results])
        
    except Exception as e:
        logger.error(f"Error getting transformer IDs: {str(e)}")
        return []

def get_customer_data(transformer_id: str, start_date: date, end_date: date, feeder: int = None) -> pd.DataFrame:
    """Get customer data for a specific transformer and date range"""
    try:
        # Extract feeder number if not provided
        if feeder is None:
            try:
                feeder = int(transformer_id[3])
            except (IndexError, ValueError):
                logger.error(f"Could not extract feeder number from transformer ID: {transformer_id}")
                return pd.DataFrame()

        # Validate feeder number
        if feeder not in FEEDER_NUMBERS:
            logger.error(f"Invalid feeder number: Feeder {feeder}")
            return pd.DataFrame()

        # Get table names
        customer_table = f'"{CUSTOMER_TABLE_TEMPLATE.format(feeder)}"'
        reading_table = f'"Customer Feeder {feeder}"'
        
        # Execute query with all required parameters
        query = CUSTOMER_DATA_QUERY.format(customer_table=customer_table, reading_table=reading_table)
        params = (
            start_date,  # For hours CTE
            end_date,    # For hours CTE
            transformer_id  # For customer table JOIN
        )
        
        results = execute_query(query, params)
        
        if not results:
            logger.warning(f"No customer data found for transformer {transformer_id}")
            return pd.DataFrame()
            
        return pd.DataFrame(results)
        
    except Exception as e:
        logger.error(f"Error getting customer data: {str(e)}")
        return pd.DataFrame()

# Initialize database connection pool
init_db_pool()
