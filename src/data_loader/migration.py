"""
Migration Data Loader for US Census Migration Flows

Loads county-to-county migration flow data from US Census Bureau.
Data source: https://www.census.gov/data/tables/time-series/demo/geographic-mobility/county-to-county-migration-flows.html

Expected data format: CSV with columns for origin county, destination county, and flow volume.
County coordinates can be loaded from separate county centroids file.
"""

import pandas as pd
import networkx as nx
from typing import Dict, List, Tuple, Optional
import logging
import json
from ..core.bundling import create_graph

logger = logging.getLogger(__name__)


def load_county_coordinates(counties_file: str) -> Dict:
    """
    Load county coordinate data.
    
    Expected format: CSV with columns [fips, county_name, state, latitude, longitude]
    
    Args:
        counties_file: Path to county coordinates file
        
    Returns:
        Dictionary mapping county_fips -> coordinate info
    """
    try:
        counties_df = pd.read_csv(counties_file)
        
        # Ensure required columns exist
        required_cols = ['fips', 'latitude', 'longitude']
        if not all(col in counties_df.columns for col in required_cols):
            logger.error(f"Missing required columns. Expected: {required_cols}")
            return {}
            
        counties = {}
        for _, row in counties_df.iterrows():
            try:
                fips = str(row['fips']).zfill(5)  # Ensure 5-digit FIPS code
                counties[fips] = {
                    'id': fips,
                    'name': row.get('county_name', f'County {fips}'),
                    'state': row.get('state', ''),
                    'x': float(row['longitude']),
                    'y': float(row['latitude'])
                }
            except (ValueError, TypeError) as e:
                logger.debug(f"Skipping invalid county data: {e}")
                continue
                
        logger.info(f"Loaded coordinates for {len(counties)} counties")
        return counties
        
    except Exception as e:
        logger.error(f"Error loading county coordinates: {e}")
        return {}


def load_migration_flows(flows_file: str, counties: Dict, 
                        min_flow_threshold: int = 10) -> List[Tuple[str, str]]:
    """
    Load migration flow data.
    
    Expected format: CSV with origin_fips, dest_fips, flow_volume columns
    
    Args:
        flows_file: Path to migration flows file
        counties: Dictionary of county data
        min_flow_threshold: Minimum flow volume to include
        
    Returns:
        List of (origin_fips, dest_fips) tuples
    """
    try:
        flows_df = pd.read_csv(flows_file)
        
        # Check for required columns
        required_cols = ['origin_fips', 'dest_fips', 'flow_volume']
        if not all(col in flows_df.columns for col in required_cols):
            logger.error(f"Missing required columns. Expected: {required_cols}")
            return []
        
        # Filter flows above threshold
        flows_df = flows_df[flows_df['flow_volume'] >= min_flow_threshold]
        
        # Extract valid flows
        flows = []
        county_ids = set(counties.keys())
        
        for _, row in flows_df.iterrows():
            try:
                origin = str(row['origin_fips']).zfill(5)
                dest = str(row['dest_fips']).zfill(5)
                
                # Only include flows between counties we have coordinates for
                if origin in county_ids and dest in county_ids and origin != dest:
                    flows.append((origin, dest))
                    
            except (ValueError, TypeError):
                continue
                
        logger.info(f"Loaded {len(flows)} migration flows (threshold >= {min_flow_threshold})")
        return flows
        
    except Exception as e:
        logger.error(f"Error loading migration flows: {e}")
        return []


def load_migration_json(json_file: str) -> Optional[nx.DiGraph]:
    """
    Load migration data from JSON format (as referenced in original paper).
    
    Expected format: {"nodes": [...], "links": [...]}
    
    Args:
        json_file: Path to migration JSON file
        
    Returns:
        NetworkX DiGraph
    """
    try:
        with open(json_file, 'r') as f:
            data = json.load(f)
        
        # Extract nodes
        nodes = []
        for node in data.get('nodes', []):
            nodes.append({
                'id': node['id'],
                'name': node.get('name', f"Node {node['id']}"),
                'x': node['x'],
                'y': node['y']
            })
        
        # Extract edges
        edges = []
        for link in data.get('links', []):
            edges.append((link['source'], link['target']))
        
        # Create graph
        graph = create_graph(nodes, edges, distance_type='euclidean')
        
        logger.info(f"Loaded migration JSON: {graph.number_of_nodes()} nodes, {graph.number_of_edges()} edges")
        return graph
        
    except Exception as e:
        logger.error(f"Error loading migration JSON: {e}")
        return None


def load_outflow_data(outflow_file: str, min_flow_threshold: int = 100, distance: str = 'euclidean') -> Optional[nx.DiGraph]:
    """
    Load migration data from outflow.txt format (space-separated: origin dest volume).
    
    Args:
        outflow_file: Path to outflow.txt file
        min_flow_threshold: Minimum flow volume to include
        
    Returns:
        NetworkX DiGraph with county nodes and migration edges
    """
    try:
        # Read outflow data with flexible whitespace separator
        flows_df = pd.read_csv(outflow_file, sep=r'\s+', header=None, 
                              names=['origin_fips', 'dest_fips', 'flow_volume'],
                              engine='python')
        
        # Filter flows above threshold for performance
        flows_df = flows_df[flows_df['flow_volume'] >= min_flow_threshold]
        
        # Get unique county FIPS codes
        unique_fips = set(flows_df['origin_fips'].astype(str)) | set(flows_df['dest_fips'].astype(str))
        
        # Create basic county coordinates (we'll use a simple US layout)
        counties = _create_us_county_coordinates(unique_fips)
        
        # Create edges
        flows = []
        for _, row in flows_df.iterrows():
            origin = f"{row['origin_fips']:05d}"
            dest = f"{row['dest_fips']:05d}"
            
            if origin in counties and dest in counties and origin != dest:
                flows.append((origin, dest))
        
        # Create NetworkX graph
        
        # Convert counties dict to list format
        nodes = list(counties.values())
        
        graph = create_graph(nodes, flows, distance_type=distance)
        
        logger.info(f"Created migration graph from outflow: {graph.number_of_nodes()} counties, {graph.number_of_edges()} flows")
        
        return graph
        
    except Exception as e:
        logger.error(f"Error loading outflow data: {e}")
        return None


def _create_us_county_coordinates(county_fips: set) -> Dict:
    """
    Create basic US county coordinates based on FIPS codes for visualization.
    Uses state-level positioning with random offsets for counties.
    """
    import random
    import math
    
    # Basic state positions (approximate center coordinates)
    state_coords = {
        '01': {'name': 'Alabama', 'lat': 32.7, 'lon': -86.8},
        '02': {'name': 'Alaska', 'lat': 64.0, 'lon': -153.0},
        '04': {'name': 'Arizona', 'lat': 34.2, 'lon': -111.5},
        '05': {'name': 'Arkansas', 'lat': 34.9, 'lon': -92.4},
        '06': {'name': 'California', 'lat': 36.8, 'lon': -119.4},
        '08': {'name': 'Colorado', 'lat': 39.0, 'lon': -105.5},
        '09': {'name': 'Connecticut', 'lat': 41.6, 'lon': -72.7},
        '10': {'name': 'Delaware', 'lat': 39.0, 'lon': -75.5},
        '11': {'name': 'District of Columbia', 'lat': 38.9, 'lon': -77.0},
        '12': {'name': 'Florida', 'lat': 27.8, 'lon': -81.7},
        '13': {'name': 'Georgia', 'lat': 33.2, 'lon': -83.4},
        '15': {'name': 'Hawaii', 'lat': 21.1, 'lon': -157.5},
        '16': {'name': 'Idaho', 'lat': 44.2, 'lon': -114.5},
        '17': {'name': 'Illinois', 'lat': 40.3, 'lon': -89.1},
        '18': {'name': 'Indiana', 'lat': 39.8, 'lon': -86.1},
        '19': {'name': 'Iowa', 'lat': 42.0, 'lon': -93.2},
        '20': {'name': 'Kansas', 'lat': 38.5, 'lon': -96.7},
        '21': {'name': 'Kentucky', 'lat': 37.7, 'lon': -84.9},
        '22': {'name': 'Louisiana', 'lat': 31.1, 'lon': -91.8},
        '23': {'name': 'Maine', 'lat': 44.7, 'lon': -69.8},
        '24': {'name': 'Maryland', 'lat': 39.0, 'lon': -76.8},
        '25': {'name': 'Massachusetts', 'lat': 42.2, 'lon': -71.5},
        '26': {'name': 'Michigan', 'lat': 43.3, 'lon': -84.5},
        '27': {'name': 'Minnesota', 'lat': 45.7, 'lon': -93.9},
        '28': {'name': 'Mississippi', 'lat': 32.7, 'lon': -89.6},
        '29': {'name': 'Missouri', 'lat': 38.4, 'lon': -92.2},
        '30': {'name': 'Montana', 'lat': 47.1, 'lon': -110.0},
        '31': {'name': 'Nebraska', 'lat': 41.1, 'lon': -98.3},
        '32': {'name': 'Nevada', 'lat': 38.4, 'lon': -117.1},
        '33': {'name': 'New Hampshire', 'lat': 43.4, 'lon': -71.6},
        '34': {'name': 'New Jersey', 'lat': 40.3, 'lon': -74.5},
        '35': {'name': 'New Mexico', 'lat': 34.8, 'lon': -106.2},
        '36': {'name': 'New York', 'lat': 42.2, 'lon': -74.9},
        '37': {'name': 'North Carolina', 'lat': 35.6, 'lon': -79.8},
        '38': {'name': 'North Dakota', 'lat': 47.5, 'lon': -99.8},
        '39': {'name': 'Ohio', 'lat': 40.4, 'lon': -82.7},
        '40': {'name': 'Oklahoma', 'lat': 35.6, 'lon': -96.9},
        '41': {'name': 'Oregon', 'lat': 44.6, 'lon': -122.1},
        '42': {'name': 'Pennsylvania', 'lat': 40.6, 'lon': -77.2},
        '44': {'name': 'Rhode Island', 'lat': 41.7, 'lon': -71.5},
        '45': {'name': 'South Carolina', 'lat': 33.8, 'lon': -80.9},
        '46': {'name': 'South Dakota', 'lat': 44.2, 'lon': -99.8},
        '47': {'name': 'Tennessee', 'lat': 35.7, 'lon': -86.9},
        '48': {'name': 'Texas', 'lat': 31.1, 'lon': -97.6},
        '49': {'name': 'Utah', 'lat': 40.1, 'lon': -111.9},
        '50': {'name': 'Vermont', 'lat': 44.0, 'lon': -72.7},
        '51': {'name': 'Virginia', 'lat': 37.8, 'lon': -78.2},
        '53': {'name': 'Washington', 'lat': 47.4, 'lon': -121.5},
        '54': {'name': 'West Virginia', 'lat': 38.5, 'lon': -80.9},
        '55': {'name': 'Wisconsin', 'lat': 44.3, 'lon': -89.6},
        '56': {'name': 'Wyoming', 'lat': 42.8, 'lon': -107.3}
    }
    
    counties = {}
    for fips in county_fips:
        fips_str = f"{int(fips):05d}"
        state_fips = fips_str[:2]
        
        if state_fips in state_coords:
            state_info = state_coords[state_fips]
            # Add small random offset for county position within state
            lat_offset = random.uniform(-0.5, 0.5)
            lon_offset = random.uniform(-0.5, 0.5)
            
            counties[fips_str] = {
                'id': fips_str,
                'name': f"County {fips_str[-3:]}",
                'state': state_info['name'],
                'x': state_info['lon'] + lon_offset,  # longitude as x
                'y': state_info['lat'] + lat_offset   # latitude as y
            }
    
    return counties


def load_migration_data(counties_file: str, flows_file: str, 
                       min_flow_threshold: int = 10) -> Optional[nx.DiGraph]:
    """
    Load complete migration dataset and create NetworkX graph.
    
    Args:
        counties_file: Path to county coordinates file
        flows_file: Path to migration flows file
        min_flow_threshold: Minimum flow volume to include
        
    Returns:
        NetworkX DiGraph with county nodes and migration edges
    """
    # Load data
    counties = load_county_coordinates(counties_file)
    if not counties:
        logger.error("No county coordinate data loaded")
        return None
        
    flows = load_migration_flows(flows_file, counties, min_flow_threshold)
    if not flows:
        logger.error("No migration flow data loaded")
        return None
    
    # Create NetworkX graph
    
    # Convert counties dict to list format
    nodes = list(counties.values())
    
    graph = create_graph(nodes, flows, distance_type='euclidean')
    
    logger.info(f"Created migration graph: {graph.number_of_nodes()} counties, {graph.number_of_edges()} flows")
    
    return graph


if __name__ == "__main__":
    import logging
    logging.basicConfig(level=logging.INFO)
    
    print("Migration Data Loader Test")
    print("To test, place migration data files in data/migration/:")
    print("- county_coordinates.csv (fips, county_name, state, latitude, longitude)")
    print("- migration_flows.csv (origin_fips, dest_fips, flow_volume)")
    print("OR")
    print("- migrations.json (in paper's format)")