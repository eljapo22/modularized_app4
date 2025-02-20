import duckdb

def test_connection():
    """Test connecting to ModApp4DB4"""
    token = 'eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJlbWFpbCI6ImpobmFwbzIyMTNAZ21haWwuY29tIiwic2Vzc2lvbiI6ImpobmFwbzIyMTMuZ21haWwuY29tIiwicGF0IjoibDY1Y0Q4cmJ3dVNHdjBGdkowQV9PTjFYNTVyVXZxeS0tMGU5bndvRGtEbyIsInVzZXJJZCI6IjI4Mzg5MGMwLTZhYmEtNDIyZi04OTI1LWQyNTg0YjJiZmU1NiIsImlzcyI6Im1kX3BhdCIsInJlYWRPbmx5IjpmYWxzZSwidG9rZW5UeXBlIjoicmVhZF93cml0ZSIsImlhdCI6MTczOTk0NTk4NywiZXhwIjoxNzQxODQ2Nzg3fQ.ypdFwGl-VbN50KskPqEabxnmekGQbAi5xufUge6C9nU'
    
    try:
        # Connect directly to ModApp4DB4
        print("1. Connecting to ModApp4DB4...")
        con = duckdb.connect(f'md:ModApp4DB4?motherduck_token={token}')
        
        # List tables in processed_data schema
        print("\n2. Listing tables in processed_data schema:")
        tables = con.execute("""
            SELECT table_schema, table_name 
            FROM information_schema.tables 
            WHERE table_schema = 'processed_data'
        """).fetchdf()
        print(tables)
        
        # Try to query a table
        print("\n3. Querying transformer_analysis_hourly_feeder1:")
        result = con.execute("""
            SELECT * FROM processed_data.transformer_analysis_hourly_feeder1 
            LIMIT 5
        """).fetchdf()
        print(result)
        
    except Exception as e:
        print(f"Error: {str(e)}")

if __name__ == "__main__":
    test_connection()
