#!/usr/bin/env python3
"""
Run All Privacy Algorithm Simulations
=======================================

Single entry point that executes all five location-privacy algorithms
in sequence on the GeoLife dataset.  Each algorithm produces its own
results under results/<algorithm>/.

After this script completes, run evaluation.py to generate cross-algorithm
comparisons.

Usage
-----
    python3 run_all.py              # run all
    python3 run_all.py --only k_anonymity differential_privacy
    python3 run_all.py --skip temporal_cloaking

Pipeline
--------
    run_all.py  ->  results/  ->  evaluation.py  ->  paper/
"""

import os
import sys
import time
import argparse
import importlib


# -----------------------------------------------------------------------
# Algorithm registry
# -----------------------------------------------------------------------
_HERE = os.path.dirname(os.path.abspath(__file__))

ALGORITHMS = {
    "k_anonymity": {
        "dir":    os.path.join(_HERE, "algorithms", "k_anonymity"),
        "module": "k_anonymity_simulation",
    },
    "differential_privacy": {
        "dir":    os.path.join(_HERE, "algorithms", "differential_privacy"),
        "module": "differential_privacy_simulation",
    },
    "graph_constrained_dp": {
        "dir":    os.path.join(_HERE, "algorithms", "graph_constrained_dp"),
        "module": "graph_constrained_dp_simulation",
    },
    "density_aware_k_anonymity": {
        "dir":    os.path.join(_HERE, "algorithms", "density-aware_k-anonymity"),
        "module": "density_aware_k_anonymity_simulation",
    },
    "temporal_cloaking": {
        "dir":    os.path.join(_HERE, "algorithms", "temporal_cloaking"),
        "module": "temporal_cloaking_simulation",
    },
}


# -----------------------------------------------------------------------
# Runner
# -----------------------------------------------------------------------
def run_algorithm(name, info):
    """Import and run a single algorithm's simulation."""
    algo_dir = info["dir"]
    module_name = info["module"]

    print(f"\n{'=' * 70}")
    print(f"  RUNNING: {name}")
    print(f"  Directory: {algo_dir}")
    print(f"{'=' * 70}\n")

    # Add the algorithm directory to sys.path so local imports work
    if algo_dir not in sys.path:
        sys.path.insert(0, algo_dir)

    # Save and change working directory (some algorithms use relative paths)
    original_cwd = os.getcwd()
    os.chdir(algo_dir)

    try:
        # Import (or reimport) the simulation module
        if module_name in sys.modules:
            mod = importlib.reload(sys.modules[module_name])
        else:
            mod = importlib.import_module(module_name)

        # Call the run() entry point
        start = time.time()
        mod.run()
        elapsed = time.time() - start

        print(f"\n  {name} completed in {elapsed:.1f} seconds.")
        return True, elapsed

    except Exception as e:
        print(f"\n  ERROR in {name}: {e}")
        import traceback
        traceback.print_exc()
        return False, 0.0

    finally:
        os.chdir(original_cwd)
        # Clean up sys.path to avoid cross-contamination
        if algo_dir in sys.path:
            sys.path.remove(algo_dir)


# -----------------------------------------------------------------------
# Main
# -----------------------------------------------------------------------
def main():
    parser = argparse.ArgumentParser(
        description="Run all privacy algorithm simulations.")
    parser.add_argument(
        "--only", nargs="+", default=None,
        help="Run only these algorithms (space-separated names).")
    parser.add_argument(
        "--skip", nargs="+", default=None,
        help="Skip these algorithms.")
    args = parser.parse_args()

    # Determine which algorithms to run
    to_run = list(ALGORITHMS.keys())
    if args.only:
        to_run = [a for a in args.only if a in ALGORITHMS]
    if args.skip:
        to_run = [a for a in to_run if a not in args.skip]

    print("=" * 70)
    print("  PRIVACY ALGORITHM SIMULATION PIPELINE")
    print(f"  Algorithms to run: {', '.join(to_run)}")
    print("=" * 70)

    summary = {}
    total_start = time.time()

    for name in to_run:
        success, elapsed = run_algorithm(name, ALGORITHMS[name])
        summary[name] = {"success": success, "time": elapsed}

    total_elapsed = time.time() - total_start

    # Print summary
    print(f"\n\n{'=' * 70}")
    print("  PIPELINE SUMMARY")
    print(f"{'=' * 70}")
    for name, info in summary.items():
        status = "OK" if info["success"] else "FAILED"
        print(f"  {name:35s}  {status:8s}  {info['time']:7.1f}s")
    print(f"{'=' * 70}")
    print(f"  Total time: {total_elapsed:.1f}s")
    print(f"\n  Next step: python3 evaluation.py")
    print(f"{'=' * 70}")


if __name__ == "__main__":
    main()
