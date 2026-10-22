"""Version families use explicit replacement links, never upload-name heuristics."""
from datetime import datetime
from sqlalchemy import select
from app.models.document import Document
from app.core.time_utils import utc_naive


def family_root(doc, by_id):
    seen = set()
    while getattr(doc, 'supersedes_document_id', None) in by_id:
        if doc.id in seen:
            return None  # Invalid cycle is never published.
        seen.add(doc.id)
        doc = by_id[doc.supersedes_document_id]
    return doc.id


async def version_family_root(db, doc):
    """Resolve a version URL to the immutable root document ID."""
    seen = set()
    while doc.supersedes_document_id is not None:
        if doc.id in seen:
            raise ValueError('Invalid version lineage')
        seen.add(doc.id)
        parent = await db.get(Document, doc.supersedes_document_id)
        if parent is None or parent.workspace_id != doc.workspace_id:
            raise ValueError('Invalid version lineage')
        doc = parent
    return doc.id


def published_ids(documents, eligible):
    by_id = {doc.id: doc for doc in documents}
    families = {}
    for doc in eligible:
        root = family_root(doc, by_id)
        if root is None:
            continue
        # Only versions explicitly in one family compete. Distinct sources
        # remain visible even when their contents contradict one another.
        rank = (doc.effective_from, utc_naive(getattr(doc, 'approved_at', None)) or datetime.min, doc.id)
        if root not in families or rank > families[root][0]:
            families[root] = (rank, doc.id)
    chosen = {entry[1] for entry in families.values()}
    return [doc.id for doc in documents if doc.id in chosen]


async def set_family_deleted(db, doc, *, restore=False):
    documents = list((await db.execute(select(Document).where(
        Document.workspace_id == doc.workspace_id).with_for_update())).scalars().all())
    by_id = {item.id: item for item in documents}
    root = family_root(doc, by_id)
    if root is None:
        raise ValueError('Invalid version lineage')
    stamp = doc.deleted_at if restore else datetime.utcnow()
    restored = []
    if restore:
        from app.services.text_duplicate import text_fingerprint, verified_text_only
        prospective = [item for item in documents if family_root(item, by_id) == root and item.deleted_at == stamp]
        live_hashes = {item.content_hash for item in documents
                       if item.deleted_at is None and family_root(item, by_id) != root and item.content_hash}
        if any(item.content_hash in live_hashes for item in prospective if item.content_hash):
            raise ValueError('Duplicate content on restore')
        live_text = {item.text_fingerprint or text_fingerprint(item.markdown_content or '')
                     for item in documents if item.deleted_at is None
                     and family_root(item, by_id) != root and verified_text_only(item)}
        if any((item.text_fingerprint or text_fingerprint(item.markdown_content or '')) in live_text
               for item in prospective if verified_text_only(item)
               and (item.text_fingerprint or item.markdown_content)):
            raise ValueError('Duplicate content on restore')
    for item in documents:
        if family_root(item, by_id) != root:
            continue
        # Restore only rows removed by this operation, not earlier deletions.
        if restore and item.deleted_at == stamp:
            item.deleted_at = None
            item.index_cleaned_at = None
            restored.append(item)
        elif not restore and item.deleted_at is None:
            item.deleted_at = stamp

    return restored
