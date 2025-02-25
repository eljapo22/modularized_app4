"""
Database configuration for MotherDuck
"""
import os
from typing import Dict, List

# Table templates
TRANSFORMER_TABLE_TEMPLATE = "transformer_data_feeder_{}"
CUSTOMER_TABLE_TEMPLATE = "customer_data_feeder_{}"

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
SELECT 
    t."timestamp",
    t."voltage_v",
    t."size_kva",
    t."loading_percentage",
    t."current_a",
    t."power_kw",
    t."power_kva",
    t."power_factor",
    t."transformer_id",
    t."load_range"
FROM {table_name} t 
WHERE t."transformer_id" = ?
  AND t."timestamp" >= ?
  AND t."timestamp" <= ?
ORDER BY t."timestamp"
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
    CAST(COALESCE(c."current_a", LAG(c."current_a") OVER (PARTITION BY c."customer_id" ORDER BY hours.hour)) AS DECIMAL(5,2)) as "current_a",
    c."customer_id",
    EXTRACT(HOUR FROM hours.hour) as "hour",
    CAST(COALESCE(c."power_factor", LAG(c."power_factor") OVER (PARTITION BY c."customer_id" ORDER BY hours.hour)) AS DECIMAL(4,3)) as "power_factor",
    CAST(COALESCE(c."power_kva", LAG(c."power_kva") OVER (PARTITION BY c."customer_id" ORDER BY hours.hour)) AS DECIMAL(5,2)) as "power_kva",
    CAST(COALESCE(c."power_kw", LAG(c."power_kw") OVER (PARTITION BY c."customer_id" ORDER BY hours.hour)) AS DECIMAL(5,2)) as "power_kw",
    c."size_kva",
    hours.hour as "timestamp",
    c."transformer_id",
    COALESCE(c."voltage_v", LAG(c."voltage_v") OVER (PARTITION BY c."customer_id" ORDER BY hours.hour)) as "voltage_v"
FROM hours
LEFT JOIN {table_name} c ON c."timestamp" = hours.hour AND c."transformer_id" = ?
WHERE hours.hour::DATE BETWEEN ?::DATE AND ?::DATE
ORDER BY hours.hour, c."customer_id"
"""

TRANSFORMER_LIST_QUERY = """
SELECT DISTINCT transformer_id
FROM {table_name}
ORDER BY transformer_id;
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

# Query to get feeder names
FEEDER_LIST_QUERY = """
SELECT DISTINCT table_name 
FROM information_schema.tables 
WHERE table_schema = 'main'
AND table_name LIKE 'Transformer Feeder %'
AND table_catalog = 'ModApp4DB'
ORDER BY table_name;
"""

def init_db_pool():
    """Initialize database connection pool"""
    pass  # Placeholder for actual implementation

def execute_query(query: str, params: tuple = None) -> List[Dict]:
    """Execute a query with optional parameters"""
    pass  # Placeholder for actual implementation
