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
    """
    Calculate Euclidean distance between two points.
    """
    dist = math.sqrt((x2-x1)**2 + (y2-y1)**2)
    if z1 is not None and z2 is not None:
        dist = math.sqrt(dist**2 + (z2-z1)**2)

    return dist


def create_graph(nodes: List[Dict], edges: List[Tuple], distance_type: str = 'euclidean') -> nx.DiGraph:
    """
    Create NetworkX graph with spatial nodes and weighted edges.
    
    Args:
        nodes: List of dicts with keys: 'id', 'x', 'y', optional 'z', 'name'
        edges: List of (source_id, target_id) tuples
        distance_type: 'euclidean' or 'haversine'
    
    Returns:
        NetworkX DiGraph with edge weights based on spatial distance
    """
    G = nx.DiGraph()
    
    # Add nodes with position attributes
    for node in nodes:
        G.add_node(node['id'], 
                  x=node['x'], 
                  y=node['y'],
                  z=node.get('z'),
                  name=node.get('name', ''))
    
    # Add edges with weights based on spatial distance
    for source, target in edges:
        if source not in G or target not in G:
            continue
            
        # Calculate distance
        s_attrs = G.nodes[source]
        t_attrs = G.nodes[target]
        
        if distance_type == 'haversine':
            weight = haversine_distance(s_attrs['y'], s_attrs['x'], 
                                      t_attrs['y'], t_attrs['x'])
        else:  # euclidean
            weight = euclidean_distance(s_attrs['x'], s_attrs['y'],
                                      t_attrs['x'], t_attrs['y'],
                                      s_attrs['z'], t_attrs['z'])
        
        G.add_edge(source, target, weight=weight, bundled=False)
    
    return G


def bundle_edges(graph: nx.DiGraph, max_detour_ratio: float = 2.0) -> Dict:
    """
    Main edge bundling algorithm.
    
    Args:
        graph: NetworkX DiGraph with weighted edges
        max_detour_ratio: Maximum allowed detour ratio (k_max in paper)
    
    Returns:
        Dict with bundled paths and statistics
    """
    bundled_paths = []
    stats = {'total_edges': 0, 'bundled': 0, 'no_path': 0, 'too_long': 0}
    
    # Create a working copy to modify during bundling
    working_graph = graph.copy()
    
    # Process each edge in original graph
    # sorce and target in Algorithm 1 is already extracted and looped over
    # TODO sorting edges
    for source, target in graph.edges():
        stats['total_edges'] += 1
        
        # Skip if already bundled
        # if lock(e)
        if graph.edges[source, target]['bundled']:
            continue
            
        # Calculate direct distance
        # original edge length 
        direct_distance = graph.edges[source, target]['weight']
        
        # Remove this edge temporarily to find alternative path
        if working_graph.has_edge(source, target):
            working_graph.remove_edge(source, target)
        
        # Find shortest path without this direct edge
        # Using dijkstra algorithm
        try:
            path = nx.shortest_path(working_graph, source, target, weight='weight')
            path_distance = nx.shortest_path_length(working_graph, source, target, weight='weight')
        except nx.NetworkXNoPath:
            stats['no_path'] += 1
            continue

        # if path == null : 
        # skip(e) = False
        # continue
        
        # Check detour ratio
        # not used in original algorithm
        detour_ratio = path_distance / direct_distance
        
        if detour_ratio > max_detour_ratio:
            stats['too_long'] += 1
            continue
            
        # Bundle this edge
        stats['bundled'] += 1
        
        # Mark original edge as bundled
        graph.edges[source, target]['bundled'] = True
        
        # Mark all edges in the bundling path as bundled
        for i in range(len(path) - 1):
            u, v = path[i], path[i + 1]
            if working_graph.has_edge(u, v):
                graph.edges[u, v]['bundled'] = True
                working_graph.remove_edge(u, v)  # Remove from future path finding
        
        # Store bundled path information
        bundled_paths.append({
            'original_edge': (source, target),
            'path': path,
            'direct_distance': direct_distance,
            'path_distance': path_distance,
            'detour_ratio': detour_ratio
        })
    
    return {
        'bundled_paths': bundled_paths,
        'statistics': stats
    }


if __name__ == "__main__":
    # Simple test
    test_nodes = [
        {'id': 'A', 'x': 0, 'y': 0, 'name': 'Node A'},
        {'id': 'B', 'x': 1, 'y': 1, 'name': 'Node B'},
        {'id': 'C', 'x': 2, 'y': 0, 'name': 'Node C'},
        {'id': 'D', 'x': 1, 'y': 0, 'name': 'Node D'}
    ]
    
    test_edges = [('A', 'B'), ('B', 'C'), ('A', 'D'), ('D', 'C'), ('A', 'C')]
    
    # Create graph
    G = create_graph(test_nodes, test_edges)
    print(f"Created graph with {G.number_of_nodes()} nodes and {G.number_of_edges()} edges")
    
    # Run bundling algorithm
    result = bundle_edges(G, max_detour_ratio=1.5)
    
    print("\nBundling Results:")
    print(f"Total edges: {result['statistics']['total_edges']}")
    print(f"Bundled: {result['statistics']['bundled']}")
    print(f"No path: {result['statistics']['no_path']}")
    print(f"Too long: {result['statistics']['too_long']}")
    
    for bundle in result['bundled_paths']:
        print(f"Edge {bundle['original_edge']} bundled via path: {' -> '.join(bundle['path'])}")