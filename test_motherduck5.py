import duckdb
import os

try:
    # Set token in environment
    token = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJlbWFpbCI6ImpobmFwbzIyMTNAZ21haWwuY29tIiwic2Vzc2lvbiI6ImpobmFwbzIyMTMuZ21haWwuY29tIiwicGF0IjoiMFBiVDRqY2p3WTQtMGQxOXdEUmJfNlE0NXM1WWgtZlZTYkItX2hQVUJKWSIsInVzZXJJZCI6IjI4Mzg5MGMwLTZhYmEtNDIyZi04OTI1LWQyNTg0YjJiZmU1NiIsImlzcyI6Im1kX3BhdCIsInJlYWRPbmx5IjpmYWxzZSwidG9rZW5UeXBlIjoicmVhZF93cml0ZSIsImlhdCI6MTczOTk0NDc5MH0.XpT3PzKgOTz6pVlFXcxb9AXpjyc9yuhvmZxmaPXH6c"
    os.environ['motherduck_token'] = token
    
    print("Connecting to MotherDuck...")
    # Use the direct connection string without database name first
    conn = duckdb.connect('motherduck:')
    
    print("\nCreating database...")
    conn.execute('CREATE DATABASE IF NOT EXISTS ModApp4DB;')
    conn.execute('USE ModApp4DB;')
    
    print("\nListing tables...")
    tables = conn.execute('SHOW TABLES;').fetchdf()
    print(tables)
    
except Exception as e:
    print(f"Error: {str(e)}")
finally:
    if 'conn' in locals():
        conn.close()
