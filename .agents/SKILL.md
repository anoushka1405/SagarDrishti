---
name: sagardrishti-pipeline
description: >-
  Use this skill when building, running, debugging, or verifying the SagarDrishti
  oil spill detection, drift hindcast, and AIS vessel attribution pipeline and UI.
---

# SagarDrishti Pipeline Engineering Playbook

This skill provides step-by-step procedures to build, run, mock, and verify the SagarDrishti end-to-end oil spill detection and vessel attribution system.

---

## 1. Project Architecture & Contracts

Every module must interact through standard data contracts defined in `src/data/schema.py`:
- `SATELLITE_FIELDS`: `image_id`, `timestamp`, `bbox`, `sar_array`, `resolution_m`
- `OCEAN_FIELDS`: `timestamp`, `lat_grid`, `lon_grid`, `u_current`, `v_current`
- `WEATHER_FIELDS`: `timestamp`, `lat_grid`, `lon_grid`, `u_wind`, `v_wind`
- `AIS_FIELDS`: `mmsi`, `timestamp`, `lat`, `lon`, `speed_knots`, `course`, `heading`, `vessel_type`

---

## 2. Step-by-Step Module Implementation Workflows

### Step 1: Data Loaders & Synthetic Data (Members 1, 2, 3)
1. Verify raster reading using `rasterio` and NetCDF reading using `xarray`.
2. Ensure custom `DataLoadError` is raised on missing files without crashing.
3. Test synthetic AIS generator:
   ```bash
   python -c "from src.data.synthetic_ais import generate_synthetic_vessels; df = generate_synthetic_vessels(18.43, 70.82, '2026-08-27T12:00:00Z'); print(df.head()); assert (df['mmsi'].str.startswith('SYN-')).all()"
   ```

### Step 2: Detection & Geometry (Member 1)
1. Apply speckle filter (`cv2.fastNlMeansDenoising` or Lee filter) on Sentinel-1 SAR.
2. Inference via `SpillSegmentationModel` (fallback to pretrained U-Net backbone if weights are absent).
3. Compute geodesic area ($km^2$), perimeter ($km$), and compactness with `shapely` & `skimage`.

### Step 3: Age Estimation & Drift Hindcast (Member 2)
1. Calculate age range $(T_{min}, T_{max}, \text{confidence})$ from elongation and drift velocity ($v_{drift} \approx \vec{v}_{current} + 0.03 \cdot \vec{v}_{wind}$).
2. Run backward particle advection with negated velocity vectors to derive estimated origin centroid $(\text{lat}, \text{lon}) \pm \text{uncertainty\_km}$.
3. Run forward simulation (+1h, +3h, +6h, +12h) for forecast drift cone.

### Step 4: AIS Correlation & Anomaly Features (Member 3 & 4)
1. Spatio-temporal filter: keep vessels within $R=50\text{ km}$ and $\Delta T = \pm 6\text{ hrs}$ of origin window.
2. Check trajectory intersection using `shapely.LineString`.
3. Extract behavioral features:
   - Speed anomaly vs vessel median
   - Heading delta $> 45^\circ$
   - Unexpected mid-route stop ($v < 1\text{ knot}$)
   - AIS dark gap near origin ($> 30\text{ min}$)

### Step 5: Attribution Scoring & Explainability (Member 4)
1. Normalize sub-scores to $[0, 1]$ and compute composite Attribution Score ($0 - 100$):
   $$\text{Score} = 30\% \cdot S_{spatial} + 25\% \cdot S_{temporal} + 20\% \cdot S_{trajectory} + 10\% \cdot S_{behaviour} + 10\% \cdot S_{gap} + 5\% \cdot S_{type}$$
2. Generate human-readable evidence bullets via `explain_score()`. Always report confidence level (Low/Medium/High).

---

## 3. Execution & Verification Commands

### Run Full Pipeline in Mock Mode (Zero-data Safety Net)
```bash
python -m src.pipeline.run_pipeline --mock
```

### Run Pipeline on Real Sample Data
```bash
python -m src.pipeline.run_pipeline --image data/raw/sentinel1_sample.tif
```

### Launch Interactive Dashboard
```bash
# For React UI:
npm run dev
# Or for Streamlit/Python UI (if using Python dashboard):
python -m dashboard.app
```

### Run Pipeline Smoke & Sanity Tests
```bash
pytest tests/test_pipeline.py -v
```

---

## 4. Troubleshooting & Fallback Checklist

- [ ] **Missing SAR weights**: Ensure `SpillSegmentationModel` logs a warning and returns heuristic threshold mask instead of crashing.
- [ ] **Missing Wave/Wind NetCDF**: Ensure `simulate_forward` and `hindcast_origin` fallback to default wind drift ($3\%$) when wave data is `None`.
- [ ] **No real AIS pings in area**: Automatically switch to `src/data/synthetic_ais.py` and flag records with `SYN-` prefix.
- [ ] **UI Blank Screen**: Fallback `dashboard/app.py` to default mock payload if backend returns an error.
