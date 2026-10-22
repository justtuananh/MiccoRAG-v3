"""Recover abandoned ingest states independently of schema auto-creation."""
from datetime import datetime, timedelta
from sqlalchemy import update
from app.models import Document, KnowledgeEntry
from app.models.document import DocumentStatus


async def recover_stale_processing(db, timeout_minutes, *, now=None):
    cutoff=(now or datetime.utcnow())-timedelta(minutes=timeout_minutes)
    result=await db.execute(update(Document).where(
        Document.status.in_([DocumentStatus.PROCESSING,DocumentStatus.PARSING,DocumentStatus.INDEXING]),
        Document.updated_at<cutoff,
    ).values(status=DocumentStatus.FAILED,error_message='Xử lý bị gián đoạn hoặc quá hạn. Có thể thử lại.').returning(Document.id))
    documents=list(result.scalars().all())
    result=await db.execute(update(KnowledgeEntry).where(
        KnowledgeEntry.ingest_status=='processing',KnowledgeEntry.updated_at<cutoff,
    ).values(ingest_status='failed',ingest_error='Xử lý bị gián đoạn hoặc quá hạn. Có thể thử lại.').returning(KnowledgeEntry.id))
    knowledge=list(result.scalars().all())
    await db.commit()
    return {'documents':documents,'knowledge':knowledge}
