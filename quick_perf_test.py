#!/usr/bin/env python3
"""Quick performance test to identify bottlenecks"""

import time
import sys
from pathlib import Path
sys.path.append(str(Path(__file__).parent / 'src'))

from core.bundling import bundle_edges
from data_loader.brain_connectivity import load_brain_graphml

def quick_test():
    print("🔍 Quick performance test...")
    
    # Test brain data (smallest dataset)
    print("\n1. Loading brain data...")
    start = time.time()
    graph = load_brain_graphml("data/brain_connectivity/996782_repeated10_scale60.graphml")
    load_time = time.time() - start
    print(f"   ✅ Loaded in {load_time:.2f}s: {graph.number_of_nodes()} nodes, {graph.number_of_edges()} edges")
    
    # Test bundling with default params
    print("\n2. Testing bundling algorithm...")
    start = time.time() 
    result = bundle_edges(graph, k=2.0, d=1.0)
    bundle_time = time.time() - start
    stats = result['statistics']
    bundling_ratio = (stats['bundled'] / stats['total_edges'] * 100) if stats['total_edges'] > 0 else 0
    print(f"   ✅ Bundled in {bundle_time:.2f}s: {stats['bundled']}/{stats['total_edges']} edges ({bundling_ratio:.1f}%)")
    
    # Test with different k values (performance critical parameter)
    print("\n3. Testing different k values...")
    for k in [1.0, 1.5, 2.0, 3.0]:
        start = time.time()
        result = bundle_edges(graph, k=k, d=1.0)
        bundle_time = time.time() - start
        stats = result['statistics'] 
        ratio = (stats['bundled'] / stats['total_edges'] * 100) if stats['total_edges'] > 0 else 0
        print(f"   k={k}: {bundle_time:.3f}s, {ratio:.1f}% bundled")
    
    print(f"\n💡 Performance analysis:")
    if load_time > 2.0:
        print(f"   🐌 Data loading is slow ({load_time:.2f}s)")
    if bundle_time > 5.0:
        print(f"   🔄 Bundling algorithm is slow ({bundle_time:.2f}s)")
    if bundle_time < 1.0 and load_time < 1.0:
        print(f"   ✅ Performance looks good!")
    
if __name__ == "__main__":
    quick_test()