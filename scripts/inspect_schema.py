import duckdb
import os

# MotherDuck token
token = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJlbWFpbCI6ImpobmFwbzIyMTNAZ21haWwuY29tIiwic2Vzc2lvbiI6ImpobmFwbzIyMTMuZ21haWwuY29tIiwicGF0IjoiMFBiVDRqY2p3WTQtMGQxOXdEUmJfNlE0NXM1WWgtZlZTYkItX2hQVUJKWSIsInVzZXJJZCI6IjI4Mzg5MGMwLTZhYmEtNDIyZi04OTI1LWQyNTg0YjJiZmU1NiIsImlzcyI6Im1kX3BhdCIsInJlYWRPbmx5IjpmYWxzZSwidG9rZW5UeXBlIjoicmVhZF93cml0ZSIsImlhdCI6MTczOTk0NDc5MH0.XpT3PzKgOTz6pVlFXcxb9AXpjyc9yuhvmZxmaPXH6c"

print("Connecting to MotherDuck...")
conn = duckdb.connect(f'md:ModApp4DB?motherduck_token={token}')

print("\nListing tables...")
tables = conn.execute("SHOW TABLES").fetchdf()
print(tables if not tables.empty else "No tables found")

if not tables.empty:
    print("\nDescribing tables:")
    for table in tables['name']:
        print(f"\nTable: {table}")
        schema = conn.execute(f"DESCRIBE {table}").fetchdf()
        print(schema)
        
        print("\nSample data:")
        sample = conn.execute(f"SELECT * FROM {table} LIMIT 5").fetchdf()
        print(sample)
