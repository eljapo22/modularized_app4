import duckdb

def main():
    try:
        print("Connecting to MotherDuck...")
        conn = duckdb.connect('motherduck:')
        
        print("\nUsing ModApp4DB...")
        conn.execute('USE ModApp4DB;')
        
        # Get all tables and their columns
        query = """
        SELECT 
            table_name,
            column_name,
            column_type,
            is_nullable,
            column_default,
            CASE WHEN constraint_type = 'PRIMARY KEY' THEN 'PK' ELSE '' END as key_type
        FROM duckdb_columns()
        LEFT JOIN duckdb_constraints() 
            ON duckdb_columns.table_name = duckdb_constraints.table_name 
            AND duckdb_columns.column_name = duckdb_constraints.column_name
        ORDER BY table_name, ordinal_position;
        """
        
        result = conn.execute(query).fetchdf()
        
        # Print results in a formatted way
        current_table = None
        for _, row in result.iterrows():
            if current_table != row['table_name']:
                current_table = row['table_name']
                print(f"\n=== {current_table} ===")
                print("Column Name".ljust(30), "Type".ljust(15), "Nullable".ljust(10), "Default".ljust(20), "Key")
                print("-" * 85)
            
            print(
                str(row['column_name']).ljust(30),
                str(row['column_type']).ljust(15),
                str(row['is_nullable']).ljust(10),
                str(row['column_default'] or '').ljust(20),
                row['key_type']
            )
        
    except Exception as e:
        print(f"Error: {str(e)}")
    finally:
        if 'conn' in locals():
            conn.close()

if __name__ == "__main__":
    main()
