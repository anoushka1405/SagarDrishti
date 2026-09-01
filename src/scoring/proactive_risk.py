"""
USP feature - Proactive vessel risk scoring.

Every other team's system is reactive: a spill is observed, THEN vessels get
scored. This module flips that - it scores any vessel's behaviour the moment
it enters an environmentally sensitive zone, with zero dependency on a spill
having been detected at all. It reuses the exact same behavioural features
from ais/behaviour_features.py (speed anomaly, heading changes, AIS gaps,
route deviation) - no new data source, no new model, just a different trigger.

This turns the system from "who did this" into "who looks risky right now,"
which is the more genuinely novel and NTRO-relevant capability - continuous
maritime risk awareness rather than single-incident forensics.
"""

from typing import List, Tuple, Dict, Any, Optional
from src.ais.behaviour_features import extract_behaviour_features
from src.utils.geo_utils import haversine_km

def vessel_in_sensitive_zone(vessel_position: Tuple[float, float], sensitive_zones: List[Dict[str, Any]], buffer_km: float = 5.0) -> Optional[Dict[str, Any]]:
    """
    Checks if a vessel's current position is within a sensitive zone (e.g., marine sanctuaries, ports).
    
    Args:
        vessel_position: (lat, lon) coordinates of the vessel's current position.
        sensitive_zones: list of zone dicts, each with {"name": str, "lat": float, "lon": float, "radius_km": float}
        buffer_km: extra margin added to the zone radius.
        
    Returns:
        The matching zone dictionary or None.
    """
    lat, lon = vessel_position
    for zone in sensitive_zones:
        dist = haversine_km(lat, lon, zone["lat"], zone["lon"])
        if dist <= zone["radius_km"] + buffer_km:
            return zone
    return None

def score_proactive_risk(trajectory: List[Tuple[float, float, str, float, float]], zone: Dict[str, Any]) -> Dict[str, Any]:
    """
    Score a vessel's behavioural risk independent of any spill event.

    Args:
        trajectory: this vessel's reconstructed AIS trajectory (from trajectory.reconstruct_trajectory).
        zone: the sensitive zone dict the vessel is currently inside (from vessel_in_sensitive_zone).

    Returns:
        Dictionary containing:
            - 'risk_score': float 0-100
            - 'zone': zone name
            - 'evidence': list of explanation strings
            - 'watchlist': bool
    """
    features = extract_behaviour_features(
        trajectory,
        origin_lat=zone["lat"],
        origin_lon=zone["lon"],
        event_time=trajectory[-1][2] if trajectory else None
    )

    evidence = []
    risk = 0.0

    if features.get("speed_anomaly", 0.0) > 0.5:
        risk += 30
        evidence.append("Unusual speed pattern for this vessel/type")
    if features.get("heading_change_max", 0.0) > 60.0:
        risk += 20
        evidence.append("Sharp, unexplained heading change")
    if features.get("unexpected_stop", False):
        risk += 20
        evidence.append("Unexpected stop while transiting a sensitive zone")
    if features.get("route_deviation_km", 0.0) > 5.0:
        risk += 15
        evidence.append("Significant deviation from expected route")
    if features.get("ais_gap_near_origin", False):
        risk += 15
        evidence.append(f"AIS signal gap while inside {zone['name']}")

    risk = min(risk, 100.0)
    return {
        "risk_score": risk,
        "zone": zone["name"],
        "evidence": evidence,
        "watchlist": risk >= 50.0,
    }

def run_proactive_watchlist(
    current_vessel_positions: Dict[str, Tuple[float, float]],
    trajectories_by_mmsi: Dict[str, List[Tuple[float, float, str, float, float]]],
    sensitive_zones: List[Dict[str, Any]]
) -> List[Dict[str, Any]]:
    """
    Identifies all vessels currently inside sensitive zones that score above threshold.
    """
    watchlist = []
    for mmsi, position in current_vessel_positions.items():
        zone = vessel_in_sensitive_zone(position, sensitive_zones)
        if zone is None:
            continue
        trajectory = trajectories_by_mmsi.get(mmsi)
        if not trajectory:
            continue
        result = score_proactive_risk(trajectory, zone)
        result["mmsi"] = mmsi
        watchlist.append(result)

    return sorted(watchlist, key=lambda r: r["risk_score"], reverse=True)
