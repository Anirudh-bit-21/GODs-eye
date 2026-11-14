#!/usr/bin/env python3
"""
verify_data.py
Validates offline files against SCHEMA.md rules and honesty timestamp requirements.
"""

import json
import glob
import os
import sys

def verify_all(data_dir):
    print(f"[+] Verifying datasets in {data_dir}...")
    files = glob.glob(os.path.join(data_dir, "*.*"))
    assert len(files) >= 7, f"Expected at least 7 files, found {len(files)}"
    
    for fpath in files:
        fname = os.path.basename(fpath)
        with open(fpath, "r", encoding="utf-8") as f:
            data = json.load(f)
        
        # Check honesty rule and latest SAR pass timestamp
        if fname.endswith(".geojson"):
            assert data.get("type") == "FeatureCollection", f"{fname} not FeatureCollection"
            assert len(data.get("features", [])) > 0, f"{fname} has no features"
            for feat in data["features"]:
                props = feat.get("properties", {})
                assert "sar_pass_utc" in props, f"{fname} feature missing sar_pass_utc"
                assert "honesty_label" in props, f"{fname} feature missing honesty_label"
            print(f" [OK] {fname}: {len(data['features'])} features (all carry SAR timestamp)")
        elif fname == "road_graph.json":
            nodes = data.get("nodes", {})
            edges = data.get("edges", [])
            stats = data.get("stats", {})
            assert len(nodes) > 0, "No nodes in road graph"
            assert len(edges) > 0, "No edges in road graph"
            assert stats["flooded_edge_count"] > 0, "No flooded edges found"
            assert stats["dry_edge_count"] > 0, "No dry edges found"
            assert "sar_pass_utc" in data, "road_graph missing sar_pass_utc"
            print(f" [OK] {fname}: {len(nodes)} nodes, {len(edges)} edges ({stats['dry_edge_count']} dry, {stats['flooded_edge_count']} flooded)")
        elif fname == "dem_corridor.json":
            transects = data.get("transects", [])
            assert len(transects) >= 5, "Expected at least 5 cross-valley transects"
            assert "sar_pass_utc" in data, "dem_corridor missing sar_pass_utc"
            print(f" [OK] {fname}: {len(transects)} cross-valley transects")
        elif fname == "metadata.json":
            assert "sar_latest_pass_utc" in data, "metadata missing sar_latest_pass_utc"
            assert "honesty_rule" in data, "metadata missing honesty_rule"
            print(f" [OK] {fname}: valid scenario metadata and honesty statement")

    print("[SUCCESS] All Phase 1 datasets fully verified and compliant.")

if __name__ == "__main__":
    d = sys.argv[1] if len(sys.argv) > 1 else "gods-eye-view/data/nepal"
    verify_all(d)
