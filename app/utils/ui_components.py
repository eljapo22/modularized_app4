"""
Reusable UI components for the Transformer Loading Analysis Application
"""

import streamlit as st

def create_tile(title: str, value: str, is_clickable: bool = False):
    """Create a styled tile using pure Streamlit components"""
    
    # Style disabled buttons to have same text color
    st.markdown("""
        <style>
        /* Make disabled button text same color as enabled */
        .stButton button:disabled {
            color: rgb(49, 51, 63) !important;
        }
        </style>
    """, unsafe_allow_html=True)
    
    # Create unique key for this tile
    key = f"tile_{title.lower().replace(' ', '_')}"
    
    # Create button content
    button_label = f"{title}  \n{value}"  # Use markdown double space for line break
    
    # Return button with consistent styling
    return st.button(
        label=button_label,
        key=key,
        disabled=not is_clickable,
        use_container_width=True,
        type="secondary"
    )

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
    """Create a banner using Streamlit button styling"""
    st.button(
        title,
        disabled=True,
        use_container_width=True,
        type="secondary"
    )

def create_bordered_header(title: str):
    """Create a header with a professional border using Streamlit elements"""
    st.divider()
    st.header(title)
    st.divider()
