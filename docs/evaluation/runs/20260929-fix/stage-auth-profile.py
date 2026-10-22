import asyncio,json,sys,secrets
from pathlib import Path
import os
root=Path('/tmp/micco-fix-20260929')
os.environ.update(json.loads((root/'runtime-env.json').read_text()))
sys.path.insert(0,str(root/'micco-backend/backend'))
import httpx
from sqlalchemy import select,delete
from app.core.database import AsyncSessionLocal
from app.models.user import User
from app.models.department import Department
from app.models.knowledge_base import KnowledgeBase
from app.models.document import Document
from app.models.knowledge_entry import KnowledgeEntry
from app.models.chat_message import ChatMessage
RUN='EVAL-AUTH-'+secrets.token_hex(5);records=[];ids=[]
async def main():
 async with httpx.AsyncClient(base_url='http://127.0.0.1:18001',timeout=30) as c:
  email=RUN.lower()+'@example.invalid';pwd=secrets.token_urlsafe(24);newpwd=secrets.token_urlsafe(24)
  try:
   r=await c.post('/api/auth/register',json={'name':RUN,'email':email,'password':pwd,'department_id':6,'role':'Admin'})
   record={'case':'register_cannot_escalate','status':r.status_code};records.append(record)
   if r.status_code not in [200,201]:record['body']=r.json();return
   d=r.json();token=d['access_token'];headers={'Authorization':'Bearer '+token}
   async with AsyncSessionLocal() as db:
    u=(await db.execute(select(User).where(User.email==email))).scalar_one();ids.append(u.id);record['actual_role']=u.role
   me=await c.get('/api/auth/me',headers=headers);records.append({'case':'get_me_before','status':me.status_code,'department_id':me.json().get('department_id')})
   r=await c.put('/api/auth/me',headers=headers,json={'name':RUN+'-changed','password':newpwd,'role':'Admin'})
   records.append({'case':'update_profile_department_user','status':r.status_code,'error':r.json().get('detail') if r.status_code>=400 else None})
   r=await c.post('/api/auth/login',json={'email':email,'password':newpwd});records.append({'case':'new_password_login','status':r.status_code})
   r=await c.post('/api/auth/login',json={'email':email,'password':pwd});records.append({'case':'old_password_login','status':r.status_code})
   async with AsyncSessionLocal() as db:
    u=(await db.execute(select(User).where(User.email==email))).scalar_one();records.append({'case':'persisted_profile','name_changed':u.name==RUN+'-changed','role':u.role})
  finally:
   async with AsyncSessionLocal() as db:
    r=await db.execute(delete(User).where(User.email==email));await db.commit();records.append({'case':'cleanup','deleted_users':r.rowcount})
   Path('/tmp/micco-fix-20260929/stage-auth-profile-results.json').write_text(json.dumps({'run_id':RUN,'records':records},ensure_ascii=False,indent=2));print(json.dumps(records,ensure_ascii=False))
asyncio.run(main())
