# Phase 3B mining-output bridge and fiscal validation

Inputs are the immutable raw API replies beneath `data/raw/phase3b/`, the timestamped snapshot manifest in `data/snapshots/nso/`, and corrected [`m4-quarterly-v4.csv`](../data/processed/m4-quarterly-v4.csv). Re-run `PYTHONPATH=src python3 scripts/build_phase3b.py` followed by `PYTHONPATH=src python3 scripts/evaluate_phase3b.py`. The latter writes [`phase3b-diagnostics.json`](../results/estimation-v0/phase3b-diagnostics.json). Neither script activates a model equation.

## Production accounting

NSO table `DT_NSO_0500_004V1` supplies current-price GDP, all industry components, and taxes less subsidies on products. For 106 available quarters, the identity

`GDP = agriculture + mining + manufacturing + electricity + construction + transport + trade + other services + services + taxes less subsidies`

holds to published rounding: the maximum absolute gap is 0.3 million MNT. Version 3 therefore carries `industry_gva_nominal_mnt_million`, `taxes_less_subsidies_nominal_mnt_million`, and the clean accounting residual `other_industry_gva_nominal_mnt_million = industry GVA − agriculture − mining − construction`. This closes the accounting gap; it does not identify an other-industry behavioural equation.

## Official mining production bridge

NSO `DT_NSO_1100_016V5` is an industrial-production *comparison index*. The selected “same period of previous year” measure is converted from index points to YoY percentage growth (`index − 100`) and its monthly observations are averaged within quarter. It covers only 2020-Q3–2026-Q2 after matching real mining GVA. Its correlation with real mining-GVA YoY growth is 0.412 and its residual RMSE is 49.6 percentage points. It is useful as a contemporaneous diagnostic, not as a calibrated bridge.

NSO `DT_NSO_1100_006V2` records physical monthly output flows. Coal, copper concentrate, gold, and iron ore are summed to quarters, with the lone undated source cell excluded as non-observation. These remain distinct from customs export quantities. Their matched YoY correlations with exports are coal 0.854, copper concentrate 0.357, gold 0.238, and iron ore 0.013: production is neither a synonym nor a safe substitute for export volume.

A four-product, export-value-weighted physical-production growth index has 42 common YoY quarters and correlation 0.695 with real mining GVA. Export values are used only as adjacent-year weights, not to relabel export data as production. Short coverage, composition gaps, and weight endogeneity mean the decision is **ACCOUNTING + CALIBRATED DIAGNOSTIC; no mining-output equation is activated**.

### Coal UI semantics

Expose two separate controls: **Coal production (thousand tonnes)** for physical mining output and **Coal export quantity (thousand tonnes)** for trade volume. If the basic UI can support only one, label it “coal export quantity” and keep real mining output exogenous. An advanced joint-shock preset may alter both only after explicitly stating the linking assumption; it must not silently use exports as production.

## Fiscal validation

The prespecified candidate regresses total-government-revenue YoY growth on nominal mining-export-income YoY growth in the same quarter and at a one-quarter lag. Nominal mining export income is consistently converted to million MNT using the quarterly average MNT/USD rate. HC0 uncertainty is diagnostic only.

Same-quarter expanding-window forecasts (24-quarter minimum training sample) have RMSE 26.95 and MAE 19.19 percentage points, worse than historical mean RMSE 26.66 and MAE 19.08. The slope also falls from 0.138 in the early half to 0.021 in the late half. The lag-one candidate narrowly improves RMSE (27.64 versus 27.67) but has worse MAE and its slope reverses from -0.011 to 0.166. Directional accuracy does not improve over the benchmark in either case.

Decision: **KEEP FISCAL REVENUE EXOGENOUS**. These are reduced-form correlations, not causal fiscal mechanisms; no fiscal feedback, spending response, or forecast parameter is installed.
