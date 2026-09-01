"""
Suspect Scoring module for SagarDrishti.
Computes composite Attribution Scores and generates human-readable evidence bullets.
"""

from typing import Dict, Any, List

def score_vessel(features: Dict[str, Any], weights: Dict[str, float]) -> float:
    """
    Computes a composite Attribution Score (0 to 100) based on weighted sub-scores.
    
    Sub-scores:
    1. Spatial: Proximity of closest approach to estimated origin.
    2. Temporal: Proximity in time to estimated release window.
    3. Trajectory: Interpolated track intersection with the origin.
    4. Behaviour: Speed anomaly and unexpected stops.
    5. AIS Gap: Signal silence/gap near the origin.
    6. Relevance: Cargo/Tankers have higher default relevance than fishing/pleasure boats.
    
    Args:
        features: Dictionary of extracted features:
            - 'closest_distance_km': float
            - 'time_delta_hours': float
            - 'intersects_origin': bool
            - 'speed_anomaly': float
            - 'unexpected_stop': bool
            - 'ais_gap_near_origin': bool
            - 'vessel_type': str
        weights: Dictionary of weights matching config.yaml -> scoring.weights
        
    Returns:
        Score between 0.0 and 100.0
    """
    # 1. Spatial score: closer approach -> higher score (radius = 50km)
    dist = features.get("closest_distance_km", 50.0)
    s_spatial = max(0.0, 1.0 - (dist / 50.0))
    
    # 2. Temporal score: closer time -> higher score (window = 6h)
    time_delta = abs(features.get("time_delta_hours", 6.0))
    s_temporal = max(0.0, 1.0 - (time_delta / 6.0))
    
    # 3. Trajectory intersection
    intersects = features.get("intersects_origin", False)
    s_trajectory = 1.0 if intersects else 0.0
    
    # 4. Behaviour (Speed anomaly & unexpected stops)
    speed_anom = features.get("speed_anomaly", 0.0)
    unexp_stop = features.get("unexpected_stop", False)
    s_behaviour = 0.5 * min(1.0, speed_anom) + 0.5 * (1.0 if unexp_stop else 0.0)
    
    # 5. AIS Gap near origin
    gap_near = features.get("ais_gap_near_origin", False)
    s_gap = 1.0 if gap_near else 0.0
    
    # 6. Vessel Type relevance
    v_type = features.get("vessel_type", "").lower()
    if "tanker" in v_type or "chemical" in v_type:
        s_type = 1.0
    elif "cargo" in v_type or "carrier" in v_type or "container" in v_type:
        s_type = 0.7
    elif "fishing" in v_type:
        s_type = 0.3
    else:
        s_type = 0.1
        
    # Combine sub-scores using weights
    w_spatial = weights.get("spatial", 0.30)
    w_temporal = weights.get("temporal", 0.25)
    w_trajectory = weights.get("trajectory", 0.20)
    w_behaviour = weights.get("behaviour", 0.10)
    w_gap = weights.get("ais_anomaly", 0.10)  # Maps to ais_anomaly weight in config.yaml
    w_type = weights.get("vessel_relevance", 0.05)
    
    composite_score = (
        w_spatial * s_spatial +
        w_temporal * s_temporal +
        w_trajectory * s_trajectory +
        w_behaviour * s_behaviour +
        w_gap * s_gap +
        w_type * s_type
    )
    
    # Scale to 0-100 range
    return float(min(100.0, max(0.0, composite_score * 100.0)))

def explain_score(vessel_id: str, features: Dict[str, Any]) -> List[str]:
    """
    Generates 3 to 6 evidence bullets explaining the score.
    
    Args:
        vessel_id: MMSI or vessel name
        features: Dictionary of features
        
    Returns:
        List of human-readable explanation strings
    """
    evidence = []
    
    dist = features.get("closest_distance_km", 50.0)
    if dist < 5.0:
        evidence.append(f"Passed very close to estimated origin ({dist:.1f} km)")
    elif dist < 20.0:
        evidence.append(f"Passed within proximity of estimated origin ({dist:.1f} km)")
        
    time_delta = features.get("time_delta_hours", 6.0)
    if abs(time_delta) < 1.0:
        evidence.append("Matched release window perfectly (closest approach under 1 hour offset)")
    elif abs(time_delta) < 3.0:
        evidence.append(f"Coincided with release window (time offset {abs(time_delta):.1f} hours)")
        
    if features.get("intersects_origin", False):
        evidence.append("Vessel trajectory directly intersected the probable origin area")
        
    if features.get("unexpected_stop", False):
        evidence.append("Unexpected speed drop or stop near estimated origin")
        
    if features.get("ais_gap_near_origin", False):
        evidence.append("AIS signal gap / dark period occurred near estimated origin")
        
    v_type = features.get("vessel_type", "")
    if "Tanker" in v_type:
        evidence.append(f"High-risk vessel type classification: {v_type}")
        
    if not evidence:
        evidence.append("No strong anomalous indicators observed.")
        
    return evidence
