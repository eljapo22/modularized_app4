import duckdb

def setup_database():
    """Set up the MotherDuck database and tables"""
    token = 'eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJlbWFpbCI6ImpobmFwbzIyMTNAZ21haWwuY29tIiwic2Vzc2lvbiI6ImpobmFwbzIyMTMuZ21haWwuY29tIiwicGF0IjoibDY1Y0Q4cmJ3dVNHdjBGdkowQV9PTjFYNTVyVXZxeS0tMGU5bndvRGtEbyIsInVzZXJJZCI6IjI4Mzg5MGMwLTZhYmEtNDIyZi04OTI1LWQyNTg0YjJiZmU1NiIsImlzcyI6Im1kX3BhdCIsInJlYWRPbmx5IjpmYWxzZSwidG9rZW5UeXBlIjoicmVhZF93cml0ZSIsImlhdCI6MTczOTk0NTk4NywiZXhwIjoxNzQxODQ2Nzg3fQ.ypdFwGl-VbN50KskPqEabxnmekGQbAi5xufUge6C9nU'
    
    try:
        # Connect to DuckDB
        print("1. Connecting to DuckDB...")
        con = duckdb.connect()
        
        # Install and load MotherDuck extension
        print("2. Installing MotherDuck extension...")
        con.execute("INSTALL motherduck")
        print("3. Loading MotherDuck extension...")
        con.execute("LOAD motherduck")
        
        # Set token
        print("4. Setting token...")
        con.execute(f"SET motherduck_token='{token}'")
        
        # Create database
        print("\n5. Creating database...")
        con.execute("CREATE DATABASE IF NOT EXISTS 'md:ModApp4DB4'")
        con.execute("USE 'md:ModApp4DB4'")
        
        # Create schema
        print("\n6. Creating schema...")
        con.execute("CREATE SCHEMA IF NOT EXISTS processed_data")
        
        # Create transformer tables
        print("\n7. Creating transformer tables...")
        for feeder in range(1, 5):
            table_name = f"processed_data.transformer_analysis_hourly_feeder{feeder}"
            print(f"Creating {table_name}...")
            con.execute(f"""
                CREATE TABLE IF NOT EXISTS {table_name} (
                    transformer_id VARCHAR,
                    timestamp TIMESTAMP,
                    loading_percentage DOUBLE,
                    PRIMARY KEY (transformer_id, timestamp)
                )
            """)
        
        # Create customer tables
        print("\n8. Creating customer tables...")
        for feeder in range(1, 5):
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
        
        # List all tables
        print("\n9. Listing all tables:")
        tables = con.execute("""
            SELECT table_schema, table_name 
            FROM information_schema.tables 
            WHERE table_schema = 'processed_data'
        """).fetchdf()
        print(tables)
        
    except Exception as e:
        print(f"Error: {str(e)}")

if __name__ == "__main__":
    setup_database()
