import duckdb
import os
from dotenv import load_dotenv

# Set the token as an environment variable
os.environ['MOTHERDUCK_TOKEN'] = 'eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJlbWFpbCI6ImpobmFwbzIyMTNAZ21haWwuY29tIiwic2Vzc2lvbiI6ImpobmFwbzIyMTMuZ21haWwuY29tIiwicGF0IjoiMFBiVDRqY2p3WTQtMGQxOXdEUmJfNlE0NXM1WWgtZlZTYkItX2hQVUJKWSIsInVzZXJJZCI6IjI4Mzg5MGMwLTZhYmEtNDIyZi04OTI1LWQyNTg0YjJiZmU1NiIsImlzcyI6Im1kX3BhdCIsInJlYWRPbmx5IjpmYWxzZSwidG9rZW5UeXBlIjoicmVhZF93cml0ZSIsImlhdCI6MTczOTk0NDc5MH0.XpT3PzKgOTz6pVlFXcxb9AXpjyc9yuhvmZxmaPXH6c'

try:
    print("Connecting to MotherDuck...")
    # Connect to the root database first
    conn = duckdb.connect('md:?motherduck_token=' + os.environ['MOTHERDUCK_TOKEN'])
    
    print("\nListing all databases:")
    databases = conn.execute("SHOW DATABASES").fetchdf()
    print(databases)
    
    print("\nConnecting to ModApp4DB...")
    conn = duckdb.connect('md:ModApp4DB?motherduck_token=' + os.environ['MOTHERDUCK_TOKEN'])
    
    print("\nListing tables:")
    tables = conn.execute("SHOW TABLES").fetchdf()
    print(tables)
    
    if not tables.empty:
        for table in tables['name']:
            print(f"\nSchema for {table}:")
            schema = conn.execute(f"DESCRIBE {table}").fetchdf()
            print(schema)
            
            print(f"\nSample data from {table}:")
            sample = conn.execute(f"SELECT * FROM {table} LIMIT 3").fetchdf()
            print(sample)
            
except Exception as e:
    print(f"Error: {str(e)}")
