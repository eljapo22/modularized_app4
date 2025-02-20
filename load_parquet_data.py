import duckdb
import os
import glob
import logging
from datetime import datetime
from collections import defaultdict

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

def normalize_path(path):
    """Normalize path for DuckDB"""
    return os.path.normpath(path).replace('\\', '/')

def connect_to_db(use_motherduck=False):
    """Connect to database"""
    try:
        if use_motherduck:
            conn = duckdb.connect('md:ModApp4DB')
            logger.info("Successfully connected to MotherDuck")
        else:
            conn = duckdb.connect(':memory:')
            logger.info("Connected to in-memory DuckDB")
        return conn
    except Exception as e:
        logger.error(f"Failed to connect to database: {str(e)}")
        raise

def preview_parquet_files():
    """Preview all parquet files from the specified directories"""
    try:
        conn = connect_to_db(use_motherduck=False)
        
        # Base directories
        customer_dir = normalize_path(r"C:\Users\JohnApostolo\CascadeProjects\processed_data\customer_analysis")
        transformer_dir = normalize_path(r"C:\Users\JohnApostolo\CascadeProjects\processed_data\transformer_analysis")
        
        file_categories = defaultdict(list)
        
        # Analyze transformer data
        logger.info("\nAnalyzing transformer data files...")
        transformer_files = glob.glob(os.path.join(transformer_dir, "**/*.parquet"), recursive=True)
        
        for file in transformer_files:
            try:
                normalized_file = normalize_path(file)
                logger.info(f"Analyzing file: {normalized_file}")
                
                # Try to read the parquet file schema first
                try:
                    schema = conn.execute(f"SELECT * FROM parquet_schema('{normalized_file}')").fetchall()
                except Exception as e:
                    logger.error(f"Failed to read schema from {normalized_file}: {str(e)}")
                    continue
                
                # Create temporary view
                try:
                    conn.execute(f"CREATE VIEW temp_view AS SELECT * FROM read_parquet('{normalized_file}')")
                except Exception as e:
                    logger.error(f"Failed to create view for {normalized_file}: {str(e)}")
                    continue
                
                # Get schema and row count
                columns = conn.execute("DESCRIBE temp_view").fetchall()
                column_names = [col[0] for col in columns]
                row_count = conn.execute("SELECT COUNT(*) FROM temp_view").fetchone()[0]
                
                # Determine file type
                if 'loading_percentage' in column_names:
                    category = 'transformer_hourly_stats'
                elif 'installation_date' in column_names:
                    category = 'transformer_base'
                else:
                    category = 'unknown_transformer'
                
                # Get sample data
                sample = conn.execute("SELECT * FROM temp_view LIMIT 2").fetchall()
                
                file_info = {
                    'file': os.path.basename(file),
                    'full_path': normalized_file,
                    'columns': column_names,
                    'row_count': row_count,
                    'sample': sample
                }
                
                file_categories[category].append(file_info)
                logger.info(f"Successfully analyzed {normalized_file}")
                
                # Clean up
                conn.execute("DROP VIEW IF EXISTS temp_view")
                
            except Exception as e:
                logger.error(f"Error analyzing file {file}: {str(e)}")
                continue
        
        # Analyze customer data
        logger.info("\nAnalyzing customer data files...")
        customer_files = glob.glob(os.path.join(customer_dir, "**/*.parquet"), recursive=True)
        
        for file in customer_files:
            try:
                normalized_file = normalize_path(file)
                logger.info(f"Analyzing file: {normalized_file}")
                
                # Try to read the parquet file schema first
                try:
                    schema = conn.execute(f"SELECT * FROM parquet_schema('{normalized_file}')").fetchall()
                except Exception as e:
                    logger.error(f"Failed to read schema from {normalized_file}: {str(e)}")
                    continue
                
                # Create temporary view
                try:
                    conn.execute(f"CREATE VIEW temp_view AS SELECT * FROM read_parquet('{normalized_file}')")
                except Exception as e:
                    logger.error(f"Failed to create view for {normalized_file}: {str(e)}")
                    continue
                
                # Get schema and row count
                columns = conn.execute("DESCRIBE temp_view").fetchall()
                column_names = [col[0] for col in columns]
                row_count = conn.execute("SELECT COUNT(*) FROM temp_view").fetchone()[0]
                
                # Determine file type
                if 'customer_id' in column_names and 'transformer_id' in column_names:
                    category = 'customer_transformer_map'
                elif 'customer_id' in column_names:
                    category = 'customer'
                else:
                    category = 'unknown_customer'
                
                # Get sample data
                sample = conn.execute("SELECT * FROM temp_view LIMIT 2").fetchall()
                
                file_info = {
                    'file': os.path.basename(file),
                    'full_path': normalized_file,
                    'columns': column_names,
                    'row_count': row_count,
                    'sample': sample
                }
                
                file_categories[category].append(file_info)
                logger.info(f"Successfully analyzed {normalized_file}")
                
                # Clean up
                conn.execute("DROP VIEW IF EXISTS temp_view")
                
            except Exception as e:
                logger.error(f"Error analyzing file {file}: {str(e)}")
                continue
        
        # Print summary
        print("\n=== Data Loading Preview ===")
        total_rows = 0
        
        for category, files in file_categories.items():
            category_rows = sum(f['row_count'] for f in files)
            total_rows += category_rows
            
            print(f"\n{category.upper()} Files:")
            print(f"Total files: {len(files)}")
            print(f"Total rows: {category_rows:,}")
            print("\nSample files:")
            
            for file_info in files[:3]:  # Show first 3 files of each category
                print(f"\nFile: {file_info['file']}")
                print(f"Rows: {file_info['row_count']:,}")
                print(f"Columns: {', '.join(file_info['columns'])}")
                print("Sample data:")
                for row in file_info['sample']:
                    print(f"  {row}")
            
            if len(files) > 3:
                print(f"... and {len(files) - 3} more files")
        
        print(f"\nTotal rows to be loaded: {total_rows:,}")
        
        return file_categories
        
    except Exception as e:
        logger.error(f"Failed to analyze parquet files: {str(e)}")
        raise
    finally:
        if 'conn' in locals():
            conn.close()

def load_parquet_files(file_categories):
    """Load all parquet files from the specified directories"""
    try:
        conn = connect_to_db(use_motherduck=True)
        
        # Base directories
        customer_dir = normalize_path(r"C:\Users\JohnApostolo\CascadeProjects\processed_data\customer_analysis")
        transformer_dir = normalize_path(r"C:\Users\JohnApostolo\CascadeProjects\processed_data\transformer_analysis")
        
        # Create staging tables
        logger.info("Creating staging tables...")
        
        # Load transformer data
        logger.info("Loading transformer data...")
        for file_info in file_categories['transformer_hourly_stats']:
            try:
                table_name = f"temp_transformer_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
                logger.info(f"Loading file: {file_info['full_path']}")
                
                # Load into temporary table
                conn.execute(f"""
                    CREATE TABLE {table_name} AS 
                    SELECT * FROM read_parquet('{file_info['full_path']}')
                """)
                
                # Insert into appropriate table
                conn.execute(f"""
                    INSERT INTO transformer_hourly_stats 
                    SELECT * FROM {table_name}
                """)
                
                # Drop temporary table
                conn.execute(f"DROP TABLE {table_name}")
                
            except Exception as e:
                logger.error(f"Error loading file {file_info['full_path']}: {str(e)}")
                continue
        
        for file_info in file_categories['transformer_base']:
            try:
                table_name = f"temp_transformer_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
                logger.info(f"Loading file: {file_info['full_path']}")
                
                # Load into temporary table
                conn.execute(f"""
                    CREATE TABLE {table_name} AS 
                    SELECT * FROM read_parquet('{file_info['full_path']}')
                """)
                
                # Insert into appropriate table
                conn.execute(f"""
                    INSERT INTO transformer_base 
                    SELECT * FROM {table_name}
                """)
                
                # Drop temporary table
                conn.execute(f"DROP TABLE {table_name}")
                
            except Exception as e:
                logger.error(f"Error loading file {file_info['full_path']}: {str(e)}")
                continue
        
        # Load customer data
        logger.info("Loading customer data...")
        for file_info in file_categories['customer']:
            try:
                table_name = f"temp_customer_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
                logger.info(f"Loading file: {file_info['full_path']}")
                
                # Load into temporary table
                conn.execute(f"""
                    CREATE TABLE {table_name} AS 
                    SELECT * FROM read_parquet('{file_info['full_path']}')
                """)
                
                # Insert into appropriate table
                conn.execute(f"""
                    INSERT INTO customer 
                    SELECT * FROM {table_name}
                """)
                
                # Drop temporary table
                conn.execute(f"DROP TABLE {table_name}")
                
            except Exception as e:
                logger.error(f"Error loading file {file_info['full_path']}: {str(e)}")
                continue
        
        for file_info in file_categories['customer_transformer_map']:
            try:
                table_name = f"temp_customer_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
                logger.info(f"Loading file: {file_info['full_path']}")
                
                # Load into temporary table
                conn.execute(f"""
                    CREATE TABLE {table_name} AS 
                    SELECT * FROM read_parquet('{file_info['full_path']}')
                """)
                
                # Insert into appropriate table
                conn.execute(f"""
                    INSERT INTO customer_transformer_map 
                    SELECT * FROM {table_name}
                """)
                
                # Drop temporary table
                conn.execute(f"DROP TABLE {table_name}")
                
            except Exception as e:
                logger.error(f"Error loading file {file_info['full_path']}: {str(e)}")
                continue
        
        logger.info("Data loading completed successfully!")
        
    except Exception as e:
        logger.error(f"Failed to load parquet files: {str(e)}")
    finally:
        if 'conn' in locals():
            conn.close()

if __name__ == "__main__":
    file_categories = preview_parquet_files()
    load_parquet_files(file_categories)
