"""
AIS Correlation module for SagarDrishti.
Filters AIS pings within a spatial radius and temporal window of the estimated spill origin.
"""

from typing import List, Dict, Any, Union
import pandas as pd
import numpy as np
from src.utils.geo_utils import haversine_km

def find_candidate_vessels(
    origin_lat: float,
    origin_lon: float,
    event_time: Union[str, pd.Timestamp],
    ais_df: pd.DataFrame,
    radius_km: float = 50.0,
    time_window_hours: float = 6.0
) -> List[Dict[str, Any]]:
    """
    Finds vessels that were close to the spill origin coordinate within the time window.
    
    Args:
        origin_lat: Estimated origin latitude
        origin_lon: Estimated origin longitude
        event_time: Estimated spill release timestamp
        ais_df: DataFrame matching AIS_FIELDS
        radius_km: Spatial filter radius in kilometers
        time_window_hours: Temporal window filter in hours
        
    Returns:
        List of dictionaries, each representing a candidate vessel:
            - 'mmsi': str
            - 'vessel_type': str
            - 'closest_distance_km': float
            - 'time_delta_hours': float (offset of closest approach to event_time)
    """
    if ais_df.empty:
        return []
        
    e_time = pd.to_datetime(event_time)
    if e_time.tz is not None:
        e_time = e_time.tz_localize(None)
    
    # Work on a copy to avoid SettingWithCopyWarning
    df = ais_df.copy()
    
    # Ensure AIS timestamps are tz-naive
    df["timestamp_clean"] = pd.to_datetime(df["timestamp"])
    if hasattr(df["timestamp_clean"].dt, "tz") and df["timestamp_clean"].dt.tz is not None:
        df["timestamp_clean"] = df["timestamp_clean"].dt.tz_localize(None)
    
    # Calculate distance and time delta for each ping
    df["distance_km"] = df.apply(
        lambda row: haversine_km(origin_lat, origin_lon, row["lat"], row["lon"]),
        axis=1
    )
    df["time_delta_h"] = df.apply(
        lambda row: (row["timestamp_clean"] - e_time).total_seconds() / 3600.0,
        axis=1
    )
    
    # Filter by radius and time window
    filtered_df = df[
        (df["distance_km"] <= radius_km) &
        (df["time_delta_h"].abs() <= time_window_hours)
    ]
    
    candidates = []
    
    # Group by MMSI to find unique vessels
    for mmsi, group in filtered_df.groupby("mmsi"):
        min_idx = int(np.argmin(np.asarray(group["distance_km"])))
        closest_row = group.iloc[min_idx]
        
        candidates.append({
            "mmsi": str(mmsi),
            "vessel_type": str(closest_row.get("vessel_type", "Unknown")),
            "closest_distance_km": float(closest_row["distance_km"]),
            "time_delta_hours": float(closest_row["time_delta_h"])
        })
        
    # Sort candidates by closest distance
    candidates = sorted(candidates, key=lambda c: c["closest_distance_km"])
    return candidates
