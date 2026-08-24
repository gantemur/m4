"""Retrieve official NSO data and build the corrected Phase 1A v1 panel."""

from __future__ import annotations

import csv
import hashlib
import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from m4.data import NsoClient, parse_jsonstat2
from m4.data.transforms import cumulative_monthly_to_flow, implied_unit_value, monthly_average_to_quarterly, monthly_flow_to_quarterly
from m4.data.versioning import detect_revisions

ROOT = Path(__file__).resolve().parents[1]
RUN_DATE = datetime.now(timezone.utc).strftime("%Y-%m-%dT%H%M%SZ")
RAW_DIR = ROOT / "data/raw/nso"
SNAPSHOT_DIR = ROOT / f"data/snapshots/nso/{RUN_DATE}"
PROCESSED_DIR = ROOT / "data/processed"
METADATA_DIR = ROOT / "data/metadata/series"
REVISION_DIR = ROOT / "data/metadata/revisions"

GDP = "Economy%2C%20environment/National%20Accounts/DT_NSO_0500_004V1.px"
TRADE_TOTAL = "Economy%2C%20environment/Foreign%20Trade/DT_NSO_1400_003V1.px"
TRADE_COMMODITY = "Economy%2C%20environment/Foreign%20Trade/DT_NSO_1400_006V2_month.px"
REVENUE = "Economy%2C%20environment/Government%20budget/DT_NSO_0800_002V1.px"
EXPENDITURE = "Economy%2C%20environment/Government%20budget/DT_NSO_0800_005V1.px"
CPI = "Economy%2C%20environment/Consumer%20Price%20Index/DT_NSO_0600_001V3.px"


def normalize_quarter(label: str) -> str:
    year, raw = label.split("-", 1)
    raw = raw.upper()
    quarter = {"I": 1, "II": 2, "III": 3, "IV": 4}.get(raw)
    if quarter is None:
        quarter = int(raw)
    return f"{int(year)}-Q{quarter}"


def all_values(metadata: dict[str, Any], dimension: int) -> list[str]:
    return list(metadata["variables"][dimension]["values"])


def fetch(client: NsoClient, table: str, selections: dict[str, list[str]]) -> tuple[dict[str, Any], list[dict[str, Any]]]:
    # Keep the ignored raw cache immutable per retrieval run as well as the
    # compact, versioned normalized snapshot.
    dataset = client.query_dataset(table, selections, raw_directory=RAW_DIR / RUN_DATE)
    return dataset, parse_jsonstat2(dataset)


def source_checksum(dataset: dict[str, Any]) -> str:
    encoded = json.dumps(dataset, ensure_ascii=False, sort_keys=True, separators=(",", ":")).encode("utf-8")
    return hashlib.sha256(encoded).hexdigest()


def requested(metadata: dict[str, Any], selections: dict[str, list[str]]) -> list[dict[str, str]]:
    records = []
    for variable in metadata["variables"]:
        if variable["code"] not in selections:
            continue
        selected = set(selections[variable["code"]])
        records.extend({"dimension_name": variable["code"], "source_code": code, "source_label": str(label).strip()}
                       for code, label in zip(variable["values"], variable["valueTexts"]) if code in selected)
    return records


def write_snapshot(name: str, table: str, dataset: dict[str, Any], rows: list[dict[str, Any]], unit: str, frequency: str, transformation: str, selections: list[dict[str, str]]) -> dict[str, Any]:
    output = SNAPSHOT_DIR / f"{name}.csv"
    dimensions = dataset["id"]
    period_dimension = dimensions[-1]
    series_dimension = dimensions[-2] if len(dimensions) > 1 else dimensions[0]
    records = [{"period": row[period_dimension], "series_id": str(row.get(f"{series_dimension}_id", "")), "series_label": str(row.get(series_dimension, "")).strip(), "value": row["value"]} for row in rows]
    records.sort(key=lambda row: (str(row["period"]), row["series_id"]))
    with output.open("w", newline="", encoding="utf-8") as stream:
        writer = csv.DictWriter(stream, fieldnames=["period", "series_id", "series_label", "value"])
        writer.writeheader()
        writer.writerows(records)
    return {"snapshot_id": f"nso-{RUN_DATE}-{name}", "source": "National Statistics Office of Mongolia", "source_url": f"https://data.1212.mn/api/v1/en/NSO/{table}", "table_id": table.rsplit("/", 1)[-1], "retrieved_at_utc": datetime.now(timezone.utc).isoformat(), "raw_response_checksum_sha256": source_checksum(dataset), "schema": {"dimensions": dataset["id"], "sizes": dataset["size"], "format": "json-stat2"}, "unit": unit, "native_frequency": frequency, "transformation": transformation, "requested_dimensions": selections, "file": str(output.relative_to(ROOT))}


def main() -> None:
    if SNAPSHOT_DIR.exists():
        raise SystemExit(f"Refusing to overwrite existing snapshot: {SNAPSHOT_DIR}")
    previous_dirs = sorted(path for path in (ROOT / "data/snapshots/nso").glob("*") if path.is_dir())
    previous_snapshot_dir = previous_dirs[-1] if previous_dirs else None
    client = NsoClient()
    SNAPSHOT_DIR.mkdir(parents=True, exist_ok=False)
    manifests: list[dict[str, Any]] = []
    panel: dict[str, dict[str, Any]] = {}

    # GDP: retain each official vintage separately; never concatenate bases.
    metadata = client.metadata(GDP)
    ind_dim, comp_dim, time_dim = [v["code"] for v in metadata["variables"]]
    indicators = client.codes_for_labels(metadata, ind_dim, ["GDP, at current prices", "GDP, at 2005 constant prices", "GDP, at 2010 constant prices", "GDP, at 2015 constant prices"])
    compositions = client.codes_for_labels(metadata, comp_dim, ["GDP", "Agriculture, forestry, fishing and hunting", "Mining and quarrying", "Construction"])
    selections = {ind_dim: list(indicators.values()), comp_dim: list(compositions.values()), time_dim: all_values(metadata, 2)}
    dataset, rows = fetch(client, GDP, selections)
    comp_names = {compositions["GDP"]: "total", compositions["Agriculture, forestry, fishing and hunting"]: "agriculture", compositions["Mining and quarrying"]: "mining", compositions["Construction"]: "construction"}
    vintage_names = {indicators["GDP, at current prices"]: "nominal", indicators["GDP, at 2005 constant prices"]: "real2005", indicators["GDP, at 2010 constant prices"]: "real2010", indicators["GDP, at 2015 constant prices"]: "real2015"}
    for row in rows:
        target = f"gdp_{vintage_names[str(row[f'{ind_dim}_id'])]}_{comp_names[str(row[f'{comp_dim}_id'])]}"
        panel.setdefault(normalize_quarter(str(row[time_dim])), {})[target] = row["value"]
    manifests.append(write_snapshot("gdp_quarterly", GDP, dataset, rows, "million MNT", "quarterly", "official nominal and constant-price vintages retained separately", requested(metadata, selections)))

    # Trade: semantic labels, correct USD-million unit, and all accounting series.
    metadata = client.metadata(TRADE_TOTAL)
    trade_dim, trade_period = [v["code"] for v in metadata["variables"]]
    trade_labels = client.codes_for_labels(metadata, trade_dim, ["Total turnover", "Exports", "Imports", "Balance"])
    selections = {trade_dim: list(trade_labels.values()), trade_period: all_values(metadata, 1)}
    dataset, rows = fetch(client, TRADE_TOTAL, selections)
    targets = {"Exports": "exports_usd_million", "Imports": "imports_usd_million", "Total turnover": "trade_turnover_usd_million", "Balance": "trade_balance_usd_million"}
    for label, code in trade_labels.items():
        monthly = [{"period": row[trade_period], "value": row["value"]} for row in rows if str(row[f"{trade_dim}_id"]) == code]
        for quarter, value in monthly_flow_to_quarterly(monthly, "period", "value").items():
            panel.setdefault(quarter, {})[targets[label]] = value
    manifests.append(write_snapshot("trade_total_monthly", TRADE_TOTAL, dataset, rows, "USD million", "monthly flow", "semantic Export/Import/Total turnover/Balance values summed to quarter", requested(metadata, selections)))

    # Commodity exports: preserve cumulative convention and de-cumulate exactly once.
    metadata = client.metadata(TRADE_COMMODITY)
    indicator_dim, commodity_dim, commodity_period = [v["code"] for v in metadata["variables"]]
    indicator_labels = client.codes_for_labels(metadata, indicator_dim, ["Volume", "Value(USD.thous)"])
    commodity_labels = client.codes_for_labels(metadata, commodity_dim, ["Gold, unwrought or in semi-manufactured forms (t)", "Copper ores and concentrate (thous.t)", "Iron ores & concentrates (thous.t)", "Coal (thous.t)"])
    selections = {indicator_dim: list(indicator_labels.values()), commodity_dim: list(commodity_labels.values()), commodity_period: all_values(metadata, 2)}
    dataset, rows = fetch(client, TRADE_COMMODITY, selections)
    names = {(commodity_labels["Coal (thous.t)"], indicator_labels["Volume"]): "coal_export_quantity_thousand_t", (commodity_labels["Coal (thous.t)"], indicator_labels["Value(USD.thous)"]): "coal_export_value_usd_thousand", (commodity_labels["Copper ores and concentrate (thous.t)"], indicator_labels["Volume"]): "copper_concentrate_export_quantity_thousand_t", (commodity_labels["Copper ores and concentrate (thous.t)"], indicator_labels["Value(USD.thous)"]): "copper_concentrate_export_value_usd_thousand", (commodity_labels["Gold, unwrought or in semi-manufactured forms (t)"], indicator_labels["Volume"]): "gold_export_quantity_t", (commodity_labels["Gold, unwrought or in semi-manufactured forms (t)"], indicator_labels["Value(USD.thous)"]): "gold_export_value_usd_thousand", (commodity_labels["Iron ores & concentrates (thous.t)"], indicator_labels["Volume"]): "iron_ore_export_quantity_thousand_t", (commodity_labels["Iron ores & concentrates (thous.t)"], indicator_labels["Value(USD.thous)"]): "iron_ore_export_value_usd_thousand"}
    for (commodity_id, indicator_id), target in names.items():
        monthly = [{"period": row[commodity_period], "value": row["value"]} for row in rows if str(row[f"{commodity_dim}_id"]) == commodity_id and str(row[f"{indicator_dim}_id"]) == indicator_id]
        for quarter, value in monthly_flow_to_quarterly(cumulative_monthly_to_flow(monthly, "period", "value"), "period", "value").items():
            panel.setdefault(quarter, {})[target] = value
    manifests.append(write_snapshot("trade_main_commodities_monthly_cumulative", TRADE_COMMODITY, dataset, rows, "commodity-specific (see labels)", "monthly cumulative flow", "cumulative values de-cumulated within calendar year and summed to quarter", requested(metadata, selections)))

    # Fiscal tables: indicator Month is a direct monthly flow; do not de-cumulate.
    for table, name, class_labels, targets in ((REVENUE, "budget_revenue_monthly_flow", ["Total revenue and grants"], {"Total revenue and grants": "government_revenue_mnt_million"}), (EXPENDITURE, "budget_expenditure_monthly_flow", ["Total expenditure and net lending", "Capital expenditure"], {"Total expenditure and net lending": "government_expenditure_mnt_million", "Capital expenditure": "government_capital_expenditure_mnt_million"})):
        metadata = client.metadata(table)
        ind_dim, class_dim, period_dim = [v["code"] for v in metadata["variables"]]
        indicator = client.codes_for_labels(metadata, ind_dim, ["Month"])
        classes = client.codes_for_labels(metadata, class_dim, class_labels)
        selections = {ind_dim: list(indicator.values()), class_dim: list(classes.values()), period_dim: all_values(metadata, 2)}
        dataset, rows = fetch(client, table, selections)
        manifests.append(write_snapshot(name, table, dataset, rows, "million MNT", "monthly flow", "Month flow summed directly to quarter; no de-cumulation", requested(metadata, selections)))
        for label, code in classes.items():
            monthly = [{"period": row[period_dim], "value": row["value"]} for row in rows if str(row[f"{class_dim}_id"]) == code]
            for quarter, value in monthly_flow_to_quarterly(monthly, "period", "value").items():
                panel.setdefault(quarter, {})[targets[label]] = value

    # CPI: retain official bases independently; no casual splicing.
    metadata = client.metadata(CPI)
    base_dim, group_dim, cpi_period = [v["code"] for v in metadata["variables"]]
    bases = client.codes_for_labels(metadata, base_dim, ["2015=100", "2020=100", "2023=100"])
    groups = client.codes_for_labels(metadata, group_dim, ["Overall  index"])
    selections = {base_dim: list(bases.values()), group_dim: list(groups.values()), cpi_period: all_values(metadata, 2)}
    dataset, rows = fetch(client, CPI, selections)
    for label, code in bases.items():
        monthly = [{"period": row[cpi_period], "value": row["value"]} for row in rows if str(row[f"{base_dim}_id"]) == code]
        for quarter, value in monthly_average_to_quarterly(monthly, "period", "value").items():
            panel.setdefault(quarter, {})[f"cpi_index_{label.split('=')[0]}"] = value
    manifests.append(write_snapshot("cpi_national_monthly_all_bases", CPI, dataset, rows, "index (base-specific)", "monthly index", "each official base averaged separately; no splicing or seasonal adjustment", requested(metadata, selections)))

    for values in panel.values():
        values["coal_implied_export_unit_value_usd_per_t"] = implied_unit_value(values.get("coal_export_value_usd_thousand"), values.get("coal_export_quantity_thousand_t"))
        values["copper_concentrate_implied_export_unit_value_usd_per_t"] = implied_unit_value(values.get("copper_concentrate_export_value_usd_thousand"), values.get("copper_concentrate_export_quantity_thousand_t"))
    periods = [period for period in sorted(panel) if period >= "2000-Q1" and panel[period].get("gdp_nominal_total") is not None]
    columns = sorted({key for values in panel.values() for key in values})
    PROCESSED_DIR.mkdir(parents=True, exist_ok=True)
    output = PROCESSED_DIR / "m4-quarterly-v1.csv"
    with output.open("w", newline="", encoding="utf-8") as stream:
        writer = csv.DictWriter(stream, fieldnames=["quarter", *columns])
        writer.writeheader()
        for quarter in periods:
            writer.writerow({"quarter": quarter, **panel[quarter]})

    def snapshot_id(fragment: str) -> str:
        return next(item["snapshot_id"] for item in manifests if fragment in item["snapshot_id"])

    variable_metadata: dict[str, dict[str, Any]] = {}
    for column in columns:
        if column.startswith("gdp_"):
            info = (snapshot_id("gdp_quarterly"), "million MNT", "quarterly", "official vintage retained separately")
        elif column.endswith("_usd_million"):
            info = (snapshot_id("trade_total_monthly"), "USD million", "monthly→quarterly", "semantic monthly flow summed to quarter")
        elif "implied_export_unit_value" in column:
            info = (snapshot_id("trade_main_commodities"), "USD/t", "monthly→quarterly", "matching cumulative value and quantity de-cumulated, summed, then divided")
        elif "_export_" in column:
            info = (snapshot_id("trade_main_commodities"), "source-labelled", "monthly→quarterly", "cumulative flow de-cumulated within year and summed")
        elif column == "government_revenue_mnt_million":
            info = (snapshot_id("budget_revenue"), "million MNT", "monthly→quarterly", "Month flow summed directly to quarter")
        elif column.startswith("government_"):
            info = (snapshot_id("budget_expenditure"), "million MNT", "monthly→quarterly", "Month flow summed directly to quarter")
        elif column.startswith("cpi_index_"):
            info = (snapshot_id("cpi_national"), f"index ({column.split('_')[-1]}=100)", "monthly→quarterly", "official base averaged separately")
        else:
            info = (None, None, None, "derived or unresolved")
        variable_metadata[column] = {"source_snapshot_id": info[0], "unit": info[1], "frequency": info[2], "transformation": info[3]}
    manifest = {"dataset_id": "m4-quarterly-v1", "created_at_utc": datetime.now(timezone.utc).isoformat(), "period_start": periods[0], "period_end": periods[-1], "seasonal_adjustment": "none", "source_snapshots": [item["snapshot_id"] for item in manifests], "variables": variable_metadata, "notes": ["m4-quarterly-v0.csv is deprecated and invalid for analysis due to Phase 1A extraction errors.", "No GDP core residual is computed; tax/subsidies accounting convention is not yet resolved.", "Missing observations remain empty; no interpolation or source substitution is performed."]}
    METADATA_DIR.mkdir(parents=True, exist_ok=True)
    (METADATA_DIR / "m4-quarterly-v1.json").write_text(json.dumps(manifest, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    (SNAPSHOT_DIR / "manifest.json").write_text(json.dumps({"snapshot_date": RUN_DATE, "snapshots": manifests}, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    revision_report = {"new_snapshot": RUN_DATE, "previous_snapshot": previous_snapshot_dir.name if previous_snapshot_dir else None, "files": []}
    if previous_snapshot_dir:
        for item in manifests:
            previous_file = ROOT / item["file"].replace(RUN_DATE, previous_snapshot_dir.name)
            current_file = ROOT / item["file"]
            if not previous_file.exists():
                revision_report["files"].append({"file": item["file"], "status": "added"})
                continue
            with previous_file.open(encoding="utf-8", newline="") as stream:
                old_rows = list(csv.DictReader(stream))
            with current_file.open(encoding="utf-8", newline="") as stream:
                new_rows = list(csv.DictReader(stream))
            revision_report["files"].append({"file": item["file"], "changes": detect_revisions(old_rows, new_rows)})
    REVISION_DIR.mkdir(parents=True, exist_ok=True)
    (REVISION_DIR / f"revision-{RUN_DATE}.json").write_text(json.dumps(revision_report, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    print(f"Wrote {output} with {len(periods)} quarters and {len(columns)} variables.")


if __name__ == "__main__":
    main()
