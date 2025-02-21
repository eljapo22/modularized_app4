"""
Data models for transformer and customer data
"""
from dataclasses import dataclass
from datetime import datetime
from typing import List, Optional

@dataclass
class TransformerData:
    """Model for transformer measurements"""
    timestamp: datetime
    transformer_id: str
    power_kw: float
    power_factor: float
    power_kva: float
    voltage_v: float
    current_a: float
    index_level_0: Optional[int] = None

@dataclass
class CustomerData:
    """Model for customer measurements"""
    timestamp: datetime
    customer_id: str
    transformer_id: str
    power_kw: float
    power_factor: float
    power_kva: float
    voltage_v: float
    current_a: float
    index_level_0: Optional[int] = None

@dataclass
class AggregatedCustomerData:
    """Aggregated metrics for customers connected to a transformer"""
    transformer_id: str
    customer_count: int
    total_power_kw: float
    avg_power_factor: float
    total_power_kva: float
    avg_voltage_v: float
    total_current_a: float
