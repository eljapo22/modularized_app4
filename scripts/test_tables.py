import duckdb

def test_motherduck_tables():
    """Test connection to MotherDuck and verify table structure"""
    token = 'eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJlbWFpbCI6ImpobmFwbzIyMTNAZ21haWwuY29tIiwic2Vzc2lvbiI6ImpobmFwbzIyMTMuZ21haWwuY29tIiwicGF0IjoiMFBiVDRqY2p3WTQtMGQxOXdEUmJfNlE0NXM1WWgtZlZTYkItX2hQVUJKWSIsInVzZXJJZCI6IjI4Mzg5MGMwLTZhYmEtNDIyZi04OTI1LWQyNTg0YjJiZmU1NiIsImlzcyI6Im1kX3BhdCIsInJlYWRPbmx5IjpmYWxzZSwidG9rZW5UeXBlIjoicmVhZF93cml0ZSIsImlhdCI6MTczOTk0NDc5MH0.XpT3PzKgOTz6pVlFXcxb9AXpjyc9yuhvmZxmaPXH6c'
    
    try:
        # Connect to MotherDuck
        print("1. Connecting to MotherDuck...")
        con = duckdb.connect(f'md:?motherduck_token={token}')
        
        # Test transformer tables
        for feeder in range(1, 5):
            table_name = f"processed_data.transformer_analysis_hourly_feeder{feeder}"
            print(f"\nTesting {table_name}:")
            try:
                result = con.execute(f"""
                    SELECT * FROM {table_name}
                    LIMIT 1
                """).fetchdf()
                print(f"✓ Successfully queried {table_name}")
                print("Columns:", result.columns.tolist())
                if not result.empty:
                    print("Sample row:", result.iloc[0].to_dict())
            except Exception as e:
                print(f"✗ Error querying {table_name}: {str(e)}")
        
        # Test customer tables
        for feeder in range(1, 5):
            table_name = f"processed_data.customer_analysis_hourly_feeder{feeder}"
            print(f"\nTesting {table_name}:")
            try:
                result = con.execute(f"""
                    SELECT * FROM {table_name}
                    LIMIT 1
                """).fetchdf()
                print(f"✓ Successfully queried {table_name}")
                print("Columns:", result.columns.tolist())
                if not result.empty:
                    print("Sample row:", result.iloc[0].to_dict())
            except Exception as e:
                print(f"✗ Error querying {table_name}: {str(e)}")
                
    except Exception as e:
        print(f"Connection error: {str(e)}")

if __name__ == "__main__":
    test_motherduck_tables()
