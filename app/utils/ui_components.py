"""
Reusable UI components for the Transformer Loading Analysis Application
"""

import streamlit as st

def create_tile(title: str, value: str, has_multiline_title: bool = False, is_clickable: bool = False):
    """Create a styled tile using Streamlit components"""
    with st.container():
        css = """
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
        """
        st.markdown(css, unsafe_allow_html=True)
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

def create_section_header(title: str):
    """Create a section header with blue vertical bar."""
    st.markdown(
        f"""
        <div style="
            border-left: 4px solid #0d6efd;
            padding-left: 10px;
            margin: 20px 0 10px 0;
            ">
            <h3 style="
                margin: 0;
                color: #333;
                font-size: 16px;
                font-weight: 500;
                ">{title}</h3>
        </div>
        """,
        unsafe_allow_html=True
    )

def create_tile(label: str, value: str):
    """Create a metric tile with light gray background."""
    st.markdown(
        f"""
        <div style="
            background-color: #f8f9fa;
            padding: 15px;
            border-radius: 4px;
            margin: 5px 0;
            ">
            <div style="
                color: #6c757d;
                font-size: 12px;
                margin-bottom: 5px;
                ">{label}</div>
            <div style="
                color: #212529;
                font-size: 14px;
                font-weight: 500;
                ">{value}</div>
        </div>
        """,
        unsafe_allow_html=True
    )

def create_chart_container():
    """Create a container for charts with proper height."""
    return st.container().markdown(
        """
        <div style="height: 250px;">
        </div>
        """,
        unsafe_allow_html=True
    )

def create_two_column_charts():
    """Create a two-column layout for charts."""
    return st.columns(2)
