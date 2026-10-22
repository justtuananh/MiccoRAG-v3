import asyncio,json,sys,hashlib
from pathlib import Path
sys.path.insert(0,'/home/micco/MiccoRAG-v3/micco-backend/backend')
from sqlalchemy import select,func
from app.core.database import AsyncSessionLocal
from app.models.user import User
from app.models.department import Department
from app.models.document import Document
from app.models.knowledge_base import KnowledgeBase
from app.models.knowledge_entry import KnowledgeEntry
from app.models.chat_message import ChatMessage
from app.models.system_chat_log import SystemChatLog
async def main():
 result={}
 async with AsyncSessionLocal() as db:
  for model,label,field in [(User,'users',User.name),(KnowledgeBase,'knowledge_bases',KnowledgeBase.name),(Document,'documents',Document.original_filename)]:
   result[label]={'total':(await db.execute(select(func.count()).select_from(model))).scalar(),'eval_remaining':(await db.execute(select(func.count()).select_from(model).where(field.like('EVAL-%')))).scalar()}
  result['eval_history_remaining']=(await db.execute(select(func.count()).select_from(ChatMessage).where(ChatMessage.content.contains('EVAL-20260929-')))).scalar()
  result['eval_logs_remaining']=(await db.execute(select(func.count()).select_from(SystemChatLog).where(SystemChatLog.question.contains('EVAL-20260929-')))).scalar()
 p=Path('/tmp/micco-evaluation-20260929');snap=json.loads((p/'snapshot.json').read_text());root=Path('/home/micco/MiccoRAG-v3')
 result['source_files_changed']=[n for n,h in snap['files'].items() if hashlib.sha256((root/n).read_bytes()).hexdigest()!=h]
 result['private_fixture_image_dirs_remaining']=[n for n in ['kb_13','kb_14'] if (root/'micco-backend/backend/data/docling'/n).exists()]
 (p/'cleanup-verification.json').write_text(json.dumps(result,ensure_ascii=False,indent=2));print(json.dumps(result,ensure_ascii=False))
asyncio.run(main())
