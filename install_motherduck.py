import duckdb

try:
    print("Creating local connection...")
    conn = duckdb.connect(':memory:')
    
    print("\nInstalling MotherDuck extension...")
    conn.execute("INSTALL motherduck;")
    conn.execute("LOAD motherduck;")
    print("MotherDuck extension installed and loaded!")
    
except Exception as e:
    print(f"Error: {str(e)}")
finally:
    if 'conn' in locals():
        conn.close()
