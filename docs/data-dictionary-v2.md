# M4 data dictionary (Phase 1A-R v1)

`m4-quarterly-v0.csv` is retained for audit only and is deprecated/invalid for analysis. It had four errors: total-trade indicator mapping, total-trade unit, de-cumulation of direct monthly fiscal flows, and overstated constant-price/CPI coverage.

| family | official semantics | canonical treatment |
|---|---|---|
| Trade | `DT_NSO_1400_003V1`: `1` Total turnover, `11` Exports, `12` Imports, `2` Balance | USD million; monthly flows summed to quarters; identities checked within USD 0.25m source-rounding tolerance |
| Fiscal revenue | `DT_NSO_0800_002V1`: indicator `0` Month; class `0` Total revenue and grants | direct monthly flow summed; no de-cumulation |
| Fiscal expenditure | `DT_NSO_0800_005V1`: indicator `0` Month; classes `0` Total expenditure and net lending, `43` Capital expenditure | direct monthly flows summed; no de-cumulation |
| GDP | `DT_NSO_0500_004V1`: current prices plus 2005, 2010, 2015 constant-price indicators | each vintage retained separately; no concatenation |
| CPI | `DT_NSO_0600_001V3`: 2015=100, 2020=100, 2023=100; Overall index | each base averaged separately; no splice |
| Commodity exports | `DT_NSO_1400_006V2_month.px`: Volume and Value(USD.thous) | cumulative observations de-cumulated within calendar year, then summed |

The corrected panel is [`data/processed/m4-quarterly-v1.csv`](../data/processed/m4-quarterly-v1.csv), covering 2000-Q1–2026-Q2. Exact requested dimension names, codes, and labels are in the snapshot manifest and [`m4-quarterly-v1.json`](../data/metadata/series/m4-quarterly-v1.json).

Actual nonmissing coverage: GDP real 2005, 2000-Q1–2014-Q1; GDP real 2010, 2010-Q1–2021-Q1; GDP real 2015, 2015-Q1–2026-Q2; CPI 2015, 2006-Q1–2022-Q3; CPI 2020/2023, 2010-Q1–2026-Q2. No official continuous real level was identified across GDP bases.
