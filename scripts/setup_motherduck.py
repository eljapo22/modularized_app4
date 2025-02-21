import duckdb
import streamlit as st
import pandas as pd
from io import StringIO

print("Setting up MotherDuck database...")

try:
    # Connect to DuckDB with MotherDuck token from Streamlit secrets
    print("1. Connecting to DuckDB...")
    motherduck_token = st.secrets["MOTHERDUCK_TOKEN"]
    con = duckdb.connect(f'md:?motherduck_token={motherduck_token}')
    
    # Drop existing table if it exists
    print("\n2. Dropping existing table if it exists...")
    con.execute('DROP TABLE IF EXISTS "Transformer Feeder 1"')
    
    # Create the transformer table if it doesn't exist
    print("\n3. Creating Transformer Feeder 1 table...")
    con.execute("""
        CREATE TABLE "Transformer Feeder 1" (
            timestamp TIMESTAMP,
            transformer_id VARCHAR,
            size_kva DOUBLE,
            load_range VARCHAR,
            loading_percentage DOUBLE,
            current_a DOUBLE,
            voltage_v DOUBLE,
            power_kw DOUBLE,
            power_kva DOUBLE,
            power_factor DOUBLE,
            PRIMARY KEY (transformer_id, timestamp)
        )
    """)
    
    # Sample data
    sample_data = """timestamp	transformer_id	size_kva	load_range	loading_percentage	current_a	voltage_v	power_kw	power_kva	power_factor
2024-01-01 00:00:00	S1F1ATF001	75.0	50%-80%	56.05	90.68	400	33.63	36.27	0.927
2024-01-01 01:00:00	S1F1ATF001	75.0	50%-80%	55.33	91.17	400	33.2	36.47	0.91
2024-01-01 02:00:00	S1F1ATF001	75.0	50%-80%	54.45	89.98	400	32.67	35.99	0.908"""
    
    # Convert sample data to DataFrame
    df = pd.read_csv(StringIO(sample_data), sep='\t')
    df['timestamp'] = pd.to_datetime(df['timestamp'])
    
    # Insert sample data
    print("\n4. Inserting sample data...")
    con.execute('INSERT INTO "Transformer Feeder 1" SELECT * FROM df')
    
    # Verify data
    print("\n5. Verifying data...")
    result = con.execute('SELECT * FROM "Transformer Feeder 1" LIMIT 3').fetchdf()
    print("\nSample data in table:")
    print(result)
    
    print("\nSetup completed successfully!")
    
except Exception as e:
    print(f"Error during setup: {str(e)}")
finally:
    if 'con' in locals():
        con.close()
