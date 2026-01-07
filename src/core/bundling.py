"""
Edge Path Bundling Implementation

This module implements the edge path bundling algorithm as described in:
"Edge Path Bundling: A Less Ambiguous Edge Bundling Approach" 
Following Algorithm 1 from the paper.
"""

import networkx as nx
from typing import Dict, List, Tuple, Optional
import math


def haversine_distance(lat1: float, lon1: float, lat2: float, lon2: float) -> float:
    """
    Calculate great circle distance between two points on Earth.
    This is needed for the geospacial datasets.
    """
    R = 6371.0  # Earth radius in kilometers
    
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


def create_graph(nodes: List[Dict], edges: List[Tuple], distance_type: str = 'euclidean') -> nx.DiGraph:
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


def initialize_edge_attributes(G: nx.DiGraph, distance_type: str = 'euclidean') -> None:
    """Initialize edge attributes: length, locked, skip (weight calculated later)"""
    for u, v in G.edges():
        ux, uy = G.nodes[u]["x"], G.nodes[u]["y"]
        vx, vy = G.nodes[v]["x"], G.nodes[v]["y"]
        uz = G.nodes[u].get("z")
        vz = G.nodes[v].get("z")

        # Calculate distance based on type
        if distance_type == 'haversine':
            length = haversine_distance(uy, ux, vy, vx)  # lat, lon order
        else:  # euclidean
            length = euclidean_distance(ux, uy, vx, vy, uz, vz)

        G.edges[u, v]["length"] = length
        G.edges[u, v]["locked"] = False
        G.edges[u, v]["skip"] = False


def update_attributes(graph: nx.DiGraph, d: float = 1.0) -> None:
    """Prepare graph for bundling by calculating weights and resetting state."""
    for u, v in graph.edges():
        length = graph.edges[u, v]["length"]
        graph.edges[u, v]["weight"] = length ** d
        # Reset bundling state for fresh run
        graph.edges[u, v]["locked"] = False
        graph.edges[u, v]["skip"] = False


def sort_edges(graph: nx.DiGraph) -> List[Tuple]:
    """Returns edges sorted by weight in descending order (heaviest first)"""
    return sorted(graph.edges(), 
                  key=lambda e: graph.edges[e]['weight'], 
                  reverse=True)


def dijkstra_with_skip(graph: nx.DiGraph, source, target) -> Optional[List]:
    """Find shortest path from source to target, excluding edges where skip=True"""
    # Use networkx dijkstra with custom weight function to avoid graph copying
    def weight_func(u, v, edge_data):
        # Return infinite weight for skipped edges (effectively excluding them)
        if edge_data.get('skip', False):
            return float('inf')
        return edge_data.get('weight', 1.0)
    
    try:
        return nx.dijkstra_path(graph, source, target, weight=weight_func)
    except nx.NetworkXNoPath:
        return None


def calculate_path_length(graph: nx.DiGraph, path: List) -> float:
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
        if graph.has_edge(u, v):
            total_length += graph.edges[u, v]['length']
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
    
    # Step 1: Algorithm 1 Line 5 - sortedEdges ← sortDescending(E, weight)
    sorted_edges = sort_edges(graph)
    
    # Step 2: Algorithm 1 Lines 6-21 - Main loop
    for i, (source, target) in enumerate(sorted_edges):
        # Line 7: if lock(e) then continue
        if graph.edges[source, target]['locked']:
            continue
            
        # Line 8: skip(e) ← True
        graph.edges[source, target]['skip'] = True
        
        # Line 9-10: s ← source(e), t ← target(e)
        s, t = source, target
        
        # Line 11: p ← dijkstraAlgorithm(G, s, t, weight, skip)
        p = dijkstra_with_skip(graph, s, t)
        
        # Lines 12-13: if p == null then skip(e) ← False, continue
        if p is None:
            graph.edges[source, target]['skip'] = False
            continue
        
        # Lines 14-16: Calculate detour ratio and check maximum distortion
        # detour ← length(p) / length(e)
        path_length = calculate_path_length(graph, p)
        direct_length = graph.edges[source, target]['length']
        detour_ratio = path_length / direct_length
        
        # if detour > k then skip(e) ← False, continue
        if detour_ratio > k:
            graph.edges[source, target]['skip'] = False
            continue
        
        # Lines 17-21: Bundle successful - lock path edges and store result
        # for each edge f in p do lock(f) ← True
        for i in range(len(p) - 1):
            u, v = p[i], p[i + 1]
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
