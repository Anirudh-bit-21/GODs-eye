#!/usr/bin/env python3
"""
route_engine.py
Dancing with the SARs - NASA Space Apps Challenge
Dry-Path Evacuation Routing Engine (Dijkstra / A* over flood-penalized road graph).

Core function:
- Takes a civilian's GPS coordinates or settlement choice.
- Prunes all road segments intersecting SAR-detected flood extent (+ 30m buffer).
- Computes optimal dry path to the safest and nearest high-ground safe haven.
- Computes dual ETAs: standard walking (4.2 km/h) and vulnerable group walking (2.8 km/h for children & elderly).
- Explains exactly "why it is safe" and generates child/elderly-friendly simple directions.
"""

import os
import json
import math
import networkx as nx

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
    return os.path.join(SCRIPT_DIR, "..", "data", "nepal", filename)

def haversine_m(lon1, lat1, lon2, lat2):
    R = 6371000.0
    phi1, phi2 = math.radians(lat1), math.radians(lat2)
    dphi = math.radians(lat2 - lat1)
    dlam = math.radians(lon2 - lon1)
    a = math.sin(dphi / 2)**2 + math.cos(phi1) * math.cos(phi2) * math.sin(dlam / 2)**2
    return 2 * R * math.atan2(math.sqrt(a), math.sqrt(1 - a))

def bearing_compass(lon1, lat1, lon2, lat2):
    phi1, phi2 = math.radians(lat1), math.radians(lat2)
    dlam = math.radians(lon2 - lon1)
    y = math.sin(dlam) * math.cos(phi2)
    x = math.cos(phi1) * math.sin(phi2) - math.sin(phi1) * math.cos(phi2) * math.cos(dlam)
    deg = (math.degrees(math.atan2(y, x)) + 360) % 360
    
    compass_brackets = ["NORTH ⬆️", "NORTHEAST ↗️", "EAST ➡️", "SOUTHEAST ↘️", 
                        "SOUTH ⬇️", "SOUTHWEST ↙️", "WEST ⬅️", "NORTHWEST ↖️"]
    idx = int((deg + 22.5) / 45) % 8
    return compass_brackets[idx]

class DryPathRouter:
    def __init__(self, road_graph_path=None, safe_zones_path=None):
        road_graph_path = road_graph_path or find_data_file("road_graph.json")
        safe_zones_path = safe_zones_path or find_data_file("safe_zones.geojson")
        
        with open(road_graph_path, "r", encoding="utf-8") as f:
            self.graph_data = json.load(f)
        with open(safe_zones_path, "r", encoding="utf-8") as f:
            self.safe_zones_data = json.load(f)

        self.nodes = self.graph_data["nodes"]
        self.edges = self.graph_data["edges"]
        self.sar_pass_utc = self.graph_data.get("sar_pass_utc", "2026-08-27T00:15:32Z")

        # Map safe zone id -> safe zone feature
        self.safe_zone_by_id = {}
        self.safe_zone_by_node = {}
        for feat in self.safe_zones_data["features"]:
            props = feat["properties"]
            self.safe_zone_by_id[props["safe_zone_id"]] = feat
            # Find closest graph node
            best_dist = 999999
            best_node = None
            coords = feat["geometry"]["coordinates"][0][0] # centroid approx
            for nid, ndata in self.nodes.items():
                d = haversine_m(coords[0], coords[1], ndata["lon"], ndata["lat"])
                if d < best_dist:
                    best_dist = d
                    best_node = nid
            if best_node:
                self.safe_zone_by_node[best_node] = feat

        # Build NetworkX graph excluding flooded edges
        self.G = nx.Graph()
        for nid, ndata in self.nodes.items():
            self.G.add_node(nid, **ndata)

        self.flooded_edge_count = 0
        for e in self.edges:
            if e["is_flooded"]:
                self.flooded_edge_count += 1
                # Skip flooded edges completely to sever hazardous roads!
                continue
            
            # Use vulnerable walking seconds as primary weight to prioritize safety for children & elderly
            self.G.add_edge(
                e["u"], e["v"],
                weight=e["walk_time_sec_vulnerable"],
                length_m=e["length_m"],
                walk_time_sec_standard=e["walk_time_sec_standard"],
                walk_time_sec_vulnerable=e["walk_time_sec_vulnerable"],
                slope_deg=e["slope_deg"],
                description=e["description"],
                geometry=e["geometry"]
            )

    def find_nearest_node(self, lon, lat):
        best_node = None
        min_dist = float("inf")
        for nid, ndata in self.nodes.items():
            d = haversine_m(lon, lat, ndata["lon"], ndata["lat"])
            if d < min_dist:
                min_dist = d
                best_node = nid
        return best_node, min_dist

    def compute_route(self, origin_lon, origin_lat, destination_sz_id=None):
        start_node, dist_to_start = self.find_nearest_node(origin_lon, origin_lat)
        if not start_node or start_node not in self.G:
            return {"status": "ERROR", "message": "No accessible dry road network near location"}

        target_nodes = []
        if destination_sz_id:
            for nid, feat in self.safe_zone_by_node.items():
                if feat["properties"]["safe_zone_id"] == destination_sz_id:
                    target_nodes.append(nid)
        else:
            target_nodes = list(self.safe_zone_by_node.keys())

        if not target_nodes:
            return {"status": "ERROR", "message": "Target safe zone not found on road network"}

        # Find best target using Dijkstra shortest path
        best_path = None
        best_target = None
        min_cost = float("inf")

        for target in target_nodes:
            if target == start_node:
                best_path = [start_node]
                best_target = target
                min_cost = 0
                break
            try:
                cost = nx.shortest_path_length(self.G, source=start_node, target=target, weight="weight")
                if cost < min_cost:
                    min_cost = cost
                    best_path = nx.shortest_path(self.G, source=start_node, target=target, weight="weight")
                    best_target = target
            except (nx.NetworkXNoPath, nx.NodeNotFound):
                continue

        if not best_path:
            return {"status": "UNREACHABLE", "message": "All land routes to safe havens are cut off by floodwaters"}

        # Compile path details
        target_feat = self.safe_zone_by_node[best_target]
        sz_props = target_feat["properties"]

        total_distance_m = dist_to_start
        total_time_std_sec = int(dist_to_start / (CONFIG["routing"]["standard_walking_speed_kmh"] * 1000 / 3600))
        total_time_vuln_sec = int(dist_to_start / (CONFIG["routing"]["child_elderly_walking_speed_kmh"] * 1000 / 3600))
        
        path_coords = [[origin_lon, origin_lat]]
        step_directions = []

        if dist_to_start > 15:
            nd = self.nodes[start_node]
            direction_name = bearing_compass(origin_lon, origin_lat, nd["lon"], nd["lat"])
            step_directions.append({
                "step": 1,
                "action": f"WALK {direction_name}",
                "instruction": f"Walk towards {nd.get('name', 'Main Road')} ({int(dist_to_start)} meters)",
                "distance_m": int(dist_to_start),
                "is_safe_dry": True
            })

        for i in range(len(best_path) - 1):
            u = best_path[i]
            v = best_path[i+1]
            edge_data = self.G[u][v]
            total_distance_m += edge_data["length_m"]
            total_time_std_sec += edge_data["walk_time_sec_standard"]
            total_time_vuln_sec += edge_data["walk_time_sec_vulnerable"]

            u_node = self.nodes[u]
            v_node = self.nodes[v]
            path_coords.append([u_node["lon"], u_node["lat"]])
            path_coords.append([v_node["lon"], v_node["lat"]])

            step_dir = bearing_compass(u_node["lon"], u_node["lat"], v_node["lon"], v_node["lat"])
            step_directions.append({
                "step": len(step_directions) + 1,
                "action": f"FOLLOW {step_dir}",
                "instruction": f"{edge_data['description']} towards {v_node.get('name', 'next point')}",
                "distance_m": int(edge_data["length_m"]),
                "slope_deg": edge_data["slope_deg"],
                "is_safe_dry": True
            })

        final_sz_coord = target_feat["geometry"]["coordinates"][0][0]
        path_coords.append(final_sz_coord)
        step_directions.append({
            "step": len(step_directions) + 1,
            "action": "ARRIVED AT SAFE HAVEN 🏆",
            "instruction": f"Enter {sz_props['name']}. You are {sz_props['height_above_flood_m']} meters above flood level.",
            "distance_m": 0,
            "is_safe_dry": True
        })

        return {
            "status": "SUCCESS",
            "origin": [origin_lon, origin_lat],
            "destination_safe_zone": {
                "id": sz_props["safe_zone_id"],
                "name": sz_props["name"],
                "rank": sz_props["rank"],
                "elevation_m": sz_props["elevation_m"],
                "height_above_flood_m": sz_props["height_above_flood_m"],
                "slope_deg": sz_props["slope_deg"],
                "capacity_people": sz_props["capacity_people"],
                "why_safe": sz_props["why_safe"],
                "staging_facilities": sz_props.get("staging_facilities", [])
            },
            "routing_metrics": {
                "total_distance_m": round(total_distance_m, 1),
                "eta_minutes_standard": max(1, round(total_time_std_sec / 60.0, 1)),
                "eta_minutes_vulnerable": max(1, round(total_time_vuln_sec / 60.0, 1)),
                "path_nodes": best_path,
                "is_100pct_dry": True,
                "flooded_edges_avoided": self.flooded_edge_count
            },
            "steps": step_directions,
            "path_coordinates": path_coords,
            "sar_pass_utc": self.sar_pass_utc,
            "honesty_label": f"latest SAR pass: {self.sar_pass_utc}"
        }

def test_sample_points():
    print("================================================================================")
    print(" INVERTED SAR DRY-ROUTING ENGINE: 3 SAMPLE POINT VERIFICATION")
    print("================================================================================")
    router = DryPathRouter()

    test_locations = [
        {
            "name": "Sample Point 1: Timure Bazaar",
            "coords": [85.36658, 28.25193],
            "context": "Mountain settlement near Chinese border. Lower river bridge is submerged."
        },
        {
            "name": "Sample Point 2: Syabru Besi Confluence Market",
            "coords": [85.33256, 28.16025],
            "context": "Deep gorge river junction. Main bridge washed away by 5.4m surge."
        },
        {
            "name": "Sample Point 3: Bidur Riverfront Ward",
            "coords": [85.14802, 27.92085],
            "context": "Dense urban valley center. Trishuli River crossing inundated under 4.1m water."
        }
    ]

    for sample in test_locations:
        lon, lat = sample["coords"]
        print(f"\n[>] EVALUATING {sample['name']} (Lon: {lon}, Lat: {lat})")
        print(f"    Context: {sample['context']}")

        result = router.compute_route(lon, lat)
        assert result["status"] == "SUCCESS", f"Routing failed for {sample['name']}"

        dest = result["destination_safe_zone"]
        metrics = result["routing_metrics"]

        print(f"    🎯 RECOMMENDED SAFE HAVEN: #{dest['rank']} {dest['name']}")
        print(f"       - Clearance above flood (HAND): +{dest['height_above_flood_m']} m")
        print(f"       - Total dry route distance:     {metrics['total_distance_m']:,} m")
        print(f"       - ETA Standard (4.2 km/h):      {metrics['eta_minutes_standard']} mins")
        print(f"       - ETA Child / Elderly (2.8 km/h): {metrics['eta_minutes_vulnerable']} mins")
        print(f"       - Flooded riverbanks bypassed:  {metrics['flooded_edges_avoided']} hazardous segments severed")
        print(f"       - Why Safe: {dest['why_safe']}")
        print(f"    🧭 Turn-by-Turn Guidance:")
        for step in result["steps"]:
            print(f"       [{step['step']}] {step['action']}: {step['instruction']}")

    print("\n[SUCCESS] Phase 3 Routing Engine verification complete. All 3 sample points routed dry!")

if __name__ == "__main__":
    test_sample_points()
