"""
Suggested Questions Service
===========================
Generates 4 suggested questions for a workspace based on its newest document.
Used both:
  - Automatically after document ingestion (NexusRAGService)
  - Manually via GET /workspaces/{id}/suggested-questions
"""
from __future__ import annotations

import json
import logging
import re
from typing import TYPE_CHECKING

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import settings
from app.models.knowledge_base import KnowledgeBase
from app.services.llm import get_llm_provider
from app.services.llm.types import LLMMessage, LLMResult
from app.services.vector_store import get_vector_store

if TYPE_CHECKING:
    pass

logger = logging.getLogger(__name__)

# Static fallback questions
FALLBACK_QUESTIONS = [
    "Phân tích rủi ro & cơ hội?",
    "Chiến lược hành động cốt lõi",
    "Đánh giá hiệu quả hệ thống",
    "Tối ưu hóa quy trình hiện tại",
]

# System prompt cho việc tạo câu hỏi
SYSTEM_PROMPT = (
    "Bạn là một trợ lý phân tích tài liệu chuyên nghiệp. "
    "Chỉ trả về một mảng JSON chứa các chuỗi ký tự (câu hỏi tiếng Việt ngắn gọn, dưới 15 từ), "
    "phù hợp để người dùng click vào nhằm khám phá nội dung tài liệu."
)


async def generate_suggested_questions(
    db: AsyncSession,
    workspace_id: int,
    document_id: int | None = None,
) -> list[str]:
    """
    Generate 4 suggested questions for a workspace based on the newest document.

    Args:
        db: Database session
        workspace_id: Knowledge base / workspace ID
        document_id: Optional. If provided, only use this document's chunks.
                     Otherwise, use the latest document in the workspace.

    Returns:
        List of 4 suggested questions (Tiếng Việt).
    """
    try:
        # 1. Load workspace
        kb_result = await db.execute(
            select(KnowledgeBase).where(KnowledgeBase.id == workspace_id)
        )
        kb = kb_result.scalar_one_or_none()
        if kb is None:
            logger.warning(f"Workspace {workspace_id} not found for suggested questions")
            return FALLBACK_QUESTIONS

        # 2. Get chunks from vector store
        chunks: list[str] = []

        if document_id is not None:
            # Use specific document
            vs = get_vector_store(workspace_id)
            chunks = vs.get_by_document_id(document_id, limit=20)
        else:
            # Fallback: use all chunks from workspace (latest document logic in step 3)
            vs = get_vector_store(workspace_id)
            all_data = vs.collection.get(limit=50, include=["documents", "metadatas"])
            docs = all_data.get("documents", []) or []
            metadatas = all_data.get("metadatas", []) or []

            if not docs:
                logger.info(f"No chunks found in workspace {workspace_id}")
                kb.suggested_questions = FALLBACK_QUESTIONS
                await db.commit()
                return FALLBACK_QUESTIONS

            # Pick chunks from newest document (by sorting on chunk_index=0 and document_id desc)
            from app.models.document import Document, DocumentStatus
            newest_doc_result = await db.execute(
                select(Document)
                .where(
                    Document.workspace_id == workspace_id,
                    Document.status == DocumentStatus.INDEXED,
                )
                .order_by(Document.updated_at.desc())
                .limit(1)
            )
            newest_doc = newest_doc_result.scalar_one_or_none()

            if newest_doc:
                # Filter chunks belonging to newest document
                chunks = [
                    doc
                    for doc, meta in zip(docs, metadatas)
                    if meta and meta.get("document_id") == newest_doc.id
                ]
                logger.info(
                    f"Suggested questions: using newest doc {newest_doc.id} "
                    f"('{newest_doc.original_filename}') in workspace {workspace_id}"
                )
            else:
                chunks = docs[:20]

        if not chunks:
            logger.info(f"No chunks for workspace {workspace_id} in suggested questions")
            kb.suggested_questions = FALLBACK_QUESTIONS
            await db.commit()
            return FALLBACK_QUESTIONS

        # 3. Build context from chunks
        context = "\n\n".join(chunks[:15])  # Limit to avoid token overflow

        # 4. Call LLM
        llm = get_llm_provider()
        user_prompt = (
            f"Dựa trên các đoạn văn bản sau trích từ không gian làm việc '{kb.name}', "
            f"hãy đề xuất 4 câu hỏi tiếng Việt ngắn gọn (dưới 15 từ), súc tích "
            f"mà người dùng có thể muốn hỏi để tìm hiểu nội dung.\n"
            f"Yêu cầu:\n"
            f"- Trả về DUY NHẤT một mảng JSON. Ví dụ: [\"Câu hỏi 1?\", \"Câu hỏi 2?\", \"Câu hỏi 3?\", \"Câu hỏi 4?\"]\n"
            f"- Không thêm bất kỳ lời dẫn hay giải thích nào khác.\n"
            f"- Các câu hỏi nên đa dạng, bao quát nhiều khía cạnh của tài liệu.\n\n"
            f"Nội dung tài liệu:\n{context[:5000]}"
        )

        response = await llm.acomplete(
            messages=[
                LLMMessage(role="system", content=SYSTEM_PROMPT),
                LLMMessage(role="user", content=user_prompt),
            ],
            temperature=0.7,
        )

        # Parse response
        response_text = (
            response.content if isinstance(response, LLMResult) else str(response)
        )

        # Extract JSON array
        match = re.search(r"\[\s*\".*?\"\s*\]", response_text, re.DOTALL)
        if match:
            questions = json.loads(match.group(0))
        else:
            logger.warning(f"LLM did not return JSON array: {response_text[:200]}")
            questions = FALLBACK_QUESTIONS

        if isinstance(questions, list) and len(questions) > 0:
            # Ensure exactly 4 questions
            questions = questions[:4]
            while len(questions) < 4:
                questions.append(FALLBACK_QUESTIONS[len(questions) % len(FALLBACK_QUESTIONS)])

            # Save to workspace
            kb.suggested_questions = questions
            await db.commit()
            logger.info(f"Generated {len(questions)} suggested questions for workspace {workspace_id}")
            return questions
        else:
            raise ValueError(f"Invalid questions response: {response_text[:200]}")

    except Exception as e:
        logger.error(f"Failed to generate suggested questions for WS {workspace_id}: {e}")
        # Save fallback on error
        try:
            kb_result = await db.execute(
                select(KnowledgeBase).where(KnowledgeBase.id == workspace_id)
            )
            kb = kb_result.scalar_one_or_none()
            if kb:
                kb.suggested_questions = FALLBACK_QUESTIONS
                await db.commit()
        except Exception:
            pass
        return FALLBACK_QUESTIONS
