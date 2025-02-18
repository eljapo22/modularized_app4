import duckdb
import os
from dotenv import load_dotenv

def import_to_motherduck():
    """Import data directly to MotherDuck tables"""
    try:
        # Get token from environment variable
        token = os.getenv('MOTHERDUCK_TOKEN')
        if not token:
            print("Please set your MOTHERDUCK_TOKEN environment variable")
            return False
            
        print("Connecting to ModApp4DB...")
        conn = duckdb.connect(f'md:ModApp4DB?motherduck_token={token}')
        
        # Base path for data
        data_path = os.path.join("C:", "Users", "JohnApostolo", "CascadeProjects", 
                              "processed_data", "transformer_analysis", "hourly", "feeder1")
        
        print("\nImporting data directly to MotherDuck...")
        
        # Import transformer readings
        print("Importing transformer readings...")
        conn.execute("""
            INSERT INTO transformer_reading
            SELECT 
                ROW_NUMBER() OVER () as reading_id,
                transformer_id,
                timestamp,
                power_kw,
                current_a,
                voltage_v,
                power_factor,
                power_kw / NULLIF(size_kva * power_factor, 0) * 100 as loading_percentage,
                CASE
                    WHEN power_kw / NULLIF(size_kva * power_factor, 0) * 100 >= 120 THEN 'Critical'
                    WHEN power_kw / NULLIF(size_kva * power_factor, 0) * 100 >= 100 THEN 'Overloaded'
                    WHEN power_kw / NULLIF(size_kva * power_factor, 0) * 100 >= 80 THEN 'Warning'
                    WHEN power_kw / NULLIF(size_kva * power_factor, 0) * 100 >= 50 THEN 'Pre-Warning'
                    ELSE 'Normal'
                END as load_range
            FROM read_parquet('{}/*.parquet')
        """.format(data_path.replace('\\', '/')))
        
        # Import unique transformers
        print("Importing transformer data...")
        conn.execute("""
            INSERT INTO transformer
            SELECT DISTINCT
                transformer_id,
                'Feeder1' as feeder_id,
                size_kva,
                nominal_voltage,
                rated_current,
                CURRENT_TIMESTAMP as created_at,
                CURRENT_TIMESTAMP as updated_at,
                NULL as x_coordinate,
                NULL as y_coordinate
            FROM read_parquet('{}/*.parquet')
        """.format(data_path.replace('\\', '/')))
        
        # Verify the imports
        print("\nVerifying imported data...")
        
        transformer_count = conn.execute("SELECT COUNT(*) FROM transformer").fetchone()[0]
        reading_count = conn.execute("SELECT COUNT(*) FROM transformer_reading").fetchone()[0]
        
        print(f"Imported {transformer_count} transformers")
        print(f"Imported {reading_count} readings")
        
        return True
        
    except Exception as e:
        print(f"Error during import: {str(e)}")
        return False

if __name__ == "__main__":
    load_dotenv()
    success = import_to_motherduck()
    if success:
        print("\nData import completed successfully!")
    else:
        print("\nFailed to import data.")
