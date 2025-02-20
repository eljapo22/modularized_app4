# Visualization Directory

This directory contains visualization components and chart generation for the Transformer Loading Analysis Application.

## Components

### charts.py
- Chart generation components
- Interactive visualizations
- Key functions:
  - `add_hour_indicator()`: Time marker
  - `create_base_figure()`: Base plots
  - `display_loading_status_line_chart()`: Loading visualization
  - `display_power_time_series()`: Power trends
  - `display_current_time_series()`: Current analysis
  - `display_voltage_time_series()`: Voltage tracking
  - `display_transformer_dashboard()`: Complete dashboard

### tables.py
- Table generation
- Data presentation
- Features:
  - Sortable columns
  - Filtering
  - Pagination
  - Formatting
  - Color coding

## Code Interactions

### charts.py
Interacts with:
- `config/constants.py`: For colors and thresholds
- `utils/ui_utils.py`: For chart components
- `services/cloud_data_service.py`: For data
- `cloud_main.py`: For display

Key Variables and Types:
```python
# Chart Data Types
figure: go.Figure            # Plotly figure object
data: pd.DataFrame          # Source data with columns:
    timestamp: datetime     # X-axis time values
    loading_percentage: float  # Y-axis loading values
    voltage_v: float       # Y-axis voltage values
    current_a: float       # Y-axis current values
    power_kw: float       # Y-axis power values

# Chart Configuration
layout: Dict[str, Any] = {
    'height': 400,
    'margin': dict(l=40, r=40, t=40, b=40),
    'hovermode': 'x unified',
    'showlegend': True
}

# Time Marker
selected_hour: int         # Hour to mark (0-23)
marker_color: str         # Line color ('#666666')
marker_style: str        # Line style ('dash')
```

### tables.py
Interacts with:
- `services/cloud_data_service.py`: For data
- `utils/ui_utils.py`: For styling
- `config/constants.py`: For colors

Key Variables:
```python
# Table Configuration
table_config: Dict[str, Any] = {
    'page_size': 10,
    'sort_action': 'native',
    'sort_mode': 'multi',
    'filter_action': 'native'
}

# Column Definitions
columns: List[Dict[str, str]] = [
    {'name': 'Time', 'id': 'timestamp'},
    {'name': 'Loading (%)', 'id': 'loading_percentage'},
    {'name': 'Power (kW)', 'id': 'power_kw'},
    {'name': 'Status', 'id': 'status'}
]
```

## Chart Generation Examples

### Loading Status Chart:
```python
def display_loading_status_line_chart(data: pd.DataFrame, selected_hour: int = None):
    fig = go.Figure()
    
    # Add loading percentage line
    fig.add_trace(go.Scatter(
        x=data['timestamp'],
        y=data['loading_percentage'],
        name='Loading %',
        line=dict(color='#2c3e50', width=2)
    ))
    
    # Add threshold lines
    for threshold, color in THRESHOLDS.items():
        fig.add_hline(y=threshold, line_dash='dash',
                     line_color=color, opacity=0.5)
    
    # Add hour marker if specified
    if selected_hour is not None:
        add_hour_indicator(fig, data, selected_hour)
```

### Power Time Series:
```python
def display_power_time_series(data: pd.DataFrame):
    fig = create_base_figure()
    fig.add_trace(go.Scatter(
        x=data['timestamp'],
        y=data['power_kw'],
        name='Power (kW)',
        line=dict(color='#3498db', width=2)
    ))
```

## Chart Customization
Common chart parameters:
```python
# Axis Configuration
xaxis_config = {
    'title': 'Time',
    'showgrid': True,
    'gridcolor': '#f0f0f0'
}

yaxis_config = {
    'title': 'Loading (%)',
    'showgrid': True,
    'gridcolor': '#f0f0f0',
    'rangemode': 'tozero'
}

# Theme Colors
COLORS = {
    'primary': '#2c3e50',
    'secondary': '#3498db',
    'warning': '#f1c40f',
    'danger': '#e74c3c',
    'success': '#2ecc71'
}
```

## Integration Points
1. Dashboard Integration:
```python
# In cloud_main.py
from visualization.charts import display_transformer_dashboard

def show_dashboard():
    results = data_service.get_transformer_data(...)
    display_transformer_dashboard(results, selected_hour)
```

2. Alert Visualization:
```python
# In cloud_alert_service.py
from visualization.charts import create_loading_chart

def visualize_alert(results_df, alert_time):
    fig = create_loading_chart(results_df)
    add_hour_indicator(fig, results_df, alert_time.hour)
```

## Visualization Features

### Loading Status Charts
- Real-time loading percentage
- Threshold indicators
- Time markers
- Alert status colors

### Power Analysis
- Power consumption trends
- Time series analysis
- Usage patterns
- Comparative views

### Voltage and Current
- Three-phase voltage
- Current measurements
- Power factor
- Load balancing

### Dashboard Integration
- Combined views
- Interactive elements
- Filter controls
- Export options

## Usage
Visualizations are used to:
1. Display transformer status
2. Show loading conditions
3. Present alert information
4. Track metrics over time
5. Compare performance

## Chart Types
- Line charts
- Time series
- Status indicators
- Metric displays
- Heat maps
- Comparative views
