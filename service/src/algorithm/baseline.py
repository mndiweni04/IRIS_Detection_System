import json
from typing import Dict, Optional

# Canonical baseline (single source of truth in this module)
BASELINE: Dict[str, float] = {
    "avg_blink_duration_ms": 250.0,
    "nod_freq_hz": 0.2,
    "avg_accel_ay": 0.0,
}

def load_baseline() -> Dict[str, float]:
    """Return the canonical in-module baseline (no file I/O by default)."""
    return dict(BASELINE)  # return a copy so callers cannot mutate the module constant

def define_and_save_drowsiness_baseline(path: Optional[str] = None) -> None:
    """Persist the canonical baseline only when a path is explicitly provided.

    Avoid implicit or absolute disk paths; callers must opt in to persistence by supplying path.
    """
    if path is None:
        print("No path provided; baseline available in-module via load_baseline()")
        return
    from pathlib import Path
    p = Path(path)
    p.parent.mkdir(parents=True, exist_ok=True)
    with p.open("w", encoding="utf-8") as f:
        json.dump(BASELINE, f, indent=4)
    print(f"Drowsiness detection baseline saved to {p}")
