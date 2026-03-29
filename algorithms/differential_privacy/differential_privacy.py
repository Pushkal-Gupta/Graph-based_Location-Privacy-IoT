"""
Differential Privacy Location Obfuscation for IoT Smart Cities
================================================================

References
----------
[1] Dwork, C. (2006). Differential Privacy.
    Proc. ICALP 2006, LNCS 4052, pp. 1-12.
    https://doi.org/10.1007/11787006_1
    -- Foundational definition: a randomised mechanism M satisfies
       ε-differential privacy when for all datasets D₁, D₂ differing
       in one record and all outputs S:  Pr[M(D₁)∈S] ≤ eᵋ·Pr[M(D₂)∈S].

[2] Dwork, C., McSherry, F., Nissim, K., & Smith, A. (2006).
    Calibrating Noise to Sensitivity in Private Data Analysis.
    Proc. TCC 2006, LNCS 3876, pp. 265-284.
    -- Introduces the Laplace mechanism: for a function f with L₁
       sensitivity Δf, adding Lap(Δf/ε) noise to each output
       coordinate achieves ε-differential privacy.

[3] Andrés, M. E., Bordenabe, N. E., Chatzikokolakis, K., & Palamidessi, C.
    (2013). Geo-indistinguishability: Differential Privacy for
    Location-Based Systems.  Proc. CCS 2013, pp. 901-914.
    https://doi.org/10.1145/2508859.2516735
    -- Adapts differential privacy to the spatial domain: a user's
       reported location is ε-geo-indistinguishable when the
       probability ratio for any two true locations decays
       exponentially with distance.  The planar Laplace mechanism
       (independent Laplace noise on each coordinate) is shown to
       satisfy this property.

[4] Chatzikokolakis, K., Andrés, M. E., Bordenabe, N. E., & Palamidessi, C.
    (2013). Broadening the Scope of Differential Privacy Using Metrics.
    Proc. PETS 2013, pp. 82-102.
    -- Generalises ε-differential privacy to arbitrary metric spaces,
       providing the formal basis for applying Laplace noise in
       geographic coordinate spaces.

Algorithm: Independent Laplace Noise on Geographic Coordinates
    (Planar Laplace mechanism from [3], using the Laplace distribution
     from [2])

    Input : snapshot S = {user_id -> node_id}, privacy budget ε
    For each user u in S at node v:
      1. (lon, lat) <- coordinates of v
      2. noisy_lon <- lon + Lap(0, Δ/ε)
         noisy_lat <- lat + Lap(0, Δ/ε)
         where Δ is the coordinate-space sensitivity (grid spacing)
      3. location_error <- haversine(original, noisy) in metres
    Output: {user_id -> {original_node, noisy_coords, location_error}}
"""

import json
import math
import numpy as np


def _haversine_m(lon1, lat1, lon2, lat2):
    """
    Great-circle distance in metres between two (lon, lat) points.
    Uses the Haversine formula (error < 0.5% for distances under 10 km).
    """
    R = 6_371_000  # Earth radius in metres
    phi1, phi2 = math.radians(lat1), math.radians(lat2)
    dphi = math.radians(lat2 - lat1)
    dlam = math.radians(lon2 - lon1)
    a = (math.sin(dphi / 2) ** 2 +
         math.cos(phi1) * math.cos(phi2) * math.sin(dlam / 2) ** 2)
    return 2 * R * math.atan2(math.sqrt(a), math.sqrt(1 - a))


class DPLocationObfuscator:
    """
    Coordinate-based differential privacy for location data.

    Implements the planar Laplace mechanism from Andrés et al. (2013) [3]:
    independent Laplace noise is added to each geographic coordinate,
    achieving ε-geo-indistinguishability.

    This is a *coordinate-based* mechanism — the noisy output is a point
    in continuous 2-D space, not necessarily on the road-network graph.
    """

    def __init__(self, nodes, edges, epsilon=1.0):
        """
        Parameters
        ----------
        nodes : str | list
            Path to nodes JSON, or pre-loaded list.
        edges : str | list
            Path to edges JSON, or pre-loaded list (unused by this
            algorithm but accepted for interface consistency).
        epsilon : float
            Privacy budget.  Smaller ε → stronger privacy, more noise.
        """
        self.epsilon = epsilon
        self.node_coords = self._load_nodes(nodes)

        # Coordinate-space sensitivity: average spacing between
        # adjacent grid nodes (one cell width in degrees).
        self.sensitivity = self._estimate_sensitivity(nodes, edges)

    # ------------------------------------------------------------------
    # Data loading
    # ------------------------------------------------------------------
    @staticmethod
    def _load_nodes(nodes_input):
        if isinstance(nodes_input, str):
            with open(nodes_input) as f:
                nodes_input = json.load(f)
        coords = {}
        for n in nodes_input:
            nid = str(n["id"])
            coords[nid] = (float(n["x"]), float(n["y"]))  # (lon, lat)
        return coords

    @staticmethod
    def _estimate_sensitivity(nodes_input, edges_input):
        """
        Estimate Δ as the median edge length in coordinate space.

        This represents one grid-cell movement, the natural unit of
        change for a single location update.
        """
        if isinstance(nodes_input, str):
            with open(nodes_input) as f:
                nodes_input = json.load(f)
        if isinstance(edges_input, str):
            with open(edges_input) as f:
                edges_input = json.load(f)

        coords = {}
        for n in nodes_input:
            coords[str(n["id"])] = (float(n["x"]), float(n["y"]))

        dists = []
        for e in edges_input:
            s, t = str(e["source"]), str(e["target"])
            if s in coords and t in coords:
                dx = coords[s][0] - coords[t][0]
                dy = coords[s][1] - coords[t][1]
                dists.append(math.sqrt(dx * dx + dy * dy))

        return float(np.median(dists)) if dists else 0.01

    # ------------------------------------------------------------------
    # Laplace noise  [Dwork et al. 2006, Mechanism 1]
    # ------------------------------------------------------------------
    def _add_laplace(self, value):
        """Add Lap(0, Δ/ε) noise to a single coordinate."""
        scale = self.sensitivity / self.epsilon
        return value + np.random.laplace(0, scale)

    # ------------------------------------------------------------------
    # Main entry point
    # ------------------------------------------------------------------
    def anonymize_snapshot(self, snapshot):
        """
        Apply ε-differential privacy obfuscation to a location snapshot.

        Parameters
        ----------
        snapshot : dict  {user_id: node_id}

        Returns
        -------
        dict  {user_id: {
            "original_node"   : str,
            "original_coords" : (lon, lat),
            "noisy_coords"    : (lon, lat),
            "location_error"  : float  (metres, haversine),
        }}
        """
        result = {}
        for uid, node in snapshot.items():
            node = str(node)
            ox, oy = self.node_coords[node]           # (lon, lat)
            nx_ = self._add_laplace(ox)
            ny_ = self._add_laplace(oy)
            err = _haversine_m(ox, oy, nx_, ny_)

            result[uid] = {
                "original_node":   node,
                "original_coords": (ox, oy),
                "noisy_coords":    (nx_, ny_),
                "location_error":  err,
            }
        return result
