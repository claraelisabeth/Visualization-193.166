"""
Data loaders for edge path bundling datasets.

This module provides loaders for the three main datasets used in our study:
1. Air Traffic - OpenFlights dataset with airport routes (geographic, 2D)
2. Migration - US Census county migration flows (geographic, 2D) 
3. Brain Connectivity - HCP brain networks (spatial, 3D)
"""

from .air_traffic import load_air_traffic_data
from .migration import load_migration_json, load_outflow_data
from .brain_connectivity import load_brain_graphml

__all__ = [
    'load_air_traffic_data',
    'load_migration_json',
    'load_outflow_data',
    'load_brain_graphml'
]