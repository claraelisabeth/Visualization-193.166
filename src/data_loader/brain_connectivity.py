"""
Brain Connectivity Data Loader for Human Connectome Project (HCP)

Loads brain network data with 3D spatial coordinates from HCP datasets.
Data source: http://braingraph.org/

Expected data formats:
- Node file: CSV with node_id, x, y, z coordinates, region_name
- Edge file: CSV with source_node, target_node, connection_strength
- GraphML format: Complete graph in GraphML format
"""

import pandas as pd
import networkx as nx
import numpy as np
from typing import Dict, List, Tuple, Optional
import logging
from pathlib import Path
import sys

# Import create_graph at module level
sys.path.append(str(Path(__file__).parent.parent))
from core.bundling import create_graph

logger = logging.getLogger(__name__)


def load_brain_nodes(nodes_file: str) -> Dict:
    """
    Load brain region nodes with 3D coordinates.
    
    Expected format: CSV with columns [node_id, x, y, z, region_name, hemisphere]
    
    Args:
        nodes_file: Path to brain nodes file
        
    Returns:
        Dictionary mapping node_id -> node info with 3D coordinates
    """
    try:
        nodes_df = pd.read_csv(nodes_file)
        
        # Check required columns
        required_cols = ['node_id', 'x', 'y', 'z']
        if not all(col in nodes_df.columns for col in required_cols):
            logger.error(f"Missing required columns. Expected: {required_cols}")
            return {}
        
        nodes = {}
        for _, row in nodes_df.iterrows():
            try:
                node_id = int(row['node_id']) if pd.notna(row['node_id']) else None
                if node_id is None:
                    continue
                    
                nodes[node_id] = {
                    'id': node_id,
                    'name': row.get('region_name', f'Region {node_id}'),
                    'x': float(row['x']),
                    'y': float(row['y']),
                    'z': float(row['z']),
                    'hemisphere': row.get('hemisphere', 'unknown')
                }
            except (ValueError, TypeError) as e:
                logger.debug(f"Skipping invalid node data: {e}")
                continue
                
        logger.info(f"Loaded {len(nodes)} brain regions")
        return nodes
        
    except Exception as e:
        logger.error(f"Error loading brain nodes: {e}")
        return {}


def load_brain_connections(connections_file: str, nodes: Dict,
                          strength_threshold: float = 0.1) -> List[Tuple[int, int]]:
    """
    Load brain connectivity data.
    
    Expected format: CSV with source_node, target_node, connection_strength
    
    Args:
        connections_file: Path to brain connections file
        nodes: Dictionary of brain node data
        strength_threshold: Minimum connection strength to include
        
    Returns:
        List of (source_node, target_node) tuples
    """
    try:
        connections_df = pd.read_csv(connections_file)
        
        # Check required columns
        required_cols = ['source_node', 'target_node', 'connection_strength']
        if not all(col in connections_df.columns for col in required_cols):
            logger.error(f"Missing required columns. Expected: {required_cols}")
            return []
        
        # Filter connections above threshold
        connections_df = connections_df[connections_df['connection_strength'] >= strength_threshold]
        
        # Extract valid connections
        connections = []
        node_ids = set(nodes.keys())
        
        for _, row in connections_df.iterrows():
            try:
                source = int(row['source_node'])
                target = int(row['target_node'])
                
                # Only include connections between nodes we have coordinates for
                if source in node_ids and target in node_ids and source != target:
                    connections.append((source, target))
                    
            except (ValueError, TypeError):
                continue
                
        logger.info(f"Loaded {len(connections)} brain connections (strength >= {strength_threshold})")
        return connections
        
    except Exception as e:
        logger.error(f"Error loading brain connections: {e}")
        return []


def load_brain_graphml(graphml_file: str) -> Optional[nx.DiGraph]:
    """
    Load brain network from GraphML format.
    
    Args:
        graphml_file: Path to GraphML file
        
    Returns:
        NetworkX DiGraph with 3D node positions
    """
    try:
        graph = nx.read_graphml(graphml_file)
        
        # Convert to directed graph if needed
        if not graph.is_directed():
            graph = graph.to_directed()
        
        # Ensure nodes have 3D coordinates (check multiple possible formats)
        nodes_with_coords = 0
        for node_id in graph.nodes():
            node_data = graph.nodes[node_id]
            
            # Check for standard format
            if all(coord in node_data for coord in ['x', 'y', 'z']):
                nodes_with_coords += 1
            # Check for HCP format  
            elif all(coord in node_data for coord in ['dn_position_x', 'dn_position_y', 'dn_position_z']):
                # Convert HCP format to standard format
                node_data['x'] = float(node_data['dn_position_x'])
                node_data['y'] = float(node_data['dn_position_y']) 
                node_data['z'] = float(node_data['dn_position_z'])
                node_data['name'] = node_data.get('dn_name', f'Region_{node_id}')
                nodes_with_coords += 1
            else:
                logger.warning(f"Node {node_id} missing 3D coordinates")
                
        if nodes_with_coords == 0:
            logger.error("No nodes with 3D coordinates found in GraphML")
            return None
        
        # Add edge weights and length based on 3D distance if not present
        for source, target in graph.edges():
            s_data = graph.nodes[source]
            t_data = graph.nodes[target]
            
            try:
                distance = np.sqrt(
                    (float(t_data['x']) - float(s_data['x']))**2 +
                    (float(t_data['y']) - float(s_data['y']))**2 +
                    (float(t_data['z']) - float(s_data['z']))**2
                )
                
                # Set both weight and length for bundling algorithm
                if 'weight' not in graph.edges[source, target]:
                    graph.edges[source, target]['weight'] = distance
                graph.edges[source, target]['length'] = distance
                graph.edges[source, target]['bundled'] = False
                
                # Also preserve original connectivity strength if available
                if 'number_of_fibers' in graph.edges[source, target]:
                    graph.edges[source, target]['fiber_count'] = graph.edges[source, target]['number_of_fibers']
                    
            except (ValueError, KeyError):
                graph.edges[source, target]['weight'] = 1.0
                graph.edges[source, target]['length'] = 1.0
                graph.edges[source, target]['bundled'] = False
                
        logger.info(f"Loaded brain GraphML: {graph.number_of_nodes()} nodes, {graph.number_of_edges()} edges")
        return graph
        
    except Exception as e:
        logger.error(f"Error loading GraphML: {e}")
        return None


def load_brain_connectivity_data(nodes_file: str, connections_file: str,
                                strength_threshold: float = 0.1) -> Optional[nx.DiGraph]:
    """
    Load complete brain connectivity dataset and create NetworkX graph.
    
    Args:
        nodes_file: Path to brain nodes file
        connections_file: Path to brain connections file
        strength_threshold: Minimum connection strength to include
        
    Returns:
        NetworkX DiGraph with brain regions and connections
    """
    # Load data
    nodes = load_brain_nodes(nodes_file)
    if not nodes:
        logger.error("No brain node data loaded")
        return None
        
    connections = load_brain_connections(connections_file, nodes, strength_threshold)
    if not connections:
        logger.error("No brain connection data loaded")
        return None
    
    # Convert nodes dict to list format
    node_list = list(nodes.values())
    
    graph = create_graph(node_list, connections, distance_type='euclidean')
    
    logger.info(f"Created brain graph: {graph.number_of_nodes()} regions, {graph.number_of_edges()} connections")
    
    return graph


def generate_synthetic_brain_data(num_regions: int = 100, connection_prob: float = 0.1) -> nx.DiGraph:
    """
    Generate synthetic 3D brain connectivity data for testing.
    
    Args:
        num_regions: Number of brain regions
        connection_prob: Probability of connection between regions
        
    Returns:
        NetworkX DiGraph with synthetic brain data
    """
    # Generate random 3D coordinates (roughly brain-shaped)
    np.random.seed(42)  # For reproducibility
    
    nodes = []
    for i in range(num_regions):
        # Generate coordinates roughly within brain volume
        x = np.random.normal(0, 30)  # mm
        y = np.random.normal(0, 40)
        z = np.random.normal(0, 30)
        
        nodes.append({
            'id': i,
            'name': f'Region_{i}',
            'x': x,
            'y': y,
            'z': z
        })
    
    # Generate connections
    connections = []
    for i in range(num_regions):
        for j in range(i + 1, num_regions):
            if np.random.random() < connection_prob:
                # Add bidirectional connections
                connections.append((i, j))
                connections.append((j, i))
    
    # Create graph
    graph = create_graph(nodes, connections, distance_type='euclidean')
    
    logger.info(f"Generated synthetic brain data: {graph.number_of_nodes()} regions, {graph.number_of_edges()} connections")
    
    return graph


if __name__ == "__main__":
    import logging
    logging.basicConfig(level=logging.INFO)
    
    print("Brain Connectivity Data Loader Test")
    print("To test, place brain data files in data/brain_connectivity/:")
    print("- brain_nodes.csv (node_id, x, y, z, region_name)")
    print("- brain_connections.csv (source_node, target_node, connection_strength)")
    print("OR")
    print("- brain_network.graphml")
    
    # Generate synthetic data for testing
    print("\nGenerating synthetic brain data for testing...")
    synthetic_graph = generate_synthetic_brain_data(50, 0.05)
    print(f"Synthetic brain network: {synthetic_graph.number_of_nodes()} regions, {synthetic_graph.number_of_edges()} connections")