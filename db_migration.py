import duckdb
import os
from datetime import datetime, timedelta

def create_schema(conn):
    """Create the new schema tables"""
    print("\nCreating new schema tables...")
    
    # Create transformer_base table
    print("Creating transformer_base table...")
    conn.execute("""
        CREATE TABLE IF NOT EXISTS transformer_base (
            transformer_id VARCHAR PRIMARY KEY,
            feeder_id INTEGER,
            size_kva DOUBLE,
            location_x DOUBLE,
            location_y DOUBLE,
            installation_date DATE,
            last_maintenance_date DATE,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        );
    """)
    
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
    
    # Create customer_transformer_map table
    print("Creating customer_transformer_map table...")
    conn.execute("""
        CREATE TABLE IF NOT EXISTS customer_transformer_map (
            customer_id VARCHAR,
            transformer_id VARCHAR,
            connection_date DATE,
            status VARCHAR,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            PRIMARY KEY (customer_id, transformer_id)
        );
    """)
    
    # Create new transformer_alerts table
    print("Creating new transformer_alerts table...")
    conn.execute("""
        CREATE TABLE IF NOT EXISTS transformer_alerts_new (
            alert_id INTEGER PRIMARY KEY,
            transformer_id VARCHAR,
            timestamp TIMESTAMP,
            alert_level VARCHAR,
            alert_message TEXT,
            resolved BOOLEAN DEFAULT FALSE,
            resolution_timestamp TIMESTAMP,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        );
    """)

def migrate_data(conn):
    """Migrate data from existing tables to new schema"""
    print("\nMigrating data to new schema...")
    
    # Migrate transformer base data
    print("Migrating transformer base data...")
    conn.execute("""
        INSERT INTO transformer_base (
            transformer_id,
            feeder_id,
            size_kva,
            location_x,
            location_y
        )
        SELECT DISTINCT
            t.transformer_id,
            tl.feeder_id,
            tl.size_kva,
            0.0 as location_x,  -- Default values for now
            0.0 as location_y   -- Default values for now
        FROM transformer t
        LEFT JOIN transformer_loading tl ON t.transformer_id = tl.transformer_id
        WHERE t.transformer_id IS NOT NULL
        ON CONFLICT (transformer_id) DO NOTHING;
    """)
    
    # Create hourly stats from transformer_loading
    print("Creating hourly stats...")
    conn.execute("""
        INSERT INTO transformer_hourly_stats (
            transformer_id,
            hour_timestamp,
            loading_percentage,
            power_kw,
            power_factor,
            size_kva,
            customer_count,
            alert_level,
            avg_loading_24h,
            max_loading_24h
        )
        WITH hourly_data AS (
            SELECT 
                transformer_id,
                DATE_TRUNC('hour', timestamp) as hour_timestamp,
                AVG(loading_percentage) as loading_percentage,
                AVG(power_kw) as power_kw,
                AVG(power_factor) as power_factor,
                MAX(size_kva) as size_kva,
                0 as customer_count,  -- Will update this later
                CASE 
                    WHEN AVG(loading_percentage) >= 120 THEN 'Critical'
                    WHEN AVG(loading_percentage) >= 100 THEN 'Overloaded'
                    WHEN AVG(loading_percentage) >= 80 THEN 'Warning'
                    WHEN AVG(loading_percentage) >= 50 THEN 'Pre-Warning'
                    ELSE 'Normal'
                END as alert_level,
                AVG(loading_percentage) OVER (
                    PARTITION BY transformer_id 
                    ORDER BY DATE_TRUNC('hour', timestamp)
                    ROWS BETWEEN 23 PRECEDING AND CURRENT ROW
                ) as avg_loading_24h,
                MAX(loading_percentage) OVER (
                    PARTITION BY transformer_id 
                    ORDER BY DATE_TRUNC('hour', timestamp)
                    ROWS BETWEEN 23 PRECEDING AND CURRENT ROW
                ) as max_loading_24h
            FROM transformer_loading
            GROUP BY transformer_id, DATE_TRUNC('hour', timestamp)
        )
        SELECT * FROM hourly_data
        ON CONFLICT (transformer_id, hour_timestamp) DO NOTHING;
    """)
    
    # Migrate customer mapping
    print("Migrating customer mapping...")
    conn.execute("""
        INSERT INTO customer_transformer_map (
            customer_id,
            transformer_id,
            connection_date,
            status
        )
        SELECT DISTINCT
            cr.customer_id,
            cr.transformer_id,
            DATE(MIN(cr.timestamp)) as connection_date,
            'Active' as status
        FROM customer_reading cr
        WHERE cr.customer_id IS NOT NULL AND cr.transformer_id IS NOT NULL
        GROUP BY cr.customer_id, cr.transformer_id
        ON CONFLICT (customer_id, transformer_id) DO NOTHING;
    """)
    
    # Migrate alerts
    print("Migrating alerts...")
    conn.execute("""
        INSERT INTO transformer_alerts_new (
            transformer_id,
            timestamp,
            alert_level,
            alert_message,
            resolved
        )
        SELECT 
            transformer_id,
            timestamp,
            alert_level,
            'Historical alert from migration' as alert_message,
            TRUE as resolved
        FROM transformer_alerts
        ON CONFLICT DO NOTHING;
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
    """)
    
    # Customer mapping indexes
    conn.execute("""
        CREATE INDEX IF NOT EXISTS idx_ctm_transformer 
        ON customer_transformer_map(transformer_id);
        
        CREATE INDEX IF NOT EXISTS idx_ctm_customer 
        ON customer_transformer_map(customer_id);
    """)
    
    # Alert indexes
    conn.execute("""
        CREATE INDEX IF NOT EXISTS idx_alerts_transformer_timestamp 
        ON transformer_alerts_new(transformer_id, timestamp);
        
        CREATE INDEX IF NOT EXISTS idx_alerts_level 
        ON transformer_alerts_new(alert_level);
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
        
        print("\nMigration completed successfully!")
        
    except Exception as e:
        print(f"Error during migration: {str(e)}")
    finally:
        if 'conn' in locals():
            conn.close()

if __name__ == "__main__":
    main()
