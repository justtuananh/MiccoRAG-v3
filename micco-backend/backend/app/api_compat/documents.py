"""
Documents API — legacy compatibility layer for micco-server frontend.
Provides document CRUD, upload, versioning, thumbnails, and department-based access.
"""
from __future__ import annotations

import os
import uuid
import hashlib
from datetime import date, datetime
import aiofiles
from pathlib import Path
from typing import Annotated
from pydantic import BaseModel

from fastapi import Header, BackgroundTasks, APIRouter, Depends, File, Form, HTTPException, Query, UploadFile
from fastapi.responses import FileResponse
from sqlalchemy import select, func, or_, and_, update
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.core.config import settings
from app.core.permissions import (can_read_all_knowledge, can_read_document, require_workspace_read, require_document_write)
from app.core.deps import get_db
from app.core.security import get_current_user
from app.models.user import User
from app.models.department import Department
from app.models.knowledge_base import KnowledgeBase
from app.models.document import Document, DocumentStatus
from app.models.document_version import DocumentVersion
from docx import Document as DocxDocument
from app.schemas.compat import (
    LegacyDocumentVersionResponse,
    ProcessingStatusResponse,
    ProcessingStatusListResponse,
)
from app.api_compat.utils import (
    format_bytes_to_human,
    get_or_create_default_workspace,
    get_or_create_department_workspace,
    get_or_create_user_workspace,
    get_all_department_workspaces,
    map_rag_doc_to_legacy_with_dept,
    workspace_file_path,
)

ORG_APPROVER_ROLES = {"Admin", "Giám đốc", "Phó giám đốc"}
DEPT_APPROVER_ROLES = {"Admin", "Trưởng phòng"}

router = APIRouter(prefix="/api/documents", tags=["Documents"])

UPLOAD_DIR = settings.BASE_DIR / "uploads"
UPLOAD_DIR.mkdir(parents=True, exist_ok=True)

THUMBNAIL_DIR = UPLOAD_DIR / "thumbnails"
THUMBNAIL_DIR.mkdir(parents=True, exist_ok=True)

MAX_FILE_SIZE = 50 * 1024 * 1024  # 50MB
ALLOWED_EXTENSIONS = {".pdf", ".txt", ".md", ".docx", ".pptx"}


class EffectiveDatesUpdate(BaseModel):
    effective_from: date
    effective_until: date | None = None
    reason: str


# ─── Access Control Helpers ────────────────────────────────────────

async def _doc_kb(db: AsyncSession, doc: Document) -> KnowledgeBase:
    kb = (await db.execute(select(KnowledgeBase).where(KnowledgeBase.id == doc.workspace_id))).scalar_one_or_none()
    if kb is None:
        raise HTTPException(status_code=404, detail="Knowledge base not found")
    return kb


async def _check_doc_access(user: User, doc: Document, db: AsyncSession) -> None:
    kb = await _doc_kb(db, doc)
    require_workspace_read(user, kb)
    if not can_read_document(user, doc, kb, allow_owner_pending=True):
        raise HTTPException(status_code=403, detail="Bạn không có quyền truy cập tài liệu này")


async def _can_modify_doc(user: User, doc: Document, db: AsyncSession) -> None:
    kb = await _doc_kb(db, doc)
    require_workspace_read(user, kb)
    if user.role != "Admin" and doc.uploader_id != user.id:
        raise HTTPException(status_code=403, detail="Chỉ người tải lên hoặc Admin mới được sửa tài liệu")


# ─── Document Listing ───────────────────────────────────────────────

@router.get("")
async def list_documents(
    search: str | None = Query(None),
    type_filter: str | None = Query(None, alias="type"),
    category: str | None = Query(None),
    department_id: int | None = Query(None),
    include_deleted: bool = Query(False),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """List documents scoped to the user's department (admins see all)."""
    # NOTE: Documents are now stored per-department workspace (not just default workspace).
    # We list ALL documents (workspace filter removed) and rely on RBAC/department scoping below.

    # Base query with department + uploader joins
    stmt = (
        select(Document, Department.name.label("dept_name"), User.name.label("owner_name"))
        .outerjoin(Department, Document.department_id == Department.id)
        .outerjoin(User, Document.uploader_id == User.id)
    )
    stmt = stmt.where(Document.deleted_at.is_not(None) if include_deleted else Document.deleted_at.is_(None))

    # Department + visibility scoping
    if not can_read_all_knowledge(current_user):
        stmt = stmt.where(
            or_(
                Document.visibility == "public",
                and_(
                    Document.visibility.in_(["internal", "department"]),
                    Document.department_id == current_user.department_id,
                ),
                Document.uploader_id == current_user.id,
            )
        )

    # Filter by selected department (admin only)
    if department_id is not None and can_read_all_knowledge(current_user):
        stmt = stmt.where(Document.department_id == department_id)

    # Filter by approval_status:
    # - Admin: sees approved + rejected (pending handled in approvals tab)
    # - Trưởng phòng: sees approved only
    # - Nhân viên: sees approved + their own pending, but never rejected
    if include_deleted:
        stmt = stmt.where(Document.uploader_id == current_user.id if current_user.role != "Admin" else True)
    elif current_user.role == "Admin":
        stmt = stmt.where(Document.approval_status.notin_(["pending", "pending_org"]))
    elif current_user.role == "Trưởng phòng":
        stmt = stmt.where(Document.approval_status == "approved")
    else:
        stmt = stmt.where(
            or_(
                Document.approval_status == "approved",
                and_(
                    Document.uploader_id == current_user.id,
                    Document.approval_status.in_(["pending", "pending_org"]),
                ),
            )
        )

    # In-memory filters (for simplicity)
    rows = (await db.execute(stmt.order_by(Document.created_at.desc()))).all()
    mapped = []
    for row in rows:
        doc = row[0]
        dept_name = row[1]
        owner_name = row[2]
        mapped.append(map_rag_doc_to_legacy_with_dept(doc, owner_name=owner_name, dept_name=dept_name))

    kb_ids = {row[0].workspace_id for row in rows}
    if kb_ids:
        kb_result = await db.execute(select(KnowledgeBase).where(KnowledgeBase.id.in_(kb_ids)))
        kb_by_id = {kb.id: kb for kb in kb_result.scalars().all()}
        mapped = [item for item, row in zip(mapped, rows)
                  if (kb := kb_by_id.get(row[0].workspace_id)) is not None
                  and (current_user.role == "Admin" or (include_deleted and row[0].uploader_id == current_user.id)
                       or can_read_document(current_user, row[0], kb, allow_owner_pending=True))]

    # Apply search
    if search:
        s = search.lower()
        mapped = [d for d in mapped if s in d["name"].lower()]

    # Apply type filter
    if type_filter and type_filter != "All":
        mapped = [d for d in mapped if d["type"] == type_filter.upper()]

    # Apply category filter
    if category and category != "All":
        mapped = [d for d in mapped if d.get("category") == category]

    return mapped


# ─── Upload Documents ──────────────────────────────────────────────

@router.post("/upload")
async def upload_documents(
    files: list[UploadFile] = File(...),
    tags: str | None = Form(None),
    category: str | None = Form(None),
    visibility: str | None = Form("internal"),
    department_id: int | None = Form(None),
    idempotency_key: str | None = Header(None, max_length=128),
    same_name_action: str | None = Form(None),
    effective_from: date = Form(...),
    effective_until: date | None = Form(None),
    thumbnail: UploadFile | None = File(None),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """
    Upload one or more files.
    Admins/Trưởng phòng get auto-approved; regular users need approval.

    Workspace routing:
    - Tài liệu cá nhân (personal/private) → workspace cá nhân của uploader
    - Tài liệu nội bộ → workspace của phòng ban tác giả
    - Tài liệu công khai → workspace của phòng ban tác giả (sẽ được replicate khi approve)
    Nếu user không có phòng ban → fallback về default workspace.
    """
    if not files:
        raise HTTPException(status_code=400, detail="Chưa chọn tài liệu")
    if effective_until and effective_until < effective_from:
        raise HTTPException(status_code=400, detail="Ngày hết hiệu lực không hợp lệ")

    requested_visibility = (visibility or "internal").lower()
    effective_visibility = (
        "private" if requested_visibility in ("personal", "private")
        else requested_visibility if requested_visibility in ("internal", "public", "department")
        else "internal"
    )
    # Department choice is privileged. The user's own department is authoritative
    # for every ordinary upload, including directors whose all-KB privilege is read-only.
    effective_dept_id = (
        department_id if current_user.role == "Admin" and department_id is not None
        else current_user.department_id
    )
    if effective_visibility == "private":
        effective_dept_id = None

    is_org_approver = current_user.role in ORG_APPROVER_ROLES
    is_dept_approver = current_user.role in DEPT_APPROVER_ROLES
    if effective_visibility == "private":
        doc_approval_status = "approved"
    elif effective_visibility == "public":
        doc_approval_status = (
            "approved" if is_org_approver else "pending_org" if is_dept_approver else "pending"
        )
    else:
        doc_approval_status = "approved" if (current_user.role == "Admin" or is_dept_approver) else "pending"

    # Validate the entire batch before creating a workspace, DB record, or file.
    prepared: list[tuple[UploadFile, bytes, str]] = []
    for upload in files:
        ext = Path(upload.filename or "file").suffix.lower()
        if ext not in ALLOWED_EXTENSIONS:
            raise HTTPException(status_code=400, detail=f"Định dạng file không được hỗ trợ: {ext}")
        content = await upload.read(MAX_FILE_SIZE + 1)
        if len(content) > MAX_FILE_SIZE:
            raise HTTPException(status_code=400, detail=f"File {upload.filename} vượt quá giới hạn 50MB")
        if not content or (ext in {".txt", ".md"} and not content.strip()):
            raise HTTPException(status_code=400, detail="Tệp rỗng hoặc không có nội dung")
        prepared.append((upload, content, ext))

    thumb_content = None
    thumb_ext = None
    if thumbnail:
        thumb_ext = Path(thumbnail.filename or "file").suffix.lower()
        if thumb_ext not in {".png", ".jpg", ".jpeg", ".webp"}:
            raise HTTPException(status_code=400, detail="Định dạng thumbnail không được hỗ trợ")
        thumb_content = await thumbnail.read(MAX_FILE_SIZE + 1)
        if len(thumb_content) > MAX_FILE_SIZE:
            raise HTTPException(status_code=400, detail="Thumbnail vượt quá giới hạn 50MB")

    written_paths: list[Path] = []
    created_docs: list[tuple[Document, Path]] = []
    try:
        if effective_visibility == "private":
            workspace = await get_or_create_user_workspace(db, current_user.id, commit=False)
        elif effective_visibility == "public":
            workspace = await get_or_create_default_workspace(db, commit=False)
        elif effective_dept_id is not None:
            workspace = await get_or_create_department_workspace(db, effective_dept_id, commit=False)
        else:
            workspace = await get_or_create_default_workspace(db, commit=False)
        require_workspace_read(current_user, workspace)
        from app.services.upload_idempotency import replay_upload, record_upload, lock_upload_hashes, require_filename_choice
        payload = {"same_name_action":same_name_action,"files":[(item.filename,hashlib.sha256(content).hexdigest()) for item,content,_ in prepared],
            "workspace_id":workspace.id,"visibility":effective_visibility,"department_id":effective_dept_id,
            "effective_from":effective_from,"effective_until":effective_until,"tags":tags,"category":category,
            "thumbnail":hashlib.sha256(thumb_content).hexdigest() if thumb_content else None}
        replay = await replay_upload(db,current_user,"legacy-upload",idempotency_key,payload)
        if replay is not None:
            return replay
        await lock_upload_hashes(db,workspace.id,[hashlib.sha256(content).hexdigest() for _,content,_ in prepared])
        existing_hashes = set((await db.execute(select(Document.content_hash).where(
            Document.workspace_id == workspace.id, Document.deleted_at.is_(None),
            Document.content_hash.is_not(None),
        ))).scalars().all())
        batch_hashes = set()
        for _, content, _ in prepared:
            digest = hashlib.sha256(content).hexdigest()
            if digest in existing_hashes or digest in batch_hashes:
                raise HTTPException(status_code=409, detail="Nội dung trùng trong cùng kho tri thức")
            batch_hashes.add(digest)

        await require_filename_choice(db,workspace.id,[item.filename for item,_,_ in prepared],same_name_action)

        dept_name = None
        if effective_dept_id is not None:
            dept_name = (await db.execute(
                select(Department.name).where(Department.id == effective_dept_id)
            )).scalar_one_or_none()

        thumb_name = None
        if thumb_content is not None:
            thumb_name = f"{uuid.uuid4().hex}{thumb_ext}"
            thumb_path = THUMBNAIL_DIR / thumb_name
            written_paths.append(thumb_path)
            async with aiofiles.open(thumb_path, "wb") as out:
                await out.write(thumb_content)

        for upload, content, ext in prepared:
            stored_name = f"{uuid.uuid4().hex}{ext}"
            file_path = UPLOAD_DIR / stored_name
            written_paths.append(file_path)
            async with aiofiles.open(file_path, "wb") as out:
                await out.write(content)
            doc = Document(
                workspace_id=workspace.id,
                filename=stored_name,
                original_filename=upload.filename,
                file_type=ext[1:],
                file_size=len(content),
                status=(DocumentStatus.PROCESSING if doc_approval_status == "approved"
                        else DocumentStatus.PENDING),
                uploader_id=current_user.id,
                department_id=effective_dept_id,
                visibility=effective_visibility,
                approval_status=doc_approval_status,
                effective_from=effective_from,
                effective_until=effective_until,
                content_hash=hashlib.sha256(content).hexdigest(),
                approved_by=current_user.id if doc_approval_status == "approved" else None,
                approved_at=datetime.utcnow() if doc_approval_status == "approved" else None,
                category=category,
                tags=tags,
                thumbnail=thumb_name,
            )
            db.add(doc)
            await db.flush()
            db.add(DocumentVersion(
                document_id=doc.id, version_number=1, version_label="V 1.0",
                filename=stored_name, original_filename=upload.filename,
                file_size=len(content), change_note="Phiên bản gốc",
                created_by=current_user.id, is_current=True,
                approval_status=doc_approval_status,
                processing_status="processing" if doc_approval_status == "approved" else "pending",
                effective_from=effective_from,
                effective_until=effective_until,
                approved_by=current_user.id if doc_approval_status == "approved" else None,
                approved_at=datetime.utcnow() if doc_approval_status == "approved" else None,
            ))
            created_docs.append((doc, file_path))

        await db.flush()
        response = [map_rag_doc_to_legacy_with_dept(
            doc, owner_name=current_user.name, dept_name=dept_name
        ) for doc, _ in created_docs]
        record_upload(db,current_user,"legacy-upload",idempotency_key,payload,response)
        await db.commit()
    except Exception:
        await db.rollback()
        for path in written_paths:
            path.unlink(missing_ok=True)
        raise

    # Start processing only after every file and DB record has committed.
    if doc_approval_status == "approved":
        import asyncio
        from app.api.documents import process_document_background
        for doc, file_path in created_docs:
            asyncio.get_event_loop().create_task(
                process_document_background(doc.id, str(file_path), workspace.id)
            )
    return response


# ─── Processing Status ────────────────────────────────────

@router.get("/processing-status", response_model=ProcessingStatusListResponse)
async def get_processing_status(
    filter: str = Query("all", description="Filter group: all | processing | indexed | failed"),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """
    Get documents by processing status group.
    - `all`        → pending / parsing / processing / indexing (active only)
    - `processing` → same as `all`
    - `indexed`    → completed (INDEXED)
    - `failed`     → failed (FAILED)

    Always returns `counts` with totals for all groups (for tab badges).

    NOTE: this route MUST be defined BEFORE /{doc_id} routes to prevent
    FastAPI from trying to parse "processing-status" as an integer.
    """
    from app.schemas.compat import StatusCounts
    from sqlalchemy import case

    # ── Determine which statuses to fetch ────────────────────────
    ACTIVE_STATUSES = ["PENDING", "PARSING", "PROCESSING", "INDEXING"]

    if filter in ("all", "processing"):
        fetch_statuses = ACTIVE_STATUSES
    elif filter == "indexed":
        fetch_statuses = ["INDEXED"]
    elif filter == "failed":
        fetch_statuses = ["FAILED"]
    else:
        fetch_statuses = ACTIVE_STATUSES  # fallback

    # ── Base access-scope sub-filter ─────────────────────────────
    if current_user.role in ("Admin", "Trưởng phòng"):
        if current_user.department_id:
            scope_filter = or_(
                Document.uploader_id == current_user.id,
                Document.department_id == current_user.department_id,
            )
        else:
            scope_filter = True  # Admin without dept → see all
    else:
        scope_filter = Document.uploader_id == current_user.id

    # ── Fetch items for requested filter ─────────────────────────
    stmt = (
        select(Document, Department.name.label("dept_name"), User.name.label("uploader_name"))
        .outerjoin(Department, Document.department_id == Department.id)
        .outerjoin(User, Document.uploader_id == User.id)
        .where(
            Document.status.in_(fetch_statuses),
            Document.approval_status != "rejected",
            scope_filter,
        )
        .order_by(Document.created_at.desc())
    )
    result = await db.execute(stmt)
    rows = result.all()
    kb_ids = {doc.workspace_id for doc, _, _ in rows}
    kb_by_id = {}
    if kb_ids:
        kb_rows = await db.execute(select(KnowledgeBase).where(KnowledgeBase.id.in_(kb_ids)))
        kb_by_id = {kb.id: kb for kb in kb_rows.scalars().all()}
    rows = [row for row in rows
            if (kb := kb_by_id.get(row[0].workspace_id)) is not None
            and (current_user.role == "Admin" or
                 can_read_document(current_user, row[0], kb, allow_owner_pending=True))]

    items = [
        ProcessingStatusResponse(
            id=doc.id,
            name=doc.original_filename or doc.filename,
            status=doc.status.value if hasattr(doc.status, "value") else doc.status,
            chunk_count=doc.chunk_count or 0,
            error_message=doc.error_message,
            uploader_name=uploader_name or "Không rõ",
            department_name=dept_name,
            created_at=doc.created_at,
            file_type=doc.file_type,
            file_size=doc.file_size or 0,
        )
        for doc, dept_name, uploader_name in rows
    ]

    # Count only documents through the same KB and document policy as items.
    all_status_rows = (await db.execute(select(Document).where(
        Document.approval_status != "rejected", scope_filter,
    ))).scalars().all()
    missing_kb_ids = {doc.workspace_id for doc in all_status_rows} - set(kb_by_id)
    if missing_kb_ids:
        more = await db.execute(select(KnowledgeBase).where(KnowledgeBase.id.in_(missing_kb_ids)))
        kb_by_id.update({kb.id: kb for kb in more.scalars().all()})
    visible_docs = [doc for doc in all_status_rows
                    if (kb := kb_by_id.get(doc.workspace_id)) is not None
                    and (current_user.role == "Admin" or
                         can_read_document(current_user, doc, kb, allow_owner_pending=True))]
    cnt_processing = sum(doc.status.value.upper() in ACTIVE_STATUSES for doc in visible_docs)
    cnt_indexed = sum(doc.status == DocumentStatus.INDEXED for doc in visible_docs)
    cnt_failed = sum(doc.status == DocumentStatus.FAILED for doc in visible_docs)

    counts = StatusCounts(
        all=cnt_processing,          # "Tất cả" badge = active docs
        processing=cnt_processing,
        indexed=cnt_indexed,
        failed=cnt_failed,
    )

    return ProcessingStatusListResponse(items=items, total=len(items), counts=counts)



# ─── Get Single Document ──────────────────────────────────────────

@router.get("/{doc_id}")
async def get_document(
    doc_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Get a single document by ID with department access check."""
    result = await db.execute(
        select(Document, Department.name.label("dept_name"), User.name.label("owner_name"))
        .outerjoin(Department, Document.department_id == Department.id)
        .outerjoin(User, Document.uploader_id == User.id)
        .where(Document.id == doc_id)
    )
    row = result.one_or_none()
    if not row:
        raise HTTPException(status_code=404, detail="Document not found")

    # Unpack carefully — owner_name may be None if uploader was deleted
    doc = row[0]
    dept_name = row[1]
    owner_name = row[2]

    await _check_doc_access(current_user, doc, db)

    return map_rag_doc_to_legacy_with_dept(doc, owner_name=owner_name, dept_name=dept_name)


# ─── Download Document ────────────────────────────────────────────

@router.get("/{doc_id}/download")
async def download_document(
    doc_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Download the current version of a document."""
    doc = (await db.execute(select(Document).where(Document.id == doc_id))).scalar_one_or_none()
    if not doc:
        raise HTTPException(status_code=404, detail="Document not found")

    await _check_doc_access(current_user, doc, db)

    file_path = UPLOAD_DIR / doc.filename
    if not file_path.exists():
        raise HTTPException(status_code=404, detail="File not found on disk")

    return FileResponse(
        path=str(file_path),
        filename=doc.original_filename or doc.filename,
        media_type="application/octet-stream",
    )


# ─── Preview Text Document ─────────────────────────────────────────

from docx import Document as DocxDocument

@router.get("/{doc_id}/preview")
async def preview_document_text(
    doc_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Preview first few paragraphs/chars of text-based documents (docx, txt, md).
    Respects access controls.
    """
    doc = (await db.execute(select(Document).where(Document.id == doc_id))).scalar_one_or_none()
    if not doc:
        raise HTTPException(status_code=404, detail="Document not found")

    await _check_doc_access(current_user, doc, db)

    file_path = UPLOAD_DIR / doc.filename
    if not file_path.exists():
        raise HTTPException(status_code=404, detail="File not found on disk")

    ext = doc.file_type.lower()
    text_content = ""

    try:
        if ext == "docx":
            d = DocxDocument(str(file_path))
            text_content = "\n".join([p.text for p in d.paragraphs[:30]])
            if len(d.paragraphs) > 30:
                text_content += "\n\n...(Còn tiếp)..."
        elif ext in ("txt", "md"):
            async with aiofiles.open(file_path, mode='r', encoding='utf-8', errors='ignore') as f:
                text_content = await f.read(5000)
                if len(text_content) == 5000:
                    text_content += "\n\n...(Còn tiếp)..."
        else:
            return {"supported": False, "message": "Preview not supported for this type"}

        return {"supported": True, "content": text_content, "file_type": ext}
    except Exception as e:
        import logging
        logging.getLogger(__name__).error(f"Error previewing file {file_path}: {str(e)}")
        return {"supported": False, "message": f"Lỗi rách tệp hoặc mất nội dung: {str(e)}"}


# ─── Document Thumbnail ────────────────────────────────────────────

@router.get("/{doc_id}/thumbnail")
async def get_thumbnail(
    doc_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """
    Serve document thumbnail image.
    Returns 404 if no thumbnail is associated with this document.
    """
    doc = (await db.execute(select(Document).where(Document.id == doc_id))).scalar_one_or_none()
    if not doc:
        raise HTTPException(status_code=404, detail="Document not found")

    await _check_doc_access(current_user, doc, db)

    # Thumbnail is stored in the document record as a path string
    thumb_path_str = getattr(doc, "thumbnail", None) or ""
    if not thumb_path_str:
        raise HTTPException(status_code=404, detail="Thumbnail not found")

    thumb_path = THUMBNAIL_DIR / thumb_path_str
    if not thumb_path.exists():
        raise HTTPException(status_code=404, detail="Thumbnail file not found on disk")

    ext = thumb_path_str.rsplit(".", 1)[-1].lower()
    media_types = {
        "jpg": "image/jpeg",
        "jpeg": "image/jpeg",
        "png": "image/png",
        "gif": "image/gif",
        "webp": "image/webp",
    }
    media_type = media_types.get(ext, "image/jpeg")

    return FileResponse(path=str(thumb_path), media_type=media_type)


# ─── Document Versions ────────────────────────────────────────────

@router.get("/{doc_id}/versions", response_model=list[LegacyDocumentVersionResponse])
async def get_document_versions(
    doc_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """List all versions of a document."""
    doc = (await db.execute(select(Document).where(Document.id == doc_id))).scalar_one_or_none()
    if not doc:
        raise HTTPException(status_code=404, detail="Document not found")

    await _check_doc_access(current_user, doc, db)

    from app.services.document_lifecycle import version_family_root
    try:
        root_id = await version_family_root(db, doc)
    except ValueError:
        raise HTTPException(status_code=409, detail="Dòng phiên bản không hợp lệ")

    versions = (
        await db.execute(
            select(DocumentVersion)
            .options(selectinload(DocumentVersion.creator))
            .where(DocumentVersion.document_id == root_id)
            .order_by(DocumentVersion.version_number.desc())
        )
    ).scalars().all()

    kb = await _doc_kb(db, doc)
    visible = []
    for version in versions:
        target = await db.get(Document, version.document_ref_id) if version.document_ref_id else await db.get(Document, root_id)
        if target and can_read_document(current_user, target, kb, allow_owner_pending=True):
            visible.append(version)
    from app.api.rag import get_allowed_document_ids
    current_ids = set(await get_allowed_document_ids(db, current_user, doc.workspace_id))
    versions = visible

    return [
        LegacyDocumentVersionResponse(
            id=v.id,
            document_id=v.document_id,
            version_number=v.version_number,
            version_label=v.version_label,
            filename=v.filename,
            size=v.size_human,
            change_note=v.change_note,
            created_by_name=v.creator_name,
            is_current=(v.document_ref_id or root_id) in current_ids,
            created_at=v.created_at,
        )
        for v in versions
    ]


@router.post("/{doc_id}/versions", response_model=LegacyDocumentVersionResponse)
async def upload_new_version(
    doc_id: int,
    file: UploadFile = File(...),
    change_note: str | None = Form(None),
    effective_from: date = Form(...),
    effective_until: date | None = Form(None),
    idempotency_key: str | None = Header(None, alias="Idempotency-Key", max_length=128),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """
    Upload a new version of an existing document.
    Creates an independent candidate. The previous approved file stays intact.
    """
    doc = (await db.execute(select(Document).where(Document.id == doc_id))).scalar_one_or_none()
    if not doc:
        raise HTTPException(status_code=404, detail="Document not found")
    if doc.deleted_at is not None:
        raise HTTPException(status_code=410, detail="Tài liệu đã bị xóa")
    if effective_until and effective_until < effective_from:
        raise HTTPException(status_code=400, detail="Ngày hết hiệu lực không hợp lệ")

    await _can_modify_doc(current_user, doc, db)

    from app.services.document_lifecycle import version_family_root
    try:
        root_id = await version_family_root(db, doc)
    except ValueError:
        raise HTTPException(status_code=409, detail="Dòng phiên bản không hợp lệ")
    # Every version request locks the same root before calculating its number.
    root = (await db.execute(select(Document).where(Document.id == root_id).with_for_update())).scalar_one()
    await db.refresh(doc)
    if root.deleted_at is not None or doc.deleted_at is not None:
        raise HTTPException(status_code=410, detail="Tài liệu đã bị xóa")

    # Read file
    content = await file.read(MAX_FILE_SIZE + 1)
    if len(content) > MAX_FILE_SIZE:
        raise HTTPException(
            status_code=400,
            detail=f"File vượt quá giới hạn {MAX_FILE_SIZE // (1024*1024)}MB",
        )

    ext = Path(file.filename or "file").suffix.lower()
    if ext not in ALLOWED_EXTENSIONS:
        raise HTTPException(
            status_code=400,
            detail=f"Định dạng file không được hỗ trợ: {ext}",
        )

    if not content or (ext in {".txt", ".md"} and not content.strip()):
        raise HTTPException(status_code=400, detail="Tệp rỗng hoặc không có nội dung")

    from app.services.upload_idempotency import lock_upload_hashes, replay_upload, record_upload
    digest = hashlib.sha256(content).hexdigest()
    payload = {"document_id": root_id, "parent_document_id": doc_id,
               "filename": file.filename, "hash": digest,
               "change_note": change_note, "effective_from": effective_from,
               "effective_until": effective_until}
    replay = await replay_upload(db, current_user, "legacy-version", idempotency_key, payload)
    if replay is not None:
        return replay["version"]
    await lock_upload_hashes(db,doc.workspace_id,[digest])
    duplicate = (await db.execute(select(Document).where(
        Document.workspace_id == doc.workspace_id, Document.deleted_at.is_(None),
        Document.content_hash == digest,
    ).limit(1))).scalar_one_or_none()
    if duplicate is not None:
        kb = await _doc_kb(db, duplicate)
        detail = "Nội dung phiên bản đã tồn tại trong kho tri thức"
        if can_read_document(current_user, duplicate, kb, allow_owner_pending=True):
            detail += f" (ID: {duplicate.id})"
        raise HTTPException(status_code=409, detail=detail)

    # Save new file
    stored_name = f"{uuid.uuid4().hex}{ext}"
    file_path = UPLOAD_DIR / stored_name
    try:
        async with aiofiles.open(file_path, "wb") as out:
            await out.write(content)

        # Get next version number
        max_ver_row = await db.execute(
            select(func.max(DocumentVersion.version_number)).where(
                DocumentVersion.document_id == root_id
            )
        )
        max_ver = max_ver_row.scalar() or 0
        next_ver = max_ver + 1

        # A candidate gets its own document/vector identity. The approved document
        # stays intact until this candidate is approved, indexed, and effective.
        is_personal_doc = (doc.visibility or "internal") == "private"
        if is_personal_doc or current_user.role == "Admin":
            next_approval = "approved"
        elif (doc.visibility or "internal") == "public":
            next_approval = "approved" if current_user.role in {"Giám đốc", "Phó giám đốc"} else "pending_org" if current_user.role == "Trưởng phòng" else "pending"
        else:
            next_approval = "approved" if current_user.role == "Trưởng phòng" and doc.department_id == current_user.department_id else "pending"
        candidate = Document(
            workspace_id=doc.workspace_id, filename=stored_name, original_filename=file.filename,
            file_type=ext[1:], file_size=len(content),
            status=DocumentStatus.PROCESSING if next_approval == "approved" else DocumentStatus.PENDING,
            uploader_id=current_user.id, department_id=doc.department_id,
            visibility=doc.visibility, approval_status=next_approval,
            effective_from=effective_from, effective_until=effective_until,
            approved_by=current_user.id if next_approval == "approved" else None,
            approved_at=datetime.utcnow() if next_approval == "approved" else None,
            content_hash=hashlib.sha256(content).hexdigest(),
            supersedes_document_id=doc.id, category=doc.category, tags=doc.tags,
        )
        db.add(candidate)
        await db.flush()

        current_version_id = (await db.execute(select(DocumentVersion.id).where(
            DocumentVersion.document_id == root_id,
            DocumentVersion.document_ref_id == doc.id if doc.id != root_id
            else DocumentVersion.document_ref_id.is_(None),
        ).order_by(DocumentVersion.version_number.desc()).limit(1))).scalar_one_or_none()
        new_version = DocumentVersion(
            document_id=root_id,
            version_number=next_ver,
            version_label=f"V {next_ver}.0",
            filename=stored_name,
            original_filename=file.filename,
            file_size=len(content),
            change_note=change_note or f"Phiên bản {next_ver}.0",
            created_by=current_user.id,
            is_current=False,
            approval_status=next_approval,
            processing_status="processing" if next_approval == "approved" else "pending",
            effective_from=effective_from,
            effective_until=effective_until,
            approved_by=current_user.id if next_approval == "approved" else None,
            approved_at=datetime.utcnow() if next_approval == "approved" else None,
            supersedes_version_id=current_version_id,
            document_ref_id=candidate.id,
        )
        db.add(new_version)
        await db.flush()
        response = LegacyDocumentVersionResponse(
            id=new_version.id, document_id=root_id, version_number=next_ver,
            version_label=new_version.version_label, filename=stored_name,
            size=new_version.size_human, change_note=new_version.change_note,
            created_by_name=current_user.name, is_current=False,
            created_at=new_version.created_at,
        )
        record_upload(db, current_user, "legacy-version", idempotency_key, payload,
                      {"id": candidate.id, "version": response})

        await db.commit()
    except Exception:
        await db.rollback()
        file_path.unlink(missing_ok=True)
        raise

    await db.refresh(new_version)

    if next_approval == "approved":
        import asyncio
        from app.api.documents import process_document_background

        asyncio.get_event_loop().create_task(
            process_document_background(candidate.id, str(file_path), doc.workspace_id)
        )

    # Load creator
    result = await db.execute(
        select(DocumentVersion)
        .options(selectinload(DocumentVersion.creator))
        .where(DocumentVersion.id == new_version.id)
    )
    loaded = result.scalar_one()

    return LegacyDocumentVersionResponse(
        id=loaded.id,
        document_id=loaded.document_id,
        version_number=loaded.version_number,
        version_label=loaded.version_label,
        filename=loaded.filename,
        size=loaded.size_human,
        change_note=loaded.change_note,
        created_by_name=loaded.creator_name,
        is_current=bool(loaded.is_current),
        created_at=loaded.created_at,
    )


@router.get("/{doc_id}/versions/{version_id}/download")
async def download_version(
    doc_id: int,
    version_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Download a specific version of a document."""
    doc = (await db.execute(select(Document).where(Document.id == doc_id))).scalar_one_or_none()
    if not doc:
        raise HTTPException(status_code=404, detail="Document not found")

    await _check_doc_access(current_user, doc, db)
    from app.services.document_lifecycle import version_family_root
    try:
        root_id = await version_family_root(db, doc)
    except ValueError:
        raise HTTPException(status_code=409, detail="Dòng phiên bản không hợp lệ")

    version = (
        await db.execute(
            select(DocumentVersion).where(
                DocumentVersion.id == version_id,
                DocumentVersion.document_id == root_id,
            )
        )
    ).scalar_one_or_none()
    if not version:
        raise HTTPException(status_code=404, detail="Version not found")

    if version.document_ref_id is not None:
        candidate = await db.get(Document, version.document_ref_id)
        if candidate is None:
            raise HTTPException(status_code=404, detail="Version not found")
        await _check_doc_access(current_user, candidate, db)

    file_path = UPLOAD_DIR / version.filename
    if not file_path.exists():
        raise HTTPException(status_code=404, detail="Version file not found on disk")

    return FileResponse(
        path=str(file_path),
        filename=version.original_filename or f"{doc.original_filename} ({version.version_label})",
        media_type="application/octet-stream",
    )


# ─── Delete Document ───────────────────────────────────────────────

@router.put("/{doc_id}/effective-dates")
async def confirm_effective_dates(
    doc_id: int, body: EffectiveDatesUpdate,
    db: AsyncSession = Depends(get_db), current_user: User = Depends(get_current_user),
):
    """Admin records confirmed source metadata for a historical document."""
    if current_user.role != "Admin":
        raise HTTPException(status_code=403, detail="Chỉ Admin được bổ sung metadata lịch sử")
    if not body.reason.strip():
        raise HTTPException(status_code=400, detail="Cần lý do xác nhận metadata")
    if body.effective_until and body.effective_until < body.effective_from:
        raise HTTPException(status_code=400, detail="Ngày hết hiệu lực không hợp lệ")
    doc = (await db.execute(select(Document).where(Document.id == doc_id).with_for_update())).scalar_one_or_none()
    if not doc or doc.deleted_at is not None:
        raise HTTPException(status_code=404, detail="Document not found")
    doc.effective_from = body.effective_from
    doc.effective_until = body.effective_until
    doc.approved_by = current_user.id
    doc.approved_at = datetime.utcnow()
    doc.approval_note = body.reason.strip()
    from app.models.audit_event import AuditEvent
    db.add(AuditEvent(actor_id=current_user.id, action="confirm_effective_dates", object_type="document", object_id=doc.id, reason=body.reason.strip()))
    await db.commit()
    return {"id": doc.id, "effective_from": doc.effective_from, "effective_until": doc.effective_until}

@router.delete("/{doc_id}")
async def delete_document(
    doc_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """
    Delete a document and all its versions.
    Only the uploader or Admin can delete.
    """
    doc = (await db.execute(select(Document).where(Document.id == doc_id))).scalar_one_or_none()
    if not doc:
        raise HTTPException(status_code=404, detail="Document not found")

    await _can_modify_doc(current_user, doc, db)

    if doc.deleted_at is not None:
        raise HTTPException(status_code=409, detail="Tài liệu đã ở trong thùng rác")
    from app.services.document_lifecycle import set_family_deleted
    await set_family_deleted(db, doc)
    await db.commit()
    return {"message": "Đã chuyển tài liệu vào thùng rác"}


@router.post("/{doc_id}/restore")
async def restore_document(doc_id: int, background_tasks: BackgroundTasks, db: AsyncSession = Depends(get_db), current_user: User = Depends(get_current_user)):
    doc = (await db.execute(select(Document).where(Document.id == doc_id))).scalar_one_or_none()
    if not doc or doc.deleted_at is None:
        raise HTTPException(status_code=404, detail="Tài liệu không có trong thùng rác")
    if current_user.role != "Admin" and doc.uploader_id != current_user.id:
        raise HTTPException(status_code=403, detail="Permission denied")
    if (datetime.utcnow() - doc.deleted_at).days >= 30:
        raise HTTPException(status_code=410, detail="Thời hạn khôi phục đã hết")
    from app.services.document_lifecycle import set_family_deleted
    try:
        restored = await set_family_deleted(db, doc, restore=True)
    except ValueError as exc:
        if str(exc) == 'Duplicate content on restore':
            raise HTTPException(status_code=409, detail="Nội dung đã tồn tại trong kho tri thức; không thể khôi phục")
        raise
    await db.commit()
    from app.services.index_cleanup import queue_restored_documents
    await queue_restored_documents(db, restored, background_tasks)
    return {"id": doc.id, "message": "Đã khôi phục; quyền và hiệu lực được kiểm lại khi truy cập"}


class SourceAuthorityUpdate(BaseModel):
    issuer: str
    scope: str
    rank: int | None = None
    reason: str


@router.put("/{doc_id}/source-authority")
async def confirm_source_authority(doc_id: int, body: SourceAuthorityUpdate,
    db: AsyncSession = Depends(get_db), current_user: User = Depends(get_current_user)):
    if current_user.role != 'Admin':
        raise HTTPException(status_code=403,detail='Chỉ Admin được xác nhận thẩm quyền nguồn')
    if not body.reason.strip() or len(body.reason)>1000:
        raise HTTPException(status_code=400,detail='Cần lý do và căn cứ xác nhận thẩm quyền')
    if body.rank is not None and (not 1 <= body.rank <= 100 or not body.issuer.strip() or not body.scope.strip()):
        raise HTTPException(status_code=400,detail='Cần đơn vị ban hành, phạm vi và cấp ưu tiên từ 1 đến 100')
    if len(body.issuer)>250 or len(body.scope)>250:
        raise HTTPException(status_code=400,detail='Metadata thẩm quyền quá dài')
    doc=(await db.execute(select(Document).where(Document.id==doc_id).with_for_update())).scalar_one_or_none()
    if doc is None or doc.deleted_at is not None:
        raise HTTPException(status_code=404,detail='Document not found')
    doc.issuer=body.issuer.strip() or None;doc.authority_scope=body.scope.strip() or None;doc.authority_rank=body.rank
    doc.authority_verified_by=current_user.id if body.rank is not None else None
    doc.authority_verified_at=datetime.utcnow() if body.rank is not None else None
    from app.models.audit_event import AuditEvent
    from app.services.source_authority import authority_metadata
    db.add(AuditEvent(actor_id=current_user.id,action='confirm_source_authority',object_type='document',object_id=doc.id,reason=body.reason.strip()))
    await db.commit()
    return {'id':doc.id,'authority':authority_metadata(doc)}


@router.get("/{doc_id}/duplicate-check")
async def get_content_duplicate_check(
    doc_id: int, db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Expose content comparison without revealing an inaccessible match."""
    doc = await db.get(Document, doc_id)
    if doc is None:
        raise HTTPException(status_code=404, detail="Document not found")
    await _check_doc_access(current_user, doc, db)
    exact_id = getattr(doc, 'duplicate_of_document_id', None)
    near_id = getattr(doc, 'near_duplicate_document_id', None)
    match_type = 'exact' if exact_id else 'similar' if near_id else None
    target = await db.get(Document, exact_id or near_id) if match_type else None
    match = None
    if target is not None and target.workspace_id == doc.workspace_id:
        kb = await db.get(KnowledgeBase, target.workspace_id)
        if kb is not None and can_read_document(current_user, target, kb, allow_owner_pending=True):
            match = {'id': target.id, 'name': target.original_filename}
    return {
        'checked': bool(getattr(doc, 'text_fingerprint', None)),
        'match_type': match_type,
        'similarity': getattr(doc, 'duplicate_similarity', None) if match_type == 'similar' else None,
        'match': match,
        'scope': 'workspace',
    }
