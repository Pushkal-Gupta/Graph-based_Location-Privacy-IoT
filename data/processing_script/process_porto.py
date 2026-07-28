"""
Map-match the Porto taxi dataset (ECML/PKDD 2015, UCI #339) to the Porto OSM
graph. train.csv has a POLYLINE column = "[[lon,lat],...]" sampled every 15 s,
with TIMESTAMP = unix start of the trip. Emits device_locations_porto.csv in the
standard schema (user_id=TAXI_ID, location_id=graph node, date, time).
"""
import os, csv, glob, zipfile, json, ast, numpy as np
from datetime import datetime, timezone, timedelta
from pyproj import Transformer
from scipy.spatial import cKDTree

_HERE = os.path.dirname(os.path.abspath(__file__))
_PROC = os.path.join(_HERE, "..", "processed_data")
_PORTO = os.path.join(_HERE, "..", "original_data", "porto")
OUT = os.path.join(_PROC, "device_locations_porto.csv")
STEP = 15  # seconds between consecutive POLYLINE points


def find_train_csv():
    hits = glob.glob(os.path.join(_PORTO, "**", "train.csv"), recursive=True)
    if hits:
        return hits[0]
    # extract nested zips
    for z in glob.glob(os.path.join(_PORTO, "*.zip")):
        try:
            with zipfile.ZipFile(z) as zf:
                zf.extractall(_PORTO)
        except zipfile.BadZipFile:
            pass
    for z in glob.glob(os.path.join(_PORTO, "**", "*.zip"), recursive=True):
        try:
            with zipfile.ZipFile(z) as zf:
                zf.extractall(os.path.dirname(z))
        except zipfile.BadZipFile:
            pass
    hits = glob.glob(os.path.join(_PORTO, "**", "train.csv"), recursive=True)
    return hits[0] if hits else None


def load_graph():
    nodes = json.load(open(f"{_PROC}/porto_graph_nodes.json"))
    utm = np.load(f"{_PROC}/porto_graph_nodes_utm.npy")
    meta = json.load(open(f"{_PROC}/porto_graph_meta.json"))
    b = meta["bbox"]
    return [str(n["id"]) for n in nodes], utm, meta["utm_crs"], b


def process(max_trips=None):
    train = find_train_csv()
    if not train:
        raise SystemExit("train.csv not found under data/original_data/porto/")
    node_ids, utm, crs, b = load_graph()
    tree = cKDTree(utm)
    to_utm = Transformer.from_crs("EPSG:4326", crs, always_xy=True)
    print(f"Porto graph {len(node_ids)} nodes; parsing {train}")

    n_written, n_trips = 0, 0
    import csv as _csv
    _csv.field_size_limit(10**7)
    with open(train) as fin, open(OUT, "w", newline="") as fout:
        r = _csv.DictReader(fin); w = _csv.writer(fout)
        w.writerow(["user_id", "location_id", "date", "time"])
        for row in r:
            if max_trips and n_trips >= max_trips:
                break
            n_trips += 1
            if row.get("MISSING_DATA") == "True":
                continue
            poly = row.get("POLYLINE", "[]")
            if len(poly) < 5:
                continue
            try:
                pts = ast.literal_eval(poly)
            except Exception:
                continue
            if not pts:
                continue
            taxi = row["TAXI_ID"]; t0 = int(row["TIMESTAMP"])
            lons = np.array([p[0] for p in pts]); lats = np.array([p[1] for p in pts])
            m = ((lats >= b["min_lat"]) & (lats <= b["max_lat"]) &
                 (lons >= b["min_lon"]) & (lons <= b["max_lon"]))
            if not m.any():
                continue
            idxs = np.where(m)[0]
            ex, ey = to_utm.transform(lons[idxs], lats[idxs])
            _, nn = tree.query(np.column_stack([ex, ey]))
            for j, gi in zip(idxs, nn):
                ts = datetime.fromtimestamp(t0 + int(j) * STEP, tz=timezone.utc)
                w.writerow([taxi, node_ids[gi], ts.strftime("%Y-%m-%d"),
                            ts.strftime("%H:%M:%S")])
                n_written += 1
            if n_trips % 100000 == 0:
                print(f"  {n_trips} trips, {n_written:,} rows")
    print(f"Done: {n_written:,} rows from {n_trips} trips -> {OUT}")


if __name__ == "__main__":
    process()
