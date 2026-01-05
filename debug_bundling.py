#!/usr/bin/env python3
"""Debug why edges bundle with k=1, d=1"""

import sys
from pathlib import Path
sys.path.append(str(Path(__file__).parent / 'src'))

from core.bundling import bundle_edges
from data_loader.brain_connectivity import load_brain_graphml
from src.dashboard.app import _create_migration_subset

def debug_bundling():
    print("🔍 Debugging bundling with k=1, d=1...")
    
    # Test brain dataset
    print("\n1. 🧠 Brain dataset with k=1, d=1:")
    brain_graph = load_brain_graphml("data/brain_connectivity/996782_repeated10_scale60.graphml")
    if brain_graph:
        result = bundle_edges(brain_graph, k=1.0, d=1.0)
        stats = result['statistics']
        ratio = (stats['bundled'] / stats['total_edges'] * 100) if stats['total_edges'] > 0 else 0
        print(f"   📊 {stats['bundled']}/{stats['total_edges']} edges bundled ({ratio:.1f}%)")
        
        if stats['bundled'] > 0:
            print(f"   🔍 First few bundled paths:")
            for i, bundle in enumerate(result['bundled_paths'][:3]):
                print(f"      Path {i+1}: {bundle['path']}")
                print(f"      Detour ratio: {bundle['detour_ratio']:.3f} (should be ≤ {1.0})")
                print(f"      Direct: {bundle['direct_length']:.3f}, Path: {bundle['path_length']:.3f}")
    
    # Test migration dataset
    print("\n2. 🏘️ Migration dataset with k=1, d=1:")
    migration_graph = _create_migration_subset("data/migration/outflow.txt")
    if migration_graph:
        result = bundle_edges(migration_graph, k=1.0, d=1.0)
        stats = result['statistics']
        ratio = (stats['bundled'] / stats['total_edges'] * 100) if stats['total_edges'] > 0 else 0
        print(f"   📊 {stats['bundled']}/{stats['total_edges']} edges bundled ({ratio:.1f}%)")
        
        if stats['bundled'] > 0:
            print(f"   🔍 First few bundled paths:")
            for i, bundle in enumerate(result['bundled_paths'][:3]):
                print(f"      Path {i+1}: {bundle['path']}")
                print(f"      Detour ratio: {bundle['detour_ratio']:.3f} (should be ≤ {1.0})")
                print(f"      Direct: {bundle['direct_length']:.3f}, Path: {bundle['path_length']:.3f}")
    
    print(f"\n💡 Analysis:")
    print(f"   With k=1.0, edges should only bundle if detour_ratio ≤ 1.0")
    print(f"   This means the bundled path is SHORTER than or equal to direct edge")
    print(f"   This can happen in networks where routing through other nodes is more efficient!")

if __name__ == "__main__":
    debug_bundling()