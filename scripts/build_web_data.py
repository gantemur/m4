"""Build the small, reviewable static bundle used by the GitHub Pages alpha."""
from __future__ import annotations

import csv
import json
from dataclasses import asdict
from pathlib import Path

from m4.fiscal import ReferencePrice, RoyaltyInput, evaluate_royalty
from m4.model import AssumptionLinks, Baseline, Closure, Scenario, Shock

ROOT = Path(__file__).resolve().parents[1]
PANEL = ROOT / "data/processed/m4-quarterly-v4.csv"
OUT = ROOT / "web/data"
FIXTURES = ROOT / "tests/fixtures/model-parity"
PUBLIC_COLUMNS = (
    "coal_export_quantity_thousand_t", "coal_export_value_usd_thousand",
    "copper_concentrate_export_quantity_thousand_t", "copper_concentrate_export_value_usd_thousand",
    "gold_export_quantity_t", "gold_export_value_usd_thousand", "iron_ore_export_quantity_thousand_t",
    "iron_ore_export_value_usd_thousand", "exports_usd_million", "imports_usd_million",
    "trade_balance_usd_million", "government_revenue_mnt_million", "government_expenditure_mnt_million",
    "mnt_per_usd_quarterly_average", "gdp_real2015_mining", "gdp_real2015_agriculture",
    "gdp_real2015_construction", "gdp_nominal_mining", "gdp_nominal_agriculture",
    "gdp_nominal_construction", "other_industry_gva_nominal_mnt_million",
    "taxes_less_subsidies_nominal_mnt_million", "gdp_nominal_total",
)


def clean(row: dict[str, str]) -> dict[str, float | None]:
    return {key: (None if row.get(key, "") in {"", "None"} else float(row[key])) for key in PUBLIC_COLUMNS}


def scenario_fixture(name: str, baseline: dict, shocks=(), links=None, closure=Closure.HISTORICAL_DEFAULT):
    b = Baseline({"2023-Q1": baseline})
    result = Scenario(closure=closure, shocks=list(shocks), links=links or AssumptionLinks()).run(b)
    return {"name": name, "baseline": {"2023-Q1": baseline}, "units": {key: b.unit(key) for key in baseline}, "closure": closure.value,
            "shocks": [{"column": s.column, "multiplier": s.multiplier, "quarters": list(s.quarters)} for s in shocks],
            "links": asdict(links or AssumptionLinks()), "expected": result.to_dict()}


def main() -> None:
    panel = Baseline.load(PANEL)
    failures = panel.replay_checks()
    if any(failures.values()):
        raise SystemExit(f"Refusing public build: accounting validation failed: {failures}")
    safe = {q: {k: panel.rows[q].get(k) for k in PUBLIC_COLUMNS} for q in sorted(panel.rows)
            if all(panel.rows[q].get(k) is not None for k in PUBLIC_COLUMNS)}
    meta = json.loads((ROOT / "data/metadata/series/m4-quarterly-v4.json").read_text(encoding="utf-8"))
    OUT.mkdir(parents=True, exist_ok=True)
    (OUT / "public-alpha-v1.json").write_text(json.dumps({
        "bundle_version": "public-alpha-v1", "model_version": "M4 v0", "data_version": meta["dataset_id"],
        "source_snapshot": meta["source_snapshot"], "units": {
            "exports_usd_million": "USD million", "imports_usd_million": "USD million", "trade_balance_usd_million": "USD million",
            "government_revenue_mnt_million": "million MNT", "government_expenditure_mnt_million": "million MNT",
            "mnt_per_usd_quarterly_average": "MNT/USD", "coal_export_quantity_thousand_t": "thousand tonnes",
            "copper_concentrate_export_quantity_thousand_t": "thousand tonnes", "coal_export_value_usd_thousand": "USD thousand",
            "copper_concentrate_export_value_usd_thousand": "USD thousand", "gdp_real2015_mining": "million MNT, 2015 prices",
            "gdp_real2015_agriculture": "million MNT, 2015 prices", "gdp_real2015_construction": "million MNT, 2015 prices"},
        "provenance": {"institution": "National Statistics Office of Mongolia / Bank of Mongolia", "panel_metadata": "../data/metadata/series/m4-quarterly-v4.json", "note": "Historical observations only; no missing values were interpolated."},
        "quarters": safe}, ensure_ascii=False, separators=(",", ":")) + "\n", encoding="utf-8")
    rules = json.loads((ROOT / "data/metadata/project-fiscal-rules/ett-coal-royalty-v0.json").read_text(encoding="utf-8"))
    review = json.loads((ROOT / "data/metadata/mrpam-price-review-v0.json").read_text(encoding="utf-8"))
    reviewed_prices = [row for row in review["records"] if row["review_status"] == "REVIEWED"]
    keys = [(row["applicable_royalty_month"], row["mrpam_product_id"]) for row in reviewed_prices]
    if len(keys) != len(set(keys)) or any(not row.get("units") or not row.get("source_url") or not row.get("source_checksum_sha256") for row in reviewed_prices):
        raise SystemExit("Refusing public build: reviewed MRPAM records fail provenance or duplicate-key validation")
    if any(row.get("public") is True and row["review_status"] != "REVIEWED" for row in review["records"]):
        raise SystemExit("Refusing public build: unreviewed MRPAM record marked public")
    if not review.get("legal_checked_at") or not any(item["rule_version"] == "general_export_reference_2019" and item["effective_to"] is None for item in rules["legal_regimes"]):
        raise SystemExit("Refusing public build: royalty legal-date coverage is inconsistent")
    rules["legal_checked_at"] = review["legal_checked_at"]
    (OUT / "ett-coal-royalty-v0.json").write_text(json.dumps(rules, ensure_ascii=False, separators=(",", ":")) + "\n", encoding="utf-8")
    (OUT / "mrpam-reviewed-coal-prices-v0.json").write_text(json.dumps({
        "dataset_id": review["dataset_id"], "institution": review["institution"], "retrieved_at": review["retrieved_at"],
        "review_policy": review["review_policy"], "records": reviewed_prices}, ensure_ascii=False, separators=(",", ":")) + "\n", encoding="utf-8")

    baseline = {k: panel.rows["2023-Q1"].get(k) for k in PUBLIC_COLUMNS}
    cases = [
        scenario_fixture("coal_quantity_minus_30", baseline, [Shock("coal_export_quantity_thousand_t", .7, ("2023-Q1",))]),
        scenario_fixture("copper_price_plus_20", baseline, [Shock("copper_concentrate_export_price", 1.2, ("2023-Q1",))]),
        scenario_fixture("imports_plus_10", baseline, [Shock("imports_usd_million", 1.1, ("2023-Q1",))]),
        scenario_fixture("fx_only", baseline, [Shock("mnt_per_usd_quarterly_average", 1.1, ("2023-Q1",))]),
        scenario_fixture("agriculture_output", baseline, [Shock("agriculture_real_output", .9, ("2023-Q1",))]),
        scenario_fixture("lambda_revenue", baseline, [Shock("coal_export_quantity_thousand_t", .7, ("2023-Q1",))], AssumptionLinks(lambda_revenue=.1)),
        scenario_fixture("phi_response", baseline, [Shock("coal_export_quantity_thousand_t", .7, ("2023-Q1",))], AssumptionLinks(lambda_revenue=.1, phi_revenue_to_expenditure=.5), Closure.USER_SPECIFIED_FISCAL_RESPONSE),
        scenario_fixture("missing_link", baseline, [Shock("coal_production_thousand_t", .7, ("2023-Q1",))]),
    ]
    FIXTURES.mkdir(parents=True, exist_ok=True)
    for case in cases:
        (FIXTURES / f"{case['name']}.json").write_text(json.dumps(case, ensure_ascii=False, sort_keys=True) + "\n", encoding="utf-8")
    royalty_cases = []
    for product, price in (("raw_coal", 25), ("raw_coal", 125.01), ("processed_coal", 130), ("final_coal_product", 270.01)):
        value = evaluate_royalty(RoyaltyInput("2026-08", 1000, product, ReferencePrice(price, "2026-08", "2026-08-11", "https://mrpam.gov.mn/", product_label="manual"), 3500))
        royalty_cases.append({"input": {"transaction_month": "2026-08", "quantity_tonnes": 1000, "product_class": product, "price_usd_per_tonne": price, "mnt_per_usd": 3500}, "expected": asdict(value)})
    royalty_cases += [{"input": {"transaction_month": "2025-10", "quantity_tonnes": 1, "product_class": "raw_coal", "price_usd_per_tonne": 50, "mnt_per_usd": 3500, "valuation_regime": "mse_temporary_2025"}, "expected_status": "NOT_DETERMINED_UNDER_CURRENT_CLOSURE"}, {"input": {"transaction_month": "2026-08", "quantity_tonnes": None, "product_class": "raw_coal", "price_usd_per_tonne": 50, "mnt_per_usd": 3500}, "expected_status": "NOT_DETERMINED_UNDER_CURRENT_CLOSURE"}]
    (FIXTURES / "royalty.json").write_text(json.dumps(royalty_cases, ensure_ascii=False, sort_keys=True) + "\n", encoding="utf-8")
    print(f"Built web bundle for {len(safe)} historical quarters and {len(cases)} model fixtures.")


if __name__ == "__main__":
    main()
