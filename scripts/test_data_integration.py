"""
Test script to verify data integration from MotherDuck
"""
import duckdb
import toml
import os
from pathlib import Path
from datetime import datetime, timedelta

# Load secrets
secrets_path = Path('.streamlit/secrets.toml')
secrets = toml.load(secrets_path)
token = secrets['MOTHERDUCK_TOKEN']

# Set token in environment
os.environ["motherduck_token"] = token

# Connect directly to MotherDuck
conn = duckdb.connect('md:')

def test_transformer_data():
    """Test transformer data retrieval"""
    print("\nTesting Transformer Data:")
    query = """
    SELECT COUNT(DISTINCT transformer_id) as transformer_count,
           MIN(timestamp) as min_date,
           MAX(timestamp) as max_date
    FROM "Transformer Feeder 1"
    """
    result = conn.execute(query).fetchone()
    print(f"Feeder 1: {result[0]} transformers, Date range: {result[1]} to {result[2]}")

def test_customer_data():
    """Test customer data retrieval"""
    print("\nTesting Customer Data:")
    for feeder in range(1, 5):
        query = f"""
        SELECT COUNT(DISTINCT customer_id) as customer_count,
               COUNT(DISTINCT transformer_id) as transformer_count
        FROM "Customer Feeder {feeder}"
        """
        result = conn.execute(query).fetchone()
        print(f"Feeder {feeder}: {result[0]} customers across {result[1]} transformers")

def test_data_alignment():
    """Test alignment between transformer and customer data"""
    print("\nTesting Data Alignment:")
    query = """
    WITH transformer_counts AS (
        SELECT 'Feeder 1' as feeder, COUNT(DISTINCT transformer_id) as t_count 
        FROM "Transformer Feeder 1"
        UNION ALL
        SELECT 'Feeder 2', COUNT(DISTINCT transformer_id) 
        FROM "Transformer Feeder 2"
        UNION ALL
        SELECT 'Feeder 3', COUNT(DISTINCT transformer_id) 
        FROM "Transformer Feeder 3"
        UNION ALL
        SELECT 'Feeder 4', COUNT(DISTINCT transformer_id) 
        FROM "Transformer Feeder 4"
    ),
    customer_counts AS (
        SELECT 'Feeder 1' as feeder, COUNT(DISTINCT transformer_id) as c_count 
        FROM "Customer Feeder 1"
        UNION ALL
        SELECT 'Feeder 2', COUNT(DISTINCT transformer_id)
        FROM "Customer Feeder 2"
        UNION ALL
        SELECT 'Feeder 3', COUNT(DISTINCT transformer_id)
        FROM "Customer Feeder 3"
        UNION ALL
        SELECT 'Feeder 4', COUNT(DISTINCT transformer_id)
        FROM "Customer Feeder 4"
    )
    SELECT 
        t.feeder,
        t.t_count as transformer_count,
        c.c_count as customer_transformer_count,
        CASE 
            WHEN t.t_count = c.c_count THEN 'OK'
            ELSE 'MISMATCH'
        END as status
    FROM transformer_counts t
    JOIN customer_counts c ON t.feeder = c.feeder
    """
    results = conn.execute(query).fetchall()
    for row in results:
        print(f"{row[0]}: {row[1]} transformers (data table) vs {row[2]} transformers (customer table) - {row[3]}")

def test_sample_transformer():
    """Test detailed data for one transformer"""
    print("\nTesting Sample Transformer (S1F2ATF001):")
    query = """
    SELECT 
        timestamp,
        transformer_id,
        size_kva,
        load_range,
        loading_percentage,
        current_a,
        voltage_v,
        power_kw,
        power_kva,
        power_factor
    FROM "Transformer Feeder 2"
    WHERE transformer_id = 'S1F2ATF001'
    ORDER BY timestamp
    LIMIT 5
    """
    results = conn.execute(query).fetchall()
    for row in results:
        print(f"Time: {row[0]}, Load: {row[4]}%, Power: {row[7]} kW, PF: {row[9]}")

if __name__ == "__main__":
    print("Testing MotherDuck Data Integration")
    print("=" * 50)
    
    try:
        test_transformer_data()
        test_customer_data()
        test_data_alignment()
        test_sample_transformer()
        print("\nAll tests completed successfully!")
    except Exception as e:
        print(f"\nError during testing: {e}")
    finally:
        conn.close()
