"""
Database configuration for MotherDuck
"""
import os
from typing import Dict

# Database connection parameters
DB_CONFIG: Dict[str, str] = {
    'host': os.getenv('DB_HOST', 'localhost'),
    'port': os.getenv('DB_PORT', '5432'),
    'database': os.getenv('DB_NAME', 'transformer_db'),
    'user': os.getenv('DB_USER', 'postgres'),
    'password': os.getenv('DB_PASSWORD', '')
}

# Query templates
TRANSFORMER_DATA_QUERY = """
SELECT 
    timestamp,
    transformer_id,
    power_kw,
    power_kva,
    power_factor,
    voltage_v,
    current_a,
    loading_percentage
FROM transformer_data
WHERE transformer_id = ? 
  AND DATE(timestamp) = ?
  AND EXTRACT(HOUR FROM timestamp) = ?
ORDER BY timestamp
"""

CUSTOMER_DATA_QUERY = """
SELECT 
    timestamp,
    customer_id,
    transformer_id,
    power_kw,
    power_factor,
    voltage_v,
    current_a
FROM customer_data
WHERE transformer_id = ?
  AND DATE(timestamp) = ?
  AND EXTRACT(HOUR FROM timestamp) = ?
ORDER BY timestamp
"""

TRANSFORMER_LIST_QUERY = """
SELECT DISTINCT transformer_id
FROM transformer_data
ORDER BY transformer_id
"""

CUSTOMER_AGGREGATION_QUERY = """
WITH latest_data AS (
    SELECT 
        customer_id,
        transformer_id,
        power_kw,
        power_factor,
        voltage_v,
        current_a,
        ROW_NUMBER() OVER (PARTITION BY customer_id ORDER BY timestamp DESC) as rn
    FROM customer_data
    WHERE transformer_id = ?
      AND DATE(timestamp) = ?
      AND EXTRACT(HOUR FROM timestamp) = ?
)
SELECT 
    COUNT(DISTINCT customer_id) as customer_count,
    SUM(power_kw) as total_power_kw,
    AVG(power_factor) as avg_power_factor,
    SUM(current_a) as total_current_a
FROM latest_data
WHERE rn = 1
"""
