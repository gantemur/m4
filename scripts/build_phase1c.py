"""Build the Phase 1C extended panel from official BoM and NSO sources."""
from __future__ import annotations

import csv, hashlib, json
from collections import defaultdict
from datetime import datetime, timezone
from pathlib import Path
from urllib.request import Request, urlopen

from m4.data import NsoClient, parse_jsonstat2
from m4.data.transforms import monthly_average_to_quarterly, monthly_stock_to_quarter_end

ROOT = Path(__file__).resolve().parents[1]
RUN = datetime.now(timezone.utc).strftime("%Y-%m-%dT%H%M%SZ")
SNAP = ROOT / f"data/snapshots/nso/{RUN}"
BOM_SNAP = ROOT / f"data/snapshots/bom/{RUN}"
RAW = ROOT / "data/raw/phase1c" / RUN
PANEL = ROOT / "data/processed/m4-quarterly-v1.csv"
OUT = ROOT / "data/processed/m4-quarterly-v2.csv"

GDP_CHAIN = "Economy%2C%20environment/National%20Accounts/DT_NSO_0500_001V4.px"
GDP_EXP = "Economy%2C%20environment/National%20Accounts/DT_NSO_0500_003V1_quarter.px"
GFCF = "Economy%2C%20environment/National%20Accounts/DT_NSO_0500_020V1.px"
EMP = "Labour%2C%20business/Labour/EMPLOYMENT%2C%20by%20economic%20activities%2C%20sex%2C%20age%20group%2C%20aimags%20and%20the%20Capital/DT_NSO_0400_035V7_2.px"
CREDIT = "Economy%2C%20environment/Money%20and%20Finance/DT_NSO_0700_002V2.px"


def post_json(path: str, payload: dict) -> dict:
    req = Request("https://www.mongolbank.mn/en/" + path, data=json.dumps(payload).encode(), headers={"Content-Type": "application/json"}, method="POST")
    return json.loads(urlopen(req, timeout=60).read())


def checksum(value: object) -> str:
    return hashlib.sha256(json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(",", ":")).encode()).hexdigest()


def codes(client: NsoClient, metadata: dict, dim: str, labels: list[str]) -> dict[str, str]:
    return client.codes_for_labels(metadata, dim, labels)


def write_rows(path: Path, rows: list[dict], fields: list[str]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", newline="", encoding="utf-8") as stream:
        writer = csv.DictWriter(stream, fieldnames=fields); writer.writeheader(); writer.writerows(rows)


def nso_extract(client: NsoClient, table: str, selections: dict[str, list[str]], name: str, unit: str, frequency: str, transform: str):
    metadata = client.metadata(table)
    dataset = client.query_dataset(table, selections, raw_directory=RAW)
    rows = parse_jsonstat2(dataset)
    dimensions = dataset["id"]; period = dimensions[-1]; series = dimensions[-2] if len(dimensions) > 1 else dimensions[0]
    normalized = [{"period": row[period], "series_id": str(row.get(f"{series}_id", "")), "series_label": str(row.get(series, "")).strip(), "value": row["value"]} for row in rows]
    write_rows(SNAP / f"{name}.csv", normalized, ["period", "series_id", "series_label", "value"])
    return metadata, dataset, rows, {"snapshot_id": f"nso-{RUN}-{name}", "source_url": "https://data.1212.mn/api/v1/en/NSO/" + table, "unit": unit, "native_frequency": frequency, "transformation": transform, "checksum": checksum(dataset), "file": str((SNAP / f"{name}.csv").relative_to(ROOT))}


def main() -> None:
    client = NsoClient(); SNAP.mkdir(parents=True, exist_ok=False); BOM_SNAP.mkdir(parents=True, exist_ok=False); RAW.mkdir(parents=True, exist_ok=True)
    manifests = []; panel = {r["quarter"]: dict(r) for r in csv.DictReader(PANEL.open(encoding="utf-8", newline=""))}

    # BoM daily official FX endpoint: USD is MNT per USD, so increases mean depreciation.
    bom_records = []
    # The daily page endpoint returns the latest point; its historical tab uses
    # this structured movement endpoint and honors the requested date range.
    fx = post_json("currency-rate-movement/data", {"startDate": "2000-01-01", "endDate": datetime.now(timezone.utc).strftime("%Y-%m-%d")})
    (RAW / "bom-currency-rates.json").write_text(json.dumps(fx, ensure_ascii=False) + "\n", encoding="utf-8")
    if not fx.get("success"): raise RuntimeError("BoM FX endpoint failed: " + str(fx.get("data")))
    for row in fx["data"]:
        if row.get("USD") not in (None, ""):
            bom_records.append({"date": row["RATE_DATE"], "mnt_per_usd": float(str(row["USD"]).replace(",", ""))})
    bom_records.sort(key=lambda row: row["date"])
    write_rows(BOM_SNAP / "currency-rates-daily.csv", bom_records, ["date", "mnt_per_usd"])
    fx_month = defaultdict(list)
    for row in bom_records: fx_month[row["date"][:7]].append(row["mnt_per_usd"])
    fx_q = defaultdict(list)
    for month, values in fx_month.items():
        y, m = map(int, month.split("-")); fx_q[f"{y}-Q{(m-1)//3+1}"].extend(values)
    for q, values in fx_q.items():
        panel.setdefault(q, {})["mnt_per_usd_quarterly_average"] = sum(values) / len(values); panel[q]["mnt_per_usd_quarter_end"] = values[-1]
    manifests.append({"snapshot_id": f"bom-{RUN}-currency-rates-daily", "source_url": "https://www.mongolbank.mn/en/currency-rate-movement", "endpoint": "/en/currency-rate-movement/data POST", "unit": "MNT per USD", "frequency": "daily", "transformation": "quarterly mean and last observation", "coverage": [bom_records[0]["date"], bom_records[-1]["date"]], "raw_checksum": checksum(fx)})

    # Record transparent endpoint failures; no substitutes are used.
    bom_failures = []
    for name, endpoint in [("reserves", "international-reserves/data"), ("policy_rate", "policy-interest-rate/data")]:
        try: result = post_json(endpoint, {"startDate": "2000-01-01", "endDate": datetime.now(timezone.utc).strftime("%Y-%m-%d")})
        except Exception as exc: result = {"success": False, "data": str(exc)}
        (RAW / f"bom-{name}.json").write_text(json.dumps(result, ensure_ascii=False) + "\n", encoding="utf-8")
        if not result.get("success"): bom_failures.append({"series": name, "endpoint": "/en/" + endpoint, "status": "FAILED", "reason": result.get("data")})

    # Chain-linked GDP publishes growth/contribution measures, not levels.
    metadata = client.metadata(GDP_CHAIN); ind, section, year = [v["code"] for v in metadata["variables"]]
    inds = codes(client, metadata, ind, ["Year over year /Compared to same period of prevoius year/"]); secs = codes(client, metadata, section, ["Total", "Agriculture, forestry, fishing and hunting", "Mining and quarrying", "Construction"])
    sel = {ind: list(inds.values()), section: list(secs.values()), year: [v for v in metadata["variables"][2]["values"]]}; _, _, rows, manifest = nso_extract(client, GDP_CHAIN, sel, "gdp_chainlinked_growth_quarterly", "percent / percentage-point measure", "quarterly", "official chain-linked YoY indicator retained; no level reconstruction"); manifests.append(manifest)
    for row in rows:
        q = row[year].replace("-", "-Q") if "-" in row[year] else row[year]
        label = str(row[section]).strip(); value = row["value"]
        if str(row[f"{ind}_id"]) == list(inds.values())[0] and value is not None:
            target = {"Total": "gdp_chainlinked_yoy_total", "Agriculture, forestry, fishing and hunting": "gdp_chainlinked_yoy_agriculture", "Mining and quarrying": "gdp_chainlinked_yoy_mining", "Construction": "gdp_chainlinked_yoy_construction"}.get(label)
            if target: panel.setdefault(q, {})[target] = value

    # Expenditure-side current-price components; gross capital formation is not relabelled GFCF.
    metadata = client.metadata(GDP_EXP); ind, comp, period = [v["code"] for v in metadata["variables"]]
    indmap = codes(client, metadata, ind, ["GDP, at current prices"]); compmap = codes(client, metadata, comp, ["GDP", "Household consumption, NPISHs consumption", "Government consumption", "Gross capital formation", "Gross fixed capital formation", "Net exports"])
    sel = {ind: list(indmap.values()), comp: list(compmap.values()), period: all_values(metadata, 2)}
    _, _, rows, manifest = nso_extract(client, GDP_EXP, sel, "gdp_expenditure_current_quarterly", "million MNT", "quarterly flow", "official current-price expenditure components retained"); manifests.append(manifest)
    targets = {"GDP": "gdp_expenditure_current", "Household consumption, NPISHs consumption": "household_consumption_current", "Government consumption": "government_consumption_current", "Gross capital formation": "gross_capital_formation_current", "Gross fixed capital formation": "gross_fixed_capital_formation_current", "Net exports": "net_exports_current"}
    for row in rows:
        target = targets.get(str(row[comp]).strip()); q = row[period].replace("-", "-Q")
        if target and row["value"] is not None: panel.setdefault(q, {})[target] = row["value"]

    # Annual GFCF by industry is kept separate and never interpolated.
    metadata = client.metadata(GFCF); act, yr = [v["code"] for v in metadata["variables"]]; amap = codes(client, metadata, act, ["Total", "Mining and quarrying", "Construction"]); sel = {act: list(amap.values()), yr: all_values(metadata, 1)}
    _, _, rows, manifest = nso_extract(client, GFCF, sel, "gfcf_annual_by_activity", "million MNT", "annual stock/flow as published", "annual values retained; not interpolated to quarters"); manifests.append(manifest)

    # Employment: total region/age/sex, selected industries, quarterly.
    metadata = client.metadata(EMP); region, activity, age, sex, quarter = [v["code"] for v in metadata["variables"]]; amap = codes(client, metadata, activity, ["Total", "Agriculture, forestry and fishing", "Mining and quarrying", "Construction"]); sel = {region: [codes(client, metadata, region, ["Total"])["Total"]], activity: list(amap.values()), age: [codes(client, metadata, age, ["Total"])["Total"]], sex: [codes(client, metadata, sex, ["Total"])["Total"]], quarter: all_values(metadata, 4)}
    _, _, rows, manifest = nso_extract(client, EMP, sel, "employment_quarterly_by_activity", "persons", "quarterly stock", "official quarterly employment; 2019-2023 sampling-weight revision documented"); manifest["known_break"] = "NSO revised 2019-2023 observations in 2024 due to updated sampling weights"; manifests.append(manifest)
    etarget = {"Total": "employment_total", "Agriculture, forestry and fishing": "employment_agriculture", "Mining and quarrying": "employment_mining", "Construction": "employment_construction"}
    for row in rows:
        target = etarget.get(str(row[activity]).strip()); q = row[quarter].replace("-", "-Q")
        if target and row["value"] is not None: panel.setdefault(q, {})[target] = row["value"]

    # Broad depository-corporation loan stock, quarter-end extraction.
    metadata = client.metadata(CREDIT); loan, sector, month = [v["code"] for v in metadata["variables"]]; lmap = codes(client, metadata, loan, ["Loans outstanding"]); smap = codes(client, metadata, sector, ["Total"]); sel = {loan: list(lmap.values()), sector: list(smap.values()), month: all_values(metadata, 2)}
    _, _, rows, manifest = nso_extract(client, CREDIT, sel, "depository_loans_outstanding_monthly", "million MNT (official table unit)", "monthly stock", "total depository-corporation loans outstanding; quarter-end observation"); manifests.append(manifest)
    monthly = [{"period": row[month], "value": row["value"]} for row in rows if row["value"] is not None]
    for q, value in monthly_stock_to_quarter_end(monthly, "period", "value").items(): panel.setdefault(q, {})["depository_loans_outstanding_quarter_end"] = value

    # Write extended panel without truncating the v1 quarters.
    columns = sorted({k for value in panel.values() for k in value if k != "quarter"}); periods = sorted(panel)
    with OUT.open("w", newline="", encoding="utf-8") as stream:
        writer = csv.DictWriter(stream, fieldnames=["quarter", *columns]); writer.writeheader(); [writer.writerow({"quarter": q, **panel[q]}) for q in periods]
    series_dir = ROOT / "data/metadata/series"; series_dir.mkdir(parents=True, exist_ok=True)
    source_by_key = {}
    for item in manifests:
        sid = item["snapshot_id"]
        for key in columns:
            if ("chainlinked" in key and "gdp_chainlinked" in key) or ("expenditure" in key or "consumption" in key or "capital_formation" in key or key == "net_exports_current") and "gdp_expenditure" in sid or ("employment" in key and "employment_" in sid) or ("loans" in key and "loans" in sid): source_by_key[key] = sid
    source_by_key.update({"mnt_per_usd_quarterly_average": manifests[0]["snapshot_id"], "mnt_per_usd_quarter_end": manifests[0]["snapshot_id"]})
    (series_dir / "m4-quarterly-v2.json").write_text(json.dumps({"dataset_id": "m4-quarterly-v2", "created_at_utc": datetime.now(timezone.utc).isoformat(), "period_start": periods[0], "period_end": periods[-1], "source_snapshots": [m["snapshot_id"] for m in manifests], "variables": {key: {"source_snapshot_id": source_by_key.get(key), "unit": "see source snapshot", "transformation": "see source snapshot"} for key in columns}, "notes": ["v1 columns are retained unchanged; annual GFCF is not interpolated."]}, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    (SNAP / "manifest.json").write_text(json.dumps({"snapshot_date": RUN, "snapshots": manifests}, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    (BOM_SNAP / "manifest.json").write_text(json.dumps({"snapshot_date": RUN, "snapshots": manifests[:1], "failed_endpoints": bom_failures}, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    (ROOT / "data/metadata/revisions" / f"phase1c-{RUN}.json").write_text(json.dumps({"snapshot": RUN, "bom_failures": bom_failures, "notes": ["China demand candidates and international benchmarks remain deferred; no substitutes used."]}, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    print(f"Wrote {OUT} with {len(periods)} quarters and {len(columns)} extended variables; BoM failures={len(bom_failures)}")


def all_values(metadata: dict, index: int) -> list[str]: return list(metadata["variables"][index]["values"])


if __name__ == "__main__": main()
