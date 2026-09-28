#!/usr/bin/env python3
"""WestQuant QAB Reproducibility Pipeline — reproduce_all.py

Regenerates the Quantum Advantage Boundary Atlas and all non-QPU results.

Usage:
    python projects/QAB/reproduce_all.py                  # Full reproduction
    python projects/QAB/reproduce_all.py --phase atlas     # Just Atlas ingestion
    python projects/QAB/reproduce_all.py --phase visualize # Just figures
    python projects/QAB/reproduce_all.py --summary        # Print Atlas summary
"""
from __future__ import annotations

import argparse
import subprocess
import sys
from pathlib import Path

# Ensure the westquant root is on the path so 'projects.QAB' is importable
BASE = Path(__file__).resolve().parents[2]  # westquant/
if str(BASE) not in sys.path:
    sys.path.insert(0, str(BASE))

QAB = Path(__file__).resolve().parent

PHASES = {
    "atlas": ("Atlas ingestion (R01)", "projects.QAB.atlas.ingest"),
    "visualize": ("Atlas visualization", "projects.QAB.atlas.visualize"),
}


def run_phase(phase: str, name: str, module: str) -> int:
    print(f"\n{'='*70}")
    print(f"PHASE: {name}")
    print(f"{'='*70}")
    cmd = [sys.executable, "-m", module]
    result = subprocess.run(cmd, cwd=str(BASE))
    if result.returncode != 0:
        print(f"  WARNING: Phase '{phase}' exited with code {result.returncode}")
    return result.returncode


def print_summary():
    """Print Atlas summary."""
    from projects.QAB.atlas.registry import AtlasRegistry
    db = QAB / "atlas" / "v0.1" / "atlas.db"
    if not db.exists():
        print("Atlas not found. Run 'reproduce_all.py --phase atlas' first.")
        return
    registry = AtlasRegistry(db)
    s = registry.summary()
    print(f"\n{'='*70}")
    print("WestQuant Quantum Advantage Boundary Atlas v0.1")
    print(f"{'='*70}")
    print(f"  Total records: {s['total_records']}")
    print(f"  By status: {s['by_status']}")
    print(f"  By track: {s['by_track']}")
    print(f"  Database: {s['db_path']}")

    # Check figures
    figs_dir = QAB / "atlas" / "v0.1" / "figures"
    if figs_dir.exists():
        figs = list(figs_dir.glob("*.png"))
        print(f"  Figures: {len(figs)}")
        for f in sorted(figs):
            print(f"    {f.name}")


def main():
    parser = argparse.ArgumentParser(description="WestQuant QAB Reproducibility")
    parser.add_argument("--phase", choices=list(PHASES.keys()),
                        help="Run only a specific phase")
    parser.add_argument("--summary", action="store_true",
                        help="Print Atlas summary")
    args = parser.parse_args()

    print("WestQuant Quantum Advantage Boundary — Reproducibility Pipeline")
    print(f"Base: {BASE}")
    print(f"QAB:   {QAB}")

    # Check prerequisites
    gqo_log = BASE / "logs" / "gqo_qss_final_experiment.json"
    basin_stats = BASE / "results" / "gqo_basin_statistics.json"
    cert_dir = BASE / "data" / "ground_truth_certificates"
    basin_dir = BASE / "data" / "recovery_basins"

    print(f"\nPrerequisites:")
    print(f"  GQO final experiment: {'OK' if gqo_log.exists() else 'MISSING'}")
    print(f"  Basin statistics:      {'OK' if basin_stats.exists() else 'MISSING'}")
    print(f"  Ground truth certs:   {len(list(cert_dir.glob('*.json')))} files")
    print(f"  Recovery basin masks: {len(list(basin_dir.glob('*.npz')))} files")

    if args.summary:
        print_summary()
        return

    if args.phase:
        name, module = PHASES[args.phase]
        run_phase(args.phase, name, module)
    else:
        for phase, (name, module) in PHASES.items():
            run_phase(phase, name, module)

    print_summary()
    print(f"\n{'='*70}")
    print("REPRODUCTION COMPLETE")
    print(f"{'='*70}")
    print(f"\nNext steps:")
    print(f"  1. Review Atlas figures in atlas/v0.1/figures/")
    print(f"  2. Query Atlas: python -m projects.QAB.atlas.query --summary")
    print(f"  3. Read MASTER_RESEARCH_PLAN.md for R01-R20 project details")


if __name__ == "__main__":
    main()
