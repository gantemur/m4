# Model comparison (v0)

This comparison distinguishes documented facts from the currently unavailable NRGI-FSC-24 code/data package. It is a design decision aid, not a claim that M4 should copy either predecessor.

| dimension | Original NRGI-MMFM (2017) | NRGI-FSC-24 (reported 2024 update) | Proposed M4 | provisional decision |
|---|---|---|---|---|
| purpose | Long-run macro-fiscal sustainability scenarios | Medium-term macro/fiscal forecasting and policy-costing support | Transparent historical exploration and counterfactuals | ADAPT |
| historical/scenario frequency | Annual model; historical sheets include monthly, quarterly and annual inputs; 30-year horizon | Monthly commodity evidence; report produces 2024–27/three-year forecasts | Monthly inputs and quarterly historical model; annual long-run scenarios later | ADAPT |
| production sectors | Mining, agriculture, core (construction within core) | Report does not establish a new construction sector | Mining, agriculture, core; construction undecided | UNDECIDED |
| mining representation | Project sheets: OT, Erdenet, Tsagaan Suvarga, Gatsuurt, ETT, ER, other mines | Commodity: gold; copper (concentrate and refined forms noted); coal (brown/black); iron ore | Commodity layer plus project layer/residual | ADAPT |
| agriculture/core | Explicit agriculture; core aggregate | Not documented as redesigned | Explicit agriculture/core | RETAIN |
| fiscal | Detailed taxes, expenditure, debt and fiscal rules | Mining receipts recomputed; other revenue/expenditure updated after 2015 | Explicit receipts, spending, debt/funds with versioned rules | ADAPT |
| external/FX/inflation | Imports/exports, managed-float FX and hybrid Phillips curve | China/US/EU growth and inflation inputs; copper/iron price assumptions; report assigns FX forecast to DIGNAR in combined outputs | Explicit export/import, reserves and MNT channels; Russian fuel price candidate | ADAPT |
| GDP | Real/nominal macro block and fiscal bridge | Coefficients re-estimated to 2023; combined workflow uses DIGNAR real GDP and NRGI-FSC nominal GDP | National-account identities and separately labelled real/nominal series | RETAIN |
| funds/debt/FDI | Debt and fiscal-rule sheets; no modern project-finance treatment inferred | Combined workflow did not use model outputs for funds/debt in the cited table | Explicit, documented later | ADAPT |
| China/Russia | China present indirectly through trade/foreign variables; no Russia-fuel module found | China industrial production in commodity VARs; US policy rate for gold; US/EU/China macro inputs | China demand explicit; Russian fuel price a tested imported-inflation channel | ADAPT |
| estimation | Mix of calibration, judgement and estimated macro relations | Macro coefficients re-estimated; commodity quantities use ARIMA/VAR | Parameter register with sample, method and status | RETAIN principle / REJECT opaque values |
| transparency/updateability | CC BY XLSX recovered; 91 sheets and legacy links make maintenance difficult | Reported Matlab/Iris/Excel materials submitted to Parliament, not located publicly | Small Python pipeline, snapshots, published assumptions | REJECT legacy delivery / RETAIN inspectability |
| browser simulation | Excel interface, not browser-native | Not established | Browser-read JSON and inspectable causal chain | ADAPT |
| contract experiments | Stronger: mine financial models | Weak: commodity aggregates lose contract detail | Project layer supports OT/Badrakh; commodity layer drives shocks | ADAPT |
| coal transition | Mine/project schedules can be edited, but no dedicated transition structure | Coal forecast has a manually imposed decline after 2025 | Explicit coal commodity scenarios, export demand and domestic capture | ADAPT |

## Two-level mining recommendation

Use an eventual two-level architecture: **project flows → commodity aggregates → macro/fiscal blocks**. A project record (OT, Erdenet, ETT, MMC, Badrakh and any later candidate) supplies production, realised/assumed price, ownership/financing, domestic procurement, employment and fiscal-payment detail. Commodity aggregates combine those records with a clearly labelled `other_<commodity>` residual. Macro shocks can then be applied cleanly to coal/copper/gold/iron/uranium aggregates, while contract experiments act on a project and are reconciled back to its commodity total.

Advantages: contract and ownership questions remain possible; aggregate price/quantity shocks do not require invented mine detail; reconciliation exposes missing coverage. Costs: mine-level fiscal data are confidential/incomplete, commodity definitions differ across production/export/tax records, and double counting must be prevented. Required Phase 1 evidence: commodity-to-project crosswalk; production/export units and grades; project ownership/contract/tax terms with dates; EITI receipts; public company reporting; and an explicit residual/reconciliation identity.

## Construction decision rule

Both recovered 2017 machinery and the 2024 report leave construction inside the broad non-mining/core treatment; no separate construction equation was established. Phase 1 must assemble quarterly real construction GVA and deflator, public capital expenditure (de-cumulated), credit by purpose, GFCF/imported capital goods, housing/non-residential indicators, mine-development investment and employment. Only after checking definition breaks, seasonality, volatility, explanatory distinctness and whether a construction equation improves **out-of-sample interpretability** should M4 choose `Y_M + Y_A + Y_N` or `Y_M + Y_A + Y_C + Y_N`.

## Data snapshot/versioning recommendation

Keep `data/raw/` as an ignored immutable local/API cache. Add versioned `data/snapshots/<source>/<YYYY-MM-DD>/` containing compact normalized parquet/CSV extracts plus a manifest of raw-response hash, source URL/identifier, retrieval timestamp, schema, transformations and revision status. Keep versioned `data/metadata/` source registry and per-snapshot checksums. Generate ignored `data/latest/` during refresh, then publish browser-ready immutable bundles under `web/data/<snapshot-id>/` and a small versioned `web/data/latest.json` pointer only after validation.

The refresh workflow should fetch → retain raw cache → normalize → compare checksums/schema and revisions → test → create a new snapshot → build browser bundle → atomically update the pointer. On upstream failure, retain the last validated pointer; never publish partial data. Git stores compact snapshots and metadata, not bulky raw responses. This gives a public GitHub Pages build a stable previous release and allows every published chart/model run to cite a snapshot ID.
