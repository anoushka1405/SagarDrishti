"""
Spill Geometry module for SagarDrishti.
Extracts connected components from masks and calculates geodesic area, perimeter, and shape features.
"""

import math
from typing import Dict, Any, Tuple
import numpy as np
from skimage.measure import label, regionprops
from shapely.geometry import Polygon

def compute_geometry(mask: np.ndarray, centroid_lat: float, centroid_lon: float, bbox_latlon: Tuple[float, float, float, float]) -> Dict[str, Any]:
    """
    Computes geometric properties of the largest connected spill component.
    
    Args:
        mask: Binary mask of shape (H, W) where 1 indicates oil spill.
        centroid_lat: Satellite image centroid latitude.
        centroid_lon: Satellite image centroid longitude.
        bbox_latlon: Bounding box of the image (min_lon, min_lat, max_lon, max_lat).
        
    Returns:
        Dictionary containing:
            - 'area_km2': float
            - 'perimeter_km': float
            - 'centroid': Tuple[float, float] (lat, lon)
            - 'bbox': Tuple[float, float, float, float] (min_lat, min_lon, max_lat, max_lon)
            - 'compactness': float (skimage style [0, 1] where 1 is circular)
            - 'polygon': shapely.geometry.Polygon (in lat/lon coordinates)
    """
    if mask.sum() == 0:
        return {
            "area_km2": 0.0,
            "perimeter_km": 0.0,
            "centroid": (centroid_lat, centroid_lon),
            "bbox": (centroid_lat, centroid_lon, centroid_lat, centroid_lon),
            "compactness": 0.0,
            "polygon": None
        }
        
    H, W = mask.shape
    min_lon, min_lat, max_lon, max_lat = bbox_latlon
    
    # 1. Label components and find the largest one
    labeled_mask = label(mask)
    regions = regionprops(labeled_mask)
    if not regions:
        return {
            "area_km2": 0.0,
            "perimeter_km": 0.0,
            "centroid": (centroid_lat, centroid_lon),
            "bbox": (centroid_lat, centroid_lon, centroid_lat, centroid_lon),
            "compactness": 0.0,
            "polygon": None
        }
        
    largest_region = max(regions, key=lambda r: r.area)
    
    # Get coordinates of contour or coords
    # We can get the coordinates of the region pixels to approximate the shape
    # For a polygon, we can find the convex hull or the outer boundary
    # Let's find coordinates of boundary pixels using simple edge detection
    # A simple way to get a polygon is using the coordinates of the region perimeter
    # Or simply:
    coords = largest_region.coords  # list of (r, c)
    
    # If the region is too small, fallback
    if len(coords) < 3:
        return {
            "area_km2": 0.0,
            "perimeter_km": 0.0,
            "centroid": (centroid_lat, centroid_lon),
            "bbox": (centroid_lat, centroid_lon, centroid_lat, centroid_lon),
            "compactness": 0.0,
            "polygon": None
        }
        
    # Convert pixels to lat/lon
    # row index maps to latitude (max_lat at row 0, min_lat at row H)
    # col index maps to longitude (min_lon at col 0, max_lon at col W)
    lats = max_lat - (coords[:, 0] / H) * (max_lat - min_lat)
    lons = min_lon + (coords[:, 1] / W) * (max_lon - min_lon)
    
    # Compute centroid of region in lat/lon
    c_r, c_c = largest_region.centroid
    spill_lat = max_lat - (c_r / H) * (max_lat - min_lat)
    spill_lon = min_lon + (c_c / W) * (max_lon - min_lon)
    
    # Local Mercator conversion factor to project lat/lon to meters (centered on spill centroid)
    lat_rad = math.radians(spill_lat)
    dy_per_deg = 110.574  # km per degree lat
    dx_per_deg = 111.320 * math.cos(lat_rad)  # km per degree lon
    
    # Convert all coordinate points of the region to local km coordinates relative to spill centroid
    x_km = (lons - spill_lon) * dx_per_deg
    y_km = (lats - spill_lat) * dy_per_deg
    
    # Approximate polygon using convex hull or boundary of points
    # Let's use standard convex hull from skimage or simple outline to build a Polygon
    from scipy.spatial import ConvexHull
    points = np.column_stack((x_km, y_km))
    
    try:
        hull = ConvexHull(points)
        hull_points = points[hull.vertices]
        
        # Build Shapely polygon in kilometer space
        poly_km = Polygon(hull_points)
        
        # Build Shapely polygon in lat/lon space
        hull_lons = spill_lon + (hull_points[:, 0] / dx_per_deg)
        hull_lats = spill_lat + (hull_points[:, 1] / dy_per_deg)
        poly_latlon = Polygon(np.column_stack((hull_lons, hull_lats)))
        
        area_km2 = poly_km.area
        perimeter_km = poly_km.length
    except Exception:
        # Fallback if ConvexHull fails (e.g. collinear points)
        # Use pixel area approximation
        pixel_area_km2 = largest_region.area * ((max_lon - min_lon) * dx_per_deg / W) * ((max_lat - min_lat) * dy_per_deg / H)
        area_km2 = max(0.01, pixel_area_km2)
        perimeter_km = max(0.1, math.sqrt(area_km2) * 4)
        
        # Mock polygon
        r = math.sqrt(area_km2) / math.sqrt(math.pi)
        angles = np.linspace(0, 2*math.pi, 20, endpoint=False)
        hull_lons = spill_lon + (r * np.cos(angles) / dx_per_deg)
        hull_lats = spill_lat + (r * np.sin(angles) / dy_per_deg)
        poly_latlon = Polygon(np.column_stack((hull_lons, hull_lats)))

    if poly_latlon is not None and not poly_latlon.is_valid:
        poly_latlon = poly_latlon.buffer(0)
        
    # Compactness: 4 * pi * Area / (Perimeter^2)
    if perimeter_km > 0:
        compactness = (4.0 * math.pi * area_km2) / (perimeter_km ** 2)
    else:
        compactness = 0.0
    compactness = min(1.0, max(0.0, compactness))
    
    # Bounding box of region in lat/lon
    r_min, c_min, r_max, c_max = largest_region.bbox
    spill_min_lat = max_lat - (r_max / H) * (max_lat - min_lat)
    spill_max_lat = max_lat - (r_min / H) * (max_lat - min_lat)
    spill_min_lon = min_lon + (c_min / W) * (max_lon - min_lon)
    spill_max_lon = min_lon + (c_max / W) * (max_lon - min_lon)
    bbox = (spill_min_lat, spill_min_lon, spill_max_lat, spill_max_lon)
    
    return {
        "area_km2": float(area_km2),
        "perimeter_km": float(perimeter_km),
        "centroid": (float(spill_lat), float(spill_lon)),
        "bbox": bbox,
        "compactness": float(compactness),
        "polygon": poly_latlon
    }
