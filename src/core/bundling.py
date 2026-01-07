"""
Edge Path Bundling Implementation

This module implements the edge path bundling algorithm as described in:
"Edge Path Bundling: A Less Ambiguous Edge Bundling Approach" 
Following Algorithm 1 from the paper.
"""

import networkx as nx
from typing import Dict, List, Tuple, Optional
import math

# Constants
EARTH_RADIUS_KM = 6371.0
DISTANCE_EUCLIDEAN = 'euclidean'
DISTANCE_HAVERSINE = 'haversine'


def haversine_distance(lat1: float, lon1: float, lat2: float, lon2: float) -> float:
    """
    Calculate great circle distance between two points on Earth.
    This is needed for the geospacial datasets.
    """
    R = EARTH_RADIUS_KM
    
    lat1, lon1, lat2, lon2 = map(math.radians, [lat1, lon1, lat2, lon2])
    dlat = lat2 - lat1
    dlon = lon2 - lon1
    
    a = math.sin(dlat/2)**2 + math.cos(lat1) * math.cos(lat2) * math.sin(dlon/2)**2
    c = 2 * math.atan2(math.sqrt(a), math.sqrt(1-a))
    
    return R * c


def euclidean_distance(x1: float, y1: float, x2: float, y2: float, 
                       z1: Optional[float] = None, z2: Optional[float] = None) -> float:
    dx = x2 - x1
    dy = y2 - y1
    dz = 0.0 if (z1 is None or z2 is None) else (z2 - z1)
    return math.sqrt(dx*dx + dy*dy + dz*dz)


def create_graph(nodes: List[Dict], edges: List[Tuple], distance_type: str = DISTANCE_EUCLIDEAN) -> nx.DiGraph:
    """Create NetworkX graph with spatial nodes and weighted edges"""
    G = nx.DiGraph()
    
    # Add nodes with position attributes
    for node in nodes:
        G.add_node(node['id'], x=node['x'], y=node['y'], z=node.get('z'))

    # Add edges
    for source, target in edges:
        if source not in G or target not in G:
            continue
        G.add_edge(source, target, bundled=False)
    
    # Initialize edge attributes
    initialize_edge_attributes(G, distance_type=distance_type)
    
    return G


def initialize_edge_attributes(G: nx.DiGraph, distance_type: str = DISTANCE_EUCLIDEAN) -> None:
    """Initialize edge attributes: length, locked, skip (weight calculated later)"""
    for u, v in G.edges():
        ux, uy = G.nodes[u]["x"], G.nodes[u]["y"]
        vx, vy = G.nodes[v]["x"], G.nodes[v]["y"]
        uz = G.nodes[u].get("z")
        vz = G.nodes[v].get("z")

        # Calculate distance based on type
        if distance_type == DISTANCE_HAVERSINE:
            length = haversine_distance(uy, ux, vy, vx)  # lat, lon order
        else:  # euclidean
            length = euclidean_distance(ux, uy, vx, vy, uz, vz)

        G.edges[u, v]["length"] = length
        G.edges[u, v]["locked"] = False
        G.edges[u, v]["skip"] = False


def update_attributes(graph: nx.DiGraph, d: float = 1.0) -> None:
    """Prepare graph for bundling by calculating weights and resetting state."""
    for u, v in graph.edges():
        edge_data = graph.edges[u, v]
        length = edge_data["length"]
        edge_data["weight"] = length ** d
        # Reset bundling state for fresh run
        edge_data["locked"] = False
        edge_data["skip"] = False


def sort_edges(graph: nx.DiGraph) -> List[Tuple]:
    """Returns edges sorted by weight in descending order (heaviest first)"""
    return sorted(graph.edges(), 
                  key=lambda e: graph.edges[e]['weight'], 
                  reverse=True)


def _edge_weight_with_skip(_, __, edge_data):
    """Weight function that excludes edges where skip=True"""
    if edge_data.get('skip', False):
        return float('inf')
    return edge_data.get('weight', 1.0)


def dijkstra_with_skip(graph: nx.DiGraph, source, target) -> Optional[List]:
    """Find shortest path from source to target, excluding edges where skip=True"""
    try:
        return nx.dijkstra_path(graph, source, target, weight=_edge_weight_with_skip)
    except nx.NetworkXNoPath:
        return None


def calculate_path_length(graph: nx.DiGraph, path: List[int]) -> float:
    """
    Calculate the total length of a path through the graph.
    
    Args:
        graph: NetworkX DiGraph with edge 'length' attributes
        path: List of node IDs forming the path
        
    Returns:
        Total length of the path
    """
    if len(path) < 2:
        return 0.0
    
    total_length = 0.0
    for i in range(len(path) - 1):
        u, v = path[i], path[i + 1]
        edge_data = graph.edges.get((u, v))
        if edge_data:
            total_length += edge_data['length']
        else:
            # This shouldn't happen if path is valid
            return float('inf')
    
    return total_length


def bundle_edges(graph: nx.DiGraph, k: float = 2.0, d: float = 1.0) -> Dict:
    """
    Algorithm 1: Edge-Path Bundling Algorithm
    
    Input: Graph G = (V,E), input drawing DG, maximum distortion k, edge weight factor d.
    Output: Control points for an Edge-Path bundled drawing Γ.
    
    Args:
        graph: NetworkX DiGraph with initialized edge attributes (length, locked, skip)
        k: Maximum distortion (detour ratio)
        d: Edge weight factor (from slider)
    
    Returns:
        Dict with bundled paths and control points
    """
    bundled_paths = []
    
    # Adjust weights with current d parameter and reset state
    update_attributes(graph, d)
    
    sorted_edges = sort_edges(graph)
    
    # Main loop
    for i, (source, target) in enumerate(sorted_edges):
        edge_data = graph.edges[source, target]
        
        # if lock(e) then continue
        if edge_data['locked']:
            continue
            
        edge_data['skip'] = True
        
        p = dijkstra_with_skip(graph, source, target)
        
        if p is None:
            edge_data['skip'] = False
            continue
        
        # Calculate detour ratio and check maximum distortion
        path_length = calculate_path_length(graph, p)
        direct_length = edge_data['length']
        detour_ratio = path_length / direct_length
        
        if detour_ratio > k:
            edge_data['skip'] = False
            continue
        
        # Bundle successful - lock path edges and store result
        for j in range(len(p) - 1):
            u, v = p[j], p[j + 1]
            if graph.has_edge(u, v):
                graph.edges[u, v]['locked'] = True
        
        # Store a bundled path
        bundled_paths.append({
            'original_edge': (source, target),
            'path': p,
            'detour_ratio': detour_ratio,
            'direct_length': direct_length,
            'path_length': path_length
        })
    
    # Calculate statistics
    total_edges = len(sorted_edges)
    bundled_count = len(bundled_paths)
    
    return {
        'bundled_paths': bundled_paths,
        'statistics': {
            'total_edges': total_edges,
            'bundled': bundled_count,
        }
    }
