"""
Main Streamlit Application for SagarDrishti.
Interfaces with the pipeline and displays results in Forensic and Proactive tabs.
"""

import os
import sys
import streamlit as st
import pandas as pd
import numpy as np

# Ensure workspace root is in path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

# Import pipeline runner and proactive scorer
from src.pipeline.run_pipeline import run as run_pipeline
from src.scoring.proactive_risk import run_proactive_watchlist, score_proactive_risk
from src.data.synthetic_ais import generate_synthetic_vessels

# Import UI components
from dashboard.components.spill_panel import render_spill_panel
from dashboard.components.vessel_panel import render_vessel_panel
from dashboard.components.map_view import render_map_view

# Page Config
st.set_page_config(
    layout="wide",
    page_title="SagarDrishti (सागरदृष्टि) | Marine Oil Spill Attribution",
    page_icon="🌊"
)

# Custom header style
st.markdown(
    """
    <div style="background-color: #0f2b3c; border-bottom: 2px solid #26a69a; padding: 15px; border-radius: 8px; margin-bottom: 20px;">
        <h1 style="color: #ffffff; margin: 0; font-family: 'Outfit', sans-serif;">🌊 SagarDrishti (सागरदृष्टि) 🛢️</h1>
        <p style="color: #80cbc4; margin: 5px 0 0 0; font-size: 0.95rem;">
            Automated Satellite Oil Spill Detection, Drift Modeling & AIS Vessel Attribution Pipeline
        </p>
    </div>
    """,
    unsafe_allow_html=True
)

# Hardcoded Sensitive Zones for USP Proactive Watchlist
SENSITIVE_ZONES = [
    {"name": "Laccadive Marine Sanctuary", "lat": 10.5, "lon": 72.5, "radius_km": 30.0},
    {"name": "Mumbai Port Anchorage Zone", "lat": 18.9, "lon": 72.8, "radius_km": 15.0},
    {"name": "Gulf of Kutch Eco-Sensitive Zone", "lat": 22.5, "lon": 69.5, "radius_km": 40.0},
    {"name": "Malvan Marine Sanctuary", "lat": 16.05, "lon": 73.45, "radius_km": 20.0}
]

# Tabs
tab_forensic, tab_proactive = st.tabs(["🔍 Forensic Post-Spill Attribution", "📡 Proactive Surveillance Watchlist"])

# -------------------------------------------------------------
# TAB 1: Forensic Post-Spill Attribution
# -------------------------------------------------------------
with tab_forensic:
    # Sidebar control panels inside the columns
    col_left, col_mid, col_right = st.columns([1, 2.2, 1.2])
    
    with col_left:
        st.subheader("⚙️ Analysis Controls")
        
        mode = st.radio("Operation Mode", ["Load from Real Dataset (150 images)", "Run Mock Demo (Recommended)", "Load Local SAR File"])
        
        image_path = ""
        if mode == "Load from Real Dataset (150 images)":
            import glob
            category = st.selectbox("Dataset Category", ["Oil", "Lookalike", "No oil"])
            category_dir = os.path.join("data", "raw", "SARSatelite", "Images", category)
            if os.path.exists(category_dir):
                tif_files = sorted([os.path.basename(f) for f in glob.glob(os.path.join(category_dir, "*.tif"))])
            else:
                tif_files = []
            
            if tif_files:
                selected_file = st.selectbox("Select Satellite Image", tif_files)
                image_path = os.path.join(category_dir, selected_file)
            else:
                st.warning(f"No TIFF files found in {category_dir}")
                image_path = ""
        elif mode == "Load Local SAR File":
            image_path = st.text_input("Local TIFF Path", "data/raw/sentinel1_sample.tif")
            
        # Interactive Raw SAR Satellite Image & Mask Visual Preview
        if image_path and os.path.exists(image_path):
            with st.expander("📷 View Raw SAR Image & Mask Preview", expanded=True):
                try:
                    import rasterio
                    import numpy as np
                    with rasterio.open(image_path) as src:
                        band = src.read(1)
                    clipped = np.clip(band, -35.0, 5.0)
                    norm_sar = ((clipped - (-35.0)) / (5.0 - (-35.0)) * 255.0).astype(np.uint8)
                    
                    # Resolve mask path if in SARSatelite structure
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
                        
                    if mask_path and os.path.exists(mask_path):
                        with rasterio.open(mask_path) as msrc:
                            mband = msrc.read(1)
                        norm_mask = (mband * 255).astype(np.uint8)
                        col_a, col_b = st.columns(2)
                        with col_a:
                            st.image(norm_sar, caption="Radar VV Band", use_container_width=True)
                        with col_b:
                            st.image(norm_mask, caption="Ground Truth Mask", use_container_width=True)
                    else:
                        st.image(norm_sar, caption="Radar VV Band", use_container_width=True)
                except Exception as e:
                    st.caption(f"Preview unavailable: {e}")

        run_btn = st.button("🚀 Analyze Satellite Pass", use_container_width=True)
        
        # Load or run pipeline
        pipeline_results = st.session_state.get("pipeline_results", None)
        
        if run_btn:
            with st.spinner("Processing SAR imagery & backtracking drift..."):
                try:
                    mock_flag = (mode == "Run Mock Demo (Recommended)")
                    res = run_pipeline(image_path, mock_mode=mock_flag)
                    st.session_state["pipeline_results"] = res
                    pipeline_results = res
                    st.success("Analysis Complete!")
                except Exception as e:
                    st.error(f"Pipeline failed: {e}")
                    
        # Render left sidebar details panel
        render_spill_panel(pipeline_results)
        
    with col_mid:
        st.subheader("🗺️ Maritime GIS Layer Plot")
        if pipeline_results and pipeline_results.get("spill_detected", False):
            # Render interactive Folium map
            render_map_view(pipeline_results)
        else:
            st.info("Trigger analysis to load GIS mapping layers.")
            
    with col_right:
        st.subheader("🚢 Suspect Vessel Ranking")
        render_vessel_panel(pipeline_results)

# -------------------------------------------------------------
# TAB 2: Proactive Surveillance Watchlist (USP Feature)
# -------------------------------------------------------------
with tab_proactive:
    st.markdown(
        """
        <div style="background-color: #0f161c; padding: 15px; border-radius: 8px; border: 1px dashed #1a3c40; margin-bottom: 20px;">
            <span style="color: #26a69a; font-weight: bold; font-size: 1.05rem;">🌟 USP Feature: Proactive Maritime Surveillance</span><br>
            Instead of reactively analyzing after a spill occurs, SagarDrishti continuously monitors vessels inside 
            environmentally sensitive zones. Suspicious maneuvers (stops, heading changes, AIS gap anomalies) trigger immediate alerts.
        </div>
        """,
        unsafe_allow_html=True
    )
    
    # Render sensitive zones
    st.write("### 📌 Protected Marine Zones")
    cols_zones = st.columns(len(SENSITIVE_ZONES))
    for i, zone in enumerate(SENSITIVE_ZONES):
        with cols_zones[i]:
            st.markdown(
                f"""
                <div style="background-color: #111e25; border: 1px solid #1a3c40; border-radius: 8px; padding: 12px; text-align: center;">
                    <span style="color: #80cbc4; font-weight: 500; font-size: 0.9rem;">{zone['name']}</span><br>
                    <span style="color: #ffffff; font-size: 0.8rem;">({zone['lat']:.2f}N, {zone['lon']:.2f}E) | R={zone['radius_km']}km</span>
                </div>
                """,
                unsafe_allow_html=True
            )
            
    # Proactive Watchlist calculation
    st.write("### 🚨 Active Watchlist Alerts")
    
    # Generate mock positions for active vessels inside sensitive zones to demo watchlist
    # Vessel 1: Suspicious Tanker in Laccadive Sanctuary
    v1_mmsi = "SYN-998822101"
    v1_type = "Crude Oil Tanker"
    v1_lat, v1_lon = 10.51, 72.52 # inside Laccadive Sanctuary
    # Build suspicious trajectory: Unexpected stop, heading change, and AIS gaps
    v1_traj = [
        (10.3, 72.3, "2026-08-29T18:00:00Z", 12.0, 45.0),
        (10.4, 72.4, "2026-08-29T18:30:00Z", 11.5, 45.0),
        (10.51, 72.52, "2026-08-29T19:00:00Z", 0.5, 135.0), # stop and sharp turn
        # GAP in AIS transmission of 45 minutes
        (10.53, 72.54, "2026-08-29T20:15:00Z", 4.0, 45.0)
    ]
    
    # Vessel 2: Normal Container ship transiting Laccadive Sanctuary
    v2_mmsi = "SYN-112233445"
    v2_type = "Container Ship"
    v2_lat, v2_lon = 10.45, 72.38 # inside Laccadive Sanctuary
    v2_traj = [
        (10.38, 72.31, "2026-08-29T18:00:00Z", 14.5, 30.0),
        (10.42, 72.35, "2026-08-29T18:30:00Z", 14.2, 30.0),
        (10.45, 72.38, "2026-08-29T19:00:00Z", 14.6, 30.0) # normal speed, direct route
    ]
    
    # Execute Watchlist check
    vessel_positions = {v1_mmsi: (v1_lat, v1_lon), v2_mmsi: (v2_lat, v2_lon)}
    trajectories = {v1_mmsi: v1_traj, v2_mmsi: v2_traj}
    
    watchlist = run_proactive_watchlist(vessel_positions, trajectories, SENSITIVE_ZONES)
    
    if watchlist:
        for alert in watchlist:
            mmsi = alert["mmsi"]
            score = alert["risk_score"]
            zone_name = alert["zone"]
            evidence = alert["evidence"]
            
            # Show Alert card
            border_color = "#c62828" if score >= 50 else "#2e7d32"
            status_text = "CRITICAL ALERT" if score >= 50 else "NORMAL TRANSIT"
            
            st.markdown(
                f"""
                <div style="background-color: #111e25; border-left: 5px solid {border_color}; border-radius: 4px; padding: 15px; margin-bottom: 12px;">
                    <div style="display: flex; justify-content: space-between; align-items: center;">
                        <span style="font-size: 1.05rem; font-weight: bold; color: #ffffff;">🚢 Vessel MMSI: {mmsi}</span>
                        <span style="background-color: {border_color}; color: white; padding: 2px 8px; border-radius: 4px; font-size: 0.75rem; font-weight: bold;">{status_text}</span>
                    </div>
                    <div style="font-size: 0.88rem; color: #80cbc4; margin: 4px 0;">
                        Zone: <b>{zone_name}</b> | Behavioural Anomaly Score: <b>{score:.0f}/100</b>
                    </div>
                </div>
                """,
                unsafe_allow_html=True
            )
            
            if evidence:
                st.markdown("**🚨 Behaviour Anomalies Found:**")
                for ev in evidence:
                    st.markdown(f"- <span style='font-size: 0.85rem; color: #ef9a9a;'>{ev}</span>", unsafe_allow_html=True)
            else:
                st.markdown("<span style='font-size: 0.85rem; color: #a5d6a7;'>✓ Vessel transiting normally with zero behavioral anomalies.</span>", unsafe_allow_html=True)
    else:
        st.info("No active vessels inside protected marine sanctuaries.")
