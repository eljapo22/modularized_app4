import duckdb

# Connect to MotherDuck
print("Connecting to MotherDuck...")
token = 'eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJlbWFpbCI6ImpobmFwbzIyMTNAZ21haWwuY29tIiwic2Vzc2lvbiI6ImpobmFwbzIyMTMuZ21haWwuY29tIiwicGF0IjoiMFBiVDRqY2p3WTQtMGQxOXdEUmJfNlE0NXM1WWgtZlZTYkItX2hQVUJKWSIsInVzZXJJZCI6IjI4Mzg5MGMwLTZhYmEtNDIyZi04OTI1LWQyNTg0YjJiZmU1NiIsImlzcyI6Im1kX3BhdCIsInJlYWRPbmx5IjpmYWxzZSwidG9rZW5UeXBlIjoicmVhZF93cml0ZSIsImlhdCI6MTczOTk0NDc5MH0.XpT3PzKgOTz6pVlFXcxb9AXpjyc9yuhvmZxmaPXH6c'

try:
    # First try connecting to root to see databases
    conn = duckdb.connect()
    conn.execute("INSTALL motherduck")
    conn.execute("LOAD motherduck")
    conn.execute(f"SET motherduck_token='{token}'")
    
    print("\nListing databases:")
    print(conn.execute("SHOW DATABASES").fetchdf())
    
    print("\nConnecting to ModApp4DB...")
    conn.execute("USE ModApp4DB")
    
    print("\nListing tables:")
    print(conn.execute("SHOW TABLES").fetchdf())
    
except Exception as e:
    print(f"Error: {str(e)}")
