#!/usr/bin/env python3
"""Test performance with existing dashboard datasets"""

import time
import sys
from pathlib import Path
sys.path.append(str(Path(__file__).parent / 'src'))

# Import dashboard functions directly
from src.dashboard.app import _create_migration_subset, _create_major_airports_subset, _create_air_traffic_demo, _create_migration_demo
from data_loader.brain_connectivity import load_brain_graphml
from core.bundling import bundle_edges

def test_dashboard_datasets():
    print("🔍 Testing performance with dashboard's actual datasets...")
    
    datasets = {}
    
    # 1. Brain connectivity (real data)
    print("\n1. 🧠 Brain connectivity...")
    brain_file = "data/brain_connectivity/996782_repeated10_scale60.graphml"
    brain_graph = load_brain_graphml(brain_file)
    if brain_graph:
        datasets['brain'] = brain_graph
        print(f"   📊 {brain_graph.number_of_nodes()} nodes, {brain_graph.number_of_edges()} edges")
    
    # 2. Migration data (subset as dashboard does)
    print("\n2. 🏘️ Migration data...")
    outflow_file = "data/migration/outflow.txt"
    migration_graph = _create_migration_subset(outflow_file)
    if migration_graph:
        datasets['migration'] = migration_graph
        print(f"   📊 {migration_graph.number_of_nodes()} nodes, {migration_graph.number_of_edges()} edges")
    else:
        # Fallback to demo
        migration_graph = _create_migration_demo()
        datasets['migration_demo'] = migration_graph
        print(f"   📊 Demo: {migration_graph.number_of_nodes()} nodes, {migration_graph.number_of_edges()} edges")
    
    # 3. Air traffic data (subset as dashboard does)
    print("\n3. ✈️ Air traffic data...")
    airports_file = "data/air_traffic/airports.dat"
    routes_file = "data/air_traffic/routes.dat"
    air_graph = _create_major_airports_subset(airports_file, routes_file)
    if air_graph:
        datasets['air_traffic'] = air_graph
        print(f"   📊 {air_graph.number_of_nodes()} nodes, {air_graph.number_of_edges()} edges")
    else:
        # Fallback to demo
        air_graph = _create_air_traffic_demo()
        datasets['air_traffic_demo'] = air_graph
        print(f"   📊 Demo: {air_graph.number_of_nodes()} nodes, {air_graph.number_of_edges()} edges")
    
    # Test bundling performance on each dataset
    print(f"\n⚡ Bundling performance test (k=2.0, d=1.0):")
    results = {}
    
    for name, graph in datasets.items():
        start = time.time()
        result = bundle_edges(graph, k=2.0, d=1.0)
        bundle_time = time.time() - start
        
        stats = result['statistics']
        ratio = (stats['bundled'] / stats['total_edges'] * 100) if stats['total_edges'] > 0 else 0
        
        results[name] = {
            'time': bundle_time,
            'bundling_ratio': ratio,
            'total_edges': stats['total_edges']
        }
        
        print(f"   {name:15}: {bundle_time:6.2f}s  ({ratio:5.1f}% bundled)")
    
    # Performance assessment
    print(f"\n💡 Dashboard performance assessment:")
    max_time = max(results.values(), key=lambda x: x['time'])['time']
    
    if max_time < 1.0:
        print(f"   ✅ Excellent: All datasets bundle in under 1 second")
    elif max_time < 3.0:
        print(f"   ✅ Good: All datasets bundle in under 3 seconds")
    elif max_time < 5.0:
        print(f"   ⚠️  Acceptable: Slowest takes {max_time:.1f}s")
    else:
        print(f"   ❌ Slow: Optimization needed, slowest takes {max_time:.1f}s")
    
    print(f"   🎯 Dashboard user experience: {'Responsive' if max_time < 3.0 else 'May feel slow'}")

if __name__ == "__main__":
    test_dashboard_datasets()