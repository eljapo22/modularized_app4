import duckdb
import streamlit as st

print("Testing MotherDuck connection...")

# Your token
token = 'eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJlbWFpbCI6ImpobmFwbzIyMTNAZ21haWwuY29tIiwic2Vzc2lvbiI6ImpobmFwbzIyMTMuZ21haWwuY29tIiwicGF0IjoiMFBiVDRqY2p3WTQtMGQxOXdEUmJfNlE0NXM1WWgtZlZTYkItX2hQVUJKWSIsInVzZXJJZCI6IjI4Mzg5MGMwLTZhYmEtNDIyZi04OTI1LWQyNTg0YjJiZmU1NiIsImlzcyI6Im1kX3BhdCIsInJlYWRPbmx5IjpmYWxzZSwidG9rZW5UeXBlIjoicmVhZF93cml0ZSIsImlhdCI6MTczOTk0NDc5MH0.XpT3PzKgOTz6pVlFXcxb9AXpjyc9yuhvmZxmaPXH6c'

try:
    # Connect directly to MotherDuck
    print("Connecting to MotherDuck...")
    conn = duckdb.connect(f'md:?motherduck_token={token}')
    
    # List all databases
    print("\nListing all databases:")
    result = conn.execute("SHOW DATABASES").fetchdf()
    print(result)
    
    # Try to list tables in the processed_data schema
    print("\nTrying to list tables in processed_data schema:")
    result = conn.execute("SHOW TABLES").fetchdf()
    print(result)
    
except Exception as e:
    print(f"Error: {str(e)}")
