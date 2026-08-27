"""
Synthetic AIS Data Generator for SagarDrishti Demo & Testing.
"""

from typing import Optional
import datetime
import random
import pandas as pd
import numpy as np

def generate_synthetic_vessels(
    origin_lat: float,
    origin_lon: float,
    event_time: str,
    n_vessels: int = 6
) -> pd.DataFrame:
    """
    Generate realistic synthetic vessel trajectories around the estimated spill origin.
    
    Args:
        origin_lat: Spill origin latitude
        origin_lon: Spill origin longitude
        event_time: ISO-8601 string or datetime of estimated spill release
        n_vessels: Number of synthetic vessels to generate (default: 6)
        
    Returns:
        DataFrame matching AIS_FIELDS with 'SYN-' prefixed MMSI values
    """
    if isinstance(event_time, str):
        base_time = pd.to_datetime(event_time)
    else:
        base_time = event_time

    records = []
    vessel_types = ["Crude Oil Tanker", "Chemical Tanker", "Container Ship", "Bulk Carrier", "Cargo Ship", "Fishing Vessel"]
    
    for i in range(n_vessels):
        mmsi = f"SYN-{100000000 + i*1379}"
        v_type = vessel_types[i % len(vessel_types)]
        
        # Determine if this vessel is configured as the prime suspect for demo clarity
        is_prime_suspect = (i == 0)
        
        # Speed in knots (5-20)
        base_speed = random.uniform(8.0, 16.0)
        course = random.uniform(30.0, 75.0)
        
        # Start offset in km
        if is_prime_suspect:
            dist_km = random.uniform(1.5, 3.5)
            time_offset_min = random.uniform(-40, 20)
        else:
            dist_km = random.uniform(12.0, 55.0)
            time_offset_min = random.uniform(-180, 180)
            
        # Convert km offset to rough lat/lon offset (1 deg lat ~ 111 km)
        lat_offset = (dist_km / 111.0) * random.choice([-1, 1])
        lon_offset = (dist_km / (111.0 * np.cos(np.radians(origin_lat)))) * random.choice([-1, 1])
        
        start_lat = origin_lat + lat_offset
        start_lon = origin_lon + lon_offset
        
        # Generate 10-15 pings along the track
        n_pings = random.randint(10, 15)
        for p in range(n_pings):
            t = base_time + datetime.timedelta(minutes=time_offset_min + (p * 15))
            # Move along course
            cur_lat = start_lat + (p * 0.012 * np.cos(np.radians(course)))
            cur_lon = start_lon + (p * 0.012 * np.sin(np.radians(course)))
            
            # Add anomaly to suspect
            cur_speed = base_speed
            if is_prime_suspect and p in (4, 5):
                cur_speed = 1.2  # unexpected slow down / stop
                
            records.append({
                "mmsi": mmsi,
                "timestamp": t,
                "lat": cur_lat,
                "lon": cur_lon,
                "speed": cur_speed,
                "heading": course,
                "course": course,
                "vessel_type": v_type
            })
            
    df = pd.DataFrame(records)
    return df.sort_values(by=["mmsi", "timestamp"]).reset_index(drop=True)
