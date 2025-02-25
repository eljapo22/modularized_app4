"""
Minimal test script for customer data functionality
"""
import logging
from datetime import datetime, date
import streamlit as st

from app.services.services import CloudDataService
from app.config.cloud_config import use_motherduck

# Set up logging to see all messages
logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)

def test_customer_data():
    print("\nTesting Customer Data...")
    print("-" * 50)
    
    # First verify MotherDuck is enabled
    try:
        enabled = use_motherduck()
        print(f"MotherDuck enabled: {enabled}")
    except Exception as e:
        print(f"Error checking MotherDuck: {str(e)}")
        return
        
    # Initialize service
    try:
        service = CloudDataService()
        print("CloudDataService initialized")
        
        # Print available methods
        print("\nAvailable methods:")
        methods = [method for method in dir(service) if not method.startswith('_')]
        print(methods)
        
        # Test parameters
        test_data = {
            'transformer_id': 'S1F1ATF001',
            'start_date': date.today(),
            'end_date': date.today(),
            'feeder': 'Feeder 1'
        }
        print(f"\nTest parameters: {test_data}")
        
        # Try to get customer data
        try:
            customer_data = service.get_customer_data(
                transformer_id=test_data['transformer_id'],
                start_date=test_data['start_date'],
                end_date=test_data['end_date'],
                feeder=test_data['feeder']
            )
            print("\nCustomer data retrieved successfully")
            print(f"Data shape: {customer_data.shape if hasattr(customer_data, 'shape') else 'No data'}")
            
        except AttributeError as e:
            print(f"\nMethod not found error: {str(e)}")
            print("This suggests the method is not properly defined in the class")
            
        except Exception as e:
            print(f"\nError getting customer data: {str(e)}")
            
    except Exception as e:
        print(f"Error initializing service: {str(e)}")

if __name__ == "__main__":
    test_customer_data()
