"""
Brain Connectivity Data Loader for Human Connectome Project (HCP)

Loads brain network data with 3D spatial coordinates from HCP datasets.
Data source: http://braingraph.org/

Expected data formats:
- Node file: CSV with node_id, x, y, z coordinates, region_name
- Edge file: CSV with source_node, target_node, connection_strength
- GraphML format: Complete graph in GraphML format
"""

import networkx as nx
import numpy as np
from typing import Optional
import logging

logger = logging.getLogger(__name__)

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






