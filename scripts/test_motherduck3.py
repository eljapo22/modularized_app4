import duckdb

print("Testing MotherDuck connection (attempt 3)...")

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
    
    # Connect to ModApp4DB
    print("\n5. Connecting to ModApp4DB...")
    con.execute("USE 'md:ModApp4DB'")
    
    # List tables in processed_data schema
    print("\n6. Listing tables in processed_data schema:")
    result = con.execute("SHOW TABLES").fetchdf()
    print(result)
    
    # Try to query one of the tables
    print("\n7. Trying to query transformer_analysis_hourly_feeder1:")
    result = con.execute("""
        SELECT * FROM processed_data.transformer_analysis_hourly_feeder1 
        LIMIT 5
    """).fetchdf()
    print(result)
    
except Exception as e:
    print(f"Error: {str(e)}")
