import asyncio,json,sys,time,secrets,hashlib
from pathlib import Path
from datetime import timedelta
import os
os.environ.update(json.loads(Path('/tmp/micco-fix-20260929/deploy-backup/processes.json').read_text())['backend']['env'])
sys.path.insert(0,'/home/micco/MiccoRAG-v3/micco-backend/backend')
import httpx
from sqlalchemy import select,delete
from app.core.database import AsyncSessionLocal
from app.core.security import hash_password,create_access_token
from app.models.user import User
from app.models.department import Department
from app.models.document import Document
from app.models.knowledge_base import KnowledgeBase
from app.models.knowledge_entry import KnowledgeEntry
from app.models.chat_message import ChatMessage
from app.models.system_chat_log import SystemChatLog
P=Path('/tmp/micco-fix-20260929/live-proof');P.mkdir(exist_ok=True);extra_users=[];run='EVAL-LIFECYCLE-'+secrets.token_hex(5)
password=secrets.token_urlsafe(24);email=run.lower()+'@example.invalid';uid=None;wid=None;did=None
records=[]
TEXT='''TÀI LIỆU KIỂM THỬ TỔNG HỢP — KHÔNG PHẢI QUY ĐỊNH MICCO
Mã hồ sơ thử: EVA-57924.
Đây là dữ liệu thử cô lập để kiểm tra xử lý, tìm kiếm và dẫn nguồn.
Dự án thử mang tên Sen Xanh. Người phụ trách thử là Nguyễn Thử Nghiệm.
Ngân sách thử nghiệm được phê duyệt là 7.654.321 đồng.
Ngày nghiệm thu thử dự kiến là 15/11/2026.
Thời hạn xử lý hồ sơ thử tối đa là 6 ngày làm việc.
Không có số điện thoại, mật khẩu hay dữ liệu cá nhân thật trong tài liệu này.
'''
async def main():
 global uid,wid,did
 async with AsyncSessionLocal() as db:
  u=User(name=run,email=email,hashed_password=hash_password(password),role='Admin');db.add(u);await db.commit();await db.refresh(u);uid=u.id
 token=create_access_token({'sub':str(uid)},timedelta(minutes=30));headers={'Authorization':'Bearer '+token}
 async with httpx.AsyncClient(base_url='http://127.0.0.1:8001',timeout=120) as c:
  async def req(name,method,path,**kw):
   t=time.monotonic();r=await c.request(method,path,headers=headers,**kw)
   try:body=r.json()
   except Exception:body={'byte_length':len(r.content),'sha256':hashlib.sha256(r.content).hexdigest()}
   if path.endswith('/login') and isinstance(body,dict):body={k:v for k,v in body.items() if 'token' not in k}
   record={'name':name,'method':method,'path':path,'status':r.status_code,'seconds':round(time.monotonic()-t,3),'body':body};records.append(record);save()
   print(json.dumps({'name':name,'status':r.status_code},ensure_ascii=False),flush=True);return r
  try:
   await req('login_correct','POST','/api/auth/login',json={'email':email,'password':password})
   await req('login_wrong','POST','/api/auth/login',json={'email':email,'password':'wrong-evaluation-password'})
   r=await req('create_private_workspace','POST','/api/v1/workspaces',json={'name':run,'visibility':'private','description':'Temporary evaluation fixture','search_mode':'vector_only'})
   r.raise_for_status();wid=r.json()['id'];save()
   await req('edit_workspace','PUT',f'/api/v1/workspaces/{wid}',json={'name':run+'-updated','description':'Updated evaluation fixture'})
   await req('reject_bad_extension','POST',f'/api/v1/documents/upload/{wid}',files={'file':('fixture.exe',b'not executable','application/octet-stream')})
   r=await req('upload_txt','POST',f'/api/v1/documents/upload/{wid}?visibility=private',files={'file':(run+'.txt',TEXT.encode(),'text/plain')});r.raise_for_status();did=r.json().get('document_id') or r.json().get('id');save()
   await req('document_before_process','GET',f'/api/v1/documents/{did}')
   await req('process','POST',f'/api/v1/rag/process/{did}')
   await req('process_duplicate','POST',f'/api/v1/rag/process/{did}')
   deadline=time.monotonic()+660
   state='processing'
   while time.monotonic()<deadline:
    r=await c.get(f'/api/v1/documents/{did}',headers=headers);b=r.json();state=b.get('status')
    if state in ['indexed','failed','rejected']:
     records.append({'name':'terminal_ingest','status':r.status_code,'body':b});save();print('ingest terminal',state,flush=True);break
    await asyncio.sleep(3)
   if state not in ['indexed','failed','rejected']:raise RuntimeError('Ingest still active after11min; preserve fixture for explicit cleanup')
   await req('download','GET',f'/api/v1/documents/{did}/download')
   if state=='indexed':
    for port in [8001,8888]:
     response=await c.get(f'http://127.0.0.1:{port}/api/v1/rag/chunks/{did}')
     data=response.json(); chunks=data.get('chunks',[])
     records.append({'name':'anonymous_fixture_chunks','port':port,'status':response.status_code,'fixture_marker_present':any('EVA-57924' in str(x) or 'Sen Xanh' in str(x) for x in chunks),'chunk_count':len(chunks),'body_sha256':hashlib.sha256(response.content).hexdigest()});save()
    response=await c.get(f'/api/v1/documents/{did}')
    records.append({'name':'anonymous_document_control','status':response.status_code});save()
   if state=='indexed':
    async with AsyncSessionLocal() as db:
     for n,role in enumerate(['Giám đốc','Phó giám đốc','Nhân viên']):
      u=User(name=run+'-'+str(n),email=run.lower()+'-'+str(n)+'@example.invalid',hashed_password=hash_password(secrets.token_urlsafe(24)),role=role,department_id=6 if role!='Nhân viên' else 1)
      db.add(u);await db.flush();extra_users.append({'id':u.id,'role':role,'token':create_access_token({'sub':str(u.id)},timedelta(minutes=30))})
     await db.commit()
    for identity in extra_users:
     auth={'Authorization':'Bearer '+identity['token']};role=identity['role']
     response=await c.get(f'http://127.0.0.1:8888/api/v1/rag/chunks/{did}',headers=auth)
     expected=403 if role=='Nhân viên' else 200
     records.append({'name':'gateway_private_chunks_role','role':role,'status':response.status_code,'expected':expected,'pass':response.status_code==expected});save()
     if role!='Nhân viên':
      response=await c.put(f'/api/v1/documents/{did}',headers=auth,json={'original_filename':'forbidden rename'})
      records.append({'name':'management_no_write','role':role,'status':response.status_code,'expected':403,'pass':response.status_code==403});save()
      response=await c.post(f'http://127.0.0.1:8888/api/v1/rag/query/{wid}',headers=auth,json={'question':'Ngân sách và thời hạn dự án thử Sen Xanh?','document_ids':[did],'top_k':8})
      records.append({'name':'management_private_query','role':role,'status':response.status_code,'body':response.json()});save()
      if role=='Giám đốc':
       response=await c.post(f'http://127.0.0.1:8888/api/v1/rag/chat/{wid}',headers=auth,json={'message':'Ngân sách và thời hạn xử lý hồ sơ dự án thử Sen Xanh là bao nhiêu?','document_ids':[did],'force_search':True})
       records.append({'name':'management_private_answer','role':role,'status':response.status_code,'body':response.json()});save()
   await req('delete_fixture_doc','DELETE',f'/api/v1/documents/{did}')
   await req('deleted_doc_absent','GET',f'/api/v1/documents/{did}')
   await req('query_after_delete','POST',f'/api/v1/rag/query/{wid}',json={'question':'Ngân sách dự án thử Sen Xanh bao nhiêu?','top_k':8,'mode':'vector_only'})
   await req('delete_fixture_workspace','DELETE',f'/api/v1/workspaces/{wid}')
  except Exception as e:
   records.append({'name':'runner_error','error':type(e).__name__+':'+str(e)});save();print('runner_error',type(e).__name__,str(e),flush=True)
  finally:
   async with AsyncSessionLocal() as db:
    doc=await db.get(Document,did) if did else None
    ws=await db.get(KnowledgeBase,wid) if wid else None
    # Never delete an actively processing document underneath a job.
    active=doc and str(doc.status).split('.')[-1].lower() in ['parsing','processing','indexing']
    if active:
     records.append({'name':'cleanup_deferred_active_processing','user_id':uid,'workspace_id':wid,'document_id':did})
    else:
     if doc: await c.delete(f'/api/v1/documents/{did}',headers=headers)
     if ws: await c.delete(f'/api/v1/workspaces/{wid}',headers=headers)
     all_ids=[uid]+[x['id'] for x in extra_users]
     await db.execute(delete(ChatMessage).where(ChatMessage.user_id.in_(all_ids)))
     await db.execute(delete(User).where(User.id.in_([x['id'] for x in extra_users]),User.email.like(run.lower()+'-%')))
     if wid:await db.execute(delete(SystemChatLog).where(SystemChatLog.workspace_id==wid))
     await db.execute(delete(User).where(User.id==uid,User.email==email));await db.commit()
     records.append({'name':'cleanup_attempted','fixture_user_id':uid,'fixture_workspace_id':wid,'fixture_document_id':did})
    save()
def save(): (P/'live-postfix-results.json').write_text(json.dumps({'run_id':run,'fixture_ids':{'user':uid,'workspace':wid,'document':did},'fixture_text_sha256':hashlib.sha256(TEXT.encode()).hexdigest(),'expected_answer':'7.654.321 đồng; 6 ngày làm việc','results':records},ensure_ascii=False,indent=2))
asyncio.run(main())
