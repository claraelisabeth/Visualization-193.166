"""
Plotly Visualization Renderer for Edge Path Bundling

This module handles visualization of bundled graphs using Plotly,
with support for smooth Bézier curves following the paper's approach.
"""

import plotly.graph_objects as go
import numpy as np
from typing import Dict, List, Tuple, Optional
from .curves import create_smooth_bundled_path


def create_network_visualization(graph, bundled_paths: List[Dict], title: str,
                                use_curves: bool = True, smoothing_level: int = 2,
                                num_samples: int = 100) -> go.Figure:
    """
    Create a Plotly network visualization with smooth bundled paths.
    
    Args:
        graph: NetworkX graph
        bundled_paths: List of bundled path dictionaries
        title: Plot title
        use_curves: Whether to use smooth curves (True) or line segments (False)
        smoothing_level: Bézier smoothing level (paper default: 2)
        num_samples: Curve sampling points (paper default: 100)
        
    Returns:
        Plotly Figure object
    """
    fig = go.Figure()
    
    # Get node positions
    node_positions = {node: (data['x'], data['y']) for node, data in graph.nodes(data=True)}
    
    # Define colors
    unbundled_color = 'lightgray'
    bundled_color = 'red'
    node_color = 'rgb(78, 110, 77)'  # Green from dashboard theme
    
    # Draw unbundled edges (straight lines)
    _add_unbundled_edges(fig, graph, node_positions, unbundled_color)
    
    # Draw bundled paths (smooth curves or line segments)
    if use_curves:
        _add_bundled_curves(fig, bundled_paths, node_positions, bundled_color, 
                           smoothing_level, num_samples)
    else:
        _add_bundled_segments(fig, bundled_paths, node_positions, bundled_color)
    
    # Draw nodes
    _add_nodes(fig, graph, node_positions, node_color)
    
    # Configure layout
    _configure_layout(fig, title, use_curves)
    
    return fig


def _add_unbundled_edges(fig: go.Figure, graph, node_positions: Dict, color: str):
    """Add unbundled edges as straight lines."""
    unbundled_edges = [(u, v) for u, v, data in graph.edges(data=True) 
                      if not data.get('bundled', False)]
    
    for u, v in unbundled_edges:
        if u in node_positions and v in node_positions:
            x0, y0 = node_positions[u]
            x1, y1 = node_positions[v]
            
            fig.add_trace(go.Scatter(
                x=[x0, x1, None], 
                y=[y0, y1, None],
                mode='lines',
                line=dict(color=color, width=1),
                hoverinfo='none',
                showlegend=False,
                name='unbundled'
            ))


def _add_bundled_curves(fig: go.Figure, bundled_paths: List[Dict], 
                       node_positions: Dict, color: str,
                       smoothing_level: int, num_samples: int):
    """Add bundled paths as smooth Bézier curves."""
    for i, bundle in enumerate(bundled_paths):
        path_nodes = bundle['path']
        
        # Generate smooth curve
        curve_points = create_smooth_bundled_path(
            path_nodes, node_positions, smoothing_level, num_samples
        )
        
        if curve_points:
            x_coords = [point[0] for point in curve_points]
            y_coords = [point[1] for point in curve_points]
            
            # Create hover text
            path_text = ' → '.join(map(str, path_nodes))
            detour_ratio = bundle.get('detour_ratio', 0)
            hover_text = f"Bundled path: {path_text}<br>Detour ratio: {detour_ratio:.2f}"
            
            fig.add_trace(go.Scatter(
                x=x_coords, 
                y=y_coords,
                mode='lines',
                line=dict(color=color, width=2.5),
                hoverinfo='text',
                hovertext=hover_text,
                showlegend=False,
                name=f'bundle_{i}'
            ))


def _add_bundled_segments(fig: go.Figure, bundled_paths: List[Dict], 
                         node_positions: Dict, color: str):
    """Add bundled paths as straight line segments (for comparison)."""
    for i, bundle in enumerate(bundled_paths):
        path_nodes = bundle['path']
        
        # Get coordinates for path nodes
        path_coords = []
        for node in path_nodes:
            if node in node_positions:
                path_coords.append(node_positions[node])
        
        if len(path_coords) >= 2:
            x_coords = [coord[0] for coord in path_coords]
            y_coords = [coord[1] for coord in path_coords]
            
            # Create hover text
            path_text = ' → '.join(map(str, path_nodes))
            detour_ratio = bundle.get('detour_ratio', 0)
            hover_text = f"Bundled path: {path_text}<br>Detour ratio: {detour_ratio:.2f}"
            
            fig.add_trace(go.Scatter(
                x=x_coords, 
                y=y_coords,
                mode='lines',
                line=dict(color=color, width=2),
                hoverinfo='text',
                hovertext=hover_text,
                showlegend=False,
                name=f'bundle_{i}'
            ))


def _add_nodes(fig: go.Figure, graph, node_positions: Dict, color: str):
    """Add nodes to the visualization."""
    node_x = [node_positions[node][0] for node in graph.nodes() if node in node_positions]
    node_y = [node_positions[node][1] for node in graph.nodes() if node in node_positions]
    node_text = [f"{node}: {data.get('name', '')}" for node, data in graph.nodes(data=True) 
                if node in node_positions]
    
    fig.add_trace(go.Scatter(
        x=node_x, 
        y=node_y,
        mode='markers',
        marker=dict(size=8, color=color, line=dict(width=1, color='white')),
        text=node_text,
        hoverinfo='text',
        showlegend=False,
        name='nodes'
    ))


def _configure_layout(fig: go.Figure, title: str, use_curves: bool):
    """Configure the plot layout."""
    curve_type = "Smooth Bézier curves" if use_curves else "Line segments"
    annotation_text = f"Red: bundled paths ({curve_type}), Gray: direct edges"
    
    fig.update_layout(
        title=title,
        showlegend=False,
        hovermode='closest',
        margin=dict(b=20, l=5, r=5, t=40),
        annotations=[
            dict(
                text=annotation_text,
                showarrow=False, 
                xref="paper", yref="paper",
                x=0.005, y=-0.002, 
                xanchor='left', yanchor='bottom',
                font=dict(size=12, color='gray')
            )
        ],
        xaxis=dict(showgrid=False, zeroline=False, showticklabels=False),
        yaxis=dict(showgrid=False, zeroline=False, showticklabels=False),
        plot_bgcolor='rgba(0,0,0,0)',
        paper_bgcolor='rgba(0,0,0,0)'
    )


def create_comparison_visualization(graph, bundled_paths: List[Dict], title: str) -> go.Figure:
    """
    Create side-by-side comparison of line segments vs smooth curves.
    
    Args:
        graph: NetworkX graph
        bundled_paths: List of bundled path dictionaries
        title: Base title for the plot
        
    Returns:
        Plotly Figure with subplots
    """
    from plotly.subplots import make_subplots
    
    fig = make_subplots(
        rows=1, cols=2,
        subplot_titles=("Line Segments", "Smooth Bézier Curves"),
        specs=[[{"type": "scatter"}, {"type": "scatter"}]]
    )
    
    # Get node positions
    node_positions = {node: (data['x'], data['y']) for node, data in graph.nodes(data=True)}
    
    # Left plot: line segments
    segments_fig = create_network_visualization(
        graph, bundled_paths, "", use_curves=False
    )
    
    # Right plot: smooth curves  
    curves_fig = create_network_visualization(
        graph, bundled_paths, "", use_curves=True
    )
    
    # Add traces to subplots
    for trace in segments_fig.data:
        fig.add_trace(trace, row=1, col=1)
    
    for trace in curves_fig.data:
        fig.add_trace(trace, row=1, col=2)
    
    # Update layout
    fig.update_layout(
        title_text=f"{title} - Visualization Comparison",
        showlegend=False
    )
    
    # Update subplot axes
    for i in [1, 2]:
        fig.update_xaxes(showgrid=False, zeroline=False, showticklabels=False, row=1, col=i)
        fig.update_yaxes(showgrid=False, zeroline=False, showticklabels=False, row=1, col=i)
    
    return fig


# Test function
def test_plotly_visualization():
    """Test the plotly visualization with synthetic data."""
    import networkx as nx
    from ..core.bundling import create_graph, bundle_edges
    
    # Create test graph
    nodes = [
        {'id': 0, 'x': 0, 'y': 0, 'name': 'A'},
        {'id': 1, 'x': 1, 'y': 1, 'name': 'B'},
        {'id': 2, 'x': 2, 'y': 0, 'name': 'C'},
        {'id': 3, 'x': 1, 'y': -1, 'name': 'D'}
    ]
    
    edges = [(0, 1), (1, 2), (0, 3), (3, 2), (0, 2)]
    
    graph = create_graph(nodes, edges)
    result = bundle_edges(graph, max_detour_ratio=1.8)
    
    # Create visualization
    fig = create_network_visualization(graph, result['bundled_paths'], 
                                     "Test Network with Smooth Curves")
    
    print(f"Created visualization with {len(result['bundled_paths'])} bundled paths")
    return fig


if __name__ == "__main__":
    test_plotly_visualization()