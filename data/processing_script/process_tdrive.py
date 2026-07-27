"""
Map-Match the T-Drive Beijing Taxi Dataset to the Real Road Graph
=================================================================

Second dataset (reviewer critique E: a single dataset cannot separate genuine
algorithm properties from dataset quirks).  T-Drive is ~10k Beijing taxis over
one week -- the SAME city as GeoLife, so it reuses the same OSM road graph, and
much denser, so it also lets temporal cloaking reach k>3 (which GeoLife could
not support).

Each raw T-Drive line is:  taxi_id, YYYY-MM-DD HH:MM:SS, longitude, latitude
We filter to the central crop, snap to the nearest real-graph node, and emit
device_locations_tdrive.csv in the standard schema
(user_id, location_id, date, time) so the exact same evaluation runs on it.
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
_TD = os.path.join(_HERE, "..", "original_data", "tdrive")
_EXTRACT = os.path.join(_TD, "extracted")

MIN_LAT, MAX_LAT = 39.90, 40.05
MIN_LON, MAX_LON = 116.26, 116.41
OUT_CSV = os.path.join(_PROC, "device_locations_tdrive.csv")


def ensure_extracted():
    txts = glob.glob(os.path.join(_EXTRACT, "**", "*.txt"), recursive=True)
    if txts:
        return _EXTRACT
    os.makedirs(_EXTRACT, exist_ok=True)
    for z in sorted(glob.glob(os.path.join(_TD, "*.zip"))):
        print(f"  extracting {os.path.basename(z)}")
        try:
            with zipfile.ZipFile(z) as zf:
                zf.extractall(_EXTRACT)
        except zipfile.BadZipFile:
            print(f"    WARNING: {z} is not a valid zip, skipping")
    return _EXTRACT


def load_real_graph():
    import json
    with open(os.path.join(_PROC, "real_graph_nodes.json")) as f:
        nodes = json.load(f)
    utm = np.load(os.path.join(_PROC, "real_graph_nodes_utm.npy"))
    with open(os.path.join(_PROC, "real_graph_meta.json")) as f:
        meta = json.load(f)
    return [str(n["id"]) for n in nodes], utm, meta["utm_crs"]


def process():
    root = ensure_extracted()
    txts = sorted(glob.glob(os.path.join(root, "**", "*.txt"), recursive=True))
    print(f"T-Drive taxi files: {len(txts)}")
    node_ids, utm, utm_crs = load_real_graph()
    tree = cKDTree(utm)
    to_utm = Transformer.from_crs("EPSG:4326", utm_crs, always_xy=True)

    n_written = 0
    with open(OUT_CSV, "w", newline="") as fout:
        writer = csv.writer(fout)
        writer.writerow(["user_id", "location_id", "date", "time"])
        for fi, path in enumerate(txts):
            taxi = os.path.splitext(os.path.basename(path))[0]
            lats, lons, dates, times = [], [], [], []
            try:
                with open(path) as f:
                    for line in f:
                        p = line.strip().split(",")
                        if len(p) < 4:
                            continue
                        try:
                            lon = float(p[2]); lat = float(p[3])
                        except ValueError:
                            continue
                        if not (MIN_LAT <= lat <= MAX_LAT and MIN_LON <= lon <= MAX_LON):
                            continue
                        dt = p[1].strip()
                        if " " not in dt:
                            continue
                        d, t = dt.split(" ", 1)
                        lats.append(lat); lons.append(lon); dates.append(d); times.append(t)
            except Exception:
                continue
            if not lats:
                continue
            ex, ey = to_utm.transform(np.array(lons), np.array(lats))
            _, idx = tree.query(np.column_stack([ex, ey]))
            # time-sort this taxi's points
            order = np.argsort([f"{d} {t}" for d, t in zip(dates, times)])
            for j in order:
                writer.writerow([taxi, node_ids[idx[j]], dates[j], times[j]])
                n_written += 1
            if (fi + 1) % 1000 == 0:
                print(f"  {fi+1}/{len(txts)} taxis, {n_written:,} rows")

    print(f"\nDone: {n_written:,} rows -> {OUT_CSV}")


if __name__ == "__main__":
    process()
