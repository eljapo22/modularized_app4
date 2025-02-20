"""
Reusable UI components for the Transformer Loading Analysis Application
"""

import streamlit as st

def create_tile(title: str, value: str, has_multiline_title: bool = False, is_clickable: bool = False):
    """Create a styled tile using Streamlit components"""
    st.markdown(
        f"""
        <div style="
            background-color: #f8f9fa;
            padding: 1rem;
            border-radius: 0.5rem;
            box-shadow: 0 2px 4px rgba(0,0,0,0.1);
            height: 100%;
            {'cursor: pointer;' if is_clickable else ''}
        ">
            <h3 style="
                margin: 0;
                color: #6c757d;
                font-size: 0.9rem;
                font-weight: 600;
                {'white-space: normal;' if has_multiline_title else 'white-space: nowrap;'}
                overflow: hidden;
                text-overflow: ellipsis;
            ">{title}</h3>
            <p style="
                margin: 0.5rem 0 0 0;
                color: #212529;
                font-size: 1.1rem;
                font-weight: 500;
            ">{value}</p>
        </div>
        """,
        unsafe_allow_html=True
    )

def create_banner(title: str):
    """Create a professional banner with title"""
    st.markdown(
        f"""
        <div style="
            background-color: #f8f9fa;
            padding: 1.5rem;
            border-radius: 0.5rem;
            margin-bottom: 2rem;
            box-shadow: 0 2px 4px rgba(0,0,0,0.1);
        ">
            <h1 style="
                margin: 0;
                color: #212529;
                font-size: 2rem;
                font-weight: 600;
            ">{title}</h1>
        </div>
        """,
        unsafe_allow_html=True
    )

def create_section_banner(title: str):
    """Create a section banner with professional styling"""
    st.markdown(
        f"""
        <div style="
            background-color: #e9ecef;
            padding: 1rem;
            border-radius: 0.5rem;
            margin: 1rem 0;
        ">
            <h2 style="
                margin: 0;
                color: #495057;
                font-size: 1.25rem;
                font-weight: 600;
            ">{title}</h2>
        </div>
        """,
        unsafe_allow_html=True
    )
