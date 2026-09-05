"""
AIS Behavioural Features module for SagarDrishti.
Extracts speed anomalies, heading deltas, unexpected stops, route deviations, and signal gaps.
"""

import math
from typing import List, Tuple, Dict, Any, Optional
import numpy as np
import pandas as pd
from shapely.geometry import LineString, Point
from src.utils.geo_utils import haversine_km

def extract_behaviour_features(
    trajectory: List[Tuple[float, float, str, float, float]],
    origin_lat: Optional[float] = None,
    origin_lon: Optional[float] = None,
    event_time: Optional[str] = None
) -> Dict[str, Any]:
    """
    Extracts behavior anomaly features from a vessel's trajectory.
    
    Args:
        trajectory: List of tuples (lat, lon, timestamp_str, speed, heading)
        origin_lat: Optional estimated origin latitude
        origin_lon: Optional estimated origin longitude
        event_time: Optional estimated event time (ISO string or Timestamp)
        
    Returns:
        Dictionary of behavioural features
    """
    features = {
        "speed_anomaly": 0.0,
        "heading_change_max": 0.0,
        "unexpected_stop": False,
        "route_deviation_km": 0.0,
        "ais_gap_near_origin": False,
        "max_gap_minutes": 0.0
    }
    
    if not trajectory or len(trajectory) < 2:
        return features
        
    speeds = [p[3] for p in trajectory]
    headings = [p[4] for p in trajectory]
    times = []
    for p in trajectory:
        t = pd.to_datetime(p[2])
        if getattr(t, "tz", None) is not None:
            t = t.tz_localize(None)
        times.append(t)
    
    # 1. Speed Anomaly
    median_speed = float(np.median(speeds))
    # Deviation from own median speed (standard deviation/variance)
    if median_speed > 1.0:
        std_speed = float(np.std(speeds))
        features["speed_anomaly"] = float(std_speed / median_speed)
    else:
        features["speed_anomaly"] = 0.0
        
    # Unexpected stop mid-route (speed drops below 1 knot while median is > 5 knots)
    if min(speeds) < 1.0 and median_speed > 4.0:
        features["unexpected_stop"] = True
        
    # 2. Heading changes
    max_heading_delta = 0.0
    for i in range(1, len(headings)):
        h1, h2 = headings[i-1], headings[i]
        diff = abs(h1 - h2)
        # Handle wrap-around
        heading_delta = min(diff, 360.0 - diff)
        if heading_delta > max_heading_delta:
            max_heading_delta = heading_delta
    features["heading_change_max"] = float(max_heading_delta)
    
    # 3. Route Deviation (max perpendicular distance from start-end line)
    try:
        lat_start, lon_start = trajectory[0][0], trajectory[0][1]
        lat_end, lon_end = trajectory[-1][0], trajectory[-1][1]
        
        # Project points to local km coordinates relative to start point
        lat_rad = math.radians(lat_start)
        dy_per_deg = 110.574
        dx_per_deg = 111.320 * math.cos(lat_rad)
        
        proj_points = []
        for lat, lon, _, _, _ in trajectory:
            y = (lat - lat_start) * dy_per_deg
            x = (lon - lon_start) * dx_per_deg
            proj_points.append((x, y))
            
        start_pt = proj_points[0]
        end_pt = proj_points[-1]
        
        dx = end_pt[0] - start_pt[0]
        dy = end_pt[1] - start_pt[1]
        if math.sqrt(dx * dx + dy * dy) > 0.001:
            route_line = LineString([start_pt, end_pt])
            max_dev = 0.0
            for pt in proj_points[1:-1]:
                dev = route_line.distance(Point(pt))
                if dev > max_dev:
                    max_dev = dev
            features["route_deviation_km"] = float(max_dev)
    except Exception:
        pass
        
    # 4. AIS Gaps and proximity to origin/time
    max_gap_secs = 0.0
    gap_near_origin = False
    
    e_time = pd.to_datetime(event_time) if event_time else None
    if e_time is not None and getattr(e_time, "tz", None) is not None:
        e_time = e_time.tz_localize(None)
    
    for i in range(1, len(times)):
        t1, t2 = times[i-1], times[i]
        gap_sec = (t2 - t1).total_seconds()
        if gap_sec > max_gap_secs:
            max_gap_secs = gap_sec
            
        # If gap is > 30 minutes (1800 seconds)
        if gap_sec > 1800:
            # Check if this gap occurred near the estimated spill origin and release window
            if origin_lat is not None and origin_lon is not None and e_time is not None:
                lat1, lon1 = trajectory[i-1][0], trajectory[i-1][1]
                lat2, lon2 = trajectory[i][0], trajectory[i][1]
                
                # Check distances
                dist1 = haversine_km(origin_lat, origin_lon, lat1, lon1)
                dist2 = haversine_km(origin_lat, origin_lon, lat2, lon2)
                
                # Check time differences
                time_diff1 = abs((t1 - e_time).total_seconds()) / 3600.0
                time_diff2 = abs((t2 - e_time).total_seconds()) / 3600.0
                
                # If gap starts or ends within 15 km of origin and within 3 hours of spill event
                if (dist1 <= 15.0 or dist2 <= 15.0) and (time_diff1 <= 3.0 or time_diff2 <= 3.0):
                    gap_near_origin = True
                    
    features["max_gap_minutes"] = float(max_gap_secs / 60.0)
    features["ais_gap_near_origin"] = gap_near_origin
    
    return features
