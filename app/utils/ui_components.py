"""
Reusable UI components for the Transformer Loading Analysis Application
"""

import streamlit as st

def create_tile(title: str, value: str, is_clickable: bool = False):
    """Create a styled tile using pure Streamlit components"""
    
    # Create unique key for this tile
    key = f"tile_{title.lower().replace(' ', '_')}"
    
    if is_clickable:
        # For clickable tiles, use a button with container styling
        clicked = st.button(
            label="",  # Empty label since we'll add content inside
            key=key,
            use_container_width=True
        )
        
        # Add content inside a container to preserve styling
        with st.container():
            st.caption(title)  # Small gray text for title
            st.write(value)    # Larger text for value
            
        return clicked
    else:
        # For non-clickable tiles, just show the content
        with st.container():
            st.caption(title)
            st.write(value)
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
