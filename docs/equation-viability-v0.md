# Phase 3B equation viability

Input: corrected `m4-quarterly-v4`; reproducible Phase 3B diagnostics: [`results/estimation-v0/phase3b-diagnostics.json`](../results/estimation-v0/phase3b-diagnostics.json). These diagnostics are evaluation-only and have not been activated in the engine.

## Accounting reconciliation

The full current-price GDP decomposition now reconciles to published rounding: GDP equals industry GVA plus taxes less subsidies on products. Version 4 retains a clean `other_industry_GVA = industry GVA - mining - agriculture - construction` accounting residual. The legacy `Y_N` label maps to `Y_O` only after this reconciliation; the other-industry behavioral equation remains disabled because it is not validated, not because accounting is unresolved.

| relationship | decision | evidence / interpretation |
|---|---|---|
| Mining quantity to real mining | ACCOUNTING + CALIBRATED DIAGNOSTIC; no equation | Official physical production is distinct from exports. A four-product physical index has 42 comparable YoY quarters and correlation 0.695 with real mining growth, but short/compositional coverage prevents activation. |
| Fiscal receipts | KEEP FISCAL REVENUE EXOGENOUS | Same-quarter expanding forecasts are worse than a historical-mean benchmark; lag-one improvement in RMSE is negligible, has worse MAE, and slopes are unstable. |
| Fiscal spending response | POLICY PARAMETER — DO NOT ESTIMATE STRUCTURALLY | `phi_R` remains user/closure controlled. A historical benchmark may later be reported, never installed as invariant behavior. |
| Construction | KEEP CONSTRUCTION SEPARATE BUT EXOGENOUS | Capex-growth diagnostic has 42 observations and a positive simple slope, but no rolling validation, credit comparison, or stable structural identification yet. |
| Other-industry output | KEEP EXOGENOUS | Production accounting is reconciled, but no validated behavioral equation exists. |
| Imports | KEEP EXOGENOUS | Simple demand-growth diagnostic has 82 observations but mixes nominal MNT demand with USD imports and excludes the required FX formulation/stability audit. |
| Agriculture | KEEP EXOGENOUS | No weather/dzud drivers; no autoregression is introduced merely for completeness. |
| Credit / FX | KEEP EXOGENOUS | Required by the v0 closure; no exports-to-FX or policy-to-credit equation is estimated. |

## Functional form and stability

The prespecified diagnostics use YoY changes to reduce strong seasonality. No nonlinear challenger is accepted: no economic/validation evidence currently justifies extra parameters. Local linear/log-linear forms are a reasonable *candidate* language for fiscal and construction testing, but data are insufficient to characterize the full model globally as linear or nonlinear.

The fiscal, construction, and import diagnostics are not activated equations. Phase 3B completed the fiscal expanding-window, benchmark, and stability audit and rejected the fiscal candidate for v0; the accounting gap is reconciled. Major period changes (OT, the 2015–16 downturn, COVID/border disruption, and coal boom) reinforce the decision not to treat fixed correlations as structural laws.
