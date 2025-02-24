"""
Data models for the application
"""
from dataclasses import dataclass
from typing import List
from datetime import datetime
import pandas as pd

@dataclass
class TransformerData:
    """Data model for transformer measurements"""
    transformer_id: List[str]
    timestamp: List[datetime]
    size_kva: List[float]
    load_range: List[str]
    loading_percentage: List[float]
    current_a: List[float]
    voltage_v: List[float]
    power_kw: List[float]
    power_kva: List[float]
    power_factor: List[float]
    
    def __post_init__(self):
        self.data = pd.DataFrame({
            'transformer_id': self.transformer_id,
            'timestamp': self.timestamp,
            'size_kva': self.size_kva,
            'load_range': self.load_range,
            'loading_percentage': self.loading_percentage,
            'current_a': self.current_a,
            'voltage_v': self.voltage_v,
            'power_kw': self.power_kw,
            'power_kva': self.power_kva,
            'power_factor': self.power_factor
        })

@dataclass
class CustomerData:
    """Data model for customer measurements"""
    timestamp: List[datetime]
    customer_id: List[str]
    transformer_id: List[str]
    power_kw: List[float]
    power_factor: List[float]
    power_kva: List[float]
    index_level_0: List[int]  # Maps to __index_level_0__
    voltage_v: List[float]
    current_a: List[float]
    
    def __post_init__(self):
        self.data = pd.DataFrame({
            'timestamp': self.timestamp,
            'customer_id': self.customer_id,
            'transformer_id': self.transformer_id,
            'power_kw': self.power_kw,
            'power_factor': self.power_factor,
            'power_kva': self.power_kva,
            '__index_level_0__': self.index_level_0,
            'voltage_v': self.voltage_v,
            'current_a': self.current_a
        })

@dataclass
class AggregatedCustomerData:
    """Data model for hourly aggregated customer data"""
    timestamp: List[datetime]
    customer_id: List[str]
    avg_power_kw: List[float]
    avg_power_factor: List[float]
    avg_power_kva: List[float]
    avg_current_a: List[float]
    avg_voltage_v: List[float]
    
    def __post_init__(self):
        self.data = pd.DataFrame({
            'timestamp': self.timestamp,
            'customer_id': self.customer_id,
            'avg_power_kw': self.avg_power_kw,
            'avg_power_factor': self.avg_power_factor,
            'avg_power_kva': self.avg_power_kva,
            'avg_current_a': self.avg_current_a,
            'avg_voltage_v': self.avg_voltage_v
        })
