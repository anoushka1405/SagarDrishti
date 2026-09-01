# SagarDrishti (सागरदृष्टि) — Project Roadmap & TODO List 🌊🛢️

> **Note for Antigravity AI Agents & Team Members:**  
> This file outlines the current project status, remaining tasks, module ownership, and git workflow instructions. When team members pull this repository, their AI agents automatically read this file, `.agents/rules.md`, and `.agents/skills/` to inherit full context and know what needs to be worked on next.

---

## 🚦 Current Status Summary
- ✅ **Core Pipeline Orchestration (`src/pipeline/run_pipeline.py`)**: Fully working end-to-end (loads satellite, cleans SAR, segments slick, filters lookalikes, estimates age, runs particle hindcast & forecast, correlates AIS pings, scores suspects, & outputs JSON).
- ✅ **Mock & Synthetic Fallback Mode**: Pipeline runs cleanly with `--mock` flag when real files are missing.
- ✅ **Interactive Dashboard (`dashboard/app.py`)**: Streamlit UI active and displaying GIS map layers, slick metrics, particle drift tracks, and ranked suspect vessel scorecards.
- ✅ **Automated Tests (`tests/test_pipeline.py`)**: All 4 pytest integration smoke tests pass cleanly (`4/4 passed`).

---

## 📌 Remaining Tasks & Future Roadmap

### Phase 1: Real Data & Model Fine-Tuning 🤖 (Priority: High)
- [ ] **Pretrained U-Net Weights (`src/detection/segmentation_model.py`)**:
  - Train U-Net / DeepLab model on labeled Sentinel-1 SAR oil spill datasets (e.g. SARSatelite) and save PyTorch model weights (`.pth`) to `models/spill_unet.pth`.
  - Update `SpillSegmentationModel` to load weights by default.
- [ ] **Live NetCDF Data Loaders (`src/data/loaders.py`)**:
  - Replace mock grid fallback with live ERA5 wind and HYCOM current NetCDF file parsing for real ocean coordinates.
- [ ] **Live AIS Feed Integration (`src/data/loaders.py` / `src/ais/correlation.py`)**:
  - Add optional live AIS stream loader (e.g., AISHub / Spire API / MarineTraffic) alongside CSV and synthetic data.

### Phase 2: Advanced Marine Physics 🌊 (Priority: Medium)
- [ ] **Stokes Wave Drift (`src/drift/forward_simulation.py` & `backward_hindcast.py`)**:
  - Integrate Stokes wave drift into particle advection alongside current vectors and 3% wind drift factor.
- [ ] **Oil Weathering Factors (`src/age_estimation/age_model.py`)**:
  - Add evaporation and emulsification rate calculations to refine slick age window estimation.

### Phase 3: Dashboard & Next-Gen React UI 🎨 (Priority: High)
- [ ] **Modern React Web Application (`frontend/` or `dashboard/react/`)**:
  - Build a high-performance React (Vite / Next.js) web dashboard with rich aesthetics, sleek dark mode, Mapbox / Leaflet GIS integration, interactive particle drift time-lapses, and real-time suspect vessel ranking cards.
- [ ] **Automated Forensic Evidence PDF/HTML Export (`dashboard/app.py`)**:
  - Add a button in the UI to download a formatted legal evidence PDF report containing slick geometry, origin coordinates, and suspect vessel evidence bullets.
- [ ] **Time-Lapse Drift Playback**:
  - Add interactive time-slider controls to animate particle movement (+1h to +12h forecast) on map layers.
- [ ] **Real-Time Alert Notifications (`src/pipeline/run_pipeline.py`)**:
  - Add email/SMS/webhook alerts (e.g. via SendGrid / Twilio) triggered when a high-confidence spill ($>70\%$) is identified.

### Phase 4: Production API & Deployment 🚀 (Priority: Low)
- [ ] **FastAPI Service (`src/pipeline/api.py`)**:
  - Wrap `run_pipeline.py` in a RESTful API (`POST /api/v1/detect`) for external app integration.
- [ ] **Dockerization (`Dockerfile` / `docker-compose.yml`)**:
  - Create Docker containers for single-command deployment of backend pipeline + Streamlit UI.
- [ ] **GitHub Actions CI/CD (`.github/workflows/ci.yml`)**:
  - Add automated workflow running `pytest tests/test_pipeline.py` on pull requests.

---

## 🎯 Product Strategy & Feature Roadmap (Now vs. Next vs. Later)

### 🟢 NOW (Building for Internal Round / MVP)
1. **Full Detect → Age → Backtrack → AIS Correlation → Explainable Scoring Pipeline:**
   - Look at SAR satellite image, confirm oil presence (lookalike filter), estimate slick age, rewind time (advection advection) to calculate origin, check nearby vessels, and rank suspects with human-readable evidence.
2. **Near-Real-Time Polling Monitor (`src/pipeline/monitor.py`):**
   - Automatically polls incoming image folders for new satellite pass arrivals and triggers the pipeline.
3. **Proactive Vessel Risk Watchlist for Sensitive Zones (`src/scoring/proactive_risk.py`):**
   - Continuously monitors vessel behavior in protected marine zones (e.g. Laccadive Sanctuary) and flags anomalous behavior (sudden speed drops, course deviations, AIS blackouts) *before* a spill occurs.
4. **Vessel Identity Enrichment (`src/ais/correlation.py`):**
   - Resolves raw MMSI IDs to vessel names and types (e.g., Cargo, Tanker, Container) for intuitive dashboard display.

### 🟡 NEXT (Planned for Next Round / Architecture Slides)
1. **Coastal Impact & Time-to-Shore Forecasting with Alerts:**
   - Predicts exact landfall time and coastline impact zone, triggering early warnings ("Spill reaching coast in 8 hours").
2. **Multi-Sensor Fusion (EO Optical Cross-Validation):**
   - Fuses optical Earth Observation imagery (when cloud-free) to cross-validate SAR radar slick detections and reduce false alarms.

### 🔴 LATER (Long-Term Production & Agency Deployment)
1. **Historical Repeat-Offender & Fleet Risk Intelligence:**
   - Accumulates multi-year historical spill incident databases to elevate baseline risk scores for vessels with past violations.
2. **Direct Integration with Maritime Authorities (Coast Guard / DG Shipping):**
   - Direct API integration with maritime response agency command centers for automated emergency dispatches.


---

## 👥 Team Workflow & Git Instructions

### How to Safely Pull & Push Code to GitHub

1. **Pull Latest Changes First:**
   ```bash
   git pull origin main
   ```
   *(If you have uncommitted local edits, run `git stash` before pulling, then `git stash pop` after pulling).*

2. **Verify Tests Pass Locally:**
   ```bash
   .venv\Scripts\python.exe -m pytest tests/test_pipeline.py -v
   ```

3. **Stage, Commit, and Push Your Work:**
   ```bash
   git add .
   git commit -m "feat: updated TODO roadmap, pipeline status, and context docs"
   git push origin main
   ```

---

## 🧠 Context Sharing with Teammates' Antigravity AI Agents

**Q: If team members pull this repository now, will their Antigravity AI agents have all the previous context?**

**A: YES!** 
* **What is shared:** Antigravity AI automatically reads repository files committed to git (`TODO.md`, `README.md`, `.agents/rules.md`, `.agents/skills/`, docstrings, and tests) every time a turn starts.
* **How it works:** When your teammates run `git pull`, their local copy receives all these files. Their Antigravity agents will instantly read `TODO.md` and `.agents/rules.md` to know the architecture, what is finished, and what tasks to work on next.
* **Note:** Private local settings (like chat history logs or API keys) remain private to each developer's system for security.
