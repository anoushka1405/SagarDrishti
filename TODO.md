# SagarDrishti (सागरदृष्टि) — Project Roadmap & TODO List 🌊🛢️

> **Note for Antigravity AI Agents & Team Members:**  
> This file outlines the current project status, remaining tasks, module ownership, and git workflow instructions. When team members pull this repository, their AI agents automatically read this file, `.agents/rules.md`, and `.agents/skills/` to inherit full context and know what needs to be worked on next.

---

## 🚦 Current Status Summary
- ✅ **Core Pipeline Orchestration (`src/pipeline/run_pipeline.py`)**: Fully working end-to-end (loads satellite, cleans SAR, segments slick with PyTorch U-Net weights `models/spill_unet.pth`, filters lookalikes, estimates age, runs particle hindcast & forecast, correlates AIS pings, scores suspects, & outputs JSON).
- ✅ **FastAPI Backend Server (`src/api/main.py`)**: Fully implemented & active with endpoints `/api/health`, `/api/dataset/categories`, `/api/sar_preview`, `/api/analyze`, `/api/proactive_watchlist`, `/api/simulate_drift`, and `/api/export_report`.
- ✅ **React Web Application (`frontend/`)**: Modern Vite + Tailwind CSS React dashboard built with `ForensicTab.jsx`, `ProactiveTab.jsx`, `SandboxTab.jsx`, `GISMap.jsx`, and `HelpModal.jsx`.
- ✅ **Mock & Synthetic Fallback Mode**: Pipeline runs cleanly with `--mock` flag when real files or pings are missing.
- ✅ **Automated Tests (`tests/test_pipeline.py`)**: All 4 pytest integration smoke tests pass cleanly (`4/4 passed`).
- ✅ **Sandbox integrity fix**: `/api/simulate_drift` now calls real `forward_simulation.py` + `backward_hindcast.py` physics modules (not fake Gaussian). Hindcast results displayed on frontend with origin marker, uncertainty radius, and backward track.
- ✅ **ML Segmentation Recall Tuning**: Recall improved from ~40% to **72.7%**. Added FocalLoss + DiceBCE combined loss, ReduceLROnPlateau scheduler, hard negative mining, and threshold grid search (optimal: 0.55). Checkpoint updated.
- ✅ **Interactive Time-Lapse Drift Playback**: GISMap.jsx has play/pause/skip/reset controls with time slider for step-by-step particle animation.
- ✅ **Automated Forensic Evidence PDF Export**: Backend `/api/export_report` generates PDF with detection summary, origin analysis, and vessel rankings. Frontend "Export PDF Report" button wired and functional.
- ✅ **OpenStreetMap Free Tile Layer Fix**: Replaced CARTO Voyager map tiles (which required API keys) with open-access OpenStreetMap raster tiles across `ProactiveTab.jsx` and `SandboxTab.jsx`.

---

## 📌 Remaining Tasks & Roadmap

### Phase 1: Must-Fix Before Internal Round (Priority: Highest)

- [x] **Sandbox integrity fix (`src/api/main.py`, `frontend/src/components/SandboxTab.jsx`)**:
  - `/api/simulate_drift` now calls the real `src/drift/forward_simulation.py` and `src/drift/backward_hindcast.py` modules.
  - Frontend SandboxTab renders hindcast track, estimated origin marker, uncertainty radius, and results panel.
  - Pitch script language should say "real Euler-advection physics engine" — not "simplified visualization".

- [x] **ML Segmentation Model Recall Tuning (`src/detection/train_model.py` & `segmentation_model.py`)**:
  - Recall improved from ~40% to **72.7%** on test set.
  - Added `FocalLoss` (alpha=0.75, gamma=2.0) + `DiceBCELoss` combined loss.
  - Added `ReduceLROnPlateau` scheduler (factor=0.5, patience=3).
  - Hard negative mining: top 20% loss samples oversampled 3x for 2 fine-tuning epochs.
  - Threshold grid search: optimal threshold **0.55** (F1=0.5565) selected over default 0.5.
  - Updated `models/spill_unet.pth` and `models/checkpoints/spill_unet_resnet34.pth`.

- [x] **Interactive Time-Lapse Drift Playback (`frontend/src/components/GISMap.jsx`)**:
  - Time-slider control bar with Play/Pause, Skip Forward, Reset buttons.
  - Step-through: ALL → +1h → +3h → +6h → +12h with tick labels.
  - Auto-cycles every 1.5s when playing; pauses on manual interaction.

- [x] **Automated Forensic Evidence PDF/HTML Export (`frontend/src/components/ForensicTab.jsx`)**:
  - Backend `/api/export_report` endpoint generates PDF with detection summary, origin analysis, and top-5 vessel rankings with evidence bullets.
  - Frontend "Export PDF Report" button appears after analysis, triggers browser download.
  - Uses `fpdf2` library; PDF includes title, sections, and footer.

- [x] **OpenStreetMap Free Map Tile Migration (`frontend/src/components/ProactiveTab.jsx`, `SandboxTab.jsx`)**:
  - Replaced CARTO Voyager map tiles (which required API keys) with 100% free OpenStreetMap tile layers.
  - Verified map loading, sanctuary boundaries, and simulation particle rendering with zero tile authentication errors.

- [x] **Pretrained U-Net Weights (`src/detection/segmentation_model.py`)** — done.
- [x] **Live Weather & Marine Data Loaders (`src/data/loaders.py`)** — done.
- [x] **FastAPI REST Service (`src/api/main.py`)** — done, verified via direct endpoint testing.
- [x] **Modern React Web Application (`frontend/`)** — done, verified via direct component review.

---

### Phase 2: Nice-to-Have Only If Time Remains (Priority: Low — do not let these take time from Phase 1)

- [ ] **Real-Time Alert Notifications (`src/pipeline/run_pipeline.py`)**:
  - One simple demo email/SMS via a free-tier SendGrid/Twilio account when a high-confidence spill (>70%) is identified. Keep it minimal — a real agency integration is a Phase 4/Later item, not this.
- [ ] **Stokes Wave Drift (`src/drift/forward_simulation.py` & `backward_hindcast.py`)**:
  - Only attempt if the core pipeline is fully stable and rehearsed — marginal accuracy gain judges are unlikely to probe deeply.
- [ ] **Oil Weathering Factors (`src/age_estimation/age_model.py`)**:
  - Same caveat as above — nice scientific depth, low priority for this round.

---

### Phase 3: Presentation (Priority: Highest — run in parallel with Phase 1, not after it)

- [ ] Convert slide deck content into final PPTX (innovation, feasibility, risks, strategies, impact, benefits, USP).
- [ ] Write the live demo narrative as an investigation story (spill → age → origin → suspect vessel → evidence), not a feature tour.
- [x] Confirm the demo script's Sandbox language matches Phase 1 decision — **Sandbox now uses real Euler-advection physics** (not Gaussian approximation). Pitch language: "real hydrodynamic particle advection engine."
- [x] ML recall improved to **72.7%** — update pitch claims accordingly (was "40% recall bottleneck").
- [x] PDF export functional — can demonstrate live evidence download during demo.
- [x] Time-lapse drift playback — can demonstrate step-by-step forecast animation during demo.
- [ ] Prepare direct answers for likely questions: "is this real-time," "how is an attribution score not an accusation," "where does your data come from," "why polling instead of continuous monitoring."
- [ ] Run at least one full team dry-run once Phase 1 items are done.

---

### Phase 4: Explicitly Deferred to Roadmap Slide Only — Do NOT Build for Internal Round

- [ ] **Live AIS Feed Integration (AISHub / Spire / MarineTraffic)**: paid commercial APIs, explicitly a production-phase item, not a hackathon gap. State this on the roadmap slide, don't attempt integration now.
- [ ] **Coastal Impact & Time-to-Shore Forecasting with Alerts**: needs coastline/protected-zone boundary data not yet collected — architecture-only slide item.
- [ ] **Multi-Sensor Fusion (EO Optical Cross-Validation)**: second full data pipeline — next-round item.
- [ ] **Dockerization (`Dockerfile` / `docker-compose.yml`)**: real risk of last-minute environment breakage this close to the deadline — use a simple start script instead for the actual demo.
- [ ] **GitHub Actions CI/CD**: zero demo value to judges, purely internal engineering hygiene.
- [ ] **Historical Repeat-Offender / Fleet Risk Intelligence**: needs persistent multi-incident data accumulated over time — vision slide only.
- [ ] **Direct Integration with Coast Guard / DG Shipping systems**: needs real agency partnership — vision slide only.

---

## 🎯 Product Strategy Recap (Now vs. Next vs. Later)

### 🟢 NOW (Internal Round / MVP)
1. Full Detect → Age → Backtrack → AIS Correlation → Explainable Scoring Pipeline.
2. Near-Real-Time Polling Monitor (`src/pipeline/monitor.py`).
3. Proactive Vessel Risk Watchlist for Sensitive Zones (`src/scoring/proactive_risk.py`).
4. Vessel Identity Enrichment (`src/ais/correlation.py`).
5. Forensic Evidence PDF Export.
6. Time-Lapse Drift Playback.
7. Sandbox integrity fix.
8. OpenStreetMap Free Map Tile Migration (Zero API Key Dependency).
9. Proactive Maritime Surveillance UI Header Polish.

### 🟡 NEXT (Next Round / Architecture Slides Only)
1. Coastal Impact & Time-to-Shore Forecasting with Alerts.
2. Multi-Sensor Fusion (EO Optical Cross-Validation).
3. Live AIS Feed Integration.
4. Real-Time Alert Notifications (beyond a minimal demo version).

### 🔴 LATER (Long-Term Production & Agency Deployment)
1. Historical Repeat-Offender & Fleet Risk Intelligence.
2. Direct Integration with Maritime Authorities (Coast Guard / DG Shipping).
3. Dockerization & CI/CD.

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
