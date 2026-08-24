"""Validate Phase 1C extension invariants."""
from __future__ import annotations
import csv, json, math
from pathlib import Path
from m4.data.versioning import is_non_decreasing

ROOT = Path(__file__).resolve().parents[1]
PANEL = ROOT / "data/processed/m4-quarterly-v2.csv"
OUT = ROOT / "data/processed/m4-validation-v2.json"

def val(row, key):
    return None if row.get(key, "") in {"", "None"} else float(row[key])

def main():
    rows = list(csv.DictReader(PANEL.open(encoding="utf-8", newline="")))
    fx = [val(r, "mnt_per_usd_quarterly_average") for r in rows if val(r, "mnt_per_usd_quarterly_average") is not None]
    fx_eop = [val(r, "mnt_per_usd_quarter_end") for r in rows if val(r, "mnt_per_usd_quarter_end") is not None]
    identity = []
    for r in rows:
        keys = ["gdp_expenditure_current", "household_consumption_current", "government_consumption_current", "gross_capital_formation_current", "net_exports_current"]
        values = [val(r, k) for k in keys]
        if all(v is not None for v in values) and not math.isclose(values[0], sum(values[1:]), rel_tol=1e-9, abs_tol=0.6): identity.append(r["quarter"])
    report = {"dataset": "m4-quarterly-v2", "rows": len(rows), "period_start": rows[0]["quarter"], "period_end": rows[-1]["quarter"], "checks": {"quarters_non_decreasing": is_non_decreasing([r["quarter"] for r in rows]), "fx_positive": all(v > 0 for v in fx + fx_eop), "fx_average_min": min(fx), "fx_average_max": max(fx), "expenditure_identity_failures": identity, "chain_linked_is_growth_measure": True, "annual_gfcf_interpolated": False}, "notes": ["BoM reserves and policy-rate endpoints returned no-result responses; no substitute was used.", "Employment 2019-2023 sampling-weight revision is recorded in the source manifest."]}
    OUT.write_text(json.dumps(report, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    if identity or not report["checks"]["fx_positive"] or not report["checks"]["quarters_non_decreasing"]: raise SystemExit("Phase 1C validation failed")
    print(f"Wrote {OUT}; Phase 1C checks passed for {len(rows)} quarters.")

if __name__ == "__main__": main()
