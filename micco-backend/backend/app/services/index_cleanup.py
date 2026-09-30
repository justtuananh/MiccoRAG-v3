"""Retryable index cleanup; tombstones deny access before this worker runs."""
import asyncio
import logging
from datetime import datetime
from sqlalchemy import select, or_, update
from app.models import Document, KnowledgeBase
from app.models.document import DocumentStatus
logger=logging.getLogger(__name__)


async def delete_index_data(workspace_id, document_id):
    from app.services.vector_store import get_vector_store
    from app.services.knowledge_graph_service import KnowledgeGraphService
    store=get_vector_store(workspace_id)
    await asyncio.to_thread(store.delete_by_document_id,document_id)
    remaining=await asyncio.to_thread(store.collection.get,where={'document_id':document_id},include=[])
    if remaining.get('ids'):
        raise RuntimeError('Vector cleanup incomplete')
    kg=KnowledgeGraphService(workspace_id)
    rag=await kg._get_rag()
    await rag.adelete_by_doc_id(str(document_id))
    if await rag.full_docs.get_by_id(str(document_id)):
        raise RuntimeError('Graph cleanup incomplete')


async def cleanup_deleted_indexes(db, *, cleaner=delete_index_data, limit=10):
    ids=list((await db.execute(select(Document.id).join(KnowledgeBase).where(
        or_(Document.deleted_at.is_not(None),KnowledgeBase.deleted_at.is_not(None)),
        Document.index_cleaned_at.is_(None),
    ).order_by(Document.id).limit(limit))).scalars().all())
    result={'cleaned':[],'retry':[]}
    for did in ids:
        doc=(await db.execute(select(Document).join(KnowledgeBase).where(
            Document.id==did,or_(Document.deleted_at.is_not(None),KnowledgeBase.deleted_at.is_not(None)),
            Document.index_cleaned_at.is_(None),
        ).with_for_update(of=Document,skip_locked=True))).scalar_one_or_none()
        if doc is None:continue
        wid=doc.workspace_id
        try:
            await cleaner(wid,did)
            doc.index_cleaned_at=datetime.utcnow();doc.index_cleanup_attempts+=1
            doc.index_cleanup_error=None;doc.chunk_count=0;doc.status=DocumentStatus.PENDING
            await db.commit();result['cleaned'].append(did)
        except Exception as error:
            await db.rollback()
            await db.execute(update(Document).where(Document.id==did).values(
                index_cleanup_attempts=Document.index_cleanup_attempts+1,
                index_cleanup_error=type(error).__name__,status=DocumentStatus.PENDING,
            ))
            await db.commit();result['retry'].append(did)
    return result


async def queue_restored_documents(db, documents, tasks):
    from app.api.documents import process_document_background, UPLOAD_DIR
    for doc in documents:
        doc.index_cleaned_at=None
        kb=await db.get(KnowledgeBase,doc.workspace_id)
        if (kb and kb.deleted_at is None and doc.deleted_at is None and doc.approval_status=='approved'
                and doc.effective_from is not None and doc.status!=DocumentStatus.INDEXED):
            doc.status=DocumentStatus.PROCESSING
            tasks.add_task(process_document_background,doc.id,str(UPLOAD_DIR/doc.filename),doc.workspace_id)
    await db.commit()


async def maintenance_loop():
    from app.core.database import async_session_maker
    from app.core.config import settings
    from app.services.processing_recovery import recover_stale_processing
    while True:
        try:
            async with async_session_maker() as db:
                await recover_stale_processing(db,settings.NEXUSRAG_PROCESSING_TIMEOUT_MINUTES)
                await cleanup_deleted_indexes(db)
        except Exception as error:
            logger.warning('Index maintenance will retry: %s',type(error).__name__)
        await asyncio.sleep(60)
