# Phase 1C extended data dictionary

The extended panel is [`data/processed/m4-quarterly-v2.csv`](../data/processed/m4-quarterly-v2.csv). It retains all Phase 1A-R columns and adds:

| series | source and treatment |
|---|---|
| `mnt_per_usd_quarterly_average`, `mnt_per_usd_quarter_end` | BoM `/en/currency-rates/data` POST; daily MNT per USD; quarterly mean and last observation; increase means MNT depreciation |
| `gdp_chainlinked_yoy_*` | NSO `DT_NSO_0500_001V4`; official chain-linked YoY/contribution measures, not reconstructed levels |
| expenditure-side GDP columns | NSO `DT_NSO_0500_003V1_quarter`; current-price household/government consumption, gross capital formation, GFCF, net exports, GDP; gross capital formation is not renamed GFCF |
| annual GFCF snapshot | NSO `DT_NSO_0500_020V1`; annual by activity; kept separate and never interpolated |
| `employment_*` | NSO `DT_NSO_0400_035V7_2`; quarterly total/agriculture/mining/construction employment; NSO 2019–2023 sampling-weight revision recorded |
| `depository_loans_outstanding_quarter_end` | NSO `DT_NSO_0700_002V2`; total depository-corporation loans outstanding, monthly stock reduced to quarter-end |

Exact requested labels/codes, checksums, endpoints, and retrieval timestamps are in the timestamped NSO/BoM manifests. BoM reserves and policy-rate endpoints were discovered but returned a structured no-result response for tested ranges; no substitute series was used. China-demand candidates and international commodity benchmarks remain deferred.
