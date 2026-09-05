"""
Forward Simulation module for SagarDrishti.
Predicts future slick movement (forecasting) using Euler advection.
"""

import math
from typing import Dict, Any, List, Tuple, Optional
import numpy as np
import pandas as pd

def simulate_forward(
    particles: np.ndarray,
    currents: Dict[str, Any],
    wind: Dict[str, Any],
    waves: Optional[Dict[str, Any]] = None,
    hours: Tuple[int, ...] = (1, 3, 6, 12),
    wind_drift_factor: float = 0.03,
    time_step_minutes: int = 15
) -> Dict[int, np.ndarray]:
    """
    Simulates the forward drift of particles over time.
    
    Args:
        particles: numpy.ndarray of shape (n_particles, 2) containing (lat, lon)
        currents: dict with 'timestamp', 'u_current', 'v_current', 'lat_grid', 'lon_grid'
        wind: dict with 'timestamp', 'u_wind', 'v_wind', 'lat_grid', 'lon_grid'
        waves: optional dict with wave heights
        hours: tuple of hour marks to record particle positions (e.g. 1, 3, 6, 12)
        wind_drift_factor: standard 3% drift factor for wind
        time_step_minutes: integration timestep in minutes
        
    Returns:
        Dict mapping hour -> array of particle positions of shape (n_particles, 2)
    """
    results = {}
    if particles.size == 0:
        return {h: particles for h in hours}
        
    current_particles = particles.copy()
    
    # Standard initial time is the first timestamp in currents/wind
    first_ts = currents["timestamp"][0] if hasattr(currents.get("timestamp"), "__getitem__") else currents.get("timestamp")
    start_time = _make_tz_naive_scalar(first_ts) or pd.Timestamp.now()
    
    dt_seconds = time_step_minutes * 60.0
    total_steps = int(max(hours) * 60 / time_step_minutes)
    
    # Store times to interpolate at each step
    sim_time = start_time
    
    for step in range(1, total_steps + 1):
        sim_time += pd.Timedelta(minutes=time_step_minutes)
        
        # 1. Find indices in currents/wind for the current simulation time
        c_idx = _find_closest_time_idx(currents["timestamp"], sim_time)
        w_idx = _find_closest_time_idx(wind["timestamp"], sim_time)
        
        # 2. Compute drift velocity (in m/s) for each particle
        # For simplicity, extract representative values at current index (can handle grid or scalar)
        # If grid, we sample nearest point, otherwise use the single series value
        u_c_field = currents["u_current"]
        v_c_field = currents["v_current"]
        u_w_field = wind["u_wind"]
        v_w_field = wind["v_wind"]
        
        # Grid sizes
        c_lat_grid = currents.get("lat_grid", np.array([0.0]))
        c_lon_grid = currents.get("lon_grid", np.array([0.0]))
        w_lat_grid = wind.get("lat_grid", np.array([0.0]))
        w_lon_grid = wind.get("lon_grid", np.array([0.0]))
        
        # Pre-extract slice for temporal speed
        u_c_t = u_c_field[c_idx] if hasattr(u_c_field, "__len__") else u_c_field
        v_c_t = v_c_field[c_idx] if hasattr(v_c_field, "__len__") else v_c_field
        u_w_t = u_w_field[w_idx] if hasattr(u_w_field, "__len__") else u_w_field
        v_w_t = v_w_field[w_idx] if hasattr(v_w_field, "__len__") else v_w_field
        
        # Advect each particle
        for i in range(len(current_particles)):
            lat, lon = current_particles[i]
            
            # Simple nearest-neighbor spatial interpolation if grids are actually spatial
            if u_c_t.ndim >= 2 and len(c_lat_grid) > 1 and len(c_lon_grid) > 1:
                lat_i = np.argmin(np.abs(c_lat_grid - lat))
                lon_i = np.argmin(np.abs(c_lon_grid - lon))
                u_c = u_c_t[lat_i, lon_i]
                v_c = v_c_t[lat_i, lon_i]
            else:
                # If scalar or 1D array
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
                
            # Compute total velocity: current + 3% wind
            v_x = u_c + wind_drift_factor * u_w  # Eastward
            v_y = v_c + wind_drift_factor * v_w  # Northward
            
            # Update coordinate position
            dy_deg = (v_y * dt_seconds) / 111000.0
            dx_deg = (v_x * dt_seconds) / (111000.0 * math.cos(math.radians(lat)))
            
            current_particles[i, 0] = lat + dy_deg
            current_particles[i, 1] = lon + dx_deg
            
        # Record at requested hour marks
        hour_elapsed = (step * time_step_minutes) / 60.0
        for h in hours:
            if abs(hour_elapsed - h) < 1e-4 and h not in results:
                results[h] = current_particles.copy()
                
    # Fill in any missing keys just in case
    for h in hours:
        if h not in results:
            results[h] = current_particles.copy()
            
    return results

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
