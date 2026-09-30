"""Executable policy checks on real ORM rows and authenticated ASGI routes."""
from datetime import date, datetime, timedelta
from types import SimpleNamespace
from unittest.mock import AsyncMock
import json
import pytest
from fastapi import HTTPException
from sqlalchemy import select
from app.models import Document, KnowledgeBase
from app.models.document import DocumentStatus
from app.services.answer_guard import validate_review, guard_answer, NO_EVIDENCE
from app.services.document_lifecycle import published_ids
from app.services.conversation_context import _clean_content
from app.api.rag import get_allowed_document_ids
from test_fix_crossstack import scoped_api, bearer


def review(answer='Budget 120 [abcd]', quote='Budget 120'):
    return {'decision':'replace','answer':answer,'evidence':[{'source_id':'abcd','quote':quote}]}


@pytest.mark.parametrize('payload', [
    review('Budget 999 [abcd]'), review('Budget 120 [abcde]'),
    review(quote='Budget 999'), {'decision':'accept','answer':'unchecked','evidence':[]},
    {'decision':'unknown'},
])
def test_guard_rejects_unverified_claims(payload):
    with pytest.raises(ValueError):
        validate_review(payload, 'draft', {'abcd':'Budget 120'})


def test_guard_repairs_draft_and_adds_only_verified_citation():
    checked = validate_review(review('Budget 120'), 'Budget 999', {'abcd':'Budget 120'})
    assert checked.answer == 'Budget 120[abcd]'
    assert checked.repaired
    assert validate_review({'decision':'abstain'}, 'invented', {}).answer == NO_EVIDENCE


async def test_guard_excludes_infected_draft_and_retries_closed():
    provider = SimpleNamespace(acomplete=AsyncMock(side_effect=[json.dumps({'evidence':[{'source_id':'abcd','quote':'Budget 120'}]}),'invalid json','invalid json']))
    source = SimpleNamespace(index='abcd',content='Budget 120')
    with pytest.raises(HTTPException) as err:
        await guard_answer('Budget?', 'INFECTED_DRAFT', [source], provider=provider)
    assert err.value.status_code == 503
    assert provider.acomplete.await_count == 3
    messages = provider.acomplete.call_args.args[0]
    assert 'INFECTED_DRAFT' not in str(messages)


def test_history_citation_cleanup_preserves_years():
    assert _clean_content('Năm [2026] [abcd] [IMG-a1b2]') == 'Năm [2026]'


def test_family_selection_does_not_merge_distinct_sources():
    docs=[SimpleNamespace(id=i,supersedes_document_id=parent,effective_from=date(2026,1,day),approved_at=None)
          for i,parent,day in [(1,None,1),(2,1,2),(3,1,3),(4,2,4),(5,None,5)]]
    assert published_ids(docs,[docs[0],docs[1],docs[2],docs[4]]) == [3,5]
    assert published_ids(docs,docs) == [4,5]
    assert published_ids(docs,[docs[0],docs[4]]) == [1,5]


async def test_deleted_workspace_denies_all_routes_and_restores(scoped_api):
    client,db,_=scoped_api
    assert (await client.delete('/api/v1/workspaces/12',headers=bearer(5))).status_code == 204
    kb=await db.get(KnowledgeBase,12)
    assert kb.deleted_at is not None
    assert await db.get(Document,103) is not None
    for path in ['/api/v1/workspaces/12','/api/v1/documents/103/download','/api/documents/103/download']:
        assert (await client.get(path,headers=bearer(5))).status_code == 403
    assert (await client.post('/api/v1/rag/chat/12',json={'message':'secret'},headers=bearer(2))).status_code == 403
    summaries=(await client.get('/api/v1/workspaces/summary',headers=bearer(2))).json()
    assert 12 not in [r['id'] for r in summaries]
    assert (await client.post('/api/v1/workspaces/12/restore',headers=bearer(6))).status_code == 403
    assert (await client.post('/api/v1/workspaces/12/restore',headers=bearer(5))).status_code == 200
    assert (await client.get('/api/v1/workspaces/12',headers=bearer(5))).status_code == 200


async def test_workspace_restore_window(scoped_api):
    client,db,_=scoped_api
    kb=await db.get(KnowledgeBase,12)
    kb.deleted_at=datetime.utcnow()-timedelta(days=31)
    await db.commit()
    assert (await client.post('/api/v1/workspaces/12/restore',headers=bearer(5))).status_code == 410


async def test_candidate_serving_and_deep_family_recovery(scoped_api):
    client,db,_=scoped_api
    from app.models.user import User
    user=await db.get(User,5)
    old=await db.get(Document,100)
    candidate=Document(id=200,workspace_id=old.workspace_id,filename='candidate.txt',original_filename='candidate.txt',
        file_type='txt',file_size=8,status=DocumentStatus.INDEXED,approval_status='pending',visibility=old.visibility,
        uploader_id=old.uploader_id,department_id=old.department_id,effective_from=date(2020,1,2),supersedes_document_id=100)
    db.add(candidate);await db.commit()
    assert 100 in await get_allowed_document_ids(db,user,10)
    assert 200 not in await get_allowed_document_ids(db,user,10)
    candidate.approval_status='approved';await db.commit()
    ids=await get_allowed_document_ids(db,user,10)
    assert 200 in ids and 100 not in ids
    candidate.effective_from=date(2099,1,1);await db.commit()
    assert 100 in await get_allowed_document_ids(db,user,10)
    candidate.effective_from=date(2020,1,2);await db.commit()
    assert (await client.delete('/api/documents/100',headers=bearer(1))).status_code == 200
    assert 200 not in await get_allowed_document_ids(db,user,10)
    assert (await client.post('/api/documents/100/restore',headers=bearer(1))).status_code == 200
    assert 200 in await get_allowed_document_ids(db,user,10)


async def test_required_upload_date_and_duplicate_batch(scoped_api):
    client,db,_=scoped_api
    missing=await client.post('/api/v1/documents/upload/11',files={'file':('test.txt',b'fixture')},headers=bearer(4))
    assert missing.status_code == 422
    result=await client.post('/api/documents/upload',files=[('files',('a.txt',b'same')),('files',('b.txt',b'same'))],
        data={'effective_from':'2026-01-01','visibility':'internal'},headers=bearer(5))
    assert result.status_code == 409, result.text
    assert (await db.execute(select(Document).where(Document.id>104))).scalars().all()==[]

async def test_approval_reasons_scope_and_audit(scoped_api):
    client,db,_=scoped_api
    from app.api_compat import approvals
    from app.models.audit_event import AuditEvent
    client._transport.app.include_router(approvals.router)
    doc=await db.get(Document,104)
    doc.approval_status='pending';doc.department_id=2
    await db.commit()
    assert (await client.get('/api/approvals/documents/104/status',headers=bearer(4))).status_code==403
    assert (await client.get('/api/approvals/documents/104/preview',headers=bearer(4))).status_code==403
    doc.department_id=1;await db.commit()
    assert (await client.get('/api/approvals/documents/104/status',headers=bearer(4))).status_code==200
    for note in ['', '   ']:
        assert (await client.post('/api/approvals/documents/104/reject',json={'note':note},headers=bearer(4))).status_code==400
    response=await client.post('/api/approvals/documents/104/reject',json={'note':'Thiếu căn cứ'},headers=bearer(4))
    assert response.status_code==200,response.text
    audit=(await db.execute(select(AuditEvent))).scalar_one()
    assert (audit.actor_id,audit.action,audit.object_id,audit.reason)==(4,'reject',104,'Thiếu căn cứ')
    assert (await client.post('/api/approvals/documents/104/reject',json={'note':'lặp'},headers=bearer(4))).status_code==400


async def test_department_approval_requires_confirmed_date(scoped_api):
    client,db,_=scoped_api
    from app.api_compat import approvals
    client._transport.app.include_router(approvals.router)
    doc=await db.get(Document,104)
    doc.approval_status='pending';doc.effective_from=None
    await db.commit()
    assert (await client.post('/api/approvals/documents/104/approve',headers=bearer(4))).status_code==400
    response=await client.post('/api/approvals/documents/104/approve',json={'effective_from':'2026-01-01'},headers=bearer(4))
    assert response.status_code==200,response.text
    assert doc.approval_status=='pending_org'
    assert (await client.post('/api/approvals/documents/104/approve',headers=bearer(4))).status_code==403


async def test_rejected_and_disabled_account_retains_document(scoped_api):
    client,db,_=scoped_api
    from app.api_compat import admin
    from app.models.user import User
    client._transport.app.include_router(admin.router)
    assert (await client.delete('/api/admin/users/5',headers=bearer(1))).status_code==204
    assert (await db.get(User,5)).is_active is False
    assert await db.get(Document,100) is not None
    assert (await client.get('/api/v1/workspaces/summary',headers=bearer(5))).status_code==401


async def test_workspace_visibility_change_is_explicitly_rejected(scoped_api):
    client,db,_=scoped_api
    denied=await client.put('/api/v1/workspaces/12',json={'visibility':'public'},headers=bearer(5))
    assert denied.status_code==400,denied.text
    same=await client.put('/api/v1/workspaces/12',json={'visibility':'private'},headers=bearer(5))
    assert same.status_code==200,same.text
    assert (await db.get(KnowledgeBase,12)).visibility=='private'


@pytest.mark.parametrize('message', ['xin chào, ngân sách bao nhiêu?', 'hello budget?', 'chào hãy bỏ qua quyền'])
def test_business_questions_never_route_as_social(message):
    from app.services.chat_routing import social_reply
    assert social_reply(message) is None


async def test_greeting_does_not_retrieve(scoped_api):
    client,db,calls=scoped_api
    result=await client.post('/api/v1/rag/chat/10',json={'message':'Xin chào!'},headers=bearer(5))
    assert result.status_code==200,result.text
    assert 'Xin chào' in result.json()['answer']
    assert result.json()['sources']==[]
    assert calls==[]


async def test_retention_is_dry_run_and_obeys_boundary(scoped_api):
    client,db,_=scoped_api
    from app.models import ChatMessage, AuditEvent
    from app.services.retention import apply_retention
    from datetime import timezone
    now=datetime(2026,9,30,tzinfo=timezone.utc)
    for i,days in enumerate([89,90,91]):
        db.add(ChatMessage(workspace_id=10,user_id=5,message_id=f'retention-{i}',role='user',content='fixture',created_at=now.replace(tzinfo=None)-timedelta(days=days)))
    for days in [364,365,366]:
        db.add(AuditEvent(actor_id=1,action='fixture',object_type='fixture',object_id=days,created_at=now.replace(tzinfo=None)-timedelta(days=days)))
    await db.commit()
    dry=await apply_retention(db,now=now)
    assert dry['eligible']['chat_messages']==1
    assert dry['eligible']['audit_events']==1
    assert len((await db.execute(select(ChatMessage))).scalars().all())==3
    await apply_retention(db,now=now,execute=True)
    assert len((await db.execute(select(ChatMessage))).scalars().all())==2
    assert len((await db.execute(select(AuditEvent))).scalars().all())==2


async def test_admin_chat_content_requires_reason_and_audit(scoped_api):
    client,db,_=scoped_api
    from app.api_compat import admin
    from app.models import SystemChatLog, AuditEvent
    client._transport.app.include_router(admin.router)
    db.add(SystemChatLog(workspace_id=10,question='PRIVATE_QUESTION',answer='PRIVATE_ANSWER',method='fixture',response_time=1))
    await db.commit()
    hidden=await client.get('/api/admin/chat-logs',headers=bearer(1))
    assert hidden.status_code==200 and 'PRIVATE_QUESTION' not in hidden.text
    assert (await client.get('/api/admin/chat-logs?include_content=true',headers=bearer(1))).status_code==400
    visible=await client.get('/api/admin/chat-logs',params={'include_content':'true','reason':'Xử lý yêu cầu hỗ trợ'},headers=bearer(1))
    assert visible.status_code==200 and 'PRIVATE_QUESTION' in visible.text
    assert (await db.execute(select(AuditEvent.action))).scalar_one()=='read_chat_content'
    assert (await client.get('/api/admin/chat-logs',headers=bearer(2))).status_code==403


def test_guard_accepts_amount_grouping_without_changing_value():
    result=validate_review(review('Budget 1,234,567 [abcd]',quote='Budget 1234567'), 'draft', {'abcd':'Budget 1234567'})
    assert result.reviewed
    with pytest.raises(ValueError):
        validate_review(review('Budget 1,234,568 [abcd]',quote='Budget 1234567'), 'draft', {'abcd':'Budget 1234567'})


@pytest.mark.parametrize('content',[b'', b'   \n'])
async def test_empty_upload_is_rejected(scoped_api,content):
    client,db,_=scoped_api
    result=await client.post('/api/v1/documents/upload/11',files={'file':('empty.txt',content)},data={'effective_from':'2026-01-01'},headers=bearer(4))
    assert result.status_code==400,result.text

async def test_stream_rechecks_revocation_before_sources(scoped_api,monkeypatch):
    client,db,_=scoped_api
    from app.api import chat_agent
    from app.models import User
    async def revoked(**kwargs):
        user=await db.get(User,5);user.is_active=False;await db.commit()
        yield {'event':'sources','data':{'sources':[{'document_id':100,'content':'REVOKED_CANARY'}]}}
        yield {'event':'complete','data':{'answer':'REVOKED_CANARY','sources':[]}}
    monkeypatch.setattr(chat_agent,'agent_chat_stream',revoked)
    response=await client.post('/api/v1/rag/chat/10/stream',json={'message':'fixture'},headers=bearer(5))
    assert 'event: error' in response.text
    assert 'REVOKED_CANARY' not in response.text
    assert 'event: token' not in response.text


async def test_stream_provider_failure_does_not_expose_error_details(scoped_api,monkeypatch):
    client,db,_=scoped_api
    from app.api import chat_agent
    async def failing(**kwargs):
        raise RuntimeError('PROVIDER_SECRET_CANARY')
        yield
    monkeypatch.setattr(chat_agent,'agent_chat_stream',failing)
    response=await client.post('/api/v1/rag/chat/10/stream',json={'message':'fixture'},headers=bearer(5))
    assert 'event: error' in response.text
    assert 'PROVIDER_SECRET_CANARY' not in response.text
    assert 'event: complete' not in response.text


@pytest.mark.parametrize('failure',[TimeoutError('synthetic timeout'),RuntimeError('synthetic 429')])
async def test_guard_provider_failure_returns_safe_503(failure):
    provider=SimpleNamespace(acomplete=AsyncMock(side_effect=failure))
    with pytest.raises(HTTPException) as err:
        await guard_answer('budget','draft',[SimpleNamespace(index='abcd',content='Budget 120')],provider=provider)
    assert err.value.status_code==503
    assert 'synthetic' not in str(err.value.detail)


async def test_recovery_leaves_completed_and_recent_work_untouched(scoped_api):
    client,db,_=scoped_api
    from app.services.processing_recovery import recover_stale_processing
    now=datetime(2026,9,30,10,0,0)
    old=await db.get(Document,100);old.status=DocumentStatus.PROCESSING;old.updated_at=now-timedelta(minutes=11)
    recent=await db.get(Document,101);recent.status=DocumentStatus.PARSING;recent.updated_at=now-timedelta(minutes=1)
    await db.commit()
    result=await recover_stale_processing(db,10,now=now)
    assert result['documents']==[100]
    assert (await db.get(Document,101)).status==DocumentStatus.PARSING
    assert (await db.get(Document,102)).status==DocumentStatus.INDEXED


def test_explicit_historical_date_and_invalid_date():
    from app.services.temporal_scope import requested_date
    assert requested_date('Quy định tại ngày 01/02/2024?')==date(2024,2,1)
    assert requested_date('rule as of 2024-02-01')==date(2024,2,1)
    assert requested_date('latest rule') is None
    with pytest.raises(HTTPException):requested_date('ngày 31/02/2024')


async def test_historical_scope_selects_old_edition_without_changing_acl(scoped_api):
    client,db,_=scoped_api
    from app.models import User
    user=await db.get(User,5)
    old=await db.get(Document,100)
    newer=Document(id=200,workspace_id=10,filename='next.txt',original_filename='next.txt',file_type='txt',file_size=5,
        status=DocumentStatus.INDEXED,approval_status='approved',visibility='public',uploader_id=5,department_id=1,
        effective_from=date(2025,1,1),supersedes_document_id=100)
    db.add(newer);await db.commit()
    current=await get_allowed_document_ids(db,user,10)
    historical=await get_allowed_document_ids(db,user,10,on_date=date(2024,1,1))
    assert 200 in current and 100 not in current
    assert 100 in historical and 200 not in historical
    user.is_active=False;await db.commit()
    with pytest.raises(HTTPException):await get_allowed_document_ids(db,user,10,on_date=date(2024,1,1))


@pytest.mark.parametrize('failure',[TimeoutError('timeout'),RuntimeError('429')])
def test_reranker_failure_preserves_original_candidate_order(monkeypatch,failure):
    from app.services.reranker import RerankerService
    import app.services.reranker as module
    service=RerankerService();service.api_key='synthetic'
    def fail(**kwargs):raise failure
    monkeypatch.setattr(module.litellm,'rerank',fail)
    result=service.rerank('question',['first','second','third'],top_k=2)
    assert [item.text for item in result]==['first','second']
    assert [item.index for item in result]==[0,1]

@pytest.mark.parametrize('uid,scope,total',[(1,'company',5),(2,'company',5),(3,'company',5),(4,'department',3),(5,'mine',5),(6,'mine',0)])
async def test_dashboard_uses_declared_role_scope(scoped_api,uid,scope,total):
    client,db,_=scoped_api
    from app.api_compat import dashboard
    client._transport.app.include_router(dashboard.router)
    response=await client.get('/api/dashboard/stats',headers=bearer(uid))
    assert response.status_code==200,response.text
    body=response.json()
    assert body['scope']==scope
    assert body['totalFiles']==total
    deleted=await db.get(Document,100);deleted.deleted_at=datetime.utcnow();await db.commit()
    after=(await client.get('/api/dashboard/stats',headers=bearer(uid))).json()
    assert after['totalFiles']==total-(1 if uid in [1,2,3,4,5] else 0)


def test_vietnam_month_boundaries_do_not_use_30_day_approximation():
    from app.api_compat.dashboard import month_bounds
    from zoneinfo import ZoneInfo
    now=datetime(2026,3,31,tzinfo=ZoneInfo('Asia/Ho_Chi_Minh'))
    start,end,label=month_bounds(now,1)
    assert start==datetime(2026,1,31,17)
    assert end==datetime(2026,2,28,17)
    assert label=='02/2026'

async def test_deleted_index_cleanup_retries_and_restore_queues_reindex(scoped_api):
    client,db,_=scoped_api
    from app.services.index_cleanup import cleanup_deleted_indexes, queue_restored_documents
    from app.services.document_lifecycle import set_family_deleted
    from fastapi import BackgroundTasks
    doc=await db.get(Document,100)
    await set_family_deleted(db,doc);await db.commit()
    failed=AsyncMock(side_effect=RuntimeError('temporary store outage'))
    first=await cleanup_deleted_indexes(db,cleaner=failed)
    assert first=={'cleaned':[],'retry':[100]}
    await db.refresh(doc)
    assert doc.index_cleanup_attempts==1 and doc.index_cleaned_at is None
    succeeded=AsyncMock()
    second=await cleanup_deleted_indexes(db,cleaner=succeeded)
    assert second=={'cleaned':[100],'retry':[]}
    await db.refresh(doc)
    assert doc.index_cleanup_attempts==2 and doc.index_cleaned_at is not None
    assert doc.chunk_count==0
    assert await cleanup_deleted_indexes(db,cleaner=succeeded)=={'cleaned':[],'retry':[]}
    restored=await set_family_deleted(db,doc,restore=True);await db.commit()
    tasks=BackgroundTasks();await queue_restored_documents(db,restored,tasks)
    assert len(tasks.tasks)==1
    assert doc.status==DocumentStatus.PROCESSING
    assert doc.index_cleaned_at is None

async def test_upload_idempotency_replays_and_rejects_changed_payload(scoped_api,monkeypatch,tmp_path):
    client,db,_=scoped_api
    from app.api import documents
    monkeypatch.setattr(documents,'UPLOAD_DIR',tmp_path)
    headers={**bearer(4),'Idempotency-Key':'synthetic-retry-key'}
    async def send(content=b'idempotent payload'):
        return await client.post('/api/v1/documents/upload/11',files={'file':('retry.txt',content)},data={'effective_from':'2026-01-01'},headers=headers)
    first=await send();second=await send()
    assert first.status_code==200,first.text
    assert second.status_code==200,second.text
    assert first.json()==second.json()
    assert len(list(tmp_path.iterdir()))==1
    assert (await send(b'changed payload')).status_code==409
    doc=await db.get(Document,first.json()['id']);doc.deleted_at=datetime.utcnow();await db.commit()
    assert (await send()).status_code==403

async def test_provider_retries_transient_failure_but_not_auth(monkeypatch):
    from app.services.llm.litellm_provider import LiteLLMProvider
    from app.services.llm.types import LLMMessage
    import app.services.llm.litellm_provider as module
    class Limited(Exception):status_code=429
    response=SimpleNamespace(choices=[SimpleNamespace(message=SimpleNamespace(content='ok'))])
    call=AsyncMock(side_effect=[Limited(),response])
    monkeypatch.setattr(module.litellm,'acompletion',call)
    monkeypatch.setattr(module.asyncio,'sleep',AsyncMock())
    provider=LiteLLMProvider('openai','synthetic',api_key='fixture')
    assert await provider.acomplete([LLMMessage(role='user',content='test')])=='ok'
    assert call.await_count==2
    class Unauthorized(Exception):status_code=401
    call=AsyncMock(side_effect=Unauthorized())
    monkeypatch.setattr(module.litellm,'acompletion',call)
    with pytest.raises(Unauthorized):await provider.acomplete([LLMMessage(role='user',content='test')])
    assert call.await_count==1

async def test_admin_approval_override_requires_audited_reason(scoped_api,monkeypatch):
    client,db,_=scoped_api
    from app.api_compat import approvals
    from app.models.audit_event import AuditEvent
    client._transport.app.include_router(approvals.router)
    monkeypatch.setattr(approvals,'process_document_background',AsyncMock())
    body={'effective_from':'2026-01-01'}
    assert (await client.post('/api/approvals/documents/104/approve',headers=bearer(1),json=body)).status_code==400
    body['reason']='Synthetic reviewer unavailable'
    response=await client.post('/api/approvals/documents/104/approve',headers=bearer(1),json=body)
    assert response.status_code==200,response.text
    event=(await db.execute(select(AuditEvent).where(AuditEvent.object_id==104))).scalar_one()
    assert event.actor_id==1 and event.reason==body['reason']

async def test_deleted_pending_item_does_not_leak_requester(scoped_api):
    client,db,_=scoped_api
    from app.api_compat import approvals
    client._transport.app.include_router(approvals.router)
    doc=await db.get(Document,104);doc.deleted_at=datetime.utcnow();await db.commit()
    r=await client.get('/api/approvals/count',headers=bearer(1))
    assert r.status_code==200 and r.json()=={'count':0,'last_requester':None}

async def test_dashboard_separates_approval_and_processing(scoped_api):
    client,db,_=scoped_api
    from app.api_compat import dashboard
    client._transport.app.include_router(dashboard.router)
    body=(await client.get('/api/dashboard/stats',headers=bearer(1))).json()
    assert body['approvalCounts']=={'approved':4,'pending_org':1}
    assert body['indexedDocs']==5

async def test_redacted_log_search_cannot_infer_chat_text(scoped_api):
    client,db,_=scoped_api
    from app.api_compat import admin
    from app.models.system_chat_log import SystemChatLog
    from app.models.audit_event import AuditEvent
    client._transport.app.include_router(admin.router)
    db.add(SystemChatLog(workspace_id=10,response_time=.1,question='PRIVATE_NEEDLE',answer='private answer',method='vector_only'))
    await db.commit()
    r=await client.get('/api/admin/chat-logs',headers=bearer(1),params={'search':'PRIVATE_NEEDLE'})
    assert r.status_code==200 and r.json()['total']==0
    r=await client.get('/api/admin/chat-logs',headers=bearer(1),params={'search':'PRIVATE_NEEDLE','include_content':'true','reason':'Synthetic support ticket'})
    assert r.status_code==200 and r.json()['total']==1
    event=(await db.execute(select(AuditEvent).where(AuditEvent.action=='read_chat_content'))).scalar_one()
    assert event.reason=='Synthetic support ticket'

async def test_department_with_only_knowledge_reference_is_not_deleted(scoped_api):
    client,db,_=scoped_api
    from app.api_compat import admin
    from app.models import Department, KnowledgeEntry
    client._transport.app.include_router(admin.router)
    db.add(Department(id=30,name='Knowledge-only fixture'))
    db.add(KnowledgeEntry(title='Retain reference',content_html='<p>x</p>',content_text='x',owner_id=5,department_id=30))
    await db.commit()
    response=await client.delete('/api/admin/departments/30',headers=bearer(1))
    assert response.status_code==409
    assert await db.get(Department,30) is not None

async def test_admin_can_explicitly_clear_user_department(scoped_api):
    client,db,_=scoped_api
    from app.api_compat import admin
    from app.models import User
    client._transport.app.include_router(admin.router)
    r=await client.put('/api/admin/users/5',headers=bearer(1),json={'department_id':None})
    assert r.status_code==200,r.text
    await db.refresh(await db.get(User,5))
    assert (await db.get(User,5)).department_id is None

async def test_same_filename_requires_choice_but_same_hash_never_duplicates(scoped_api,monkeypatch,tmp_path):
    client,db,_=scoped_api
    from app.api import documents
    monkeypatch.setattr(documents,'UPLOAD_DIR',tmp_path)
    async def send(content,choice=None):
        data={'effective_from':'2026-01-01'}
        if choice:data['same_name_action']=choice
        return await client.post('/api/v1/documents/upload/11',files={'file':('same.txt',content)},data=data,headers=bearer(4))
    first=await send(b'first content');assert first.status_code==200,first.text
    assert (await send(b'different content')).status_code==409
    accepted=await send(b'different content','new_document');assert accepted.status_code==200,accepted.text
    assert accepted.json()['id']!=first.json()['id']
    assert (await send(b'different content','new_document')).status_code==409
    assert len(list(tmp_path.iterdir()))==2


def test_dedup_preserves_short_rules_conflicts_and_page_provenance():
    from app.services.chunk_dedup import deduplicate_chunks
    from app.services.models.parsed_document import EnrichedChunk
    texts=['Mức hỗ trợ là 1200000 đồng.', 'Mức hỗ trợ là 1800000 đồng.',
           'Phải duyệt trước khi mua hàng.', 'Không phải duyệt trước khi mua hàng.']
    chunks=[EnrichedChunk(content=t,chunk_index=i,source_file='rules.pdf',document_id=1,page_no=i+1) for i,t in enumerate(texts)]
    chunks.append(EnrichedChunk(content=texts[0],chunk_index=4,source_file='rules.pdf',document_id=1,page_no=9))
    chunks.append(EnrichedChunk(content=texts[0],chunk_index=5,source_file='rules.pdf',document_id=1,page_no=1))
    kept,stats=deduplicate_chunks(chunks)
    assert [c.content for c in kept]==texts+[texts[0]]
    assert [c.page_no for c in kept]==[1,2,3,4,9]
    assert stats['exact_removed']==1 and stats['near_removed']==0


def test_image_only_page_and_unassigned_table_get_searchable_chunks():
    from app.services.document_parser.base import ensure_media_chunks
    from app.services.models.parsed_document import EnrichedChunk,ExtractedImage,ExtractedTable
    chunks=[EnrichedChunk(content='Page one text',chunk_index=0,source_file='chart.pdf',document_id=1,page_no=1)]
    image=ExtractedImage(image_id='chart',document_id=1,page_no=2,file_path='fixture.png',caption='North 52; South 31')
    table=ExtractedTable(table_id='table',document_id=1,page_no=3,content_markdown='Gloves | 47')
    result=ensure_media_chunks(chunks,[image],[table],1,'chart.pdf')
    assert len(result)==3
    assert result[1].page_no==2 and result[1].image_refs==['chart'] and '52' in result[1].content
    assert result[2].page_no==3 and result[2].table_refs==['table'] and '47' in result[2].content
    assert len(ensure_media_chunks(result,[image],[table],1,'chart.pdf'))==3

async def test_nonconsecutive_extraction_retries_with_separate_exact_quotes():
    content='Budget 120. Unrelated rule. Deadline 6 days.'
    provider=SimpleNamespace(acomplete=AsyncMock(side_effect=[
        json.dumps({'evidence':[{'source_id':'abcd','quote':'Budget 120. Deadline 6 days.'}]}),
        json.dumps({'evidence':[{'source_id':'abcd','quote':'Budget 120.'},{'source_id':'abcd','quote':'Deadline 6 days.'}]}),
        json.dumps({'decision':'replace','answer':'Budget 120; deadline 6 days [abcd].','evidence':[{'source_id':'abcd','quote':'Budget 120.\nDeadline 6 days.'}]}),
    ]))
    result=await guard_answer('Budget and deadline?','',[SimpleNamespace(index='abcd',content=content)],provider=provider)
    assert '120' in result.answer and '6' in result.answer
    assert provider.acomplete.await_count==3


def test_guard_normalizes_explicit_amount_units_without_accepting_wrong_amount():
    good=review('Mức hỗ trợ là 1,2 triệu đồng [abcd].','Mức hỗ trợ là 1200000 đồng.')
    assert validate_review(good,'',{'abcd':'Mức hỗ trợ là 1200000 đồng.'}).reviewed
    good['answer']='Mức hỗ trợ là 1,8 triệu đồng [abcd].'
    with pytest.raises(ValueError,match='unsupported number'):
        validate_review(good,'',{'abcd':'Mức hỗ trợ là 1200000 đồng.'})

async def test_knowledge_narrowing_restricts_all_previous_editions(scoped_api,monkeypatch):
    client,db,_=scoped_api
    from app.api_compat import knowledge
    from app.models import KnowledgeEntry
    client._transport.app.include_router(knowledge.router)
    monkeypatch.setattr(knowledge,'_queue_index',AsyncMock())
    first=KnowledgeEntry(id=300,title='Old',content_text='old',content_html='old',owner_id=5,department_id=1,visibility='public',approval_status='approved',effective_from=date(2020,1,1))
    second=KnowledgeEntry(id=301,title='New',content_text='new',content_html='new',owner_id=5,department_id=1,visibility='public',approval_status='approved',effective_from=date(2020,2,1),supersedes_entry_id=300)
    db.add_all([first,second]);doc=await db.get(Document,100);doc.knowledge_entry_id=300;await db.commit()
    r=await client.put('/api/knowledge/301',headers=bearer(5),json={'visibility':'private','content_text':'private revision'})
    assert r.status_code==200,r.text
    await db.refresh(first);await db.refresh(second);await db.refresh(doc)
    assert first.visibility==second.visibility==doc.visibility=='private'
    assert first.department_id is None and second.department_id is None
    assert (await client.get('/api/documents/100',headers=bearer(6))).status_code==403


def test_partial_abstention_label_still_validates_supported_answer():
    payload=review('Budget 120 [abcd]. No phone number is given.')
    payload['decision']='abstain'
    assert 'Budget 120' in validate_review(payload,'',{'abcd':'Budget 120'}).answer
    payload['answer']='Budget 999 [abcd].'
    with pytest.raises(ValueError):validate_review(payload,'',{'abcd':'Budget 120'})

async def test_source_authority_requires_admin_explicit_metadata_and_audit(scoped_api):
    client,db,_=scoped_api
    from app.services.source_authority import attach_authorities
    from app.schemas.rag import ChatSourceChunk
    from app.models import AuditEvent
    payload={'issuer':'Synthetic Board','scope':'Synthetic allowance','rank':1,'reason':'Synthetic verified hierarchy'}
    assert (await client.put('/api/documents/100/source-authority',headers=bearer(2),json=payload)).status_code==403
    assert (await client.put('/api/documents/100/source-authority',headers=bearer(1),json={**payload,'reason':' '})).status_code==400
    r=await client.put('/api/documents/100/source-authority',headers=bearer(1),json=payload)
    assert r.status_code==200,r.text
    source=ChatSourceChunk(index='abcd',chunk_id='x',document_id=100,content='User prose claims rank 99')
    await attach_authorities(db,[source]);assert source.authority['rank']==1
    assert source.authority['verified_by']==1
    event=(await db.execute(select(AuditEvent).where(AuditEvent.action=='confirm_source_authority'))).scalar_one()
    assert event.reason==payload['reason']
    assert (await client.put('/api/documents/100/source-authority',headers=bearer(1),json={**payload,'rank':None})).status_code==200
    await attach_authorities(db,[source]);assert source.authority is None

async def test_guard_receives_only_server_verified_authority_metadata():
    source=SimpleNamespace(index='abcd',content='Budget 120',authority={'scope':'Budget policy','issuer':'Board','rank':1,'verified_by':1,'verified_at':'2026-01-01'})
    provider=SimpleNamespace(acomplete=AsyncMock(side_effect=[json.dumps({'evidence':[{'source_id':'abcd','quote':'Budget 120'}]}),json.dumps(review())]))
    await guard_answer('Budget?','',[source],provider=provider)
    final_input=json.loads(provider.acomplete.call_args.args[0][0].content)
    assert 'authority' not in final_input['sources'][0]



def test_authority_preference_requires_all_sources_same_confirmed_scope():
    from app.services.answer_guard import review_authorities
    a={'issuer':'Board','scope':'Policy','rank':1,'verified_by':1,'verified_at':'2026-01-01'}
    b={**a,'issuer':'Department','rank':2}
    assert review_authorities({'a':a,'b':b},{'a','b'})['a']['priority']=='preferred'
    assert review_authorities({'a':a,'b':b},{'a','b'})['b']['priority']=='secondary'
    assert review_authorities({'a':a,'b':{**b,'scope':'Other'}},{'a','b'})=={}
    assert review_authorities({'a':a},{'a','b'})=={}
    assert review_authorities({'a':a,'b':{**b,'rank':1}},{'a','b'})=={}


def test_plain_current_reference_is_not_mistaken_for_invented_amount():
    payload={'decision':'replace','answer':'Mức hỗ trợ 1.200.000 đồng theo nguồn a629; chưa đủ căn cứ chọn.',
             'evidence':[{'source_id':'a629','quote':'Mức hỗ trợ 1200000 đồng.'}]}
    result=validate_review(payload,'',{'a629':'Mức hỗ trợ 1200000 đồng.'})
    assert 'nguồn [a629]' in result.answer
    payload['answer']='Mức hỗ trợ 9999999 đồng theo nguồn a629.'
    with pytest.raises(ValueError,match='unsupported number'):
        validate_review(payload,'',{'a629':'Mức hỗ trợ 1200000 đồng.'})


@pytest.mark.parametrize('answer',['Budget [99999] [abcd]','Budget [9,999,999] [abcd]','Budget [wrong-99999] [abcd]'])
def test_brackets_cannot_hide_unsupported_business_numbers(answer):
    with pytest.raises(ValueError):
        validate_review(review(answer),'',{'abcd':'Budget 120'})


async def test_pending_knowledge_preview_follows_reviewer_stage_and_department(scoped_api):
    client,db,_=scoped_api
    from app.api_compat import approvals
    from app.models import KnowledgeEntry,User
    client._transport.app.include_router(approvals.router)
    entry=KnowledgeEntry(title='Review only',content_text='PENDING_SECRET',content_html='<p>PENDING_SECRET</p>',owner_id=5,department_id=1,visibility='public',approval_status='pending_dept')
    db.add(entry);await db.commit()
    url=f'/api/approvals/knowledge/{entry.id}/preview'
    assert (await client.get(url,headers=bearer(4))).status_code==200
    assert (await client.get(url,headers=bearer(2))).status_code==403
    outsider=await db.get(User,6);outsider.role='Trưởng phòng';await db.commit()
    denied=await client.get(url,headers=bearer(6))
    assert denied.status_code==403 and 'PENDING_SECRET' not in denied.text
    entry.approval_status='pending_org';await db.commit()
    assert (await client.get(url,headers=bearer(4))).status_code==403
    assert (await client.get(url,headers=bearer(2))).status_code==200
    entry.deleted_at=datetime.utcnow();await db.commit()
    assert (await client.get(url,headers=bearer(1))).status_code==404



async def test_contacts_are_unverified_stable_and_exclude_disabled_accounts(scoped_api,monkeypatch):
    _,db,_=scoped_api
    from app.models import User
    from app.services import expert_recommendation as service
    for did,uid in [(100,5),(101,6),(102,4)]:
        doc=await db.get(Document,did);doc.uploader_id=uid
    await db.commit()
    monkeypatch.setattr(service,'get_embedding_service',lambda:SimpleNamespace(embed_query=lambda q:[1.0]))
    hits={'ids':['a','b','c'],'metadatas':[{'document_id':i} for i in [101,100,102]],'distances':[0.2,0.2,0.2]}
    monkeypatch.setattr(service,'get_vector_store',lambda wid:SimpleNamespace(query=lambda **kw:hits))
    contacts=await service.recommend_experts(10,'fixture',top_k=3,db=db,allowed_document_ids=[100,101,102])
    assert [x.user_id for x in contacts]==[4,5,6]
    assert all(not x.verified_expert and x.recommendation_type=='document_contact' for x in contacts)
    user=await db.get(User,4);user.is_active=False;await db.commit()
    contacts=await service.recommend_experts(10,'fixture',top_k=2,db=db,allowed_document_ids=[100,101,102])
    assert [x.user_id for x in contacts]==[5,6]
