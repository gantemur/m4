"""Acquire Phase 3B official additions; write corrected immutable v4."""
import csv,json
from pathlib import Path
from datetime import datetime,timezone
from m4.data import NsoClient,parse_jsonstat2
from m4.data.transforms import monthly_flow_to_quarterly,monthly_average_to_quarterly
ROOT=Path(__file__).resolve().parents[1]; RUN=datetime.now(timezone.utc).strftime('%Y-%m-%dT%H%M%SZ'); SNAP=ROOT/f'data/snapshots/nso/{RUN}'; OUT=ROOT/'data/processed/m4-quarterly-v4.csv'
GDP='Economy%2C%20environment/National%20Accounts/DT_NSO_0500_004V1.px'; IPI='Industry%2C%20service/Industry/DT_NSO_1100_016V5.px'; PROD='Industry%2C%20service/Industry/DT_NSO_1100_006V2.px'
def av(m,i):return list(m['variables'][i]['values'])
def codes(c,m,d,labels):return c.codes_for_labels(m,d,labels)
def q(s):
 y,x=s.split('-',1); quarter={'I':1,'II':2,'III':3,'IV':4}.get(x.upper())
 if quarter is None: quarter=int(x)
 return f'{y}-Q{quarter}'
def main():
 c=NsoClient();SNAP.mkdir(parents=True,exist_ok=False); p={r['quarter']:{k:v for k,v in r.items() if k not in {'quarter','quarter.1'}} for r in csv.DictReader(open(ROOT/'data/processed/m4-quarterly-v2.csv'))}; manifests=[]
 # Full nominal production decomposition, including taxes less subsidies.
 m=c.metadata(GDP); ind,comp,t=[v['code'] for v in m['variables']]; ids=codes(c,m,ind,['GDP, at current prices']); ds={ind:list(ids.values()),comp:av(m,1),t:av(m,2)}; d=c.query_dataset(GDP,ds,raw_directory=ROOT/'data/raw/phase3b'/RUN); rows=parse_jsonstat2(d); labels={v.strip():k for k,v in zip(m['variables'][1]['values'],m['variables'][1]['valueTexts'])};
 for r in rows:
  if r['value'] is None:continue
  period=q(r[t]); label=str(r[comp]).strip(); p.setdefault(period,{})[f'_gdpcomp_{r[f"{comp}_id"]}']=float(r['value'])
 for period,row in p.items():
  total=row.get('_gdpcomp_0'); tax=row.get('_gdpcomp_10'); components=[row.get(f'_gdpcomp_{i}') for i in map(str,range(1,10))]
  if total is not None and tax is not None and all(value is not None for value in components):
   industry=sum(components)
   row['industry_gva_nominal_mnt_million']=industry; row['taxes_less_subsidies_nominal_mnt_million']=tax; row['other_industry_gva_nominal_mnt_million']=industry-row.get('_gdpcomp_1',0)-row.get('_gdpcomp_2',0)-row.get('_gdpcomp_5',0); row['gdp_gva_identity_gap_mnt_million']=total-(industry+tax)
 manifests.append({'table':'DT_NSO_0500_004V1','purpose':'GDP = industry GVA + taxes less subsidies; other industry GVA accounting'})
 # IPI YoY, average monthly published rates into quarters.
 m=c.metadata(IPI);ind,sec,mo=[v['code'] for v in m['variables']]; ids=codes(c,m,ind,['Compared with same period of previous year']); ss=codes(c,m,sec,['Mining and quarrying','Mining of coal and lignite','Mining of metal ores']);d=c.query_dataset(IPI,{ind:list(ids.values()),sec:list(ss.values()),mo:av(m,2)},raw_directory=ROOT/'data/raw/phase3b'/RUN);rows=parse_jsonstat2(d);targets={'Mining and quarrying':'ipi_mining_yoy_percent','Mining of coal and lignite':'ipi_coal_yoy_percent','Mining of metal ores':'ipi_metal_ores_yoy_percent'}
 for label,code in ss.items():
  # The selected NSO comparison measure is an index (100 = no annual change),
  # so express it as percentage-point YoY growth before quarterly averaging.
  monthly=[{'period':r[mo],'value':None if r['value'] is None else float(r['value'])-100} for r in rows if r[f'{sec}_id']==code]
  for period,value in monthly_average_to_quarterly(monthly,'period','value').items():p.setdefault(period,{})[targets[label]]=value
 manifests.append({'table':'DT_NSO_1100_016V5','purpose':'official monthly IPI comparison index transformed as index minus 100, then averaged quarterly'})
 # Physical production monthly flows.
 m=c.metadata(PROD);prod,mo=[v['code'] for v in m['variables']]; ps=codes(c,m,prod,['Coal /thousand t/','Copper, concentrate /thousand t/','Gold /kg/','Iron ore /thousand t/']);d=c.query_dataset(PROD,{prod:list(ps.values()),mo:av(m,1)},raw_directory=ROOT/'data/raw/phase3b'/RUN);rows=parse_jsonstat2(d);targets={'Coal /thousand t/':'coal_production_thousand_t','Copper, concentrate /thousand t/':'copper_concentrate_production_thousand_t','Gold /kg/':'gold_production_kg','Iron ore /thousand t/':'iron_ore_production_thousand_t'}
 for label,code in ps.items():
  # NSO includes an undated first category cell ("1"); it is not a monthly
  # observation and is excluded transparently rather than imputed.
  monthly=[{'period':r[mo],'value':r['value']} for r in rows if r[f'{prod}_id']==code and len(str(r[mo]).split('-'))==2]
  for period,value in monthly_flow_to_quarterly(monthly,'period','value').items():p.setdefault(period,{})[targets[label]]=value
 manifests.append({'table':'DT_NSO_1100_006V2','purpose':'physical production monthly flows summed to quarter'})
 cols=sorted({k for v in p.values() for k in v if not k.startswith('_') and k != 'quarter'});
 with OUT.open('w',newline='') as f:
  w=csv.DictWriter(f,fieldnames=['quarter',*cols]);w.writeheader();[w.writerow({'quarter':x,**{k:v for k,v in p[x].items() if not k.startswith('_')}}) for x in sorted(p)]
 (SNAP/'manifest.json').write_text(json.dumps({'snapshot':RUN,'tables':manifests},indent=2)+'\n');print(f'Wrote {OUT}')
if __name__=='__main__':main()
