"""
Direct test script for data services
"""
import os
import logging
from datetime import datetime
from app.services.services import CloudDataService
from app.config.cloud_config import use_motherduck

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def test_data_services():
    print("\nTesting Data Services...")
    print("-" * 50)
    
    # Check if MotherDuck is enabled
    try:
        enabled = use_motherduck()
        if not enabled:
            print("✗ MotherDuck is not enabled")
            return
        print("✓ MotherDuck is enabled")
    except Exception as e:
        print(f"✗ Error checking MotherDuck status: {str(e)}")
        return
    
    try:
        data_service = CloudDataService()
        print("✓ Created CloudDataService")
        
        # Test parameters
        transformer_id = "S1F1ATF001"
        start_date = datetime.now().date()
        end_date = start_date
        feeder = "Feeder 1"
        
        print("\nTesting transformer data...")
        try:
            transformer_data = data_service.get_transformer_data_range(
                start_date=start_date,
                end_date=end_date,
                feeder=feeder,
                transformer_id=transformer_id
            )
            
            if not transformer_data.empty:
                print("✓ Successfully queried transformer data")
                print("\nSample data:")
                print(transformer_data.head())
            else:
                print("! No transformer data found")
        except Exception as e:
            print(f"✗ Error querying transformer data: {str(e)}")
            
        print("\nTesting customer data...")
        try:
            customer_data = data_service.get_customer_data(
                start_date=start_date,
                end_date=end_date,
                feeder=feeder,
                transformer_id=transformer_id
            )
            
            if not customer_data.empty:
                print("✓ Successfully queried customer data")
                print("\nSample data:")
                print(customer_data.head())
            else:
                print("! No customer data found")
        except Exception as e:
            print(f"✗ Error querying customer data: {str(e)}")
            
    except Exception as e:
        print(f"✗ Test failed: {str(e)}")

if __name__ == "__main__":
    test_data_services()
