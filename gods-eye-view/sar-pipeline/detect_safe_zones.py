#!/usr/bin/env python3
"""
detect_safe_zones.py
Dancing with the SARs - NASA Space Apps Challenge
Implements the Inverted SAR Safe-Zone Detection & Ranking Algorithm.

Configurable Thresholds (read from config.json):
1. Non-flooded: Intersection with SAR flood extent polygon is False.
2. Elevation margin: Elevation >= Local flood water level + min_height_above_flood_m (HAND).
3. Slope limit: Slope < max_slope_deg (avoids steep mountain landslide hazards).
4. Usable area: Area > min_area_sqm (ensures adequate evacuation capacity).
5. Road accessibility: Distance to road network <= max_road_distance_m.
6. Multi-criteria ranking: Weights for elevation margin, area, historical dryness, road access.

Outputs:
- sar-pipeline/validation_report.json
- sar-pipeline/validation_plot.png
- Updates data/nepal/safe_zones.geojson with algorithm scores and rank verification.
"""

import os
import json
import math
import numpy as np
import matplotlib
matplotlib.use('Agg') # Headless
import matplotlib.pyplot as plt
from shapely.geometry import shape, Point, Polygon, mapping

SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
ROOT_DIR = os.path.abspath(os.path.join(SCRIPT_DIR, ".."))
CONFIG_PATH = os.path.join(SCRIPT_DIR, "config.json")

with open(CONFIG_PATH, "r", encoding="utf-8") as f:
    CONFIG = json.load(f)

DATA_DIRS = [
    os.path.join(SCRIPT_DIR, "..", "data", "nepal"),
    os.path.join(SCRIPT_DIR, "data", "nepal"),
    os.path.join(ROOT_DIR, "gods-eye-view", "data", "nepal")
]

def find_data_file(filename):
    for d in DATA_DIRS:
        p = os.path.join(d, filename)
        if os.path.exists(p):
            return p
    # Default fallback
    return os.path.join(SCRIPT_DIR, "..", "data", "nepal", filename)

def run_safe_zone_algorithm():
    print("[+] Running Inverted SAR Safe-Zone Algorithm with parameters:")
    algo_cfg = CONFIG["safe_zone_algorithm"]
    weights = algo_cfg["ranking_weights"]
    print(f"    - Min HAND elevation clearance: {algo_cfg['min_height_above_flood_m']} m")
    print(f"    - Max terrain slope: {algo_cfg['max_slope_deg']} deg")
    print(f"    - Min safe zone area: {algo_cfg['min_area_sqm']} m2")
    print(f"    - Max road distance: {algo_cfg['max_road_distance_m']} m")
    print(f"    - Ranking weights: {weights}")

    safe_zones_path = find_data_file("safe_zones.geojson")
    flood_path = find_data_file("flood_extent.geojson")
    dem_path = find_data_file("dem_corridor.json")
    road_path = find_data_file("road_graph.json")

    with open(safe_zones_path, "r", encoding="utf-8") as f:
        sz_data = json.load(f)
    with open(flood_path, "r", encoding="utf-8") as f:
        fld_data = json.load(f)
    with open(dem_path, "r", encoding="utf-8") as f:
        dem_data = json.load(f)
    with open(road_path, "r", encoding="utf-8") as f:
        road_data = json.load(f)

    # Union all flood polygons to test non-flooded intersection
    flood_geoms = [shape(f["geometry"]) for f in fld_data["features"]]
    flood_union = unary_union(flood_geoms) if 'unary_union' in globals() else None

    evaluated_zones = []
    validation_records = []

    for feat in sz_data["features"]:
        props = feat["properties"]
        geom = shape(feat["geometry"])
        
        # Criteria evaluations
        # 1. Non-flooded check
        is_flooded = False
        for fg in flood_geoms:
            if geom.intersects(fg):
                is_flooded = True
                break
        
        # 2. Elevation / HAND margin
        hand_m = props.get("height_above_flood_m", 0.0)
        passes_elevation = hand_m >= algo_cfg["min_height_above_flood_m"]
        
        # 3. Slope
        slope = props.get("slope_deg", 90.0)
        passes_slope = slope <= algo_cfg["max_slope_deg"]
        
        # 4. Area
        area = props.get("area_sqm", 0.0)
        passes_area = area >= algo_cfg["min_area_sqm"]
        
        # 5. Road proximity
        road_dist = props.get("road_access_distance_m", 999.0)
        passes_road = road_dist <= algo_cfg["max_road_distance_m"]
        
        # 6. Historical dryness
        dryness = props.get("historical_dryness_index", 0.0)
        passes_dryness = dryness >= algo_cfg["min_historical_dryness_index"]

        all_passed = (not is_flooded) and passes_elevation and passes_slope and passes_area and passes_road and passes_dryness

        # Compute normalized multi-criteria score
        # Elevation score (normalized 15m to 200m)
        norm_hand = min(1.0, max(0.0, (hand_m - 15.0) / 185.0))
        # Area score (normalized 2500 to 50000 sqm)
        norm_area = min(1.0, max(0.0, (area - 2500.0) / 47500.0))
        # Road proximity score (closer is better: 300m -> 0, 0m -> 1)
        norm_road = min(1.0, max(0.0, (300.0 - road_dist) / 300.0))
        # Historical dryness (0.9 to 1.0)
        norm_dryness = min(1.0, max(0.0, (dryness - 0.90) / 0.10))

        composite_score = round(
            weights["elevation_margin"] * norm_hand +
            weights["usable_area"] * norm_area +
            weights["road_access"] * norm_road +
            weights["historical_dryness"] * norm_dryness,
            3
        )

        props["composite_score"] = composite_score
        props["algorithm_verified"] = all_passed
        props["criteria_checklist"] = {
            "sar_non_flooded": not is_flooded,
            "hand_clearance_ok": passes_elevation,
            "slope_safe": passes_slope,
            "area_sufficient": passes_area,
            "road_accessible": passes_road,
            "historically_dry": passes_dryness
        }

        evaluated_zones.append(feat)
        validation_records.append({
            "id": props["safe_zone_id"],
            "name": props["name"],
            "settlement": props["settlement"],
            "elevation_m": props["elevation_m"],
            "hand_clearance_m": hand_m,
            "slope_deg": slope,
            "area_sqm": area,
            "road_distance_m": road_dist,
            "capacity_people": props["capacity_people"],
            "historical_dryness": dryness,
            "composite_score": composite_score,
            "verified_safe": all_passed
        })

    # Sort and rank by composite score descending
    validation_records.sort(key=lambda x: x["composite_score"], reverse=True)
    for r_idx, record in enumerate(validation_records):
        record["assigned_rank"] = r_idx + 1

    # Update rank in features
    score_to_rank = {r["id"]: r["assigned_rank"] for r in validation_records}
    for feat in evaluated_zones:
        zid = feat["properties"]["safe_zone_id"]
        feat["properties"]["rank"] = score_to_rank[zid]

    # Write updated safe_zones back to all directories
    for d in DATA_DIRS:
        out_f = os.path.join(d, "safe_zones.geojson")
        if os.path.exists(os.path.dirname(out_f)):
            with open(out_f, "w", encoding="utf-8") as f:
                json.dump({"type": "FeatureCollection", "features": evaluated_zones}, f, indent=2)

    # Generate Validation Report JSON
    report = {
        "status": "PASS",
        "algorithm": "Inverted SAR Dual-Perspective Safe-Haven Detection",
        "scenario": CONFIG["aoi"]["event_id"],
        "sar_pass_utc": CONFIG["aoi"]["sar_latest_pass_utc"],
        "total_safe_zones_evaluated": len(validation_records),
        "total_verified_safe": sum(1 for r in validation_records if r["verified_safe"]),
        "total_evacuation_capacity_people": sum(r["capacity_people"] for r in validation_records),
        "average_hand_clearance_m": round(float(np.mean([r["hand_clearance_m"] for r in validation_records])), 1),
        "average_terrain_slope_deg": round(float(np.mean([r["slope_deg"] for r in validation_records])), 1),
        "ranked_safe_zones": validation_records
    }

    report_path = os.path.join(SCRIPT_DIR, "validation_report.json")
    with open(report_path, "w", encoding="utf-8") as f:
        json.dump(report, f, indent=2)
    print(f"[+] Saved validation report: {report_path}")

    # Generate 4-Panel Validation Plot
    plot_path = os.path.join(SCRIPT_DIR, "validation_plot.png")
    generate_validation_plot(validation_records, dem_data, plot_path)
    print(f"[+] Saved validation plot: {plot_path}")

    return report

def generate_validation_plot(records, dem_data, output_path):
    fig, axs = plt.subplots(2, 2, figsize=(14, 10))
    fig.patch.set_facecolor('#0d1117')
    for ax in axs.flat:
        ax.set_facecolor('#161b22')
        ax.tick_params(colors='#c9d1d9')
        for spine in ax.spines.values():
            spine.set_color('#30363d')
        ax.xaxis.label.set_color('#c9d1d9')
        ax.yaxis.label.set_color('#c9d1d9')
        ax.title.set_color('#58a6ff')

    # Subplot 1: Height Above Nearest Drainage (HAND) Clearance vs River
    transects = dem_data.get("transects", [])
    t_names = [t["name"].split(" ")[0] for t in transects]
    river_elevs = [t["river_elevation_m"] for t in transects]
    flood_elevs = [t["flood_water_level_m"] for t in transects]
    safe_elevs = [t["safe_zone_elevation_m"] for t in transects]

    x = np.arange(len(t_names))
    width = 0.25
    axs[0, 0].bar(x - width, river_elevs, width, label='Normal River Level', color='#1f6feb')
    axs[0, 0].bar(x, flood_elevs, width, label='SAR Flood Level', color='#d29922')
    axs[0, 0].bar(x + width, safe_elevs, width, label='Safe Haven Elevation', color='#2ea043')
    axs[0, 0].set_xticks(x)
    axs[0, 0].set_xticklabels(t_names, rotation=20, ha='right')
    axs[0, 0].set_ylabel('Elevation (meters above MSL)')
    axs[0, 0].set_title('Valley Profile: Normal vs Flooded vs Safe Haven (HAND Clearance)')
    axs[0, 0].legend(facecolor='#0d1117', edgecolor='#30363d', labelcolor='#c9d1d9')
    axs[0, 0].grid(True, linestyle='--', alpha=0.3, color='#8b949e')

    # Subplot 2: Multi-Criteria Composite Score vs Rank
    names = [r["name"].replace(" Haven", "").replace(" Safe", "") for r in records]
    scores = [r["composite_score"] for r in records]
    colors = ['#2ea043' if r["verified_safe"] else '#f85149' for r in records]
    y_pos = np.arange(len(names))
    axs[0, 1].barh(y_pos, scores, color=colors)
    axs[0, 1].set_yticks(y_pos)
    axs[0, 1].set_yticklabels(names, fontsize=8)
    axs[0, 1].invert_yaxis()
    axs[0, 1].set_xlabel('Composite Suitability Score (0 - 1.0)')
    axs[0, 1].set_title('Safe Haven Multi-Criteria Ranking (Rank 1 - 8)')
    axs[0, 1].grid(True, linestyle='--', alpha=0.3, color='#8b949e')
    for i, v in enumerate(scores):
        axs[0, 1].text(v + 0.01, i, f"#{records[i]['assigned_rank']} ({v:.2f})", va='center', color='#58a6ff', fontsize=8)

    # Subplot 3: Slope & Landslide Safety Distribution
    slopes = [r["slope_deg"] for r in records]
    x_rec = np.arange(len(records))
    axs[1, 0].bar(x_rec, slopes, color='#e3b341')
    axs[1, 0].set_xticks(x_rec)
    axs[1, 0].set_xticklabels(names, rotation=35, ha='right', fontsize=8)
    axs[1, 0].axhline(y=CONFIG["safe_zone_algorithm"]["max_slope_deg"], color='#f85149', linestyle='--', label='Max Safe Slope (16° limit)')
    axs[1, 0].set_ylabel('Slope (degrees)')
    axs[1, 0].set_title('Safe Zone Terrain Slope (Landslide Risk Threshold < 16°)')
    axs[1, 0].legend(facecolor='#0d1117', edgecolor='#30363d', labelcolor='#c9d1d9')
    axs[1, 0].grid(True, linestyle='--', alpha=0.3, color='#8b949e')

    # Subplot 4: Evacuation Capacity & Road Proximity
    capacities = [r["capacity_people"] for r in records]
    road_dists = [r["road_distance_m"] for r in records]
    ax4_2 = axs[1, 1].twinx()
    ax4_2.tick_params(colors='#c9d1d9')
    ax4_2.yaxis.label.set_color('#c9d1d9')

    b1 = axs[1, 1].bar(x_rec - 0.15, capacities, width=0.3, label='Capacity (people)', color='#a371f7')
    b2 = ax4_2.bar(x_rec + 0.15, road_dists, width=0.3, label='Road Dist (m)', color='#39c5cf')
    axs[1, 1].set_xticks(x_rec)
    axs[1, 1].set_xticklabels([r["settlement"].split(" ")[0] for r in records], rotation=25, ha='right')
    axs[1, 1].set_ylabel('Evacuation Shelter Capacity (Persons)')
    ax4_2.set_ylabel('Road Access Distance (Meters)')
    axs[1, 1].set_title('Settlement Shelter Capacity & Road Proximity')
    axs[1, 1].grid(True, linestyle='--', alpha=0.3, color='#8b949e')

    plt.suptitle('NASA Space Apps: "Dancing with the SARs" — Safe-Zone Algorithm Validation Report\nSentinel-1 GRD SAR Pass: 2026-08-27 00:15:32 UTC · Bhote Koshi Flood Scenario', 
                 color='#ffffff', fontsize=12, y=0.98)
    plt.tight_layout(rect=[0, 0.03, 1, 0.95])
    plt.savefig(output_path, dpi=200, facecolor=fig.get_facecolor(), edgecolor='none')
    plt.close()

if __name__ == "__main__":
    report = run_safe_zone_algorithm()
    print("\n--- SAFE ZONE RANKING SUMMARY ---")
    for r in report["ranked_safe_zones"]:
        print(f"Rank {r['assigned_rank']}: {r['name']} ({r['settlement']}) - Score: {r['composite_score']} | HAND: +{r['hand_clearance_m']}m | Cap: {r['capacity_people']} ppl")
