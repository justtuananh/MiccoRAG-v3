"""Independent acceptance checks: real routes/auth/SQL, synthetic DB and no providers."""
import json
from datetime import date
from io import BytesIO
from types import SimpleNamespace
from unittest.mock import AsyncMock

import httpx
import pytest
import pytest_asyncio
from fastapi import FastAPI, HTTPException, UploadFile
from PIL import Image
from sqlalchemy.ext.asyncio import create_async_engine, async_sessionmaker

from app.core.database import Base
from app.core.deps import get_db
from app.core.config import Settings, settings
from app.core.security import create_access_token
from app.models import User, Department, KnowledgeBase, Document
from app.models.document import DocumentStatus
from app.api import rag, documents, workspaces, expert
from app.api_compat import documents as legacy_documents, auth


@pytest_asyncio.fixture
async def scoped_api(monkeypatch):
    engine = create_async_engine('sqlite+aiosqlite:///:memory:')
    async with engine.begin() as connection:
        await connection.run_sync(Base.metadata.create_all)
    sessions = async_sessionmaker(engine, expire_on_commit=False)
    monkeypatch.setattr(settings, 'DEBUG', False)
    monkeypatch.setattr(settings, 'JWT_SECRET_KEY', 'isolated-acceptance-test-secret-not-a-deployed-key')
    async with sessions() as db:
        db.add_all([Department(id=1,name='A'), Department(id=2,name='B')])
        for uid, role, dept in [(1,'Admin',None),(2,'Giám đốc',None),(3,'Phó giám đốc',None),(4,'Trưởng phòng',1),(5,'Nhân viên',1),(6,'Nhân viên',2),(7,'Nhân viên',None)]:
            db.add(User(id=uid,name=f'U{uid}',email=f'{uid}@fixture.test',hashed_password='unused',role=role,department_id=dept))
        db.add_all([KnowledgeBase(id=10,name='Public',visibility='public'), KnowledgeBase(id=11,name='Department A',visibility='department',department_id=1),KnowledgeBase(id=12,name='Private A',visibility='private',owner_id=5)])
        for did,wid,vis,dept,owner,approval in [(100,10,'public',1,5,'approved'),(101,11,'department',1,5,'approved'),(102,12,'private',None,5,'approved'),(103,12,'public',2,5,'approved'),(104,10,'public',1,5,'pending_org')]:
            db.add(Document(id=did,workspace_id=wid,filename=f'{did}.txt',original_filename=f'Quy trình {did}.txt',file_type='txt',file_size=3,status=DocumentStatus.INDEXED,chunk_count=1,visibility=vis,department_id=dept,uploader_id=owner,approval_status=approval,effective_from=date(2020, 1, 1),markdown_content='PRIVATE_FIXTURE' if wid==12 else f'public fixture {did}',category='Quy trình',tags='fixture'))
        await db.commit()
        async def database():
            yield db
        app=FastAPI()
        for router in (rag.router,documents.router,workspaces.router,expert.router): app.include_router(router,prefix='/api/v1')
        app.include_router(legacy_documents.router)
        app.dependency_overrides[get_db]=database
        calls=[]
        class Vector:
            def get_by_ids(self, ids):
                calls.append(ids)
                return {'ids':ids,'documents':['PRIVATE_FIXTURE']*len(ids),'metadatas':[{}]*len(ids)}
        service=SimpleNamespace(vector_store=Vector())
        monkeypatch.setattr(rag,'get_rag_service',lambda *a,**k: service)
        async with httpx.AsyncClient(transport=httpx.ASGITransport(app=app),base_url='http://fixture') as client:
            yield client,db,calls
    await engine.dispose()


def bearer(uid):
    return {'Authorization':'Bearer '+create_access_token({'sub':uid})}


@pytest.mark.parametrize('method,path,body',[
 ('GET','/api/v1/rag/chunks/102',None),('GET','/api/v1/rag/stats/12',None),
 ('GET','/api/v1/rag/analytics/12',None),('GET','/api/v1/rag/graph/12',None),
 ('GET','/api/v1/rag/entities/12',None),('GET','/api/v1/rag/relationships/12',None),
 ('POST','/api/v1/rag/process/102',{}),('POST','/api/v1/rag/process-batch',{'document_ids':[102]}),
 ('POST','/api/v1/rag/reindex/102',{}),('POST','/api/v1/rag/reindex-workspace/12',{}),
 ('POST','/api/v1/rag/query/12',{'question':'fixture'}),('POST','/api/v1/rag/chat/12',{'message':'fixture'}),
 ('POST','/api/v1/rag/chat/12/stream',{'message':'fixture'}),('POST','/api/v1/rag/debug-chat/12',{'message':'fixture'}),
 ('POST','/api/v1/rag/chat/12/rate',{'message_id':'fixture','source_id':'x','rating':1}),
 ('GET','/api/v1/documents/102/markdown',None),('GET','/api/v1/documents/102/images/x/file',None),
])
async def test_anonymous_rejected_before_data_or_jobs(scoped_api,method,path,body):
    client,_,calls=scoped_api
    response=await client.request(method,path,json=body)
    assert response.status_code==401,response.text
    assert not calls


@pytest.mark.parametrize('uid,allowed',[(1,True),(2,True),(3,True),(4,False),(5,True),(6,False),(7,False)])
@pytest.mark.parametrize('path',['/api/v1/rag/chunks/102','/api/v1/documents/102/markdown','/api/v1/documents/103/markdown','/api/v1/documents/workspace/12'])
async def test_private_kb_boundary_overrides_public_child_metadata(scoped_api,uid,allowed,path):
    client,_,calls=scoped_api
    response=await client.get(path,headers=bearer(uid))
    assert response.status_code==(200 if allowed else 403),response.text
    if not allowed:
        assert 'PRIVATE_FIXTURE' not in response.text
        assert not calls


@pytest.mark.parametrize('uid',[1,2,3,5])
async def test_private_owner_and_directors_retrieval_scope(scoped_api,uid):
    _,db,_=scoped_api
    user=await db.get(User,uid)
    assert set(await rag.get_allowed_document_ids(db,user,12))=={102,103}
    assert 104 not in await rag.get_allowed_document_ids(db,user,10)


@pytest.mark.parametrize('params,expected',[
 ({'search':'QUY TRÌNH 100'}, {100}),({'search':'không tồn tại' },set()),
 ({'type':'txt'}, {100,101,102,103}),({'type':'pdf'},set()),
 ({'category':'Quy trình','department_id':2},{103}),
])
async def test_legacy_filters_on_real_sql(scoped_api,params,expected):
    client,_,_=scoped_api
    response=await client.get('/api/documents',params=params,headers=bearer(1))
    assert response.status_code==200,response.text
    assert {int(d['id']) for d in response.json()}==expected


@pytest.mark.parametrize('uid',[4,6,7])
async def test_legacy_list_cannot_leak_private_public_child(scoped_api,uid):
    client,_,_=scoped_api
    response=await client.get('/api/documents',headers=bearer(uid))
    assert response.status_code==200,response.text
    assert not {102,103}&{int(d['id']) for d in response.json()}


@pytest.mark.parametrize('secret',['',' ','change-me-in-env'])
def test_production_rejects_unconfigured_jwt(secret):
    config=Settings(_env_file=None,DEBUG=False,JWT_SECRET_KEY=secret)
    with pytest.raises(RuntimeError,match='JWT_SECRET_KEY'):config.validate_runtime_security()


def test_configured_jwt_and_explicit_dev_are_accepted():
    Settings(_env_file=None,DEBUG=False,JWT_SECRET_KEY='test-configured-secret').validate_runtime_security()
    Settings(_env_file=None,DEBUG=True,JWT_SECRET_KEY='change-me-in-env').validate_runtime_security()


@pytest.mark.parametrize('data',[b'<script>alert(1)</script>',b'not an image',b'\x89PNG\r\n\x1a\n'])
def test_fake_avatar_rejected(data):
    with pytest.raises(HTTPException) as error:auth._avatar_png(data)
    assert error.value.status_code==400


async def test_avatar_reencoding_and_db_failure_preserve_previous(tmp_path,monkeypatch):
    monkeypatch.setattr(auth,'AVATAR_DIR',tmp_path)
    image=Image.new('RGB',(4,4),'red'); source=BytesIO();image.save(source,format='PNG')
    clean=auth._avatar_png(source.getvalue()+b'<script>marker</script>')
    assert b'marker' not in clean
    Image.open(BytesIO(clean)).verify()
    (tmp_path/'old.png').write_bytes(clean)
    user=SimpleNamespace(id=5,avatar='old.png')
    db=SimpleNamespace(commit=AsyncMock(side_effect=RuntimeError('fixture commit failure')),rollback=AsyncMock())
    with pytest.raises(RuntimeError):
        await auth.upload_avatar(UploadFile(filename='new.png',file=BytesIO(clean)),user,db)
    assert user.avatar=='old.png'
    assert [p.name for p in tmp_path.iterdir()]==['old.png']
    db.rollback.assert_awaited_once()


@pytest.mark.parametrize('db_ok,vector_ok',[(True,True),(False,True),(True,False),(False,False)])
async def test_readiness_reports_dependency_failures(monkeypatch,db_ok,vector_ok):
    from app import main
    class Connection:
        async def __aenter__(self):return self
        async def __aexit__(self,*args):pass
        async def execute(self,*args):
            if not db_ok:raise RuntimeError('fake database failure')
    class Client:
        def __init__(self,*args,**kwargs):pass
        async def __aenter__(self):return self
        async def __aexit__(self,*args):pass
        async def get(self,*args):
            if not vector_ok:raise httpx.ConnectError('fake vector failure')
            return httpx.Response(200,json={'nanosecond heartbeat':123},request=httpx.Request('GET','http://fixture'))
    monkeypatch.setattr(main,'engine',SimpleNamespace(connect=lambda:Connection()))
    monkeypatch.setattr(main.httpx,'AsyncClient',Client)
    result=await main.ready()
    assert result.status_code==(200 if db_ok and vector_ok else 503)
    assert json.loads(result.body)['checks']=={'database':db_ok,'vector':vector_ok}


@pytest.mark.parametrize('uid',[2,3,4,6,7])
@pytest.mark.parametrize('method,path,body',[
 ('POST','/api/v1/rag/reindex/102',None),
 ('POST','/api/v1/rag/reindex-workspace/12',None),
 ('PUT','/api/v1/documents/102',{'original_filename':'unauthorized rename'}),
 ('DELETE','/api/v1/documents/102',None),
 ('PUT','/api/v1/workspaces/12',{'name':'unauthorized rename'}),
])
async def test_read_all_does_not_grant_write(scoped_api,uid,method,path,body):
    client,db,calls=scoped_api
    response=await client.request(method,path,json=body,headers=bearer(uid))
    assert response.status_code==403,response.text
    assert not calls
    assert await db.get(Document,102) is not None


def test_no_public_document_image_mount():
    from app.main import app
    assert not any(getattr(route,'path','')=='/static/doc-images' for route in app.routes)


async def test_insecure_startup_fails_before_database(monkeypatch):
    from app import main
    monkeypatch.setattr(settings,'DEBUG',False)
    monkeypatch.setattr(settings,'JWT_SECRET_KEY','change-me-in-env')
    class ForbiddenEngine:
        def begin(self):raise AssertionError('Database must not be reached')
    monkeypatch.setattr(main,'engine',ForbiddenEngine())
    with pytest.raises(RuntimeError,match='JWT_SECRET_KEY'):
        async with main.lifespan(main.app):pass


@pytest.mark.parametrize('module_name',['app.core.deps','app.core.database'])
async def test_disconnect_cannot_interrupt_returning_database_connection(monkeypatch,module_name):
    import importlib
    import anyio
    module=importlib.import_module(module_name)
    closed=[]
    class Session:
        async def close(self):
            await anyio.sleep(0)
            closed.append(True)
    monkeypatch.setattr(module,'AsyncSessionLocal',Session)
    generator=module.get_db()
    await anext(generator)
    with anyio.CancelScope() as scope:
        scope.cancel()
        await generator.aclose()
    assert closed==[True]


async def test_dev_skip_only_works_in_explicit_debug(scoped_api,monkeypatch):
    client,_,_=scoped_api
    response=await client.get('/api/v1/workspaces',headers={'Authorization':'Bearer dev-skip'})
    assert response.status_code==401
    monkeypatch.setattr(settings,'DEBUG',True)
    response=await client.get('/api/v1/workspaces',headers={'Authorization':'Bearer dev-skip'})
    assert response.status_code==200,response.text
