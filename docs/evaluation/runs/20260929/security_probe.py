"""Isolated MiccoRAG security probes. No production DB, Chroma, LLM or queue calls."""
import asyncio, json, os, tempfile, socket
from pathlib import Path
from types import SimpleNamespace as NS
from unittest.mock import patch
from fastapi import FastAPI
from fastapi.testclient import TestClient
from app.api import rag, documents, expert
from app.core.deps import get_db
from app.core.security import get_current_user
from app.models.document import Document, DocumentStatus
from app.models.knowledge_base import KnowledgeBase
from app.services import llm as llm_module
from app.services import vector_store as vector_module

# Fail closed if any test accidentally tries the real network.
def no_network(*args,**kwargs): raise RuntimeError('network disabled in isolated security probe')
socket.socket.connect=no_network
socket.socket.connect_ex=no_network
socket.create_connection=no_network
asyncio.open_connection=no_network
class FakeLLM:
 async def acomplete(self,*args,**kwargs): return 'fixture-answer'
llm_module.get_llm_provider=lambda: FakeLLM()
class FakeVectorCollection:
 def delete_collection(self): pass
vector_module.get_vector_store=lambda *args,**kwargs: FakeVectorCollection()

SENTINEL='SECURITY_FIXTURE_SENTINEL'
user=NS(id=22,role='Nhân viên',department_id=2)
manager=NS(id=23,role='Trưởng phòng',department_id=2)
owner=NS(id=11,role='Nhân viên',department_id=1)
kb=KnowledgeBase(id=77,name='fixture private KB',visibility='private',owner_id=11,department_id=None,search_mode='vector_only')
doc=Document(id=88,workspace_id=77,filename='fixture.txt',original_filename='fixture.txt',file_type='txt',file_size=8,status=DocumentStatus.INDEXED,chunk_count=1,uploader_id=11,department_id=2,visibility='public',approval_status='approved',markdown_content=SENTINEL,page_count=0,image_count=0,table_count=0,processing_time_ms=0)
class Rows:
 def __init__(self,val=None,items=None): self.val=val; self.items=items if items is not None else ([val] if val is not None else [])
 def scalar_one_or_none(self): return self.val
 def scalar(self): return self.val
 def scalars(self): return self
 def all(self): return self.items
 def first(self): return self.items[0] if self.items else None
class DB:
 def __init__(self): self.added=[]; self.commits=0; self.calls=[]
 async def execute(self,stmt):
  statement_text=str(stmt)
  self.calls.append(statement_text.splitlines()[0][:90])
  if 'count(' in statement_text.lower(): return Rows(0)
  if 'documents.status NOT IN' in statement_text: return Rows(items=[])
  desc=getattr(stmt,'column_descriptions',[])
  if desc and desc[0].get('name')=='id': return Rows(items=[(88,)])
  entity=desc[0].get('entity') if desc else None
  name=getattr(entity,'__name__','')
  if name=='KnowledgeBase': return Rows(kb)
  if name=='Document': return Rows(doc)
  return Rows(0,[])
 async def commit(self): self.commits+=1
 async def refresh(self,obj): pass
 def add(self,obj):
  if getattr(obj,'id',None) is None: obj.id=1000+len(self.added)
  self.added.append(obj)

db=DB(); who=user
async def dbdep(): yield db
async def authdep(): return who
app=FastAPI()
for router in (rag.router,documents.router,expert.router): app.include_router(router,prefix='/api/v1')
app.dependency_overrides[get_db]=dbdep
app.dependency_overrides[get_current_user]=authdep
client=TestClient(app,raise_server_exceptions=False)
results=[]
def rec(cid,status,actual,evidence,scope='isolated-asgi',limitations=''):
 results.append(dict(criterion_id=cid,status=status,actual=actual,evidence=evidence,environment='remote venv, fake DB/fixtures, no app lifespan',scope=scope,limitations=limitations))
def request(method,path,**kw):
 r=client.request(method,path,**kw)
 return r

def missing_auth(path):
 # Runtime API route's dependency tree is resolved by FastAPI on request, not app.routes introspection.
 # This helper relies on observed no-Authorization responses with fake DB.
 return path

# SEC-01/02: mocked vector store returns a private sentinel; no real Chroma access.
class Vector:
 def get_by_ids(self,ids): return {'ids':ids,'documents':[SENTINEL],'metadatas':[{}]}
class RagService:
 vector_store=Vector()
 def query(self,**kw): return NS(query=kw['question'],chunks=[NS(content=SENTINEL,chunk_id='fixture',score=1.0,metadata={})],context=SENTINEL)
 def get_chunk_count(self): return 1
 async def query_deep(self,**kw):
  chunk=NS(content=SENTINEL,document_id=88,page_no=1,heading_path=[],source_file='fixture.txt',chunk_index=0)
  cite=NS(source_file='fixture.txt',page_no=1,document_id=88)
  return NS(chunks=[chunk],citations=[cite],knowledge_graph_summary='',context=SENTINEL,image_refs=[],query=kw.get('question',''))
 async def delete_document(self,*args): pass
 async def process_document(self,**kw): return 1
with patch.object(rag,'get_rag_service',return_value=RagService()):
 app.dependency_overrides.pop(get_current_user,None)
 r=request('GET','/api/v1/rag/chunks/88')
 rec('SEC-01','FAIL' if r.status_code==200 and SENTINEL in r.text else 'BLOCKED',f'HTTP {r.status_code}; private sentinel returned={SENTINEL in r.text}','rag.get_document_chunks via TestClient; fake Document and vector store')
 app.dependency_overrides[get_current_user]=authdep
 r=request('GET','/api/v1/rag/chunks/88')
 rec('SEC-02','FAIL' if r.status_code==200 and SENTINEL in r.text else 'BLOCKED',f'HTTP {r.status_code}; foreign user sentinel returned={SENTINEL in r.text}','same fixture, foreign user id=22, owner=11')

# SEC-03/04: fake workspace but no provider; checking that request reaches handler with no auth.
for cid,token in [('SEC-03',False),('SEC-04',True)]:
 if not token: app.dependency_overrides.pop(get_current_user,None)
 else: app.dependency_overrides[get_current_user]=authdep
 with patch.object(rag,'get_rag_service',return_value=RagService()) as getrag, patch('app.services.nexus_rag_service.NexusRAGService',RagService):
  r=request('POST','/api/v1/rag/debug-chat/77',json={'message':'fixture question','document_ids':[88]})
  exposed=r.status_code==200 and SENTINEL in r.text
  rec(cid,'FAIL' if exposed else 'BLOCKED',f'HTTP {r.status_code}; fake retriever invoked={getrag.called}; private sentinel returned={exposed}','fake KB/retriever/LLM; socket network disabled')
app.dependency_overrides[get_current_user]=authdep

# SEC-05: four anonymous calls against fixtures, no files or jobs. Process indexed doc returns 200; batch with missing ID responds.
app.dependency_overrides.pop(get_current_user,None)
r1=request('POST','/api/v1/rag/process/88')
r2=request('POST','/api/v1/rag/process-batch',json={'document_ids':[999999]})
r3=request('POST','/api/v1/rag/reindex/88')
r4=request('POST','/api/v1/rag/reindex-workspace/77')
rec('SEC-05','FAIL' if r1.status_code==200 or r2.status_code==200 or r4.status_code==200 else 'BLOCKED',f'HTTP process={r1.status_code}, batch={r2.status_code}, reindex={r3.status_code}, workspace={r4.status_code}','fake DB; missing local fixture file prevents reindex; no background job launched',limitations='Reindex action not exercised; authentication absence also verified from route signatures')
app.dependency_overrides[get_current_user]=authdep

# SEC-07: private KB with public-marked doc, query in vector_only mode and fake RAG.
with patch.object(rag,'get_rag_service',return_value=RagService()):
 r=request('POST','/api/v1/rag/query/77',json={'question':'fixture?','mode':'vector_only'})
 rec('SEC-07','FAIL' if r.status_code==200 and SENTINEL in r.text else 'BLOCKED',f'HTTP {r.status_code}; foreign user private KB sentinel={SENTINEL in r.text}','fake private KB/public-marked doc, fake vector RAG')

# SEC-09: document detail and markdown; response may serialize model; no file disk read.
r=request('GET','/api/v1/documents/88/markdown')
rec('SEC-09','FAIL' if r.status_code==200 and SENTINEL in r.text else 'BLOCKED',f'HTTP {r.status_code}; private KB document markdown sentinel={SENTINEL in r.text}','fake DB, foreign user and public-marked doc',limitations='Covers markdown variant; list/detail/download not all executed')

# SEC-11/12: upload uses only temporary directory, never repository uploads; fake DB saves metadata in memory.
with tempfile.TemporaryDirectory(prefix='micco-sec-') as td:
 with patch.object(documents,'UPLOAD_DIR',Path(td)):
  who=user
  r=request('POST','/api/v1/documents/upload/77',files={'file':('fixture.txt',b'fixture','text/plain')})
  rec('SEC-11','FAIL' if r.status_code==200 and bool(db.added) else 'BLOCKED',f'HTTP {r.status_code}; fake DB added={len(db.added)>0}; temp files={len(os.listdir(td))}','fake private KB foreign to user; temp dir only')
  db.added.clear()
  who=manager
  r=request('POST','/api/v1/documents/upload/77?department_id=5&visibility=public',files={'file':('fixture2.txt',b'fixture','text/plain')})
  added=db.added[-1] if db.added else None
  rec('SEC-12','FAIL' if r.status_code==200 and added is not None and added.approval_status=='approved' and added.department_id==5 else 'BLOCKED',f'HTTP {r.status_code}; foreign KB added={added is not None}; forged dept retained={getattr(added,"department_id",None)==5}; autoapproved={getattr(added,"approval_status",None)=="approved"}','temp dir only; manager dept=2, forged dept=5')
who=user

# SEC-16 public StaticFiles mount: no private image fixture exists yet; read-only status checked elsewhere.
rec('SEC-16','BLOCKED','No synthetic extracted image in app mount; no private live image URL used','app/main.py StaticFiles mount without auth','static-only',limitations='Needs isolated mount fixture to prove actual bytes')

# SEC-18: stats/analytics anonymous; fake db returns counts and records, no Chroma.
app.dependency_overrides.pop(get_current_user,None)
with patch.object(rag,'get_rag_service',return_value=RagService()):
 a=request('GET','/api/v1/rag/stats/77')
 b=request('GET','/api/v1/rag/analytics/77')
 rec('SEC-18','FAIL' if a.status_code==200 else 'BLOCKED',f'HTTP stats={a.status_code}, analytics={b.status_code}; no auth token','fake private KB; no real stats/KG',limitations='Analytics may fail on incomplete fake DB; stats path is confirmed')
app.dependency_overrides[get_current_user]=authdep

# SEC-20 configuration check uses equality only, never secret output.
from app.core.config import settings
is_default=settings.JWT_SECRET_KEY=='change-me-in-env'
rec('SEC-20','BLOCKED',f'effective JWT secret uses built-in default={is_default}; DEBUG={settings.DEBUG}','boolean equality only, secret value not printed','remote-process-config',limitations='Startup fail-safe behavior has not been added/tested; current config may differ from deployed process')

# SEC-21 isolated auth dependency: fake DB user object cannot pass SQLAlchemy selectinload; DEBUG false path is clear.
rec('SEC-21','BLOCKED',f'current DEBUG={settings.DEBUG}; dev-skip branch gated on DEBUG','app/core/security.py:61-81','code+remote-config',limitations='DEBUG=true runtime variant not exercised')

# SEC-22 route behavior on isolated ASGI, live probes collected separately.
rec('SEC-22','BLOCKED','Live backend/gateway GET probes are stored in live-probes.json','direct backend and gateway','live-read-only',limitations='No state-changing live requests')

# SEC-23 isolated file size/extension checks. Avoid >50MB allocation; extension case only.
with tempfile.TemporaryDirectory(prefix='micco-sec-') as td:
 with patch.object(documents,'UPLOAD_DIR',Path(td)):
  r=request('POST','/api/v1/documents/upload/77',files={'file':('fixture.exe',b'fixture','application/octet-stream')})
  rec('SEC-23','BLOCKED',f'bad-extension HTTP {r.status_code}; temp files={len(os.listdir(td))}','isolated document upload validation',limitations='Oversize and image content spoofing not exercised')

# SEC-24 intended management policy inspected through helper; no DB fixture route test.
from app.api.workspaces import _can_access_workspace,_can_modify_workspace
for role in ['Giám đốc','Phó giám đốc']:
 mgr=NS(id=99,role=role,department_id=9)
 assert _can_access_workspace(mgr,kb) and not _can_modify_workspace(mgr,kb)
rec('SEC-24','PASS','Both management roles read private fixture KB; neither can modify it','workspaces._can_access_workspace/_can_modify_workspace','isolated-unit',limitations='Dynamic newly created KB variant covered by role-only logic, not DB creation')

# SEC-06: foreign user reindex with only temporary file and fully fake RAG service.
with tempfile.TemporaryDirectory(prefix='micco-sec-') as td:
 Path(td,'fixture.txt').write_text('synthetic fixture')
 with patch.object(rag,'UPLOAD_DIR',td),patch.object(rag,'get_rag_service',return_value=RagService()) as svc:
  r=request('POST','/api/v1/rag/reindex/88')
  rec('SEC-06','FAIL' if r.status_code==200 and svc.called else 'BLOCKED',f'HTTP {r.status_code}; foreign reindex reached fake RAG={svc.called}','temp file; fake DB/RAG; socket network disabled')

# SEC-10: exercise real DeepRetriever.query with a fake KG and vector store.
from app.services.deep_retriever import DeepRetriever
class KG:
 async def get_relevant_context(self,question): return SENTINEL
class EmptyVector:
 def query(self,**kw): return {'documents':[],'metadatas':[],'ids':[]}
class Embed:
 def embed_query(self,question): return [0.0]
retriever=DeepRetriever.__new__(DeepRetriever)
retriever.workspace_id=77; retriever.kg_service=KG(); retriever.vector_store=EmptyVector(); retriever.embedder=Embed(); retriever.db=None; retriever.reranker=None
try:
 kg_result=asyncio.run(retriever.query('fixture?',mode='hybrid',document_ids=[88],include_images=False))
 leaked=SENTINEL in kg_result.context or SENTINEL in kg_result.knowledge_graph_summary
 rec('SEC-10','FAIL' if leaked else 'BLOCKED',f'private KG sentinel returned={leaked} with allowed document_ids=[88]','real DeepRetriever.query, fake KG/vector/embedder; socket network disabled')
except Exception as e:
 rec('SEC-10','BLOCKED',f'isolated retriever exception={type(e).__name__}','fake KG/vector/embedder',limitations='No data exposure assertion completed')

# SEC-16: same StaticFiles mount behavior with temp private image, no repository file write.
from fastapi.staticfiles import StaticFiles
with tempfile.TemporaryDirectory(prefix='micco-sec-static-') as td:
 Path(td,'private.png').write_bytes(b'PNG_FIXTURE')
 static_app=FastAPI(); static_app.mount('/static/doc-images',StaticFiles(directory=td))
 sr=TestClient(static_app).get('/static/doc-images/private.png')
 rec('SEC-16','FAIL' if sr.status_code==200 and sr.content==b'PNG_FIXTURE' else 'BLOCKED',f'HTTP {sr.status_code}; anonymous fixture bytes returned={sr.content==b"PNG_FIXTURE"}','isolated identical StaticFiles mount, temp file; not deployed image ID')

# SEC-17: fake chat row, no DB persistence, anonymous caller.
from app.models.chat_message import ChatMessage
class RatingDB(DB):
 async def execute(self,stmt):
  if 'chat_messages' in str(stmt): return Rows(rating_row)
  return await super().execute(stmt)
rating_row=ChatMessage(id=99,workspace_id=77,user_id=11,message_id='fixture-message',role='assistant',content='fixture',ratings={})
rating_db=RatingDB()
async def rating_dep(): yield rating_db
app.dependency_overrides[get_db]=rating_dep
app.dependency_overrides.pop(get_current_user,None)
rr=request('POST','/api/v1/rag/chat/77/rate',json={'message_id':'fixture-message','source_index':'a1','rating':'relevant'})
rec('SEC-17','FAIL' if rr.status_code==200 and rating_row.ratings.get('a1')=='relevant' else 'BLOCKED',f'HTTP {rr.status_code}; anonymous fake rating changed={rating_row.ratings.get("a1")=="relevant"}','fake chat row/DB; no production data')
app.dependency_overrides[get_db]=dbdep
app.dependency_overrides[get_current_user]=authdep

# SEC-19: KB existence check is reached by foreign user; fake recommendation avoids vector DB.
async def empty_experts(**kw): return []
with patch.object(expert,'recommend_experts',side_effect=empty_experts) as ex:
 er=request('GET','/api/v1/expert/recommend/77?query=fixture')
 rec('SEC-19','FAIL' if er.status_code==200 else 'BLOCKED',f'HTTP {er.status_code}; recommendation invoked={ex.called}','fake KB/doc IDs/recommendation; foreign user')

# SEC-21: actual auth function, two config branches, no route or network.
from fastapi.security import HTTPAuthorizationCredentials
from fastapi import HTTPException
from app.core.security import get_current_user as current_user_fn
class UserDB(DB):
 async def execute(self,stmt): return Rows(owner)
creds=HTTPAuthorizationCredentials(scheme='Bearer',credentials='dev-skip')
prior_debug=settings.DEBUG
try:
 settings.DEBUG=False
 try:
  asyncio.run(current_user_fn(creds,UserDB()))
  denied=False
 except HTTPException as e: denied=(e.status_code==401)
 settings.DEBUG=True
 allowed=asyncio.run(current_user_fn(creds,UserDB())) is owner
 rec('SEC-21','PASS' if denied and allowed else 'FAIL',f'DEBUG=false rejected={denied}; DEBUG=true fixture user returned={allowed}','actual get_current_user, fake DB; settings restored')
finally: settings.DEBUG=prior_debug

# SEC-08: nonstream chat in a foreign private KB; all services fake and sockets blocked.
with patch.object(rag,'get_rag_service',return_value=RagService()) as chat_svc,patch.object(rag,'log_system_chat',side_effect=empty_experts):
 cr=request('POST','/api/v1/rag/chat/77',json={'message':'fixture question','mode':'vector_only'})
 rec('SEC-08','FAIL' if cr.status_code==200 and chat_svc.called else 'BLOCKED',f'nonstream HTTP {cr.status_code}; foreign private KB retrieval invoked={chat_svc.called}','fake KB/RAG/LLM/DB; socket network disabled',limitations='Streaming variant not executed; one failing variant suffices to fail criterion')

# SEC-23: legacy avatar accepts a .png name but non-image bytes. Temp dir only.
from app.api_compat import auth as compat_auth
avatar_app=FastAPI(); avatar_app.include_router(compat_auth.router)
avatar_user=NS(id=22,avatar=None,role='Nhân viên',department_id=2)
async def avatar_auth(): return avatar_user
avatar_app.dependency_overrides[get_db]=dbdep
avatar_app.dependency_overrides[get_current_user]=avatar_auth
with tempfile.TemporaryDirectory(prefix='micco-sec-avatar-') as td:
 with patch.object(compat_auth,'AVATAR_DIR',Path(td)):
  ar=TestClient(avatar_app,raise_server_exceptions=False).post('/api/auth/me/avatar',files={'file':('fake.png',b'this is not an image','image/png')})
  accepted=ar.status_code==200 and len(os.listdir(td))==1
  rec('SEC-23','FAIL' if accepted else 'BLOCKED',f'non-image bytes with .png HTTP {ar.status_code}; temp file saved={accepted}','legacy avatar upload, temp dir/fake DB; no real image parser',limitations='Oversize branch not executed; spoofed image variant fails')

# SEC-25 extension: caller-controlled user_id on authenticated chat persistence.
from app.models.chat_message import ChatMessage as ChatModel
db.added.clear()
with patch.object(rag,'get_rag_service',return_value=RagService()),patch.object(rag,'log_system_chat',side_effect=empty_experts):
 hijack=request('POST','/api/v1/rag/chat/77?user_id=11',json={'message':'fixture question','mode':'vector_only'})
 rows=[x for x in db.added if isinstance(x,ChatModel)]
 forged=bool(rows) and all(x.user_id==11 for x in rows)
 rec('SEC-25','FAIL' if hijack.status_code==200 and forged else 'BLOCKED',f'HTTP {hijack.status_code}; authenticated id=22 wrote {len(rows)} fake chat rows as id=11={forged}','fake DB/RAG/LLM; no production persistence; socket network disabled',limitations='Requires user_id query parameter; endpoint still authenticates caller')

print(json.dumps(results,ensure_ascii=False))
