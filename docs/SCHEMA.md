# "Dancing with the SARs" — Data Schemas & Honesty Protocol

> **Project:** "Inverted SAR" Dual-Perspective Flood Safe-Haven Platform  
> **Challenge:** NASA Space Apps Challenge — *Dancing with the SARs*  
> **Target Scenario:** Bhote Koshi / Trishuli River Flood Corridor, Nepal (`bhote-koshi-2026`)  
> **Coordinate Reference System:** WGS 84 (`EPSG:4326`), `[longitude, latitude]` for GeoJSON coordinates.

---

## 1. The Honesty Protocol (Mandatory)

Synthetic Aperture Radar (SAR) from ESA Sentinel-1 or NASA-ISRO NISAR is **not a continuous real-time video feed**. Sentinel-1 orbital passes revisit a given region every few days (or 6–12 days for a single constellation member).

### Rules for All Schemas, APIs, Docs, and UI:
1. **Never call SAR "real-time".**
2. **Every file, API response, and UI panel must carry an explicit `latest_sar_pass_utc` timestamp** formatted in ISO 8601 UTC (e.g. `2026-08-27T00:15:32Z`).
3. UI headers and cards must label the SAR layer as:
   ```text
   Latest SAR pass: 2026-08-27 00:15:32 UTC (Sentinel-1 GRD IW)
   ```
4. Only ancillary feeds (e.g. Open-Meteo rainfall, FIRMS fire hotspots, or USGS seismic alerts) may be termed "live" or "near-real-time".

---

## 2. Shared File Inventory (`/data/nepal/`)

| File Name | Format | Primary Role |
| :--- | :--- | :--- |
| `metadata.json` | JSON | AOI bounds, timestamps, dataset provenance, and honesty metadata. |
| `flood_extent.geojson` | GeoJSON FeatureCollection | SAR backscatter thresholded floodwater polygons along the river corridor. |
| `safe_zones.geojson` | GeoJSON FeatureCollection | Ranked, non-flooded, accessible high-ground havens with human-readable explanations. |
| `dry_microzones.geojson` | GeoJSON FeatureCollection | Historical flood-frequency guaranteed-dry micro-zones for relief supply staging. |
| `safe_corridors.geojson` | GeoJSON FeatureCollection | Dry road/path segments connecting settlements to safe havens. |
| `dem_corridor.json` | JSON | Clipped DEM elevation profile and cross-valley transects (Copernicus GLO-30 / SRTM). |
| `road_graph.json` | JSON | Graph network (nodes, edges, lengths, status, walk times) for routing engine. |

---

## 3. Schema Definitions

### 3.1. `metadata.json`
```json
{
  "scenario_id": "bhote-koshi-2026",
  "name": "Bhote Koshi / Trishuli Outburst Flood Corridor",
  "country": "Nepal",
  "district": "Rasuwa & Nuwakot",
  "bbox": [85.08, 27.84, 85.50, 28.38],
  "center": [85.25, 28.10],
  "event_date": "2026-08-26",
  "sar_reference_pass_utc": "2026-08-20T00:15:00Z",
  "sar_latest_pass_utc": "2026-08-27T00:15:32Z",
  "sar_sensor": "Sentinel-1 C-band SAR (GRD, IW mode, VV polarization)",
  "dem_source": "Copernicus GLO-30 / SRTM 30m",
  "road_source": "OpenStreetMap contributors (ODbL)",
  "permanent_water_mask": "JRC Global Surface Water (occurrence > 80%)",
  "honesty_rule": "Sentinel-1 revisits every few days; it is NOT a live video feed. In UI and docs, label it 'latest SAR pass: <date/time UTC>'. Never call SAR real-time."
}
```

---

### 3.2. `flood_extent.geojson`
```json
{
  "type": "FeatureCollection",
  "features": [
    {
      "type": "Feature",
      "geometry": {
        "type": "Polygon",
        "coordinates": [[[85.378, 28.279], [85.376, 28.277], "..."]]
      },
      "properties": {
        "feature_type": "flood_extent",
        "event_id": "bhote-koshi-2026",
        "sar_pass_utc": "2026-08-27T00:15:32Z",
        "sensor": "Sentinel-1 GRD IW VV",
        "backscatter_mean_db": -18.4,
        "backscatter_threshold_db": -16.0,
        "flood_water_elevation_m": 1812.5,
        "water_depth_estimate_m": 4.8,
        "severity": "critical",
        "water_type": "active_inundation"
      }
    }
  ]
}
```

---

### 3.3. `safe_zones.geojson`
```json
{
  "type": "FeatureCollection",
  "features": [
    {
      "type": "Feature",
      "geometry": {
        "type": "Polygon",
        "coordinates": [[[85.334, 28.162], [85.336, 28.164], "..."]]
      },
      "properties": {
        "safe_zone_id": "SZ-01-SYABRU-BESI-NORTH",
        "name": "Syabru Besi North Ridge Haven",
        "settlement_cluster": "Syabru Besi",
        "rank": 1,
        "composite_score": 0.94,
        "elevation_m": 1545.0,
        "height_above_flood_m": 128.0,
        "slope_deg": 6.5,
        "area_sqm": 24500,
        "capacity_people": 2400,
        "road_access_distance_m": 25.0,
        "historical_dryness_index": 0.99,
        "why_safe": "128m above peak river surge; slope under 7°; direct paved road access; 100% dry across 30-year satellite flood history.",
        "recommended_for": ["children", "older_adults", "general_evacuation", "emergency_shelter"],
        "staging_facilities": ["potable_water", "dry_food_rations", "power_banks_and_solar", "trauma_and_first_aid_medicine", "sanitation_kits"],
        "sar_pass_utc": "2026-08-27T00:15:32Z"
      }
    }
  ]
}
```

---

### 3.4. `dry_microzones.geojson` (Pre-Disaster Staging)
```json
{
  "type": "FeatureCollection",
  "features": [
    {
      "type": "Feature",
      "geometry": {
        "type": "Polygon",
        "coordinates": [[[85.297, 28.115], [85.299, 28.116], "..."]]
      },
      "properties": {
        "microzone_id": "MZ-02-DHUNCHE-STAGE",
        "name": "Dhunche Hospital High Staging Plateau",
        "elevation_m": 1980.0,
        "height_above_flood_m": 680.0,
        "slope_deg": 4.1,
        "historical_dry_frequency": 1.0,
        "staging_capacity_sqm": 8200,
        "target_supplies": [
          "5,000L Potable Water Cistern",
          "1,200 High-Calorie Meal Packs",
          "80x 20,000mAh Power Banks + 4x 200W Solar Mats",
          "Hypothermia & Water Purification Kits",
          "Portable Emergency Latrines"
        ],
        "nearest_road_access_m": 12.0,
        "sar_pass_utc": "2026-08-27T00:15:32Z"
      }
    }
  ]
}
```

---

### 3.5. `safe_corridors.geojson`
```json
{
  "type": "FeatureCollection",
  "features": [
    {
      "type": "Feature",
      "geometry": {
        "type": "LineString",
        "coordinates": [[85.332, 28.160], [85.333, 28.161], [85.334, 28.162]]
      },
      "properties": {
        "corridor_id": "SC-SYABRU-BESI-ACCESS",
        "name": "Syabru Besi Upper Evacuation Route",
        "origin_settlement": "Syabru Besi Bazaar",
        "destination_safe_zone_id": "SZ-01-SYABRU-BESI-NORTH",
        "distance_m": 620.0,
        "walk_time_min_standard": 8.8,
        "walk_time_min_vulnerable": 13.3,
        "status": "dry_safe",
        "surface": "paved_road",
        "min_clearance_above_flood_m": 35.0,
        "sar_pass_utc": "2026-08-27T00:15:32Z"
      }
    }
  ]
}
```

---

### 3.6. `road_graph.json`
```json
{
  "scenario": "bhote-koshi-2026",
  "sar_pass_utc": "2026-08-27T00:15:32Z",
  "nodes": {
    "N-TIMURE-01": {
      "id": "N-TIMURE-01",
      "lon": 85.36658,
      "lat": 28.25193,
      "elevation_m": 1689.0,
      "name": "Timure Center"
    }
  },
  "edges": [
    {
      "edge_id": "E-TIMURE-SYABRU-01",
      "u": "N-TIMURE-01",
      "v": "N-SYABRU-01",
      "length_m": 12400.0,
      "status": "dry",
      "is_flooded": false,
      "slope_deg": 3.8,
      "walk_time_sec_standard": 10600,
      "walk_time_sec_vulnerable": 15900,
      "geometry": [[85.36658, 28.25193], [85.33256, 28.16025]]
    }
  ],
  "stats": {
    "node_count": 48,
    "edge_count": 72,
    "dry_edge_count": 58,
    "flooded_edge_count": 14
  }
}
```

---

### 3.7. `dem_corridor.json`
```json
{
  "scenario": "bhote-koshi-2026",
  "source": "Copernicus GLO-30 / SRTM 30m Resampled",
  "bounds": [85.08, 27.84, 85.50, 28.38],
  "corridor_stats": {
    "min_elevation_m": 350.0,
    "max_elevation_m": 3820.0,
    "mean_river_gradient_pct": 2.4
  },
  "transects": [
    {
      "name": "Syabru Besi Valley Cross-Section",
      "center": [85.3325, 28.1602],
      "river_elevation_m": 1417.0,
      "flood_water_elevation_m": 1424.5,
      "safe_zone_elevation_m": 1545.0,
      "clearance_m": 120.5
    }
  ]
}
```

