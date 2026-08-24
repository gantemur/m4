# M4 v0 formal specification

## Classification and baseline

M4 v0 is an **accounting + calibrated, assumption-controlled scenario model**. It is not an unconditional forecast model, estimated DSGE/CGE, fitted structural macro model, or VAR. Its baseline is the observed historical path in `m4-quarterly-v4.csv`; scenarios are deviations from that path.

Every endogenous change arises from exactly one accounting identity, documented institutional rule, or explicit user/calibration parameter. No fitted propagation coefficient is hidden in the engine. Historical reduced-form diagnostics are evidence only, never defaults.

## I. Accounting identities

Current-price production accounting uses NSO semantics:

`GDP = Y_M + Y_A + Y_C + Y_O + T`

where `Y_M`, `Y_A`, and `Y_C` are mining, agriculture, and construction GVA; `Y_O` is other-industry GVA; and `T` is taxes less subsidies on products. The prior ambiguous `Y_N` maps to `Y_O` only after Phase 3B reconciliation and never includes product taxes.

For each modeled commodity, `X_c = P_c × Q_c` with native quantity units and a corresponding implied export price; the implementation preserves the observed export-value identity with the required thousand/million conversion. Total exports are `modeled commodity exports + residual merchandise exports`. The residual is observed baseline merchandise exports and is not labelled “non-mining exports.” `TB = X − M` in USD million and `FB = R − G` in million MNT.

## II. Observed and exogenous paths

Physical production, export quantity, and real mining output are separate variables. Prices, residual exports, imports, FX, credit, agriculture, construction, other industry, taxes, and fiscal paths are observed/exogenous unless directly shocked. An FX change is not a real-output change.

Real-output controls use the single official 2015-price component vintage only where available (2015 onward). The components are chain-linked and not safely additive with a constructed real `Y_O` or product-tax residual. Accordingly v0 reports component real-output deviations but returns `NOT_DETERMINED_UNDER_CURRENT_CLOSURE` for an aggregate real-GDP effect; it does not splice bases or fabricate a residual.

## III. Scenario primitives

`Shock` supports a quarter list, inclusive date range, permanent-from-date path, and custom quarter/multiplier path. Primitive names include commodity export price/quantity, physical production, mining/agriculture/construction/other-industry real output, nominal GVA/taxes accounting components, MNT/USD, imports, residual exports, government revenue/expenditure, and credit. A coal export shock changes coal export value, total exports, and trade balance by identity. A coal production shock changes only physical output unless a link is supplied.

## IV. Optional explicit links

All links are disabled unless supplied in `AssumptionLinks`:

- `lambda_revenue`: `ΔR = λ_R × Δ(mining export income in MNT)`, where USD million × MNT/USD equals million MNT.
- `phi_revenue_to_expenditure`: `ΔG = φ_R × ΔR`, a user policy/closure choice.
- `production_to_mining_output`: commodity-specific calibrated real-output elasticities. No default is supplied; the Phase 3B 0.695 correlation is diagnostic evidence, not a coefficient.
- `project_fiscal_receipts_mnt_million`: future project modules can add receipts by type and bypass generic `lambda_revenue`.

## V. Closures

`historical-default` has no automatic fiscal response. `fixed-government-spending` prevents a spending link. `user-specified-fiscal-response` permits an explicit `phi_R`; `user-specified-fx` records an exogenous FX path. A future institutional fiscal-rule interface may replace either generic link.

## VI. Unresolved and future modules

Future project modules may emit commodity production, export value, fiscal receipts by type, domestic wages/procurement, and investment. They have no macro effect until explicit accounting or institutional links are installed. Detailed project finance, endogenous FX, fiscal contracts, construction propagation, and domestic-output equations are outside v0.

## What M4 v0 does NOT infer

It does not infer that a coal export fall reduces mining real output, that a production fall reduces exports, that a trade change moves FX, or that mining exports change fiscal receipts. It does not project China demand, prices, output, or government policy. Those effects require a transparent user assumption or a future validated institutional module.
