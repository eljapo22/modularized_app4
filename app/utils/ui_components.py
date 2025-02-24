"""
Reusable UI components for the Transformer Loading Analysis Application
"""

import streamlit as st

def create_tile(title: str, value: str, is_clickable: bool = False):
    """Create a styled tile using Streamlit components"""
    
    # Create unique key for this tile
    key = f"tile_{title.lower().replace(' ', '_')}"
    
    # Custom styling for the tile
    st.markdown(
        """
        <style>
        div[data-testid="stButton"] > button {
            background-color: white;
            color: #212529;
            border: 1px solid #dee2e6;
            border-radius: 0.25rem;
            padding: 1rem;
            width: 100%;
            text-align: left;
            font-weight: normal;
        }
        div[data-testid="stButton"] > button:hover {
            background-color: #f8f9fa;
            border: 1px solid #dee2e6;
        }
        div[data-testid="stButton"] > button:active {
            background-color: #f8f9fa;
            border: 1px solid #dee2e6;
        }
        div[data-testid="stButton"] > button:focus {
            box-shadow: none;
        }
        </style>
        """,
        unsafe_allow_html=True
    )
    
    # Create button content with title and value
    button_content = f"""
    <div>
        <div style='color: #6c757d; font-size: 0.875rem;'>{title}</div>
        <div style='font-size: 1.25rem;'>{value}</div>
    </div>
    """
    
    # Return button click state if clickable, otherwise just display content
    if is_clickable:
        return st.button(
            button_content,
            key=key,
            use_container_width=True
        )
    else:
        st.button(
            button_content,
            key=key,
            disabled=True,
            use_container_width=True
        )
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
