"""
Expert Recommendation Service
==============================
Đề xuất chuyên gia (users đã upload nhiều tài liệu liên quan nhất)
dựa trên câu hỏi của người dùng trong 1 workspace cụ thể.

Logic:
  1. Embed câu hỏi bằng EmbeddingService
  2. Vector search trong workspace để tìm top-K documents liên quan
  3. Với mỗi document tìm được → lấy uploader_id + relevance score
  4. Group by user → đếm số doc liên quan + avg relevance
  5. Join với User + Department để lấy thông tin đầy đủ
  6. Sort theo document_count desc, trả về top_K
"""
from __future__ import annotations

import logging
from collections import defaultdict
from typing import Annotated

from pydantic import BaseModel, Field
from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.models.user import User
from app.models.department import Department
from app.models.document import Document, DocumentStatus
from app.services.embedder import get_embedding_service
from app.services.vector_store import get_vector_store

logger = logging.getLogger(__name__)


class ExpertRecommendation(BaseModel):
    """Schema cho một chuyên gia được đề xuất."""
    user_id: int
    name: str
    email: str
    role: str
    department: str
    document_count: int = Field(ge=1)
    avg_relevance: float = Field(ge=0.0, le=1.0)


def _cosine_to_relevance(distance: float) -> float:
    """Chuyển cosine distance → relevance score (0-1)."""
    # ChromaDB dùng cosine distance: 0 = identical, 2 = opposite
    # relevance = 1 - distance/2 → 1.0 (identical) → 0.0 (opposite)
    return max(0.0, min(1.0, 1.0 - distance / 2.0))


async def recommend_experts(
    workspace_id: int,
    query: str,
    top_k: int = 3,
    db: AsyncSession | None = None,
    allowed_document_ids: list[int] | None = None,
) -> list[ExpertRecommendation]:
    """
    Đề xuất top-K chuyên gia trong một workspace dựa trên câu hỏi.

    Args:
        workspace_id: ID của knowledge base / workspace
        query: Câu hỏi của người dùng
        top_k: Số lượng chuyên gia cần trả về (default 3, max 10)
        db: AsyncSession để query database (optional)
        allowed_document_ids: Filter chỉ search trong các document được phép truy cập

    Returns:
        Danh sách ExpertRecommendation đã được sort theo document_count desc
    """
    if top_k < 1:
        top_k = 1
    if top_k > 10:
        top_k = 10

    if not query or not query.strip():
        return []

    # ── Step 1: Embed câu hỏi ──────────────────────────────────────────────
    embedder = get_embedding_service()
    query_embedding = embedder.embed_query(query)
    logger.debug(f"Embedded query for expert recommendation (dim={len(query_embedding)})")

    # ── Step 2: Vector search trong ChromaDB ───────────────────────────────
    # Over-fetch để có đủ data cho việc group by user
    search_k = top_k * 5  # mỗi user có thể có nhiều doc → fetch nhiều hơn
    vector_store = get_vector_store(workspace_id)

    where: dict | None = None
    if allowed_document_ids:
        where = {"document_id": {"$in": allowed_document_ids}}

    try:
        results = vector_store.query(
            query_embedding=query_embedding,
            n_results=search_k,
            where=where,
        )
    except Exception as e:
        logger.warning(f"Vector search failed for workspace {workspace_id}: {e}")
        return []

    chunk_ids: list[str] = results.get("ids", [])
    metadatas: list[dict] = results.get("metadatas", [])
    distances: list[float] = results.get("distances", [])

    if not chunk_ids:
        logger.debug(f"No relevant documents found in workspace {workspace_id}")
        return []

    # ── Step 3: Map document_id → relevance, group by document ─────────────
    # Lấy unique document_id + max relevance per document
    doc_relevance: dict[int, float] = {}  # document_id → best relevance

    for i, meta in enumerate(metadatas):
        doc_id = int(meta.get("document_id", 0)) if meta.get("document_id") else 0
        if doc_id == 0:
            continue
        distance = distances[i] if i < len(distances) else 1.0
        relevance = _cosine_to_relevance(distance)
        # Keep max (best) relevance when same doc_id appears multiple times
        if doc_id not in doc_relevance or relevance > doc_relevance[doc_id]:
            doc_relevance[doc_id] = relevance

    if not doc_relevance:
        return []

    # ── Step 4: Query database để lấy uploader_id ─────────────────────────
    if db is None:
        logger.warning("No database session provided — cannot resolve uploaders")
        return []

    doc_ids_list = list(doc_relevance.keys())

    # Lấy documents với uploader_id (chỉ documents đã indexed)
    stmt = (
        select(Document.id, Document.uploader_id)
        .where(
            Document.id.in_(doc_ids_list),
            Document.status == DocumentStatus.INDEXED,
            Document.uploader_id.isnot(None),  # chỉ docs có uploader
        )
    )
    result = await db.execute(stmt)
    doc_uploader_map: dict[int, int] = {
        row.id: row.uploader_id for row in result.all()
    }

    # ── Step 5: Group by uploader_id ────────────────────────────────────────
    # user_id → list of (document_id, relevance)
    user_docs: dict[int, list[tuple[int, float]]] = defaultdict(list)
    for doc_id, relevance in doc_relevance.items():
        uploader_id = doc_uploader_map.get(doc_id)
        if uploader_id is not None:
            user_docs[uploader_id].append((doc_id, relevance))

    if not user_docs:
        logger.debug("No uploaders found for relevant documents")
        return []

    # ── Step 6: Tính aggregate stats per user ─────────────────────────────
    user_stats: dict[int, tuple[int, float]] = {}  # user_id → (doc_count, avg_relevance)
    for user_id, docs in user_docs.items():
        doc_count = len(docs)
        avg_rel = sum(r for _, r in docs) / doc_count
        user_stats[user_id] = (doc_count, avg_rel)

    # ── Step 7: Sort by document_count desc, lấy top_K ─────────────────────
    sorted_users = sorted(user_stats.items(), key=lambda x: x[1][0], reverse=True)
    top_user_ids = [uid for uid, _ in sorted_users[:top_k]]

    if not top_user_ids:
        return []

    # ── Step 8: Join với User + Department để lấy thông tin ───────────────
    stmt = (
        select(User)
        .options(selectinload(User.department))
        .where(User.id.in_(top_user_ids))
    )
    result = await db.execute(stmt)
    users = list(result.scalars().all())

    # Build lookup
    user_map: dict[int, User] = {u.id: u for u in users}

    experts: list[ExpertRecommendation] = []
    for user_id in top_user_ids:
        user = user_map.get(user_id)
        if user is None:
            continue
        doc_count, avg_rel = user_stats[user_id]
        experts.append(ExpertRecommendation(
            user_id=user.id,
            name=user.name,
            email=user.email,
            role=user.role or "Không xác định",
            department=str(user.department.name) if hasattr(user.department, 'name') else (str(user.department) if user.department else "Không xác định"),
            document_count=doc_count,
            avg_relevance=round(avg_rel, 4),
        ))

    logger.info(
        f"Expert recommendation: {len(experts)} experts found "
        f"from {len(user_stats)} unique uploaders in workspace {workspace_id}"
    )
    return experts
