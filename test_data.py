"""
Test script to verify data in MotherDuck
"""
import streamlit as st
import duckdb
import os
import pandas as pd

def test_data_access():
    st.title("MotherDuck Data Test")
    
    try:
        # Get token from secrets
        token = st.secrets["MOTHERDUCK_TOKEN"]
        os.environ["motherduck_token"] = token
        
        # Connect to MotherDuck
        conn = duckdb.connect('md:ModApp4DB')
        st.success("✓ Connected to MotherDuck")
        
        # Test queries
        queries = {
            "Count total records": "SELECT COUNT(*) as total FROM transformer_readings",
            "Count unique transformers": "SELECT COUNT(DISTINCT transformer_id) as transformers FROM transformer_readings",
            "Count unique feeders": "SELECT COUNT(DISTINCT feeder_id) as feeders FROM transformer_readings",
            "Latest timestamp": "SELECT MAX(timestamp) as latest FROM transformer_readings",
            "Earliest timestamp": "SELECT MIN(timestamp) as earliest FROM transformer_readings"
        }
        
        # Execute each query
        for title, query in queries.items():
            try:
                result = conn.execute(query).df()
                st.write(f"### {title}")
                st.dataframe(result)
            except Exception as e:
                st.error(f"Query failed: {title}\nError: {str(e)}")
        
        # Sample data preview
        st.write("### Sample Data Preview")
        try:
            sample = conn.execute("""
                SELECT *
                FROM transformer_readings
                LIMIT 5
            """).df()
            st.dataframe(sample)
        except Exception as e:
            st.error(f"Failed to get sample data: {str(e)}")
            
    except Exception as e:
        st.error(f"Failed to connect to MotherDuck: {str(e)}")

if __name__ == "__main__":
    test_data_access()
