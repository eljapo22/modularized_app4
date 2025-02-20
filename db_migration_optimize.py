import duckdb
import os
from datetime import datetime
import logging

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

def connect_to_motherduck():
    """Connect to MotherDuck database"""
    try:
        # Use the new token format
        token = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJlbWFpbCI6ImpobmFwbzIyMTNAZ21haWwuY29tIiwic2Vzc2lvbiI6ImpobmFwbzIyMTMuZ21haWwuY29tIiwicGF0IjoibEhyVjhyYThNUWdiYUlGR1FZZUcwX3N2NjRBVUFWcXN2UmREOGpSeC1XMCIsInVzZXJJZCI6IjI4Mzg5MGMwLTZhYmEtNDIyZi04OTI1LWQyNTg0YjJiZmU1NiIsImlzcyI6Im1kX3BhdCIsInJlYWRPbmx5IjpmYWxzZSwidG9rZW5UeXBlIjoicmVhZF93cml0ZSIsImlhdCI6MTczOTk5MzM0Mn0.nwlxvtlzcBYSOqYGV_bgUcvlH60Mwp8yJXEQzvBtku0"
        
        # Set the environment variable for the token
        os.environ['motherduck_token'] = token
        
        # Connect using v1.2.0 compatible connection string
        conn = duckdb.connect('md:ModApp4DB')
        
        # Test connection
        conn.execute('SELECT 1').fetchone()
        logger.info("Successfully connected to MotherDuck")
        return conn
    except Exception as e:
        logger.error(f"Failed to connect to MotherDuck: {str(e)}")
        raise

def migrate_database(conn):
    """Perform the database migration"""
    try:
        logger.info("Starting database migration...")
        
        # 1. Create new optimized transformer table
        logger.info("Creating optimized transformer table...")
        conn.execute("""
            CREATE TABLE IF NOT EXISTS transformer_optimized AS
            SELECT 
                t.transformer_id,
                t.feeder_id,
                t.size_kva,
                t.nominal_voltage,
                t.rated_current,
                t.x_coordinate,
                t.y_coordinate,
                tb.installation_date,
                tb.last_maintenance_date
            FROM transformer t
            LEFT JOIN transformer_base tb ON t.transformer_id = tb.transformer_id
        """)
        
        # 2. Add indexes to transformer_hourly_stats
        logger.info("Adding indexes to transformer_hourly_stats...")
        conn.execute("""
            CREATE INDEX IF NOT EXISTS idx_ths_transformer_time 
            ON transformer_hourly_stats(transformer_id, hour_timestamp)
        """)
        
        conn.execute("""
            CREATE INDEX IF NOT EXISTS idx_ths_alert 
            ON transformer_hourly_stats(alert_level)
        """)
        
        # 3. Consolidate alerts with proper schema
        logger.info("Consolidating alert tables...")
        conn.execute("""
            CREATE TABLE IF NOT EXISTS transformer_alerts_optimized AS
            SELECT 
                ROW_NUMBER() OVER (ORDER BY hour_timestamp) as alert_id,
                transformer_id,
                hour_timestamp as timestamp,
                loading_percentage as alert_level,
                CASE 
                    WHEN loading_percentage >= 120 THEN 'Critical'
                    WHEN loading_percentage >= 100 THEN 'Overloaded'
                    WHEN loading_percentage >= 80 THEN 'Warning'
                    WHEN loading_percentage >= 50 THEN 'Pre-Warning'
                    ELSE 'Normal'
                END as alert_status,
                'Transformer loading alert' as alert_message,
                loading_percentage,
                power_factor,
                true as resolved,
                hour_timestamp + INTERVAL '1 hour' as resolution_timestamp,
                hour_timestamp as created_at,
                hour_timestamp as updated_at
            FROM transformer_hourly_stats
            WHERE loading_percentage >= 50
        """)
        
        logger.info("Migration completed successfully!")
        return True
        
    except Exception as e:
        logger.error(f"Migration failed: {str(e)}")
        return False

def main():
    conn = None
    try:
        # Connect to MotherDuck
        conn = connect_to_motherduck()
        
        # Perform migration
        if migrate_database(conn):
            logger.info("Database optimization completed successfully!")
        else:
            logger.error("Database optimization failed!")
            
    except Exception as e:
        logger.error(f"Migration failed: {str(e)}")
    finally:
        if conn:
            conn.close()

if __name__ == "__main__":
    main()
