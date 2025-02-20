"""
Test script to verify MotherDuck connection and data access
"""
import os
import duckdb
import pandas as pd
from datetime import datetime, timedelta

def test_connection():
    """Test MotherDuck connection"""
    try:
        # Use the token directly for testing
        token = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJlbWFpbCI6ImpobmFwbzIyMTNAZ21haWwuY29tIiwic2Vzc2lvbiI6ImpobmFwbzIyMTMuZ21haWwuY29tIiwicGF0IjoibEhyVjhyYThNUWdiYUlGR1FZZUcwX3N2NjRBVUFWcXN2UmREOGpSeC1XMCIsInVzZXJJZCI6IjI4Mzg5MGMwLTZhYmEtNDIyZi04OTI1LWQyNTg0YjJiZmU1NiIsImlzcyI6Im1kX3BhdCIsInJlYWRPbmx5IjpmYWxzZSwidG9rZW5UeXBlIjoicmVhZF93cml0ZSIsImlhdCI6MTczOTk5MzM0Mn0.nwlxvtlzcBYSOqYGV_bgUcvlH60Mwp8yJXEQzvBtku0"
        conn = duckdb.connect(f'md:ModApp4DB?motherduck_token={token}')
        print("✓ Successfully connected to MotherDuck")
        return conn
    except Exception as e:
        print(f"✗ Connection failed: {str(e)}")
        return None

def test_transformer_data(conn):
    """Test transformer data access"""
    try:
        # Test each feeder table
        for feeder in range(1, 5):
            table_name = f'"Transformer Feeder {feeder}"'
            query = f"""
            SELECT 
                COUNT(*) as total_records,
                COUNT(DISTINCT transformer_id) as unique_transformers,
                MIN(timestamp) as earliest_date,
                MAX(timestamp) as latest_date
            FROM {table_name}
            """
            result = conn.execute(query).fetchdf()
            print(f"\nTransformer Feeder {feeder} Stats:")
            print(f"Total Records: {result['total_records'].iloc[0]:,}")
            print(f"Unique Transformers: {result['unique_transformers'].iloc[0]:,}")
            print(f"Date Range: {result['earliest_date'].iloc[0]} to {result['latest_date'].iloc[0]}")
            
            # Sample some data
            sample_query = f"""
            SELECT *
            FROM {table_name}
            LIMIT 1
            """
            sample = conn.execute(sample_query).fetchdf()
            print("\nSample Record:")
            print(sample)
            
    except Exception as e:
        print(f"✗ Transformer data test failed: {str(e)}")

def test_customer_data(conn):
    """Test customer data access"""
    try:
        # Test each feeder table
        for feeder in range(1, 5):
            table_name = f'"Customer Feeder {feeder}"'
            query = f"""
            SELECT 
                COUNT(*) as total_records,
                COUNT(DISTINCT customer_id) as unique_customers,
                COUNT(DISTINCT transformer_id) as unique_transformers,
                MIN(timestamp) as earliest_date,
                MAX(timestamp) as latest_date
            FROM {table_name}
            """
            result = conn.execute(query).fetchdf()
            print(f"\nCustomer Feeder {feeder} Stats:")
            print(f"Total Records: {result['total_records'].iloc[0]:,}")
            print(f"Unique Customers: {result['unique_customers'].iloc[0]:,}")
            print(f"Unique Transformers: {result['unique_transformers'].iloc[0]:,}")
            print(f"Date Range: {result['earliest_date'].iloc[0]} to {result['latest_date'].iloc[0]}")
            
            # Sample some data
            sample_query = f"""
            SELECT *
            FROM {table_name}
            LIMIT 1
            """
            sample = conn.execute(sample_query).fetchdf()
            print("\nSample Record:")
            print(sample)
            
    except Exception as e:
        print(f"✗ Customer data test failed: {str(e)}")

def test_relationships(conn):
    """Test relationships between transformers and customers"""
    try:
        # Test for each feeder
        for feeder in range(1, 5):
            t_table = f'"Transformer Feeder {feeder}"'
            c_table = f'"Customer Feeder {feeder}"'
            query = f"""
            SELECT 
                t.transformer_id,
                t.size_kva,
                t.loading_percentage,
                COUNT(DISTINCT c.customer_id) as customer_count
            FROM {t_table} t
            LEFT JOIN {c_table} c 
                ON t.transformer_id = c.transformer_id
                AND strftime(t.timestamp, '%Y-%m-%d') = strftime(c.timestamp, '%Y-%m-%d')
            GROUP BY t.transformer_id, t.size_kva, t.loading_percentage
            LIMIT 5
            """
            result = conn.execute(query).fetchdf()
            print(f"\nFeeder {feeder} Relationship Sample:")
            print(result)
            
    except Exception as e:
        print(f"✗ Relationship test failed: {str(e)}")

def check_tables(conn):
    """Check if all required tables exist"""
    try:
        tables = conn.execute('SHOW TABLES').fetchdf()
        print("\nChecking for required tables:")
        
        # Check transformer feeders
        for i in range(1, 5):
            table_name = f'Transformer Feeder {i}'
            exists = table_name in tables['name'].values
            print(f"✓ {table_name}" if exists else f"✗ {table_name} missing")
            
        # Check customer feeders    
        for i in range(1, 5):
            table_name = f'Customer Feeder {i}'
            exists = table_name in tables['name'].values
            print(f"✓ {table_name}" if exists else f"✗ {table_name} missing")
            
    except Exception as e:
        print(f"✗ Table check failed: {str(e)}")

def main():
    print("Starting MotherDuck Connection Tests...")
    print("-" * 50)
    
    # Test connection
    conn = test_connection()
    if not conn:
        return
        
    # Check tables
    check_tables(conn)
    
    # Test transformer data
    print("\nTesting Transformer Data...")
    print("-" * 50)
    test_transformer_data(conn)
    
    # Test customer data
    print("\nTesting Customer Data...")
    print("-" * 50)
    test_customer_data(conn)
    
    # Test relationships
    print("\nTesting Data Relationships...")
    print("-" * 50)
    test_relationships(conn)
    
    print("\nTests completed!")

if __name__ == "__main__":
    main()
