"""
Database configuration for MotherDuck
"""
import os
from typing import Dict

# Query for transformer data
TRANSFORMER_DATA_QUERY = """
SELECT 
    t."timestamp",
    t."voltage_v",
    t."size_kva",
    CAST(t."loading_percentage" AS DECIMAL(3,0)) AS "loading_percentage",
    CAST(t."current_a" AS DECIMAL(5,2)) AS "current_a",
    CAST(t."power_kw" AS DECIMAL(5,2)) AS "power_kw",
    CAST(t."power_kva" AS DECIMAL(5,2)) AS "power_kva",
    CAST(t."power_factor" AS DECIMAL(4,3)) AS "power_factor",
    t."transformer_id",
    t."load_range"
FROM {table_name} t
WHERE t."transformer_id" = ?
  AND t."loading_percentage" IS NOT NULL
ORDER BY t."timestamp";
"""

# Query for transformer data within a date range
TRANSFORMER_DATA_RANGE_QUERY = """
SELECT 
    t."timestamp",
    t."voltage_v",
    t."size_kva",
    CAST(t."loading_percentage" AS DECIMAL(3,0)) AS "loading_percentage",
    CAST(t."current_a" AS DECIMAL(5,2)) AS "current_a",
    CAST(t."power_kw" AS DECIMAL(5,2)) AS "power_kw",
    CAST(t."power_kva" AS DECIMAL(5,2)) AS "power_kva",
    CAST(t."power_factor" AS DECIMAL(4,3)) AS "power_factor",
    t."transformer_id",
    t."load_range"
FROM {table_name} t 
WHERE t."transformer_id" = ?
  AND t."timestamp" BETWEEN ? AND ?
  AND t."loading_percentage" IS NOT NULL
ORDER BY t."timestamp";
"""

# Query for hourly customer data
CUSTOMER_DATA_QUERY = """
SELECT 
    c."timestamp",
    c."customer_id",
    EXTRACT(HOUR FROM c."timestamp") AS "hour",
    CAST(c."power_factor" AS DECIMAL(4,3)) AS "power_factor",
    CAST(c."power_kva" AS DECIMAL(5,2)) AS "power_kva",
    CAST(c."power_kw" AS DECIMAL(5,2)) AS "power_kw",
    c."size_kva",
    c."transformer_id",
    c."voltage_v",
    CAST(c."current_a" AS DECIMAL(5,2)) AS "current_a"
FROM {table_name} c
WHERE c."transformer_id" = ?
  AND c."timestamp" BETWEEN ? AND ?
ORDER BY c."timestamp", c."customer_id";
"""

# Query to retrieve distinct transformer IDs
TRANSFORMER_LIST_QUERY = """
SELECT DISTINCT "transformer_id"
FROM {table_name}
ORDER BY "transformer_id";
"""

# Query for daily customer power statistics
CUSTOMER_AGGREGATION_QUERY = """
SELECT 
    DATE(c."timestamp") AS date,
    c."customer_id",
    CAST(AVG(c."power_kw") AS DECIMAL(4,3)) AS avg_power_kw,
    CAST(MAX(c."power_kw") AS DECIMAL(4,3)) AS max_power_kw,
    CAST(MIN(c."power_kw") AS DECIMAL(4,3)) AS min_power_kw,
    CAST(AVG(c."power_factor") AS DECIMAL(4,3)) AS avg_power_factor
FROM {table_name} c
WHERE c."transformer_id" = ?
  AND c."timestamp" BETWEEN ? AND ?
GROUP BY DATE(c."timestamp"), c."customer_id"
ORDER BY DATE(c."timestamp"), c."customer_id";
"""

# Query to get feeder names from MotherDuck
FEEDER_LIST_QUERY = """
SELECT DISTINCT table_name 
FROM information_schema.tables 
WHERE table_schema = 'main'
AND table_name LIKE 'Transformer Feeder %'
AND table_catalog = 'ModApp4DB'
ORDER BY table_name;
"""
