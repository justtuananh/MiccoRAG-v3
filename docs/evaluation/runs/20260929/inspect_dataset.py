import asyncio,json,sys,hashlib,subprocess
from pathlib import Path
sys.path.insert(0,'/home/micco/MiccoRAG-v3/micco-backend/backend')
from app.core.database import AsyncSessionLocal
from sqlalchemy import select
from app.models.user import User
from app.models.department import Department
from app.models.document import Document
from app.models.knowledge_base import KnowledgeBase
from app.models.knowledge_entry import KnowledgeEntry
from app.models.chat_message import ChatMessage
async def main():
 async with AsyncSessionLocal() as db:
  docs=list((await db.execute(select(Document))).scalars())
  users=list((await db.execute(select(User))).scalars())
  kbs=list((await db.execute(select(KnowledgeBase))).scalars())
  out={'documents':[{'id':d.id,'kb':d.workspace_id,'name':d.original_filename,'status':str(d.status),'approval':d.approval_status,'visibility':d.visibility,'department_id':d.department_id,'chunk_count':d.chunk_count,'pages':d.page_count,'markdown_len':len(d.markdown_content or ''),'markdown_sha256':hashlib.sha256((d.markdown_content or '').encode()).hexdigest()} for d in docs],'users':[{'id':u.id,'role':u.role,'department_id':u.department_id} for u in users],'kbs':[{'id':k.id,'visibility':k.visibility,'owner_id':k.owner_id,'department_id':k.department_id,'search_mode':k.search_mode} for k in kbs]}
  p=Path('/tmp/micco-evaluation-20260929');p.mkdir(exist_ok=True)
  (p/'dataset.json').write_text(json.dumps(out,ensure_ascii=False,indent=2))
  # Only source content of named synthetic demo docs, not arbitrary business docs.
  demo=[{'id':d.id,'kb':d.workspace_id,'name':d.original_filename,'markdown':d.markdown_content} for d in docs if d.original_filename.startswith(('micco-','Test_','test_'))]
  (p/'demo-sources.json').write_text(json.dumps(demo,ensure_ascii=False,indent=2))
  print(json.dumps(out,ensure_ascii=False))
asyncio.run(main())
