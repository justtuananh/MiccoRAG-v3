import asyncio,json,sys,time,hashlib,secrets,zipfile,xml.etree.ElementTree as ET,re,os
os.environ.update(json.load(open('/tmp/micco-fix-20260929/runtime-env.json')))
from pathlib import Path
from datetime import timedelta
sys.path.insert(0,'/tmp/micco-fix-20260929/micco-backend/backend')
import httpx
from sqlalchemy import select,delete
from app.core.database import AsyncSessionLocal
from app.core.config import settings
from app.core.security import create_access_token,hash_password
from app.models.user import User
from app.models.department import Department
from app.models.document import Document
from app.models.knowledge_base import KnowledgeBase
from app.models.knowledge_entry import KnowledgeEntry
from app.models.chat_message import ChatMessage
from app.models.system_chat_log import SystemChatLog
P=Path('/tmp/micco-fix-20260929/pilot-citation');P.mkdir(exist_ok=True)
RUN='EVAL-CIT-20260929-'+secrets.token_hex(4)
CASES=[
 {'id':'G01','doc':26,'kb':11,'question':'Theo quy chế phụ cấp độc hại trong tài liệu được chọn, mức phụ cấp mỗi tháng là bao nhiêu và có dùng làm căn cứ đóng bảo hiểm xã hội không?','required':['1.250.000','không'],'expected':'1.250.000 đồng/tháng; không dùng làm căn cứ tính đóng BHXH','criteria':['RAG-17','SRC-01']},
 {'id':'G02','doc':26,'kb':11,'question':'Theo tài liệu được chọn, nghỉ đúng 14 ngày trong tháng có được hưởng phụ cấp độc hại không? Có được quy đổi bồi dưỡng hiện vật thành tiền không?','required':['14','không'],'expected':'Nghỉ từ 14 ngày trở lên không được hưởng phụ cấp tháng đó; hiện vật không quy đổi thành tiền','criteria':['RAG-14','RAG-17']},
 {'id':'G03','doc':26,'kb':11,'question':'Theo tài liệu được chọn, Phòng Nhân sự rà soát danh sách hưởng phụ cấp vào ngày nào hằng tháng?','required':['25'],'expected':'Ngày 25 hằng tháng','criteria':['RAG-17','SRC-02']},
 {'id':'G04','doc':22,'kb':9,'question':'Theo quy trình mua sắm vật tư được chọn, gói đúng 500 triệu đồng có phải đấu thầu không, ai phê duyệt và thời gian xử lý tối đa bao nhiêu ngày làm việc?','required':['500','20','giám đốc','đấu thầu'],'expected':'Có đấu thầu; Giám đốc phê duyệt; 20 ngày làm việc; từ 500 triệu trở lên','criteria':['RAG-02','RAG-14','RAG-17']},
 {'id':'G05','doc':22,'kb':9,'question':'Theo tài liệu được chọn, hãy nêu đủ năm bước mua sắm vật tư và đơn vị nghiệm thu chất lượng trước khi thanh toán.','required':['đề xuất','thẩm định','nhà cung cấp','hợp đồng','nghiệm thu','ban an toàn'],'expected':'Đề xuất; thẩm định; chọn nhà cung cấp; ký hợp đồng và nhận hàng; nghiệm thu và thanh toán; Ban An toàn nghiệm thu trước Phòng Kế toán thanh toán','criteria':['RAG-14','SRC-01']},
 {'id':'G06','doc':27,'kb':11,'question':'Theo kế hoạch huấn luyện năm 2026 được chọn, đợt III diễn ra tháng nào, bao nhiêu người, thời lượng và đơn vị huấn luyện là gì?','required':['9','134','16','cao đẳng'],'expected':'Tháng 9; 134 người; 16 giờ; Trường Cao đẳng Công nghiệp','criteria':['RAG-02','RAG-17']},
 {'id':'G07','doc':27,'kb':11,'question':'Theo kế hoạch huấn luyện được chọn, bài sát hạch có bao nhiêu câu, thời gian làm bài, mức điểm đạt và người không đạt phải thi lại trong bao lâu?','required':['40','45','80','30'],'expected':'40 câu trong 45 phút; từ 80 điểm; học lại và sát hạch bổ sung trong 30 ngày','criteria':['RAG-14','RAG-17']},
 {'id':'G08','doc':26,'kb':11,'question':'Chỉ theo tài liệu được chọn, số điện thoại cá nhân của người phụ trách quy chế phụ cấp là gì? Nếu tài liệu không có thì nói rõ không có thông tin.','required':[],'expected':'Không có số điện thoại trong nguồn; phải từ chối cung cấp số phỏng đoán','no_answer':True,'criteria':['RAG-16']},
 {'id':'G09','doc':26,'kb':11,'question':'Theo tài liệu được chọn, phụ cấp độc hại là 9.999.999 đồng/tháng đúng không? Hãy kiểm tra và đính chính theo nguồn.','required':['1.250.000'],'expected':'Bác bỏ 9.999.999; xác nhận 1.250.000 đồng/tháng','criteria':['RAG-17','SRC-01']},
 {'id':'G10','doc':26,'kb':11,'question':'Theo tài liệu được chọn, mức phụ cấp độc hại hằng tháng là bao nhiêu, và số điện thoại cá nhân người phụ trách là gì?','required':['1.250.000'],'expected':'1.250.000 đồng/tháng; nguồn không có số điện thoại cá nhân','criteria':['RAG-15']},
]
results=[];users=[];questions=[]
def save(): (P/'rag-pilot-results.json').write_text(json.dumps({'run_id':RUN,'cases':CASES,'results':results},ensure_ascii=False,indent=2))
async def call(client,case,variant,role,token,repeat=1):
 q=case['question']+f' [Mã phiên đánh giá {RUN}/{case["id"]}/{variant}/{role}/{repeat}]'
 questions.append(q)
 kind='query' if variant=='query' else 'chat'
 url=f'http://127.0.0.1:18001/api/v1/rag/{kind}/{case["kb"]}'+('/stream' if variant=='stream' else '')
 body={'question' if kind=='query' else 'message':q,'document_ids':[case['doc']],'mode':'vector_only' if role=='Admin' else 'hybrid'}
 if kind=='query':body['top_k']=8
 else:body['force_search']=True;body['enable_thinking']=False
 start=time.monotonic();record={'case_id':case['id'],'variant':variant,'role':role,'repeat':repeat,'url':url,'request':body,'mode_requested':body['mode']}
 try:
  if variant=='stream':
   events=[];first=None;event_name=None;raw=[]
   async with client.stream('POST',url,headers={'Authorization':'Bearer '+token},json=body) as response:
    record['status_code']=response.status_code
    async for line in response.aiter_lines():
     raw.append(line)
     if line.startswith('event:'):event_name=line[6:].strip()
     if line.startswith('data:'):
      data=line[5:].strip()
      try:event=json.loads(data)
      except Exception:event={'raw':data}
      events.append({'event':event_name,'data':event})
      if first is None and event_name=='token': first=time.monotonic()-start
   record['events']=events;record['raw_sse']='\n'.join(raw);record['first_token_seconds']=first
  else:
   response=await client.post(url,headers={'Authorization':'Bearer '+token},json=body)
   record['status_code']=response.status_code
   try:record['response']=response.json()
   except Exception:record['response_text']=response.text[:1000]
 except Exception as e:record['error']=type(e).__name__+': '+str(e)
 record['seconds']=round(time.monotonic()-start,3);results.append(record);save()
 print(json.dumps({'case':case['id'],'variant':variant,'role':role,'status':record.get('status_code'),'seconds':record['seconds'],'error':record.get('error')},ensure_ascii=False),flush=True)
async def main():
 try:
  async with AsyncSessionLocal() as db:
   for role in ['Admin','Giám đốc']:
    u=User(name='Evaluation '+RUN, email=RUN.lower()+'-'+str(len(users))+'@example.invalid',hashed_password=hash_password(secrets.token_urlsafe(24)),role=role,department_id=6 if role!='Admin' else None)
    db.add(u);await db.flush();users.append({'id':u.id,'role':role,'token':create_access_token({'sub':str(u.id)},timedelta(minutes=40))})
   await db.commit()
   (P/'rag-fixtures.json').write_text(json.dumps({'run_id':RUN,'user_ids':[u['id'] for u in users]}))
   originals=[]
   for d in (await db.execute(select(Document).where(Document.id.in_([22,26,27])))).scalars():
    f=settings.BASE_DIR/'uploads'/d.filename;record={'id':d.id,'exists':f.exists(),'markdown_hash':hashlib.sha256((d.markdown_content or '').encode()).hexdigest()}
    if f.exists():
     record['file_sha256']=hashlib.sha256(f.read_bytes()).hexdigest()
     if f.suffix.lower()=='.docx':
      with zipfile.ZipFile(f) as z: x=ET.fromstring(z.read('word/document.xml'));record['text']='\n'.join(n.text or '' for n in x.iter('{http://schemas.openxmlformats.org/wordprocessingml/2006/main}t'))
     elif f.suffix.lower()=='.pdf':
      import pypdfium2 as pdfium
      pdf=pdfium.PdfDocument(f);record['pages']=[pdf[i].get_textpage().get_text_range() for i in range(len(pdf))]
    originals.append(record)
   (P/'original-sources.json').write_text(json.dumps(originals,ensure_ascii=False,indent=2))
  async with httpx.AsyncClient(timeout=httpx.Timeout(100,connect=10)) as client:
   admin=users[0];director=users[1]
   
   await call(client,CASES[3],'chat',director['role'],director['token'])
   await call(client,CASES[3],'stream',director['role'],director['token'])
   

 finally:
  # Remove only run-owned users/history and log entries carrying this unique marker.
  async with AsyncSessionLocal() as db:
   ids=[u['id'] for u in users]
   if ids:
    hist=await db.execute(delete(ChatMessage).where(ChatMessage.user_id.in_(ids)))
    logs=await db.execute(delete(SystemChatLog).where(SystemChatLog.question.contains(RUN)))
    gone=await db.execute(delete(User).where(User.id.in_(ids),User.email.like(RUN.lower()+'%')))
    await db.commit()
    (P/'rag-cleanup.json').write_text(json.dumps({'run_id':RUN,'removed_history':hist.rowcount,'removed_logs':logs.rowcount,'removed_users':gone.rowcount,'user_ids':ids}))
  save()
asyncio.run(main())
