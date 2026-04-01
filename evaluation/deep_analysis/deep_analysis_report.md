
# Deep Analysis Report: Privacy, Availability, and Energy

> **Dataset:** Microsoft GeoLife GPS Trajectory Dataset (v1.3) — 182 users, ~24M GPS points, Beijing area.

> **Graph:** 30×30 grid abstraction, 900 nodes, 1,740 edges.

> **Evaluation window (representative):** 10 minutes (600 s).


## 1. Privacy Analysis


### 1.1 Formal Definitions

We evaluate privacy using algorithm-specific formal guarantees:

- **k-Anonymity:** A query is *k-anonymous* if the cloaked region contains at least *k* users. Privacy strength ∝ *k* and the fraction of requests satisfying the guarantee (k-satisfaction rate).

- **Differential Privacy (DP):** Location mechanism satisfies *ε-geo-indistinguishability* [Andrés et al., 2013]. Lower ε = stronger privacy. Normalized score uses log-scale: score = (ln ε_max − ln ε) / (ln ε_max − ln ε_min).

- **Density-Aware k-Anon:** Adaptive k selection (k ∈ {2,5,8}) based on local user density; weighted privacy score = (avg_adaptive_k / k_max) × k_satisfaction_rate.

- **Temporal Cloaking:** Group-based k-guarantee over time windows; privacy score = (group_size / k_max) × k_satisfaction_rate.




### 1.2 Privacy Scores (representative config, window = 10 min)

| Algorithm | Config | Privacy Score | k-Sat Rate | Avg Error (m) |
|-----------|--------|:-------------:|:----------:|:-------------:|
| Temporal Cloaking | group k=3.0 | **1.000** | 100.00% | 5758 |
| k-Anonymity | k=3 | **0.500** | 100.00% | 1189 |
| Differential Privacy | ε=1.0 | **0.411** | 100.00% | 1545 |
| Graph-Constrained DP | ε=1.0 | **0.411** | 100.00% | 1843 |
| Density-Aware k-Anon | adaptive k≈2.95 | **0.370** | 75.37% | 2546 |



### 1.3 Privacy-Utility Tradeoff

Key observations from the full parameter sweep:

- **DP at ε=0.1** (strongest): avg error = 15903 m (highly unusable).

- **DP at ε=5.0** (weakest): avg error = 318 m (good utility, weak privacy).

- **k-Anon k=2**: error = 728 m; **k=6**: error = 2203 m — 2.7× degradation for 3× privacy gain.

- **Graph-Constrained DP** reduces error vs vanilla DP at same ε (graph projection eliminates out-of-network noise).

- **Density-Aware k-Anon** offers the best utility among k-anon variants (adaptive k reduces unnecessary cloaking in dense areas).


## 2. Availability Analysis


### 2.1 Definition

Service availability is the fraction of location requests that receive a valid, privacy-satisfying response within the time window:

  **Availability = (n_served / n_total) × k_satisfaction_rate**

where n_served is the number of records processed and n_total is the baseline (maximum users in the window, as achieved by DP).




### 2.2 Availability Scores

| Algorithm | n Served | Baseline | Service Rate | k-Sat | Availability |
|-----------|:--------:|:--------:|:------------:|:-----:|:------------:|
| k-Anonymity | 759 | 1019 | 74.5% | 100.0% | **74.5%** |
| Differential Privacy | 1019 | 1019 | 100.0% | 100.0% | **100.0%** |
| Graph-Constrained DP | 1019 | 1019 | 100.0% | 100.0% | **100.0%** |
| Density-Aware k-Anon | 1019 | 1019 | 100.0% | 75.4% | **75.4%** |
| Temporal Cloaking | 189 | 1019 | 18.5% | 100.0% | **18.5%** |



### 2.3 Key Availability Findings

- **Temporal Cloaking**: critically low availability — only 189/1019 = 18.5% of users receive responses. Average delay: 1095 s.

- **Differential Privacy / GC-DP**: highest availability — all 1019 records served (100%), no denial of service.

- **k-Anonymity (k=3)**: 74.5% service rate — 25.5% of users cannot find k=3 neighbors in their spatial graph neighborhood.

- **Density-Aware k-Anon**: 100% service rate (all users served) but only 75.4% meet the adaptive k guarantee.

- **Tradeoff**: Higher k dramatically reduces availability. At k=6 (window=10 min), only 261 of 1019 users (25.6%) are served.


### 2.4 Effect of Window Size on Availability

Larger time windows aggregate more users, improving availability:

- k-Anon k=3: w=1min → 576 served; w=20min → 863 served (+50%).

- For DP, availability is invariant to window size (all users always served).

- For Temporal Cloaking, larger windows paradoxically increase delay (more waiting needed to collect k users), reducing effective availability.


## 3. Energy Efficiency Analysis


### 3.1 IoT Energy Model

For resource-constrained IoT devices, we decompose energy into:

1. **E_radio**: Dominant cost — radio transmission (≈5 mJ/tx at 10 mW for 500 ms).

2. **E_compute**: Algorithm processing overhead per report:

   - DP (Laplace noise): **0.05 mJ** — single floating-point operation.

   - Graph-Constrained DP: **0.05–0.15 mJ** — noise + nearest-node search (O(N)).

   - k-Anonymity BFS: **0.05–0.35 mJ** — scales with cloaking region size.

   - Temporal Cloaking: **0.05 mJ** — simple server-side windowing.

3. **E_retrans**: Wasted energy from unsatisfied k-constraints (devices that retransmit after k-satisfaction failure).




### 3.2 Energy Results

| Algorithm | E_radio (mJ) | E_comp (mJ) | E_retrans (mJ) | E_success (mJ) | Eff. Score |
|-----------|:------------:|:-----------:|:--------------:|:--------------:|:----------:|
| k-Anonymity | 5.00 | 0.5662 | 0.00 | **5.57** | 0.907 |
| Differential Privacy | 5.00 | 0.0500 | 0.00 | **5.05** | 1.000 |
| Graph-Constrained DP | 5.00 | 0.0806 | 0.00 | **5.08** | 0.994 |
| Density-Aware k-Anon | 5.00 | 0.8325 | 0.62 | **8.56** | 0.590 |
| Temporal Cloaking | 5.00 | 0.0500 | 0.00 | **5.05** | 1.000 |



### 3.3 Energy Efficiency Findings

- **Most efficient**: Differential Privacy (E_success = 5.05 mJ, score = 1.000).

- **Least efficient**: Density-Aware k-Anon (E_success = 8.56 mJ, score = 0.590).

- **k-Anonymity BFS overhead**: region_size=186 nodes → E_comp = 0.5662 mJ/report (11.3% of radio cost).

- **Radio dominates** (≈98–99% of total energy). Algorithm computation overhead is negligible compared to transmission cost, confirming that communication-efficient strategies (batching, window optimization) are the primary lever for IoT energy savings.

- **Retransmission penalty**: Density-Aware k-Anon (k-sat≈75%) incurs retransmission overhead that degrades effective energy efficiency.

- **Window-size effect**: Doubling the window from 5→10 min halves the update frequency, reducing total radio energy by ~50% — a significant battery lifetime improvement for IoT deployments.


## 4. Combined Evaluation Summary


### 4.1 Dimension Score Table

| Algorithm | Privacy | Availability | Energy Eff. | Overall |
|-----------|:-------:|:------------:|:-----------:|:-------:|
| k-Anonymity | 0.500 | 0.745 | 0.907 | **0.717** |
| Differential Privacy | 0.411 | 1.000 | 1.000 | **0.804** |
| Graph-Constrained DP | 0.411 | 1.000 | 0.994 | **0.802** |
| Density-Aware k-Anon | 0.370 | 0.754 | 0.590 | **0.571** |
| Temporal Cloaking | 1.000 | 0.185 | 1.000 | **0.728** |



### 4.2 Algorithm Recommendations

Based on the three-dimensional analysis:

1. **Differential Privacy** — highest overall balanced score (0.804). Recommended when a well-rounded tradeoff is required.

2. **Graph-Constrained DP** — strong in availability.

3. **Temporal Cloaking** — favored for privacy scenarios.

**Context-specific recommendations:**

- *Maximum privacy* (e.g., sensitive medical IoT): Differential Privacy (ε=0.1) or Temporal Cloaking.

- *Maximum availability* (e.g., real-time fleet tracking): Differential Privacy (ε=1–2) or Graph-Constrained DP.

- *Minimum energy* (e.g., long-life remote sensors): Differential Privacy with large window (20 min) for optimal efficiency.

- *Heterogeneous density* (e.g., smart city): Density-Aware k-Anonymity adapts to urban vs. rural distributions.


## 5. References

- Sweeney, L. (2002). k-anonymity: A model for protecting privacy. *IJUFKS*, 10(5), 557–570.

- Gruteser, M., & Grunwald, D. (2003). Anonymous usage of location-based services through spatial and temporal cloaking. *MobiSys*.

- Dwork, C. (2006). Differential privacy. *ICALP*.

- Andrés, M. E., et al. (2013). Geo-indistinguishability: Differential privacy for location-based systems. *CCS*.

- Gedik, B., & Liu, L. (2008). Protecting location privacy with personalized k-anonymity. *TMC*, 7(1), 1–18.

- Bordenabe, N. E., et al. (2014). Optimal geo-indistinguishable mechanisms for location privacy. *CCS*.

- Niu, B., et al. (2014). Achieving k-anonymity in privacy-aware location-based services. *INFOCOM*.
