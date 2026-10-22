import sys,asyncio,json
from pathlib import Path
sys.path.insert(0,'/home/micco/MiccoRAG-v3/micco-backend/backend')
from app.core.database import AsyncSessionLocal
from app.models.user import User
from app.models.department import Department
from app.models.document import Document
from app.models.knowledge_base import KnowledgeBase
from app.models.knowledge_entry import KnowledgeEntry
from app.models.chat_message import ChatMessage
from app.api.expert import _get_allowed_document_ids
from app.api.rag import get_allowed_document_ids
from sqlalchemy import select
async def main():
 out=[]
 async with AsyncSessionLocal() as db:
  for role in ['Giám đốc','Phó giám đốc']:
   user=(await db.execute(select(User).where(User.role==role).order_by(User.id))).scalars().first()
   for wid in [9,11]:out.append({'role':role,'workspace_id':wid,'rag_allowed':await get_allowed_document_ids(db,user,wid),'expert_allowed':await _get_allowed_document_ids(db,user,wid)})
 Path('/tmp/micco-evaluation-20260929/expert-scope-results.json').write_text(json.dumps(out,ensure_ascii=False,indent=2));print(json.dumps(out,ensure_ascii=False))
asyncio.run(main())
