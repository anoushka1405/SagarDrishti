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
import pandas as pd
from typing import Optional, List, Dict, Any
from pydantic import BaseModel

from fastapi import FastAPI, HTTPException, Query
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse, StreamingResponse
from fastapi.staticfiles import StaticFiles

# Ensure workspace root is in sys.path
WORKSPACE_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
if WORKSPACE_ROOT not in sys.path:
    sys.path.append(WORKSPACE_ROOT)

from src.pipeline.run_pipeline import run as run_pipeline
from src.scoring.proactive_risk import run_proactive_watchlist
from src.data.synthetic_ais import generate_synthetic_vessels
from src.drift.forward_simulation import simulate_forward
from src.drift.backward_hindcast import hindcast_origin
from shapely.geometry import Polygon

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
    """Simulates drift using real forward_simulation + backward_hindcast physics modules."""
    center_lat, center_lon = 18.43, 70.82
    np.random.seed(42)

    # Build a small spill polygon around center to initialize particles
    poly = Polygon([
        (center_lon - 0.015, center_lat - 0.010),
        (center_lon + 0.015, center_lat - 0.010),
        (center_lon + 0.015, center_lat + 0.010),
        (center_lon - 0.015, center_lat + 0.010),
    ])
    from src.drift.particle_model import initialize_particles
    particles = initialize_particles(poly, req.n_particles)

    # Mock environmental data with timestamps spanning the simulation window
    max_hr = max(req.forecast_hours) if req.forecast_hours else 12
    timestamps = pd.date_range("2026-08-27T00:00:00", periods=max_hr * 4 + 1, freq="15min")

    currents = {
        "timestamp": timestamps,
        "u_current": np.full(len(timestamps), 0.15),
        "v_current": np.full(len(timestamps), 0.08),
        "lat_grid": np.array([center_lat]),
        "lon_grid": np.array([center_lon]),
    }
    wind = {
        "timestamp": timestamps,
        "u_wind": np.full(len(timestamps), 5.0),
        "v_wind": np.full(len(timestamps), 3.0),
        "lat_grid": np.array([center_lat]),
        "lon_grid": np.array([center_lon]),
    }

    # Forward forecast via real physics engine
    forecast_raw = simulate_forward(
        particles, currents, wind,
        hours=tuple(req.forecast_hours),
        wind_drift_factor=req.wind_drift_factor,
    )
    forecast_tracks = {str(hr): pos.tolist() for hr, pos in forecast_raw.items()}

    # Backward hindcast: use the +1h forecast as the "observed" slick
    obs_hour = req.forecast_hours[0] if req.forecast_hours else 1
    observed_particles = forecast_raw.get(obs_hour, particles)
    hindcast_result = hindcast_origin(
        observed_particles, currents, wind,
        observation_time_str="2026-08-27T01:00:00Z",
        age_range=(3.0, 8.0),
        wind_drift_factor=req.wind_drift_factor,
    )

    origin_lat, origin_lon = hindcast_result["estimated_origin"]
    hindcast_track = [list(pt) for pt in hindcast_result["hindcast_track"]]

    return {
        "center": [center_lat, center_lon],
        "wind_drift_factor": req.wind_drift_factor,
        "n_particles": req.n_particles,
        "forecast_tracks": forecast_tracks,
        "hindcast": {
            "estimated_origin": [origin_lat, origin_lon],
            "origin_uncertainty_km": hindcast_result["origin_uncertainty_km"],
            "release_window": [
                str(hindcast_result["release_window"][0]),
                str(hindcast_result["release_window"][1]),
            ],
            "track": hindcast_track,
        },
    }

@app.post("/api/export_report")
def export_report(req: AnalyzeRequest):
    """Generates a forensic PDF report from pipeline results."""
    try:
        from fpdf import FPDF

        full_path = req.image_path
        if full_path and not os.path.isabs(full_path):
            full_path = os.path.join(WORKSPACE_ROOT, req.image_path)

        result = run_pipeline(full_path, mock_mode=req.mock_mode)

        pdf = FPDF()
        pdf.set_auto_page_break(auto=True, margin=15)
        pdf.add_page()

        # Title
        pdf.set_font("Helvetica", "B", 18)
        pdf.cell(0, 12, "SagarDrishti Forensic Report", new_x="LMARGIN", new_y="NEXT", align="C")
        pdf.set_font("Helvetica", "", 10)
        pdf.set_text_color(120, 120, 120)
        pdf.cell(0, 6, "Automated Satellite Oil Spill Detection & Vessel Attribution", new_x="LMARGIN", new_y="NEXT", align="C")
        pdf.ln(4)

        pdf.set_draw_color(200, 200, 200)
        pdf.line(10, pdf.get_y(), 200, pdf.get_y())
        pdf.ln(6)

        pdf.set_text_color(0, 0, 0)

        # Section: Detection Summary
        pdf.set_font("Helvetica", "B", 13)
        pdf.cell(0, 8, "1. Detection Summary", new_x="LMARGIN", new_y="NEXT")
        pdf.set_font("Helvetica", "", 11)
        rows = [
            ("Spill Detected", "Yes" if result.get("spill_detected") else "No"),
            ("Confidence", f"{result.get('confidence', 0)}%"),
            ("Surface Area", f"{result.get('area_km2', 0)} km2"),
            ("Perimeter", f"{result.get('perimeter_km', 0)} km"),
        ]
        for label, val in rows:
            pdf.set_font("Helvetica", "B", 11)
            pdf.cell(55, 7, label + ":", new_x="END")
            pdf.set_font("Helvetica", "", 11)
            pdf.cell(0, 7, val, new_x="LMARGIN", new_y="NEXT")
        pdf.ln(4)

        # Section: Origin & Drift
        pdf.set_font("Helvetica", "B", 13)
        pdf.cell(0, 8, "2. Origin & Drift Analysis", new_x="LMARGIN", new_y="NEXT")
        pdf.set_font("Helvetica", "", 11)
        origin = result.get("estimated_origin", [0, 0])
        origin_rows = [
            ("Estimated Origin", f"{origin[0]:.4f} N, {origin[1]:.4f} E"),
            ("Uncertainty Radius", f"+/- {result.get('origin_uncertainty_km', 0)} km"),
            ("Estimated Age", f"{result.get('age_low', 0)} - {result.get('age_high', 0)} hours"),
            ("Age Confidence", f"{result.get('age_confidence', 0)}%"),
        ]
        for label, val in origin_rows:
            pdf.set_font("Helvetica", "B", 11)
            pdf.cell(55, 7, label + ":", new_x="END")
            pdf.set_font("Helvetica", "", 11)
            pdf.cell(0, 7, val, new_x="LMARGIN", new_y="NEXT")

        release_window = result.get("release_window")
        if release_window:
            pdf.set_font("Helvetica", "B", 11)
            pdf.cell(55, 7, "Release Window:", new_x="END")
            pdf.set_font("Helvetica", "", 11)
            pdf.cell(0, 7, f"{release_window[0]} to {release_window[1]}", new_x="LMARGIN", new_y="NEXT")
        pdf.ln(4)

        # Section: Suspect Vessel Rankings
        vessels = result.get("ranked_vessels", [])
        if vessels:
            pdf.set_font("Helvetica", "B", 13)
            pdf.cell(0, 8, "3. Suspect Vessel Rankings", new_x="LMARGIN", new_y="NEXT")
            pdf.set_font("Helvetica", "", 10)

            for i, v in enumerate(vessels[:5], 1):
                pdf.set_font("Helvetica", "B", 11)
                score = v.get("attribution_score", 0)
                pdf.cell(0, 7,
                    f"#{i}  {v.get('mmsi', 'N/A')}  ({v.get('vessel_type', 'Unknown')})  Score: {score}/100  [{v.get('confidence_level', '')}]",
                    new_x="LMARGIN", new_y="NEXT")
                pdf.set_font("Helvetica", "", 10)
                pdf.cell(0, 6,
                    f"    Closest Approach: {v.get('closest_distance_km', 0)} km  |  Time Offset: {v.get('time_delta_hours', 0)} hrs",
                    new_x="LMARGIN", new_y="NEXT")
                for ev in v.get("evidence", [])[:3]:
                    pdf.set_x(15)
                    pdf.cell(0, 5, f"  - {ev}", new_x="LMARGIN", new_y="NEXT")
                pdf.ln(2)
        else:
            pdf.set_font("Helvetica", "B", 13)
            pdf.cell(0, 8, "3. Suspect Vessel Rankings", new_x="LMARGIN", new_y="NEXT")
            pdf.set_font("Helvetica", "", 11)
            pdf.cell(0, 7, "No suspect vessels identified.", new_x="LMARGIN", new_y="NEXT")

        # Footer
        pdf.ln(6)
        pdf.set_draw_color(200, 200, 200)
        pdf.line(10, pdf.get_y(), 200, pdf.get_y())
        pdf.ln(3)
        pdf.set_font("Helvetica", "I", 9)
        pdf.set_text_color(140, 140, 140)
        pdf.cell(0, 5, "Generated by SagarDrishti Marine Intelligence Platform", new_x="LMARGIN", new_y="NEXT", align="C")

        pdf_buf = io.BytesIO()
        pdf.output(pdf_buf)
        pdf_buf.seek(0)

        return StreamingResponse(
            pdf_buf,
            media_type="application/pdf",
            headers={"Content-Disposition": "attachment; filename=sagardrishti_report.pdf"},
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Report generation error: {str(e)}")

# Mount compiled React frontend static files if built (for Render deployment)
FRONTEND_DIST = os.path.join(WORKSPACE_ROOT, "frontend", "dist")
if os.path.exists(FRONTEND_DIST):
    app.mount("/", StaticFiles(directory=FRONTEND_DIST, html=True), name="frontend")

if __name__ == "__main__":
    import uvicorn
    uvicorn.run("src.api.main:app", host="0.0.0.0", port=8000, reload=True)
