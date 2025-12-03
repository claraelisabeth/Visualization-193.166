"""
Air Traffic Data Loader for OpenFlights Dataset

Loads airport and route data from OpenFlights project for edge bundling analysis.
Data source: https://openflights.org/data.html

Expected data files:
- airports.dat: Airport information (ID, name, city, country, IATA, ICAO, lat, lon, altitude, timezone, DST, Tz)
- routes.dat: Route information (airline, airline_id, source_airport, source_airport_id, dest_airport, dest_airport_id, codeshare, stops, equipment)
"""

import pandas as pd
import networkx as nx
from typing import Dict, List, Tuple, Optional
import logging
from pathlib import Path

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

import sys
sys.path.append(str(Path(__file__).parent.parent))
from core.bundling import create_graph


def load_airports(airports_file: str) -> Dict:
    """Load airport data from OpenFlights airports.dat file"""
    # Define column names for airports.dat (14 columns total)
    airport_columns = [
        'airport_id', 'name', 'city', 'country', 'iata', 'icao',
        'latitude', 'longitude', 'altitude', 'timezone', 'dst', 'tz', 'type', 'source'
    ]
    
    try:
        # Read airport data with proper CSV parsing for quoted fields
        airports_df = pd.read_csv(airports_file, names=airport_columns, quotechar='"', skipinitialspace=True)
        
        # Filter out airports without valid coordinates
        airports_df = airports_df.dropna(subset=['latitude', 'longitude'])
        airports_df = airports_df[airports_df['airport_id'] != '\\N']
        
        # Convert to dict for faster lookup
        airports = {}
        for _, row in airports_df.iterrows():
            airport_id = int(row['airport_id'])
            airports[airport_id] = {
                'id': airport_id,
                'name': row['name'],
                'city': row['city'],
                'country': row['country'],
                'iata': row['iata'],
                'x': float(row['longitude']),
                'y': float(row['latitude']),
                'altitude': row['altitude']
            }

        logger.info(f"Loaded {len(airports)} airports")
        return airports
        
    except Exception as e:
        logger.error(f"Error loading airports: {e}")
        return {}


def load_routes(routes_file: str, airports: Dict) -> List[Tuple[int, int]]:
    """Load route data from OpenFlights routes.dat file"""
    # Define column names for routes.dat
    route_columns = [
        'airline', 'airline_id', 'source_airport', 'source_airport_id',
        'dest_airport', 'dest_airport_id', 'codeshare', 'stops', 'equipment'
    ]
    
    try:
        # Read routes data
        routes_df = pd.read_csv(routes_file, names=route_columns)
        
        # Filter out invalid routes
        routes_df = routes_df[routes_df['source_airport_id'] != '\\N']
        routes_df = routes_df[routes_df['dest_airport_id'] != '\\N']
        
        # Extract valid routes
        routes = []
        airport_ids = set(airports.keys())
        
        for _, row in routes_df.iterrows():
            source_id = int(row['source_airport_id'])
            dest_id = int(row['dest_airport_id'])

            # Only include routes between airports we have data for
            if source_id in airport_ids and dest_id in airport_ids:
                routes.append((source_id, dest_id))
                
        logger.info(f"Loaded {len(routes)} routes")
        return routes
        
    except Exception as e:
        logger.error(f"Error loading routes: {e}")
        return []


def load_air_traffic_data(airports_file: str, routes_file: str) -> Optional[nx.DiGraph]:
    """Load complete air traffic dataset and create NetworkX graph"""
    # Load data
    airports = load_airports(airports_file)
    if not airports:
        logger.error("No airport data loaded")
        return None
        
    routes = load_routes(routes_file, airports)
    if not routes:
        logger.error("No route data loaded")
        return None
    
    # Convert airports dict to list format expected by create_graph
    nodes = list(airports.values())
    
    graph = create_graph(nodes, routes, distance_type='haversine')
    
    logger.info(f"Created air traffic graph: {graph.number_of_nodes()} airports, {graph.number_of_edges()} routes")

    return graph


