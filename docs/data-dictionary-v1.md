# M4 data dictionary (Phase 1A v1)

Status vocabulary: `ACCESSED` means the official endpoint was queried and a compact snapshot is present; `DEFERRED` means identified but not used in the canonical panel; `FAILED` is reserved for a source that was attempted and failed; `IDENTIFIED` means located but not queried.

| variable(s) | status | exact source/table | native period | available period | unit | canonical transformation |
|---|---|---|---|---|---|---|
| `gdp_nominal_total`, `gdp_nominal_mining`, `gdp_nominal_agriculture`, `gdp_nominal_construction` | ACCESSED | NSO `DT_NSO_0500_004V1`, indicator `0`, compositions `0,1,2,5` | quarterly | 2000-Q1–2026-Q2 | million MNT | retain official quarterly values |
| `gdp_real2015_total`, `gdp_real2015_mining`, `gdp_real2015_agriculture`, `gdp_real2015_construction` | ACCESSED | NSO `DT_NSO_0500_004V1`, indicator `3`, compositions `0,1,2,5` | quarterly | 2000-Q1–2026-Q2 | million MNT, 2015 constant prices | retain official 2015-constant indicator; no rebasing |
| `exports_usd_thousand`, `imports_usd_thousand` | ACCESSED | NSO `DT_NSO_1400_003V1`, indicators `1,2` | monthly flow | 1997-01–2026-07 | USD thousand | monthly sum to quarter |
| coal export quantity/value | ACCESSED | NSO `DT_NSO_1400_006V2_month`, commodity `31` `Coal (thous.t)`, indicators `0,1` | monthly cumulative | 2011-01–2026-07 | thousand tonnes / USD thousand | de-cumulate within year, sum to quarter |
| copper concentrate export quantity/value | ACCESSED | NSO `DT_NSO_1400_006V2_month`, commodity `7` `Copper ores and concentrate (thous.t)`, indicators `0,1` | monthly cumulative | 2011-01–2026-07 | thousand tonnes / USD thousand | de-cumulate within year, sum to quarter |
| gold export quantity/value | ACCESSED | same, commodity `6` `Gold, unwrought or in semi-manufactured forms (t)` | monthly cumulative | 2011-01–2026-07 | tonnes / USD thousand | de-cumulate within year, sum to quarter |
| iron ore export quantity/value | ACCESSED | same, commodity `11` `Iron ores & concentrates (thous.t)` | monthly cumulative | 2011-01–2026-07 | thousand tonnes / USD thousand | de-cumulate within year, sum to quarter |
| `coal_implied_export_unit_value_usd_per_t`, copper equivalent | ACCESSED | derived from matching NSO commodity value/quantity pairs | quarterly derived | commodity coverage above | USD/t | value thousand USD ÷ quantity thousand tonnes; explicitly implied Mongolian export unit value |
| `government_revenue_mnt_million` | ACCESSED | NSO `DT_NSO_0800_002V1`, indicator `0` Month, classification `0` Total revenue and grants | monthly cumulative | 2000-01–2026-07 | million MNT | January is first flow; subsequent months difference within calendar year; sum to quarter |
| `government_expenditure_mnt_million` | ACCESSED | NSO `DT_NSO_0800_005V1`, indicator `0` Month, classification `0` Total expenditure and net lending | monthly cumulative | 2000-01–2026-07 | million MNT | same de-cumulation and quarterly sum |
| `government_capital_expenditure_mnt_million` | ACCESSED | same, classification `43` Capital expenditure | monthly cumulative | 2000-01–2026-07 | million MNT | same de-cumulation and quarterly sum |
| `cpi_index_2020` | ACCESSED | NSO `DT_NSO_0600_001V3`, base `1` `2020=100`, group `0` Overall index | monthly index | 2006-01–2026-07; pre-base values blank | index | average available months in quarter; no inflation conversion |
| MNT/USD; reserves | DEFERRED | Bank of Mongolia official statistics | daily/monthly | not connected | MNT/USD; USD | no substitute source used |
| copper/coal/oil benchmarks | DEFERRED | World Bank/IMF primary commodity series | monthly | not included | benchmark-specific | coal grade choice and endpoint provenance unresolved |
| GDP expenditure components, credit, GFCF, construction employment | DEFERRED | NSO/BoM candidate tables | quarterly/monthly | not included | source-specific | reserved for Phase 1B/targeted follow-up |

Exact retrieval timestamps, JSON-stat schemas, source-response checksums, and per-column snapshot IDs are in [`data/metadata/series/m4-quarterly-v0.json`](../data/metadata/series/m4-quarterly-v0.json) and the immutable manifests under `data/snapshots/nso/`.
