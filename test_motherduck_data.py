"""
Test script to verify MotherDuck connection and data access
"""
import os
import duckdb
import pandas as pd
from datetime import datetime, timedelta

# MotherDuck token
MOTHERDUCK_TOKEN = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJlbWFpbCI6ImpobmFwbzIyMTNAZ21haWwuY29tIiwic2Vzc2lvbiI6ImpobmFwbzIyMTMuZ21haWwuY29tIiwicGF0IjoibTl6dmIzUzRCbnUxWTZSOTRCVVRKb2ZCbDNPZno5MzJ0TmdacTNkVjIyVSIsInVzZXJJZCI6IjI4Mzg5MGMwLTZhYmEtNDIyZi04OTI1LWQyNTg0YjJiZmU1NiIsImlzcyI6Im1kX3BhdCIsInJlYWRPbmx5IjpmYWxzZSwidG9rZW5UeXBlIjoicmVhZF93cml0ZSIsImlhdCI6MTc0MDAzNDYzOX0.GF9qa32LWZNnUsRyAsLsHhxZb8oug5_lUrnIAIWSVjU"
def get_connection():
    """Get MotherDuck connection"""
    connection_string = f'md:ModApp4DB?motherduck_token={MOTHERDUCK_TOKEN}'
    con = duckdb.connect(connection_string)
    con.execute("SET enable_progress_bar=false")
    con.execute("SET errors_as_json=true")
    return con

def test_transformer_data(conn):
    """Test transformer data retrieval"""
    print("\nTesting Transformer Data...")
    print("-" * 50)
    
    # Test date
    test_date = datetime(2024, 1, 1).date()
    
    # Test for each feeder
    for feeder in range(1, 5):
        print(f"\nFeeder {feeder}:")
        try:
            # Get transformer data
            query = f"""
            SELECT *
            FROM ModApp4DB.main."Transformer Feeder {feeder}"
            WHERE CAST(timestamp AS DATE) = ?
            """
            data = conn.execute(query, [test_date]).df()
            
            if data.empty:
                print(f"[X] No data found for feeder {feeder}")
                continue
                
            print(f"[+] Found {len(data)} records")
            print(f"[+] Unique transformers: {data['transformer_id'].nunique()}")
            print(f"[+] Date range: {data['timestamp'].min()} to {data['timestamp'].max()}")
            print("\nSample record:")
            print(data.iloc[0])
            
        except Exception as e:
            print(f"[X] Error accessing feeder {feeder}: {str(e)}")

def test_customer_data(conn):
    """Test customer data retrieval"""
    print("\nTesting Customer Data...")
    print("-" * 50)
    
    # Test date
    test_date = datetime(2024, 1, 1).date()
    
    # Test for each feeder
    for feeder in range(1, 5):
        print(f"\nFeeder {feeder}:")
        try:
            # Get customer data
            query = f"""
            SELECT *
            FROM ModApp4DB.main."Customer Feeder {feeder}"
            WHERE CAST(timestamp AS DATE) = ?
            """
            data = conn.execute(query, [test_date]).df()
            
            if data.empty:
                print(f"[X] No data found for feeder {feeder}")
                continue
                
            print(f"[+] Found {len(data)} records")
            print(f"[+] Unique customers: {data['customer_id'].nunique()}")
            print(f"[+] Date range: {data['timestamp'].min()} to {data['timestamp'].max()}")
            print("\nSample record:")
            print(data.iloc[0])
            
        except Exception as e:
            print(f"[X] Error accessing feeder {feeder}: {str(e)}")

def test_relationships(conn):
    """Test transformer-customer relationships"""
    print("\nTesting Data Relationships...")
    print("-" * 50)
    
    # Test date
    test_date = datetime(2024, 1, 1).date()
    
    try:
        # Get relationships for each feeder
        for feeder in range(1, 5):
            print(f"\nFeeder {feeder} Relationships:")
            query = f"""
            SELECT 
                t.transformer_id,
                t.size_kva,
                t.loading_percentage,
                COUNT(DISTINCT c.customer_id) as customer_count
            FROM ModApp4DB.main."Transformer Feeder {feeder}" t
            LEFT JOIN ModApp4DB.main."Customer Feeder {feeder}" c 
                ON t.transformer_id = c.transformer_id 
                AND CAST(t.timestamp AS DATE) = CAST(c.timestamp AS DATE)
            WHERE CAST(t.timestamp AS DATE) = ?
            GROUP BY t.transformer_id, t.size_kva, t.loading_percentage
            LIMIT 5
            """
            relationships = conn.execute(query, [test_date]).df()
            
            if relationships.empty:
                print(f"[X] No relationships found for feeder {feeder}")
                continue
                
            print(f"[+] Found relationships")
            print("\nSample relationships:")
            print(relationships)
            
    except Exception as e:
        print(f"[X] Error testing relationships: {str(e)}")

def main():
    """Main test function"""
    print("Starting MotherDuck Data Tests...")
    print("=" * 50)
    
    try:
        # Get database connection
        conn = get_connection()
        print("[+] Connected to MotherDuck")
        
        # Run tests
        test_transformer_data(conn)
        test_customer_data(conn)
        test_relationships(conn)
        
        print("\nTests completed!")
        
    except Exception as e:
        print(f"[X] Test failed: {str(e)}")

if __name__ == "__main__":
    main()
