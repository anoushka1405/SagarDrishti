"""
Pytest smoke and sanity tests for the SagarDrishti pipeline.
Ensures that all modules integrate and run without crashing.
"""

import pytest
import numpy as np
import pandas as pd

from src.pipeline.run_pipeline import run as run_pipeline
from src.detection.lookalike_filter import classify_dark_region
from src.age_estimation.age_model import estimate_spill_age
from src.scoring.proactive_risk import score_proactive_risk

def test_pipeline_mock_run():
    """Verify that running the pipeline in mock mode completes successfully."""
    result = run_pipeline("mock_image.tif", mock_mode=True)
    
    assert result is not None
    assert isinstance(result, dict)
    assert "spill_detected" in result
    assert result["spill_detected"] is True
    
    # Check fields are present and valid
    assert "confidence" in result
    assert "area_km2" in result
    assert "centroid" in result
    assert "estimated_origin" in result
    assert "ranked_vessels" in result
    
    # Check candidates list
    vessels = result["ranked_vessels"]
    assert len(vessels) > 0
    assert "mmsi" in vessels[0]
    assert "attribution_score" in vessels[0]
    assert "evidence" in vessels[0]

def test_lookalike_filter():
    """Verify the lookalike filter detects false positives under extreme wind or shape conditions."""
    # Standard real spill features
    spill_features = {"compactness": 0.4, "wind_speed": 6.0, "area_km2": 2.5}
    assert classify_dark_region(spill_features) is True
    
    # Extremely low wind speed should trigger lookalike filter (False classification)
    calm_wind_features = {"compactness": 0.4, "wind_speed": 1.5, "area_km2": 2.5}
    assert classify_dark_region(calm_wind_features) is False
    
    # Circular blob of small area under normal wind should be filtered as lookalike
    circular_features = {"compactness": 0.9, "wind_speed": 6.0, "area_km2": 0.2}
    assert classify_dark_region(circular_features) is False

def test_spill_age_estimation():
    """Verify the physics-informed age estimation returns valid output ranges."""
    geom = {"area_km2": 15.0, "compactness": 0.3, "perimeter_km": 30.0}
    wind = {"u_wind": np.ones((1, 1)) * 4.0, "v_wind": np.ones((1, 1)) * 3.0} # 5 m/s wind
    currents = {"u_current": np.ones((1, 1)) * 0.1, "v_current": np.ones((1, 1)) * 0.1}
    
    age_low, age_high, confidence = estimate_spill_age(geom, wind, currents)
    
    assert age_low > 0.0
    assert age_high >= age_low
    assert 0.0 <= confidence <= 1.0

def test_proactive_risk_scoring():
    """Verify proactive surveillance watchlist scoring correctly triggers alarms."""
    # Trajectory with severe anomalies (sudden stop and signal gap)
    suspicious_trajectory = [
        (10.0, 72.0, "2026-08-29T10:00:00Z", 15.0, 45.0),
        (10.1, 72.1, "2026-08-29T10:15:00Z", 0.2, 135.0),  # sudden stop
        # 1-hour AIS GAP, with speed 8.0 knots to keep median > 4.0 knots
        (10.2, 72.2, "2026-08-29T11:15:00Z", 8.0, 45.0)
    ]
    zone = {"name": "Laccadive Sanctuary", "lat": 10.1, "lon": 72.1, "radius_km": 20.0}
    
    alert = score_proactive_risk(suspicious_trajectory, zone)
    
    assert alert["risk_score"] >= 50.0
    assert alert["watchlist"] is True
    assert len(alert["evidence"]) > 0
    assert any("Unexpected stop" in ev for ev in alert["evidence"]) or any("signal gap" in ev for ev in alert["evidence"]) or any("gap" in ev.lower() for ev in alert["evidence"])
