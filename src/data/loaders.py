"""
Data Loaders for SagarDrishti Pipeline.
Handles satellite SAR imagery, AIS telemetry, ocean currents, and weather grids.
"""

from typing import Dict, Any, Optional, List, Tuple
import os
import glob
import re
import math
import numpy as np
import pandas as pd
import requests

try:
    import rasterio
except ImportError:
    rasterio = None

try:
    import xarray as xr
except ImportError:
    xr = None

class DataLoadError(Exception):
    """Custom human-readable exception for missing or corrupt data files."""
    pass

def load_satellite(path: str, acquisition_time: Optional[str] = None) -> Dict[str, Any]:
    """
    Load Sentinel-1 SAR GeoTIFF or HDF5 raster data.
    
    Args:
        path: Path to SAR raster file or directory
        acquisition_time: Optional explicit timestamp string. If None, attempts to extract from metadata/filename.
        
    Returns:
        Dict matching SATELLITE_FIELDS contract
    """
    # Fallback/Mock mode check
    if not os.path.exists(path):
        # Generate mock SAR image if file is missing
        res = _load_mock_satellite(path)
        if acquisition_time:
            res["timestamp"] = acquisition_time
        return res
        
    actual_path = path
    if os.path.isdir(path):
        tif_files = sorted(glob.glob(os.path.join(path, "*.tif")) + glob.glob(os.path.join(path, "*.tiff")))
        if not tif_files:
            raise DataLoadError(f"No GeoTIFF files found in directory: {path}")
        actual_path = tif_files[0]

    if rasterio is None:
        raise DataLoadError("rasterio is not installed, cannot read satellite images.")

    try:
        with rasterio.open(actual_path) as src:
            bands = src.read()  # (C, H, W)
            # Transpose to (H, W, C)
            sar_array = np.transpose(bands, (1, 2, 0)) if bands.ndim == 3 else np.expand_dims(bands, axis=-1)
            
            # Normalize to [0, 1] if not already
            if sar_array.max() > sar_array.min():
                sar_array = (sar_array - sar_array.min()) / (sar_array.max() - sar_array.min())
            else:
                sar_array = np.zeros_like(sar_array, dtype=np.float32)

            bounds = src.bounds
            left, bottom, right, top = bounds.left, bounds.bottom, bounds.right, bounds.top
            if src.crs and str(src.crs).upper() != "EPSG:4326":
                try:
                    from rasterio.warp import transform_bounds
                    left, bottom, right, top = transform_bounds(src.crs, "EPSG:4326", bounds.left, bounds.bottom, bounds.right, bounds.top)
                except Exception:
                    pass

            centroid_lat = (top + bottom) / 2.0
            centroid_lon = (left + right) / 2.0
            bbox = (left, bottom, right, top)
            
            # Try to get pixel resolution in meters
            try:
                resolution_m = float(src.res[0])
            except Exception:
                resolution_m = 10.0

            # Attempt timestamp extraction from metadata tags or filename pattern
            timestamp_val = acquisition_time
            if not timestamp_val:
                tags = src.tags()
                timestamp_val = tags.get("TIFFTAG_DATETIME") or tags.get("ACQUISITION_TIME") or tags.get("DATETIME")
            
            if not timestamp_val:
                # Try parsing Sentinel-1 filename standard pattern (e.g. S1A_..._YYYYMMDDTHMMSS_...)
                match = re.search(r"(\d{8}T\d{6})", os.path.basename(actual_path))
                if match:
                    raw_dt = match.group(1)
                    timestamp_val = f"{raw_dt[:4]}-{raw_dt[4:6]}-{raw_dt[6:8]}T{raw_dt[9:11]}:{raw_dt[11:13]}:{raw_dt[13:15]}Z"
            
            if not timestamp_val:
                import logging
                logging.getLogger("loaders").warning(
                    f"No timestamp metadata or Sentinel-1 filename timestamp found for '{os.path.basename(actual_path)}' "
                    f"and no explicit 'acquisition_time' provided. Falling back to default timestamp '2026-08-27T10:30:00Z'. "
                    f"For ML crop datasets (e.g. Zenodo 0001.tif), pass 'acquisition_time' explicitly."
                )
                timestamp_val = "2026-08-27T10:30:00Z"

            # Try to load a ground truth mask alongside the image (e.g. filename_mask.tif)
            mask = None
            base, ext = os.path.splitext(actual_path)
            mask_candidates = [
                f"{base}_mask{ext}",
                os.path.join(os.path.dirname(actual_path), "masks", f"{os.path.basename(base)}_mask{ext}"),
                os.path.join(os.path.dirname(actual_path), f"{os.path.basename(base)}_mask{ext}")
            ]
            
            # Support the SARSatelite folder structure
            if "SARSatelite" in actual_path:
                norm_path = os.path.normpath(actual_path)
                parts = norm_path.split(os.sep)
                if "Images" in parts:
                    idx = parts.index("Images")
                    parts[idx] = "Mask"
                    filename = parts[-1]
                    name_part, ext_part = os.path.splitext(filename)
                    parts[-1] = f"{name_part}_segmentation{ext_part}"
                    mask_candidates.append(os.sep.join(parts))

            for m_path in mask_candidates:
                if os.path.exists(m_path):
                    try:
                        with rasterio.open(m_path) as m_src:
                            mask = m_src.read(1)
                            break
                    except Exception:
                        pass

            return {
                "image_id": os.path.basename(actual_path),
                "timestamp": timestamp_val,
                "bbox": bbox,
                "sar_array": sar_array,
                "resolution_m": resolution_m,
                "centroid_lat": centroid_lat,
                "centroid_lon": centroid_lon,
                "ground_truth_mask": mask
            }
    except Exception as e:
        raise DataLoadError(f"Failed to load satellite image from {actual_path}: {e}")

def _load_mock_satellite(path: str) -> Dict[str, Any]:
    """Generates a mock SAR image structure for demo/testing."""
    sar_array = np.zeros((512, 512, 2), dtype=np.float32)
    # Add a mock slick (low backscatter dark region)
    # Let's create an ellipse mask in the center
    H, W, _ = sar_array.shape
    y, x = np.ogrid[:H, :W]
    center_y, center_x = H // 2, W // 2
    # Elongated ellipse slick shape
    slick_mask = (((x - center_x) / 60) ** 2 + ((y - center_y) / 20) ** 2) <= 1.0
    sar_array[slick_mask, :] = 0.1  # Low intensity
    sar_array[~slick_mask, :] = 0.6 + np.random.normal(0, 0.05, sar_array[~slick_mask, :].shape) # High ocean clutter
    
    return {
        "image_id": "mock_sentinel1.tif",
        "timestamp": "2026-08-27T10:30:00Z",
        "bbox": (70.5, 18.2, 71.1, 18.6),
        "sar_array": sar_array,
        "resolution_m": 10.0,
        "centroid_lat": 18.43,
        "centroid_lon": 70.82,
        "ground_truth_mask": slick_mask.astype(np.uint8)
    }

def load_ais(path: str, fallback_lat: float = 18.43, fallback_lon: float = 70.82, fallback_time: str = "2026-08-27T12:00:00Z") -> pd.DataFrame:
    """
    Load AIS vessel tracking pings from CSV or Parquet.
    
    Args:
        path: Path to AIS file
        fallback_lat: Latitude fallback for synthetic generator if file missing
        fallback_lon: Longitude fallback for synthetic generator if file missing
        fallback_time: Time fallback for synthetic generator if file missing
        
    Returns:
        DataFrame matching AIS_FIELDS
    """
    if not os.path.exists(path):
        # Try generating synthetic vessels if missing
        from src.data.synthetic_ais import generate_synthetic_vessels
        return generate_synthetic_vessels(fallback_lat, fallback_lon, fallback_time)
        
    try:
        if path.endswith(".parquet"):
            df = pd.read_parquet(path)
        else:
            df = pd.read_csv(path)
            
        df["timestamp"] = pd.to_datetime(df["timestamp"])
        for col in ["speed", "heading", "course", "lat", "lon"]:
            if col in df.columns:
                df[col] = pd.to_numeric(df[col], errors="coerce")
        df = df.dropna(subset=["mmsi", "timestamp", "lat", "lon"])
        return df
    except Exception as e:
        raise DataLoadError(f"Failed to load AIS data from {path}: {e}")

def load_ocean_currents(path: str, latitude: float = 18.43, longitude: float = 70.82, date_str: str = "2026-08-27") -> Dict[str, Any]:
    """
    Load hydrodynamic current fields from NetCDF, or fetch from Open-Meteo Marine API.
    """
    if os.path.exists(path) and xr is not None:
        try:
            ds = xr.open_dataset(path)
            # Parse NetCDF variables
            return {
                "timestamp": pd.to_datetime(ds['time'].values.tolist()) if 'time' in ds else pd.date_range(start=f"{date_str}T00:00:00Z", end=f"{date_str}T23:00:00Z", freq="1h"),
                "lat_grid": ds['latitude'].values if 'latitude' in ds else np.array([latitude]),
                "lon_grid": ds['longitude'].values if 'longitude' in ds else np.array([longitude]),
                "u_current": ds['uo'].values if 'uo' in ds else ds['u_current'].values if 'u_current' in ds else np.zeros((1, 1)),
                "v_current": ds['vo'].values if 'vo' in ds else ds['v_current'].values if 'v_current' in ds else np.zeros((1, 1)),
                "wave_height": ds['hs'].values if 'hs' in ds else None
            }
        except Exception as e:
            # Fall back to online API if NetCDF load fails
            pass

    # Free Online API fallback
    try:
        url = "https://marine-api.open-meteo.com/v1/marine"
        params = {
            "latitude": latitude,
            "longitude": longitude,
            "hourly": "ocean_current_velocity,ocean_current_direction",
            "start_date": date_str,
            "end_date": date_str,
        }
        resp = requests.get(url, params=params, timeout=10)
        resp.raise_for_status()
        data = resp.json()
        
        hourly = data.get("hourly", {})
        times = pd.to_datetime(hourly.get("time", []))
        raw_speeds = hourly.get("ocean_current_velocity", [])
        raw_dirs = hourly.get("ocean_current_direction", [])
        if len(times) == 0 or len(raw_speeds) == 0:
            raise ValueError("Empty hourly ocean current payload from API")
        speeds = np.array(raw_speeds, dtype=np.float32) / 3.6  # Convert km/h to m/s
        directions = np.radians(np.array(raw_dirs, dtype=np.float32))
        
        # Convert speed/dir to U (eastward) and V (northward) vectors
        u_current = speeds * np.sin(directions)
        v_current = speeds * np.cos(directions)
        
        return {
            "timestamp": times,
            "lat_grid": np.array([latitude]),
            "lon_grid": np.array([longitude]),
            "u_current": u_current.reshape(-1, 1, 1),
            "v_current": v_current.reshape(-1, 1, 1),
            "wave_height": np.zeros_like(u_current)
        }
    except Exception as e:
        # Final fallback - static zero current
        times = pd.date_range(start=f"{date_str}T00:00:00Z", end=f"{date_str}T23:00:00Z", freq="1h")
        return {
            "timestamp": times,
            "lat_grid": np.array([latitude]),
            "lon_grid": np.array([longitude]),
            "u_current": np.zeros((len(times), 1, 1), dtype=np.float32),
            "v_current": np.zeros((len(times), 1, 1), dtype=np.float32),
            "wave_height": None
        }

def load_wind(path: str, latitude: float = 18.43, longitude: float = 70.82, date_str: str = "2026-08-27") -> Dict[str, Any]:
    """
    Load weather wind fields from NetCDF, or fetch from Open-Meteo Weather API.
    """
    if os.path.exists(path) and xr is not None:
        try:
            ds = xr.open_dataset(path)
            return {
                "timestamp": pd.to_datetime(ds['time'].values.tolist()) if 'time' in ds else pd.date_range(start=f"{date_str}T00:00:00Z", end=f"{date_str}T23:00:00Z", freq="1h"),
                "lat_grid": ds['latitude'].values if 'latitude' in ds else np.array([latitude]),
                "lon_grid": ds['longitude'].values if 'longitude' in ds else np.array([longitude]),
                "u_wind": ds['u10'].values if 'u10' in ds else ds['u_wind'].values if 'u_wind' in ds else np.zeros((1, 1)),
                "v_wind": ds['v10'].values if 'v10' in ds else ds['v_wind'].values if 'v_wind' in ds else np.zeros((1, 1)),
            }
        except Exception as e:
            pass

    # Free Online API fallback
    try:
        url = "https://api.open-meteo.com/v1/forecast"
        params = {
            "latitude": latitude,
            "longitude": longitude,
            "hourly": "wind_speed_10m,wind_direction_10m",
            "start_date": date_str,
            "end_date": date_str,
        }
        resp = requests.get(url, params=params, timeout=10)
        resp.raise_for_status()
        data = resp.json()
        
        hourly = data.get("hourly", {})
        times = pd.to_datetime(hourly.get("time", []))
        raw_speeds = hourly.get("wind_speed_10m", [])
        raw_dirs = hourly.get("wind_direction_10m", [])
        if len(times) == 0 or len(raw_speeds) == 0:
            raise ValueError("Empty hourly wind payload from API")
        speeds = np.array(raw_speeds, dtype=np.float32) / 3.6  # Convert km/h to m/s
        
        # Wind direction is where it blows FROM.
        # Wind flow vector points to: dir_flow = dir_from + 180.
        # u = speed * sin(dir_flow) = -speed * sin(dir_from)
        # v = speed * cos(dir_flow) = -speed * cos(dir_from)
        directions = np.radians(np.array(raw_dirs, dtype=np.float32))
        u_wind = -speeds * np.sin(directions)
        v_wind = -speeds * np.cos(directions)
        
        return {
            "timestamp": times,
            "lat_grid": np.array([latitude]),
            "lon_grid": np.array([longitude]),
            "u_wind": u_wind.reshape(-1, 1, 1),
            "v_wind": v_wind.reshape(-1, 1, 1)
        }
    except Exception as e:
        # Final fallback - static light wind
        times = pd.date_range(start=f"{date_str}T00:00:00Z", end=f"{date_str}T23:00:00Z", freq="1h")
        return {
            "timestamp": times,
            "lat_grid": np.array([latitude]),
            "lon_grid": np.array([longitude]),
            "u_wind": np.ones((len(times), 1, 1), dtype=np.float32) * 1.5,  # 1.5 m/s eastward
            "v_wind": np.ones((len(times), 1, 1), dtype=np.float32) * 1.5   # 1.5 m/s northward
        }
