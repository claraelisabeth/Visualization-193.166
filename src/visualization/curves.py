"""
Bézier Curve Generation for Edge Path Bundling

This module implements smooth curve generation following the paper's approach:
"Edge-Path Bundling: A Less Ambiguous Edge Bundling Approach"

Uses recursive smoothing and Bézier curve interpolation as described in the paper.
"""

import numpy as np
from typing import List, Tuple, Optional


def generate_control_points(path_nodes: List, node_positions: dict, smoothing_level: int = 2) -> List[np.ndarray]:
    """
    Generate control points for Bézier curve from bundled path.
    
    Follows the paper's approach:
    1. Extract node coordinates from path
    2. Apply recursive smoothing (paper default: level 2)
    
    Args:
        path_nodes: List of node IDs in the bundled path
        node_positions: Dict mapping node_id -> (x, y) coordinates
        smoothing_level: Level of recursive smoothing (paper default: 2)
        
    Returns:
        List of control points as numpy arrays
    """
    # Extract coordinates from path nodes
    control_points = []
    for node_id in path_nodes:
        if node_id in node_positions:
            x, y = node_positions[node_id]
            control_points.append(np.array([x, y]))
    
    # Apply recursive smoothing (paper's approach)
    return apply_recursive_smoothing(control_points, smoothing_level)


def apply_recursive_smoothing(points: List[np.ndarray], smoothing_level: int) -> List[np.ndarray]:
    """
    Apply recursive smoothing to control points.
    
    Paper's approach: "for each level of smoothing, insert new control point 
    in the middle of all points already in the array"
    
    Args:
        points: Original control points
        smoothing_level: Number of smoothing iterations
        
    Returns:
        Smoothed control points
    """
    if smoothing_level <= 1 or len(points) < 2:
        return points
        
    smoothed_points = points.copy()
    
    # Apply recursive smoothing (loop starts from 1, paper approach)
    for level in range(1, smoothing_level):
        new_points = []
        
        for i in range(len(smoothed_points) - 1):
            # Add current point
            new_points.append(smoothed_points[i])
            # Add midpoint between current and next
            midpoint = (smoothed_points[i] + smoothed_points[i + 1]) / 2.0
            new_points.append(midpoint)
        
        # Add final point
        new_points.append(smoothed_points[-1])
        smoothed_points = new_points
    
    return smoothed_points


def evaluate_bezier_curve(control_points: List[np.ndarray], t: float) -> np.ndarray:
    """
    Evaluate Bézier curve at parameter t using De Casteljau's algorithm.
    
    Args:
        control_points: List of control points
        t: Parameter value (0 <= t <= 1)
        
    Returns:
        Point on curve as numpy array
    """
    if not control_points:
        return np.array([0, 0])
    
    if t <= 0:
        return control_points[0]
    if t >= 1:
        return control_points[-1]
    
    # De Casteljau's algorithm
    points = control_points.copy()
    
    while len(points) > 1:
        next_level = []
        for i in range(len(points) - 1):
            # Linear interpolation between consecutive points
            interpolated = (1 - t) * points[i] + t * points[i + 1]
            next_level.append(interpolated)
        points = next_level
    
    return points[0]


def generate_bezier_curve(control_points: List[np.ndarray], num_samples: int = 100) -> List[Tuple[float, float]]:
    """
    Generate sampled points along Bézier curve.
    
    Paper's default: n=100 sampling points
    
    Args:
        control_points: Control points for the curve
        num_samples: Number of points to sample (paper default: 100)
        
    Returns:
        List of (x, y) coordinates along the curve
    """
    if len(control_points) < 2:
        # Not enough points for a curve, return straight line
        if len(control_points) == 1:
            return [(control_points[0][0], control_points[0][1])]
        return []
    
    if num_samples < 2:
        # Return endpoints only
        start = control_points[0]
        end = control_points[-1]
        return [(start[0], start[1]), (end[0], end[1])]
    
    curve_points = []
    
    for i in range(num_samples):
        t = i / (num_samples - 1)  # Parameter from 0 to 1
        point = evaluate_bezier_curve(control_points, t)
        curve_points.append((float(point[0]), float(point[1])))
    
    return curve_points


def create_smooth_bundled_path(path_nodes: List, node_positions: dict, 
                              smoothing_level: int = 2, num_samples: int = 100) -> List[Tuple[float, float]]:
    """
    Create smooth Bézier curve for a bundled path.
    
    Complete pipeline following the paper's approach:
    1. Generate control points from path
    2. Apply recursive smoothing
    3. Generate smooth Bézier curve
    
    Args:
        path_nodes: List of node IDs in the bundled path
        node_positions: Dict mapping node_id -> (x, y) coordinates  
        smoothing_level: Smoothing level (paper default: 2)
        num_samples: Curve sampling points (paper default: 100)
        
    Returns:
        List of (x, y) coordinates for smooth curve
    """
    # Generate control points
    control_points = generate_control_points(path_nodes, node_positions, smoothing_level)
    
    # Generate smooth curve
    curve_points = generate_bezier_curve(control_points, num_samples)
    
    return curve_points

