"""
Map View component for SagarDrishti Dashboard.
Renders GIS layers: spill polygon, origin beacon, backtrack/forecast paths, and vessel tracks.
"""

import streamlit as st
import folium
from streamlit_folium import st_folium
from typing import Dict, Any, List

def render_map_view(result: Dict[str, Any]):
    """
    Renders the central map using Folium and streamlit-folium.
    """
    if not result:
        st.info("No pipeline results to display on the map.")
        return
        
    origin = result.get("estimated_origin", (18.43, 70.82))
    origin_lat, origin_lon = origin
    
    # 1. Initialize Folium Map centered on the estimated origin
    # Using Esri Dark Gray base tile (free, clean dark mode GIS layer with zero watermark)
    m = folium.Map(
        location=[origin_lat, origin_lon],
        zoom_start=10,
        tiles="https://server.arcgisonline.com/ArcGIS/rest/services/Canvas/World_Dark_Gray_Base/MapServer/tile/{z}/{y}/{x}",
        attr="Esri World Dark Gray",
        control_scale=True
    )
    
    # 2. Plot Spill Polygon (swapping lon/lat to lat/lon for folium)
    poly_coords = result.get("spill_polygon_coords", [])
    if poly_coords:
        folium_poly = [[c[1], c[0]] for c in poly_coords]
        folium.Polygon(
            locations=folium_poly,
            color="#3e2723",
            weight=3,
            fill=True,
            fill_color="#212121",
            fill_opacity=0.7,
            tooltip=f"Oil Slick Area: {result.get('area_km2', 0.0)} km²"
        ).add_to(m)
        
        # Also put a centroid marker for the current observed slick
        c_lat, c_lon = result.get("centroid", (18.43, 70.82))
        folium.CircleMarker(
            location=[c_lat, c_lon],
            radius=6,
            color="#ffeb3b",
            fill=True,
            fill_color="#ffeb3b",
            tooltip="Current Observed Centroid"
        ).add_to(m)
        
    # 3. Plot Estimated Origin Beacon
    uncertainty = result.get("origin_uncertainty_km", 5.0)
    folium.Marker(
        location=[origin_lat, origin_lon],
        icon=folium.Icon(color="red", icon="warning", icon_color="white"),
        tooltip=f"Estimated Origin Centroid (Uncertainty: +/-{uncertainty} km)"
    ).add_to(m)
    
    # Add uncertainty circle
    folium.Circle(
        location=[origin_lat, origin_lon],
        radius=uncertainty * 1000.0,  # convert km to meters
        color="#c62828",
        weight=1,
        fill=True,
        fill_color="#c62828",
        fill_opacity=0.15,
        tooltip="Origin Uncertainty Range"
    ).add_to(m)

    # 4. Plot Backward Hindcast Trail (dashed purple line)
    hindcast_track = result.get("hindcast_track", [])
    if len(hindcast_track) > 1:
        folium.PolyLine(
            locations=hindcast_track,
            color="#9c27b0",
            weight=3,
            dash_array="5, 10",
            tooltip="Backward Hindcast Drift Trail"
        ).add_to(m)
        
    # 5. Plot Forward Forecast Particles (orange dots)
    forecast_tracks = result.get("forecast_tracks", {})
    # Draw particles for the final forecast mark (usually 12h) to show expansion cone
    last_hr = max(forecast_tracks.keys(), key=lambda k: float(k)) if forecast_tracks else None
    if last_hr:
        # Sample subset of particles (first 50) to keep map rendering fast
        pts = forecast_tracks[last_hr][:80]
        for pt in pts:
            folium.CircleMarker(
                location=[pt[0], pt[1]],
                radius=2,
                color="#ff9800",
                fill=True,
                fill_color="#ff9800",
                fill_opacity=0.5
            ).add_to(m)
            
    # 6. Plot AIS Vessel Tracks
    vessels = result.get("ranked_vessels", [])
    for v in vessels:
        traj = v["trajectory"]
        score = v["attribution_score"]
        mmsi = v["mmsi"]
        v_type = v["vessel_type"]
        
        if len(traj) > 1:
            # Color code based on risk
            if score >= 70.0:
                line_color = "#f44336"  # Red
            elif score >= 40.0:
                line_color = "#ff9800"  # Orange
            else:
                line_color = "#4caf50"  # Green
                
            coords = [[pt[0], pt[1]] for pt in traj]
            
            # Polyline for track
            folium.PolyLine(
                locations=coords,
                color=line_color,
                weight=2.5,
                opacity=0.8,
                tooltip=f"Vessel {mmsi} ({v_type}) - Score: {score}/100"
            ).add_to(m)
            
            # Add small arrow or dot for latest position
            latest_pt = coords[-1]
            folium.CircleMarker(
                location=latest_pt,
                radius=4,
                color=line_color,
                fill=True,
                fill_color=line_color,
                tooltip=f"Vessel {mmsi} Current Position"
            ).add_to(m)
            
    # 7. Render map in Streamlit
    st_folium(m, width=700, height=500, returned_objects=[])
