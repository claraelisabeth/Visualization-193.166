"""
Edge Path Bundling Interactive Dashboard

Interactive Dash application for exploring edge path bundling on different datasets.
Supports 2D visualization with parameter controls for bundling factor and dataset selection.
"""

from dash import Dash, html, dcc, Output, Input, State
import plotly.graph_objects as go

from pathlib import Path
from ..core.bundling import bundle_edges
from ..data_loader import (
    load_air_traffic_data
)
from ..data_loader.brain_connectivity import load_brain_graphml
from ..data_loader.migration import load_outflow_data
from ..visualization import create_network_visualization

# UI Colors - Academic theme
BACKGROUND = '#fafafa'
CARD_BG = '#ffffff'
TEXT_PRIMARY = '#2c3e50'
TEXT_SECONDARY = '#7f8c8d'
ACCENT = '#2980b9'
BORDER = '#e1e8ed'
HEADER_BG = '#34495e'

# Default parameters
DEFAULT_BUNDLING_FACTOR = 1.0  # k parameter - maximum distortion threshold
DEFAULT_EDGE_WEIGHT_FACTOR = 2.0  # d parameter - edge weight factor
DEFAULT_SMOOTHING_LEVEL = 2  # Bézier smoothing level
DEFAULT_DATASET = 'brain'

# Fixed visualization parameters (not user-adjustable)
FIXED_NUM_SAMPLES = 80  # Good balance of smoothness vs performance

# Performance constants
MAJOR_AIRPORTS_LIMIT = 50  # Top N airports for performance
MAJOR_COUNTIES_LIMIT = 100  # Top N counties for performance
MIN_MIGRATION_FLOW = 3000  # Minimum flow threshold

# Dataset configuration
DATASET_NAMES = {
    'brain': 'Brain Connectivity',
    'air_traffic': 'Air Traffic', 
    'migration': 'Migration Flows'
}

DATASET_FILES = {
    'brain': "data/brain_connectivity/996782_repeated10_scale60.graphml",
    'air_traffic': {
        'airports': "data/air_traffic/airports.dat",
        'routes': "data/air_traffic/routes.dat"
    },
    'migration': "data/migration/outflow.txt"
}

# Global cache for loaded datasets (performance optimization)
_dataset_cache = {}

# Global cache for bundling results (performance optimization)
_bundling_cache = {}

# Initialize the app with assets folderI
assets_path = Path(__file__).parent / 'static'
app = Dash(__name__, assets_folder=str(assets_path))

# App layout - Academic dashboard
app.layout = html.Div(style={'font-family': 'system-ui, -apple-system, sans-serif', 'background': BACKGROUND, 'min-height': '100vh'}, children=[
    # Header
    html.Div([
        html.Div("Edge Path Bundling", style={
            'color': 'white',
            'font-size': '18px',
            'font-weight': '600'
        }),
        html.Div([
            html.Span("Clara Pichler and Paul Schmitt", style={
                'color': 'rgba(255,255,255,0.9)',
                'font-size': '14px',
                'margin-right': '12px'
            }),
            html.Img(src='/assets/TUlogo.png', height='32px', width='32px')
        ], style={'display': 'flex', 'align-items': 'center'})
    ], style={
        'height': '56px',
        'background': HEADER_BG,
        'display': 'flex',
        'justify-content': 'space-between',
        'align-items': 'center',
        'padding': '0 24px',
        'box-shadow': '0 1px 3px rgba(0,0,0,0.1)'
    }),

    # Main content container with sidebar layout
    html.Div(style={'display': 'flex', 'min-height': 'calc(100vh - 56px)'}, children=[
        
        # Left sidebar - Controls
        html.Div(style={
            'width': '320px',
            'background': CARD_BG,
            'border-right': f'1px solid {BORDER}',
            'padding': '24px 16px',
            'overflow-y': 'auto'
        }, children=[
            
            # Dataset Section
            html.Div(style={
                'background': CARD_BG,
                'border': f'1px solid {BORDER}',
                'border-radius': '12px',
                'padding': '16px',
                'margin-bottom': '16px'
            }, children=[
                html.H6("Dataset", style={
                    'margin': '0 0 12px 0',
                    'color': TEXT_PRIMARY,
                    'font-size': '14px',
                    'font-weight': '600'
                }),
                dcc.Dropdown(
                    id='dataset-dropdown',
                    options=[
                        {'label': '🏘️ Migration', 'value': 'migration'},
                        {'label': '✈️ Air Traffic', 'value': 'air_traffic'},
                        {'label': '🧠 Brain Connectivity', 'value': 'brain'}
                    ],
                    value='migration',
                    clearable=False,
                    style={'fontSize': '14px'}
                )
            ]),
            
            # Bundling Algorithm Section
            html.Div(style={
                'background': CARD_BG,
                'border': f'1px solid {BORDER}',
                'border-radius': '12px',
                'padding': '16px',
                'margin-bottom': '16px'
            }, children=[
                html.H6("Bundling Algorithm", style={
                    'margin': '0 0 16px 0',
                    'color': TEXT_PRIMARY,
                    'font-size': '14px',
                    'font-weight': '600'
                }),
                
                # k parameter
                html.Div(style={'margin-bottom': '16px'}, children=[
                    html.Div(style={'display': 'flex', 'justify-content': 'space-between', 'align-items': 'center', 'margin-bottom': '8px'}, children=[
                        html.Label("Maximum Distortion Threshold (k)", style={
                            'color': TEXT_PRIMARY,
                            'font-size': '13px',
                            'font-weight': '500'
                        }),
                        html.Div(id='bundling-factor-display', style={
                            'background': ACCENT,
                            'color': 'white',
                            'padding': '4px 8px',
                            'border-radius': '12px',
                            'font-size': '12px',
                            'font-weight': '600'
                        })
                    ]),
                    dcc.Slider(
                        id='bundling-factor-slider',
                        min=1,
                        max=3,
                        step=0.5,
                        value=DEFAULT_BUNDLING_FACTOR,
                        marks={
                            1: {'label': '1', 'style': {'color': TEXT_SECONDARY, 'font-size': '11px'}},
                            1.5: {'label': '1.5', 'style': {'color': TEXT_SECONDARY, 'font-size': '11px'}},
                            2: {'label': '2', 'style': {'color': TEXT_SECONDARY, 'font-size': '11px'}},
                            2.5: {'label': '2.5', 'style': {'color': TEXT_SECONDARY, 'font-size': '11px'}},
                            3: {'label': '3', 'style': {'color': TEXT_SECONDARY, 'font-size': '11px'}}
                        },
                        tooltip={"placement": "bottom", "always_visible": True}
                    ),
                    html.P("Maximum allowed distortion ratio for bundled paths", style={
                        'color': TEXT_SECONDARY,
                        'font-size': '11px',
                        'margin': '8px 0 0 0'
                    })
                ]),
                
                # d parameter
                html.Div(children=[
                    html.Div(style={'display': 'flex', 'justify-content': 'space-between', 'align-items': 'center', 'margin-bottom': '8px'}, children=[
                        html.Label("Edge Weight Factor (d)", style={
                            'color': TEXT_PRIMARY,
                            'font-size': '13px',
                            'font-weight': '500'
                        }),
                        html.Div(id='edge-weight-display', style={
                            'background': ACCENT,
                            'color': 'white',
                            'padding': '4px 8px',
                            'border-radius': '12px',
                            'font-size': '12px',
                            'font-weight': '600'
                        })
                    ]),
                    dcc.Slider(
                        id='edge-weight-slider',
                        min=1,
                        max=3,
                        step=1,
                        value=DEFAULT_EDGE_WEIGHT_FACTOR,
                        marks={
                            1: {'label': '1', 'style': {'color': TEXT_SECONDARY, 'font-size': '11px'}},
                            2: {'label': '2', 'style': {'color': TEXT_SECONDARY, 'font-size': '11px'}},
                            3: {'label': '3', 'style': {'color': TEXT_SECONDARY, 'font-size': '11px'}}
                        },
                        tooltip={"placement": "bottom", "always_visible": True}
                    ),
                    html.P("Weight factor for edge length in bundling calculation", style={
                        'color': TEXT_SECONDARY,
                        'font-size': '11px',
                        'margin': '8px 0 0 0'
                    })
                ])
            ]),
            
            # Visualization Section
            html.Div(style={
                'background': CARD_BG,
                'border': f'1px solid {BORDER}',
                'border-radius': '12px',
                'padding': '16px'
            }, children=[
                html.H6("Visualization", style={
                    'margin': '0 0 16px 0',
                    'color': TEXT_PRIMARY,
                    'font-size': '14px',
                    'font-weight': '600'
                }),
                
                html.Div(children=[
                    html.Div(style={'display': 'flex', 'justify-content': 'space-between', 'align-items': 'center', 'margin-bottom': '8px'}, children=[
                        html.Label("Smoothing Level", style={
                            'color': TEXT_PRIMARY,
                            'font-size': '13px',
                            'font-weight': '500'
                        }),
                        html.Div(id='smoothing-level-display', style={
                            'background': ACCENT,
                            'color': 'white',
                            'padding': '4px 8px',
                            'border-radius': '12px',
                            'font-size': '12px',
                            'font-weight': '600'
                        })
                    ]),
                    dcc.Slider(
                        id='smoothing-level-slider',
                        min=1,
                        max=4,
                        step=1,
                        value=DEFAULT_SMOOTHING_LEVEL,
                        marks={i: {'label': str(i), 'style': {'color': TEXT_SECONDARY, 'font-size': '11px'}} for i in range(1, 5)},
                        tooltip={"placement": "bottom", "always_visible": True}
                    ),
                    html.P("Higher = smoother curves, more computation", style={
                        'color': TEXT_SECONDARY,
                        'font-size': '11px',
                        'margin': '8px 0 0 0'
                    })
                ]),
                
                # Bundled edge color toggle
                html.Div(style={'margin-top': '16px'}, children=[
                    html.Label("Bundled Edge Color", style={
                        'color': TEXT_PRIMARY,
                        'font-size': '13px',
                        'font-weight': '500',
                        'margin-bottom': '8px',
                        'display': 'block'
                    }),
                    dcc.RadioItems(
                        id='edge-color-toggle',
                        options=[
                            {'label': 'Highlight (red)', 'value': 'highlight'},
                            {'label': 'Normal (gray)', 'value': 'normal'}
                        ],
                        value='highlight',
                        style={'color': TEXT_PRIMARY, 'font-size': '13px'},
                        inputStyle={'margin-right': '6px', 'margin-left': '0px'}
                    ),
                    html.P("Choose how bundled edges are colored", style={
                        'color': TEXT_SECONDARY,
                        'font-size': '11px',
                        'margin': '8px 0 0 0'
                    })
                ])
            ])
        ]),

        # Right side - Visualization
        html.Div(style={
            'flex': '1',
            'display': 'flex',
            'flex-direction': 'column',
            'background': CARD_BG
        }, children=[
            
            # Visualization title
            html.Div(id='viz-title', style={
                'padding': '20px 24px 16px 24px',
                'border-bottom': f'1px solid {BORDER}',
                'background': BACKGROUND,
                'text-align': 'center',
                'font-size': '18px',
                'font-weight': '600',
                'color': TEXT_PRIMARY
            }),
            
            # Status chips
            html.Div(id='graph-stats', style={
                'padding': '8px 24px 12px 24px',
                'border-bottom': f'1px solid {BORDER}',
                'background': BACKGROUND,
                'display': 'flex',
                'justify-content': 'center',
                'gap': '8px',
                'font-size': '13px',
                'color': TEXT_SECONDARY
            }),
            
            # Loading status (compact)
            html.Div(id='loading-status', style={
                'position': 'absolute',
                'top': '72px',
                'right': '24px',
                'background': CARD_BG,
                'padding': '8px 12px',
                'border-radius': '6px',
                'font-size': '13px',
                'color': TEXT_PRIMARY,
                'box-shadow': '0 2px 8px rgba(0,0,0,0.1)',
                'z-index': '1000'
            }),
            
            # Main visualization
            html.Div(style={'flex': '1', 'position': 'relative', 'min-height': '600px'}, children=[
                dcc.Loading(
                    id="loading-graph",
                    type="default",
                    children=[dcc.Graph(
                        figure={}, 
                        id='main-graph',
                        style={'height': 'calc(100vh - 220px)', 'width': '100%'}
                    )],
                    style={
                        'height': '100%',
                        'display': 'flex',
                        'align-items': 'center',
                        'justify-content': 'center'
                    }
                )
            ])
        ])
    ])
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
    return f"d = {value}"

@app.callback(
    Output('smoothing-level-display', 'children'),
    Input('smoothing-level-slider', 'value')
)
def update_smoothing_level_display(value):
    return f"Level = {value}"


# Reset sliders to default when dataset changes - also clear graph immediately
@app.callback(
    [Output('bundling-factor-slider', 'value'),
     Output('edge-weight-slider', 'value'),
     Output('smoothing-level-slider', 'value'),
     Output('main-graph', 'figure', allow_duplicate=True)],
    Input('dataset-dropdown', 'value'),
    prevent_initial_call=True
)
def reset_sliders_on_dataset_change(dataset):
    # Immediately clear the graph to prevent showing old data
    empty_fig = go.Figure()
    empty_fig.add_annotation(
        text=f"Loading {DATASET_NAMES.get(dataset, 'Unknown')} dataset...",
        xref="paper", yref="paper", x=0.5, y=0.5,
        showarrow=False, font=dict(size=16, color="gray"),
        bgcolor="rgba(255,255,255,0.9)"
    )
    empty_fig.update_layout(
        xaxis=dict(visible=False),
        yaxis=dict(visible=False),
        plot_bgcolor='white',
        margin=dict(t=20, b=20, l=20, r=20)
    )
    return DEFAULT_BUNDLING_FACTOR, DEFAULT_EDGE_WEIGHT_FACTOR, DEFAULT_SMOOTHING_LEVEL, empty_fig

# Immediate loading message callback (fires first) - only for bundling changes
@app.callback(
    Output('loading-status', 'children'),
    [Input('dataset-dropdown', 'value'),
     Input('bundling-factor-slider', 'value'),
     Input('edge-weight-slider', 'value')]
)
def show_loading_message(dataset, bundling_factor, edge_weight_factor):
    """Show immediate loading message when bundling parameters change."""
    dataset_name = DATASET_NAMES.get(dataset, 'Unknown')
    return f"🔄 Loading {dataset_name} dataset and running bundling algorithm..."

# Fast callback for visualization-only changes
@app.callback(
    [Output('main-graph', 'figure', allow_duplicate=True), Output('loading-status', 'children', allow_duplicate=True)],
    [Input('smoothing-level-slider', 'value'),
     Input('edge-color-toggle', 'value')],
    [State('main-graph', 'figure'),
     State('dataset-dropdown', 'value'),
     State('bundling-factor-slider', 'value'),
     State('edge-weight-slider', 'value')],
    prevent_initial_call=True
)
def update_visualization_only(smoothing_level, edge_color, current_fig, dataset, bundling_factor, edge_weight_factor):
    """Fast update for visualization-only changes (no bundling recalculation)."""
    if not current_fig or not dataset:
        return current_fig, "No data available"
    
    # Get cached data
    global _dataset_cache, _bundling_cache
    graph = _dataset_cache.get(dataset)
    if not graph:
        return current_fig, "Dataset not loaded"
    
    # Get cached bundling results 
    cache_key = f"{dataset}_{bundling_factor}_{edge_weight_factor}"
    bundling_result = _bundling_cache.get(cache_key)
    if not bundling_result:
        return current_fig, "Bundling results not cached"
    
    # Regenerate visualization with new parameters (fast - no bundling computation)
    dataset_type = _get_dataset_type(dataset)
    fig = create_network_visualization(
        graph, bundling_result['bundled_paths'], "", 
        use_curves=True, 
        smoothing_level=smoothing_level, 
        num_samples=FIXED_NUM_SAMPLES,
        dataset_type=dataset_type, 
        edge_color_mode=edge_color
    )
    
    return fig, f"✓ Visualization updated (smoothing: {smoothing_level}, color: {edge_color})"

def _get_cached_dataset(dataset_key):
    """Get dataset from cache or load and cache it for performance."""
    if dataset_key not in _dataset_cache:
        if dataset_key == 'brain':
            _dataset_cache[dataset_key] = load_brain_graphml(DATASET_FILES['brain'])
        elif dataset_key == 'air_traffic':
            files = DATASET_FILES['air_traffic']
            _dataset_cache[dataset_key] = _create_major_airports_subset(files['airports'], files['routes'])
        elif dataset_key == 'migration':
            _dataset_cache[dataset_key] = _create_migration_subset(DATASET_FILES['migration'])
    
    return _dataset_cache[dataset_key]


def _load_dataset(dataset):
    """Load dataset from cache or files."""
    graph = _get_cached_dataset(dataset)
    
    if graph is None:
        return None, f"Failed to load {DATASET_NAMES.get(dataset, 'Unknown')} data", "Error loading dataset"
    
    # Create title from real data
    if dataset == 'brain':
        title = f"Brain Connectivity Network (HCP Subject 996782, {graph.number_of_nodes()} regions)"
    elif dataset == 'air_traffic':
        title = f"Air Traffic Network ({graph.number_of_nodes()} major airports)"
    else:  # migration
        title = f"US County Migration Flows ({graph.number_of_nodes()} counties)"
    
    status = f"✓ {DATASET_NAMES.get(dataset, 'Unknown')} dataset loaded and processed"
    return graph, title, status


def _run_bundling(graph, bundling_factor, edge_weight_factor):
    """Run bundling algorithm or return empty result for k=1."""
    if bundling_factor == 1.0:
        # No bundling for k=1 - better UX
        return {
            'bundled_paths': [],
            'statistics': {
                'total_edges': graph.number_of_edges(),
                'bundled': 0,
            }
        }
    else:
        return bundle_edges(graph, k=bundling_factor, d=edge_weight_factor)


def _get_dataset_type(dataset):
    """Get explicit dataset type for faster rendering."""
    if dataset == 'brain':
        return 'brain_3d'
    elif dataset == 'air_traffic':
        return 'air_traffic'
    elif dataset == 'migration':
        return 'migration'
    return None


@app.callback(
    [Output('main-graph', 'figure'), Output('viz-title', 'children'), Output('graph-stats', 'children'), Output('loading-status', 'children', allow_duplicate=True)],
    [Input('dataset-dropdown', 'value'),
     Input('bundling-factor-slider', 'value'),
     Input('edge-weight-slider', 'value')],
    [State('smoothing-level-slider', 'value'),
     State('edge-color-toggle', 'value')],
    prevent_initial_call='initial_duplicate'
)
def update_graph(dataset, bundling_factor, edge_weight_factor, smoothing_level, edge_color):
    """Update the main graph based on selected parameters."""
    
    # Handle None values (initial load)
    dataset = dataset or 'migration'
    bundling_factor = bundling_factor or DEFAULT_BUNDLING_FACTOR
    edge_weight_factor = edge_weight_factor or DEFAULT_EDGE_WEIGHT_FACTOR
    smoothing_level = smoothing_level or DEFAULT_SMOOTHING_LEVEL
    
    # Load dataset (with caching for performance)
    graph, title, status_msg = _load_dataset(dataset)
    
    if graph is None:
        return {}, "Error loading data", "", "Error loading dataset"
    
    # Run bundling algorithm and cache results
    cache_key = f"{dataset}_{bundling_factor}_{edge_weight_factor}"
    global _bundling_cache
    
    if cache_key not in _bundling_cache:
        result = _run_bundling(graph, bundling_factor, edge_weight_factor)
        _bundling_cache[cache_key] = result
    else:
        result = _bundling_cache[cache_key]
    
    stats = result['statistics']
    
    # Create visualization
    dataset_type = _get_dataset_type(dataset)
    fig = create_network_visualization(
        graph, result['bundled_paths'], "", 
        use_curves=True, 
        smoothing_level=smoothing_level, 
        num_samples=FIXED_NUM_SAMPLES,
        dataset_type=dataset_type, 
        edge_color_mode=edge_color
    )
    
    # Create stats text
    stats_text = (
        f"Total edges: {stats['total_edges']} | "
        f"Bundled: {stats['bundled']} | "
        f"Bundling ratio: {(stats['bundled']/stats['total_edges']*100):.1f}%"
    )
    
    return fig, title, stats_text, status_msg




def _create_major_airports_subset(airports_file, routes_file):
    """Create subset of major airports from real data for better performance."""
    try:
        graph = load_air_traffic_data(airports_file, routes_file, distance='haversine')
        if not graph:
            return None
            
        # Get airports with most connections (major hubs)
        airport_degrees = []
        for node in graph.nodes():
            degree = graph.degree(node)
            airport_degrees.append((degree, node))
        
        # Sort by degree and take top airports for bundling demonstration
        airport_degrees.sort(reverse=True)
        major_airports = [node for _, node in airport_degrees[:MAJOR_AIRPORTS_LIMIT]]
        
        # Create subgraph with only major airports and their connections
        subgraph = graph.subgraph(major_airports).copy()
        
        return subgraph
        
    except Exception as e:
        print(f"Error creating airport subset: {e}")
        return None




def _create_migration_subset(outflow_file):
    """Create smaller subset of migration data for dashboard performance, excluding Alaska/Hawaii."""
    try:
        # Load with high threshold for only major flows
        full_graph = load_outflow_data(outflow_file, min_flow_threshold=MIN_MIGRATION_FLOW)
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
            degree = continental_graph.degree(node)
            county_degrees.append((degree, node))
        
        # Sort by degree and take top counties for performance
        county_degrees.sort(reverse=True)
        major_counties = [node for _, node in county_degrees[:MAJOR_COUNTIES_LIMIT]]
        
        # Create final subgraph with only major continental counties
        subgraph = continental_graph.subgraph(major_counties).copy()
        
        return subgraph
        
    except Exception as e:
        print(f"Error creating migration subset: {e}")
        return None




if __name__ == '__main__':
    app.run(debug=True, port=8050)