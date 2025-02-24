"""
Reusable UI components for the Transformer Loading Analysis Application
"""

import streamlit as st

def create_tile(title: str, value: str, has_multiline_title: bool = False, is_clickable: bool = False):
    """Create a styled tile using Streamlit components"""
    
    # Create unique key for this tile
    key = f"tile_{title.lower().replace(' ', '_')}"
    
    # Define CSS for the tile
    css = """
    <style>
    .metric-container {
        background-color: white;
        border: 1px solid #dee2e6;
        border-radius: 0.25rem;
        padding: 0.75rem;
        margin-bottom: 1rem;
        cursor: pointer;
        transition: background-color 0.2s;
    }
    .metric-container:hover {
        background-color: #f8f9fa;
    }
    .metric-title {
        color: #6c757d;
        font-size: 0.875rem;
        font-weight: 500;
        margin-bottom: 0.25rem;
    }
    .metric-value {
        color: #212529;
        font-size: 1.25rem;
        font-weight: 600;
    }
    </style>
    """
    
    # Create HTML for the tile
    html = f"""
    <div class="metric-container" onclick="this.click()">
        <div class="metric-title">{title}</div>
        <div class="metric-value">{value}</div>
    </div>
    """
    
    # Add CSS to the page
    st.markdown(css, unsafe_allow_html=True)
    
    # Create a clickable container if needed
    if is_clickable:
        clicked = st.markdown(html, unsafe_allow_html=True)
        return clicked
    else:
        st.markdown(html, unsafe_allow_html=True)
        return False

def create_section_title(title: str):
    """Create a section title with the same styling as tiles"""
    st.subheader(title)

def create_banner(title: str):
    """Create a professional banner with title"""
    st.title(title)

def create_section_banner(title: str):
    """Create a section banner with professional styling"""
    st.header(title)

def create_colored_banner(title: str):
    """Create a banner using Streamlit button styling with left-aligned text"""
    st.markdown(
        f"""
        <div class="stButton">
            <button kind="secondary" class="st-emotion-cache-19rxjzo ef3psqc11" style="text-align: left; width: 100%; justify-content: flex-start;" disabled="">
                {title}
            </button>
        </div>
        """,
        unsafe_allow_html=True
    )

def create_bordered_header(title: str):
    """Create a header with a professional border using Streamlit elements"""
    with st.container():
        st.markdown(f"""---""")
        st.markdown(f"### {title}")
        st.markdown(f"""---""")
