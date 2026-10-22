import csv,json
from pathlib import Path
from collections import Counter,defaultdict
P=Path(__file__).parent;root=P.parents[1]
all_records=[]
for name in ['functional','business','rag','security']:
 d=json.loads((P/(name+'-results.json')).read_text());rs=d.get('records',d.get('criteria'))
 for r in rs:
  r=dict(r);r['criterion_id']=r.get('criterion_id',r.get('id'));r['group']=name;r['result_file']=name+'-results.json';all_records.append(r)
ids=[r['criterion_id'] for r in all_records];assert len(set(ids))==len(ids)
byid={r['criterion_id']:r for r in all_records}
with (root/'checklist.csv').open(encoding='utf-8-sig') as f:criteria=list(csv.DictReader(f))
assert set(byid)=={r['criterion_id'] for r in criteria}, (set(byid)-{r['criterion_id'] for r in criteria})
for c in criteria:
 r=byid[c['criterion_id']];c['status']=r['status'];c['actual']=r.get('actual',r.get('evidence',''));c['evidence_path']=r['result_file'];c['notes']=r.get('limitations','');c['run_id']='20260929';c['owner']=r['group'];c['reviewer']='Codex coordinator + Sol specialist';r['priority']=c['priority']
with (P/'results-checklist.csv').open('w',encoding='utf-8-sig',newline='') as f:
 w=csv.DictWriter(f,fieldnames=list(criteria[0]));w.writeheader();w.writerows(criteria)
summary={'criteria':len(criteria),'status':dict(Counter(r['status'] for r in all_records)),'by_group':{g:dict(Counter(r['status'] for r in all_records if r['group']==g)) for g in ['functional','business','rag','security']},'by_priority':{p:dict(Counter(r['status'] for r in all_records if r['priority']==p)) for p in ['P0','P1','P2']},'verdict':'NO-GO','acceptance_note':'PASS applies only to documented execution scope; broad business acceptance and release gates remain unmet.'}
(P/'summary.json').write_text(json.dumps(summary,ensure_ascii=False,indent=2));(P/'all-results.json').write_text(json.dumps({'summary':summary,'records':all_records},ensure_ascii=False,indent=2));print(json.dumps(summary,ensure_ascii=False))
