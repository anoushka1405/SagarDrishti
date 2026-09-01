"""
Spill Panel component for SagarDrishti Dashboard.
Renders satellite observation summary with premium aesthetics.
"""

import os
import streamlit as st
from typing import Dict, Any

def render_spill_panel(result: Dict[str, Any]):
    """
    Renders the left sidebar spill metadata panel.
    """
    if not result:
        st.info("No satellite observation loaded.")
        return
        
    detected = result.get("spill_detected", False)
    
    # Custom premium CSS styling for the panel
    st.markdown(
        """
        <style>
        .spill-card {
            background: linear-gradient(135deg, #111e25 0%, #070b0d 100%);
            border: 1px solid #1a3c40;
            border-radius: 12px;
            padding: 18px;
            color: #e0f2f1;
            margin-bottom: 20px;
            box-shadow: 0 4px 15px rgba(0,0,0,0.3);
        }
        .spill-card h3 {
            color: #26a69a;
            margin-top: 0;
            font-size: 1.15rem;
            letter-spacing: 0.5px;
            border-bottom: 1px solid #1a3c40;
            padding-bottom: 8px;
        }
        .stat-row {
            display: flex;
            justify-content: space-between;
            margin: 10px 0;
            font-size: 0.9rem;
        }
        .stat-label {
            color: #80cbc4;
            font-weight: 500;
        }
        .stat-value {
            font-weight: 700;
            color: #ffffff;
        }
        .status-badge {
            background-color: #c62828;
            color: #ffffff;
            padding: 2px 8px;
            border-radius: 4px;
            font-size: 0.8rem;
            font-weight: bold;
        }
        .status-ok {
            background-color: #2e7d32;
        }
        </style>
        """,
        unsafe_allow_html=True
    )

    if detected:
        st.markdown(
            f"""
            <div class="spill-card">
                <h3>📡 Satellite Pass Analysis</h3>
                <div class="stat-row">
                    <span class="stat-label">Analysis Result:</span>
                    <span class="status-badge">SPILL DETECTED ✓</span>
                </div>
                <div class="stat-row">
                    <span class="stat-label">Detection Confidence:</span>
                    <span class="stat-value">{result.get("confidence", 0.0):.1f}%</span>
                </div>
                <div class="stat-row">
                    <span class="stat-label">Slick Area:</span>
                    <span class="stat-value">{result.get("area_km2", 0.0):.2f} km²</span>
                </div>
                <div class="stat-row">
                    <span class="stat-label">Slick Perimeter:</span>
                    <span class="stat-value">{result.get("perimeter_km", 0.0):.2f} km</span>
                </div>
                <div class="stat-row">
                    <span class="stat-label">Shape Compactness:</span>
                    <span class="stat-value">{result.get("compactness", 0.0):.2f}</span>
                </div>
            </div>
            
            <div class="spill-card" style="border-color: #372948;">
                <h3 style="color: #bb86fc; border-color: #4b3d5b;">⏳ Age & Backtrack Window</h3>
                <div class="stat-row">
                    <span class="stat-label" style="color: #d1c4e9;">Estimated Age:</span>
                    <span class="stat-value">{result.get("age_low", 0.0)} - {result.get("age_high", 0.0)} hrs</span>
                </div>
                <div class="stat-row">
                    <span class="stat-label" style="color: #d1c4e9;">Age Confidence:</span>
                    <span class="stat-value">{result.get("age_confidence", 0.0):.1f}%</span>
                </div>
                <div class="stat-row" style="flex-direction: column; margin-top: 8px;">
                    <span class="stat-label" style="color: #d1c4e9; margin-bottom: 2px;">Release Window:</span>
                    <span class="stat-value" style="font-size: 0.8rem; word-break: break-all;">
                        {result.get("release_window", ("", ""))[0]}<br>to<br>{result.get("release_window", ("", ""))[1]}
                    </span>
                </div>
            </div>
            """,
            unsafe_allow_html=True
        )
    else:
        st.markdown(
            f"""
            <div class="spill-card" style="border-color: #2e7d32;">
                <h3>📡 Satellite Pass Analysis</h3>
                <div class="stat-row">
                    <span class="stat-label">Analysis Result:</span>
                    <span class="status-badge status-ok">CLEAN SEA ✓</span>
                </div>
                <div class="stat-row">
                    <span class="stat-label">Details:</span>
                    <span class="stat-value" style="font-size: 0.85rem;">No slicks detected / false positives rejected.</span>
                </div>
            </div>
            """,
            unsafe_allow_html=True
        )

    # Render SAR satellite image preview thumbnail
    img_path = result.get("image_path", "")
    if img_path and os.path.exists(img_path):
        try:
            import rasterio
            import numpy as np
            with rasterio.open(img_path) as src:
                band = src.read(1)
            clipped = np.clip(band, -35.0, 5.0)
            norm = ((clipped - (-35.0)) / (5.0 - (-35.0)) * 255.0).astype(np.uint8)
            st.markdown("### 📷 Raw SAR Backscatter Preview")
            st.image(norm, caption=f"Sentinel-1 VV Band ({os.path.basename(img_path)})", use_container_width=True)
        except Exception:
            pass
