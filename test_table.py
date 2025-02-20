import duckdb
import os
import streamlit as st

# Get token from secrets and set it
token = st.secrets["MOTHERDUCK_TOKEN"]
os.environ["motherduck_token"] = token

# Connect to MotherDuck
conn = duckdb.connect('md:ModApp4DB')

# Test query based on exact schema from screenshots
query = """
SELECT 
    current_a,
    load_range,
    loading_percentage,
    power_factor,
    power_kva,
    power_kw,
    size_kva,
    timestamp,
    transformer_id,
    voltage_v
FROM "Transformer Feeder 1"
LIMIT 5;
"""

print("Testing Transformer Feeder 1 schema...")
print("-" * 50)

try:
    result = conn.execute(query).df()
    print("\nColumns and data types:")
    print(result.dtypes)
    print("\nSample data:")
    print(result)
except Exception as e:
    print(f"Error: {str(e)}")

print("\nDone!")
