"""
Particle Model module for SagarDrishti.
Initializes particles inside a Shapely polygon for drift modeling.
"""

import random
from typing import List, Tuple
import numpy as np
from shapely.geometry import Polygon, Point

def initialize_particles(spill_polygon: Polygon, n_particles: int = 500) -> np.ndarray:
    """
    Uniformly samples particles inside the spill polygon using rejection sampling.
    
    Args:
        spill_polygon: shapely.geometry.Polygon in lat/lon space.
        n_particles: number of particles to sample.
        
    Returns:
        numpy.ndarray of shape (n_particles, 2) where each row is (lat, lon).
    """
    if spill_polygon is None or spill_polygon.is_empty:
        # Return fallback array if polygon is empty
        return np.zeros((n_particles, 2))
        
    if not spill_polygon.is_valid:
        spill_polygon = spill_polygon.buffer(0)
        
    min_lon, min_lat, max_lon, max_lat = spill_polygon.bounds
    particles = []
    
    # Safety counter to avoid infinite loops
    attempts = 0
    max_attempts = n_particles * 100
    
    while len(particles) < n_particles and attempts < max_attempts:
        attempts += 1
        lon = random.uniform(min_lon, max_lon)
        lat = random.uniform(min_lat, max_lat)
        point = Point(lon, lat)
        
        if spill_polygon.contains(point):
            particles.append((lat, lon))
            
    # Fallback if rejection sampling is too slow or shape is too thin
    if len(particles) < n_particles:
        centroid = spill_polygon.centroid
        lat_c, lon_c = centroid.y, centroid.x
        while len(particles) < n_particles:
            # Add small random offset around centroid
            offset_lat = random.normalvariate(0, (max_lat - min_lat) * 0.1)
            offset_lon = random.normalvariate(0, (max_lon - min_lon) * 0.1)
            particles.append((lat_c + offset_lat, lon_c + offset_lon))
            
    return np.array(particles)
