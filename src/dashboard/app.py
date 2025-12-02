"""
Edge Path Bundling Interactive Dashboard

Interactive Dash application for exploring edge path bundling on different datasets.
Supports 2D visualization with parameter controls for bundling factor and dataset selection.
"""

from dash import Dash, html, dcc, callback, Output, Input
import plotly.express as px
import plotly.graph_objects as go
import pandas as pd
import numpy as np

# Import our bundling implementation
from ..core.bundling import bundle_edges
from ..data_loader import (
    generate_synthetic_brain_data,
    load_migration_json,
    load_air_traffic_data
)

# UI Colors
even_lighter_beige = 'rgb(247, 242, 233)'
light_beige = 'rgb(250, 240, 220)'
beige = 'rgb(213, 184, 149)'
brown = 'rgb(86, 56, 46)'
light_brown = 'rgb(113, 80, 58)'
light_green = 'rgb(168, 203, 160)'
green = 'rgb(78, 110, 77)'

# Default parameters
DEFAULT_BUNDLING_FACTOR = 2.0
DEFAULT_DATASET = 'Brain (Synthetic)'

# Initialize the app with assets folder
import os
assets_path = os.path.join(os.path.dirname(__file__), 'static')
app = Dash(__name__, assets_folder=assets_path)

# App layout
app.layout = html.Div([
    html.Div([
        # Title and Logo
        html.Div("Edge Path Bundling", id='title'),
        html.Div("Clara Pichler and Paul Schmitt", id='user-name'),
        html.Img(src='/assets/TUlogo.png',
                 id='racoon-logo', height='60px', width='60px'),
    ], id='header', style={'display': 'flex', 'align-items': 'center'}),

    html.Div(className='overview-box', children=[
        html.Div(id='overview-text', children=[
            html.H4("Edge Path Bundling Visualization"),
            html.P([
                "This interactive dashboard demonstrates the edge path bundling algorithm ",
                "on different network datasets. The algorithm reduces visual clutter by ",
                "bundling edges that can be routed through existing paths in the network."
            ]),
            html.P([
                "Select a dataset and adjust the bundling factor to see how it affects ",
                "the number of bundled edges. A lower bundling factor creates more bundles ",
                "but allows longer detours."
            ])
        ])
    ]),

    html.Div(className='main-box', children=[
       html.Div([
           dcc.Graph(figure={}, id='main-graph'),
           html.Div(id='graph-stats', style={
               'text-align': 'center', 
               'margin-top': '10px',
               'font-size': '14px',
               'color': green
           })
       ])
    ]),

    html.Div(id='change-parameters', className='parameter-box', children=[
        html.Div(children="Parameter Control", 
                 style={'color': green, 'font-size': '25px', 'padding':'20px'}),
        
        # Dataset Selection
        html.Div([
            html.Label("Dataset:", style={'color': brown, 'font-weight': 'bold', 'margin-bottom': '5px'}),
            dcc.Dropdown(
                id='dataset-dropdown',
                options=[
                    {'label': '🧠 Brain (Synthetic)', 'value': 'brain'},
                    {'label': '✈️ Air Traffic', 'value': 'air_traffic'},
                    {'label': '🏘️ Migration', 'value': 'migration'}
                ],
                value='brain',
                placeholder="Select Dataset",
                style={'margin-bottom': '20px'}
            )
        ], style={'padding': '0 20px'}),
        
        # Bundling Factor Control
        html.Div([
            html.Label("Bundling Factor (k):", style={'color': brown, 'font-weight': 'bold'}),
            html.Div(id='bundling-factor-display', style={'color': green, 'font-size': '18px', 'margin': '5px 0'}),
            dcc.Slider(
                id='bundling-factor-slider',
                min=1.0,
                max=5.0,
                step=0.1,
                value=DEFAULT_BUNDLING_FACTOR,
                marks={i: str(i) for i in range(1, 6)},
                tooltip={"placement": "bottom", "always_visible": True}
            ),
            html.P("Lower values = more bundling, higher values = less bundling", 
                   style={'font-size': '12px', 'color': light_brown, 'margin-top': '10px'})
        ], style={'padding': '0 20px'}),
        
        # Network Size Control (for synthetic data)
        html.Div([
            html.Label("Network Size (nodes):", style={'color': brown, 'font-weight': 'bold'}),
            html.Div(id='network-size-display', style={'color': green, 'font-size': '18px', 'margin': '5px 0'}),
            dcc.Slider(
                id='network-size-slider',
                min=20,
                max=200,
                step=10,
                value=50,
                marks={i: str(i) for i in range(20, 201, 40)},
                tooltip={"placement": "bottom", "always_visible": True}
            )
        ], id='network-size-control', style={'padding': '0 20px', 'margin-top': '20px'}),
    ]),
])

# Callbacks
@app.callback(
    Output('bundling-factor-display', 'children'),
    Input('bundling-factor-slider', 'value')
)
def update_bundling_factor_display(value):
    return f"k = {value:.1f}"

@app.callback(
    Output('network-size-display', 'children'),
    Input('network-size-slider', 'value')
)
def update_network_size_display(value):
    return f"{value} nodes"

@app.callback(
    Output('network-size-control', 'style'),
    Input('dataset-dropdown', 'value')
)
def toggle_network_size_control(dataset):
    if dataset == 'brain':
        return {'padding': '0 20px', 'margin-top': '20px', 'display': 'block'}
    else:
        return {'padding': '0 20px', 'margin-top': '20px', 'display': 'none'}

@app.callback(
    [Output('main-graph', 'figure'), Output('graph-stats', 'children')],
    [Input('dataset-dropdown', 'value'),
     Input('bundling-factor-slider', 'value'),
     Input('network-size-slider', 'value')]
)
def update_graph(dataset, bundling_factor, network_size):
    """Update the main graph based on selected parameters."""
    
    # Load appropriate dataset
    if dataset == 'brain':
        graph = generate_synthetic_brain_data(num_regions=network_size, connection_prob=0.1)
        title = f"Brain Connectivity Network ({network_size} regions)"
    elif dataset == 'air_traffic':
        # For demo purposes, create a small synthetic air traffic network
        # In production, this would load real OpenFlights data
        import networkx as nx
        from ..core.bundling import create_graph
        nodes = [{'id': i, 'name': f'Airport {i}', 'x': np.random.uniform(-180, 180), 
                  'y': np.random.uniform(-90, 90)} for i in range(30)]
        edges = [(i, j) for i in range(30) for j in range(i+1, 30) if np.random.random() < 0.1]
        graph = create_graph(nodes, edges, distance_type='haversine')
        title = "Air Traffic Network (Demo)"
    else:  # migration
        # Create synthetic migration network
        from ..core.bundling import create_graph
        nodes = [{'id': i, 'name': f'County {i}', 'x': np.random.uniform(-125, -66), 
                  'y': np.random.uniform(25, 49)} for i in range(40)]
        edges = [(i, j) for i in range(40) for j in range(i+1, 40) if np.random.random() < 0.08]
        graph = create_graph(nodes, edges, distance_type='euclidean')
        title = "Migration Flows (Demo)"
    
    # Run bundling algorithm
    result = bundle_edges(graph, max_detour_ratio=bundling_factor)
    stats = result['statistics']
    
    # Create visualization
    fig = create_network_plot(graph, result['bundled_paths'], title)
    
    # Create stats text
    stats_text = (f"Total edges: {stats['total_edges']} | "
                  f"Bundled: {stats['bundled']} | "
                  f"No path: {stats['no_path']} | "
                  f"Too long: {stats['too_long']}")
    
    return fig, stats_text


def create_network_plot(graph, bundled_paths, title):
    """Create a plotly network visualization."""
    fig = go.Figure()
    
    # Get node positions
    pos = {node: (data['x'], data['y']) for node, data in graph.nodes(data=True)}
    
    # Draw unbundled edges (straight lines)
    unbundled_edges = [(u, v) for u, v, data in graph.edges(data=True) if not data.get('bundled', False)]
    
    for edge in unbundled_edges:
        x0, y0 = pos[edge[0]]
        x1, y1 = pos[edge[1]]
        fig.add_trace(go.Scatter(
            x=[x0, x1, None], y=[y0, y1, None],
            mode='lines',
            line=dict(color='lightgray', width=1),
            hoverinfo='none',
            showlegend=False
        ))
    
    # Draw bundled paths (curved)
    for bundle in bundled_paths:
        path_nodes = bundle['path']
        path_coords = [pos[node] for node in path_nodes]
        
        x_coords = [coord[0] for coord in path_coords]
        y_coords = [coord[1] for coord in path_coords]
        
        fig.add_trace(go.Scatter(
            x=x_coords, y=y_coords,
            mode='lines',
            line=dict(color='red', width=2),
            hoverinfo='text',
            hovertext=f"Bundled path: {' → '.join(map(str, path_nodes))}",
            showlegend=False
        ))
    
    # Draw nodes
    node_x = [pos[node][0] for node in graph.nodes()]
    node_y = [pos[node][1] for node in graph.nodes()]
    node_text = [f"{node}: {data.get('name', '')}" for node, data in graph.nodes(data=True)]
    
    fig.add_trace(go.Scatter(
        x=node_x, y=node_y,
        mode='markers',
        marker=dict(size=6, color=green, line=dict(width=1, color='white')),
        text=node_text,
        hoverinfo='text',
        showlegend=False
    ))
    
    # Update layout
    fig.update_layout(
        title=title,
        showlegend=False,
        hovermode='closest',
        margin=dict(b=20, l=5, r=5, t=40),
        annotations=[
            dict(text="Red lines: bundled paths, Gray lines: direct edges",
                 showarrow=False, xref="paper", yref="paper",
                 x=0.005, y=-0.002, xanchor='left', yanchor='bottom',
                 font=dict(size=12, color='gray'))
        ],
        xaxis=dict(showgrid=False, zeroline=False, showticklabels=False),
        yaxis=dict(showgrid=False, zeroline=False, showticklabels=False),
        plot_bgcolor='rgba(0,0,0,0)',
        paper_bgcolor='rgba(0,0,0,0)'
    )
    
    return fig


if __name__ == '__main__':
    app.run(debug=True, port=8050)