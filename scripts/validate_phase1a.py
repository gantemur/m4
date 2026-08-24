"""Validate economic/accounting invariants for the corrected Phase 1A v1 panel."""

from __future__ import annotations

import csv
import json
import math
from collections import defaultdict
from pathlib import Path

from m4.data.versioning import duplicate_keys, is_non_decreasing

ROOT = Path(__file__).resolve().parents[1]
PANEL = ROOT / "data/processed/m4-quarterly-v1.csv"
OUTPUT = ROOT / "data/processed/m4-validation-v1.json"


def number(row: dict[str, str], key: str) -> float | None:
    value = row.get(key, "")
    return float(value) if value not in {"", "None"} else None


def negative_periods(rows: list[dict[str, str]], columns: list[str]) -> list[str]:
    return [row["quarter"] for row in rows if any((number(row, key) is not None and number(row, key) < 0) for key in columns)]


def identity_failures(rows: list[dict[str, str]], left: str, right: str, total: str, tolerance: float = 0.25) -> list[str]:
    failures = []
    for row in rows:
        a, b, c = number(row, left), number(row, right), number(row, total)
        if a is not None and b is not None and c is not None and not math.isclose(c, a + b, rel_tol=1e-9, abs_tol=tolerance):
            failures.append(row["quarter"])
    return failures


def main() -> None:
    with PANEL.open(encoding="utf-8", newline="") as stream:
        rows = list(csv.DictReader(stream))
    quarters = [row["quarter"] for row in rows]
    trade_turnover_failures = identity_failures(rows, "exports_usd_million", "imports_usd_million", "trade_turnover_usd_million")
    balance_failures = []
    for row in rows:
        exports, imports, balance = number(row, "exports_usd_million"), number(row, "imports_usd_million"), number(row, "trade_balance_usd_million")
        if exports is not None and imports is not None and balance is not None and not math.isclose(balance, exports - imports, rel_tol=1e-9, abs_tol=0.25):
            balance_failures.append(row["quarter"])
    commodity_quantity = [c for c in ("coal_export_quantity_thousand_t", "copper_concentrate_export_quantity_thousand_t", "gold_export_quantity_t", "iron_ore_export_quantity_thousand_t")]
    commodity_value = [c for c in ("coal_export_value_usd_thousand", "copper_concentrate_export_value_usd_thousand", "gold_export_value_usd_thousand", "iron_ore_export_value_usd_thousand")]
    unit_value_columns = ["coal_implied_export_unit_value_usd_per_t", "copper_concentrate_implied_export_unit_value_usd_per_t"]
    unit_value_invalid = [row["quarter"] for row in rows for key in unit_value_columns if number(row, key) is not None and not math.isfinite(number(row, key))]
    annual = defaultdict(lambda: {"construction": 0.0, "total": 0.0})
    quarter_shares = defaultdict(list)
    for row in rows:
        construction, total = number(row, "gdp_real2015_construction"), number(row, "gdp_real2015_total")
        if construction is not None and total is not None:
            annual[row["quarter"][:4]]["construction"] += construction
            annual[row["quarter"][:4]]["total"] += total
            quarter_shares[row["quarter"][-2:]].append(100 * construction / total)
    construction_growth = {}
    for year in sorted(annual):
        previous = annual.get(str(int(year) - 1))
        if previous and previous["construction"]:
            construction_growth[year] = 100 * (annual[year]["construction"] / previous["construction"] - 1)
    report = {
        "dataset": "m4-quarterly-v1",
        "rows": len(rows),
        "period_start": quarters[0] if rows else None,
        "period_end": quarters[-1] if rows else None,
        "checks": {
            "duplicate_quarters": duplicate_keys(rows, ("quarter",)),
            "quarters_non_decreasing": is_non_decreasing(quarters),
            "negative_merchandise_exports": negative_periods(rows, ["exports_usd_million"]),
            "negative_merchandise_imports": negative_periods(rows, ["imports_usd_million"]),
            "negative_government_revenue": negative_periods(rows, ["government_revenue_mnt_million"]),
            "negative_government_expenditure": negative_periods(rows, ["government_expenditure_mnt_million"]),
            "negative_government_capital_expenditure": negative_periods(rows, ["government_capital_expenditure_mnt_million"]),
            "trade_turnover_identity_failures": trade_turnover_failures,
            "trade_balance_identity_failures": balance_failures,
            "commodity_negative_quantities": negative_periods(rows, commodity_quantity),
            "commodity_negative_values": negative_periods(rows, commodity_value),
            "commodity_unit_value_nonfinite": sorted(set(unit_value_invalid)),
            "missing_gdp_nominal_total": [row["quarter"] for row in rows if number(row, "gdp_nominal_total") is None],
            "coverage_nonmissing": {key: {"start": next((r["quarter"] for r in rows if number(r, key) is not None), None), "end": next((r["quarter"] for r in reversed(rows) if number(r, key) is not None), None), "count": sum(number(r, key) is not None for r in rows)} for key in ["gdp_real2005_total", "gdp_real2010_total", "gdp_real2015_total", "cpi_index_2015", "cpi_index_2020", "cpi_index_2023"]},
            "construction_cross_check": {"annual_growth_pct": construction_growth, "annual_share_pct": {year: 100 * values["construction"] / values["total"] for year, values in annual.items()}, "average_quarter_share_pct": {quarter: sum(values) / len(values) for quarter, values in quarter_shares.items()}},
            "seasonal_adjustment": "none",
            "interpolation": "none",
        },
        "warnings": [
            "m4-quarterly-v0.csv is deprecated and invalid for analysis; it retained incorrect trade mappings/units and de-cumulated direct fiscal flows.",
            "GDP constant-price vintages are kept as separate series; no cross-base concatenation or linked level is constructed.",
            "CPI bases are kept separately; no casual splice is performed.",
            "Commodity cumulative observations are de-cumulated within calendar year before quarterly summation.",
            "Official GDP and construction series are not seasonally adjusted.",
        ],
    }
    OUTPUT.write_text(json.dumps(report, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    failures = {key: value for key, value in report["checks"].items() if isinstance(value, list) and value}
    if failures:
        raise SystemExit(f"Validation failures: {failures}")
    print(f"Wrote {OUTPUT}; all hard validation checks passed for {len(rows)} quarters.")


if __name__ == "__main__":
    main()
