import duckdb
import os

def check_duckdb_version():
    version = duckdb.__version__
    print(f"DuckDB version: {version}")
    return version

try:
    # Check DuckDB version
    version = check_duckdb_version()
    if version != "1.2.0":
        print("Warning: You're not using DuckDB 1.2.0")
    
    # Set token in environment
    token = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJlbWFpbCI6ImpobmFwbzIyMTNAZ21haWwuY29tIiwic2Vzc2lvbiI6ImpobmFwbzIyMTMuZ21haWwuY29tIiwicGF0IjoiMFBiVDRqY2p3WTQtMGQxOXdEUmJfNlE0NXM1WWgtZlZTYkItX2hQVUJKWSIsInVzZXJJZCI6IjI4Mzg5MGMwLTZhYmEtNDIyZi04OTI1LWQyNTg0YjJiZmU1NiIsImlzcyI6Im1kX3BhdCIsInJlYWRPbmx5IjpmYWxzZSwidG9rZW5UeXBlIjoicmVhZF93cml0ZSIsImlhdCI6MTczOTk0NDc5MH0.XpT3PzKgOTz6pVlFXcxb9AXpjyc9yuhvmZxmaPXH6c"
    os.environ['motherduck_token'] = token
    
    print("\nConnecting directly to ModApp4DB...")
    # Connect directly to the database
    conn = duckdb.connect('md:ModApp4DB')
    
    print("\nListing tables...")
    tables = conn.execute('SHOW TABLES;').fetchdf()
    print(tables)
    
    if tables.empty:
        print("\nNo tables found. Creating schema...")
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
        
        # Verify tables were created
        print("\nVerifying tables...")
        tables = conn.execute('SHOW TABLES;').fetchdf()
        print(tables)
    
except Exception as e:
    print(f"Error: {str(e)}")
finally:
    if 'conn' in locals():
        conn.close()
