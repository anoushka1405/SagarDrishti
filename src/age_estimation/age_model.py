"""
Physics-informed spill age estimation module for SagarDrishti.
Estimates age range of the spill based on geometry and environmental forces.
"""

import math
from typing import Tuple, Dict, Any, Union
import numpy as np

def estimate_spill_age(
    spill_geometry: Union[Dict[str, Any], Any],
    wind: Dict[str, Any],
    currents: Dict[str, Any]
) -> Tuple[float, float, float]:
    """
    Estimate the age range of the oil spill using a physics-informed model.
    
    Args:
        spill_geometry: Dictionary or object with geometric properties of the spill:
            - 'area_km2': float
            - 'compactness': float
            - 'perimeter_km': float
        wind: Weather data dictionary conforming to WEATHER_FIELDS.
        currents: Oceanographic currents data dictionary conforming to OCEAN_FIELDS.
        
    Returns:
        Tuple of (age_low_hours, age_high_hours, confidence)
    """
    # 1. Parse geometry
    if isinstance(spill_geometry, dict):
        area = spill_geometry.get("area_km2", 1.0)
        compactness = spill_geometry.get("compactness", 0.5)
        perimeter = spill_geometry.get("perimeter_km", 4.0)
    else:
        # Support dataclass
        area = getattr(spill_geometry, "area_km2", 1.0)
        compactness = getattr(spill_geometry, "compactness", 0.5)
        perimeter = getattr(spill_geometry, "perimeter_km", 4.0)

    # 2. Extract environmental velocities (in m/s)
    # Get current velocity magnitude
    u_c = currents.get("u_current", np.zeros((1, 1)))
    v_c = currents.get("v_current", np.zeros((1, 1)))
    # If array, compute mean
    mean_u_c = u_c.mean() if hasattr(u_c, "mean") else float(u_c)
    mean_v_c = v_c.mean() if hasattr(v_c, "mean") else float(v_c)
    current_speed = math.sqrt(mean_u_c**2 + mean_v_c**2)

    # Get wind velocity magnitude
    u_w = wind.get("u_wind", np.zeros((1, 1)))
    v_w = wind.get("v_wind", np.zeros((1, 1)))
    mean_u_w = u_w.mean() if hasattr(u_w, "mean") else float(u_w)
    mean_v_w = v_w.mean() if hasattr(v_w, "mean") else float(v_w)
    wind_speed = math.sqrt(mean_u_w**2 + mean_v_w**2)

    # 3. Estimate drift velocity (m/s)
    # Standard empirical rule: 100% of current + 3% of wind
    drift_speed_ms = current_speed + 0.03 * wind_speed
    # Ensure not zero to avoid division by zero
    drift_speed_ms = max(0.05, drift_speed_ms)
    
    # Convert drift speed to km/h
    drift_speed_kmh = drift_speed_ms * 3.6

    # 4. Estimate displacement/length of slick (km)
    # Compactness (0 to 1). Fresh spills are circular/compact (close to 1).
    # Aged spills are elongated/fragmented (close to 0).
    # Major dimension (length) can be estimated using area and compactness
    slick_length_km = math.sqrt(area) * (1.5 - compactness) * 2.0
    slick_length_km = max(0.1, slick_length_km)

    # 5. Calculate base age (hours)
    # The time required to drift the length of the slick
    age_hours = slick_length_km / drift_speed_kmh
    
    # Apply baseline limits (e.g. at least 1h, capped at 48h for demo)
    age_hours = max(1.0, min(48.0, age_hours))

    # 6. Widen range and compute confidence based on shape and data availability
    # High compactness -> more circular/fresh -> higher confidence, narrow range
    # Low compactness -> elongated/fragmented -> lower confidence, wide range
    uncertainty_factor = 1.8 - compactness  # ranges from 0.8 (circular) to 1.8 (fragmented)
    
    # If wind/current data is mock (velocity near zero), increase uncertainty
    data_quality_factor = 1.0
    if current_speed < 0.01 and wind_speed < 0.01:
        uncertainty_factor *= 1.5
        data_quality_factor = 0.7

    age_low = max(0.5, age_hours / (1.2 * uncertainty_factor))
    age_high = min(72.0, age_hours * (1.2 * uncertainty_factor))
    
    # Confidence score [0, 1]
    confidence = (0.5 + 0.4 * compactness) * data_quality_factor
    confidence = max(0.2, min(0.95, confidence))

    return round(age_low, 1), round(age_high, 1), round(confidence, 2)
