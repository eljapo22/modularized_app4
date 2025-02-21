"""
Database configuration for MotherDuck
"""
import os
from typing import Dict

# Query templates with proper rounding
TRANSFORMER_DATA_QUERY = """
SELECT 
    "timestamp",
    "voltage_v",
    "size_kva",
    ROUND("loading_percentage", 2) as "loading_percentage",
    ROUND("current_a", 2) as "current_a",
    ROUND("power_kw", 2) as "power_kw",
    "power_kva",
    "power_factor",
    "transformer_id",
    "load_range"
FROM {table_name}
WHERE "transformer_id" = ? 
  AND DATE_TRUNC('day', "timestamp") = ?
ORDER BY "timestamp"
"""

CUSTOMER_DATA_QUERY = """
SELECT 
    "index_level_0",
    ROUND("current_a", 1) as "current_a",
    "customer_id",
    "hour",
    "power_factor",
    ROUND("power_kva", 1) as "power_kva",
    ROUND("power_kw", 1) as "power_kw",
    "size_kva",
    "timestamp",
    "transformer_id",
    "voltage_v"
FROM {table_name}
WHERE "transformer_id" = ?
  AND "timestamp"::DATE BETWEEN ?::DATE AND ?::DATE
ORDER BY "timestamp", "customer_id"
"""

TRANSFORMER_LIST_QUERY = """
SELECT DISTINCT "transformer_id"
FROM {table_name}
ORDER BY "transformer_id"
"""

CUSTOMER_AGGREGATION_QUERY = """
SELECT 
    "timestamp"::DATE as date,
    "customer_id",
    AVG(ROUND("power_kw", 1)) as avg_power_kw,
    MAX(ROUND("power_kw", 1)) as max_power_kw,
    MIN(ROUND("power_kw", 1)) as min_power_kw,
    AVG(ROUND("power_factor", 2)) as avg_power_factor
FROM {table_name}
WHERE "transformer_id" = ?
  AND "timestamp"::DATE BETWEEN ?::DATE AND ?::DATE
GROUP BY "timestamp"::DATE, "customer_id"
ORDER BY "timestamp"::DATE, "customer_id"
"""

TRANSFORMER_DATA_RANGE_QUERY = """
SELECT 
    "timestamp",
    "voltage_v",
    "size_kva",
    ROUND("loading_percentage", 2) as "loading_percentage",
    ROUND("current_a", 2) as "current_a",
    ROUND("power_kw", 2) as "power_kw",
    "power_kva",
    "power_factor",
    "transformer_id",
    "load_range"
FROM {table_name}
WHERE "transformer_id" = ? 
  AND "timestamp"::DATE BETWEEN ?::DATE AND ?::DATE
ORDER BY "timestamp"
"""
