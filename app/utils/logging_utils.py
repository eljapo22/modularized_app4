"""
Logging utilities for the Transformer Loading Analysis Application
"""

import time
import logging
import functools
from datetime import datetime

# Configure logging
logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)

# Create console handler with a higher log level
console_handler = logging.StreamHandler()
console_handler.setLevel(logging.INFO)

# Create formatter
formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
console_handler.setFormatter(formatter)

# Add handlers to the logger
logger.addHandler(console_handler)

class Timer:
    """Context manager for timing code execution"""
    def __init__(self, description):
        self.description = description
        
    def __enter__(self):
        self.start = time.time()
        return self
        
    def __exit__(self, *args):
        self.end = time.time()
        self.duration = self.end - self.start
        logger.info(f"{self.description} completed in {self.duration:.2f} seconds")

def log_performance(func):
    """Decorator to log function execution time"""
    @functools.wraps(func)
    def wrapper(*args, **kwargs):
        start_time = time.time()
        result = func(*args, **kwargs)
        end_time = time.time()
        duration = end_time - start_time
        logger.info(f"{func.__name__} completed in {duration:.2f} seconds")
        return result
    return wrapper
