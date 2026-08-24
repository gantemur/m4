# M4 historical data foundation (Phase 1A-R)

This corrected release is descriptive data engineering only: no equations, forecasts, seasonal adjustment, interpolation, or UI work.

The prior `m4-quarterly-v0.csv` remains in place but is deprecated/invalid. It selected total turnover and balance while labelling them exports/imports, labelled USD millions as USD thousands, and de-cumulated fiscal series whose selected indicator was already `Month`.

Phase 1A-R fixes those transformations without deleting immutable source snapshots. The new canonical output is [`m4-quarterly-v1.csv`](../data/processed/m4-quarterly-v1.csv), with 106 quarters and 36 variables. Trade identities are checked as `turnover = exports + imports` and `balance = exports - imports`, with a USD 0.25 million tolerance for source rounding.

The 2005-, 2010-, and 2015-constant-price GDP vintages remain separate; no cross-base level is concatenated. The construction cross-check using the 2015 vintage reproduces the supplied annual growth, shares, and quarterly seasonal shares, confirming strong unadjusted seasonality.

CPI bases remain separate. The 2020-base overall index is blank before 2010-Q1 in this extract; 2015-base values begin in 2006-Q1 and end in 2022-Q3. Commodity exports survive unchanged in substance, with cumulative-month de-cumulation and nonnegative/finite-value checks.

Machine-readable QA is in [`m4-validation-v1.json`](../data/processed/m4-validation-v1.json). No Phase 1B work was started.
