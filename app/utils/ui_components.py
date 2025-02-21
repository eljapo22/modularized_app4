"""
Reusable UI components for the Transformer Loading Analysis Application
"""

import streamlit as st

def create_tile(title: str, value: str, has_multiline_title: bool = False, is_clickable: bool = False):
    """Create a styled tile using Streamlit components"""
    with st.container():
        st.markdown(
            f"""
            <style>
            .stMetric .metric-container {
                background-color: white !important;
                border: 1px solid #dee2e6 !important;
                border-radius: 0.25rem !important;
                padding: 0.75rem !important;
                margin-bottom: 1rem !important;
            }
            .stMetric .metric-title {
                color: #6c757d !important;
                font-size: 0.75rem !important;
                font-weight: 400 !important;
                text-transform: uppercase !important;
                letter-spacing: 0.5px !important;
            }
            .stMetric .metric-value {
                color: #212529 !important;
                font-size: 1.25rem !important;
                font-weight: 500 !important;
                font-family: monospace !important;
            }
            </style>
            """,
            unsafe_allow_html=True
        )
        st.metric(title, value)

def create_section_title(title: str):
    """Create a section title with the same styling as tiles"""
    st.subheader(title)

def create_banner(title: str):
    """Create a professional banner with title"""
    st.title(title)

def create_section_banner(title: str):
    """Create a section banner with professional styling"""
    st.header(title)
