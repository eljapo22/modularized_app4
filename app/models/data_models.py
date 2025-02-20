"""
Data models for transformer and customer data
"""
from dataclasses import dataclass
from typing import List
from datetime import datetime

@dataclass
class TransformerData:
    """Transformer data model"""
    transformer_id: str
    timestamp: List[datetime]
    power_kw: List[float]
    power_kva: List[float]
    power_factor: List[float]
    voltage_v: List[float]
    current_a: List[float]
    loading_percentage: List[float]

@dataclass
class CustomerData:
    """Customer data model"""
    customer_ids: List[str]
    transformer_id: str
    timestamp: List[datetime]
    power_kw: List[float]
    power_factor: List[float]
    voltage_v: List[float]
    current_a: List[float]

@dataclass
class AggregatedCustomerData:
    """Aggregated customer metrics"""
    customer_count: int
    total_power_kw: float
    avg_power_factor: float
    total_current_a: float
