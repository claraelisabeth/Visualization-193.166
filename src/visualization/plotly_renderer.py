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
                                num_samples: int = 100, use_map: Optional[bool] = None) -> go.Figure:
    """
    Create a Plotly network visualization with smooth bundled paths.
    
    Args:
        graph: NetworkX graph
        bundled_paths: List of bundled path dictionaries
        title: Plot title
        use_curves: Whether to use smooth curves (True) or line segments (False)
        smoothing_level: Bézier smoothing level (paper default: 2)
        num_samples: Curve sampling points (paper default: 100)
        use_map: Whether to use map background (auto-detect if None)
        
    Returns:
        Plotly Figure object
    """
    # Get node positions
    node_positions = {node: (data['x'], data['y']) for node, data in graph.nodes(data=True)}
    
    # Auto-detect if we should use map (geographic coordinates)
    if use_map is None:
        use_map = _is_geographic_data(node_positions)
    
    if use_map:
        # Create map-based visualization
        try:
            fig = _create_map_visualization(graph, bundled_paths, node_positions, title, use_curves, smoothing_level, num_samples)
        except Exception as e:
            # Create error figure for geographic data when map fails
            fig = go.Figure()
            fig.add_annotation(
                text=f"Map visualization failed: {str(e)}<br>Please install plotly with mapbox support",
                xref="paper", yref="paper", x=0.5, y=0.5,
                showarrow=False, font=dict(size=16, color="red"),
                bgcolor="rgba(255,255,255,0.8)", bordercolor="red", borderwidth=2
            )
            fig.update_layout(
                title=f"{title} - Map Error",
                xaxis=dict(visible=False),
                yaxis=dict(visible=False),
                plot_bgcolor='white'
            )
    else:
        # Create standard scatter plot visualization
        fig = _create_scatter_visualization(graph, bundled_paths, node_positions, title, use_curves, smoothing_level, num_samples)
    
    return fig


def _is_geographic_data(node_positions: Dict) -> bool:
    """Check if node positions are likely geographic coordinates (lat/lon)."""
    if not node_positions:
        return False
    
    # Sample a few positions to check ranges
    positions = list(node_positions.values())[:10]  # Check first 10 nodes
    
    x_coords = [pos[0] for pos in positions]
    y_coords = [pos[1] for pos in positions]
    
    # Check if coordinates are in typical lat/lon ranges
    x_in_lon_range = all(-180 <= x <= 180 for x in x_coords)
    y_in_lat_range = all(-90 <= y <= 90 for y in y_coords)
    
    # Check if there's reasonable geographic spread
    x_range = max(x_coords) - min(x_coords)
    y_range = max(y_coords) - min(y_coords)
    
    return x_in_lon_range and y_in_lat_range and x_range > 1 and y_range > 1


def _is_us_data(node_positions: Dict) -> bool:
    """Check if node positions are likely US coordinates."""
    if not node_positions:
        return False
    
    # Sample positions to check if they're in US bounds
    positions = list(node_positions.values())[:20]  # Check more nodes for accuracy
    
    x_coords = [pos[0] for pos in positions]  # longitude
    y_coords = [pos[1] for pos in positions]  # latitude
    
    # US bounds (roughly): longitude -180 to -60, latitude 15 to 75
    us_lon_range = all(-180 <= x <= -60 for x in x_coords)
    us_lat_range = all(15 <= y <= 75 for y in y_coords)
    
    # Check if most coordinates are in continental US range
    continental_us_count = sum(1 for x, y in zip(x_coords, y_coords) 
                              if -130 <= x <= -65 and 20 <= y <= 50)
    
    return us_lon_range and us_lat_range and continental_us_count >= len(positions) * 0.7


def _create_map_visualization(graph, bundled_paths: List[Dict], node_positions: Dict, title: str,
                             use_curves: bool, smoothing_level: int, num_samples: int) -> go.Figure:
    """Create map-based visualization for geographic data."""
    fig = go.Figure()
    
    # Define colors
    unbundled_color = 'rgba(150, 150, 150, 0.4)'  # More transparent for map
    bundled_color = 'rgba(255, 50, 50, 0.8)'      # More opaque for emphasis
    node_color = 'rgba(78, 110, 77, 0.9)'         # Dashboard green
    
    # Draw unbundled edges
    _add_unbundled_edges_map(fig, graph, node_positions, unbundled_color)
    
    # Draw bundled paths
    if use_curves:
        _add_bundled_curves_map(fig, bundled_paths, node_positions, bundled_color, smoothing_level, num_samples)
    else:
        _add_bundled_segments_map(fig, bundled_paths, node_positions, bundled_color)
    
    # Draw nodes
    _add_nodes_map(fig, graph, node_positions, node_color)
    
    # Configure map layout
    _configure_map_layout(fig, title, use_curves, node_positions)
    
    return fig


def _create_scatter_visualization(graph, bundled_paths: List[Dict], node_positions: Dict, title: str,
                                 use_curves: bool, smoothing_level: int, num_samples: int) -> go.Figure:
    """Create standard scatter plot visualization for non-geographic data."""
    fig = go.Figure()
    
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
    _configure_layout(fig, title, use_curves, node_positions)
    
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


def _configure_layout(fig: go.Figure, title: str, use_curves: bool, node_positions: Dict = None):
    """Configure the plot layout."""
    curve_type = "Smooth Bézier curves" if use_curves else "Line segments"
    annotation_text = f"Red: bundled paths ({curve_type}), Gray: direct edges"
    
    # Check if this might be geographic data based on coordinate ranges
    is_geographic = False
    if node_positions:
        positions = list(node_positions.values())[:10]
        if positions:
            x_coords = [pos[0] for pos in positions]
            y_coords = [pos[1] for pos in positions]
            # Check if coordinates look like lat/lon
            x_in_lon_range = all(-180 <= x <= 180 for x in x_coords)
            y_in_lat_range = all(-90 <= y <= 90 for y in y_coords)
            x_range = max(x_coords) - min(x_coords)
            y_range = max(y_coords) - min(y_coords)
            is_geographic = x_in_lon_range and y_in_lat_range and x_range > 1 and y_range > 1
    
    if is_geographic:
        # Geographic scatter plot with visible axes and light grid
        fig.update_layout(
            title=title,
            showlegend=False,
            hovermode='closest',
            margin=dict(b=60, l=60, r=20, t=40),
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
            xaxis=dict(
                title="Longitude", 
                showgrid=True, 
                gridcolor='lightgray',
                gridwidth=0.5,
                showticklabels=True,
                tickfont=dict(size=10)
            ),
            yaxis=dict(
                title="Latitude", 
                showgrid=True, 
                gridcolor='lightgray',
                gridwidth=0.5,
                showticklabels=True,
                tickfont=dict(size=10)
            ),
            plot_bgcolor='white',
            paper_bgcolor='white'
        )
    else:
        # Standard network plot with minimal styling
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

# Map-specific visualization functions
def _add_unbundled_edges_map(fig: go.Figure, graph, node_positions: Dict, color: str):
    """Add unbundled edges for map visualization."""
    unbundled_edges = [(u, v) for u, v, data in graph.edges(data=True) 
                      if not data.get('bundled', False)]
    
    # Limit edges for performance
    if len(unbundled_edges) > 500:
        import random
        unbundled_edges = random.sample(unbundled_edges, 500)
    
    for u, v in unbundled_edges:
        if u in node_positions and v in node_positions:
            lon0, lat0 = node_positions[u]
            lon1, lat1 = node_positions[v]
            
            fig.add_trace(go.Scattergeo(
                lon=[lon0, lon1], 
                lat=[lat0, lat1],
                mode='lines',
                line=dict(color=color, width=1),
                hoverinfo='none',
                showlegend=False,
                name='unbundled'
            ))


def _add_bundled_curves_map(fig: go.Figure, bundled_paths: List[Dict], 
                           node_positions: Dict, color: str,
                           smoothing_level: int, num_samples: int):
    """Add bundled paths as smooth curves for map visualization."""
    for i, bundle in enumerate(bundled_paths):
        path_nodes = bundle['path']
        
        # Generate smooth curve
        curve_points = create_smooth_bundled_path(
            path_nodes, node_positions, smoothing_level, num_samples
        )
        
        if curve_points:
            lon_coords = [point[0] for point in curve_points]
            lat_coords = [point[1] for point in curve_points]
            
            # Create hover text
            path_text = ' → '.join(map(str, path_nodes))
            detour_ratio = bundle.get('detour_ratio', 0)
            hover_text = f"Bundled path: {path_text}<br>Detour ratio: {detour_ratio:.2f}"
            
            fig.add_trace(go.Scattergeo(
                lon=lon_coords, 
                lat=lat_coords,
                mode='lines',
                line=dict(color=color, width=3),
                hoverinfo='text',
                hovertext=hover_text,
                showlegend=False,
                name=f'bundle_{i}'
            ))


def _add_bundled_segments_map(fig: go.Figure, bundled_paths: List[Dict], 
                             node_positions: Dict, color: str):
    """Add bundled paths as straight segments for map visualization."""
    for i, bundle in enumerate(bundled_paths):
        path_nodes = bundle['path']
        
        # Get coordinates for path nodes
        path_coords = []
        for node in path_nodes:
            if node in node_positions:
                path_coords.append(node_positions[node])
        
        if len(path_coords) >= 2:
            lon_coords = [coord[0] for coord in path_coords]
            lat_coords = [coord[1] for coord in path_coords]
            
            # Create hover text
            path_text = ' → '.join(map(str, path_nodes))
            detour_ratio = bundle.get('detour_ratio', 0)
            hover_text = f"Bundled path: {path_text}<br>Detour ratio: {detour_ratio:.2f}"
            
            fig.add_trace(go.Scattergeo(
                lon=lon_coords, 
                lat=lat_coords,
                mode='lines',
                line=dict(color=color, width=2),
                hoverinfo='text',
                hovertext=hover_text,
                showlegend=False,
                name=f'bundle_{i}'
            ))


def _add_nodes_map(fig: go.Figure, graph, node_positions: Dict, color: str):
    """Add nodes for map visualization."""
    node_lon = [node_positions[node][0] for node in graph.nodes() if node in node_positions]
    node_lat = [node_positions[node][1] for node in graph.nodes() if node in node_positions]
    node_text = [f"{node}: {data.get('name', '')}" for node, data in graph.nodes(data=True) 
                if node in node_positions]
    
    fig.add_trace(go.Scattergeo(
        lon=node_lon, 
        lat=node_lat,
        mode='markers',
        marker=dict(size=8, color=color, opacity=0.9),
        text=node_text,
        hoverinfo='text',
        showlegend=False,
        name='airports'
    ))


def _configure_map_layout(fig: go.Figure, title: str, use_curves: bool, node_positions: Dict = None):
    """Configure the map layout with automatic US detection."""
    curve_type = "Smooth Bézier curves" if use_curves else "Line segments"
    annotation_text = f"Red: bundled paths ({curve_type}), Gray: direct routes"
    
    # Detect if this is US data and configure accordingly
    if node_positions and _is_us_data(node_positions):
        # US-focused configuration with simpler settings for better compatibility
        geo_config = dict(
            projection=dict(type="albers usa"),  # Use built-in US projection
            showland=True,
            landcolor="rgb(243, 243, 243)",
            showocean=True,
            oceancolor="rgb(204, 229, 255)", 
            showlakes=True,
            lakecolor="rgb(204, 229, 255)",
            showsubunits=True,  # Show state boundaries
            subunitcolor="rgb(150, 150, 150)",
            scope="usa"
        )
    else:
        # World map configuration with simpler settings
        geo_config = dict(
            projection=dict(type="natural earth"),
            showland=True,
            landcolor="rgb(243, 243, 243)",
            showocean=True,
            oceancolor="rgb(204, 229, 255)",
            showlakes=True,
            lakecolor="rgb(204, 229, 255)",
            showcountries=True,
            countrycolor="rgb(150, 150, 150)"
        )
    
    fig.update_layout(
        title=title,
        showlegend=False,
        hovermode='closest',
        margin=dict(b=20, l=5, r=5, t=40),
        geo=geo_config,
        annotations=[
            dict(
                text=annotation_text,
                showarrow=False, 
                xref="paper", yref="paper",
                x=0.005, y=-0.002, 
                xanchor='left', yanchor='bottom',
                font=dict(size=12, color='gray')
            )
        ]
    )