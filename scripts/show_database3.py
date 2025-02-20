import duckdb
import os

def show_database_info():
    """Show all information about the MotherDuck database"""
    token = 'eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJlbWFpbCI6ImpobmFwbzIyMTNAZ21haWwuY29tIiwic2Vzc2lvbiI6ImpobmFwbzIyMTMuZ21haWwuY29tIiwicGF0IjoiMFBiVDRqY2p3WTQtMGQxOXdEUmJfNlE0NXM1WWgtZlZTYkItX2hQVUJKWSIsInVzZXJJZCI6IjI4Mzg5MGMwLTZhYmEtNDIyZi04OTI1LWQyNTg0YjJiZmU1NiIsImlzcyI6Im1kX3BhdCIsInJlYWRPbmx5IjpmYWxzZSwidG9rZW5UeXBlIjoicmVhZF93cml0ZSIsImlhdCI6MTczOTk0NDc5MH0.XpT3PzKgOTz6pVlFXcxb9AXpjyc9yuhvmZxmaPXH6c'
    
    try:
        # Connect directly to your database with token
        print("\n1. Connecting to MotherDuck...")
        con = duckdb.connect(f'md:ModApp4DB?motherduck_token={token}')
        
        # List all tables in processed_data schema
        print("\n2. Listing all tables in processed_data schema:")
        tables = con.execute("""
            SELECT table_schema, table_name 
            FROM information_schema.tables 
            WHERE table_schema = 'processed_data'
        """).fetchdf()
        print(tables)
        
        if not tables.empty:
            # Show sample data from first table
            table_name = f"processed_data.{tables.iloc[0]['table_name']}"
            print(f"\n3. Sample data from {table_name}:")
            sample = con.execute(f"""
                SELECT * FROM {table_name}
                LIMIT 5
            """).fetchdf()
            print(sample)
        
    except Exception as e:
        print(f"Error: {str(e)}")

if __name__ == "__main__":
    show_database_info()
