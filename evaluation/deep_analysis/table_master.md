<!-- Comprehensive Algorithm Comparison: Privacy, Availability, Energy (window=10min) -->

| Algorithm            | Privacy Score | Availability Score | Energy Eff. | Mean Error (m) | Median (m) | P95 (m) | Temp. Jump (m) | Energy (mJ/report) |
| -------------------- | ------------- | ------------------ | ----------- | -------------- | ---------- | ------- | -------------- | ------------------ |
| k-Anonymity          | 0.500         | 0.745              | 0.907       | 1189           | 0          | 6747    | 6150           | 5.57               |
| Differential Privacy | 0.411         | 1.000              | 1.000       | 1545           | 1297       | 3568    | 6590           | 5.05               |
| Graph-Constrained DP | 0.411         | 1.000              | 0.994       | 1843           | 1705       | 4455    | 8465           | 5.08               |
| Density-Aware k-Anon | 0.370         | 0.754              | 0.590       | 2546           | 0          | 13431   | 6453           | 8.56               |
| Temporal Cloaking    | 1.000         | 0.185              | 1.000       | 5758           | 3927       | 16127   | 2866           | 5.05               |
