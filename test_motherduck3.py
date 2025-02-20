import duckdb
import os

try:
    print("Setting environment variable...")
    os.environ['motherduck_token'] = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJlbWFpbCI6ImpobmFwbzIyMTNAZ21haWwuY29tIiwic2Vzc2lvbiI6ImpobmFwbzIyMTMuZ21haWwuY29tIiwicGF0IjoiMFBiVDRqY2p3WTQtMGQxOXdEUmJfNlE0NXM1WWgtZlZTYkItX2hQVUJKWSIsInVzZXJJZCI6IjI4Mzg5MGMwLTZhYmEtNDIyZi04OTI1LWQyNTg0YjJiZmU1NiIsImlzcyI6Im1kX3BhdCIsInJlYWRPbmx5IjpmYWxzZSwidG9rZW5UeXBlIjoicmVhZF93cml0ZSIsImlhdCI6MTczOTk0NDc5MH0.XpT3PzKgOTz6pVlFXcxb9AXpjyc9yuhvmZxmaPXH6c"
    
    print("\nCreating database and tables...")
    # Connect to MotherDuck with database creation
    conn = duckdb.connect('md:ModApp4DB?motherduck_token=' + os.environ['motherduck_token'])
    
    # Create transformer_readings table
    conn.execute("""
        CREATE TABLE IF NOT EXISTS transformer_readings (
            timestamp TIMESTAMP,
            transformer_id VARCHAR,
            power_kw FLOAT,
            current_a FLOAT,
            voltage_v FLOAT,
            power_factor FLOAT,
            size_kva FLOAT,
            loading_percentage FLOAT,
            feeder_id INTEGER
        );
    """)
    
    # Create customer_readings table
    conn.execute("""
        CREATE TABLE IF NOT EXISTS customer_readings (
            timestamp TIMESTAMP,
            transformer_id VARCHAR,
            customer_id VARCHAR,
            consumption_kwh FLOAT,
            peak_demand_kw FLOAT,
            power_factor FLOAT,
            connection_type VARCHAR
        );
    """)
    
    print("Tables created successfully!")
    
    print("\nListing tables...")
    tables = conn.execute('SHOW TABLES').fetchdf()
    print(tables)
    
except Exception as e:
    print(f"Error: {str(e)}")
finally:
    if 'conn' in locals():
        conn.close()
