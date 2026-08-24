"""Build the Phase 1B historical atlas from the corrected v1 panel.

The script is deliberately descriptive: it produces figures, tables, and
diagnostics, but no estimated model, forecast, seasonal adjustment, or causal
analysis.
"""

from __future__ import annotations

import csv
import json
import math
import statistics
from collections import defaultdict
from pathlib import Path
from typing import Iterable

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt

ROOT = Path(__file__).resolve().parents[1]
PANEL = ROOT / "data/processed/m4-quarterly-v1.csv"
OUT = ROOT / "results/atlas-v0"
FIG = OUT / "figures"


def num(value: str) -> float | None:
    return None if value in {"", "None", None} else float(value)


def annual_sum(rows: list[dict[str, str]], column: str) -> dict[str, float]:
    out: defaultdict[str, float] = defaultdict(float)
    for row in rows:
        value = num(row.get(column, ""))
        if value is not None:
            out[row["quarter"][:4]] += value
    return dict(out)


def annual_average(rows: list[dict[str, str]], column: str) -> dict[str, float]:
    grouped: defaultdict[str, list[float]] = defaultdict(list)
    for row in rows:
        value = num(row.get(column, ""))
        if value is not None:
            grouped[row["quarter"][:4]].append(value)
    return {year: sum(values) / len(values) for year, values in grouped.items()}


def annual_full_sum(rows: list[dict[str, str]], column: str) -> dict[str, float]:
    """Annual sums restricted to years with all four quarterly observations."""
    grouped: defaultdict[str, list[float]] = defaultdict(list)
    for row in rows:
        value = num(row.get(column, ""))
        if value is not None:
            grouped[row["quarter"][:4]].append(value)
    return {year: sum(values) for year, values in grouped.items() if len(values) == 4}


def yoy(values: dict[str, float]) -> dict[str, float]:
    return {year: 100 * (values[year] / values[str(int(year) - 1)] - 1) for year in sorted(values) if str(int(year) - 1) in values and values[str(int(year) - 1)] != 0}


def quarterly_yoy(rows: list[dict[str, str]], column: str) -> dict[str, float]:
    values = {row["quarter"]: num(row.get(column, "")) for row in rows}
    return {q: 100 * (values[q] / values.get(f"{int(q[:4])-1}-{q[-2:]}") - 1) for q in values if values[q] is not None and values.get(f"{int(q[:4])-1}-{q[-2:]}") not in {None, 0}}


def pearson(x: Iterable[float], y: Iterable[float]) -> float | None:
    pairs = [(a, b) for a, b in zip(x, y) if a is not None and b is not None]
    if len(pairs) < 3:
        return None
    xs, ys = zip(*pairs)
    if len(set(xs)) < 2 or len(set(ys)) < 2:
        return None
    mx, my = statistics.mean(xs), statistics.mean(ys)
    numerator = sum((a - mx) * (b - my) for a, b in pairs)
    denominator = math.sqrt(sum((a - mx) ** 2 for a in xs) * sum((b - my) ** 2 for b in ys))
    return numerator / denominator if denominator else None


def savefig(name: str, title: str, definition: str, unit: str, transformation: str, limitation: str) -> None:
    path = FIG / f"{name}.png"
    plt.title(title)
    plt.tight_layout()
    plt.savefig(path, dpi=150)
    plt.close()
    FIGURES.append({"file": str(path.relative_to(OUT)), "variable_definition": definition, "unit": unit, "frequency_transformation": transformation, "data_vintage": DATA_VINTAGE, "limitation": limitation})


FIGURES: list[dict[str, str]] = []
DATA_VINTAGE = "m4-quarterly-v1"


def main() -> None:
    global FIGURES, DATA_VINTAGE
    FIGURES = []
    rows = list(csv.DictReader(PANEL.open(encoding="utf-8", newline="")))
    series_manifest = json.loads((ROOT / "data/metadata/series/m4-quarterly-v1.json").read_text(encoding="utf-8"))
    DATA_VINTAGE = "m4-quarterly-v1; snapshots=" + ",".join(series_manifest["source_snapshots"])
    OUT.mkdir(parents=True, exist_ok=True)
    FIG.mkdir(parents=True, exist_ok=True)
    # Keep the atlas directory reproducible when figure names change between
    # runs; this only removes generated PNGs inside the atlas output folder.
    for stale in FIG.glob("*.png"):
        stale.unlink()

    # 1–2: external trade.
    quarters = [r["quarter"] for r in rows]
    plt.figure(figsize=(10, 4)); plt.plot(quarters, [num(r["exports_usd_million"]) for r in rows], label="Exports"); plt.plot(quarters, [num(r["imports_usd_million"]) for r in rows], label="Imports"); plt.xticks(quarters[::16], rotation=45); plt.ylabel("USD million"); plt.legend(); savefig("01-exports-imports", "Merchandise exports and imports", "NSO exports and imports", "USD million", "monthly flow summed to quarterly", "Trade begins before the GDP panel; no seasonal adjustment")
    plt.figure(figsize=(10, 4)); plt.plot(quarters, [num(r["trade_balance_usd_million"]) for r in rows]); plt.axhline(0, color="black", lw=.7); plt.xticks(quarters[::16], rotation=45); plt.ylabel("USD million"); savefig("02-trade-balance", "Merchandise trade balance", "Exports minus imports", "USD million", "monthly flow summed to quarterly", "Small identity differences reflect source rounding")

    # Annual mineral decomposition and shares.
    minerals = {"Coal": "coal_export_value_usd_thousand", "Copper concentrate": "copper_concentrate_export_value_usd_thousand", "Gold": "gold_export_value_usd_thousand", "Iron ore": "iron_ore_export_value_usd_thousand"}
    total_exports = annual_sum(rows, "exports_usd_million")
    mineral_annual = {name: {y: value / 1000 for y, value in annual_sum(rows, col).items()} for name, col in minerals.items()}
    years = sorted(set(total_exports) & set.intersection(*(set(v) for v in mineral_annual.values())))
    residual = {y: total_exports[y] - sum(mineral_annual[name][y] for name in minerals) for y in years}
    plt.figure(figsize=(10, 5)); bottom = [0.0] * len(years)
    for name in [*minerals, "Residual merchandise exports"]:
        values = [mineral_annual[name][y] if name in mineral_annual else residual[y] for y in years]; plt.bar(years, values, bottom=bottom, label=name); bottom = [a + b for a, b in zip(bottom, values)]
    plt.xticks(years[::2], rotation=45); plt.ylabel("USD million"); plt.legend(fontsize=8); savefig("03-mineral-export-decomposition", "Recorded major-mineral export values and residual", "Coal, copper concentrate, gold, iron ore, and total exports minus those four", "USD million", "annual sums; commodity USD thousand converted to USD million", "Residual is not non-mining exports and may contain other minerals")
    shares = {y: 100 * sum(mineral_annual[name][y] for name in minerals) / total_exports[y] for y in years}
    plt.figure(figsize=(10, 4)); plt.plot(years, [shares[y] for y in years], marker="o"); plt.ylabel("Percent of total exports"); plt.ylim(0, 100); savefig("04-four-mineral-export-share", "Share of exports represented by four recorded commodities", "Four recorded commodity export values divided by total exports", "percent", "annual ratio", "Commodity table starts in 2011; coverage is not a universal HS classification")

    # 5–6: coal and copper price/quantity separation.
    for n, label, qcol, vcol, ucol in [(5, "Coal", "coal_export_quantity_thousand_t", "coal_export_value_usd_thousand", "coal_implied_export_unit_value_usd_per_t"), (6, "Copper concentrate", "copper_concentrate_export_quantity_thousand_t", "copper_concentrate_export_value_usd_thousand", "copper_concentrate_implied_export_unit_value_usd_per_t")]:
        avq, avv, avu = annual_sum(rows, qcol), {y: v / 1000 for y, v in annual_sum(rows, vcol).items()}, annual_average(rows, ucol)
        ys = sorted(set(avq) & set(avv) & set(avu)); fig, ax = plt.subplots(3, 1, figsize=(9, 8), sharex=True); ax[0].plot(ys, [avq[y] for y in ys]); ax[0].set_ylabel("Quantity"); ax[1].plot(ys, [avv[y] for y in ys]); ax[1].set_ylabel("USD million"); ax[2].plot(ys, [avu[y] for y in ys]); ax[2].set_ylabel("USD/t"); ax[2].set_xlabel("Year"); fig.suptitle(f"{label}: quantity, value, and implied unit value"); savefig(f"0{n}-{label.lower().replace(' ', '-')}-price-quantity", f"{label}: price and quantity separation", f"{label} export quantity, value, and implied value/quantity", "source units; USD/t for unit value", "cumulative monthly series de-cumulated then summed; unit value from quarterly totals", "Implied value is Mongolia-specific, not an international benchmark")

    # 7–8: nominal composition.
    nominal = {name: annual_sum(rows, col) for name, col in {"Mining": "gdp_nominal_mining", "Agriculture": "gdp_nominal_agriculture", "Construction": "gdp_nominal_construction", "Total GDP": "gdp_nominal_total"}.items()}
    ys = sorted(nominal["Total GDP"]); rem = {y: nominal["Total GDP"][y] - nominal["Mining"].get(y, 0) - nominal["Agriculture"].get(y, 0) - nominal["Construction"].get(y, 0) for y in ys}; fig, ax = plt.subplots(figsize=(10, 5)); bottom = [0] * len(ys)
    for name in ["Mining", "Agriculture", "Construction", "Remaining published GDP"]:
        values = [100 * (nominal[name][y] / nominal["Total GDP"][y]) if name in nominal else 100 * rem[y] / nominal["Total GDP"][y] for y in ys]; ax.bar(ys, values, bottom=bottom, label=name); bottom = [a + b for a, b in zip(bottom, values)]
    ax.set_ylabel("Share of nominal GDP (%)"); ax.legend(fontsize=8); savefig("07-nominal-gdp-composition", "Nominal GDP composition", "Mining, agriculture, construction, and remaining published GDP", "percent", "annual sums and shares", "Remaining published GDP includes other industries and the published taxes-less-subsidies component; it is not core GVA")
    mining_share = {y: 100 * nominal["Mining"][y] / nominal["Total GDP"][y] for y in ys}; plt.figure(figsize=(10, 4)); plt.plot(ys, [mining_share[y] for y in ys], marker="o"); plt.ylabel("Mining share (%)"); savefig("08-mining-share", "Nominal mining share over time", "Mining GDP divided by total GDP", "percent", "annual nominal ratio", "Annotations are broad historical periods, not causal breaks")

    # 9–10: real GDP vintages.
    vintage_cols = {"2005 base": "gdp_real2005_total", "2010 base": "gdp_real2010_total", "2015 base": "gdp_real2015_total"}; fig, ax = plt.subplots(figsize=(10, 5))
    for label, col in vintage_cols.items():
        qg = quarterly_yoy(rows, col); ax.plot(list(qg), list(qg.values()), label=label)
    ax.axhline(0, color="black", lw=.7); ax.set_xticks(quarters[::16]); ax.tick_params(axis="x", rotation=45); ax.set_ylabel("YoY growth (%)"); ax.legend(); savefig("09-real-gdp-vintage-yoy", "Quarterly real GDP growth by official vintage", "Total GDP YoY growth for 2005-, 2010-, and 2015-price vintages", "percent", "quarterly YoY; no splicing", "Overlapping growth rates are comparable diagnostics, not a linked level")
    diagnostics = {}
    annual_vintages = {label: annual_full_sum(rows, col) for label, col in vintage_cols.items()};
    for a, b in [("2005 base", "2010 base"), ("2010 base", "2015 base")]:
        ga, gb = yoy(annual_vintages[a]), yoy(annual_vintages[b]); common = sorted(set(ga) & set(gb)); diffs = [ga[y] - gb[y] for y in common]; diagnostics[f"{a}_vs_{b}"] = {"overlap_years": common, "mean_abs_difference_pp": sum(abs(x) for x in diffs) / len(diffs) if diffs else None, "correlation": pearson([ga[y] for y in common], [gb[y] for y in common])}
    plt.figure(figsize=(7, 4)); labels = list(diagnostics); plt.bar(labels, [diagnostics[k]["mean_abs_difference_pp"] for k in labels]); plt.ylabel("Mean absolute annual growth difference (pp)"); plt.xticks(rotation=20); savefig("10-real-vintage-agreement", "Agreement between overlapping real GDP vintages", "Mean absolute difference in annual total-GDP growth", "percentage points", "annual within-vintage growth comparison", "Differences are descriptive; NSO metadata do not establish a cause")

    # 11–12: agriculture.
    ag = annual_sum(rows, "gdp_real2015_agriculture"); ag_growth = yoy(ag); fig, ax = plt.subplots(2, 1, figsize=(9, 7), sharex=False); ax[0].plot(sorted(ag), [ag[y] for y in sorted(ag)]); ax[0].set_ylabel("million MNT, 2015 prices"); ax[1].bar(list(ag_growth), list(ag_growth.values())); ax[1].set_ylabel("YoY growth (%)"); fig.suptitle("Real agriculture output and growth (2015-price vintage)"); savefig("11-agriculture-output-growth", "Real agriculture output and growth", "Agriculture GDP level and annual growth", "million MNT; percent", "annual sums and YoY", "No dzud attribution is made")
    agq = defaultdict(list)
    for r in rows:
        v = num(r.get("gdp_real2015_agriculture", ""));
        if v is not None: agq[r["quarter"][-2:]].append(v)
    means = {q: sum(v) / len(v) for q, v in agq.items()}; overall = sum(means.values()) / len(means); plt.figure(figsize=(6, 4)); plt.bar(list(means), [means[q] / overall for q in means]); plt.ylabel("Quarter mean / four-quarter mean"); savefig("12-agriculture-seasonality", "Agriculture quarterly seasonality", "Average agriculture real GDP by quarter", "index", "raw quarterly values; no adjustment", "Seasonality is a descriptive pattern")

    # 13–17: construction and capex.
    con = annual_sum(rows, "gdp_real2015_construction"); con_growth = yoy(con); fig, ax = plt.subplots(2, 1, figsize=(9, 7)); ax[0].plot(sorted(con), [con[y] for y in sorted(con)]); ax[0].set_ylabel("million MNT, 2015 prices"); ax[1].bar(list(con_growth), list(con_growth.values())); ax[1].set_ylabel("YoY growth (%)"); fig.suptitle("Real construction output and annual growth"); savefig("13-construction-output-growth", "Real construction output and growth", "Construction GDP level and annual growth", "million MNT; percent", "annual sums and YoY", "Raw values are strongly seasonal")
    con_share = {y: 100 * con[y] / annual_sum(rows, "gdp_real2015_total")[y] for y in con if y in annual_sum(rows, "gdp_real2015_total")}; nom_con_share = {y: 100 * nominal["Construction"][y] / nominal["Total GDP"][y] for y in nominal["Construction"]}; plt.figure(figsize=(9, 4)); plt.plot(sorted(con_share), [con_share[y] for y in sorted(con_share)], label="Real GDP share"); plt.plot(sorted(nom_con_share), [nom_con_share[y] for y in sorted(nom_con_share)], label="Nominal GDP share"); plt.ylabel("Percent"); plt.legend(); savefig("14-construction-shares", "Construction share of GDP", "Construction divided by real and nominal total GDP", "percent", "annual ratios", "Real share uses 2015-price vintage; nominal share uses current prices")
    conq = defaultdict(list)
    for r in rows:
        c, t = num(r.get("gdp_real2015_construction", "")), num(r.get("gdp_real2015_total", ""));
        if c is not None and t is not None: conq[r["quarter"][-2:]].append(100 * c / t)
    cmeans = {q: sum(v) / len(v) for q, v in conq.items()}; plt.figure(figsize=(6, 4)); plt.bar(list(cmeans), [cmeans[q] for q in cmeans]); plt.ylabel("Construction share (%)"); savefig("15-construction-seasonality", "Construction quarterly seasonality", "Average real construction share of real GDP by quarter", "percent", "raw quarterly ratio; no adjustment", "Seasonality is unusually strong")
    capex = annual_sum(rows, "government_capital_expenditure_mnt_million"); ngdp = nominal["Total GDP"]; ys2 = sorted(set(capex) & set(ngdp) & set(con)); fig, ax = plt.subplots(figsize=(9, 4)); ax.plot(ys2, [capex[y] / max(capex.values()) for y in ys2], label="Capex normalized"); ax.plot(ys2, [con[y] / max(con.values()) for y in ys2], label="Real construction normalized"); ax.legend(); ax.set_ylabel("Index (series maximum=1)"); savefig("16-construction-capex-normalized", "Construction and public capital expenditure", "Normalized annual real construction and public capex", "index", "annual sums normalized within series", "Descriptive co-movement is not causal")
    capex_growth = yoy(capex); common_growth_years = sorted(set(con_growth) & set(capex_growth)); plt.figure(figsize=(9, 4)); plt.plot(common_growth_years, [con_growth[y] for y in common_growth_years], label="Construction real GDP"); plt.plot(common_growth_years, [capex_growth[y] for y in common_growth_years], label="Public capex"); plt.axhline(0, color="black", lw=.7); plt.ylabel("Annual growth (%)"); plt.legend(); savefig("17-construction-capex-growth", "Construction and public capital expenditure growth", "Annual growth in real construction and public capex", "percent", "annual sums and YoY growth", "Descriptive co-movement is not causal")
    q_con = {r["quarter"]: num(r.get("gdp_real2015_construction", "")) for r in rows}; q_cap = {r["quarter"]: num(r.get("government_capital_expenditure_mnt_million", "")) for r in rows}; lag_corr = {}
    for lag in range(5):
        pairs = []
        for q in q_con:
            index = int(q[:4]) * 4 + int(q[-1]) - 1 - lag
            source_q = f"{index // 4}-Q{index % 4 + 1}"
            pairs.append((q_con[q], q_cap.get(source_q)))
        lag_corr[str(lag)] = pearson([p[0] for p in pairs if p[0] is not None and p[1] is not None], [p[1] for p in pairs if p[0] is not None and p[1] is not None])
    plt.figure(figsize=(6, 4)); plt.bar(list(lag_corr), list(lag_corr.values())); plt.xlabel("Capex lead in quarters"); plt.ylabel("Descriptive correlation"); savefig("18-construction-capex-leads-lags", "Construction/capex descriptive lead-lag correlations", "Construction output correlated with prior public capex", "correlation", "quarterly raw levels; lags 0–4", "Correlations are not causal estimates")

    # 18–19: fiscal history.
    revenue, expenditure = annual_sum(rows, "government_revenue_mnt_million"), annual_sum(rows, "government_expenditure_mnt_million"); balance = {y: revenue[y] - expenditure[y] for y in set(revenue) & set(expenditure)}; fys = sorted(balance); fig, ax = plt.subplots(figsize=(10, 4)); ax.plot(fys, [revenue[y] for y in fys], label="Revenue"); ax.plot(fys, [expenditure[y] for y in fys], label="Expenditure"); ax.bar(fys, [balance[y] for y in fys], alpha=.25, label="Balance"); ax.axhline(0, color="black", lw=.7); ax.legend(); ax.set_ylabel("million MNT"); savefig("19-fiscal-levels-balance", "Government revenue, expenditure, and balance", "General-government revenue, expenditure, and revenue minus expenditure", "million MNT", "monthly flows summed to annual totals", "Balance is a simple descriptive difference, not a full fiscal-accounting balance")
    plt.figure(figsize=(10, 4)); plt.plot(fys, [100 * revenue[y] / ngdp[y] for y in fys if y in ngdp], label="Revenue/GDP"); plt.plot(fys, [100 * expenditure[y] / ngdp[y] for y in fys if y in ngdp], label="Expenditure/GDP"); plt.plot(fys, [100 * capex[y] / ngdp[y] for y in fys if y in ngdp], label="Capex/GDP"); plt.ylabel("Percent of nominal GDP"); plt.legend(); savefig("20-fiscal-shares", "Fiscal aggregates as shares of nominal GDP", "Revenue, expenditure, and capital expenditure relative to nominal GDP", "percent", "annual flow/GDP ratios", "No causal or procyclicality claim")

    # 20: seasonality audit.
    season_cols = {"GDP": "gdp_real2015_total", "Agriculture": "gdp_real2015_agriculture", "Construction": "gdp_real2015_construction", "Mining": "gdp_real2015_mining", "Capex": "government_capital_expenditure_mnt_million"}; fig, ax = plt.subplots(len(season_cols), 1, figsize=(7, 11), sharex=True)
    for axis, (label, col) in zip(ax, season_cols.items()):
        vals = defaultdict(list)
        for r in rows:
            v = num(r.get(col, ""));
            if v is not None: vals[r["quarter"][-2:]].append(v)
        means = {q: sum(v) / len(v) for q, v in vals.items()}; base = sum(means.values()) / len(means); axis.bar(list(means), [means[q] / base for q in means]); axis.set_ylabel(label)
    ax[-1].set_xlabel("Quarter"); fig.suptitle("Quarterly seasonality audit (mean quarter / mean across quarters)"); savefig("21-seasonality-audit", "Seasonality audit", "Quarterly mean relative to mean across quarters", "index", "raw quarterly values; no seasonal adjustment", "Treatment recommendation is block-specific")

    tables = {"mineral_export_annual_usd_million": {"years": years, "series": {**mineral_annual, "Residual merchandise exports": residual, "Four-mineral share percent": shares}}, "real_vintage_agreement": diagnostics, "construction_capex_lag_correlations": lag_corr, "construction_annual_growth_percent": con_growth, "construction_real_share_percent": con_share, "fiscal_balance_annual_mnt_million": balance}
    (OUT / "atlas-tables.json").write_text(json.dumps(tables, indent=2) + "\n", encoding="utf-8")
    (OUT / "figure-metadata.json").write_text(json.dumps(FIGURES, indent=2) + "\n", encoding="utf-8")
    print(f"Wrote {len(FIGURES)} figures and machine-readable tables to {OUT}")


if __name__ == "__main__":
    main()
