erDiagram
    TRANSFORMER ||--o{ TRANSFORMER_READING : has
    TRANSFORMER ||--o{ CUSTOMER : serves
    FEEDER ||--o{ TRANSFORMER : contains
    CUSTOMER ||--o{ CUSTOMER_READING : has

    TRANSFORMER {
        string transformer_id PK "S[sector]F[feeder]ATF[number]"
        string feeder_id FK
        float size_kva
        float nominal_voltage
        float rated_current
        timestamp created_at
        timestamp updated_at
    }

    TRANSFORMER_READING {
        string reading_id PK
        string transformer_id FK
        timestamp timestamp
        float power_kw
        float current_a
        float voltage_v
        float power_factor
        float loading_percentage
        string load_range "Critical/Overloaded/Warning/Pre-Warning/Normal"
    }

    FEEDER {
        string feeder_id PK "Feeder[1-4]"
        string name
        float rated_capacity
        timestamp created_at
        timestamp updated_at
    }

    CUSTOMER {
        string customer_id PK
        string transformer_id FK
        float x_coordinate
        float y_coordinate
        string service_type
        timestamp created_at
        timestamp updated_at
    }

    CUSTOMER_READING {
        string reading_id PK
        string customer_id FK
        timestamp timestamp
        float power_kw
        float current_a
        float power_factor
    }
## Schema Details

### TRANSFORMER
- Primary identifier for transformers with sector-feeder-number format
- Stores rated specifications and physical attributes
- Links to feeder for hierarchical organization

### TRANSFORMER_READING
- Time-series data for transformer measurements
- Calculated fields for loading percentage and status
- Load ranges:
  - Critical: ≥ 120%
  - Overloaded: ≥ 100%
  - Warning: ≥ 80%
  - Pre-Warning: ≥ 50%
  - Normal: < 50%

### FEEDER
- Represents main distribution feeders
- Contains capacity and identification information
- Parent entity for transformers

### CUSTOMER
- Customer location and service information
- Linked to serving transformer
- Spatial coordinates for mapping

### CUSTOMER_READING
- Time-series data for customer power consumption
- Tracks individual customer load profiles
- Enables customer-level analysis

## Relationships
1. One FEEDER can have many TRANSFORMERS
2. One TRANSFORMER can have many TRANSFORMER_READINGS
3. One TRANSFORMER can serve many CUSTOMERS
4. One CUSTOMER can have many CUSTOMER_READINGS

## Data Organization
- Transformer readings stored in parquet files by month
- Customer readings organized by feeder and transformer
- File naming convention: `{transformer_id}_{YYYY-MM}.parquet`
