import duckdb
import os

def show_database_info():
    """Show all information about the MotherDuck database"""
    token = 'eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJlbWFpbCI6ImpobmFwbzIyMTNAZ21haWwuY29tIiwic2Vzc2lvbiI6ImpobmFwbzIyMTMuZ21haWwuY29tIiwicGF0IjoiMFBiVDRqY2p3WTQtMGQxOXdEUmJfNlE0NXM1WWgtZlZTYkItX2hQVUJKWSIsInVzZXJJZCI6IjI4Mzg5MGMwLTZhYmEtNDIyZi04OTI1LWQyNTg0YjJiZmU1NiIsImlzcyI6Im1kX3BhdCIsInJlYWRPbmx5IjpmYWxzZSwidG9rZW5UeXBlIjoicmVhZF93cml0ZSIsImlhdCI6MTczOTk0NDc5MH0.XpT3PzKgOTz6pVlFXcxb9AXpjyc9yuhvmZxmaPXH6c'
    
    try:
        # Set token as environment variable
        os.environ['motherduck_token'] = token
        
        # Connect to DuckDB first
        print("\n1. Connecting to DuckDB...")
        con = duckdb.connect()
        
        # Install and load MotherDuck
        print("2. Installing MotherDuck extension...")
        con.execute("INSTALL motherduck")
        print("3. Loading MotherDuck extension...")
        con.execute("LOAD motherduck")
        
        # Set token
        print("4. Setting token...")
        con.execute(f"SET motherduck_token='{token}'")
        
        # Connect to your database
        print("\n5. Connecting to ModApp4DB...")
        con.execute("ATTACH 'md:ModApp4DB' AS md")
        
        # List all tables
        print("\n6. Listing all tables:")
        tables = con.execute("SHOW TABLES FROM md.processed_data").fetchdf()
        print(tables)
        
        # Show sample data
        print("\n7. Sample data from transformer_analysis_hourly_feeder1:")
        sample = con.execute("""
            SELECT * FROM md.processed_data.transformer_analysis_hourly_feeder1 
            LIMIT 5
        """).fetchdf()
        print(sample)
        
    except Exception as e:
        print(f"Error: {str(e)}")

if __name__ == "__main__":
    show_database_info()
