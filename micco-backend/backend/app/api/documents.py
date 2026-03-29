from __future__ import annotations

import os
import re
import uuid
import logging
from pathlib import Path

from fastapi import APIRouter, Depends, HTTPException, status, UploadFile, File, BackgroundTasks
from fastapi.responses import PlainTextResponse
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, or_

from app.core.config import settings
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
            url = f"/static/doc-images/kb_{workspace_id}/images/{img.image_id}.png"
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

    stmt = select(Document).where(
        Document.workspace_id == workspace_id,
        Document.approval_status == "approved"
    )

    # RBAC: non-admin users are scoped by visibility + department + own uploads
    if current_user.role not in ("Admin", "Trưởng phòng"):
        stmt = stmt.where(
            or_(
                Document.visibility == "public",
                Document.department_id == current_user.department_id,
                Document.uploader_id == current_user.id,
            )
        )

    stmt = stmt.order_by(Document.created_at.desc())
    result = await db.execute(stmt)
    return result.scalars().all()


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
            logger.error(f"Failed to process document {document_id}: {e}")
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
                            error_message=str(e)[:500],
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
            logger.error(f"Failed to process knowledge entry {entry_id}: {e}")
            try:
                from sqlalchemy import update
                from app.models.knowledge_entry import KnowledgeEntry
                await db.execute(
                    update(KnowledgeEntry)
                    .where(KnowledgeEntry.id == entry_id)
                    .values(
                        ingest_status="failed",
                        error_message=str(e)[:500]
                    )
                )
                await db.commit()
            except Exception as recovery_err:
                logger.error(f"Failed to set FAILED status for knowledge {entry_id}: {recovery_err}")



@router.post("/upload/{workspace_id}", response_model=DocumentUploadResponse)
async def upload_document(
    workspace_id: int,
    file: UploadFile = File(...),
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

    ext = Path(file.filename).suffix.lower()
    if ext not in ALLOWED_EXTENSIONS:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"File type {ext} not allowed. Allowed: {ALLOWED_EXTENSIONS}"
        )

    content = await file.read()
    if len(content) > MAX_FILE_SIZE:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"File too large. Max size: {MAX_FILE_SIZE // 1024 // 1024}MB"
        )

    filename = f"{uuid.uuid4()}{ext}"
    file_path = UPLOAD_DIR / filename

    import aiofiles
    async with aiofiles.open(file_path, "wb") as f:
        await f.write(content)

    # Non-admin uploads start as pending approval; admin uploads are pre-approved
    is_admin = current_user.role in ("Admin", "Trưởng phòng")
    doc_approval_status = "approved" if is_admin else "pending"

    document = Document(
        workspace_id=workspace_id,
        filename=filename,
        original_filename=file.filename,
        file_type=ext[1:],
        file_size=len(content),
        status=DocumentStatus.PENDING,
        uploader_id=current_user.id,
        department_id=department_id or current_user.department_id,
        visibility=visibility,
        approval_status=doc_approval_status,
    )
    db.add(document)
    await db.commit()
    await db.refresh(document)

    return DocumentUploadResponse(
        id=document.id,
        filename=document.original_filename,
        status=document.status,
        message="Tải lên thành công! Đang chờ phê duyệt."
        if doc_approval_status == "pending"
        else "Document uploaded. Click 'Process' to extract and index content.",
    )


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

    if document.approval_status != "approved":
        raise HTTPException(status_code=403, detail="Document chưa được phê duyệt")

    if current_user.role not in ("Admin", "Trưởng phòng"):
        if (
            document.visibility != "public"
            and document.department_id != current_user.department_id
            and document.uploader_id != current_user.id
        ):
            raise HTTPException(status_code=403, detail="Không có quyền truy cập tài liệu này")

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

    # Access check
    if document.approval_status != "approved":
        raise HTTPException(status_code=403, detail="Document chưa được phê duyệt")
    if current_user.role not in ("Admin", "Trưởng phòng"):
        if (
            document.visibility != "public"
            and document.department_id != current_user.department_id
            and document.uploader_id != current_user.id
        ):
            raise HTTPException(status_code=403, detail="Không có quyền truy cập tài liệu này")

    if not document.markdown_content:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="No markdown content available. Document may not have been processed with NexusRAG."
        )

    markdown = document.markdown_content

    # Safety net: if image placeholders remain, inject real references on-the-fly
    if "<!-- image" in markdown:
        img_result = await db.execute(
            select(DocumentImage)
            .where(DocumentImage.document_id == document_id)
            .order_by(DocumentImage.id)
        )
        images = img_result.scalars().all()
        if images:
            markdown = _inject_images_from_db(markdown, images, document.workspace_id)

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

    # Access check
    if document.approval_status != "approved":
        raise HTTPException(status_code=403, detail="Document chưa được phê duyệt")
    if current_user.role not in ("Admin", "Trưởng phòng"):
        if (
            document.visibility != "public"
            and document.department_id != current_user.department_id
            and document.uploader_id != current_user.id
        ):
            raise HTTPException(status_code=403, detail="Không có quyền truy cập tài liệu này")

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
            url=f"/static/doc-images/kb_{document.workspace_id}/images/{img.image_id}.png",
        )
        for img in images
    ]


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

    # Only uploader or admin/trưởng phòng can update
    if current_user.role not in ("Admin", "Trưởng phòng") and document.uploader_id != current_user.id:
        raise HTTPException(status_code=403, detail="Không có quyền sửa tài liệu này")

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

    # Access check
    if document.approval_status != "approved":
        raise HTTPException(status_code=403, detail="Document chưa được phê duyệt")
    if current_user.role not in ("Admin", "Trưởng phòng"):
        if (
            document.visibility != "public"
            and document.department_id != current_user.department_id
            and document.uploader_id != current_user.id
        ):
            raise HTTPException(status_code=403, detail="Không có quyền truy cập tài liệu này")

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

    # Only uploader, trưởng phòng of the doc's dept, or admin can delete
    is_owner = document.uploader_id == current_user.id
    is_dept_manager = (
        current_user.role == "Trưởng phòng"
        and document.department_id == current_user.department_id
    )
    is_admin = current_user.role == "Admin"
    if not (is_owner or is_dept_manager or is_admin):
        raise HTTPException(status_code=403, detail="Không có quyền xóa tài liệu này")

    if document.status == DocumentStatus.INDEXED:
        try:
            from app.services.rag_service import get_rag_service
            rag_service = get_rag_service(db, document.workspace_id)
            await rag_service.delete_document(document_id)
        except Exception as e:
            logger.warning(f"Failed to delete chunks from vector store: {e}")

    file_path = UPLOAD_DIR / document.filename
    if file_path.exists():
        os.remove(file_path)

    await db.delete(document)
    await db.commit()
