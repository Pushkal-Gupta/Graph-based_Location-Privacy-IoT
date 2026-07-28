"""
Generic OSM drive-network graph builder (any city / bbox).
Usage: python3 build_osm_graph.py <prefix> <south> <west> <north> <east> [tolerance_m]
Produces (in ../processed_data):
  <prefix>_graph_nodes.json  [{"id","x"=lon,"y"=lat}]
  <prefix>_graph_edges.json  [{"source","target","distance","travel_time"}]
  <prefix>_graph_meta.json
  <prefix>_graph_nodes_utm.npy
Consolidates intersections to keep the graph at a pipeline-friendly size while
preserving real topology (variable degree, dead-ends, hierarchy).
"""
import os, sys, json, math, numpy as np, osmnx as ox, networkx as nx
_OUT = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "processed_data")


def _hav(lon1, lat1, lon2, lat2):
    R = 6_371_000; p1, p2 = math.radians(lat1), math.radians(lat2)
    dphi = math.radians(lat2-lat1); dl = math.radians(lon2-lon1)
    a = math.sin(dphi/2)**2 + math.cos(p1)*math.cos(p2)*math.sin(dl/2)**2
    return 2*R*math.atan2(math.sqrt(a), math.sqrt(1-a))


def build(prefix, south, west, north, east, tol=50):
    bbox = (west, south, east, north)   # osmnx 2.x order
    print(f"Downloading drive network {prefix} bbox={bbox} ...")
    G = ox.graph_from_bbox(bbox, network_type="drive", simplify=True,
                           retain_all=False, truncate_by_edge=True)
    print(f"  raw {G.number_of_nodes()} nodes")
    Gp = ox.project_graph(G)
    Gc = ox.consolidate_intersections(Gp, tolerance=tol, rebuild_graph=True,
                                      dead_ends=True, reconnect_edges=True)
    UG = ox.convert.to_undirected(Gc)
    crs = Gc.graph["crs"]; Gll = ox.project_graph(Gc, to_latlong=True)
    osm_ids = list(UG.nodes()); id_map = {o: str(i) for i, o in enumerate(osm_ids)}
    nodes_out, utm = [], []
    for o in osm_ids:
        nll = Gll.nodes[o]; nu = Gc.nodes[o]
        nodes_out.append({"id": id_map[o], "x": float(nll["x"]), "y": float(nll["y"])})
        utm.append([float(nu["x"]), float(nu["y"])])
    edges_out, seen = [], set()
    for u, v, d in UG.edges(data=True):
        su, sv = id_map[u], id_map[v]
        if su == sv: continue
        key = (min(su, sv), max(su, sv))
        if key in seen: continue
        seen.add(key)
        L = float(d.get("length", 0) or 0)
        if L <= 0:
            L = _hav(nodes_out[int(su)]["x"], nodes_out[int(su)]["y"],
                     nodes_out[int(sv)]["x"], nodes_out[int(sv)]["y"])
        edges_out.append({"source": su, "target": sv, "distance": round(L, 2),
                          "travel_time": int(L/1.4)})
    # keep largest connected component (relabel)
    S = nx.Graph(); [S.add_node(n["id"]) for n in nodes_out]
    [S.add_edge(e["source"], e["target"]) for e in edges_out]
    gcc = max(nx.connected_components(S), key=len)
    keep = {n: str(i) for i, n in enumerate(sorted(gcc, key=int))}
    nodes_f = [{"id": keep[n["id"]], "x": n["x"], "y": n["y"]}
               for n in nodes_out if n["id"] in keep]
    utm_f = [utm[int(n["id"])] for n in nodes_out if n["id"] in keep]
    edges_f = [{"source": keep[e["source"]], "target": keep[e["target"]],
                "distance": e["distance"], "travel_time": e["travel_time"]}
               for e in edges_out if e["source"] in keep and e["target"] in keep]
    json.dump(nodes_f, open(f"{_OUT}/{prefix}_graph_nodes.json", "w"))
    json.dump(edges_f, open(f"{_OUT}/{prefix}_graph_edges.json", "w"))
    np.save(f"{_OUT}/{prefix}_graph_nodes_utm.npy", np.array(utm_f))
    Sd = nx.Graph(); [Sd.add_edge(e["source"], e["target"]) for e in edges_f]
    degs = [d for _, d in Sd.degree()]
    meta = {"bbox": {"min_lat": south, "max_lat": north, "min_lon": west, "max_lon": east},
            "utm_crs": str(crs), "n_nodes": len(nodes_f), "n_edges": len(edges_f),
            "tolerance_m": tol, "degree_mean": float(np.mean(degs)),
            "degree_max": int(max(degs)), "dead_ends": int(sum(d == 1 for d in degs))}
    json.dump(meta, open(f"{_OUT}/{prefix}_graph_meta.json", "w"), indent=2)
    print(f"  {prefix}: {len(nodes_f)} nodes, {len(edges_f)} edges, "
          f"deg mean {meta['degree_mean']:.2f} max {meta['degree_max']} "
          f"dead-ends {meta['dead_ends']}")
    return meta


if __name__ == "__main__":
    a = sys.argv
    prefix = a[1]; south, west, north, east = map(float, a[2:6])
    tol = int(a[6]) if len(a) > 6 else 50
    build(prefix, south, west, north, east, tol)
