"""
Database configuration for MotherDuck
"""
import os
from typing import Dict

# Query templates
TRANSFORMER_DATA_QUERY = """
SELECT 
    "timestamp",
    "transformer_id",
    "power_kw",
    "power_kva",
    "power_factor",
    "voltage_v",
    "current_a",
    "loading_percentage"
FROM {table_name}
WHERE "transformer_id" = ? 
  AND DATE_TRUNC('day', "timestamp") = ?
  AND EXTRACT(hour FROM "timestamp") = ?
ORDER BY "timestamp"
"""

CUSTOMER_DATA_QUERY = """
SELECT 
    "timestamp",
    "transformer_id",
    "customer_id",
    "power_kw",
    "power_factor",
    "voltage_v",
    "current_a"
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
        "power_kw",
        "power_factor",
        "voltage_v",
        "current_a",
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
