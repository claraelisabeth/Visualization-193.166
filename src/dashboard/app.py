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

from core.bundling import bundle_edges, create_graph
from data_loader import (
    generate_synthetic_brain_data,
    load_migration_json,
    load_air_traffic_data
)
from data_loader.brain_connectivity import load_brain_graphml
from data_loader.migration import load_outflow_data
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
DEFAULT_BUNDLING_FACTOR = 1.0  # k parameter - maximum detour ratio
DEFAULT_EDGE_WEIGHT_FACTOR = 1.0  # d parameter - edge weight factor
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
               children=[dcc.Graph(
                   figure={}, 
                   id='main-graph',
                   style={'height': '75vh', 'width': '100%'}
               )],
               style={'padding': '15px'}
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
                    {'label': '🏘️ Migration', 'value': 'migration'},
                    {'label': '✈️ Air Traffic', 'value': 'air_traffic'},
                    {'label': '🧠 Brain Connectivity', 'value': 'brain'}
                ],
                value='migration',
                placeholder="Select Dataset",
                clearable=False,
                style={'margin-bottom': '20px'}
            )
        ], style={'padding': '0 20px'}),
        
        # Bundling Factor Control (k parameter)
        html.Div([
            html.Label("Maximum Detour Ratio (k):", style={'color': brown, 'font-weight': 'bold'}),
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
            html.P("Lower values = less bundling, higher values = more bundling", 
                   style={'font-size': '12px', 'color': light_brown, 'margin-top': '10px'})
        ], style={'padding': '0 20px'}),
        
        # Edge Weight Factor Control (d parameter)
        html.Div([
            html.Label("Edge Weight Factor (d):", style={'color': brown, 'font-weight': 'bold'}),
            html.Div(id='edge-weight-display', style={'color': green, 'font-size': '18px', 'margin': '5px 0'}),
            html.Div([
                dcc.Slider(
                    id='edge-weight-slider',
                    min=1.0,
                    max=5.0,
                    step=0.1,
                    value=DEFAULT_EDGE_WEIGHT_FACTOR,
                    marks={i: str(i) for i in range(1, 6)},
                    tooltip={"placement": "bottom", "always_visible": True}
                )
            ]),
            html.P("Lower values = favor shorter edges (more bundling), higher values = favor longer edges (less bundling)", 
                   style={'font-size': '12px', 'color': light_brown, 'margin-top': '10px'})
        ], style={'padding': '0 20px', 'margin-top': '20px'}),
        
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
    Output('edge-weight-display', 'children'),
    Input('edge-weight-slider', 'value')
)
def update_edge_weight_display(value):
    return f"d = {value:.1f}"

# Reset sliders to default when dataset changes
@app.callback(
    [Output('bundling-factor-slider', 'value'),
     Output('edge-weight-slider', 'value')],
    Input('dataset-dropdown', 'value')
)
def reset_sliders_on_dataset_change(dataset):
    return DEFAULT_BUNDLING_FACTOR, DEFAULT_EDGE_WEIGHT_FACTOR

# Immediate loading message callback (fires first)
@app.callback(
    Output('loading-status', 'children'),
    [Input('dataset-dropdown', 'value'),
     Input('bundling-factor-slider', 'value'),
     Input('edge-weight-slider', 'value')]
)
def show_loading_message(dataset, bundling_factor, edge_weight_factor):
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
     Input('edge-weight-slider', 'value')],
    prevent_initial_call='initial_duplicate'
)
def update_graph(dataset, bundling_factor, edge_weight_factor):
    """Update the main graph based on selected parameters."""
    
    # Handle None values (initial load)
    if dataset is None:
        dataset = 'migration'
    if bundling_factor is None:
        bundling_factor = DEFAULT_BUNDLING_FACTOR
    if edge_weight_factor is None:
        edge_weight_factor = DEFAULT_EDGE_WEIGHT_FACTOR
    
    # Dataset-specific status messages
    dataset_names = {
        'brain': 'Brain Connectivity',
        'air_traffic': 'Air Traffic', 
        'migration': 'Migration Flows'
    }
    
    status_msg = f"✓ {dataset_names.get(dataset, 'Unknown')} dataset loaded and processed"
    
    # Load appropriate dataset
    if dataset == 'brain':
        # Try to load real brain data first, fallback to synthetic
        real_brain_file = "data/brain_connectivity/996782_repeated10_scale60.graphml"
        graph = load_brain_graphml(real_brain_file)
        if graph:
            title = f"Brain Connectivity Network (HCP Subject 996782, {graph.number_of_nodes()} regions)"
        else:
            # Fallback to synthetic if real data fails
            graph = generate_synthetic_brain_data(num_regions=50, connection_prob=0.1)
            title = f"Brain Connectivity Network (Synthetic, 50 regions)"
            status_msg = "⚠ Real brain data failed, using synthetic"
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
        # Load real US migration data with performance optimization
        outflow_file = "data/migration/outflow.txt"
        graph = _create_migration_subset(outflow_file)
        if graph is None:
            # Fallback to demo data if loading fails
            graph = _create_migration_demo()
            title = "Migration Flows (Demo - file load failed)"
            status_msg = "⚠ Migration data failed, using demo data"
        else:
            title = f"US County Migration Flows ({graph.number_of_nodes()} counties)"
    
    # Run bundling algorithm with new Algorithm 1 implementation
    result = bundle_edges(graph, k=bundling_factor, d=edge_weight_factor)
    stats = result['statistics']
    
    # Create visualization with smooth Bézier curves
    # Let migration data use map visualization (auto-detect geographic coordinates)
    fig = create_network_visualization(graph, result['bundled_paths'], title, 
                                     use_curves=True, smoothing_level=2, num_samples=100)
    
    # Create stats text
    stats_text = (f"Total edges: {stats['total_edges']} | "
                  f"Bundled: {stats['bundled']} | "
                  f"Bundling ratio: {(stats['bundled']/stats['total_edges']*100):.1f}%")
    
    return fig, stats_text, status_msg




def _create_major_airports_subset(airports_file, routes_file):
    """Create subset of major airports from real data for better performance."""
    try:
        graph = load_air_traffic_data(airports_file, routes_file, distance='haversine')
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
    import random
    import math
    
    # Create hub-and-spoke topology
    hubs = ['NYC', 'LAX', 'CHI', 'DFW', 'ATL']
    regional_airports = [f'REG{i:02d}' for i in range(15)]
    
    nodes = []
    
    # Position hubs in a circle
    hub_positions = {}
    for i, hub in enumerate(hubs):
        angle = 2 * math.pi * i / len(hubs)
        hub_positions[hub] = (math.cos(angle) * 3, math.sin(angle) * 3)
        nodes.append({'id': hub, 'x': hub_positions[hub][0], 'y': hub_positions[hub][1], 'name': hub})
    
    # Position regional airports randomly around hubs
    for i, airport in enumerate(regional_airports):
        hub = random.choice(hubs)
        hub_x, hub_y = hub_positions[hub]
        x = hub_x + random.uniform(-1.5, 1.5)
        y = hub_y + random.uniform(-1.5, 1.5)
        nodes.append({'id': airport, 'x': x, 'y': y, 'name': airport})
    
    # Create edges
    edges = []
    
    # Add hub-to-hub connections
    for i, hub1 in enumerate(hubs):
        for j, hub2 in enumerate(hubs):
            if i != j:
                edges.append((hub1, hub2))
    
    # Add regional-to-hub connections
    for airport in regional_airports:
        distances = []
        airport_pos = None
        for node in nodes:
            if node['id'] == airport:
                airport_pos = (node['x'], node['y'])
                break
        
        for hub in hubs:
            hub_pos = hub_positions[hub]
            dist = math.sqrt((airport_pos[0] - hub_pos[0])**2 + (airport_pos[1] - hub_pos[1])**2)
            distances.append((dist, hub))
        
        distances.sort()
        for _, hub in distances[:2]:
            edges.append((airport, hub))
            edges.append((hub, airport))
    
    return create_graph(nodes, edges)


def _create_migration_subset(outflow_file):
    """Create smaller subset of migration data for dashboard performance, excluding Alaska/Hawaii."""
    try:
        # Load with high threshold for only major flows
        full_graph = load_outflow_data(outflow_file, min_flow_threshold=3000)
        if not full_graph:
            return None
            
        # Filter out Alaska (02xxx) and Hawaii (15xxx) FIPS codes
        continental_nodes = []
        for node in full_graph.nodes():
            fips_state = str(node)[:2]  # First 2 digits = state FIPS
            if fips_state not in ['02', '15']:  # Exclude Alaska and Hawaii
                continental_nodes.append(node)
        
        # Create subgraph with only continental US counties
        continental_graph = full_graph.subgraph(continental_nodes).copy()
        
        # Get counties with most connections within continental US
        county_degrees = []
        for node in continental_graph.nodes():
            degree = continental_graph.in_degree(node) + continental_graph.out_degree(node)
            county_degrees.append((degree, node))
        
        # Sort by degree and take top counties for performance
        county_degrees.sort(reverse=True)
        major_counties = [node for _, node in county_degrees[:100]]  # Top 100 most connected counties for performance
        
        # Create final subgraph with only major continental counties
        subgraph = continental_graph.subgraph(major_counties).copy()
        
        return subgraph
        
    except Exception as e:
        print(f"Error creating migration subset: {e}")
        return None


def _create_migration_demo():
    """Create migration network with regional population centers."""
    import random
    import math
    
    centers = ['CA', 'TX', 'FL', 'NY', 'IL', 'PA', 'OH', 'GA', 'NC', 'MI']
    smaller_cities = [f'CITY{i:02d}' for i in range(12)]
    
    nodes = []
    
    # Position major centers
    center_positions = {}
    for i, center in enumerate(centers):
        if i < 5:
            angle = 2 * math.pi * i / 5
            center_positions[center] = (math.cos(angle) * 2, math.sin(angle) * 2)
        else:
            angle = 2 * math.pi * (i-5) / 5
            center_positions[center] = (math.cos(angle) * 4, math.sin(angle) * 4)
        
        nodes.append({'id': center, 'x': center_positions[center][0], 'y': center_positions[center][1], 'name': center})
    
    # Position smaller cities
    for i, city in enumerate(smaller_cities):
        x = random.uniform(-5, 5)
        y = random.uniform(-5, 5)
        nodes.append({'id': city, 'x': x, 'y': y, 'name': city})
    
    # Create edges
    edges = []
    
    # Add major center connections
    for i, center1 in enumerate(centers):
        for j, center2 in enumerate(centers):
            if i != j and random.random() < 0.4:
                edges.append((center1, center2))
    
    # Connect smaller cities to centers
    for city in smaller_cities:
        city_pos = None
        for node in nodes:
            if node['id'] == city:
                city_pos = (node['x'], node['y'])
                break
        
        distances = []
        for center in centers:
            center_pos = center_positions[center]
            dist = math.sqrt((city_pos[0] - center_pos[0])**2 + (city_pos[1] - center_pos[1])**2)
            distances.append((dist, center))
        
        distances.sort()
        for _, center in distances[:2]:
            edges.append((city, center))
            if random.random() < 0.6:
                edges.append((center, city))
    
    return create_graph(nodes, edges)


if __name__ == '__main__':
    app.run(debug=True, port=8050)