"""
Edge Path Bundling Interactive Dashboard

Interactive Dash application for exploring edge path bundling on different datasets.
Supports 2D visualization with parameter controls for bundling factor and dataset selection.
"""

from dash import Dash, html, dcc, callback, Output, Input
import dash_bootstrap_components as dbc
import plotly.express as px
import plotly.graph_objects as go
import pandas as pd
import numpy as np

# Import our bundling implementation
import sys
from pathlib import Path
sys.path.append(str(Path(__file__).parent.parent))

from core.bundling import bundle_edges
from data_loader import (
    generate_synthetic_brain_data,
    load_migration_json,
    load_air_traffic_data
)
from visualization import create_network_visualization

# UI Colors
even_lighter_beige = 'rgb(247, 242, 233)'
light_beige = 'rgb(250, 240, 220)'
beige = 'rgb(213, 184, 149)'
brown = 'rgb(86, 56, 46)'
light_brown = 'rgb(113, 80, 58)'
light_green = 'rgb(168, 203, 160)'
green = 'rgb(78, 110, 77)'

# Default parameters
DEFAULT_BUNDLING_FACTOR = 1.0
DEFAULT_DATASET = 'Brain (Synthetic)'

# Initialize the app with assets folderI
assets_path = Path(__file__).parent / 'static'
app = Dash(__name__, assets_folder=str(assets_path))

# App layout - Side by side layout
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
           dcc.Loading(
               id="loading-graph",
               type="default",
               children=[dcc.Graph(figure={}, id='main-graph')],
               style={'padding': '20px'}
           ),
           html.Div(id='loading-status', style={
               'text-align': 'center',
               'margin': '10px 0',
               'font-size': '16px',
               'font-weight': 'bold',
               'color': brown
           }),
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
            html.Div([
                dcc.Slider(
                    id='bundling-factor-slider',
                    min=1.0,
                    max=5.0,
                    step=0.1,
                    value=DEFAULT_BUNDLING_FACTOR,
                    marks={i: str(i) for i in range(1, 6)},
                    tooltip={"placement": "bottom", "always_visible": True}
                )
            ]),
            html.P("Lower values = more bundling, higher values = less bundling", 
                   style={'font-size': '12px', 'color': light_brown, 'margin-top': '10px'})
        ], style={'padding': '0 20px'}),
        
        # Network Size Control (for synthetic data)
        html.Div([
            html.Label("Network Size (nodes):", style={'color': brown, 'font-weight': 'bold'}),
            html.Div(id='network-size-display', style={'color': green, 'font-size': '18px', 'margin': '5px 0'}),
            html.Div([
                dcc.Slider(
                    id='network-size-slider',
                    min=20,
                    max=200,
                    step=10,
                    value=50,
                    marks={i: str(i) for i in range(20, 201, 40)},
                    tooltip={"placement": "bottom", "always_visible": True}
                )
            ])
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

# Immediate loading message callback (fires first)
@app.callback(
    Output('loading-status', 'children'),
    [Input('dataset-dropdown', 'value'),
     Input('bundling-factor-slider', 'value'),
     Input('network-size-slider', 'value')]
)
def show_loading_message(dataset, bundling_factor, network_size):
    """Show immediate loading message when parameters change."""
    dataset_names = {
        'brain': 'Brain Connectivity',
        'air_traffic': 'Air Traffic', 
        'migration': 'Migration Flows'
    }
    
    dataset_name = dataset_names.get(dataset, 'Unknown')
    return f"🔄 Loading {dataset_name} dataset and running bundling algorithm..."

@app.callback(
    [Output('main-graph', 'figure'), Output('graph-stats', 'children'), Output('loading-status', 'children', allow_duplicate=True)],
    [Input('dataset-dropdown', 'value'),
     Input('bundling-factor-slider', 'value'),
     Input('network-size-slider', 'value')],
    prevent_initial_call=True
)
def update_graph(dataset, bundling_factor, network_size):
    """Update the main graph based on selected parameters."""
    
    # Dataset-specific status messages
    dataset_names = {
        'brain': 'Brain Connectivity',
        'air_traffic': 'Air Traffic', 
        'migration': 'Migration Flows'
    }
    
    status_msg = f"✓ {dataset_names.get(dataset, 'Unknown')} dataset loaded and processed"
    
    # Load appropriate dataset
    if dataset == 'brain':
        graph = generate_synthetic_brain_data(num_regions=network_size, connection_prob=0.1)
        title = f"Brain Connectivity Network ({network_size} regions)"
    elif dataset == 'air_traffic':
        # Load real OpenFlights data (subset for performance)
        airports_file = "data/air_traffic/airports.dat"
        routes_file = "data/air_traffic/routes.dat"
        graph = _create_major_airports_subset(airports_file, routes_file)
        if graph is None:
            # Fallback to demo data if loading fails
            graph = _create_air_traffic_demo()
            title = "Air Traffic Network (Demo - file load failed)"
            status_msg = "⚠ Air traffic data failed, using demo data"
        else:
            title = f"Air Traffic Network ({graph.number_of_nodes()} major airports)"
    else:  # migration
        # Create migration network with regional hubs
        graph = _create_migration_demo()
        title = "Migration Flows (Demo)"
    
    # Run bundling algorithm
    result = bundle_edges(graph, max_detour_ratio=bundling_factor)
    stats = result['statistics']
    
    # Create visualization with smooth Bézier curves
    fig = create_network_visualization(graph, result['bundled_paths'], title, 
                                     use_curves=True, smoothing_level=2, num_samples=100)
    
    # Create stats text
    stats_text = (f"Total edges: {stats['total_edges']} | "
                  f"Bundled: {stats['bundled']} | "
                  f"No path: {stats['no_path']} | "
                  f"Too long: {stats['too_long']}")
    
    return fig, stats_text, status_msg




def _create_major_airports_subset(airports_file, routes_file):
    """Create subset of major airports from real data for better performance."""
    try:
        graph = load_air_traffic_data(airports_file, routes_file)
        if not graph:
            return None
            
        # Get airports with most connections (major hubs)
        airport_degrees = []
        for node in graph.nodes():
            degree = graph.in_degree(node) + graph.out_degree(node)
            airport_degrees.append((degree, node))
        
        # Sort by degree and take top airports for bundling demonstration
        airport_degrees.sort(reverse=True)
        major_airports = [node for _, node in airport_degrees[:50]]  # Top 50 busiest airports for map performance
        
        # Create subgraph with only major airports and their connections
        subgraph = graph.subgraph(major_airports).copy()
        
        return subgraph
        
    except Exception as e:
        print(f"Error creating airport subset: {e}")
        return None


def _create_air_traffic_demo():
    """Create realistic air traffic network with hub structure."""
    import networkx as nx
    import random
    import math
    
    # Create hub-and-spoke topology
    hubs = ['NYC', 'LAX', 'CHI', 'DFW', 'ATL']
    regional_airports = [f'REG{i:02d}' for i in range(15)]
    
    graph = nx.DiGraph()
    
    # Position hubs in a circle
    hub_positions = {}
    for i, hub in enumerate(hubs):
        angle = 2 * math.pi * i / len(hubs)
        hub_positions[hub] = (math.cos(angle) * 3, math.sin(angle) * 3)
        graph.add_node(hub, x=hub_positions[hub][0], y=hub_positions[hub][1], name=hub)
    
    # Position regional airports randomly around hubs
    for i, airport in enumerate(regional_airports):
        hub = random.choice(hubs)
        hub_x, hub_y = hub_positions[hub]
        x = hub_x + random.uniform(-1.5, 1.5)
        y = hub_y + random.uniform(-1.5, 1.5)
        graph.add_node(airport, x=x, y=y, name=airport)
    
    # Add hub-to-hub connections
    for i, hub1 in enumerate(hubs):
        for j, hub2 in enumerate(hubs):
            if i != j:
                graph.add_edge(hub1, hub2)
    
    # Add regional-to-hub connections
    for airport in regional_airports:
        distances = []
        for hub in hubs:
            airport_pos = (graph.nodes[airport]['x'], graph.nodes[airport]['y'])
            hub_pos = (graph.nodes[hub]['x'], graph.nodes[hub]['y'])
            dist = math.sqrt((airport_pos[0] - hub_pos[0])**2 + (airport_pos[1] - hub_pos[1])**2)
            distances.append((dist, hub))
        
        distances.sort()
        for _, hub in distances[:2]:
            graph.add_edge(airport, hub)
            graph.add_edge(hub, airport)
    
    return graph


def _create_migration_demo():
    """Create migration network with regional population centers."""
    import networkx as nx
    import random
    import math
    
    centers = ['CA', 'TX', 'FL', 'NY', 'IL', 'PA', 'OH', 'GA', 'NC', 'MI']
    smaller_cities = [f'CITY{i:02d}' for i in range(12)]
    
    graph = nx.DiGraph()
    
    # Position major centers
    center_positions = {}
    for i, center in enumerate(centers):
        if i < 5:
            angle = 2 * math.pi * i / 5
            center_positions[center] = (math.cos(angle) * 2, math.sin(angle) * 2)
        else:
            angle = 2 * math.pi * (i-5) / 5
            center_positions[center] = (math.cos(angle) * 4, math.sin(angle) * 4)
        
        graph.add_node(center, x=center_positions[center][0], y=center_positions[center][1], name=center)
    
    # Position smaller cities
    for i, city in enumerate(smaller_cities):
        x = random.uniform(-5, 5)
        y = random.uniform(-5, 5)
        graph.add_node(city, x=x, y=y, name=city)
    
    # Add major center connections
    for i, center1 in enumerate(centers):
        for j, center2 in enumerate(centers):
            if i != j and random.random() < 0.4:
                graph.add_edge(center1, center2)
    
    # Connect smaller cities to centers
    for city in smaller_cities:
        city_pos = (graph.nodes[city]['x'], graph.nodes[city]['y'])
        
        distances = []
        for center in centers:
            center_pos = center_positions[center]
            dist = math.sqrt((city_pos[0] - center_pos[0])**2 + (city_pos[1] - center_pos[1])**2)
            distances.append((dist, center))
        
        distances.sort()
        for _, center in distances[:2]:
            graph.add_edge(city, center)
            if random.random() < 0.6:
                graph.add_edge(center, city)
    
    return graph


if __name__ == '__main__':
    app.run(debug=True, port=8050)