"""
Generate sample transformer data for testing
"""

import pandas as pd
import numpy as np
from datetime import datetime, timedelta
import os
from pathlib import Path

# Base directory for data
base_dir = Path(__file__).parent.parent / "processed_data" / "transformer_analysis" / "hourly"

# Sample dates
start_date = datetime(2024, 1, 1)
end_date = datetime(2024, 6, 28)
dates = pd.date_range(start=start_date, end=end_date, freq='D')

# Sample transformer IDs and their capacities for each feeder
transformers = {
    'feeder1': {
        'TX001': {'size_kva': 500},
        'TX002': {'size_kva': 750},
        'TX003': {'size_kva': 1000}
    },
    'feeder2': {
        'TX004': {'size_kva': 300},
        'TX005': {'size_kva': 500},
        'TX006': {'size_kva': 750}
    },
    'feeder3': {
        'TX007': {'size_kva': 1000},
        'TX008': {'size_kva': 1500},
        'TX009': {'size_kva': 2000}
    },
    'feeder4': {
        'TX010': {'size_kva': 500},
        'TX011': {'size_kva': 750},
        'TX012': {'size_kva': 1000}
    }
}

# Generate data for each feeder and date
for feeder, transformer_dict in transformers.items():
    feeder_dir = base_dir / feeder
    feeder_dir.mkdir(exist_ok=True)
    
    for date in dates:
        # Create hourly data for each transformer
        data = []
        for transformer_id, specs in transformer_dict.items():
            size_kva = specs['size_kva']
            
            # Generate random load profile
            base_load = np.random.uniform(30, 70)
            hourly_variation = np.random.normal(0, 10, 24)
            load_profile = base_load + hourly_variation
            
            # Ensure some transformers have high loading for testing alerts
            if np.random.random() < 0.2:
                load_profile *= 1.5
                
            # Generate power, current, and voltage data
            for hour in range(24):
                loading_pct = load_profile[hour]
                power_kw = (loading_pct/100) * size_kva  # Calculate power based on loading and capacity
                current_a = power_kw * 1000 / (400 * np.sqrt(3))  # Assuming 400V system
                voltage_v = 400 + np.random.normal(0, 5)
                
                data.append({
                    'transformer_id': transformer_id,
                    'datetime': date.replace(hour=hour),
                    'loading_pct': loading_pct,
                    'power_kw': power_kw,
                    'current_a': current_a,
                    'voltage_v': voltage_v,
                    'size_kva': size_kva,
                    'feeder': feeder
                })
        
        # Create DataFrame and save to parquet
        df = pd.DataFrame(data)
        output_file = feeder_dir / f"{date.strftime('%Y-%m-%d')}.parquet"
        df.to_parquet(output_file, index=False)
        print(f"Generated {output_file}")

print("Sample data generation complete!")
