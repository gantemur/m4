# M4 v0 estimation plan (no estimation performed)

| block | dependent / regressors | sample and treatment | key concern / minimum test |
|---|---|---|---|
| mining volume | real mining YoY; coal/copper quantity growth | commodity-rich 2011-Q1–2026-Q2; YoY | composition weights; held-out directional check |
| fiscal receipts | nominal revenue growth; mining exports, residual output | 2011 onward; quarterly dummies or YoY | policy/discretion confounding; sign/stability check |
| construction | real construction YoY; capex, credit, lagged YoY | 2011 onward; YoY/seasonal dummies | endogeneity and short sample; rolling validation |
| residual domestic | residual-output growth; spending, mining income, credit | after accounting reconciliation | residual definition; identity consistency |
| imports | import growth; domestic demand, MNT/USD change | 2001 onward where definitions fit | FX sign and simultaneity; out-of-sample directional test |

Simple OLS with robust/HAC errors is the transparent initial benchmark if estimation is later authorized. Large unrestricted VARs, stepwise feature fishing, and R²-only equation selection are explicitly rejected.
