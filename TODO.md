# SagarDrishti (सागरदृष्टि) — Project Roadmap & TODO List 🌊🛢️

> **Note for Antigravity AI Agents & Team Members:**  
> This file outlines the current project status, remaining tasks, module ownership, and git workflow instructions. When team members pull this repository, their AI agents automatically read this file, `.agents/rules.md`, and `.agents/skills/` to inherit full context and know what needs to be worked on next.

---

## 🚦 Current Status Summary
- ✅ **Core Pipeline Orchestration (`src/pipeline/run_pipeline.py`)**: Fully working end-to-end (loads satellite, cleans SAR, segments slick with PyTorch U-Net weights `models/spill_unet.pth`, filters lookalikes, estimates age, runs particle hindcast & forecast, correlates AIS pings, scores suspects, & outputs JSON).
- ✅ **FastAPI Backend Server (`src/api/main.py`)**: Fully implemented & active with endpoints `/api/health`, `/api/dataset/categories`, `/api/sar_preview`, `/api/analyze`, `/api/proactive_watchlist`, and `/api/simulate_drift`.
- ✅ **React Web Application (`frontend/`)**: Modern Vite + Tailwind CSS React dashboard built with `ForensicTab.jsx`, `ProactiveTab.jsx`, `SandboxTab.jsx`, `GISMap.jsx`, and `HelpModal.jsx`.
- ✅ **Mock & Synthetic Fallback Mode**: Pipeline runs cleanly with `--mock` flag when real files or pings are missing.
- ✅ **Automated Tests (`tests/test_pipeline.py`)**: All 4 pytest integration smoke tests pass cleanly (`4/4 passed`).
- ⚠️ **`/api/simulate_drift` is currently a fake Gaussian dispersion placeholder, NOT the real advection engine** — see Phase 1, must be resolved before demo, not left silent.
- ⚠️ **Data storage for the 450-image real dataset (`data/raw/SARSatelite/Images/`) has not been confirmed safe for a 6-person team** — see Phase 1.

---

## 📌 Remaining Tasks & Roadmap

### Phase 1: Must-Fix Before Internal Round (Priority: Highest)

- [ ] **Sandbox integrity fix (`src/api/main.py`, `frontend/src/components/SandboxTab.jsx`)**:
  - `/api/simulate_drift` currently returns a synthetic Gaussian dispersion approximation instead of calling the real `src/drift/forward_simulation.py` / `backward_hindcast.py` modules.
  - Decide one of two paths and execute it — do not leave this silently fake:
    1. Wire the endpoint to the real physics modules, or
    2. Relabel the Sandbox UI copy as an illustrative/simplified visualization so it's never presented as the production engine.
  - Update the pitch script (Phase 3 presentation prep) to match whichever path is chosen.

- [ ] **ML Segmentation Model Recall Tuning (`src/detection/train_model.py` & `segmentation_model.py`)**:
  - Address the ~40% recall bottleneck: test threshold values (0.5 → 0.35 and nearby points against the validation set, don't just hardcode 0.35), add focal loss weighting alongside Dice+BCE, add `ReduceLROnPlateau` scheduler, mine hard negatives from look-alike images.
  - Re-run full test-set evaluation afterward and update `models/spill_unet.pth` (the checkpoint everyone else's pipeline loads).

- [ ] **Interactive Time-Lapse Drift Playback (`frontend/src/components/GISMap.jsx`)**:
  - Add a time-slider control to animate particle movement (+1h to +12h forecast) step-by-step, replacing the current static overlay.

- [ ] **Automated Forensic Evidence PDF/HTML Export (`frontend/src/components/ForensicTab.jsx`)**:
  - Build the backend generator (slick geometry, origin coordinates + uncertainty, ranked suspect evidence bullets) and wire the existing (currently non-functional) download button to it.

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
- [ ] Confirm the demo script's Sandbox language matches whichever Phase 1 decision was made — don't claim "full physics" unless it was actually wired.
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
