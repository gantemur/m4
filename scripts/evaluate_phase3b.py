"""Prespecified Phase 3B mining-bridge and fiscal validation; no activation."""
import csv, json
from datetime import datetime, timezone
from pathlib import Path
import numpy as np

ROOT = Path(__file__).resolve().parents[1]
PANEL = ROOT / "data/processed/m4-quarterly-v4.csv"
OUT = ROOT / "results/estimation-v0/phase3b-diagnostics.json"

def f(value): return None if value in ("", None, "None") else float(value)
def previous_year(q): return f"{int(q[:4])-1}-{q[-2:]}"
def yoy(rows, column):
    levels = {r["quarter"]: f(r.get(column)) for r in rows}; result = {}
    for quarter, value in levels.items():
        old = levels.get(previous_year(quarter))
        if value is not None and old not in (None, 0): result[quarter] = 100 * (value / old - 1)
    return result
def corr(a, b): return float(np.corrcoef(a, b)[0, 1]) if len(a) >= 3 and np.std(a) and np.std(b) else None
def ols(y, x):
    X = np.column_stack([np.ones(len(y)), x]); beta = np.linalg.lstsq(X, y, rcond=None)[0]
    residual = np.asarray(y) - X @ beta
    # HC0 robust uncertainty: reported only as a diagnostic, not an estimate for use.
    bread = np.linalg.inv(X.T @ X); meat = sum((u*u) * np.outer(row, row) for u, row in zip(residual, X))
    return {"coefficients": beta.tolist(), "robust_se_hc0": np.sqrt(np.diag(bread @ meat @ bread)).tolist(),
            "n": len(y), "rmse_in_sample": float(np.sqrt(np.mean(residual**2)))}
def expanding(y, x, minimum=24):
    """One-step-ahead expanding windows: every forecast only sees earlier data."""
    actual=[]; model=[]; mean=[]; origins=[]
    for end in range(minimum, len(y)):
        fit=ols(np.asarray(y[:end]), np.asarray(x[:end]))["coefficients"]
        actual.append(y[end]); model.append(fit[0] + fit[1]*x[end]); mean.append(float(np.mean(y[:end]))); origins.append(end)
    def score(pred):
        error=np.asarray(actual)-np.asarray(pred)
        return {"rmse":float(np.sqrt(np.mean(error**2))), "mae":float(np.mean(np.abs(error))),
                "directional_accuracy":float(np.mean((np.asarray(actual)>=0)==(np.asarray(pred)>=0)))}
    return {"origins": origins, "n_forecasts": len(actual), "model":score(model), "historical_mean":score(mean)}
def main():
    rows=list(csv.DictReader(PANEL.open())); OUT.parent.mkdir(parents=True, exist_ok=True)
    mining=yoy(rows, "gdp_real2015_mining")
    ipi={r["quarter"]:f(r.get("ipi_mining_yoy_percent")) for r in rows if f(r.get("ipi_mining_yoy_percent")) is not None}
    common=sorted(set(mining)&set(ipi)); ipi_stats={"n":len(common), "correlation_with_real_mining_gva_yoy":corr([ipi[q] for q in common],[mining[q] for q in common]),
      "mean_residual_pp":float(np.mean([mining[q]-ipi[q] for q in common])) if common else None,
      "rmse_residual_pp":float(np.sqrt(np.mean([(mining[q]-ipi[q])**2 for q in common]))) if common else None,
      "quarters":common}
    commodities={"coal":("coal_production_thousand_t","coal_export_quantity_thousand_t"),"copper_concentrate":("copper_concentrate_production_thousand_t","copper_concentrate_export_quantity_thousand_t"),"gold":("gold_production_kg","gold_export_quantity_t"),"iron_ore":("iron_ore_production_thousand_t","iron_ore_export_quantity_thousand_t")}
    production_export={}
    for name,(prod,expo) in commodities.items():
        a,b=yoy(rows,prod),yoy(rows,expo); qs=sorted(set(a)&set(b)); production_export[name]={"n":len(qs),"yoy_correlation":corr([a[q] for q in qs],[b[q] for q in qs]),"quarters":qs}
    # Production index: four physical growth rates, weighted by adjacent-year export values.
    pg={n:yoy(rows,p) for n,(p,_) in commodities.items()}; value={n:{r['quarter']:f(r.get(f'{n}_export_value_usd_thousand')) for r in rows} for n in commodities}; index={}
    valid=set.intersection(*(set(v) for v in pg.values()))
    for q in valid:
        old=previous_year(q); weights=[((value[n].get(q) or 0)+(value[n].get(old) or 0))/2 for n in commodities]
        if sum(weights)>0:index[q]=sum(w*pg[n][q] for w,n in zip(weights,commodities))/sum(weights)
    qi=sorted(set(index)&set(mining)); production_index={"n":len(qi),"correlation_with_real_mining_gva_yoy":corr([index[q] for q in qi],[mining[q] for q in qi]),"quarters":qi,
      "method":"Tornqvist-style weighted physical production growth; adjacent-year export values are weights only, not production."}
    revenue=yoy(rows,"government_revenue_mnt_million")
    mx={r['quarter']:sum((f(r.get(f'{n}_export_value_usd_thousand')) or 0) for n in commodities)/1000*(f(r.get('mnt_per_usd_quarterly_average')) or 0) for r in rows}
    mxg={q:100*(v/mx[previous_year(q)]-1) for q,v in mx.items() if mx.get(previous_year(q)) not in (None,0)}
    fiscal={}
    for lag in (0,1):
        pairs=sorted((q,revenue[q],mxg.get(previous_year(q)) if lag else mxg.get(q)) for q in revenue if (mxg.get(previous_year(q)) if lag else mxg.get(q)) is not None)
        qs,y,x=zip(*pairs) if pairs else ([],[],[])
        if len(y)>25:
            split=len(y)//2; full=ols(np.asarray(y),np.asarray(x)); early=ols(np.asarray(y[:split]),np.asarray(x[:split])); late=ols(np.asarray(y[split:]),np.asarray(x[split:]))
            fiscal[f"lag_{lag}"]={"quarters":list(qs),"full_sample":full,"early_slope":early['coefficients'][1],"late_slope":late['coefficients'][1],"expanding_window":expanding(list(y),list(x)),"minimum_training_observations":24}
    decision="KEEP FISCAL REVENUE EXOGENOUS"
    result={"input_dataset":"m4-quarterly-v4","generated_at":datetime.now(timezone.utc).isoformat(),"scope":"diagnostics only; no model block activated","gdp_identity":{"maximum_absolute_rounding_gap_mnt_million":max(abs(f(r.get('gdp_gva_identity_gap_mnt_million')) or 0) for r in rows)},"ipi_mining_bridge":ipi_stats,"physical_production_vs_exports":production_export,"physical_production_index":production_index,"fiscal_expanding_validation":fiscal,"fiscal_decision":decision,"decision_reason":"The candidate is a reduced-form fiscal relationship; it is not adopted without stable, benchmark-improving out-of-sample evidence and institutional fiscal timing support."}
    OUT.write_text(json.dumps(result,indent=2)+"\n"); print(json.dumps(result,indent=2))
if __name__ == "__main__": main()
