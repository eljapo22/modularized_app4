import duckdb
import os
from datetime import datetime, timedelta

def create_schema(conn):
    """Create the new schema tables"""
    print("\nCreating new schema tables...")
    
    # Create transformer_hourly_stats table
    print("Creating transformer_hourly_stats table...")
    conn.execute("""
        CREATE TABLE IF NOT EXISTS transformer_hourly_stats (
            transformer_id VARCHAR,
            hour_timestamp TIMESTAMP,
            loading_percentage DOUBLE,
            power_kw DOUBLE,
            power_factor DOUBLE,
            size_kva DOUBLE,
            customer_count INTEGER,
            alert_level VARCHAR,
            avg_loading_24h DOUBLE,
            max_loading_24h DOUBLE,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            PRIMARY KEY (transformer_id, hour_timestamp)
        );
    """)

def migrate_data(conn):
    """Migrate data from existing tables to new schema"""
    print("\nMigrating data to new schema...")
    
    print("Creating hourly stats from transformer_reading...")
    conn.execute("""
        WITH base_hourly AS (
            SELECT 
                transformer_id,
                DATE_TRUNC('hour', timestamp) as hour_timestamp,
                AVG(loading_percentage) as loading_percentage,
                AVG(power_kw) as power_kw,
                AVG(power_factor) as power_factor,
                50.0 as size_kva,
                0 as customer_count
            FROM transformer_reading
            GROUP BY transformer_id, DATE_TRUNC('hour', timestamp)
        ),
        with_24h_stats AS (
            SELECT 
                *,
                AVG(loading_percentage) OVER (
                    PARTITION BY transformer_id 
                    ORDER BY hour_timestamp 
                    ROWS BETWEEN 23 PRECEDING AND CURRENT ROW
                ) as avg_loading_24h,
                MAX(loading_percentage) OVER (
                    PARTITION BY transformer_id 
                    ORDER BY hour_timestamp 
                    ROWS BETWEEN 23 PRECEDING AND CURRENT ROW
                ) as max_loading_24h,
                CASE 
                    WHEN loading_percentage >= 120 THEN 'Critical'
                    WHEN loading_percentage >= 100 THEN 'Overloaded'
                    WHEN loading_percentage >= 80 THEN 'Warning'
                    WHEN loading_percentage >= 50 THEN 'Pre-Warning'
                    ELSE 'Normal'
                END as alert_level
            FROM base_hourly
        )
        INSERT INTO transformer_hourly_stats
        SELECT * FROM with_24h_stats
        ON CONFLICT (transformer_id, hour_timestamp) DO UPDATE SET
            loading_percentage = EXCLUDED.loading_percentage,
            power_kw = EXCLUDED.power_kw,
            power_factor = EXCLUDED.power_factor,
            size_kva = EXCLUDED.size_kva,
            customer_count = EXCLUDED.customer_count,
            alert_level = EXCLUDED.alert_level,
            avg_loading_24h = EXCLUDED.avg_loading_24h,
            max_loading_24h = EXCLUDED.max_loading_24h;
    """)

def create_indexes(conn):
    """Create indexes for performance"""
    print("\nCreating indexes...")
    
    # Transformer hourly stats indexes
    conn.execute("""
        CREATE INDEX IF NOT EXISTS idx_ths_transformer_timestamp 
        ON transformer_hourly_stats(transformer_id, hour_timestamp);
        
        CREATE INDEX IF NOT EXISTS idx_ths_timestamp 
        ON transformer_hourly_stats(hour_timestamp);
        
        CREATE INDEX IF NOT EXISTS idx_ths_alert_level
        ON transformer_hourly_stats(alert_level);
    """)

def main():
    try:
        print("Connecting to MotherDuck...")
        conn = duckdb.connect('motherduck:')
        
        print("Using ModApp4DB...")
        conn.execute('USE ModApp4DB;')
        
        # Execute migration steps
        create_schema(conn)
        migrate_data(conn)
        create_indexes(conn)
        
        # Verify migration
        print("\nVerifying migration...")
        count = conn.execute("SELECT COUNT(*) FROM transformer_hourly_stats").fetchone()[0]
        print(f"Migrated {count} hourly records")
        
        print("\nMigration completed successfully!")
        
    except Exception as e:
        print(f"Error during migration: {str(e)}")
    finally:
        if 'conn' in locals():
            conn.close()

if __name__ == "__main__":
    main()
