# Original Data — Microsoft GeoLife GPS Trajectory Dataset

## Dataset Information

**Dataset Name:** Microsoft GeoLife GPS Trajectory Dataset  
**Source:** Microsoft Research Asia  
**Official Download Page:**  
https://www.microsoft.com/en-us/download/details.aspx?id=52367

Version 1.3 Summary:

- 182 users
- April 2007 – August 2012
- ~24 million GPS points
- ~1.29 million kilometers total distance
- Majority of trajectories collected in Beijing, China

This dataset is widely used in academic research related to:

- Mobility pattern mining
- Location privacy
- Activity recognition
- Transportation mode detection

---

## Important Notice

This repository does **not** redistribute the Microsoft GeoLife dataset.

Due to the Microsoft Research non-commercial license, users must download the dataset directly from the official Microsoft website.

Do **not** commit or upload the raw trajectory files to this repository.

---

## Required Folder Structure

After downloading and extracting the dataset, place it inside this folder as follows:

```text
original data/
└── Data/
    ├── 000/
    │   └── Trajectory/
    │       ├── 20081023025304.plt
    │       ├── 20081023030000.plt
    │       └── ...
    │
    ├── 001/
    │   └── Trajectory/
    │       ├── ...
    │
    ├── 002/
    │   └── Trajectory/
    │       ├── ...
    │
    └── ...
```

Important:

- The folder must be named exactly: `Data`
- Each user folder (`000`, `001`, etc.) must remain unchanged
- Each user must contain a `Trajectory/` folder
- Do not modify `.plt` files

---

## File Format

Each `.plt` file represents a single trajectory.

After skipping the first 6 header lines, each row contains:

- Latitude
- Longitude
- (unused field)
- Altitude
- Date (numeric format)
- Date (string format)
- Time (string format)

Example:

```text
39.906631,116.385564,0,492,40097.5864583333,2009-10-11,14:04:30
```

---

## License

The dataset is released under the Microsoft Research License Agreement (Non-Commercial Use Only).

Use of this dataset is permitted for academic and non-commercial research purposes only.

For full licensing terms, refer to the official dataset documentation.
