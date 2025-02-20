import duckdb

def test_connection():
    """Just test connecting to the existing database"""
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
        
        # List databases to see what we have access to
        print("\n5. Listing databases:")
        dbs = con.execute("SHOW DATABASES").fetchdf()
        print(dbs)
        
    except Exception as e:
        print(f"Error: {str(e)}")

if __name__ == "__main__":
    test_connection()
