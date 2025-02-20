"""
Performance monitoring utilities for the Transformer Loading Analysis Application
"""

import logging
import time
import functools
from typing import Callable, Any

# Initialize logger
logger = logging.getLogger(__name__)

def log_performance(func: Callable) -> Callable:
    """
    Decorator to log the execution time of functions
    
    Args:
        func: The function to be decorated
        
    Returns:
        Wrapped function that logs execution time
    """
    @functools.wraps(func)
    def wrapper(*args, **kwargs) -> Any:
        start_time = time.time()
        try:
            result = func(*args, **kwargs)
            end_time = time.time()
            execution_time = end_time - start_time
            logger.info(f"Function {func.__name__} executed in {execution_time:.2f} seconds")
            return result
        except Exception as e:
            end_time = time.time()
            execution_time = end_time - start_time
            logger.error(f"Function {func.__name__} failed after {execution_time:.2f} seconds with error: {str(e)}")
            raise
    return wrapper
