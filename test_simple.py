import duckdb
import os
import streamlit as st
import pandas as pd
pd.set_option('display.max_columns', None)
pd.set_option('display.width', None)

# Get token from secrets and set it
token = st.secrets["MOTHERDUCK_TOKEN"]
os.environ["motherduck_token"] = token

# Connect to MotherDuck
conn = duckdb.connect('md:ModApp4DB')

# Simple test query
query = """
SELECT 
    'Transformer Feeder 1' as source,
    COUNT(*) as row_count,
    COUNT(DISTINCT transformer_id) as unique_transformers,
    MIN(timestamp) as earliest,
    MAX(timestamp) as latest,
    AVG(loading_percentage) as avg_loading
FROM "Transformer Feeder 1"
"""

print("Running test query...")
print("-" * 50)

try:
    result = conn.execute(query).df()
    print("\nResult:")
    print(result)
except Exception as e:
    print(f"Error: {str(e)}")

print("\nDone!")
