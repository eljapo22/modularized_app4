"""
Feature flags configuration for managing the transition to MotherDuck
"""

import streamlit as st
from typing import Dict, Any

class FeatureFlags:
    """Manage feature flags for the application"""
    
    @staticmethod
    def initialize_flags():
        """Initialize feature flags in session state"""
        if 'feature_flags' not in st.session_state:
            st.session_state.feature_flags = {
                'use_motherduck': False,  # Main switch for MotherDuck
                'motherduck_features': {
                    'transformer_data': False,  # Migrate transformer data first
                    'customer_data': False,     # Migrate customer data later
                    'alerts': False             # Migrate alerts last
                }
            }
    
    @staticmethod
    def get_flag(flag_name: str) -> bool:
        """Get the value of a feature flag"""
        FeatureFlags.initialize_flags()
        flags = st.session_state.feature_flags
        if '.' in flag_name:
            category, feature = flag_name.split('.')
            return flags.get(category, {}).get(feature, False)
        return flags.get(flag_name, False)
    
    @staticmethod
    def set_flag(flag_name: str, value: bool):
        """Set the value of a feature flag"""
        FeatureFlags.initialize_flags()
        flags = st.session_state.feature_flags
        if '.' in flag_name:
            category, feature = flag_name.split('.')
            if category in flags and isinstance(flags[category], dict):
                flags[category][feature] = value
        else:
            flags[flag_name] = value
    
    @staticmethod
    def get_all_flags() -> Dict[str, Any]:
        """Get all feature flags"""
        FeatureFlags.initialize_flags()
        return st.session_state.feature_flags.copy()

def is_using_motherduck() -> bool:
    """Convenience function to check if MotherDuck is enabled"""
    return FeatureFlags.get_flag('use_motherduck')
