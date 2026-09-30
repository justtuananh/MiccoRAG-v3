"""Explicit, unscheduled hard purge of expired trash. Dry-run by default.

Only call this after an isolated restore rehearsal and index maintenance. Files are
removed before the database commit so a failed unlink leaves tombstones retryable.
If the database commit then fails, missing files are tolerated on the next run.
"""
from __future__ import annotations

from datetime import datetime, timedelta, timezone
from pathlib import Path

from sqlalchemy import select

from app.core.config import settings
from app.models import (
    AuditEvent, ChatMessage, Document, DocumentImage, DocumentVersion,
    KnowledgeBase, KnowledgeEntry, SystemChatLog,
)
from app.services.document_lifecycle import family_root


def _naive_utc(value: datetime) -> datetime:
    return value.astimezone(timezone.utc).replace(tzinfo=None) if value.tzinfo else value


def _expired(value: datetime | None, cutoff: datetime) -> bool:
    return value is not None and _naive_utc(value) <= cutoff


def _owned_upload(root: Path, name: str) -> Path:
    if not name or Path(name).name != name or name in {'.', '..'}:
        raise ValueError('Unsafe upload filename')
    path = root / name
    if path.is_symlink() or path.resolve().parent != root.resolve():
        raise ValueError('Unsafe upload path')
    return path


def _owned_image(root: Path, workspace_id: int, raw: str) -> Path:
    path = Path(raw)
    if not path.is_absolute() or '..' in path.parts:
        raise ValueError('Image path must be absolute')
    expected = [root / parser / f'kb_{workspace_id}' / 'images'
                for parser in ('docling', 'marker')]
    if (path.is_symlink() or not any(path.parent == folder and
            folder.resolve().is_relative_to(root) for folder in expected)):
        raise ValueError('Unsafe image path')
    return path


async def purge_expired_trash(
    db, *, now: datetime | None = None, execute: bool = False,
    upload_root: Path | None = None, image_root: Path | None = None,
    limit: int = 20, actor_id: int = 0,
) -> dict:
    """Purge complete expired families/KBs only after every index is cleaned.

    A candidate with an unsafe path, active descendant, surviving chat/log, or
    uncleaned index is skipped. No scheduler invokes this function.
    """
    if limit < 1:
        raise ValueError('limit must be positive')
    cutoff = _naive_utc(now or datetime.now(timezone.utc)) - timedelta(days=30)
    uploads = Path(upload_root or settings.BASE_DIR / 'uploads').resolve()
    images_root = Path(image_root or settings.BASE_DIR / 'data').resolve()
    kbs = list((await db.execute(select(KnowledgeBase).order_by(KnowledgeBase.id)
                 .with_for_update())).scalars().all())
    docs = list((await db.execute(select(Document).order_by(Document.id)
                  .with_for_update())).scalars().all())
    versions = list((await db.execute(select(DocumentVersion))).scalars().all())
    images = list((await db.execute(select(DocumentImage))).scalars().all())
    entries = list((await db.execute(select(KnowledgeEntry))).scalars().all())
    chats = list((await db.execute(select(ChatMessage.workspace_id))).scalars().all())
    logs = list((await db.execute(select(SystemChatLog.workspace_id))).scalars().all())
    by_kb = {kb.id: kb for kb in kbs}
    by_doc = {doc.id: doc for doc in docs}
    selected_kbs: set[int] = set()
    selected_docs: set[int] = set()
    skipped: dict[str, str] = {}

    # A whole KB is one unit. Preserve chat/log history rather than allowing
    # database ON DELETE CASCADE to erase it before its own retention window.
    for kb in kbs:
        if not _expired(kb.deleted_at, cutoff) or len(selected_kbs) >= limit:
            continue
        members = [d for d in docs if d.workspace_id == kb.id]
        if kb.id in chats or kb.id in logs:
            skipped[f'kb:{kb.id}'] = 'history-retained'
        elif any(d.index_cleaned_at is None for d in members):
            skipped[f'kb:{kb.id}'] = 'index-not-cleaned'
        else:
            selected_kbs.add(kb.id)
            selected_docs.update(d.id for d in members)

    # For a live KB, a version family must be wholly tombstoned and expired.
    for kb in kbs:
        if kb.id in selected_kbs or kb.deleted_at is not None:
            continue
        members = [d for d in docs if d.workspace_id == kb.id]
        by_id = {d.id: d for d in members}
        families: dict[int | None, list[Document]] = {}
        for doc in members:
            families.setdefault(family_root(doc, by_id), []).append(doc)
        for root_id, family in families.items():
            if root_id is None or not any(_expired(d.deleted_at, cutoff) for d in family):
                continue
            if len(selected_docs) >= limit:
                break
            if any(not _expired(d.deleted_at, cutoff) for d in family):
                skipped[f'family:{kb.id}:{root_id}'] = 'active-or-unexpired-version'
            elif any(d.index_cleaned_at is None for d in family):
                skipped[f'family:{kb.id}:{root_id}'] = 'index-not-cleaned'
            else:
                selected_docs.update(d.id for d in family)

    entries_by_id = {entry.id: entry for entry in entries}
    for wid in {d.workspace_id for d in docs if d.id in selected_docs}:
        if wid in selected_kbs:
            continue
        projected = [d for d in docs if d.workspace_id == wid and d.id in selected_docs
                     and d.knowledge_entry_id is not None]
        if any(not _expired(entries_by_id[d.knowledge_entry_id].deleted_at, cutoff)
               and all(other.id in selected_docs for other in docs
                       if other.knowledge_entry_id == d.knowledge_entry_id)
               for d in projected if d.knowledge_entry_id in entries_by_id):
            selected_docs.difference_update(d.id for d in docs if d.workspace_id == wid)
            skipped[f'kb:{wid}'] = 'active-knowledge-projection'

    # Pruning one workspace can make its document versions survivors. Repeat
    # until no remaining candidate would detach a surviving replacement link.
    while True:
        surviving_docs = {d.id for d in docs if d.id not in selected_docs}
        removed_versions = {v.id for v in versions if v.document_id in selected_docs}
        blocked_workspaces = {by_doc[d.supersedes_document_id].workspace_id
            for d in docs if d.id in surviving_docs
            and d.supersedes_document_id in selected_docs}
        blocked_workspaces.update(by_doc[v.document_ref_id].workspace_id
            for v in versions if v.document_id in surviving_docs
            and v.document_ref_id in selected_docs)
        version_by_id = {v.id: v for v in versions}
        blocked_workspaces.update(by_doc[version_by_id[v.supersedes_version_id].document_id].workspace_id
            for v in versions if v.document_id in surviving_docs
            and v.supersedes_version_id in removed_versions)
        newly_blocked = {wid for wid in blocked_workspaces
                         if any(d.id in selected_docs and d.workspace_id == wid for d in docs)}
        if not newly_blocked:
            break
        for wid in newly_blocked:
            selected_docs.difference_update(d.id for d in docs if d.workspace_id == wid)
            selected_kbs.discard(wid)
            skipped[f'kb:{wid}'] = 'surviving-version-reference'
    for kid in tuple(selected_kbs):
        if any(d.workspace_id == kid and d.id not in selected_docs for d in docs):
            selected_kbs.discard(kid)
            skipped[f'kb:{kid}'] = 'surviving-document'

    # Files referenced by any surviving row are shared and stay in place.
    surviving_names = {d.filename for d in docs if d.id not in selected_docs}
    surviving_names.update(v.filename for v in versions if v.document_id not in selected_docs)
    surviving_thumbnails = {d.thumbnail for d in docs
                            if d.id not in selected_docs and d.thumbnail}
    surviving_images = {i.file_path for i in images if i.document_id not in selected_docs}
    paths: set[Path] = set()
    try:
        for doc in docs:
            if doc.id in selected_docs and doc.filename not in surviving_names:
                paths.add(_owned_upload(uploads, doc.filename))
        for version in versions:
            if version.document_id in selected_docs and version.filename not in surviving_names:
                paths.add(_owned_upload(uploads, version.filename))
        for doc in docs:
            if doc.id in selected_docs and doc.thumbnail and doc.thumbnail not in surviving_thumbnails:
                paths.add(_owned_upload(uploads / 'thumbnails', doc.thumbnail))
        for item in images:
            if item.document_id in selected_docs and item.file_path not in surviving_images:
                paths.add(_owned_image(images_root, by_doc[item.document_id].workspace_id, item.file_path))
    except ValueError:
        # Fail closed for the whole run; no partial file removal or DB write.
        raise

    entry_ids = {e.id for e in entries
                 if all(d.id in selected_docs for d in docs if d.knowledge_entry_id == e.id)
                 and (_expired(e.deleted_at, cutoff) or
                      (any(d.knowledge_entry_id == e.id for d in docs) and
                       all(d.workspace_id in selected_kbs for d in docs
                           if d.knowledge_entry_id == e.id)))}
    # Never sever the edition chain of a surviving knowledge entry.
    while True:
        retained_parents = {e.supersedes_entry_id for e in entries if e.id not in entry_ids}
        safe_ids = entry_ids - retained_parents
        if safe_ids == entry_ids:
            break
        entry_ids = safe_ids
    result = {'execute': execute, 'cutoff': cutoff.isoformat(),
              'workspace_ids': sorted(selected_kbs), 'document_ids': sorted(selected_docs),
              'knowledge_entry_ids': sorted(entry_ids), 'file_count': len(paths),
              'skipped': skipped}
    if not execute or not (selected_kbs or selected_docs or entry_ids):
        return result

    # Preflight paths and unlink before DB deletion. Expired tombstones make a
    # missing file safe to retry; an unlink exception leaves DB rows intact.
    for path in sorted(paths):
        if path.is_symlink():
            raise ValueError('Unsafe symlink during purge')
        path.unlink(missing_ok=True)
    try:
        for doc in docs:
            if doc.id in selected_docs:
                await db.delete(doc)  # ORM cascades image/table/version rows.
        await db.flush()
        for entry in entries:
            if entry.id in entry_ids:
                await db.delete(entry)
        for kb in kbs:
            if kb.id in selected_kbs:
                await db.delete(kb)
        db.add(AuditEvent(actor_id=actor_id, action='purge_expired_trash',
                          object_type='trash', object_id=0,
                          reason=f"KB={len(selected_kbs)} documents={len(selected_docs)} knowledge={len(entry_ids)}"))
        await db.commit()
    except Exception:
        await db.rollback()
        raise
    return result
