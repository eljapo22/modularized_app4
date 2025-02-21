"""
Database configuration for MotherDuck
"""
import os
from typing import Dict

# Query templates with different precision for transformer vs customer data
TRANSFORMER_DATA_QUERY = """
SELECT 
    "timestamp",
    "voltage_v",
    "size_kva",
    CAST("loading_percentage" AS DECIMAL(3,0)) as "loading_percentage",
    CAST("current_a" AS DECIMAL(5,2)) as "current_a",
    CAST("power_kw" AS DECIMAL(5,2)) as "power_kw",
    CAST("power_kva" AS DECIMAL(5,2)) as "power_kva",
    CAST("power_factor" AS DECIMAL(4,3)) as "power_factor",
    "transformer_id",
    "load_range"
FROM {table_name}
WHERE "transformer_id" = ? 
  AND DATE_TRUNC('day', "timestamp") = ?
ORDER BY "timestamp"
"""

CUSTOMER_DATA_QUERY = """
SELECT 
    CAST("current_a" AS DECIMAL(4,3)) as "current_a",
    "customer_id",
    "hour",
    CAST("power_factor" AS DECIMAL(4,3)) as "power_factor",
    CAST("power_kva" AS DECIMAL(4,3)) as "power_kva",
    CAST("power_kw" AS DECIMAL(4,3)) as "power_kw",
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
    CAST(AVG("power_kw") AS DECIMAL(4,3)) as avg_power_kw,
    CAST(MAX("power_kw") AS DECIMAL(4,3)) as max_power_kw,
    CAST(MIN("power_kw") AS DECIMAL(4,3)) as min_power_kw,
    CAST(AVG("power_factor") AS DECIMAL(4,3)) as avg_power_factor
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
    CAST("loading_percentage" AS DECIMAL(3,0)) as "loading_percentage",
    CAST("current_a" AS DECIMAL(5,2)) as "current_a",
    CAST("power_kw" AS DECIMAL(5,2)) as "power_kw",
    CAST("power_kva" AS DECIMAL(5,2)) as "power_kva",
    CAST("power_factor" AS DECIMAL(4,3)) as "power_factor",
    "transformer_id",
    "load_range"
FROM {table_name}
WHERE "transformer_id" = ? 
  AND "timestamp"::DATE BETWEEN ?::DATE AND ?::DATE
ORDER BY "timestamp"
"""
