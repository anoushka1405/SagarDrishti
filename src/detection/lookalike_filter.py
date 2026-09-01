"""
Lookalike Filter module for SagarDrishti.
Distinguishes real oil spills from lookalikes (calm water zones, shadows).
"""

from typing import Dict, Any

def classify_dark_region(features: Dict[str, Any]) -> bool:
    """
    Classify if a dark region is a real oil spill or a lookalike.
    
    Rule-based heuristic fallback:
    - If wind speed is very low (< 3.0 m/s), oil-like lookalikes occur due to lack of waves.
    - If wind speed is extremely high (> 12.0 m/s), oil spills disperse rapidly, so detection is unlikely.
    - Spills are usually elongated/irregular (compactness < 0.8), whereas circular blobs or very thin lines might be lookalikes.
    
    Args:
        features: Dictionary containing:
            - 'compactness': shape compactness (0 to 1, where 1 is perfect circle)
            - 'wind_speed': wind speed in m/s
            - 'area_km2': area of the spill in km²
            - 'distance_to_coast_km': distance to coast in km (optional)
            
    Returns:
        True if it is likely an oil spill, False if it is a lookalike
    """
    wind_speed = features.get("wind_speed", 5.0)
    compactness = features.get("compactness", 0.5)
    area = features.get("area_km2", 1.0)
    
    # 1. Wind speed rule
    if wind_speed < 3.0:
        # Low wind causes lookalikes (calm sea mimics low backscatter)
        return False
    if wind_speed > 12.0:
        # High wind disperses slicks
        return False
        
    # 2. Shape rule
    # Natural oil spills spread in elongated shapes or plumes (low compactness).
    # Perfectly round shapes (compactness > 0.85) are often natural biological slicks or wind shadows.
    # Extremely thin/fragmented blobs with area < 0.15 km2 might be sensor noise.
    if compactness > 0.85 and area < 0.5:
        return False
        
    if area < 0.1:
        return False
        
    return True
