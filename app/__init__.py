"""
Transformer Loading Analysis Application

File Organization:
- cloud/     # Cloud-specific implementations
- local/     # Local-specific implementations
- shared/    # Shared code used by both environments

Environment detection is handled at runtime to select appropriate implementations.
"""

# Version
__version__ = "0.1.0"

# Environment detection
import os
CLOUD_ENV = bool(os.getenv('STREAMLIT_CLOUD'))
