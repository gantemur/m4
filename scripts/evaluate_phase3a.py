"""Small prespecified Phase 3A viability diagnostics; no simulator activation."""
import csv, json, math
from pathlib import Path
import numpy as np

ROOT=Path(__file__).resolve().parents[1]; PANEL=ROOT/'data/processed/m4-quarterly-v2.csv'; OUT=ROOT/'results/estimation-v0'
def f(x): return None if x in ('',None,'None') else float(x)
def yoy(rows,col):
 d={r['quarter']:f(r.get(col)) for r in rows}; out={}
 for q,v in d.items():
  p=f'{int(q[:4])-1}-{q[-2:]}'
  if v and d.get(p) not in (None,0): out[q]=100*(v/d[p]-1)
 return out
def ols(y,x):
 X=np.column_stack([np.ones(len(y)),x]); b=np.linalg.lstsq(X,np.array(y),rcond=None)[0]; resid=np.array(y)-X@b
 return {'coefficients':b.tolist(),'n':len(y),'rmse':float(np.sqrt(np.mean(resid**2))),'residual_sd':float(np.std(resid,ddof=max(1,len(b))))}
def main():
 rows=list(csv.DictReader(PANEL.open())); OUT.mkdir(parents=True,exist_ok=True)
 # Tornqvist-style four-commodity export quantity index (coverage incomplete).
 comm=['coal','copper_concentrate','gold','iron_ore']; qg={c:yoy(rows,f'{c}_export_quantity_thousand_t' if c!='gold' else 'gold_export_quantity_t') for c in comm}; vals={c:{r['quarter']:f(r.get(f'{c}_export_value_usd_thousand')) for r in rows} for c in comm}; index={};
 for q in sorted(set.intersection(*(set(qg[c]) for c in comm))):
  prev=f'{int(q[:4])-1}-{q[-2:]}'; weights=[]
  for c in comm:
   a,b=vals[c].get(q),vals[c].get(prev)
   weights.append(0 if a is None or b is None else (a+b)/2)
  if sum(weights)>0:index[q]=sum(w*g for w,g in zip(weights,[qg[c][q] for c in comm]))/sum(weights)
 mining=yoy(rows,'gdp_real2015_mining'); common=sorted(set(index)&set(mining)); corr=float(np.corrcoef([index[q] for q in common],[mining[q] for q in common])[0,1]) if len(common)>2 else None
 # fiscal reduced form; MNT conversion is USD million * MNT/USD = million MNT.
 rev=yoy(rows,'government_revenue_mnt_million'); mx={r['quarter']:((f(r.get('coal_export_value_usd_thousand')) or 0)+(f(r.get('copper_concentrate_export_value_usd_thousand')) or 0)+(f(r.get('gold_export_value_usd_thousand')) or 0)+(f(r.get('iron_ore_export_value_usd_thousand')) or 0))/1000*(f(r.get('mnt_per_usd_quarterly_average')) or 0) for r in rows}; mxg={q:100*(v/mx.get(f'{int(q[:4])-1}-{q[-2:]}')-1) for q,v in mx.items() if mx.get(f'{int(q[:4])-1}-{q[-2:]}') not in (None,0)}; cf=sorted(set(rev)&set(mxg)); fiscal=ols([rev[q] for q in cf],[mxg[q] for q in cf]) if len(cf)>8 else None
 con=yoy(rows,'gdp_real2015_construction'); cap=yoy(rows,'government_capital_expenditure_mnt_million'); cc=sorted(set(con)&set(cap)); construction=ols([con[q] for q in cc],[cap[q] for q in cc]) if len(cc)>8 else None
 imports=yoy(rows,'imports_usd_million'); demand=yoy(rows,'gross_capital_formation_current'); ci=sorted(set(imports)&set(demand)); imp=ols([imports[q] for q in ci],[demand[q] for q in ci]) if len(ci)>8 else None
 result={'input_dataset':'m4-quarterly-v2','method':'prespecified simple OLS diagnostics with no activation','mining_quantity_index':{'n':len(common),'correlation_with_real_mining_yoy':corr,'coverage_note':'export quantities omit other mining and are not production'},'fiscal_reduced_form':fiscal,'construction_capex':construction,'imports_demand':imp,'samples':{'mining':common,'fiscal':cf,'construction':cc,'imports':ci}}
 (OUT/'phase3a-diagnostics.json').write_text(json.dumps(result,indent=2)+'\n'); print(json.dumps(result,indent=2))
if __name__=='__main__':main()
