# Data File Structure Documentation

## Overview
This document outlines the file naming conventions and structure for transformer and customer data files used in the Transformer Loading Analysis application.

## Base Directory Structure
```
processed_data/
├── transformer_analysis/
│   └── hourly/
│       ├── feeder1/
│       ├── feeder2/
│       ├── feeder3/
│       └── feeder4/
└── customer_analysis/
    └── hourly/
        ├── feeder1/
        ├── feeder2/
        ├── feeder3/
        └── feeder4/
```

## Transformer Data Files

### File Location
- Base Path: `processed_data/transformer_analysis/hourly/{feeder}/`
- Example: `processed_data/transformer_analysis/hourly/feeder1/`

### Naming Convention
- Format: `YYYY-MM-DD.parquet`
- Example: `2024-01-01.parquet`

### Key Characteristics
- Files contain data for ALL transformers within a feeder
- Data is stored at daily granularity only
- Each feeder directory contains daily files for its transformers
- Files are organized chronologically
- Data spans from January 2024 to June 2024

### Example Files
```
2024-01-01.parquet
2024-01-02.parquet
2024-01-03.parquet
...
2024-06-30.parquet
```

## Customer Data Files

### File Location
- Base Path: `processed_data/customer_analysis/hourly/{feeder}/`
- Example: `processed_data/customer_analysis/hourly/feeder1/`

### Naming Convention
- Format: `S1F#ATF###_YYYY-MM.parquet`
- Components:
  - `S1`: Substation identifier (Substation 1)
  - `F#`: Feeder number (1-4)
  - `ATF`: Distribution transformer prefix
  - `###`: Three-digit transformer number
  - `YYYY-MM`: Year and month
- Example: `S1F1ATF001_2024-01.parquet`

### Key Characteristics
- Each file is specific to ONE transformer
- Data is stored at monthly granularity
- Files are organized by feeder and transformer
- Each transformer has its own set of monthly files
- Data spans from January 2024 to June 2024

### Example Files
```
S1F1ATF001_2024-01.parquet
S1F1ATF001_2024-02.parquet
S1F1ATF001_2024-03.parquet
...
S1F1ATF090_2024-06.parquet
```

## Important Notes
1. Transformer files must be maintained at daily granularity only. Monthly aggregated files should not be present.
2. Customer files are maintained at monthly granularity, with each file containing data for a specific transformer.
3. Both datasets follow a consistent structure across all feeders.
4. File naming conventions must be strictly followed to ensure proper data retrieval by the application.
