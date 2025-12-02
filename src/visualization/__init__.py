"""
Visualization module for edge path bundling.

This module provides visualization components for edge bundling including:
- Bezier curve generation following the paper's approach
- Plotly-based interactive visualizations  
- Support for smooth curves and comparison views
"""

from .curves import (
    create_smooth_bundled_path,
    generate_control_points,
    apply_recursive_smoothing,
    generate_bezier_curve
)

from .plotly_renderer import (
    create_network_visualization,
    create_comparison_visualization
)

__all__ = [
    'create_smooth_bundled_path',
    'generate_control_points', 
    'apply_recursive_smoothing',
    'generate_bezier_curve',
    'create_network_visualization',
    'create_comparison_visualization'
]