"""
Visualization module for edge path bundling.

This module provides visualization components for edge bundling including:
- Bezier curve generation following the paper's approach
- Plotly-based interactive visualizations  
- Support for smooth curves and comparison views
"""

from .curves import create_smooth_bundled_path
from .plotly_renderer import create_network_visualization

__all__ = [
    'create_smooth_bundled_path',
    'create_network_visualization'
]