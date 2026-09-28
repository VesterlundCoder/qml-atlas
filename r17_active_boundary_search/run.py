"""R17 — Active Boundary Search.

Trains a surrogate model on Atlas results and suggests the next experiment
where |A(x)| ≈ 0 (near the boundary) and uncertainty is high.

100% local — classical ML only.

Usage:
    python -m projects.QAB.r17_active_boundary_search.run  # Train + suggest
"""
from __future__ import annotations

import sys
import json
from pathlib import Path

import numpy as np

BASE = Path(__file__).resolve().parents[2]
if str(BASE) not in sys.path:
    sys.path.insert(0, str(BASE))

from projects.QAB.atlas.registry import AtlasRegistry

ATLAS_DIR = Path(__file__).resolve().parents[1] / "atlas" / "v0.1"
DB_PATH = ATLAS_DIR / "atlas.db"


def load_atlas_data() -> tuple[np.ndarray, np.ndarray]:
    """Load Atlas records into feature matrix X and target vector A."""
    registry = AtlasRegistry(DB_PATH)
    records = registry.query()

    # Filter records that have a meaningful delta
    valid = [r for r in records if r.delta != 0.0 and r.problem_size > 0]

    if not valid:
        return np.array([]), np.array([])

    # Features: (n, p, m, shots, radius, budget)
    X = []
    A = []
    for r in valid:
        n = r.problem_size
        p = r.depth
        m = r.observable_order
        shots = r.shots
        radius = r.metadata.get("radius", 0)
        budget = r.metadata.get("budget", shots)

        X.append([n, p, m, shots, radius, budget])
        A.append(r.delta)

    return np.array(X), np.array(A)


def train_surrogate(X: np.ndarray, A: np.ndarray):
    """Train a surrogate model Â(x) ≈ A(x)."""
    try:
        from sklearn.ensemble import RandomForestRegressor
        from sklearn.model_selection import cross_val_score
    except ImportError:
        print("  sklearn not available — using simple linear model")
        # Simple linear regression
        from numpy.linalg import lstsq
        X_aug = np.column_stack([X, np.ones(len(X))])
        coeffs, _, _, _ = lstsq(X_aug, A, rcond=None)
        return ("linear", coeffs)

    rf = RandomForestRegressor(n_estimators=100, random_state=42, max_depth=10)
    rf.fit(X, A)

    # Cross-validation
    scores = cross_val_score(rf, X, A, cv=min(5, len(X) // 10 + 1), scoring="r2")
    print(f"  Surrogate R² = {scores.mean():.4f} ± {scores.std():.4f}")

    return ("rf", rf)


def suggest_experiments(model, X_train: np.ndarray, n_suggestions: int = 10):
    """Suggest next experiments where |A(x)| ≈ 0 and uncertainty is high."""
    model_type, model_obj = model

    # Generate candidate experiments
    candidates = []
    for n in [8, 12, 16, 20, 24, 28]:
        for p in [1, 2, 3, 4]:
            for m in [1, 2, 3]:
                for shots in [100, 200, 500, 1000]:
                    for radius in [0, 1, 2, 3]:
                        candidates.append([n, p, m, shots, radius, shots])

    candidates = np.array(candidates)

    if model_type == "rf":
        predictions = model_obj.predict(candidates)
        # For RF, use prediction variance across trees as uncertainty
        all_preds = np.array([tree.predict(candidates) for tree in model_obj.estimators_])
        uncertainty = np.std(all_preds, axis=0)
    else:
        # Linear model
        X_aug = np.column_stack([candidates, np.ones(len(candidates))])
        predictions = X_aug @ model_obj
        uncertainty = np.ones(len(candidates))  # No uncertainty for linear

    # Acquisition: prioritize points near boundary with high uncertainty
    acquisition = 1.0 / (np.abs(predictions) + 0.01) * (1.0 + uncertainty)

    # Get top suggestions
    top_idx = np.argsort(acquisition)[-n_suggestions:][::-1]

    suggestions = []
    for idx in top_idx:
        suggestions.append({
            "n": int(candidates[idx, 0]),
            "p": int(candidates[idx, 1]),
            "m": int(candidates[idx, 2]),
            "shots": int(candidates[idx, 3]),
            "radius": int(candidates[idx, 4]),
            "budget": int(candidates[idx, 5]),
            "predicted_A": float(predictions[idx]),
            "uncertainty": float(uncertainty[idx]),
            "acquisition": float(acquisition[idx]),
        })

    return suggestions


def main():
    print("R17: Active Boundary Search")
    print()

    X, A = load_atlas_data()
    print(f"  Loaded {len(X)} records from Atlas")

    if len(X) < 10:
        print("  Not enough data for surrogate training")
        return

    print(f"  Feature matrix: {X.shape}")
    print(f"  Target vector: {A.shape}")
    print(f"  A range: [{A.min():.4f}, {A.max():.4f}], mean={A.mean():.4f}")
    print()

    print("Training surrogate model...")
    model = train_surrogate(X, A)
    print()

    print("Suggesting next experiments...")
    suggestions = suggest_experiments(model, X, n_suggestions=10)
    print()
    print(f"Top 10 suggested experiments:")
    print(f"  {'n':<4} {'p':<3} {'m':<3} {'shots':<6} {'r':<3} {'pred_A':<10} {'uncert':<10} {'acq':<10}")
    print(f"  {'-'*55}")
    for s in suggestions:
        print(f"  {s['n']:<4} {s['p']:<3} {s['m']:<3} {s['shots']:<6} {s['radius']:<3} "
              f"{s['predicted_A']:<10.4f} {s['uncertainty']:<10.4f} {s['acquisition']:<10.4f}")

    # Save suggestions
    suggestions_path = Path(__file__).resolve().parent / "suggestions.json"
    with open(suggestions_path, "w") as f:
        json.dump(suggestions, f, indent=2)
    print(f"\nSuggestions saved to {suggestions_path}")


if __name__ == "__main__":
    main()
