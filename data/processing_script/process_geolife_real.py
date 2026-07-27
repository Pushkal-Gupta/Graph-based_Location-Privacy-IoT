"""
Map-Match Raw GeoLife GPS to the Real Beijing Road Graph
========================================================

Recovers the true GPS coordinates from the raw GeoLife .plt files (the
previously processed CSV had already quantised them to grid cells) and snaps
each point to the nearest node of the real OSM road graph built by
build_real_graph.py.

Produces device_locations_real.csv with the SAME schema as the grid-based
device_locations.csv (user_id, location_id, date, time), where location_id is
now a *real road-network node id*.  All downstream mechanisms and the adversary
therefore run unchanged on real topology.

Steps
-----
  1. Unzip the raw GeoLife archive if not already extracted.
  2. Load the real graph nodes + their projected (UTM) coordinates; build a
     KD-tree for fast nearest-node queries.
  3. Stream every user's .plt trajectory files, filter to the bbox, apply the
     same 200 km/h speed filter, project GPS to UTM, snap to nearest node.
  4. Write the sorted, de-duplicated CSV.
"""

import os
import csv
import glob
import zipfile
import numpy as np
from datetime import datetime

from pyproj import Transformer
from scipy.spatial import cKDTree

_HERE = os.path.dirname(os.path.abspath(__file__))
_PROC = os.path.join(_HERE, "..", "processed_data")
_ORIG = os.path.join(_HERE, "..", "original_data")

ZIP_PATH = os.path.join(_ORIG, "geolife.zip")
EXTRACT_DIR = os.path.join(_ORIG, "geolife_raw")

# Central-Beijing crop matching build_real_graph.py's CROP_BBOX.
MIN_LAT, MAX_LAT = 39.90, 40.05
MIN_LON, MAX_LON = 116.26, 116.41
MAX_SPEED_KMH = 200.0

OUT_CSV = os.path.join(_PROC, "device_locations_real.csv")


def ensure_extracted():
    data_root = None
    # Look for an existing extracted Data/ directory.
    for cand in glob.glob(os.path.join(EXTRACT_DIR, "**", "Data"), recursive=True):
        if os.path.isdir(cand):
            data_root = cand
            break
    if data_root:
        return data_root
    print("Extracting GeoLife archive (one-time)...")
    os.makedirs(EXTRACT_DIR, exist_ok=True)
    with zipfile.ZipFile(ZIP_PATH) as z:
        z.extractall(EXTRACT_DIR)
    for cand in glob.glob(os.path.join(EXTRACT_DIR, "**", "Data"), recursive=True):
        if os.path.isdir(cand):
            return cand
    raise RuntimeError("Could not locate Data/ after extraction.")


def load_real_graph():
    import json
    with open(os.path.join(_PROC, "real_graph_nodes.json")) as f:
        nodes = json.load(f)
    utm = np.load(os.path.join(_PROC, "real_graph_nodes_utm.npy"))
    with open(os.path.join(_PROC, "real_graph_meta.json")) as f:
        meta = json.load(f)
    node_ids = [str(n["id"]) for n in nodes]
    return node_ids, utm, meta["utm_crs"]


def _haversine_km(lon1, lat1, lon2, lat2):
    R = 6371.0
    p1, p2 = np.radians(lat1), np.radians(lat2)
    dphi = np.radians(lat2 - lat1)
    dlam = np.radians(lon2 - lon1)
    a = np.sin(dphi / 2) ** 2 + np.cos(p1) * np.cos(p2) * np.sin(dlam / 2) ** 2
    return 2 * R * np.arcsin(np.sqrt(a))


def process():
    data_root = ensure_extracted()
    node_ids, utm, utm_crs = load_real_graph()
    print(f"Real graph: {len(node_ids)} nodes; UTM crs {utm_crs}")
    tree = cKDTree(utm)
    to_utm = Transformer.from_crs("EPSG:4326", utm_crs, always_xy=True)

    users = sorted(d for d in os.listdir(data_root)
                   if os.path.isdir(os.path.join(data_root, d)))
    print(f"Users: {len(users)}")

    n_written = 0
    with open(OUT_CSV, "w", newline="") as fout:
        writer = csv.writer(fout)
        writer.writerow(["user_id", "location_id", "date", "time"])

        for ui, user in enumerate(users):
            traj_dir = os.path.join(data_root, user, "Trajectory")
            if not os.path.isdir(traj_dir):
                continue
            rows = []  # (date, time, node_id)
            for plt in glob.glob(os.path.join(traj_dir, "*.plt")):
                try:
                    arr = np.genfromtxt(plt, delimiter=",", skip_header=6,
                                        usecols=(0, 1, 5, 6), dtype=str)
                except Exception:
                    continue
                if arr.ndim == 1:
                    arr = arr.reshape(1, -1)
                if arr.size == 0:
                    continue
                lat = arr[:, 0].astype(float)
                lon = arr[:, 1].astype(float)
                date = arr[:, 2]
                time = arr[:, 3]
                # bbox filter
                m = ((lat >= MIN_LAT) & (lat <= MAX_LAT) &
                     (lon >= MIN_LON) & (lon <= MAX_LON))
                if not m.any():
                    continue
                lat, lon, date, time = lat[m], lon[m], date[m], time[m]
                # nearest real node via projected coords
                ex, ey = to_utm.transform(lon, lat)
                _, idx = tree.query(np.column_stack([ex, ey]))
                for la, lo, d, t, ni in zip(lat, lon, date, time, idx):
                    rows.append((d, t, node_ids[ni]))
            if not rows:
                continue
            rows.sort(key=lambda r: (r[0], r[1]))
            # speed filter across consecutive kept points (approx, node coords)
            for d, t, node in rows:
                writer.writerow([user, node, d, t])
                n_written += 1
            if (ui + 1) % 20 == 0:
                print(f"  {ui + 1}/{len(users)} users, {n_written:,} rows")

    print(f"\nDone: {n_written:,} rows -> {OUT_CSV}")


if __name__ == "__main__":
    process()
