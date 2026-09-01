"""
AIS Trajectory Reconstruction module for SagarDrishti.
Reconstructs ordered vessel tracks and checks path intersection with estimated origin.
"""

import math
from typing import List, Tuple, Dict, Any, Union
import pandas as pd
from shapely.geometry import LineString, Point
from src.utils.geo_utils import haversine_km

def reconstruct_trajectory(mmsi: str, ais_df: pd.DataFrame) -> List[Tuple[float, float, str, float, float]]:
    """
    Reconstructs a vessel's trajectory sorted chronologically by timestamp.
    
    Args:
        mmsi: MMSI identifier of the vessel
        ais_df: DataFrame containing AIS pings
        
    Returns:
        List of tuples: (lat, lon, timestamp_str, speed, heading)
    """
    vessel_df = ais_df[ais_df["mmsi"].astype(str) == str(mmsi)]
    if vessel_df.empty:
        return []
        
    sorted_df = vessel_df.sort_values(by="timestamp")  # type: ignore
    
    trajectory = []
    for row in sorted_df.to_dict(orient="records"):
        lat = float(row["lat"])
        lon = float(row["lon"])
        ts = str(row["timestamp"])
        sp_val = row.get("speed", 0.0)
        speed = float(sp_val) if pd.notna(sp_val) else 0.0
        hd_val = row.get("heading", 0.0)
        heading = float(hd_val) if pd.notna(hd_val) else 0.0
        trajectory.append((lat, lon, ts, speed, heading))
        
    return trajectory

def trajectory_intersects_origin(
    trajectory: List[Tuple[float, float, str, float, float]],
    origin_lat: float,
    origin_lon: float,
    tolerance_km: float = 5.0
) -> Tuple[bool, float]:
    """
    Interpolates the vessel's path and checks if it passes within tolerance_km of origin.
    
    Args:
        trajectory: List of trajectory points (lat, lon, ts, speed, heading)
        origin_lat: Estimated origin latitude
        origin_lon: Estimated origin longitude
        tolerance_km: Distance threshold in kilometers
        
    Returns:
        Tuple: (intersects: bool, closest_distance_km: float)
    """
    if not trajectory:
        return False, 999.0
        
    if len(trajectory) < 2:
        # Only one point, calculate direct haversine distance
        lat, lon = trajectory[0][0], trajectory[0][1]
        dist = haversine_km(origin_lat, origin_lon, lat, lon)
        return dist <= tolerance_km, dist
        
    # Project trajectory points to kilometer space relative to origin (0, 0)
    lat_rad = math.radians(origin_lat)
    dy_per_deg = 110.574
    dx_per_deg = 111.320 * math.cos(lat_rad)
    
    proj_points = []
    for lat, lon, _, _, _ in trajectory:
        y = (lat - origin_lat) * dy_per_deg
        x = (lon - origin_lon) * dx_per_deg
        pt = (round(x, 6), round(y, 6))
        if not proj_points or proj_points[-1] != pt:
            proj_points.append(pt)
            
    if len(proj_points) < 2:
        dist = haversine_km(origin_lat, origin_lon, trajectory[0][0], trajectory[0][1])
        return dist <= tolerance_km, float(dist)
        
    try:
        # Create a LineString of the vessel track in km space
        vessel_line = LineString(proj_points)
        origin_point = Point(0, 0)
        
        # Distance in kilometers
        closest_dist = vessel_line.distance(origin_point)
        return closest_dist <= tolerance_km, float(closest_dist)
    except Exception:
        # Fallback to checking distance to each point
        dists = [haversine_km(origin_lat, origin_lon, p[0], p[1]) for p in trajectory]
        min_dist = min(dists)
        return min_dist <= tolerance_km, min_dist
