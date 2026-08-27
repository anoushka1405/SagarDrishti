# Coding Prompt — Oil Spill Detection & Vessel Attribution System

---

## 0. System context (read first, applies to every module)

You are implementing an MVP that demonstrates this end-to-end flow for a hackathon
problem statement on oil-spill detection and responsible-vessel attribution:

##### PROBLEM STATEMENT:- 
**Leveraging satellite imagery to determine Oil spills at sea along with AIS data correlations to identify vessel responsible for the spill.**

• Background Marine oil spills inflict great damage on marine ecosystems and several times remains un-attributable to the vessel causing such spills. Leveraging satellite imagery along with AIS data will enable detection of oil spills and vessel responsible for the same.
• Description The core challenge attempts to facilitate detection of oil spills and also in identifying the polluting vessel using remote sensing satellite data, such as SAR and EO imagery and AIS data. Participants are to design an intelligent automated pipeline to do the following: 
  (a) Detect and characterise the oil spill and calculating geometric properties and age if feasible. 
  (b) Using oceanographic and meteorological data, it is envisaged to trace the slick towards the origin point and time, predict the future flow of the slick, and 
  (c) analyse and attribute the spill to a vessel using historic AIS data to reconstruct vessel traffic around the origin window in space and time. The irrelevant traffic is to be filtered out and potential suspect vessels are to be scored considering various aspects such as proximity, trajectory, behavioural anomalies etc.
• Expected Solution An automated detection and hindcasting machine learning model that identified oils slicks from satellite imagery, mapping their drift paths backward and forward. It also ranks potential culprit vessel based on spatio-temporal correlation with AIS data. A suitable visual interface is also to be developed.

```
Satellite image → detect spill → estimate spill age → backtrack → estimated origin
→ find vessels → analyze trajectories → rank suspects → explain why
```

Global rules that apply to **every** file you touch:

1. **Don't build for scientific perfection — build for a working, explainable demo.**
   Every module must run end-to-end even with imperfect models; correctness of the
   final ML models matters less than the pipeline never crashing.
2. **Never claim certainty you don't have.** Age estimates, origin estimates, and
   vessel scores must always be returned with an uncertainty range or confidence
   value, not a bare number.
3. **Never call the vessel score "guilt" or "proof."** Always label it
   "Attribution Score" or "Risk Score" in code comments, variable names, docstrings,
   and any UI text.
4. **Graceful degradation is mandatory.** If an optional data source is missing
   (EO imagery, wave data, real AIS), the pipeline must still produce a full
   result using the fallback path defined in `config/config.yaml`. Never let a
   missing optional source raise an unhandled exception — check
   `config.data_sources.*` flags and branch.
5. **Follow the existing schema.** Don't invent new field names — use exactly
   the fields defined in `src/data/schema.py` (`SATELLITE_FIELDS`, `AIS_FIELDS`,
   `OCEAN_FIELDS`, `WEATHER_FIELDS`) as the contract between modules.
6. **Every public function needs a docstring with Args/Returns**, and every
   module-level docstring should state which step/module of the plan it belongs to
   (already scaffolded — keep it accurate as you implement).
7. **Write for a live demo, not a paper.** Prefer a working baseline (e.g. a
   pretrained U-Net, simple physics formulas, weighted-sum scoring) over
   state-of-the-art research code you won't have time to debug.

Work through the modules in the order below — each one only depends on modules
above it, so implementing top-to-bottom keeps the pipeline runnable at every step.

---

## 1. `src/data/` — Data layer (step 1)

**File: `src/data/loaders.py`**

Implement:
- `load_satellite(path)` — load a Sentinel-1 SAR GeoTIFF/HDF5 file with `rasterio`,
  return a dict/DataFrame matching `SATELLITE_FIELDS`. Extract `latitude`/`longitude`
  from the raster's geotransform (centroid or per-pixel grid, your choice — document
  which). If a `ground_truth_mask` file exists alongside the image (same name +
  `_mask` suffix), load it; otherwise set to `None`.
- `load_ais(path)` — load a CSV/Parquet of AIS pings into a DataFrame matching
  `AIS_FIELDS`. Parse `timestamp` to `datetime`, coerce `speed`/`heading`/`course`
  to numeric, drop rows with invalid `mmsi`.
- `load_ocean_currents(path)` — load a NetCDF (via `xarray`) of current speed/direction
  matching `OCEAN_FIELDS`. If wave data is present in the same file, load it into a
  separate optional field, don't fail if absent.
- `load_wind(path)` — same pattern as currents but for `WEATHER_FIELDS`.

Each loader must:
- Accept a file path or directory.
- Raise a clear, custom exception (`DataLoadError`) with a human-readable message
  if the file is missing/corrupt — never let a raw `FileNotFoundError` propagate
  to the pipeline layer.
- Have a `# TODO(fallback)` comment marking where `config.yaml`'s fallback flag
  should be checked by the caller.

**File: `src/data/synthetic_ais.py`**

Implement `generate_synthetic_vessels(origin_lat, origin_lon, event_time, n_vessels=6)`:
- Generate `n_vessels` plausible vessel tracks using randomized but *physically
  sane* speed (5–20 knots), heading, and a start position within 5–60 km of the
  origin at a randomized time offset from `event_time` (some before, some after,
  so not every synthetic vessel is a "guaranteed hit" — the demo needs to show the
  scoring model correctly de-prioritizing irrelevant vessels too).
- Return a DataFrame matching `AIS_FIELDS`, with `mmsi` values prefixed `SYN-` so
  the dashboard can visually flag synthetic data.

**Acceptance test:** a notebook cell (`notebooks/01_data_loading.ipynb`) that calls
all four loaders on sample files in `data/raw/` and prints row counts / shapes
without error.

---

## 2. `src/detection/` — Oil spill detection (steps 2–3, Person 1)

**File: `src/detection/preprocess.py`**
- `preprocess_sar(image)`: apply speckle denoising (e.g. `cv2.fastNlMeansDenoising`
  or a Lee filter), normalize intensity to [0,1], and mask out land pixels using a
  coastline shapefile if available in `data/raw/`. Return the cleaned array.

**File: `src/detection/segmentation_model.py`**
- `SpillSegmentationModel` class wrapping a `segmentation-models-pytorch` U-Net
  (or your dataset's best-supported architecture — DeepLab/SegFormer are fine
  substitutes). Constructor loads weights from `checkpoint_path` if present,
  otherwise falls back to ImageNet-pretrained encoder + randomly initialized
  decoder (still usable for a live demo, just lower accuracy — log a warning).
- `.predict(image)` returns a binary mask (`np.ndarray`, same H×W as input) plus a
  scalar confidence (mean pixel probability over the predicted spill region).
- Include a minimal training script or note in a docstring for how the team should
  fine-tune this if labeled data is available — but the class itself must work
  out-of-the-box in inference mode for the demo even without fine-tuning.

**File: `src/detection/lookalike_filter.py`**
- `classify_dark_region(region_features) -> bool`: implement as a small
  classical ML classifier (logistic regression or gradient-boosted trees via
  `scikit-learn`) trained on: texture (GLCM contrast/homogeneity), mean backscatter
  intensity, shape compactness, area, distance from coast, and local wind speed
  (low wind commonly causes look-alikes). If no labeled look-alike data exists,
  implement sensible **rule-based fallback thresholds** instead (e.g. compactness
  below X and wind speed below Y ⇒ likely look-alike) and clearly comment that
  this is the fallback path — this must not block the demo.

**File: `src/detection/spill_geometry.py`**
- `compute_geometry(mask, lat, lon)`: use `skimage.measure` + `shapely` to extract
  the largest connected component, compute area (km², using proper geodesic area,
  not pixel count × constant), perimeter (km), bounding box, centroid (lat/lon),
  and an elongation/compactness ratio (used later by age estimation). Return a
  dict, e.g. `{"area_km2":..., "perimeter_km":..., "centroid": (lat, lon),
  "bbox":..., "compactness":..., "confidence":...}`.

**Acceptance test:** given one sample SAR image, the pipeline prints something
equivalent to:
```
Oil Spill Detected
Confidence: 94.2%
Area: 18.6 km²
Perimeter: 31.4 km
Centroid: 18.43°N, 70.82°E
```

---

## 3. `src/age_estimation/` — Spill age (step 4, Person 2)

**File: `src/age_estimation/age_model.py`**
- `estimate_spill_age(spill_geometry, wind, currents) -> (age_low_hr, age_high_hr, confidence)`.
- Implement as a **physics-informed estimate**, not a black-box regressor, unless
  you have real historical age-labeled data:
  ```
  estimated_displacement ≈ f(spill elongation, fragmentation, area growth assumptions)
  estimated_drift_velocity ≈ weighted combination of current_speed and
                              (wind_speed × ~3% wind-drift factor, standard
                              oil-spill-modeling approximation)
  age ≈ estimated_displacement / estimated_drift_velocity
  ```
- Widen the range based on how much wind/current data is missing or how irregular
  the spill shape is (more fragmentation ⇒ wider uncertainty band, since a
  freshly-released spill is typically more compact and an older one more
  fragmented/elongated).
- Return a tuple, never a single point estimate, e.g. `(5.0, 7.0, 0.72)`.

**Acceptance test:** printed output like:
```
Estimated Spill Age: 5–7 hours   Confidence: 72%
```

---

## 4. `src/drift/` — Drift & hindcast model (steps 5–6, Person 2)

**File: `src/drift/particle_model.py`**
- `initialize_particles(spill_polygon, n_particles=500)`: sample `n_particles`
  points uniformly inside the polygon (`shapely` + rejection sampling or
  `geopandas.GeoSeries.sample_points`). Return an array of (lat, lon) pairs.

**File: `src/drift/forward_simulation.py`**
- `simulate_forward(particles, currents, wind, waves=None, hours=(1,3,6,12))`:
  advect each particle by `velocity = current_vector + wind_drift_factor *
  wind_vector (+ wave_stokes_drift if waves provided)`, using simple Euler
  integration with a small timestep (e.g. 10–15 min steps) up to each requested
  hour mark. Interpolate current/wind fields spatially (nearest-neighbor or
  bilinear from the xarray grid) at each particle's current position each step.
  Return a dict `{hour: array_of_particle_positions}`.

**File: `src/drift/backward_hindcast.py`**
- `hindcast_origin(observed_spill, currents, wind, waves=None, hours=(1,3,6))`:
  run the same particle advection but with velocity vectors **negated** (reverse
  time), starting from the observed spill's particle positions. At each
  candidate hour, compute the particle cloud's centroid and spread. Return:
  ```python
  {
    "estimated_origin": (lat, lon),
    "origin_uncertainty_km": float,   # e.g. std-dev of particle spread converted to km
    "release_window": (start_time, end_time),  # derived from age estimate + hindcast hour
  }
  ```

**Acceptance test:** printed output like:
```
Likely release window: 11:30–13:30
Estimated origin: 18.40°N, 70.75°E   (±4.2 km)
```
plus a forward trajectory (+1h/+3h/+6h/+12h) for the forecasting view.

---

## 5. `src/ais/` — Vessel correlation (steps 7–8, Person 3)

**File: `src/ais/correlation.py`**
- `find_candidate_vessels(origin_lat, origin_lon, event_time, ais_df,
  radius_km=50, time_window_hours=6)`: filter `ais_df` to pings within
  `radius_km` (use `src/utils/geo_utils.haversine_km`) of the origin AND within
  `time_window_hours` of `event_time`. Return the **unique vessels** (grouped by
  `mmsi`), each with their closest-approach distance and time delta to the
  origin/event_time.

**File: `src/ais/trajectory.py`**
- `reconstruct_trajectory(mmsi, ais_df)`: sort that vessel's pings by timestamp,
  return an ordered list of (lat, lon, timestamp, speed, heading).
- `trajectory_intersects_origin(trajectory, origin_lat, origin_lon, tolerance_km=5)`:
  interpolate the trajectory as a `shapely.LineString` and check whether any
  point along it (not just AIS pings, but interpolated positions between them)
  passes within `tolerance_km` of the origin. Return `(bool, closest_distance_km)`.

**File: `src/ais/behaviour_features.py`**
- `extract_behaviour_features(trajectory)`: compute
  - speed anomaly (deviation from the vessel's own median speed, and from typical
    speed for its `vessel_type`)
  - heading change (max delta-heading between consecutive pings)
  - unexpected stop (speed drops near-zero mid-route)
  - route deviation (perpendicular distance from a great-circle line between
    trajectory start/end)
  - AIS gaps (time deltas between consecutive pings exceeding a threshold, e.g.
    >30 min, especially if the gap occurs near the estimated origin/time — this
    is a key suspicious signal, flag it explicitly as `ais_gap_near_origin: bool`)
  Return a flat feature dict.

**Acceptance test:** for the sample scenario, prints a ranked-by-distance
candidate list like:
```
Vessel A → 2.1 km
Vessel D → 4.5 km
Vessel B → 8.7 km
Vessel C → 31 km
```

---

## 6. `src/scoring/` — Suspect scoring (step 8, Person 3)

**File: `src/scoring/suspect_scoring.py`**
- `score_vessel(features, weights)`: normalize each raw feature into a [0,1]
  sub-score (closer/sooner/more-intersecting/more-anomalous ⇒ higher), then combine
  using the weights from `config.yaml`:
  ```
  score = 0.30*spatial + 0.25*temporal + 0.20*trajectory
        + 0.10*behaviour + 0.10*ais_anomaly + 0.05*vessel_relevance
  ```
  Return a 0–100 score. Document the normalization function for each sub-score
  (e.g. spatial: `max(0, 1 - distance_km/radius_km)`).
- `explain_score(vessel_id, features) -> list[str]`: generate 3–6 human-readable
  evidence bullets in the exact style the dashboard needs, e.g.:
  ```python
  ["Passed 2.1 km from estimated origin",
   "Time matched release window",
   "Trajectory intersected probable origin",
   "Speed anomaly detected",
   "AIS gap observed near origin"]
  ```
  Only include a bullet if that sub-feature actually crossed a meaningful
  threshold — don't pad the list with filler for low-relevance vessels.

**Acceptance test:** ranked vessel table with scores 0–100 and a `explain_score`
call for the top vessel producing the bullet list above.

---

## 7. `src/pipeline/run_pipeline.py` — Orchestration (Person 4, steps 6 & 9)

Implement `run(image_path)` to call, in order:
1. `data.loaders` → load satellite/AIS/ocean/weather for the configured region
2. `detection.preprocess` → `detection.segmentation_model` → `detection.lookalike_filter`
   → `detection.spill_geometry`
3. `age_estimation.age_model`
4. `drift.particle_model` → `drift.backward_hindcast` (origin) → `drift.forward_simulation` (forecast)
5. `ais.correlation` → `ais.trajectory` → `ais.behaviour_features`
6. `scoring.suspect_scoring` (score + explain for every candidate vessel)
7. Assemble and return a single result dict/JSON containing everything the dashboard
   needs (spill geometry, age, origin, trajectories, ranked vessels with evidence).

Wrap each stage in a try/except that logs a warning and falls back per
`config.yaml` rather than crashing the whole run — e.g. if wave data load fails,
continue drift simulation with `waves=None`.

Also add a `--mock` CLI flag that runs the full pipeline on bundled synthetic
data (spill + `synthetic_ais.py`) so the dashboard can be demoed with zero real
data files present — this is your safety net for the actual presentation.

---

## 8. `dashboard/` — React UI (steps 9–10, Person 4)

**`dashboard/components/spill_panel.py`**: left sidebar card — date, time, region,
detected ✓/✗, confidence %, area km², estimated age range.

**`dashboard/components/map_view.py`**: main map using `folium` or `pydeck` —
layers (toggleable) for: spill polygon, estimated origin marker, backward
hindcast trail, forward forecast trail, AIS vessel tracks (color-coded by score).

**`dashboard/components/vessel_panel.py`**: right sidebar — ranked vessel list
with scores; clicking a vessel expands the evidence bullets from
`explain_score` plus the numeric "Attribution Score: NN/100" and a
"Confidence: Low/Medium/High" label derived from how many strong evidence
signals fired.

**`dashboard/app.py`**: wires the above together, calls
`pipeline.run_pipeline.run()` (or the `--mock` path) on load/on file upload,
shows a loading spinner, and handles the no-data-available case by defaulting
to the mock/synthetic demo scenario so the app never shows a blank screen.

---

## 9. Testing (step 10)

**`tests/test_pipeline.py`**: implement smoke tests (pytest) for at minimum:
- a real spill image with synthetic AIS
- a real spill image with real AIS (if available)
- a known false-positive dark region (should NOT be classified as oil, or should
  be flagged low-confidence)
- two different spill locations
Each test only needs to assert the pipeline **completes without raising** and
returns a well-formed result dict — not that the science is perfectly accurate.

---

## 10. Definition of done

The MVP is complete when `react run dashboard/app.py` (or
`python -m src.pipeline.run_pipeline --mock`) produces, end-to-end, without
manual intervention:

```
🛢️ Potential Responsible Vessel: Vessel X
Attribution Score: 87/100
Confidence: Medium-High

Evidence:
• Passed 2.1 km from estimated origin
• Time matched release window
• Trajectory intersected probable origin
• Behavioural anomaly detected
• AIS gap observed near origin
```

along with the map view showing spill polygon, origin, trajectories, and AIS
tracks, and the spill summary panel showing confidence/area/age.

---

## How to use this prompt

Give the coding agent one section (2–9) at a time, in order, and tell it:
*"Implement `<file>` per section N of CODING_PROMPT.md, keeping the existing
docstring and function signatures intact, and update
`notebooks/01_data_loading.ipynb` / `tests/test_pipeline.py` if relevant."*
This keeps changes reviewable and prevents the agent from reworking the whole
scaffold structure you already committed.
