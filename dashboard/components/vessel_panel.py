"""
Vessel Panel component for SagarDrishti Dashboard.
Renders ranked suspect lists and evidence breakdowns.
"""

import streamlit as st
from typing import Dict, Any, List

def render_vessel_panel(result: Dict[str, Any]):
    """
    Renders the right sidebar suspect vessel panel.
    """
    if not result or not result.get("spill_detected", False):
        st.info("No active spill suspects to show.")
        return
        
    vessels: List[Dict[str, Any]] = result.get("ranked_vessels", [])
    
    if not vessels:
        st.info("No vessels identified in the spatio-temporal correlation window.")
        return
        
    st.markdown(
        """
        <style>
        .score-pill {
            padding: 3px 8px;
            border-radius: 6px;
            font-weight: bold;
            font-size: 0.9rem;
            color: #ffffff;
        }
        .score-high {
            background-color: #d32f2f;
        }
        .score-med {
            background-color: #f57c00;
        }
        .score-low {
            background-color: #388e3c;
        }
        .evidence-list {
            margin-top: 5px;
            padding-left: 15px;
            font-size: 0.85rem;
            color: #b0bec5;
        }
        </style>
        """,
        unsafe_allow_html=True
    )
    
    st.markdown(f"**{len(vessels)} Suspects Correlated**")
    
    for idx, v in enumerate(vessels):
        mmsi = v["mmsi"]
        score = v["attribution_score"]
        conf = v["confidence_level"]
        closest_dist = v["closest_distance_km"]
        time_offset = v["time_delta_hours"]
        v_type = v["vessel_type"]
        
        # Color coding classes
        if score >= 70.0:
            color_class = "score-high"
        elif score >= 40.0:
            color_class = "score-med"
        else:
            color_class = "score-low"
            
        header = f"🚢 {mmsi} ({score:.0f}/100)"
        
        # Use st.expander for collapsible evidence view
        with st.expander(header, expanded=(idx == 0)):
            st.markdown(
                f"""
                <div style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 8px;">
                    <span style="font-size: 0.85rem; color: #80cbc4;">Type: <b>{v_type}</b></span>
                    <span class="score-pill {color_class}">{conf} Risk</span>
                </div>
                <div style="font-size: 0.85rem; color: #eceff1; margin-bottom: 6px;">
                    • Closest Approach: <b>{closest_dist:.1f} km</b><br>
                    • Release Offset: <b>{time_offset:+.1f} hrs</b>
                </div>
                """,
                unsafe_allow_html=True
            )
            
            st.write("📋 **Evidence Logs:**")
            for ev in v["evidence"]:
                st.markdown(f"• <span style='font-size: 0.82rem; color: #cfd8dc;'>{ev}</span>", unsafe_allow_html=True)
