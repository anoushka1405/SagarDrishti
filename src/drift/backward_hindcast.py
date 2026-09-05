"""
Backward Hindcast module for SagarDrishti.
Backtracks the spill location to find estimated origin centroid and release window.
"""

import math
from typing import Dict, Any, List, Tuple, Optional
import numpy as np
import pandas as pd

def hindcast_origin(
    observed_particles: np.ndarray,
    currents: Dict[str, Any],
    wind: Dict[str, Any],
    waves: Optional[Dict[str, Any]] = None,
    observation_time_str: str = "2026-08-27T10:30:00Z",
    age_range: Tuple[float, float] = (5.0, 7.0),
    wind_drift_factor: float = 0.03,
    time_step_minutes: int = 15
) -> Dict[str, Any]:
    """
    Backtracks particles using negated velocity vectors (reverse time integration).
    
    Args:
        observed_particles: numpy.ndarray of shape (n_particles, 2)
        currents: dict containing currents data
        wind: dict containing wind data
        waves: optional waves data
        observation_time_str: ISO string of the satellite image acquisition time
        age_range: Tuple of (age_low, age_high) in hours
        wind_drift_factor: standard 3% wind drift factor
        time_step_minutes: integration timestep in minutes
        
    Returns:
        Dict containing:
            - 'estimated_origin': Tuple[float, float] (lat, lon)
            - 'origin_uncertainty_km': float (particle cloud spread)
            - 'release_window': Tuple[pd.Timestamp, pd.Timestamp]
            - 'hindcast_track': List[Tuple[float, float]] (trajectory of centroid)
    """
    if observed_particles.size == 0:
        return {
            "estimated_origin": (18.43, 70.82),
            "origin_uncertainty_km": 5.0,
            "release_window": (pd.Timestamp(observation_time_str), pd.Timestamp(observation_time_str)),
            "hindcast_track": []
        }
        
    obs_time = _make_tz_naive_scalar(observation_time_str) or pd.Timestamp("2026-08-27T10:30:00Z")
    age_low, age_high = age_range
    mean_age = (age_low + age_high) / 2.0
    
    # Release window calculations
    start_release = obs_time - pd.Timedelta(hours=age_high)
    end_release = obs_time - pd.Timedelta(hours=age_low)
    
    current_particles = observed_particles.copy()
    dt_seconds = time_step_minutes * 60.0
    total_steps = int(age_high * 60 / time_step_minutes)
    
    sim_time = obs_time
    centroid_track = []
    
    # Store initial centroid
    centroid_track.append(tuple(current_particles.mean(axis=0)))
    
    # We step BACKWARDS in time
    for step in range(1, total_steps + 1):
        sim_time -= pd.Timedelta(minutes=time_step_minutes)
        
        c_idx = _find_closest_time_idx(currents["timestamp"], sim_time)
        w_idx = _find_closest_time_idx(wind["timestamp"], sim_time)
        
        u_c_field = currents["u_current"]
        v_c_field = currents["v_current"]
        u_w_field = wind["u_wind"]
        v_w_field = wind["v_wind"]
        
        c_lat_grid = currents.get("lat_grid", np.array([0.0]))
        c_lon_grid = currents.get("lon_grid", np.array([0.0]))
        w_lat_grid = wind.get("lat_grid", np.array([0.0]))
        w_lon_grid = wind.get("lon_grid", np.array([0.0]))
        
        u_c_t = u_c_field[c_idx] if hasattr(u_c_field, "__len__") else u_c_field
        v_c_t = v_c_field[c_idx] if hasattr(v_c_field, "__len__") else v_c_field
        u_w_t = u_w_field[w_idx] if hasattr(u_w_field, "__len__") else u_w_field
        v_w_t = v_w_field[w_idx] if hasattr(v_w_field, "__len__") else v_w_field
        
        for i in range(len(current_particles)):
            lat, lon = current_particles[i]
            
            # Simple spatial nearest-neighbor
            if u_c_t.ndim >= 2 and len(c_lat_grid) > 1 and len(c_lon_grid) > 1:
                lat_i = np.argmin(np.abs(c_lat_grid - lat))
                lon_i = np.argmin(np.abs(c_lon_grid - lon))
                u_c = u_c_t[lat_i, lon_i]
                v_c = v_c_t[lat_i, lon_i]
            else:
                u_c = u_c_t.flatten()[0] if hasattr(u_c_t, "flatten") else float(u_c_t)
                v_c = v_c_t.flatten()[0] if hasattr(v_c_t, "flatten") else float(v_c_t)
                
            if u_w_t.ndim >= 2 and len(w_lat_grid) > 1 and len(w_lon_grid) > 1:
                lat_i = np.argmin(np.abs(w_lat_grid - lat))
                lon_i = np.argmin(np.abs(w_lon_grid - lon))
                u_w = u_w_t[lat_i, lon_i]
                v_w = v_w_t[lat_i, lon_i]
            else:
                u_w = u_w_t.flatten()[0] if hasattr(u_w_t, "flatten") else float(u_w_t)
                v_w = v_w_t.flatten()[0] if hasattr(v_w_t, "flatten") else float(v_w_t)
                
            # NEGATED velocity vectors for backward tracking
            v_x = -(u_c + wind_drift_factor * u_w)
            v_y = -(v_c + wind_drift_factor * v_w)
            
            dy_deg = (v_y * dt_seconds) / 111000.0
            dx_deg = (v_x * dt_seconds) / (111000.0 * math.cos(math.radians(lat)))
            
            current_particles[i, 0] = lat + dy_deg
            current_particles[i, 1] = lon + dx_deg
            
        current_centroid = current_particles.mean(axis=0)
        centroid_track.append(tuple(current_centroid))
        
        # Check if we reached the mean age mark
        elapsed_hours = (step * time_step_minutes) / 60.0
        if abs(elapsed_hours - mean_age) < (time_step_minutes / 120.0):
            # Record origin details at mean age
            origin_lat, origin_lon = current_centroid
            
            # Compute spread/standard deviation of particles
            std_lat = current_particles[:, 0].std()
            std_lon = current_particles[:, 1].std()
            
            # Convert degrees spread to km
            dy_km = std_lat * 110.574
            dx_km = std_lon * 111.320 * math.cos(math.radians(origin_lat))
            spread_km = math.sqrt(dx_km**2 + dy_km**2)
            
            # Ensure sensible bounds on uncertainty
            origin_uncertainty = max(1.5, spread_km + 0.5 * mean_age)
            
            # Return values at the mean age
            return {
                "estimated_origin": (float(origin_lat), float(origin_lon)),
                "origin_uncertainty_km": float(origin_uncertainty),
                "release_window": (start_release, end_release),
                "hindcast_track": centroid_track
            }
            
    # Final fallback if mean age wasn't hit exactly
    final_centroid = current_particles.mean(axis=0)
    std_lat = current_particles[:, 0].std()
    std_lon = current_particles[:, 1].std()
    dy_km = std_lat * 110.574
    dx_km = std_lon * 111.320 * math.cos(math.radians(final_centroid[0]))
    spread_km = math.sqrt(dx_km**2 + dy_km**2)
    origin_uncertainty = max(1.5, spread_km + 0.5 * mean_age)
    
    return {
        "estimated_origin": (float(final_centroid[0]), float(final_centroid[1])),
        "origin_uncertainty_km": float(origin_uncertainty),
        "release_window": (start_release, end_release),
        "hindcast_track": centroid_track
    }

def _make_tz_naive_scalar(x: Any) -> Any:
    """Helper to safely make a scalar timestamp or string tz-naive without AttributeError."""
    if x is None:
        return None
    try:
        ts = pd.Timestamp(x)
        if getattr(ts, "tz", None) is not None:
            return ts.tz_localize(None)
        return ts
    except Exception:
        return x

def _make_tz_naive_series(timestamps: Any) -> Any:
    """Helper to safely make timestamp series/index tz-naive without AttributeError."""
    try:
        times = pd.to_datetime(timestamps)
        if isinstance(times, pd.Series):
            if hasattr(times, "dt") and getattr(times.dt, "tz", None) is not None:
                return times.dt.tz_localize(None)
            return times
        elif isinstance(times, pd.DatetimeIndex):
            if getattr(times, "tz", None) is not None:
                return times.tz_localize(None)
            return times
        elif getattr(times, "tz", None) is not None:
            return times.tz_localize(None)
        return times
    except Exception:
        return timestamps

def _find_closest_time_idx(timestamps: Any, target_time: Any) -> int:
    """Finds the index of the closest timestamp in the series."""
    t_time = _make_tz_naive_scalar(target_time)
    times = _make_tz_naive_series(timestamps)
    try:
        diffs = np.abs(times - t_time)
        return int(np.argmin(diffs))
    except Exception:
        return 0
