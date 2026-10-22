import asyncio,json,sys,time,secrets,hashlib
from pathlib import Path
from datetime import timedelta
import os
root=Path('/tmp/micco-fix-20260929')
os.environ.update(json.loads((root/'runtime-env.json').read_text()))
sys.path.insert(0,str(root/'micco-backend/backend'))
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
P=Path('/tmp/micco-fix-20260929/lifecycle');P.mkdir(exist_ok=True);run='EVAL-LIFECYCLE-'+secrets.token_hex(5)
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
 async with httpx.AsyncClient(base_url='http://127.0.0.1:18001',timeout=120) as c:
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
    for port in [18001]:
     response=await c.get(f'http://127.0.0.1:{port}/api/v1/rag/chunks/{did}')
     data=response.json(); chunks=data.get('chunks',[])
     records.append({'name':'anonymous_fixture_chunks','port':port,'status':response.status_code,'fixture_marker_present':any('EVA-57924' in str(x) or 'Sen Xanh' in str(x) for x in chunks),'chunk_count':len(chunks),'body_sha256':hashlib.sha256(response.content).hexdigest()});save()
    response=await c.get(f'/api/v1/documents/{did}')
    records.append({'name':'anonymous_document_control','status':response.status_code});save()
   if state=='indexed':
    identities=json.loads((root/'browser-auth.json').read_text())
    for role,identity in identities.items():
     auth={'Authorization':'Bearer '+identity['token']}
     response=await c.get(f'/api/v1/rag/chunks/{did}',headers=auth)
     expected=200 if role in ['Admin','Giám đốc','Phó giám đốc'] else 403
     records.append({'name':'private_chunks_role','role':role,'status':response.status_code,'expected':expected,'pass':response.status_code==expected});save()
     if role in ['Giám đốc','Phó giám đốc']:
      response=await c.put(f'/api/v1/documents/{did}',headers=auth,json={'original_filename':'forbidden rename'})
      records.append({'name':'management_no_write','role':role,'status':response.status_code,'expected':403,'pass':response.status_code==403});save()
    await req('query_fixture','POST',f'/api/v1/rag/query/{wid}',json={'question':'Ngân sách dự án Sen Xanh bao nhiêu?','document_ids':[did],'top_k':8,'mode':'vector_only'})
    await req('answer_fixture','POST',f'/api/v1/rag/chat/{wid}',json={'message':'Ngân sách và thời hạn xử lý hồ sơ dự án thử Sen Xanh là bao nhiêu?','document_ids':[did],'force_search':True,'mode':'vector_only'})
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
     await db.execute(delete(ChatMessage).where(ChatMessage.user_id==uid))
     if wid:await db.execute(delete(SystemChatLog).where(SystemChatLog.workspace_id==wid))
     await db.execute(delete(User).where(User.id==uid,User.email==email));await db.commit()
     records.append({'name':'cleanup_attempted','fixture_user_id':uid,'fixture_workspace_id':wid,'fixture_document_id':did})
    save()
def save(): (P/'stage-lifecycle-results.json').write_text(json.dumps({'run_id':run,'fixture_ids':{'user':uid,'workspace':wid,'document':did},'fixture_text_sha256':hashlib.sha256(TEXT.encode()).hexdigest(),'expected_answer':'7.654.321 đồng; 6 ngày làm việc','results':records},ensure_ascii=False,indent=2))
asyncio.run(main())
