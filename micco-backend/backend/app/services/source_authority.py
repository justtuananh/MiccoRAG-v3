"""Authority is explicit reviewed metadata, never inferred from source prose."""
from sqlalchemy import select
from app.models import Document


def authority_metadata(document):
    if (document.authority_verified_by is None or document.authority_verified_at is None
            or document.authority_rank is None or not document.authority_scope or not document.issuer):
        return None
    return {'issuer':document.issuer,'scope':document.authority_scope,'rank':document.authority_rank,
            'verified_by':document.authority_verified_by,'verified_at':document.authority_verified_at.isoformat()}


async def attach_authorities(db, sources, images=()):
    refs=[*sources,*images]
    if not refs:return
    docs=(await db.execute(select(Document).where(Document.id.in_({s.document_id for s in refs})))).scalars().all()
    metadata={d.id:authority_metadata(d) for d in docs}
    for source in refs:source.authority=metadata.get(source.document_id)
