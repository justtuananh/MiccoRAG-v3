from __future__ import annotations

import os
import re
import uuid
import logging
import hashlib
from datetime import date, datetime
from pathlib import Path

from fastapi import Header, APIRouter, Depends, HTTPException, status, UploadFile, File, Form, BackgroundTasks
from fastapi.responses import PlainTextResponse
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, or_

from app.core.config import settings
from app.core.permissions import (
    can_modify_workspace, can_read_document, require_workspace_read,
    require_document_read, require_document_write,
)
from app.core.deps import get_db
from app.core.security import get_current_user
from app.core.exceptions import NotFoundError
from app.models.knowledge_base import KnowledgeBase
from app.models.user import User
from app.models.document import Document, DocumentImage, DocumentStatus
from app.schemas.document import DocumentResponse, DocumentUploadResponse, DocumentUpdate
from app.schemas.rag import DocumentImageResponse

logger = logging.getLogger(__name__)


def _inject_images_from_db(
    markdown: str,
    images: list[DocumentImage],
    workspace_id: int,
) -> str:
    """Replace remaining <!-- image --> placeholders with real image markdown.

    Used as a safety net when the parser didn't inject them during processing.
    Images are matched in insertion order (by primary key) which mirrors the
    order of pictures in the original Docling document.
    """
    img_iter = iter(images)

    def _replacer(match):
        try:
            img = next(img_iter)
            url = f"/api/v1/documents/{img.document_id}/images/{img.image_id}/file"
            caption = (img.caption or "").replace("[", "").replace("]", "")
            return f"\n![{caption}]({url})\n"
        except StopIteration:
            return ""

    return re.sub(r"<!--\s*image\s*-->", _replacer, markdown)

router = APIRouter(prefix="/documents", tags=["documents"])

UPLOAD_DIR = settings.BASE_DIR / "uploads"
UPLOAD_DIR.mkdir(exist_ok=True)

ALLOWED_EXTENSIONS = {".pdf", ".txt", ".md", ".docx", ".pptx"}
MAX_FILE_SIZE = 50 * 1024 * 1024  # 50MB


async def _document_kb(db: AsyncSession, document: Document) -> KnowledgeBase:
    result = await db.execute(select(KnowledgeBase).where(KnowledgeBase.id == document.workspace_id))
    kb = result.scalar_one_or_none()
    if kb is None:
        raise NotFoundError("KnowledgeBase", document.workspace_id)
    return kb


@router.get("/workspace/{workspace_id}", response_model=list[DocumentResponse])
async def list_documents(
    workspace_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """List documents in a workspace.

    Non-admin users only see approved documents that are:
      - public, OR
      - belong to their department, OR
      - were uploaded by themselves.
    Admin / Trưởng phòng see all approved documents in the workspace.
    """
    result = await db.execute(select(KnowledgeBase).where(KnowledgeBase.id == workspace_id))
    kb = result.scalar_one_or_none()

    if kb is None:
        raise NotFoundError("KnowledgeBase", workspace_id)

    require_workspace_read(current_user, kb)
    stmt = select(Document).where(Document.workspace_id == workspace_id).order_by(Document.created_at.desc())
    result = await db.execute(stmt)
    return [doc for doc in result.scalars().all() if can_read_document(current_user, doc, kb)]


async def process_document_background(document_id: int, file_path: str, workspace_id: int):
    """Background task to process document for RAG indexing."""
    from app.core.database import async_session_maker
    from app.services.rag_service import get_rag_service

    async with async_session_maker() as db:
        try:
            # Load workspace-level KG settings
            from sqlalchemy import select as sa_select
            from app.models.knowledge_base import KnowledgeBase
            ws_result = await db.execute(
                sa_select(KnowledgeBase.kg_language, KnowledgeBase.kg_entity_types)
                .where(KnowledgeBase.id == workspace_id)
            )
            ws_row = ws_result.one_or_none()
            kg_language = ws_row.kg_language if ws_row else None
            kg_entity_types = ws_row.kg_entity_types if ws_row else None

            rag_service = get_rag_service(
                db, workspace_id,
                kg_language=kg_language,
                kg_entity_types=kg_entity_types,
            )
            await rag_service.process_document(document_id, file_path)
            logger.info(f"Document {document_id} processed successfully")
        except Exception as e:
            logger.error("Failed to process document %s: %s", document_id, type(e).__name__)
            await db.rollback()
            # Guarantee FAILED status even if process_document's own handler failed
            try:
                from sqlalchemy import select, update
                from app.models.document import Document, DocumentStatus
                result = await db.execute(
                    select(Document.status).where(Document.id == document_id)
                )
                current_status = result.scalar_one_or_none()
                if current_status and current_status != DocumentStatus.FAILED:
                    await db.execute(
                        update(Document)
                        .where(Document.id == document_id)
                        .values(
                            status=DocumentStatus.FAILED,
                            error_message="Không xử lý được tài liệu; vui lòng kiểm tra tệp và thử lại.",
                        )
                    )
                    await db.commit()
            except Exception as recovery_err:
                logger.error(f"Failed to set FAILED status for doc {document_id}: {recovery_err}")


async def process_knowledge_background(entry_id: int, workspace_id: int):
    """Background task to process knowledge entry for RAG indexing (NexusRAG only)."""
    from app.core.database import async_session_maker
    from app.services.rag_service import get_rag_service

    async with async_session_maker() as db:
        try:
            rag_service = get_rag_service(db, workspace_id)
            if hasattr(rag_service, "process_knowledge_entry"):
                await rag_service.process_knowledge_entry(entry_id)
                logger.info(f"Knowledge entry {entry_id} processed successfully")
            else:
                logger.warning(f"RAG service {type(rag_service)} does not support knowledge entries")
        except Exception as e:
            logger.error("Failed to process knowledge entry %s: %s", entry_id, type(e).__name__)
            await db.rollback()
            try:
                from sqlalchemy import update
                from app.models.knowledge_entry import KnowledgeEntry
                await db.execute(
                    update(KnowledgeEntry)
                    .where(KnowledgeEntry.id == entry_id)
                    .values(
                        ingest_status="failed",
                        ingest_error="Không lập chỉ mục được tri thức; vui lòng thử lại."
                    )
                )
                await db.commit()
            except Exception as recovery_err:
                logger.error(f"Failed to set FAILED status for knowledge {entry_id}: {recovery_err}")



@router.post("/upload/{workspace_id}", response_model=DocumentUploadResponse)
async def upload_document(
    workspace_id: int,
    file: UploadFile = File(...),
    idempotency_key: str | None = Header(None, max_length=128),
    same_name_action: str | None = Form(None),
    effective_from: date = Form(...),
    effective_until: date | None = Form(None),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
    department_id: int | None = None,
    visibility: str = "internal",
):
    """Upload a document to a knowledge base. Processing must be triggered separately."""
    result = await db.execute(select(KnowledgeBase).where(KnowledgeBase.id == workspace_id))
    kb = result.scalar_one_or_none()

    if kb is None:
        raise NotFoundError("KnowledgeBase", workspace_id)
    if kb.deleted_at is not None:
        raise HTTPException(status_code=410, detail="Kho tri thức đã được xóa")
    if effective_until and effective_until < effective_from:
        raise HTTPException(status_code=400, detail="Ngày hết hiệu lực không hợp lệ")

    department_member = (
        kb.visibility == "department" and kb.department_id is not None
        and kb.department_id == current_user.department_id
    )
    if not (can_modify_workspace(current_user, kb) or department_member):
        raise HTTPException(status_code=403, detail="Không có quyền tải lên kho tri thức này")
    effective_visibility = kb.visibility
    effective_dept_id = kb.department_id if kb.visibility == "department" else None

    ext = Path(file.filename).suffix.lower()
    if ext not in ALLOWED_EXTENSIONS:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"File type {ext} not allowed. Allowed: {ALLOWED_EXTENSIONS}"
        )

    content = await file.read(MAX_FILE_SIZE + 1)
    if len(content) > MAX_FILE_SIZE:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"File too large. Max size: {MAX_FILE_SIZE // 1024 // 1024}MB"
        )
    if not content or (ext in {".txt", ".md"} and not content.strip()):
        raise HTTPException(status_code=400, detail="Tệp rỗng hoặc không có nội dung")
    content_hash = hashlib.sha256(content).hexdigest()
    from app.services.upload_idempotency import replay_upload, record_upload, lock_upload_hashes, require_filename_choice
    payload = {"same_name_action":same_name_action,"hash":content_hash,"filename":file.filename,"workspace_id":workspace_id,"effective_from":effective_from,"effective_until":effective_until}
    replay = await replay_upload(db,current_user,"v1-upload",idempotency_key,payload)
    if replay is not None:
        return replay
    await lock_upload_hashes(db,workspace_id,[content_hash])
    duplicate = (await db.execute(select(Document).where(
        Document.workspace_id == workspace_id, Document.content_hash == content_hash,
        Document.deleted_at.is_(None),
    ))).scalar_one_or_none()
    if duplicate:
        detail = {"message": "Nội dung đã tồn tại trong kho tri thức"}
        if can_read_document(current_user,duplicate,kb,allow_owner_pending=True):
            detail["document_id"] = duplicate.id
        raise HTTPException(status_code=409, detail=detail)

    await require_filename_choice(db,workspace_id,[file.filename],same_name_action)
    filename = f"{uuid.uuid4()}{ext}"
    file_path = UPLOAD_DIR / filename

    import aiofiles
    async with aiofiles.open(file_path, "wb") as f:
        await f.write(content)

    # Non-admin uploads start as pending approval; admin uploads are pre-approved
    if effective_visibility == "private" or current_user.role == "Admin":
        doc_approval_status = "approved"
    elif effective_visibility == "public":
        doc_approval_status = "approved" if current_user.role in {"Giám đốc", "Phó giám đốc"} else "pending_org" if current_user.role == "Trưởng phòng" else "pending"
    else:
        doc_approval_status = "approved" if current_user.role == "Trưởng phòng" and department_member else "pending"

    document = Document(
        workspace_id=workspace_id,
        filename=filename,
        original_filename=file.filename,
        file_type=ext[1:],
        file_size=len(content),
        status=DocumentStatus.PENDING,
        uploader_id=current_user.id,
        department_id=effective_dept_id,
        visibility=effective_visibility,
        approval_status=doc_approval_status,
        effective_from=effective_from,
        effective_until=effective_until,
        content_hash=content_hash,
        approved_by=current_user.id if doc_approval_status == "approved" else None,
        approved_at=datetime.utcnow() if doc_approval_status == "approved" else None,
    )
    db.add(document)
    try:
        await db.flush()
        response = DocumentUploadResponse(id=document.id, filename=document.original_filename,
            status=document.status, message="Đã tiếp nhận tài liệu")
        record_upload(db,current_user,"v1-upload",idempotency_key,payload,response)
        await db.commit()
    except Exception:
        await db.rollback()
        file_path.unlink(missing_ok=True)
        raise
    return response


@router.get("/{document_id}", response_model=DocumentResponse)
async def get_document(
    document_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Get document by ID.

    Users can only access approved documents that are:
      - public, OR
      - belong to their department, OR
      - were uploaded by themselves.
    Admin / Trưởng phòng bypass these restrictions.
    """
    result = await db.execute(select(Document).where(Document.id == document_id))
    document = result.scalar_one_or_none()

    if document is None:
        raise NotFoundError("Document", document_id)

    require_document_read(current_user, document, await _document_kb(db, document))

    return document


@router.get("/{document_id}/markdown")
async def get_document_markdown(
    document_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Get the full structured markdown content of a document (NexusRAG parsed)."""
    result = await db.execute(select(Document).where(Document.id == document_id))
    document = result.scalar_one_or_none()

    if document is None:
        raise NotFoundError("Document", document_id)

    require_document_read(current_user, document, await _document_kb(db, document))

    if not document.markdown_content:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="No markdown content available. Document may not have been processed with NexusRAG."
        )

    markdown = document.markdown_content

    # Replace old public image URLs in persisted markdown on read. The image ID
    # must belong to this document, so no stale cross-document link is emitted.
    if "<!-- image" in markdown or "/static/doc-images/" in markdown:
        img_result = await db.execute(
            select(DocumentImage)
            .where(DocumentImage.document_id == document_id)
            .order_by(DocumentImage.id)
        )
        images = img_result.scalars().all()
        if images:
            markdown = _inject_images_from_db(markdown, images, document.workspace_id)
            known = {img.image_id for img in images}

            def _protect_legacy_image(match):
                image_id = match.group(1)
                if image_id not in known:
                    return ""
                return f"/api/v1/documents/{document.id}/images/{image_id}/file"

            markdown = re.sub(
                r"/static/doc-images/kb_\d+/images/([A-Za-z0-9_-]+)\.png",
                _protect_legacy_image,
                markdown,
            )

    return PlainTextResponse(
        content=markdown,
        media_type="text/markdown",
    )


@router.get("/{document_id}/images", response_model=list[DocumentImageResponse])
async def get_document_images(
    document_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """List all extracted images for a document."""
    result = await db.execute(select(Document).where(Document.id == document_id))
    document = result.scalar_one_or_none()

    if document is None:
        raise NotFoundError("Document", document_id)

    require_document_read(current_user, document, await _document_kb(db, document))

    result = await db.execute(
        select(DocumentImage)
        .where(DocumentImage.document_id == document_id)
        .order_by(DocumentImage.page_no)
    )
    images = result.scalars().all()

    return [
        DocumentImageResponse(
            image_id=img.image_id,
            document_id=img.document_id,
            page_no=img.page_no,
            caption=img.caption or "",
            width=img.width,
            height=img.height,
            url=f"/api/v1/documents/{document.id}/images/{img.image_id}/file",
        )
        for img in images
    ]


@router.get("/{document_id}/images/{image_id}/file")
async def get_document_image_file(
    document_id: int,
    image_id: str,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    document = (await db.execute(select(Document).where(Document.id == document_id))).scalar_one_or_none()
    if document is None:
        raise NotFoundError("Document", document_id)
    require_document_read(current_user, document, await _document_kb(db, document))
    image = (await db.execute(select(DocumentImage).where(
        DocumentImage.document_id == document_id,
        DocumentImage.image_id == image_id,
    ))).scalar_one_or_none()
    if image is None:
        raise NotFoundError("DocumentImage", image_id)
    root = (settings.BASE_DIR / "data" / "docling").resolve()
    image_path = Path(image.file_path).resolve()
    if not image_path.is_relative_to(root) or not image_path.is_file():
        raise HTTPException(status_code=404, detail="Image file not found")
    media_type = image.mime_type or "image/png"
    if media_type not in {"image/png", "image/jpeg", "image/webp", "image/gif"}:
        raise HTTPException(status_code=415, detail="Unsupported image type")
    return FileResponse(
        image_path,
        media_type=media_type,
        headers={"X-Content-Type-Options": "nosniff", "Cache-Control": "private, no-store"},
    )


@router.put("/{document_id}", response_model=DocumentResponse)
async def update_document(
    document_id: int,
    payload: DocumentUpdate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Update document properties (e.g., rename). Only owner or admin can update."""
    result = await db.execute(select(Document).where(Document.id == document_id))
    document = result.scalar_one_or_none()

    if document is None:
        raise NotFoundError("Document", document_id)

    require_document_write(current_user, document, await _document_kb(db, document))

    document.original_filename = payload.original_filename
    await db.commit()
    await db.refresh(document)
    return document


from fastapi.responses import FileResponse

@router.get("/{document_id}/download")
async def download_original_document(
    document_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Download the original uploaded file."""
    result = await db.execute(select(Document).where(Document.id == document_id))
    document = result.scalar_one_or_none()

    if document is None:
        raise NotFoundError("Document", document_id)

    require_document_read(current_user, document, await _document_kb(db, document))

    file_path = UPLOAD_DIR / document.filename
    if not file_path.exists():
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Original file not found on disk."
        )

    return FileResponse(
        path=file_path,
        filename=document.original_filename,
        content_disposition_type="inline"  # Allows iframe preview for supported types
    )


@router.delete("/{document_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_document(
    document_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Delete a document and its chunks from vector store.

    Only the uploader, Trưởng phòng of the doc's department, or Admin can delete.
    """
    result = await db.execute(select(Document).where(Document.id == document_id))
    document = result.scalar_one_or_none()

    if document is None:
        raise NotFoundError("Document", document_id)

    require_document_write(current_user, document, await _document_kb(db, document))

    if document.deleted_at is not None:
        raise HTTPException(status_code=409, detail="Tài liệu đã ở trong thùng rác")
    from app.services.document_lifecycle import set_family_deleted
    await set_family_deleted(db, document)
    await db.commit()


@router.post("/{document_id}/restore")
async def restore_document(document_id: int, background_tasks: BackgroundTasks, db: AsyncSession = Depends(get_db), current_user: User = Depends(get_current_user)):
    document = (await db.execute(select(Document).where(Document.id == document_id))).scalar_one_or_none()
    if document is None or document.deleted_at is None:
        raise NotFoundError("Document", document_id)
    if current_user.role != "Admin" and document.uploader_id != current_user.id:
        raise HTTPException(status_code=403, detail="Không có quyền khôi phục tài liệu")
    if (datetime.utcnow() - document.deleted_at).days >= 30:
        raise HTTPException(status_code=410, detail="Thời hạn khôi phục đã hết")
    from app.services.document_lifecycle import set_family_deleted
    restored = await set_family_deleted(db, document, restore=True)
    await db.commit()
    from app.services.index_cleanup import queue_restored_documents
    await queue_restored_documents(db, restored, background_tasks)
    return {"id": document.id, "message": "Đã khôi phục; quyền và hiệu lực được kiểm lại khi truy cập"}
