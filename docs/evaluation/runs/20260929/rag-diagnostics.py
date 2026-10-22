import json,urllib.request,time
from pathlib import Path
P=Path('/tmp/micco-evaluation-20260929')
auth=json.loads((P/'browser-auth.json').read_text())['Admin']['token']
results=[]
requests=[('GET','/api/v1/rag/chunks/22',None),('POST','/api/v1/rag/query/9',{'question':'Trong bảng Thời gian xử lý tối đa, gói từ 500 triệu trở lên là bao nhiêu ngày làm việc và cấp phê duyệt nào?','document_ids':[22],'top_k':8,'mode':'vector_only'}),('POST','/api/v1/rag/query/9',{'question':'20 ngày làm việc Giám đốc qua đấu thầu','document_ids':[22],'top_k':8,'mode':'vector_only'})]
for method,path,body in requests:
 start=time.monotonic(); req=urllib.request.Request('http://127.0.0.1:8001'+path,data=json.dumps(body,ensure_ascii=False).encode() if body else None,method=method,headers={'Authorization':'Bearer '+auth,'Content-Type':'application/json'})
 try:
  with urllib.request.urlopen(req,timeout=60) as r:results.append({'path':path,'request':body,'status':r.status,'seconds':time.monotonic()-start,'response':json.load(r)})
 except Exception as e:results.append({'path':path,'error':str(e)})
(P/'rag-diagnostics.json').write_text(json.dumps(results,ensure_ascii=False,indent=2))
print(json.dumps([{'path':r['path'],'status':r.get('status'),'chunks':r.get('response',{}).get('total_chunks',r.get('response',{}).get('chunk_count'))} for r in results]))
