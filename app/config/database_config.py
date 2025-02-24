"""
Database configuration for MotherDuck
"""
import os
from typing import Dict

# Query to get all transformers from a specific feeder
TRANSFORMER_LIST_QUERY = """
SELECT DISTINCT transformer_id 
FROM ModApp4DB.main."Transformer Feeder {}"
ORDER BY transformer_id;
"""

# Query to get transformer data with proper type casting
TRANSFORMER_DATA_QUERY = """
SELECT 
    t."timestamp",
    t."transformer_id",
    CAST(t."size_kva" AS DECIMAL(5,1)) as "size_kva",
    t."load_range",
    CAST(t."loading_percentage" AS DECIMAL(5,2)) as "loading_percentage",
    CAST(t."current_a" AS DECIMAL(6,2)) as "current_a",
    CAST(t."voltage_v" AS INTEGER) as "voltage_v",
    CAST(t."power_kw" AS DECIMAL(5,2)) as "power_kw",
    CAST(t."power_kva" AS DECIMAL(5,2)) as "power_kva",
    CAST(t."power_factor" AS DECIMAL(4,3)) as "power_factor"
FROM ModApp4DB.main."Transformer Feeder {}" t 
WHERE t."transformer_id" = ?
ORDER BY t."timestamp";
"""

# Query to get customer data with proper type casting
CUSTOMER_DATA_QUERY = """
WITH customer_data AS (
    SELECT 
        c."timestamp",
        c."customer_id",
        c."transformer_id",
        CAST(c."power_kw" AS DECIMAL(5,2)) as "power_kw",
        CAST(c."power_factor" AS DECIMAL(4,3)) as "power_factor",
        CAST(c."power_kva" AS DECIMAL(5,2)) as "power_kva",
        c."__index_level_0__",
        CAST(c."voltage_v" AS DECIMAL(5,1)) as "voltage_v",
        CAST(c."current_a" AS DECIMAL(5,2)) as "current_a"
    FROM ModApp4DB.main."Customer Feeder {}" c
    WHERE c."transformer_id" = ?
        AND c."timestamp" BETWEEN ?::timestamp AND ?::timestamp
)
SELECT *
FROM customer_data
ORDER BY "timestamp", "customer_id";
"""

# Query to get aggregated customer data
CUSTOMER_AGGREGATION_QUERY = """
WITH RECURSIVE hours AS (
    SELECT DATE_TRUNC('hour', ?::timestamp) as hour
    UNION ALL
    SELECT hour + INTERVAL '1 hour'
    FROM hours
    WHERE hour < DATE_TRUNC('hour', ?::timestamp)
),
customer_data AS (
    SELECT 
        c."timestamp",
        c."customer_id",
        CAST(c."power_kw" AS DECIMAL(5,2)) as "power_kw",
        CAST(c."power_factor" AS DECIMAL(4,3)) as "power_factor",
        CAST(c."power_kva" AS DECIMAL(5,2)) as "power_kva",
        CAST(c."voltage_v" AS DECIMAL(5,1)) as "voltage_v",
        CAST(c."current_a" AS DECIMAL(5,2)) as "current_a"
    FROM ModApp4DB.main."Customer Feeder {}" c
    WHERE c."transformer_id" = ?
)
SELECT 
    hours.hour as timestamp,
    c."customer_id",
    CAST(AVG(c."power_kw") AS DECIMAL(5,2)) as avg_power_kw,
    CAST(AVG(c."power_factor") AS DECIMAL(4,3)) as avg_power_factor,
    CAST(AVG(c."power_kva") AS DECIMAL(5,2)) as avg_power_kva,
    CAST(AVG(c."current_a") AS DECIMAL(5,2)) as avg_current_a,
    CAST(AVG(c."voltage_v") AS DECIMAL(5,1)) as avg_voltage_v
FROM hours
LEFT JOIN customer_data c 
    ON DATE_TRUNC('hour', c."timestamp") = hours.hour
GROUP BY hours.hour, c."customer_id"
ORDER BY hours.hour, c."customer_id";
"""

# Query to get feeder names
FEEDER_LIST_QUERY = """
SELECT DISTINCT table_name 
FROM information_schema.tables 
WHERE table_schema = 'main'
AND table_name LIKE 'Transformer Feeder _'
AND table_catalog = 'ModApp4DB'
ORDER BY table_name;
"""

# Constants for data validation
LOAD_RANGES = ["<50%", "50%-80%", "80%-100%", "100%-120%", ">120%"]
VOLTAGE_LEVEL = 400  # Standard voltage level in V
CUSTOMER_COUNT_MAP = {
    # Feeder 1
    "S1F1": {
        (1, 5): 20,    # ATF001-005: 20 customers
        (6, 12): 16,   # ATF006-012: 16 customers
        (13, 22): 12,  # ATF013-022: 12 customers
        (23, 65): 10,  # ATF023-065: 10 customers
        (66, 80): 20,  # ATF066-080: 20 customers
        (81, 90): 28   # ATF081-090: 28 customers
    },
    # Feeder 2
    "S1F2": {
        (1, 3): 20,    # ATF001-003: 20 customers
        (4, 12): 16,   # ATF004-012: 16 customers
        (13, 24): 12,  # ATF013-024: 12 customers
        (25, 73): 10,  # ATF025-073: 10 customers
        (74, 120): 8   # ATF074-120: 8 customers
    },
    # Feeder 3
    "S1F3": {
        (1, 2): 20,    # ATF001-002: 20 customers
        (3, 9): 16,    # ATF003-009: 16 customers
        (10, 17): 12,  # ATF010-017: 12 customers
        (18, 60): 10,  # ATF018-060: 10 customers
        (61, 80): 8    # ATF061-080: 8 customers
    },
    # Feeder 4
    "S1F4": {
        (1, 7): 20,    # ATF001-007: 20 customers
        (8, 17): 16,   # ATF008-017: 16 customers
        (18, 25): 12,  # ATF018-025: 12 customers
        (26, 61): 10,  # ATF026-061: 10 customers
        (62, 85): 8    # ATF062-085: 8 customers
    }
}
