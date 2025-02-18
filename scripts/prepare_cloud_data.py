"""
Prepare data for cloud deployment while maintaining existing data structure
"""
import os
import pandas as pd
import duckdb
from pathlib import Path
from datetime import datetime, timedelta
import logging

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def prepare_feeder_data(feeder_num, source_path, target_path):
    """Prepare data for a single feeder, maintaining existing schema"""
    try:
        # Connect to DuckDB for efficient Parquet reading
        con = duckdb.connect(':memory:')
        
        # Create the target directory
        feeder_dir = target_path / f"feeder{feeder_num}"
        feeder_dir.mkdir(parents=True, exist_ok=True)
        
        # Query to get latest data with all necessary columns
        query = f"""
            SELECT 
                timestamp,
                transformer_id,
                power_kw,
                power_factor,
                power_kva,
                current_a,
                (power_kw / (power_kva * COALESCE(power_factor, 1.0))) * 100 as loading_percentage
            FROM read_parquet('{source_path}/feeder{feeder_num}/*.parquet')
            WHERE timestamp >= (
                SELECT MAX(timestamp) - INTERVAL '30 days' 
                FROM read_parquet('{source_path}/feeder{feeder_num}/*.parquet')
            )
            ORDER BY timestamp DESC
        """
        
        # Execute query and save to parquet
        df = con.execute(query).df()
        
        if not df.empty:
            # Save main data file
            df.to_parquet(feeder_dir / "data.parquet", index=False)
            
            # Save metadata for quick access
            metadata = {
                "transformer_ids": sorted(df['transformer_id'].unique().tolist()),
                "date_range": {
                    "start": df['timestamp'].min().isoformat(),
                    "end": df['timestamp'].max().isoformat()
                },
                "row_count": len(df),
                "last_updated": datetime.now().isoformat()
            }
            pd.Series(metadata).to_json(feeder_dir / "metadata.json")
            
            logger.info(f"Prepared data for feeder {feeder_num}")
            logger.info(f"Rows: {len(df)}")
            logger.info(f"Size: {(feeder_dir / 'data.parquet').stat().st_size / 1024 / 1024:.2f} MB")
            return True
            
        else:
            logger.warning(f"No data found for feeder {feeder_num}")
            return False
            
    except Exception as e:
        logger.error(f"Error processing feeder {feeder_num}: {str(e)}")
        return False

def main():
    """Prepare all feeder data for cloud deployment"""
    try:
        # Source and target paths
        source_path = Path(r"C:\Users\JohnApostolo\CascadeProjects\processed_data\transformer_analysis\hourly")
        target_path = Path(__file__).parent.parent / "data"
        
        # Create data directory
        target_path.mkdir(exist_ok=True)
        
        # Process each feeder
        success_count = 0
        for feeder in range(1, 5):
            if prepare_feeder_data(feeder, source_path, target_path):
                success_count += 1
        
        logger.info(f"Data preparation complete! {success_count}/4 feeders processed")
        
    except Exception as e:
        logger.error(f"Data preparation failed: {str(e)}")
        raise

if __name__ == "__main__":
    main()
