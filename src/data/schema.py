"""
Data Contracts and Schema Definitions for SagarDrishti Pipeline.
Enforces consistent data contracts between modules.
"""

from typing import List, Tuple, Dict, Optional, Any
from dataclasses import dataclass

SATELLITE_FIELDS: List[str] = [
    "image_id",
    "timestamp",
    "bbox",           # (min_lat, min_lon, max_lat, max_lon)
    "sar_array",      # 2D numpy array normalized [0, 1]
    "resolution_m",
    "centroid_lat",
    "centroid_lon",
    "ground_truth_mask" # Optional 2D array or None
]

AIS_FIELDS: List[str] = [
    "mmsi",
    "timestamp",
    "lat",
    "lon",
    "speed",          # knots
    "heading",        # degrees 0-360
    "course",         # degrees 0-360
    "vessel_type"     # e.g., 'Tanker', 'Cargo', 'Fishing'
]

OCEAN_FIELDS: List[str] = [
    "timestamp",
    "lat_grid",
    "lon_grid",
    "u_current",       # m/s eastward
    "v_current",       # m/s northward
    "wave_height"      # optional
]

WEATHER_FIELDS: List[str] = [
    "timestamp",
    "lat_grid",
    "lon_grid",
    "u_wind",          # m/s eastward
    "v_wind"           # m/s northward
]

@dataclass
class SpillGeometry:
    area_km2: float
    perimeter_km: float
    centroid: Tuple[float, float]
    bbox: Tuple[float, float, float, float]
    compactness: float
    confidence: float

@dataclass
class SuspectVessel:
    mmsi: str
    vessel_type: str
    attribution_score: float  # 0 to 100
    confidence_level: str     # 'Low', 'Medium', 'High'
    closest_distance_km: float
    time_delta_hours: float
    evidence: List[str]
    trajectory: List[Tuple[float, float, str]]
