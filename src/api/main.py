"""
FastAPI Backend Server for SagarDrishti.
Serves satellite datasets, SAR image previews, pipeline analysis, proactive watchlist alerts, and drift simulations.
"""

import os
import sys
import glob
import io
import base64
import numpy as np
from typing import Optional, List, Dict, Any
from pydantic import BaseModel

from fastapi import FastAPI, HTTPException, Query
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

# Ensure workspace root is in sys.path
WORKSPACE_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
if WORKSPACE_ROOT not in sys.path:
    sys.path.append(WORKSPACE_ROOT)

from src.pipeline.run_pipeline import run as run_pipeline
from src.scoring.proactive_risk import run_proactive_watchlist
from src.data.synthetic_ais import generate_synthetic_vessels

app = FastAPI(
    title="SagarDrishti Marine Intelligence API",
    description="Automated Satellite Oil Spill Detection, Drift Modeling & AIS Vessel Attribution API",
    version="2.0.0"
)

# CORS middleware for React frontend communication
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

SENSITIVE_ZONES = [
    {"id": "zone_1", "name": "Laccadive Marine Sanctuary", "lat": 10.5, "lon": 72.5, "radius_km": 30.0},
    {"id": "zone_2", "name": "Mumbai Port Anchorage Zone", "lat": 18.9, "lon": 72.8, "radius_km": 15.0},
    {"id": "zone_3", "name": "Gulf of Kutch Eco-Sensitive Zone", "lat": 22.5, "lon": 69.5, "radius_km": 40.0},
    {"id": "zone_4", "name": "Malvan Marine Sanctuary", "lat": 16.05, "lon": 73.45, "radius_km": 20.0}
]

class AnalyzeRequest(BaseModel):
    image_path: Optional[str] = "data/raw/sentinel1_sample.tif"
    mock_mode: bool = False

class DriftSimRequest(BaseModel):
    n_particles: int = 500
    wind_drift_factor: float = 0.03
    hindcast_hours: List[int] = [1, 3, 6]
    forecast_hours: List[int] = [1, 3, 6, 12]

@app.get("/api/health")
def health_check():
    return {"status": "ok", "app": "SagarDrishti FastAPI Server", "version": "2.0.0"}

@app.get("/api/dataset/categories")
def get_dataset_categories():
    """Returns dataset categories and available TIFF images."""
    base_dir = os.path.join(WORKSPACE_ROOT, "data", "raw", "SARSatelite", "Images")
    categories = {}
    
    if os.path.exists(base_dir):
        for cat in ["Oil", "Lookalike", "No oil"]:
            cat_dir = os.path.join(base_dir, cat)
            if os.path.exists(cat_dir):
                tif_files = sorted([os.path.basename(f) for f in glob.glob(os.path.join(cat_dir, "*.tif"))])
                categories[cat] = tif_files
            else:
                categories[cat] = []
    else:
        categories = {"Oil": [], "Lookalike": [], "No oil": []}
        
    return {
        "categories": categories,
        "total_images": sum(len(v) for v in categories.values()),
        "has_real_dataset": any(len(v) > 0 for v in categories.values())
    }

def convert_raster_to_png_base64(tif_path: str) -> Optional[str]:
    """Helper to convert a TIFF band into a base64 encoded PNG data URL."""
    try:
        import rasterio
        from PIL import Image
        
        full_path = os.path.join(WORKSPACE_ROOT, tif_path) if not os.path.isabs(tif_path) else tif_path
        if not os.path.exists(full_path):
            return None
            
        with rasterio.open(full_path) as src:
            band = src.read(1)
            
        # Normalize raster band values to 0-255
        clipped = np.clip(band, -35.0, 5.0) if np.min(band) < 0 else band
        b_min, b_max = np.min(clipped), np.max(clipped)
        if b_max > b_min:
            norm = ((clipped - b_min) / (b_max - b_min) * 255.0).astype(np.uint8)
        else:
            norm = np.zeros_like(clipped, dtype=np.uint8)
            
        img = Image.fromarray(norm)
        # Resize to manageable preview size if too large
        img.thumbnail((600, 600))
        
        buf = io.BytesIO()
        img.save(buf, format="PNG")
        encoded = base64.b64encode(buf.getvalue()).decode("utf-8")
        return f"data:image/png;base64,{encoded}"
    except Exception as e:
        print(f"Error rendering raster PNG preview for {tif_path}: {e}")
        return None

@app.get("/api/sar_preview")
def get_sar_preview(image_path: str = Query("data/raw/sentinel1_sample.tif")):
    """Generates preview PNG base64 strings for raw SAR image and ground truth mask."""
    sar_b64 = convert_raster_to_png_base64(image_path)
    
    # Try locating matching mask
    mask_b64 = None
    mask_path = ""
    norm_p = os.path.normpath(image_path)
    parts = norm_p.split(os.sep)
    if "Images" in parts:
        idx = parts.index("Images")
        parts[idx] = "Mask"
        filename = parts[-1]
        name_part, ext_part = os.path.splitext(filename)
        parts[-1] = f"{name_part}_segmentation{ext_part}"
        mask_path = os.sep.join(parts)
        mask_b64 = convert_raster_to_png_base64(mask_path)
        
    return {
        "image_path": image_path,
        "sar_image_base64": sar_b64,
        "mask_image_base64": mask_b64,
        "has_mask": mask_b64 is not None
    }

@app.post("/api/analyze")
def analyze_satellite_pass(req: AnalyzeRequest):
    """Runs the full SagarDrishti oil spill detection, drift, and AIS attribution pipeline."""
    try:
        full_path = req.image_path
        if full_path and not os.path.isabs(full_path):
            full_path = os.path.join(WORKSPACE_ROOT, req.image_path)
            
        result = run_pipeline(full_path, mock_mode=req.mock_mode)
        return result
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Pipeline execution error: {str(e)}")

@app.get("/api/proactive_watchlist")
def get_proactive_watchlist():
    """Returns active surveillance alerts inside protected marine zones."""
    v1_mmsi = "SYN-998822101"
    v1_type = "Crude Oil Tanker"
    v1_lat, v1_lon = 10.51, 72.52
    v1_traj = [
        (10.3, 72.3, "2026-08-29T18:00:00Z", 12.0, 45.0),
        (10.4, 72.4, "2026-08-29T18:30:00Z", 11.5, 45.0),
        (10.51, 72.52, "2026-08-29T19:00:00Z", 0.5, 135.0),
        (10.53, 72.54, "2026-08-29T20:15:00Z", 4.0, 45.0)
    ]
    
    v2_mmsi = "SYN-112233445"
    v2_type = "Container Ship"
    v2_lat, v2_lon = 10.45, 72.38
    v2_traj = [
        (10.38, 72.31, "2026-08-29T18:00:00Z", 14.5, 30.0),
        (10.42, 72.35, "2026-08-29T18:30:00Z", 14.2, 30.0),
        (10.45, 72.38, "2026-08-29T19:00:00Z", 14.6, 30.0)
    ]
    
    v3_mmsi = "SYN-774411993"
    v3_type = "Chemical Tanker"
    v3_lat, v3_lon = 18.92, 72.82
    v3_traj = [
        (18.85, 72.75, "2026-08-29T18:00:00Z", 10.0, 60.0),
        (18.92, 72.82, "2026-08-29T18:45:00Z", 0.2, 180.0),
        (18.94, 72.85, "2026-08-29T20:00:00Z", 3.5, 60.0)
    ]
    
    vessel_positions = {
        v1_mmsi: (v1_lat, v1_lon),
        v2_mmsi: (v2_lat, v2_lon),
        v3_mmsi: (v3_lat, v3_lon)
    }
    trajectories = {
        v1_mmsi: v1_traj,
        v2_mmsi: v2_traj,
        v3_mmsi: v3_traj
    }
    
    watchlist = run_proactive_watchlist(vessel_positions, trajectories, SENSITIVE_ZONES)
    
    # Enrich watchlist entries with vessel details
    details_map = {
        v1_mmsi: {"vessel_type": v1_type, "speed_knots": 0.5, "heading": 135.0},
        v2_mmsi: {"vessel_type": v2_type, "speed_knots": 14.6, "heading": 30.0},
        v3_mmsi: {"vessel_type": v3_type, "speed_knots": 0.2, "heading": 180.0}
    }
    
    for item in watchlist:
        mmsi = item["mmsi"]
        if mmsi in details_map:
            item.update(details_map[mmsi])
            
    return {
        "sensitive_zones": SENSITIVE_ZONES,
        "watchlist": watchlist
    }

@app.post("/api/simulate_drift")
def simulate_drift(req: DriftSimRequest):
    """Simulates drift particle spread under custom environmental parameters."""
    # Generate synthetic particle dispersion demo
    center_lat, center_lon = 18.43, 70.82
    np.random.seed(42)
    
    # Generate particles around origin
    n = req.n_particles
    lats = np.random.normal(center_lat, 0.02, n)
    lons = np.random.normal(center_lon, 0.02, n)
    
    # Drift vectors: current + wind_drift_factor * wind
    u_curr, v_curr = 0.15, 0.08
    u_wind, v_wind = 5.0, 3.0
    
    v_drift_u = u_curr + req.wind_drift_factor * u_wind
    v_drift_v = v_curr + req.wind_drift_factor * v_wind
    
    # Degree offsets per hour (~111km per degree)
    lat_deg_per_hr = (v_drift_v * 3600.0) / 111000.0
    lon_deg_per_hr = (v_drift_u * 3600.0) / (111000.0 * np.cos(np.radians(center_lat)))
    
    forecast = {}
    for hr in req.forecast_hours:
        hr_lats = lats + lat_deg_per_hr * hr + np.random.normal(0, 0.005 * np.sqrt(hr), n)
        hr_lons = lons + lon_deg_per_hr * hr + np.random.normal(0, 0.005 * np.sqrt(hr), n)
        forecast[str(hr)] = np.column_stack((hr_lats, hr_lons)).tolist()
        
    return {
        "center": [center_lat, center_lon],
        "wind_drift_factor": req.wind_drift_factor,
        "n_particles": n,
        "forecast_tracks": forecast
    }

if __name__ == "__main__":
    import uvicorn
    uvicorn.run("src.api.main:app", host="0.0.0.0", port=8000, reload=True)
