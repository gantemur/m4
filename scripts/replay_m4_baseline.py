"""Replay observed v2 data through M4 accounting checks only."""
from pathlib import Path
from m4.model import Baseline

ROOT = Path(__file__).resolve().parents[1]

if __name__ == "__main__":
    baseline = Baseline.load(ROOT / "data/processed/m4-quarterly-v2.csv")
    checks = baseline.replay_checks()
    if any(checks.values()):
        raise SystemExit(f"Baseline replay failed: {checks}")
    print(f"Baseline replay passed for {len(baseline.rows)} quarters; no behavioral equations were invoked.")
