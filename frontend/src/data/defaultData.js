// SagarDrishti Default Datasets & Fallbacks

export const defaultCategoriesData = {
  categories: {
    Oil: ['00001_oil.tif'],
    Lookalike: ['00001_lookalike.tif'],
    'No oil': ['00001_no_oil.tif'],
  },
  total_images: 3,
  has_real_dataset: true,
  presets: true,
};

export const defaultProactiveData = {
  sensitive_zones: [
    { id: 'zone_1', name: 'Laccadive Marine Sanctuary', lat: 10.5, lon: 72.5, radius_km: 30.0 },
    { id: 'zone_2', name: 'Mumbai Port Anchorage Zone', lat: 18.9, lon: 72.8, radius_km: 15.0 },
    { id: 'zone_3', name: 'Gulf of Kutch Eco-Sensitive Zone', lat: 22.5, lon: 69.5, radius_km: 40.0 },
    { id: 'zone_4', name: 'Malvan Marine Sanctuary', lat: 16.05, lon: 73.45, radius_km: 20.0 },
  ],
  watchlist: [
    {
      mmsi: 'SYN-998822101',
      vessel_type: 'Crude Oil Tanker',
      lat: 10.51,
      lon: 72.52,
      speed_knots: 0.5,
      heading: 135.0,
      risk_score: 85.0,
      zone: 'Laccadive Marine Sanctuary',
      watchlist: true,
      trajectory: [
        [10.30, 72.30, '2026-08-29T18:00:00Z', 12.0, 45.0],
        [10.40, 72.40, '2026-08-29T18:30:00Z', 11.5, 45.0],
        [10.51, 72.52, '2026-08-29T19:00:00Z', 0.5, 135.0],
        [10.53, 72.54, '2026-08-29T20:15:00Z', 4.0, 45.0],
      ],
      evidence: [
        'Sudden speed drop from 12.0 to 0.5 knots inside core reserve boundary',
        'Sharp 90-degree course alteration without navigational alert',
        'High environmental vulnerability risk profile for crude oil tanker',
      ],
    },
    {
      mmsi: 'SYN-774411993',
      vessel_type: 'Chemical Tanker',
      lat: 18.92,
      lon: 72.82,
      speed_knots: 0.2,
      heading: 180.0,
      risk_score: 70.0,
      zone: 'Mumbai Port Anchorage Zone',
      watchlist: true,
      trajectory: [
        [18.85, 72.75, '2026-08-29T18:00:00Z', 10.0, 60.0],
        [18.92, 72.82, '2026-08-29T18:45:00Z', 0.2, 180.0],
        [18.94, 72.85, '2026-08-29T20:00:00Z', 3.5, 60.0],
      ],
      evidence: [
        'Unexpected stationary loitering in Mumbai Port restricted channel',
        'AIS signal transmission gap detected during 45-minute window',
      ],
    },
    {
      mmsi: 'SYN-112233445',
      vessel_type: 'Container Ship',
      lat: 10.45,
      lon: 72.38,
      speed_knots: 14.6,
      heading: 30.0,
      risk_score: 35.0,
      zone: 'Laccadive Marine Sanctuary',
      watchlist: false,
      trajectory: [
        [10.38, 72.31, '2026-08-29T18:00:00Z', 14.5, 30.0],
        [10.42, 72.35, '2026-08-29T18:30:00Z', 14.2, 30.0],
        [10.45, 72.38, '2026-08-29T19:00:00Z', 14.6, 30.0],
      ],
      evidence: [],
    },
  ],
};

export const defaultPipelineResults = {
  spill_detected: true,
  confidence: 88,
  area_km2: 14.25,
  perimeter_km: 18.60,
  age_low: 3.5,
  age_high: 6.0,
  age_confidence: 82,
  centroid: [18.43, 70.82],
  estimated_origin: [18.37, 70.73],
  origin_uncertainty_km: 4.5,
  spill_polygon_coords: [
    [18.445, 70.805],
    [18.448, 70.835],
    [18.425, 70.840],
    [18.412, 70.815],
    [18.430, 70.798],
  ],
  hindcast_track: [
    [18.43, 70.82],
    [18.41, 70.79],
    [18.39, 70.76],
    [18.37, 70.73],
  ],
  forecast_tracks: {
    '1': [
      [18.435, 70.825],
      [18.438, 70.828],
      [18.432, 70.822],
      [18.440, 70.830],
      [18.436, 70.826],
    ],
    '3': [
      [18.445, 70.835],
      [18.448, 70.838],
      [18.442, 70.832],
      [18.450, 70.840],
      [18.446, 70.836],
    ],
    '6': [
      [18.460, 70.850],
      [18.463, 70.854],
      [18.458, 70.848],
      [18.466, 70.856],
      [18.462, 70.852],
    ],
    '12': [
      [18.485, 70.875],
      [18.488, 70.880],
      [18.482, 70.872],
      [18.492, 70.884],
      [18.487, 70.878],
    ],
  },
  ranked_vessels: [
    {
      mmsi: 'SYN-998822101',
      vessel_type: 'Crude Oil Tanker',
      attribution_score: 77.8,
      closest_distance_km: 1.2,
      time_delta_hours: 0.5,
      confidence_level: 'High Probability',
      trajectory: [
        [18.35, 70.70, '2026-08-29T18:00:00Z', 12.0, 45.0],
        [18.39, 70.76, '2026-08-29T18:30:00Z', 11.5, 45.0],
        [18.43, 70.82, '2026-08-29T19:00:00Z', 0.5, 135.0],
        [18.48, 70.88, '2026-08-29T20:15:00Z', 4.0, 45.0],
      ],
      evidence: [
        'Crossed within 1.2km of origin centroid during release window',
        'Speed dropped from 12.0 to 0.5 knots during transit',
        'High historical spill risk profile for crude oil carrier',
      ],
    },
    {
      mmsi: 'SYN-445566778',
      vessel_type: 'Cargo Vessel',
      attribution_score: 52.4,
      closest_distance_km: 3.8,
      time_delta_hours: 1.8,
      confidence_level: 'Moderate Probability',
      trajectory: [
        [18.38, 70.65, '2026-08-29T18:00:00Z', 14.5, 30.0],
        [18.42, 70.72, '2026-08-29T18:30:00Z', 14.2, 30.0],
        [18.45, 70.78, '2026-08-29T19:00:00Z', 14.6, 30.0],
      ],
      evidence: [
        'Crossed within 3.8km of origin centroid',
        'Maintained constant 14.2 knots transit speed',
      ],
    },
    {
      mmsi: 'SYN-112233445',
      vessel_type: 'Container Ship',
      attribution_score: 41.2,
      closest_distance_km: 6.4,
      time_delta_hours: 2.5,
      confidence_level: 'Low Probability',
      trajectory: [
        [18.25, 70.80, '2026-08-29T18:00:00Z', 10.0, 60.0],
        [18.30, 70.85, '2026-08-29T18:45:00Z', 0.2, 180.0],
        [18.36, 70.90, '2026-08-29T20:00:00Z', 3.5, 60.0],
      ],
      evidence: ['Passed outside primary 5km uncertainty radius'],
    },
  ],
};

export function getFallbackSarPreview(imagePath = '') {
  const p = (imagePath || '').toLowerCase();
  if (p.includes('lookalike')) {
    return {
      image_path: imagePath,
      sar_image_base64: '/sample_assets/00001_lookalike_preview.png',
      mask_image_base64: '/sample_assets/00001_lookalike_mask.png',
      has_mask: true,
    };
  }
  if (p.includes('no oil') || p.includes('no_oil') || p.includes('clean')) {
    return {
      image_path: imagePath,
      sar_image_base64: '/sample_assets/00001_no_oil_preview.png',
      mask_image_base64: '/sample_assets/00001_no_oil_mask.png',
      has_mask: true,
    };
  }
  return {
    image_path: imagePath,
    sar_image_base64: '/sample_assets/00001_oil_preview.png',
    mask_image_base64: '/sample_assets/00001_oil_mask.png',
    has_mask: true,
  };
}
