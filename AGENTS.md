# M4 research and data rules

1. Never manually alter downloaded raw observations.
2. Every external series must record source institution, exact table/series ID when available, source URL, retrieval date, units, native frequency, stock/flow/average/end-of-period status, and transformations applied.
3. Never silently interpolate missing values.
4. Never silently replace an unavailable official series with another series.
5. Distinguish nominal values, real values, quantities, unit values, indices, and percentages explicitly.
6. Aggregate monthly flows to quarters by summing them. For stock variables, choose and document an economically appropriate end-of-period or average convention.
7. Give every nontrivial data transformation a test where practical.
8. Preserve original raw data or raw API responses so results are reproducible.
9. Do not present fitted correlations as causal mechanisms.
10. Do not add economic equations merely because they improve in-sample fit.
11. Every future model equation must document its economic interpretation; identity/calibrated/estimated status; parameter source; and estimation sample if estimated.
12. Do not create fake data merely to make a pipeline run.
13. If an external source cannot be retrieved, fail transparently and report what is missing.

## Repository conventions

- `data/raw/` is immutable input. Keep retrieved API responses there, out of version control unless a small lawful test fixture is needed.
- Put a metadata record beside each new source before relying on it in analysis.
- Prefer standard-library Python unless a scientific dependency earns its cost.
- Do not add a model estimation or simulation in Phase 0.
