import os
import pandas as pd
import json
import math

# ========================= CONFIG =========================
GRID_SIZE = 30
MAX_USERS = None
MAX_SPEED_KMH = 200
BOUNDS = (39.8, 40.1, 116.2, 116.5)
# =========================================================


# ========================= PATH SETUP =========================
BASE_DIR = os.path.dirname(os.path.abspath(__file__))

DATA_DIR = os.path.join(BASE_DIR, "..", "original data", "Data")
OUTPUT_DIR = os.path.join(BASE_DIR, "..", "processed data")

# Ensure processed data folder exists
os.makedirs(OUTPUT_DIR, exist_ok=True)
# =============================================================


# ========================= UTIL =========================
def haversine(lat1, lon1, lat2, lon2):
    R = 6371000  # meters
    phi1 = math.radians(lat1)
    phi2 = math.radians(lat2)
    dphi = math.radians(lat2 - lat1)
    dlambda = math.radians(lon2 - lon1)

    a = math.sin(dphi/2)**2 + \
        math.cos(phi1)*math.cos(phi2)*math.sin(dlambda/2)**2

    return 2 * R * math.atan2(math.sqrt(a), math.sqrt(1 - a))


# ========================= GRAPH CREATION =========================
def create_city_graph(grid_size, bounds):
    min_lat, max_lat, min_lon, max_lon = bounds
    lat_step = (max_lat - min_lat) / grid_size
    lon_step = (max_lon - min_lon) / grid_size

    nodes = []
    edges = []

    for i in range(grid_size):
        for j in range(grid_size):
            node_id = str(i * grid_size + j)

            center_lat = min_lat + i * lat_step + lat_step / 2
            center_lon = min_lon + j * lon_step + lon_step / 2

            nodes.append({
                "id": node_id,
                "x": center_lon,
                "y": center_lat
            })

            # Horizontal edge
            if j < grid_size - 1:
                target = str(i * grid_size + (j + 1))
                dist = haversine(center_lat, center_lon,
                                 center_lat,
                                 center_lon + lon_step)

                edges.append({
                    "source": node_id,
                    "target": target,
                    "distance": round(dist, 2),
                    "travel_time": int(dist / 1.4)
                })

            # Vertical edge
            if i < grid_size - 1:
                target = str((i + 1) * grid_size + j)
                dist = haversine(center_lat, center_lon,
                                 center_lat + lat_step,
                                 center_lon)

                edges.append({
                    "source": node_id,
                    "target": target,
                    "distance": round(dist, 2),
                    "travel_time": int(dist / 1.4)
                })

    with open(os.path.join(OUTPUT_DIR, "city_graph_nodes.json"), "w") as f:
        json.dump(nodes, f, indent=2)

    with open(os.path.join(OUTPUT_DIR, "city_graph_edges.json"), "w") as f:
        json.dump(edges, f, indent=2)

    print(f"Graph created: {len(nodes)} nodes, {len(edges)} edges")


# ========================= TRAJECTORY PROCESSING =========================
def load_and_map_trajectories(data_dir, grid_size, bounds, max_users):
    min_lat, max_lat, min_lon, max_lon = bounds
    lat_step = (max_lat - min_lat) / grid_size
    lon_step = (max_lon - min_lon) / grid_size

    records = []

    user_dirs = sorted(os.listdir(data_dir))
    if max_users:
        user_dirs = user_dirs[:max_users]

    for user_id in user_dirs:
        traj_path = os.path.join(data_dir, user_id, "Trajectory")
        if not os.path.exists(traj_path):
            continue

        for file in os.listdir(traj_path):
            if not file.endswith(".plt"):
                continue

            df = pd.read_csv(
                os.path.join(traj_path, file),
                skiprows=6,
                header=None,
                names=["lat","lon","0","alt","1","date","time"]
            )

            df = df[(df["lat"].between(min_lat, max_lat)) &
                    (df["lon"].between(min_lon, max_lon))]

            df["timestamp"] = pd.to_datetime(df["date"] + " " + df["time"])
            df = df.sort_values("timestamp")

            prev_row = None

            for _, row in df.iterrows():

                if prev_row is not None:
                    dist = haversine(prev_row["lat"], prev_row["lon"],
                                     row["lat"], row["lon"])
                    dt = (row["timestamp"] - prev_row["timestamp"]).total_seconds()

                    if dt > 0:
                        speed = (dist / dt) * 3.6
                        if speed > MAX_SPEED_KMH:
                            continue

                row_idx = int((row["lat"] - min_lat) / lat_step)
                col_idx = int((row["lon"] - min_lon) / lon_step)

                row_idx = max(0, min(grid_size - 1, row_idx))
                col_idx = max(0, min(grid_size - 1, col_idx))

                location_id = str(row_idx * grid_size + col_idx)

                records.append({
                    "user_id": user_id,
                    "location_id": location_id,
                    "date": row["timestamp"].strftime("%Y-%m-%d"),
                    "time": row["timestamp"].strftime("%H:%M:%S")
                })

                prev_row = row

    df_locations = pd.DataFrame(records)

    df_locations = df_locations.drop_duplicates(
        subset=["user_id","location_id","date","time"]
    )

    df_locations = df_locations.sort_values(
        ["user_id","date","time"]
    )

    df_locations.to_csv(
        os.path.join(OUTPUT_DIR, "device_locations.csv"),
        index=False
    )

    print(f"Trajectory dataset created: {len(df_locations)} records")


# ========================= MAIN =========================
if __name__ == "__main__":
    print("Processing GeoLife...")
    create_city_graph(GRID_SIZE, BOUNDS)
    load_and_map_trajectories(DATA_DIR, GRID_SIZE, BOUNDS, MAX_USERS)
    print("Done.")