# M4 historical data foundation (v0)

This release is data engineering and descriptive validation only. It contains no estimated equations, forecasts, or counterfactual simulations.

## Sources and coverage

The connected source is the National Statistics Office of Mongolia PxWeb API. The exact table IDs and metadata are recorded in the snapshot manifest under `data/snapshots/nso/<snapshot-id>/manifest.json` and the variable manifest at `data/metadata/series/m4-quarterly-v0.json`.

| family | source table | native frequency | retrieved coverage in Phase 1A | status |
|---|---|---:|---|---|
| quarterly GDP by production | `DT_NSO_0500_004V1` | quarterly | 2000-Q1–2026-Q2 | ACCESSED |
| total trade | `DT_NSO_1400_003V1` | monthly flow | 1997-01–2026-07 | ACCESSED |
| main commodity exports | `DT_NSO_1400_006V2_month` | monthly cumulative | 2011-01–2026-07 for selected commodities | ACCESSED |
| general-government revenue | `DT_NSO_0800_002V1` | monthly cumulative | 2000-01–2026-07 | ACCESSED |
| general-government expenditure | `DT_NSO_0800_005V1` | monthly cumulative | 2000-01–2026-07 | ACCESSED |
| national CPI | `DT_NSO_0600_001V3` | monthly index | 2006-01–2026-07; 2020-base values are not back-cast | ACCESSED |
| Bank of Mongolia FX/reserves | official endpoint | monthly/daily | not connected | DEFERRED |
| World Bank/IMF commodity benchmarks | primary commodity series | monthly | not included in canonical panel | DEFERRED |

The canonical panel is [`data/processed/m4-quarterly-v0.csv`](../data/processed/m4-quarterly-v0.csv). It spans 2000-Q1 through 2026-Q2, with missing cells retained. It does not compute a core GDP residual: taxes less subsidies and the exact published accounting identity still require a separate reconciliation.

## Conventions

- Quarterly GDP retains the NSO nominal indicator and the NSO 2015-constant-price indicator as separate series. No chain-linking or rebasing was invented.
- Monthly trade flows are summed to quarters.
- Commodity and budget tables labelled cumulative are de-cumulated within calendar year; January is treated as the first flow. The year boundary is tested explicitly.
- CPI is preserved as the published 2020=100 index and quarterly-averaged. It is not a year-on-year inflation series and is not seasonally adjusted.
- Commodity export quantities and values retain the NSO labels. Implied unit values are calculated only for matching commodity/value-quantity pairs and are labelled Mongolian implied export unit values, not world prices.
- No series is interpolated or substituted. No official series is seasonally adjusted.

## Known breaks and limitations

The GDP table exposes 2005-, 2010-, and 2015-constant-price indicators; their comparability and rebasing history must be documented before a real-growth series is used for estimation. Construction and agriculture are visibly seasonal; raw values are preserved. The CPI base-year selection means pre-2020 values can be blank in the 2020-base extract. Commodity definitions are NSO “main commodities,” not a universal HS concordance. The coal series is an aggregate labelled `Coal (thous.t)` and is not yet a Mongolian coking-coal benchmark.

The BoM exchange-rate/reserves connection is deferred because a stable machine-readable endpoint was not established. This is an explicit limitation, not a substitution with IMF or World Bank values.

## Revisions and QA

Each source snapshot is immutable and includes a source URL, table ID, retrieval timestamp, schema, units, transformation, and a SHA256 checksum of the JSON-stat response. New refreshes create a new timestamped snapshot directory. Revision comparison is implemented in `m4.data.versioning`; old snapshots are never overwritten. The machine-readable validation report is [`data/processed/m4-validation-v0.json`](../data/processed/m4-validation-v0.json).

The panel has no silent interpolation, no seasonal adjustment, and no GDP identity pass because the accounting convention is not yet resolved. The QA report flags those limitations explicitly.
