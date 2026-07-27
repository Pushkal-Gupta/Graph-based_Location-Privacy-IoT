"""
Build a Real Beijing Road-Network Graph (OpenStreetMap via OSMnx)
=================================================================

Reviewer critique addressed: the 30x30 regular grid is not a real road network
(uniform degree 4, no dead-ends, no hierarchy, no one-way structure).  This
script replaces it with the *actual* central-Beijing drive network from
OpenStreetMap over the same bounding box, so the mechanisms are evaluated on
real topology.

To keep the graph compatible with the framework's all-pairs shortest-path layer
(and the adversary's distance matrix), OSM intersections are consolidated within
a distance tolerance, yielding a graph of ~1-2k nodes -- comparable in size to
the 900-node grid, but with realistic degree distribution, dead-ends, and road
hierarchy.

Outputs (same schema as city_graph_*.json so all downstream code just works):
    data/processed_data/real_graph_nodes.json   [{"id","x"=lon,"y"=lat}, ...]
    data/processed_data/real_graph_edges.json   [{"source","target","distance","travel_time"}, ...]
    data/processed_data/real_graph_meta.json     (bbox, node/edge counts, UTM crs)
    data/processed_data/real_graph_nodes_utm.npy (N x 2 projected coords, for map-matching)
"""

import os
import json
import numpy as np
import osmnx as ox
import networkx as nx

_HERE = os.path.dirname(os.path.abspath(__file__))
_OUT = os.path.join(_HERE, "..", "processed_data")

# Full grid bbox (used to download the raw network once, cached).
MIN_LAT, MAX_LAT = 39.8, 40.1
MIN_LON, MAX_LON = 116.2, 116.5
# OSMnx 2.x bbox order: (left, bottom, right, top) = (west, south, east, north).
BBOX = (MIN_LON, MIN_LAT, MAX_LON, MAX_LAT)

# Central-Beijing crop where the GeoLife trajectories concentrate (dense-core
# occupancy peaks around lat 39.98-40.0, lon 116.32-116.34).  Cropping here
# yields a clean ~2-3k-node real graph (vs. 11k+ for the full bbox), keeping the
# exact O(N^2) Bayesian adversary tractable while using genuine road topology.
CROP_LAT = (39.90, 40.05)
CROP_LON = (116.26, 116.41)
CROP_BBOX = (CROP_LON[0], CROP_LAT[0], CROP_LON[1], CROP_LAT[1])

CONSOLIDATE_TOLERANCE_M = 50    # merge intersections within this distance


_RAW_CACHE = os.path.join(_OUT, "_beijing_drive_raw.graphml")


def _get_raw(crop_bbox=None):
    """Download (once, cached) the raw drive network; optionally crop it."""
    if os.path.exists(_RAW_CACHE):
        print(f"Loading cached raw graph {_RAW_CACHE}")
        G = ox.load_graphml(_RAW_CACHE)
    else:
        print(f"Downloading Beijing drive network for bbox {BBOX} ...")
        G = ox.graph_from_bbox(BBOX, network_type="drive", simplify=True,
                               retain_all=False, truncate_by_edge=True)
        ox.save_graphml(G, _RAW_CACHE)
    print(f"  raw: {G.number_of_nodes()} nodes, {G.number_of_edges()} edges")
    if crop_bbox is not None:
        G = ox.truncate.truncate_graph_bbox(G, crop_bbox, truncate_by_edge=True)
        G = ox.truncate.largest_component(G, strongly=False)
        print(f"  cropped to {crop_bbox}: {G.number_of_nodes()} nodes, "
              f"{G.number_of_edges()} edges")
    return G


def _get_raw_projected(crop_bbox=None):
    return ox.project_graph(_get_raw(crop_bbox))


def build(tolerance=CONSOLIDATE_TOLERANCE_M, crop_bbox=CROP_BBOX):
    Gp = _get_raw_projected(crop_bbox)
    Gc = ox.consolidate_intersections(Gp, tolerance=tolerance,
                                      rebuild_graph=True, dead_ends=True,
                                      reconnect_edges=True)
    print(f"  consolidated (tol={tolerance}m): {Gc.number_of_nodes()} nodes, "
          f"{Gc.number_of_edges()} edges")

    # Undirected simple graph for the (undirected) privacy mechanisms.
    UG = ox.convert.to_undirected(Gc)

    # Unproject to lat/lon for the node coordinates.
    crs_utm = Gc.graph["crs"]
    Gc_ll = ox.project_graph(Gc, to_latlong=True)

    # Canonical 0..N-1 relabelling.
    osm_ids = list(UG.nodes())
    id_map = {osm: str(i) for i, osm in enumerate(osm_ids)}

    nodes_out, utm_coords = [], []
    for osm in osm_ids:
        nll = Gc_ll.nodes[osm]
        nutm = Gc.nodes[osm]
        nodes_out.append({"id": id_map[osm],
                          "x": float(nll["x"]),   # lon
                          "y": float(nll["y"])})  # lat
        utm_coords.append([float(nutm["x"]), float(nutm["y"])])

    edges_out = []
    seen = set()
    for u, v, data in UG.edges(data=True):
        su, sv = id_map[u], id_map[v]
        if su == sv:
            continue
        key = (min(su, sv), max(su, sv))
        if key in seen:
            continue
        seen.add(key)
        length = float(data.get("length", 0.0))
        if length <= 0:
            # Fallback: haversine between endpoints.
            length = _haversine_m(nodes_out[int(su)]["x"], nodes_out[int(su)]["y"],
                                  nodes_out[int(sv)]["x"], nodes_out[int(sv)]["y"])
        edges_out.append({"source": su, "target": sv,
                          "distance": round(length, 2),
                          "travel_time": int(length / 1.4)})

    os.makedirs(_OUT, exist_ok=True)
    with open(os.path.join(_OUT, "real_graph_nodes.json"), "w") as f:
        json.dump(nodes_out, f)
    with open(os.path.join(_OUT, "real_graph_edges.json"), "w") as f:
        json.dump(edges_out, f)
    np.save(os.path.join(_OUT, "real_graph_nodes_utm.npy"),
            np.array(utm_coords, dtype=float))

    # Degree stats on the SIMPLE (deduplicated) undirected graph -- this is the
    # graph the mechanisms actually run on (not the multigraph, whose parallel
    # edges would inflate degrees).
    import networkx as _nx
    _S = _nx.Graph()
    for n in nodes_out:
        _S.add_node(n["id"])
    for e in edges_out:
        _S.add_edge(e["source"], e["target"])
    degs = [d for _, d in _S.degree()]
    meta = {
        "bbox": {"min_lat": MIN_LAT, "max_lat": MAX_LAT,
                 "min_lon": MIN_LON, "max_lon": MAX_LON},
        "utm_crs": str(crs_utm),
        "n_nodes": len(nodes_out),
        "n_edges": len(edges_out),
        "consolidate_tolerance_m": tolerance,
        "degree_min": int(min(degs)), "degree_max": int(max(degs)),
        "degree_mean": float(np.mean(degs)),
        "degree_hist": {str(d): int((np.array(degs) == d).sum())
                        for d in sorted(set(degs))},
        "n_dead_ends": int((np.array(degs) == 1).sum()),
    }
    with open(os.path.join(_OUT, "real_graph_meta.json"), "w") as f:
        json.dump(meta, f, indent=2)

    print(f"\nReal graph saved: {len(nodes_out)} nodes, {len(edges_out)} edges")
    print(f"  degree: min={meta['degree_min']} max={meta['degree_max']} "
          f"mean={meta['degree_mean']:.2f}; dead-ends={meta['n_dead_ends']}")
    print(f"  (grid graph was uniform degree ~4, zero dead-ends)")
    return meta


def _haversine_m(lon1, lat1, lon2, lat2):
    import math
    R = 6_371_000
    p1, p2 = math.radians(lat1), math.radians(lat2)
    dphi = math.radians(lat2 - lat1)
    dlam = math.radians(lon2 - lon1)
    a = (math.sin(dphi / 2) ** 2 +
         math.cos(p1) * math.cos(p2) * math.sin(dlam / 2) ** 2)
    return 2 * R * math.atan2(math.sqrt(a), math.sqrt(1 - a))


if __name__ == "__main__":
    import sys
    tol = int(sys.argv[1]) if len(sys.argv) > 1 else CONSOLIDATE_TOLERANCE_M
    build(tol)
