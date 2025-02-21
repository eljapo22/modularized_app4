"""
Reusable UI components for the Transformer Loading Analysis Application
"""

import streamlit as st

def create_tile(title: str, value: str, has_multiline_title: bool = False, is_clickable: bool = False):
    """Create a styled tile using Streamlit components"""
    html = f'''
    <div style="
        background-color: white;
        padding: 0.75rem;
        border: 1px solid #dee2e6;
        border-radius: 0.25rem;
        height: 100%;
        margin-bottom: 1rem;
        {'''cursor: pointer;''' if is_clickable else ''}
    ">
        <p style="
            margin: 0;
            color: #6c757d;
            font-size: 0.75rem;
            font-weight: 400;
            text-transform: uppercase;
            letter-spacing: 0.5px;
        ">{title}</p>
        <p style="
            margin: 0.25rem 0 0 0;
            color: #212529;
            font-size: 1.25rem;
            font-weight: 500;
            font-family: monospace;
        ">{value}</p>
    </div>
    '''
    st.markdown(html, unsafe_allow_html=True)

def create_section_title(title: str):
    """Create a section title with the same styling as tiles"""
    html = f'''
    <div style="
        background-color: white;
        padding: 0.75rem;
        border: 1px solid #dee2e6;
        border-radius: 0.25rem;
        margin-bottom: 1rem;
    ">
        <p style="
            margin: 0;
            color: #212529;
            font-size: 1rem;
            font-weight: 500;
        ">{title}</p>
    </div>
    '''
    st.markdown(html, unsafe_allow_html=True)

def create_banner(title: str):
    """Create a professional banner with title"""
    html = f'''
    <div style="
        background-color: white;
        padding: 1.5rem;
        border-radius: 0.25rem;
        margin-bottom: 2rem;
        border: 1px solid #dee2e6;
    ">
        <h1 style="
            margin: 0;
            color: #212529;
            font-size: 1.5rem;
            font-weight: 500;
        ">{title}</h1>
    </div>
    '''
    st.markdown(html, unsafe_allow_html=True)

def create_section_banner(title: str):
    """Create a section banner with professional styling"""
    html = f'''
    <div style="
        background-color: white;
        padding: 1rem;
        border-radius: 0.25rem;
        margin: 1rem 0;
        border: 1px solid #dee2e6;
    ">
        <h2 style="
            margin: 0;
            color: #495057;
            font-size: 1.25rem;
            font-weight: 500;
        ">{title}</h2>
    </div>
    '''
    st.markdown(html, unsafe_allow_html=True)
