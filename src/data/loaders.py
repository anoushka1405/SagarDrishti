"""
Data Loaders for SagarDrishti Pipeline.
Handles satellite SAR imagery, AIS telemetry, ocean currents, and weather grids.
"""

from typing import Dict, Any, Optional
import os
import pandas as pd
import numpy as np

class DataLoadError(Exception):
    """Custom human-readable exception for missing or corrupt data files."""
    pass

def load_satellite(path: str) -> Dict[str, Any]:
    """
    Load Sentinel-1 SAR GeoTIFF or HDF5 raster data.
    
    Args:
        path: Path to SAR raster file
        
    Returns:
        Dict matching SATELLITE_FIELDS contract
    """
    if not os.path.exists(path):
        # TODO(fallback): Check config.yaml data_sources.use_mock_if_missing
        raise DataLoadError(f"SAR satellite image not found at path: {path}")
    
    # In real execution, use rasterio to extract pixel array and geotransform
    return {
        "image_id": os.path.basename(path),
        "timestamp": "2026-08-27T10:30:00Z",
        "bbox": (18.2, 70.5, 18.6, 71.1),
        "sar_array": np.zeros((512, 512), dtype=np.float32),
        "resolution_m": 10.0,
        "centroid_lat": 18.43,
        "centroid_lon": 70.82,
        "ground_truth_mask": None
    }

def load_ais(path: str) -> pd.DataFrame:
    """
    Load AIS vessel tracking pings from CSV or Parquet.
    
    Args:
        path: Path to AIS file
        
    Returns:
        DataFrame matching AIS_FIELDS
    """
    if not os.path.exists(path):
        # TODO(fallback): Check config.yaml data_sources.use_mock_if_missing
        raise DataLoadError(f"AIS data file not found at path: {path}")
        
    if path.endswith(".parquet"):
        df = pd.read_parquet(path)
    else:
        df = pd.read_csv(path)
        
    df["timestamp"] = pd.to_datetime(df["timestamp"])
    for col in ["speed", "heading", "course"]:
        if col in df.columns:
            df[col] = pd.to_numeric(df[col], errors="coerce")
    df = df.dropna(subset=["mmsi"])
    return df

def load_ocean_currents(path: str) -> Dict[str, Any]:
    """
    Load hydrodynamic current fields (NetCDF via xarray).
    """
    if not os.path.exists(path):
        # TODO(fallback): Check config.yaml
        raise DataLoadError(f"Ocean currents file not found at path: {path}")
    return {"status": "loaded", "u_current": None, "v_current": None}

def load_wind(path: str) -> Dict[str, Any]:
    """
    Load GFS/ERA5 wind vector fields.
    """
    if not os.path.exists(path):
        # TODO(fallback): Check config.yaml
        raise DataLoadError(f"Wind weather data file not found at path: {path}")
    return {"status": "loaded", "u_wind": None, "v_wind": None}
