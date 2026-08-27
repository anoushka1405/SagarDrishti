# SagarDrishti (सागरदृष्टि) 🌊🛢️
> **Automated Satellite Oil Spill Detection & AIS Vessel Attribution Pipeline**

---

## 📌 Project Overview
SagarDrishti leverages Sentinel-1 SAR imagery, oceanographic drift modeling, and AIS vessel trajectories to detect marine oil slicks, hindcast the spill release origin, and rank responsible suspect vessels with explainable attribution scoring.

---

## 👥 Team Workflow & Module Ownership (6 Members)
- **Member 1 (Detection)**: SAR speckle filtering, U-Net spill segmentation, and geometry extraction (`src/detection/`).
- **Member 2 (Drift & Hindcast)**: Spill age estimation and forward/backward particle advection (`src/drift/`, `src/age_estimation/`).
- **Member 3 (AIS Filtering)**: Spatio-temporal filtering and trajectory reconstruction (`src/ais/`, `src/data/synthetic_ais.py`).
- **Member 4 (Attribution Scoring)**: Vessel behavior anomaly extraction and weighted suspect ranking (`src/scoring/`).
- **Member 5 (Pipeline & Integration)**: End-to-end orchestration and smoke tests (`src/pipeline/`, `tests/`).
- **Member 6 (Dashboard & UI)**: GIS map layers and interactive attribution panel (`dashboard/`).

---

## 🚀 Quick Setup for Team Members

### 1. Clone the Repository
```bash
git clone <YOUR_GITHUB_REPO_URL>
cd SagarDrishti
```

### 2. Create Virtual Environment & Install Dependencies
```bash
python3 -m venv venv
source venv/bin/activate   # On Windows: venv\Scripts\activate
pip install -r requirements.txt
```

### 3. Run Pipeline in Mock Mode (Zero-data Demo)
```bash
python -m src.pipeline.run_pipeline --mock
```

---

## 🤖 Antigravity AI Customizations
The `.agents/` folder contains workspace-level rules, skills, and MCP configurations. When opening this repository in Antigravity IDE, the agent automatically loads:
- **`rules.md`**: Core data contracts, domain constraints, and architectural standards.
- **`SKILL.md`**: Runbook with step-by-step procedures for building and testing each module.
- **`mcp_config.json`**: MCP tool definitions for querying AIS datasets and inspecting data rasters.
