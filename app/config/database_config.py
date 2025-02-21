"""
Database configuration for MotherDuck
"""
import os
from typing import Dict

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
    CAST(t."loading_percentage" AS DECIMAL(3,0)) as "loading_percentage",
    CAST(t."current_a" AS DECIMAL(5,2)) as "current_a",
    CAST(t."power_kw" AS DECIMAL(5,2)) as "power_kw",
    CAST(t."power_kva" AS DECIMAL(5,2)) as "power_kva",
    CAST(t."power_factor" AS DECIMAL(4,3)) as "power_factor",
    t."transformer_id",
    t."load_range"
FROM {table_name} t 
WHERE t."timestamp" BETWEEN ?::timestamp AND ?::timestamp
    AND t."transformer_id" = ?
ORDER BY t."timestamp"
"""

CUSTOMER_DATA_QUERY = """
SELECT 
    CAST(c."current_a" AS DECIMAL(5,2)) as "current_a",
    c."customer_id",
    EXTRACT(HOUR FROM c."timestamp") as "hour",
    CAST(c."power_factor" AS DECIMAL(4,3)) as "power_factor",
    CAST(c."power_kva" AS DECIMAL(5,2)) as "power_kva",
    CAST(c."power_kw" AS DECIMAL(5,2)) as "power_kw",
    c."size_kva",
    c."timestamp",
    c."transformer_id",
    c."voltage_v"
FROM {table_name} c 
WHERE c."timestamp" BETWEEN ?::timestamp AND ?::timestamp
    AND c."transformer_id" = ?
ORDER BY c."timestamp", c."customer_id"
"""

TRANSFORMER_LIST_QUERY = """
SELECT DISTINCT "transformer_id"
FROM {table_name}
ORDER BY "transformer_id"
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
