"""
Database connection configuration
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
    power_factor,
    power_kva,
    voltage_v,
    current_a,
    index_level_0_
FROM {table_name}
WHERE transformer_id = %s
    AND DATE(timestamp) = %s
    AND EXTRACT(HOUR FROM timestamp) = %s
ORDER BY timestamp;
"""

CUSTOMER_DATA_QUERY = """
SELECT 
    timestamp,
    customer_id,
    transformer_id,
    power_kw,
    power_factor,
    power_kva,
    voltage_v,
    current_a,
    index_level_0_
FROM {table_name}
WHERE transformer_id = %s
    AND DATE(timestamp) = %s
    AND EXTRACT(HOUR FROM timestamp) = %s
ORDER BY timestamp;
"""

TRANSFORMER_LIST_QUERY = """
SELECT DISTINCT transformer_id
FROM {table_name}
ORDER BY transformer_id;
"""

CUSTOMER_AGGREGATION_QUERY = """
SELECT 
    transformer_id,
    COUNT(DISTINCT customer_id) as customer_count,
    SUM(power_kw) as total_power_kw,
    AVG(power_factor) as avg_power_factor,
    SUM(power_kva) as total_power_kva,
    AVG(voltage_v) as avg_voltage_v,
    SUM(current_a) as total_current_a
FROM {table_name}
WHERE transformer_id = %s
    AND DATE(timestamp) = %s
    AND EXTRACT(HOUR FROM timestamp) = %s
GROUP BY transformer_id;
"""
