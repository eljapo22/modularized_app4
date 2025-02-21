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
  AND EXTRACT(hour FROM "timestamp") = ?
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
  AND DATE_TRUNC('day', "timestamp") = ?
  AND EXTRACT(hour FROM "timestamp") = ?
ORDER BY "timestamp"
"""

TRANSFORMER_LIST_QUERY = """
SELECT DISTINCT "transformer_id"
FROM {table_name}
ORDER BY "transformer_id"
"""

CUSTOMER_AGGREGATION_QUERY = """
WITH latest_data AS (
    SELECT 
        "customer_id",
        "transformer_id",
        ROUND("power_kw", 1) as "power_kw",
        "power_factor",
        "voltage_v",
        ROUND("current_a", 1) as "current_a",
        ROW_NUMBER() OVER (PARTITION BY "customer_id" ORDER BY "timestamp" DESC) as rn
    FROM {table_name}
    WHERE "transformer_id" = ?
      AND DATE_TRUNC('day', "timestamp") = ?
      AND EXTRACT(hour FROM "timestamp") = ?
)
SELECT 
    COUNT(DISTINCT "customer_id") as customer_count,
    SUM("power_kw") as total_power_kw,
    AVG("power_factor") as avg_power_factor,
    SUM("current_a") as total_current_a
FROM latest_data
WHERE rn = 1
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
  AND DATE_TRUNC('day', "timestamp") >= ?
  AND DATE_TRUNC('day', "timestamp") <= ?
ORDER BY "timestamp"
"""
