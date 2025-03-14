import duckdb
import os

try:
    print("Setting environment variable...")
    os.environ['motherduck_token'] = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJlbWFpbCI6ImpobmFwbzIyMTNAZ21haWwuY29tIiwic2Vzc2lvbiI6ImpobmFwbzIyMTMuZ21haWwuY29tIiwicGF0IjoiMFBiVDRqY2p3WTQtMGQxOXdEUmJfNlE0NXM1WWgtZlZTYkItX2hQVUJKWSIsInVzZXJJZCI6IjI4Mzg5MGMwLTZhYmEtNDIyZi04OTI1LWQyNTg0YjJiZmU1NiIsImlzcyI6Im1kX3BhdCIsInJlYWRPbmx5IjpmYWxzZSwidG9rZW5UeXBlIjoicmVhZF93cml0ZSIsImlhdCI6MTczOTk0NDc5MH0.XpT3PzKgOTz6pVlFXcxb9AXpjyc9yuhvmZxmaPXH6c"
    
    print("\nInstalling MotherDuck extension...")
    conn = duckdb.connect(':memory:')
    conn.execute("INSTALL motherduck;")
    conn.execute("LOAD motherduck;")
    print("Extension installed successfully!")
    
    print("\nConnecting to MotherDuck...")
    md_conn = duckdb.connect('md:ModApp4DB')
    print("Connected successfully!")
    
    print("\nListing tables...")
    tables = md_conn.execute('SHOW TABLES').fetchdf()
    print(tables)
    
except Exception as e:
    print(f"Error: {str(e)}")
