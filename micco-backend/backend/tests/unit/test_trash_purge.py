"""Isolated trash-purge fixtures; no live paths or scheduler."""
from datetime import datetime, timedelta

import pytest
from sqlalchemy import select

from app.models import AuditEvent, Document, DocumentImage, DocumentVersion, KnowledgeBase, KnowledgeEntry
from app.services.trash_purge import purge_expired_trash
from test_fix_crossstack import scoped_api


def aged(days):
    return datetime(2026, 9, 30, 12) - timedelta(days=days)


async def test_dry_run_boundary_family_shared_file_and_audit(scoped_api, tmp_path):
    _, db, _ = scoped_api
    uploads = tmp_path / 'uploads'; uploads.mkdir()
    (uploads / 'thumbnails').mkdir()
    data = tmp_path / 'data'; data.mkdir()
    old = await db.get(Document, 100)
    old.deleted_at = aged(30)
    old.index_cleaned_at = aged(29)
    old.filename = 'shared.txt'; old.thumbnail = 'thumb.png'
    current = await db.get(Document, 101)
    current.filename = 'shared.txt'
    newer = Document(id=201, workspace_id=10, filename='newer.txt', original_filename='newer.txt',
                     file_type='txt', file_size=3, uploader_id=5, supersedes_document_id=100,
                     deleted_at=aged(31), index_cleaned_at=aged(29))
    db.add(newer)
    await db.commit()
    (uploads / 'shared.txt').write_text('shared')
    (uploads / 'newer.txt').write_text('old version')
    (uploads / 'thumbnails' / 'thumb.png').write_bytes(b'thumb')
    args = dict(now=aged(0), upload_root=uploads, image_root=data)
    before = await purge_expired_trash(db, **args)
    assert before['document_ids'] == [100, 201]
    assert (uploads / 'newer.txt').exists()
    assert await db.get(Document, 100) is not None
    done = await purge_expired_trash(db, execute=True, **args)
    assert done['document_ids'] == [100, 201]
    assert await db.get(Document, 100) is None
    assert await db.get(Document, 201) is None
    assert await db.get(Document, 101) is not None
    assert (uploads / 'shared.txt').exists()
    assert not (uploads / 'newer.txt').exists()
    assert not (uploads / 'thumbnails' / 'thumb.png').exists()
    events = list((await db.execute(select(AuditEvent).where(
        AuditEvent.action == 'purge_expired_trash'))).scalars().all())
    assert len(events) == 1 and 'documents=2' in events[0].reason


async def test_unexpired_or_uncleaned_family_is_retained(scoped_api, tmp_path):
    _, db, _ = scoped_api
    uploads = tmp_path / 'uploads'; uploads.mkdir()
    data = tmp_path / 'data'; data.mkdir()
    old = await db.get(Document, 100)
    old.deleted_at = aged(31); old.index_cleaned_at = aged(29)
    new = Document(id=202, workspace_id=10, filename='202.txt', original_filename='202.txt',
                   file_type='txt', file_size=3, uploader_id=5, supersedes_document_id=100,
                   deleted_at=aged(29), index_cleaned_at=aged(29))
    db.add(new); await db.commit()
    args = dict(now=aged(0), upload_root=uploads, image_root=data)
    result = await purge_expired_trash(db, execute=True, **args)
    assert result['document_ids'] == []
    new.deleted_at = aged(31); new.index_cleaned_at = None
    await db.commit()
    result = await purge_expired_trash(db, execute=True, **args)
    assert result['document_ids'] == []
    new.index_cleaned_at = aged(29)
    await db.commit()
    assert (await purge_expired_trash(db, execute=True, **args))['document_ids'] == [100, 202]


async def test_expired_unprojected_knowledge_is_purged_but_recent_is_kept(scoped_api, tmp_path):
    _, db, _ = scoped_api
    uploads = tmp_path / 'uploads'; uploads.mkdir()
    data = tmp_path / 'data'; data.mkdir()
    db.add_all([
        KnowledgeEntry(id=310, owner_id=5, title='Old rejected', content_html='x',
                       content_text='x', deleted_at=aged(31)),
        KnowledgeEntry(id=311, owner_id=5, title='Recent rejected', content_html='y',
                       content_text='y', deleted_at=aged(29)),
    ])
    await db.commit()
    result = await purge_expired_trash(db, now=aged(0), execute=True,
                                       upload_root=uploads, image_root=data)
    assert result['knowledge_entry_ids'] == [310]
    assert await db.get(KnowledgeEntry, 310) is None
    assert await db.get(KnowledgeEntry, 311) is not None


async def test_surviving_version_reference_blocks_purge(scoped_api, tmp_path):
    _, db, _ = scoped_api
    uploads = tmp_path / 'uploads'; uploads.mkdir()
    data = tmp_path / 'data'; data.mkdir()
    old = await db.get(Document, 100)
    old.deleted_at = aged(31); old.index_cleaned_at = aged(29)
    live_version = DocumentVersion(document_id=101, document_ref_id=100,
                                   version_number=1, filename='101.txt')
    db.add(live_version); await db.commit()
    args = dict(now=aged(0), execute=True, upload_root=uploads, image_root=data)
    result = await purge_expired_trash(db, **args)
    assert 100 not in result['document_ids']
    assert await db.get(Document, 100) is not None
    live_version.document_ref_id = None
    await db.commit()
    assert (await purge_expired_trash(db, **args))['document_ids'] == [100]


async def test_deleted_kb_removes_owned_versions_images_and_knowledge(scoped_api, tmp_path):
    _, db, _ = scoped_api
    uploads = tmp_path / 'uploads'; uploads.mkdir()
    data = tmp_path / 'data'; image_dir = data / 'docling' / 'kb_12' / 'images'
    image_dir.mkdir(parents=True)
    kb = await db.get(KnowledgeBase, 12); kb.deleted_at = aged(31)
    for did in (102, 103):
        doc = await db.get(Document, did); doc.index_cleaned_at = aged(29)
        (uploads / doc.filename).write_text(str(did))
    entry = KnowledgeEntry(id=300, owner_id=5, title='Fixture', content_html='x',
                           content_text='x', deleted_at=aged(31))
    db.add(entry)
    doc = await db.get(Document, 102); doc.knowledge_entry_id = 300
    db.add(DocumentVersion(document_id=102, version_number=1, filename='version.txt'))
    db.add(DocumentImage(document_id=102, image_id='image-fixture',
                         file_path=str(image_dir / 'image.png')))
    (uploads / 'version.txt').write_text('version')
    (image_dir / 'image.png').write_bytes(b'picture')
    await db.commit()
    result = await purge_expired_trash(db, now=aged(0), execute=True,
                                       upload_root=uploads, image_root=data)
    assert result['workspace_ids'] == [12]
    assert result['document_ids'] == [102, 103]
    assert result['knowledge_entry_ids'] == [300]
    assert await db.get(KnowledgeBase, 12) is None
    assert await db.get(KnowledgeEntry, 300) is None
    assert not (uploads / 'version.txt').exists()
    assert not (image_dir / 'image.png').exists()
    assert await db.get(KnowledgeBase, 10) is not None


async def test_unsafe_path_fails_closed_and_unlink_failure_is_retryable(scoped_api, tmp_path, monkeypatch):
    _, db, _ = scoped_api
    uploads = tmp_path / 'uploads'; uploads.mkdir()
    data = tmp_path / 'data'; data.mkdir()
    doc = await db.get(Document, 100)
    doc.deleted_at = aged(31); doc.index_cleaned_at = aged(29)
    doc.filename = '../outside.txt'
    await db.commit()
    args = dict(now=aged(0), execute=True, upload_root=uploads, image_root=data)
    with pytest.raises(ValueError, match='Unsafe upload'):
        await purge_expired_trash(db, **args)
    assert await db.get(Document, 100) is not None
    doc.filename = 'safe.txt'; await db.commit()
    path = uploads / 'safe.txt'; path.write_text('fixture')
    original = type(path).unlink
    def fail_once(self, *a, **kw):
        if self == path:
            raise OSError('fixture unlink failure')
        return original(self, *a, **kw)
    monkeypatch.setattr(type(path), 'unlink', fail_once)
    with pytest.raises(OSError, match='fixture unlink failure'):
        await purge_expired_trash(db, **args)
    assert await db.get(Document, 100) is not None
    monkeypatch.setattr(type(path), 'unlink', original)
    assert (await purge_expired_trash(db, **args))['document_ids'] == [100]
    assert await db.get(Document, 100) is None



async def test_retained_knowledge_descendant_preserves_all_ancestors(scoped_api,tmp_path):
    _,db,_=scoped_api
    uploads=tmp_path/'uploads';uploads.mkdir()
    data=tmp_path/'data';data.mkdir()
    for eid,parent,days in [(401,None,31),(402,401,31),(403,402,29)]:
        db.add(KnowledgeEntry(id=eid,title='Synthetic lineage',content_html='<p>Fixture</p>',
                             content_text='Fixture',owner_id=5,visibility='private',
                             supersedes_entry_id=parent,deleted_at=aged(days)))
        await db.flush()
    await db.commit()
    result=await purge_expired_trash(db,now=aged(0),execute=True,upload_root=uploads,image_root=data)
    assert result['knowledge_entry_ids']==[]
    for eid in [401,402,403]:assert await db.get(KnowledgeEntry,eid) is not None


async def test_projection_pruning_preserves_surviving_version_ancestor(scoped_api, tmp_path):
    _, db, _ = scoped_api
    uploads = tmp_path / 'uploads'; uploads.mkdir()
    data = tmp_path / 'data'; data.mkdir()
    old = await db.get(Document, 100)
    survivor = await db.get(Document, 101)
    for doc in (old, survivor):
        doc.deleted_at = aged(31)
        doc.index_cleaned_at = aged(29)
    db.add(KnowledgeEntry(id=410, title='Retained projection', content_html='<p>Fixture</p>',
                          content_text='Fixture', owner_id=5, deleted_at=None))
    survivor.knowledge_entry_id = 410
    ancestor = DocumentVersion(document_id=old.id, version_number=1, filename='100.txt')
    db.add(ancestor)
    await db.flush()
    descendant = DocumentVersion(document_id=survivor.id, version_number=2,
                                 filename='101.txt', supersedes_version_id=ancestor.id)
    db.add(descendant)
    await db.commit()

    result = await purge_expired_trash(db, now=aged(0), execute=True,
                                       upload_root=uploads, image_root=data)
    assert result['document_ids'] == []
    assert result['skipped']['kb:11'] == 'active-knowledge-projection'
    assert result['skipped']['kb:10'] == 'surviving-version-reference'
    assert await db.get(Document, old.id) is not None
    assert await db.get(DocumentVersion, ancestor.id) is not None
    await db.refresh(descendant)
    assert descendant.supersedes_version_id == ancestor.id
