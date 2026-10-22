import asyncio,json,sys,hashlib,os
from datetime import timedelta
from pathlib import Path
sys.path.insert(0,'/home/micco/MiccoRAG-v3/micco-backend/backend')
from app.core.database import AsyncSessionLocal
from app.core.security import create_access_token
from sqlalchemy import select
from app.models.user import User
from app.models.department import Department
from app.models.document import Document
from app.models.knowledge_base import KnowledgeBase
from app.models.knowledge_entry import KnowledgeEntry
from app.models.chat_message import ChatMessage
async def main():
 async with AsyncSessionLocal() as db:
  selected=list((await db.execute(select(Document).where(Document.id.in_([22,26,27,31])))).scalars())
  out=[{'id':d.id,'kb':d.workspace_id,'name':d.original_filename,'markdown':d.markdown_content,'sha256':hashlib.sha256((d.markdown_content or '').encode()).hexdigest()} for d in selected]
  p=Path('/tmp/micco-evaluation-20260929');p.mkdir(exist_ok=True)
  (p/'source-pilot.json').write_text(json.dumps(out,ensure_ascii=False,indent=2))
  users=list((await db.execute(select(User).order_by(User.id))).scalars())
  roles={}
  for u in users:
   if u.role not in roles: roles[u.role]={'id':u.id,'role':u.role,'department_id':u.department_id,'token':create_access_token({'sub':str(u.id)},timedelta(minutes=40))}
  tokenfile=p/'browser-auth.json';tokenfile.write_text(json.dumps(roles,ensure_ascii=False));tokenfile.chmod(0o600)
  print('source-pilot.json and protected browser auth prepared; no tokens printed')
asyncio.run(main())
