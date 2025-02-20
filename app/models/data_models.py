"""
Data models for transformer and customer data
"""
from dataclasses import dataclass
from typing import List
from datetime import datetime

@dataclass
class TransformerData:
    """Data model for transformer measurements"""
    transformer_id: str
    timestamp: List[datetime]
    voltage_v: List[float]
    size_kva: List[float]
    loading_percentage: List[float]  # Rounded to xx.xx
    current_a: List[float]          # Rounded to xx.xx
    power_kw: List[float]          # Rounded to xx.xx
    power_kva: List[float]
    power_factor: List[float]
    load_range: List[str]

@dataclass
class CustomerData:
    """Data model for customer measurements"""
    index_level_0: List[int]
    current_a: List[float]      # Rounded to x.xx
    customer_id: List[str]
    hour: List[str]
    power_factor: List[float]
    power_kva: List[float]     # Rounded to x.xx
    power_kw: List[float]      # Rounded to x.xx
    size_kva: List[float]
    timestamp: List[datetime]
    transformer_id: List[str]
    voltage_v: List[int]

@dataclass
class AggregatedCustomerData:
    """Aggregated metrics for all customers on a transformer"""
    customer_count: int
    total_power_kw: float      # Sum of rounded power_kw values
    avg_power_factor: float
    total_current_a: float     # Sum of rounded current_a values
