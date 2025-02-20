# Cloud Data Service Queries

This document lists all SQL queries used in the Transformer Loading Analysis Application's cloud data service.

## Dashboard Main Queries

### Date Range Query
```sql
-- Used for: Date selector min/max range
-- Cache Duration: 24h
SELECT 
    MIN(DATE(hour_timestamp)) as min_date,
    MAX(DATE(hour_timestamp)) as max_date
FROM transformer_hourly_stats;
```

### Feeder Transformer List
```sql
-- Used for: Transformer dropdown for selected feeder
-- Cache Duration: 24h
SELECT DISTINCT t.transformer_id
FROM transformer t
JOIN transformer_base tb ON t.transformer_id = tb.transformer_id
WHERE t.feeder_id = ?
ORDER BY t.transformer_id;
```

### Current Hour Metrics
```sql
-- Used for: Main dashboard metrics tiles
-- Cache Duration: 1h
SELECT 
    loading_percentage as current_loading,
    power_factor,
    avg_loading_24h,
    max_loading_24h,
    alert_level
FROM transformer_hourly_stats
WHERE transformer_id = ?
AND DATE(hour_timestamp) = ?
AND EXTRACT(HOUR FROM hour_timestamp) = ?;
```

### Daily Loading Profile
```sql
-- Used for: Loading status line chart
-- Cache Duration: 1h
SELECT 
    hour_timestamp,
    loading_percentage,
    alert_level
FROM transformer_hourly_stats
WHERE transformer_id = ?
AND DATE(hour_timestamp) = ?
ORDER BY hour_timestamp;
```

## Alert System Queries

### Alert Processing Query
```sql
-- Used for: Search & Alert button
-- Cache Duration: None (Real-time)
SELECT 
    ths.*,
    t.feeder_id,
    tcs.customer_count
FROM transformer_hourly_stats ths
JOIN transformer t ON ths.transformer_id = t.transformer_id
LEFT JOIN transformer_customer_stats tcs ON ths.transformer_id = tcs.transformer_id
WHERE ths.transformer_id = ?
AND DATE(ths.hour_timestamp) = ?
AND EXTRACT(HOUR FROM ths.hour_timestamp) = ?
AND ths.alert_level IN ('Critical', 'Overloaded', 'Warning');
```

## Customer Data Queries

### Customer Impact Query
```sql
-- Used for: Customer section of dashboard
-- Cache Duration: 1h
SELECT 
    c.customer_id,
    c.service_type,
    cr.consumption_kwh,
    cr.peak_demand_kw
FROM customer c
JOIN customer_transformer_map ctm ON c.customer_id = ctm.customer_id
LEFT JOIN customer_reading cr ON c.customer_id = cr.customer_id
WHERE ctm.transformer_id = ?
AND DATE(cr.timestamp) = ?;
```

## Time Series Queries

### Transformer Time Series
```sql
-- Used for: Power/Current/Voltage charts
-- Cache Duration: 1h
SELECT 
    hour_timestamp,
    power_kw,
    power_factor
FROM transformer_hourly_stats
WHERE transformer_id = ?
AND DATE(hour_timestamp) = ?
ORDER BY hour_timestamp;
```

### 24-Hour Loading Summary
```sql
-- Used for: Loading status summary
-- Cache Duration: 1h
SELECT 
    alert_level,
    COUNT(*) as hours_in_state
FROM transformer_hourly_stats
WHERE transformer_id = ?
AND hour_timestamp >= ? - INTERVAL '24 hours'
AND hour_timestamp <= ?
GROUP BY alert_level
ORDER BY 
    CASE alert_level
        WHEN 'Critical' THEN 1
        WHEN 'Overloaded' THEN 2
        WHEN 'Warning' THEN 3
        WHEN 'Pre-Warning' THEN 4
        WHEN 'Normal' THEN 5
    END;
```

## Feeder Data Queries

### Feeder Data Query
```sql
-- Used for: Getting feeder data for last 30 days
-- Cache Duration: 1h
SELECT *
FROM transformer_readings
WHERE feeder_id = ?
AND timestamp >= CURRENT_DATE - INTERVAL '30 days';
```

### Available Feeders Query
```sql
-- Used for: Feeder dropdown list
-- Cache Duration: 24h
SELECT DISTINCT feeder_id
FROM transformer_readings
ORDER BY feeder_id;
```

## Transformer Detail Queries

### Transformer Details Query
```sql
-- Used for: Detailed transformer data
-- Cache Duration: 1h
SELECT 
    timestamp,
    transformer_id,
    power_kw,
    current_a,
    voltage_v,
    power_factor,
    size_kva,
    loading_percentage,
    feeder_id
FROM transformer_readings
WHERE transformer_id = ?
AND DATE(timestamp) = ?
ORDER BY timestamp;
```

## Notes

1. All queries use parameterized inputs for security
2. Caching durations are set based on data update frequency:
   - 24h for static/reference data
   - 1h for time-series data
   - No cache for real-time alerts
3. All time-based queries use indexed columns
4. Alert levels are defined as:
   - Critical: >= 120%
   - Overloaded: >= 100%
   - Warning: >= 80%
   - Pre-Warning: >= 50%
   - Normal: < 50%
