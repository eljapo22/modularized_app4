import duckdb

print("Setting up MotherDuck database...")

# Your token
token = 'eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJlbWFpbCI6ImpobmFwbzIyMTNAZ21haWwuY29tIiwic2Vzc2lvbiI6ImpobmFwbzIyMTMuZ21haWwuY29tIiwicGF0IjoiMFBiVDRqY2p3WTQtMGQxOXdEUmJfNlE0NXM1WWgtZlZTYkItX2hQVUJKWSIsInVzZXJJZCI6IjI4Mzg5MGMwLTZhYmEtNDIyZi04OTI1LWQyNTg0YjJiZmU1NiIsImlzcyI6Im1kX3BhdCIsInJlYWRPbmx5IjpmYWxzZSwidG9rZW5UeXBlIjoicmVhZF93cml0ZSIsImlhdCI6MTczOTk0NDc5MH0.XpT3PzKgOTz6pVlFXcxb9AXpjyc9yuhvmZxmaPXH6c'

try:
    # Connect to DuckDB
    print("1. Connecting to DuckDB...")
    con = duckdb.connect()
    
    # Install and load MotherDuck extension
    print("2. Installing MotherDuck extension...")
    con.execute("INSTALL motherduck")
    print("3. Loading MotherDuck extension...")
    con.execute("LOAD motherduck")
    
    # Set the token
    print("4. Setting MotherDuck token...")
    con.execute(f"SET motherduck_token='{token}'")
    
    # Create database if it doesn't exist
    print("\n5. Creating database...")
    con.execute("CREATE DATABASE IF NOT EXISTS 'md:motherduck_db'")
    con.execute("USE 'md:motherduck_db'")
    
    # Create schema if it doesn't exist
    print("6. Creating schema...")
    con.execute("CREATE SCHEMA IF NOT EXISTS processed_data")
    
    # Create tables if they don't exist
    print("7. Creating tables...")
    for feeder in range(1, 5):
        # Create transformer analysis table
        table_name = f"processed_data.transformer_analysis_hourly_feeder{feeder}"
        print(f"\nCreating {table_name}...")
        con.execute(f"""
            CREATE TABLE IF NOT EXISTS {table_name} (
                transformer_id VARCHAR,
                timestamp TIMESTAMP,
                loading_percentage DOUBLE,
                PRIMARY KEY (transformer_id, timestamp)
            )
        """)
        
        # Create customer analysis table
        table_name = f"processed_data.customer_analysis_hourly_feeder{feeder}"
        print(f"Creating {table_name}...")
        con.execute(f"""
            CREATE TABLE IF NOT EXISTS {table_name} (
                customer_id VARCHAR,
                timestamp TIMESTAMP,
                consumption DOUBLE,
                PRIMARY KEY (customer_id, timestamp)
            )
        """)
    
    # List all tables to verify
    print("\n8. Listing all tables:")
    result = con.execute("SHOW TABLES").fetchdf()
    print(result)
    
except Exception as e:
    print(f"Error: {str(e)}")
