import duckdb
import pandas as pd

try:
    print("Installing MotherDuck extension...")
    conn = duckdb.connect(':memory:')
    conn.execute("INSTALL motherduck;")
    conn.execute("LOAD motherduck;")
    print("Extension installed successfully!")
    
    print("\nConnecting to MotherDuck...")
    token = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJlbWFpbCI6ImpobmFwbzIyMTNAZ21haWwuY29tIiwic2Vzc2lvbiI6ImpobmFwbzIyMTMuZ21haWwuY29tIiwicGF0IjoibTl6dmIzUzRCbnUxWTZSOTRCVVRKb2ZCbDNPZno5MzJ0TmdacTNkVjIyVSIsInVzZXJJZCI6IjI4Mzg5MGMwLTZhYmEtNDIyZi04OTI1LWQyNTg0YjJiZmU1NiIsImlzcyI6Im1kX3BhdCIsInJlYWRPbmx5IjpmYWxzZSwidG9rZW5UeXBlIjoicmVhZF93cml0ZSIsImlhdCI6MTc0MDAzNDYzOX0.GF9qa32LWZNnUsRyAsLsHhxZb8oug5_lUrnIAIWSVjU"
    md_conn = duckdb.connect(f'md:?motherduck_token={token}')
    print("Connected successfully!")
    
    print("\nListing tables...")
    tables = md_conn.execute('SHOW TABLES').fetchdf()
    print(tables)
    
    print("\nInspecting Transformer Feeder 1...")
    transformer_data = md_conn.execute('''
        SELECT COUNT(*) as count, 
               MIN(timestamp) as min_date,
               MAX(timestamp) as max_date,
               COUNT(DISTINCT transformer_id) as unique_transformers
        FROM "Transformer Feeder 1"
    ''').fetchdf()
    print("\nTransformer Data Summary:")
    print(transformer_data)
    
    print("\nSample transformer row:")
    sample = md_conn.execute('SELECT * FROM "Transformer Feeder 1" LIMIT 1').fetchdf()
    print(sample)
    
    print("\nInspecting Customer Feeder 1...")
    customer_data = md_conn.execute('''
        SELECT COUNT(*) as count,
               COUNT(DISTINCT customer_id) as unique_customers,
               COUNT(DISTINCT transformer_id) as unique_transformers
        FROM "Customer Feeder 1"
    ''').fetchdf()
    print("\nCustomer Data Summary:")
    print(customer_data)
    
    print("\nSample customer row:")
    sample = md_conn.execute('SELECT * FROM "Customer Feeder 1" LIMIT 1').fetchdf()
    print(sample)
    
except Exception as e:
    print(f"Error: {str(e)}")
finally:
    if 'md_conn' in locals():
        md_conn.close()
    if 'conn' in locals():
        conn.close()
