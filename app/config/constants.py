"""
Constants for the Transformer Loading Analysis Application
"""

# Loading thresholds - DO NOT MODIFY without engineering approval
LOADING_THRESHOLDS = {
    'Critical': 120,
    'Overloaded': 100,
    'Warning': 80,
    'Pre-Warning': 50,
    'Normal': 0
}

# Status colors for light theme
STATUS_COLORS = {
    'Critical': '#ff0000',      # Pure red
    'Overloaded': '#ffa500',    # Orange
    'Warning': '#ffd700',       # Gold
    'Pre-Warning': '#9370db',   # Medium purple
    'Normal': '#32cd32',        # Lime green
    'Unknown': '#808080'        # Gray
}

# Chart colors
CHART_COLORS = {
    'power': '#1e88e5',     # Blue
    'current': '#d81b60',   # Red
    'voltage': '#00c853',   # Green
    'grid': '#eeeeee',      # Light gray
    'indicator': '#9ca3af', # Medium gray
    'text': '#2f4f4f'       # Dark slate gray
}

# Gmail API scope
SCOPES = ['https://www.googleapis.com/auth/gmail.send']

# Email configuration
ALERT_EMAIL = "jhnapo2213@gmail.com"
