"""
Knowledge Base (Workspace) CRUD API endpoints.
"""
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func

from app.core.deps import get_db
from app.core.exceptions import NotFoundError
from app.models.knowledge_base import KnowledgeBase
from app.models.document import Document, DocumentStatus
from app.schemas.workspace import (
    WorkspaceCreate,
    WorkspaceUpdate,
    WorkspaceResponse,
    WorkspaceSummary,
)
from app.services.llm.types import LLMMessage, LLMResult

router = APIRouter(prefix="/workspaces", tags=["workspaces"])


async def _enrich_response(db: AsyncSession, kb: KnowledgeBase) -> WorkspaceResponse:
    """Build WorkspaceResponse with computed counts."""
    total = await db.execute(
        select(func.count(Document.id)).where(Document.workspace_id == kb.id)
    )
    indexed = await db.execute(
        select(func.count(Document.id)).where(
            Document.workspace_id == kb.id,
            Document.status == DocumentStatus.INDEXED,
        )
    )
    return WorkspaceResponse(
        id=kb.id,
        name=kb.name,
        description=kb.description,
        system_prompt=kb.system_prompt,
        kg_language=kb.kg_language,
        kg_entity_types=kb.kg_entity_types,
        search_mode=kb.search_mode,
        indexed_count=indexed.scalar() or 0,
        suggested_questions=kb.suggested_questions,
        created_at=kb.created_at,
        updated_at=kb.updated_at,
    )


@router.get("", response_model=list[WorkspaceResponse])
async def list_workspaces(db: AsyncSession = Depends(get_db)):
    """List all knowledge bases."""
    result = await db.execute(
        select(KnowledgeBase).order_by(KnowledgeBase.updated_at.desc())
    )
    kbs = result.scalars().all()
    return [await _enrich_response(db, kb) for kb in kbs]


@router.post("", response_model=WorkspaceResponse, status_code=status.HTTP_201_CREATED)
async def create_workspace(
    body: WorkspaceCreate,
    db: AsyncSession = Depends(get_db),
):
    """Create a new knowledge base."""
    kb = KnowledgeBase(
        name=body.name,
        description=body.description,
        kg_language=body.kg_language,
        kg_entity_types=body.kg_entity_types,
        search_mode=body.search_mode,
    )
    db.add(kb)
    await db.commit()
    await db.refresh(kb)
    return await _enrich_response(db, kb)


@router.get("/summary", response_model=list[WorkspaceSummary])
async def list_workspace_summaries(db: AsyncSession = Depends(get_db)):
    """Compact list for dropdown selectors."""
    result = await db.execute(
        select(KnowledgeBase).order_by(KnowledgeBase.name)
    )
    kbs = result.scalars().all()
    summaries = []
    for kb in kbs:
        cnt = await db.execute(
            select(func.count(Document.id)).where(Document.workspace_id == kb.id)
        )
        summaries.append(WorkspaceSummary(
            id=kb.id, name=kb.name, document_count=cnt.scalar() or 0
        ))
    return summaries


@router.get("/{workspace_id}", response_model=WorkspaceResponse)
async def get_workspace(
    workspace_id: int,
    db: AsyncSession = Depends(get_db),
):
    """Get a knowledge base by ID."""
    result = await db.execute(
        select(KnowledgeBase).where(KnowledgeBase.id == workspace_id)
    )
    kb = result.scalar_one_or_none()
    if kb is None:
        raise NotFoundError("KnowledgeBase", workspace_id)
    return await _enrich_response(db, kb)


@router.put("/{workspace_id}", response_model=WorkspaceResponse)
async def update_workspace(
    workspace_id: int,
    body: WorkspaceUpdate,
    db: AsyncSession = Depends(get_db),
):
    """Update a knowledge base name/description."""
    result = await db.execute(
        select(KnowledgeBase).where(KnowledgeBase.id == workspace_id)
    )
    kb = result.scalar_one_or_none()
    if kb is None:
        raise NotFoundError("KnowledgeBase", workspace_id)

    if body.name is not None:
        kb.name = body.name
    if body.description is not None:
        kb.description = body.description
    if body.system_prompt is not None:
        # Empty string → reset to default (None)
        kb.system_prompt = body.system_prompt or None
    if body.kg_language is not None:
        kb.kg_language = body.kg_language or None
    if body.kg_entity_types is not None:
        kb.kg_entity_types = body.kg_entity_types or None
    if body.search_mode is not None:
        kb.search_mode = body.search_mode or "hybrid"

    await db.commit()
    await db.refresh(kb)
    return await _enrich_response(db, kb)


@router.get("/{workspace_id}/suggested-questions", response_model=list[str])
async def get_suggested_questions(
    workspace_id: int,
    db: AsyncSession = Depends(get_db),
):
    """
    Get or generate 4 suggested questions for this workspace.
    """
    result = await db.execute(select(KnowledgeBase).where(KnowledgeBase.id == workspace_id))
    kb = result.scalar_one_or_none()
    if kb is None:
        raise NotFoundError("KnowledgeBase", workspace_id)

    if kb.suggested_questions:
        return kb.suggested_questions

    # Generate if possible
    try:
        from app.services.vector_store import get_vector_store
        vs = get_vector_store(workspace_id)
        
        # Get some sample text from vector store
        # ChromaDB .get() with limit
        data = vs.collection.get(limit=10, include=["documents"])
        docs = data.get("documents", [])
        
        if not docs:
            # Fallback defaults
            return ["Phân tích rủi ro & cơ hội?", "Chiến lược hành động cốt lõi", "Đánh giá hiệu quả hệ thống", "Tối ưu hóa quy trình hiện tại"]

        context = "\n\n".join(docs[:10])
        
        from app.services.llm import get_llm_provider
        llm = get_llm_provider()
        
        system_prompt = "Bạn là một trợ lý phân tích tài liệu chuyên nghiệp. Chỉ trả về một mảng JSON chứa các chuỗi ký tự (câu hỏi)."
        user_prompt = f"""Dựa trên các đoạn văn bản sau trích từ không gian làm việc '{kb.name}', hãy đề xuất 4 câu hỏi tiếng Việt ngắn gọn (dưới 15 từ), súc tích mà người dùng có thể muốn hỏi để tìm hiểu nội dung.
Yêu cầu:
- Trả về DUY NHẤT một mảng JSON. Ví dụ: ["Câu hỏi 1?", "Câu hỏi 2?", "Câu hỏi 3?", "Câu hỏi 4?"]
- Không thêm bất kỳ lời dẫn hay giải thích nào khác.

Nội dung tài liệu:
{context[:4000]}
"""
        response = await llm.acomplete(
            messages=[
                LLMMessage(role="system", content=system_prompt),
                LLMMessage(role="user", content=user_prompt)
            ],
            temperature=0.7
        )
        
        # response could be str or LLMResult
        response_text = response.content if isinstance(response, LLMResult) else response
        
        import json
        import re
        
        # Try to find JSON array in response
        match = re.search(r"\[\s*\".*\"\s*\]", response_text, re.DOTALL)
        if match:
            questions = json.loads(match.group(0))
        else:
            # Simple fallback if LLM output was messy but contains lines
            questions = json.loads(response_text) # fallback parse

        if isinstance(questions, list) and len(questions) > 0:
            kb.suggested_questions = questions[:4]
            await db.commit()
            return kb.suggested_questions

    except Exception as e:
        import logging
        logging.getLogger(__name__).error(f"Failed to generate suggested questions for WS {workspace_id}: {e}")
    
    # Static fallback
    return ["Phân tích rủi ro & cơ hội?", "Chiến lược hành động cốt lõi", "Đánh giá hiệu quả hệ thống", "Tối ưu hóa quy trình hiện tại"]


@router.delete("/{workspace_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_workspace(
    workspace_id: int,
    db: AsyncSession = Depends(get_db),
):
    """Delete a knowledge base and all its documents."""
    result = await db.execute(
        select(KnowledgeBase).where(KnowledgeBase.id == workspace_id)
    )
    kb = result.scalar_one_or_none()
    if kb is None:
        raise NotFoundError("KnowledgeBase", workspace_id)

    # Clean up vector store and KG data
    try:
        from app.services.vector_store import get_vector_store
        vs = get_vector_store(workspace_id)
        vs.delete_collection()
    except Exception:
        pass

    try:
        from app.services.knowledge_graph_service import KnowledgeGraphService
        kg = KnowledgeGraphService(workspace_id)
        await kg.delete_project_data()
    except Exception:
        pass

    # Clean up image files
    import shutil
    from app.core.config import settings
    images_dir = settings.BASE_DIR / "data" / "docling" / f"kb_{workspace_id}"
    if images_dir.exists():
        shutil.rmtree(images_dir, ignore_errors=True)

    await db.delete(kb)
    await db.commit()
