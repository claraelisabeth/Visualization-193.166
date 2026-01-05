#!/usr/bin/env python3
"""
Performance Testing Script for Edge Path Bundling Dashboard

Tests various aspects of the dashboard performance:
1. Data loading times
2. Bundling algorithm performance
3. Visualization rendering
4. Memory usage
"""

import time
import sys
import psutil
import os
from pathlib import Path

# Add source to path
sys.path.append(str(Path(__file__).parent / 'src'))

from core.bundling import bundle_edges
from data_loader.brain_connectivity import load_brain_graphml
from data_loader.migration import load_outflow_data
from data_loader import load_air_traffic_data
from visualization import create_network_visualization

def measure_time(func):
    """Decorator to measure function execution time."""
    def wrapper(*args, **kwargs):
        start_time = time.time()
        result = func(*args, **kwargs)
        end_time = time.time()
        return result, end_time - start_time
    return wrapper

def get_memory_usage():
    """Get current memory usage in MB."""
    process = psutil.Process(os.getpid())
    return process.memory_info().rss / 1024 / 1024

@measure_time
def test_data_loading():
    """Test data loading performance for all datasets."""
    results = {}
    
    print("🔍 Testing data loading performance...")
    
    # Test brain data loading
    brain_file = "data/brain_connectivity/996782_repeated10_scale60.graphml"
    if Path(brain_file).exists():
        start_mem = get_memory_usage()
        brain_graph, load_time = measure_time(load_brain_graphml)(brain_file)
        end_mem = get_memory_usage()
        
        results['brain'] = {
            'load_time': load_time,
            'nodes': brain_graph.number_of_nodes() if brain_graph else 0,
            'edges': brain_graph.number_of_edges() if brain_graph else 0,
            'memory_delta': end_mem - start_mem
        }
        print(f"  🧠 Brain: {load_time:.2f}s, {results['brain']['nodes']} nodes, {results['brain']['edges']} edges")
    
    # Test air traffic data loading
    airports_file = "data/air_traffic/airports.dat"
    routes_file = "data/air_traffic/routes.dat"
    if Path(airports_file).exists() and Path(routes_file).exists():
        start_mem = get_memory_usage()
        air_graph, load_time = measure_time(load_air_traffic_data)(airports_file, routes_file)
        end_mem = get_memory_usage()
        
        results['air_traffic'] = {
            'load_time': load_time,
            'nodes': air_graph.number_of_nodes() if air_graph else 0,
            'edges': air_graph.number_of_edges() if air_graph else 0,
            'memory_delta': end_mem - start_mem
        }
        print(f"  ✈️  Air Traffic: {load_time:.2f}s, {results['air_traffic']['nodes']} nodes, {results['air_traffic']['edges']} edges")
    
    # Test migration data loading  
    migration_file = "data/migration/outflow.txt"
    if Path(migration_file).exists():
        start_mem = get_memory_usage()
        migration_graph, load_time = measure_time(load_outflow_data)(migration_file, min_flow_threshold=3000)
        end_mem = get_memory_usage()
        
        results['migration'] = {
            'load_time': load_time,
            'nodes': migration_graph.number_of_nodes() if migration_graph else 0,
            'edges': migration_graph.number_of_edges() if migration_graph else 0,
            'memory_delta': end_mem - start_mem
        }
        print(f"  🏘️  Migration: {load_time:.2f}s, {results['migration']['nodes']} nodes, {results['migration']['edges']} edges")
    
    return results

@measure_time
def test_bundling_performance(graph, dataset_name, k_values=[1.0, 2.0, 3.0], d_values=[1.0, 2.0, 3.0]):
    """Test bundling algorithm performance with different parameters."""
    results = {}
    
    print(f"\n🔍 Testing bundling performance for {dataset_name}...")
    
    for k in k_values:
        for d in d_values:
            start_mem = get_memory_usage()
            bundling_result, bundle_time = measure_time(bundle_edges)(graph, k=k, d=d)
            end_mem = get_memory_usage()
            
            stats = bundling_result['statistics']
            bundling_ratio = (stats['bundled'] / stats['total_edges'] * 100) if stats['total_edges'] > 0 else 0
            
            results[f"k{k}_d{d}"] = {
                'bundle_time': bundle_time,
                'total_edges': stats['total_edges'],
                'bundled_edges': stats['bundled'],
                'bundling_ratio': bundling_ratio,
                'memory_delta': end_mem - start_mem
            }
            
            print(f"  📊 k={k}, d={d}: {bundle_time:.3f}s, {bundling_ratio:.1f}% bundled")
    
    return results

@measure_time 
def test_visualization_performance(graph, bundled_paths, title):
    """Test visualization rendering performance."""
    print(f"\n🔍 Testing visualization performance for {title}...")
    
    start_mem = get_memory_usage()
    fig, viz_time = measure_time(create_network_visualization)(
        graph, bundled_paths, title, use_curves=True, smoothing_level=2, num_samples=100
    )
    end_mem = get_memory_usage()
    
    result = {
        'viz_time': viz_time,
        'memory_delta': end_mem - start_mem,
        'traces_count': len(fig.data) if fig else 0
    }
    
    print(f"  📈 Visualization: {viz_time:.3f}s, {result['traces_count']} traces")
    return result

def run_performance_tests():
    """Run comprehensive performance tests."""
    print("🚀 Starting Edge Path Bundling Performance Tests\n")
    print(f"💾 Initial memory usage: {get_memory_usage():.2f} MB")
    
    # Test data loading
    data_results, total_load_time = test_data_loading()
    
    # Test bundling for each dataset
    bundling_results = {}
    viz_results = {}
    
    for dataset_name, data_info in data_results.items():
        if data_info['nodes'] > 0:
            # Load graph again for testing
            if dataset_name == 'brain':
                graph = load_brain_graphml("data/brain_connectivity/996782_repeated10_scale60.graphml")
            elif dataset_name == 'air_traffic':
                graph = load_air_traffic_data("data/air_traffic/airports.dat", "data/air_traffic/routes.dat")
            elif dataset_name == 'migration':
                graph = load_outflow_data("data/migration/outflow.txt", min_flow_threshold=3000)
            
            if graph:
                # Test bundling performance
                bundling_results[dataset_name], _ = test_bundling_performance(graph, dataset_name)
                
                # Test visualization with default parameters
                bundle_result = bundle_edges(graph, k=2.0, d=1.5)
                viz_results[dataset_name], _ = test_visualization_performance(
                    graph, bundle_result['bundled_paths'], f"{dataset_name.title()} Network"
                )
    
    # Print summary
    print("\n" + "="*60)
    print("📋 PERFORMANCE SUMMARY")
    print("="*60)
    
    print(f"\n📊 Data Loading Times:")
    for dataset, info in data_results.items():
        print(f"  {dataset:12}: {info['load_time']:6.3f}s  ({info['nodes']:4d} nodes, {info['edges']:5d} edges)")
    
    print(f"\n⚡ Bundling Performance (k=2.0, d=1.5):")
    for dataset in bundling_results:
        if 'k2.0_d1.5' in bundling_results[dataset]:
            result = bundling_results[dataset]['k2.0_d1.5']
            print(f"  {dataset:12}: {result['bundle_time']:6.3f}s  ({result['bundling_ratio']:5.1f}% bundled)")
    
    print(f"\n🎨 Visualization Times:")
    for dataset, result in viz_results.items():
        print(f"  {dataset:12}: {result['viz_time']:6.3f}s  ({result['traces_count']:3d} traces)")
    
    print(f"\n💾 Final memory usage: {get_memory_usage():.2f} MB")
    
    # Performance recommendations
    print(f"\n💡 PERFORMANCE RECOMMENDATIONS:")
    
    # Check if any datasets are particularly slow
    slow_datasets = []
    for dataset, info in data_results.items():
        if info['load_time'] > 5.0:  # > 5 seconds
            slow_datasets.append(dataset)
    
    if slow_datasets:
        print(f"  🐌 Slow data loading detected: {', '.join(slow_datasets)}")
        print(f"     Consider caching or reducing dataset size")
    
    # Check bundling performance
    slow_bundling = []
    for dataset in bundling_results:
        if 'k2.0_d1.5' in bundling_results[dataset]:
            if bundling_results[dataset]['k2.0_d1.5']['bundle_time'] > 3.0:
                slow_bundling.append(dataset)
    
    if slow_bundling:
        print(f"  🔄 Slow bundling detected: {', '.join(slow_bundling)}")
        print(f"     Consider algorithmic optimizations")
    
    # Check visualization performance
    slow_viz = []
    for dataset, result in viz_results.items():
        if result['viz_time'] > 2.0:
            slow_viz.append(dataset)
    
    if slow_viz:
        print(f"  🎨 Slow visualization detected: {', '.join(slow_viz)}")
        print(f"     Consider reducing trace count or curve samples")
    
    if not (slow_datasets or slow_bundling or slow_viz):
        print(f"  ✅ All components perform well!")

if __name__ == "__main__":
    run_performance_tests()