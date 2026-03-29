"""
Expert Recommendation API
==========================
Endpoint để đề xuất chuyên gia (users đã upload nhiều tài liệu liên quan nhất)
dựa trên câu hỏi của người dùng trong 1 workspace cụ thể.
"""
from fastapi import APIRouter, Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.deps import get_db
from app.core.security import get_current_user
from app.models.user import User
from app.models.knowledge_base import KnowledgeBase
from app.schemas.rag import ExpertRecommendResponse
from app.services.expert_recommendation import recommend_experts

router = APIRouter(prefix="/expert", tags=["expert"])


async def _verify_workspace_access(
    workspace_id: int,
    db: AsyncSession,
) -> KnowledgeBase:
    """Verify knowledge base exists."""
    from sqlalchemy import select
    result = await db.execute(select(KnowledgeBase).where(KnowledgeBase.id == workspace_id))
    kb = result.scalar_one_or_none()
    if kb is None:
        from app.core.exceptions import NotFoundError
        raise NotFoundError("KnowledgeBase", workspace_id)
    return kb


async def _get_allowed_document_ids(
    db: AsyncSession,
    current_user: User,
    workspace_id: int,
) -> list[int]:
    """Get list of document IDs that the user has access to."""
    from sqlalchemy import select, or_
    from app.models.document import Document, DocumentStatus

    stmt = select(Document.id).where(
        Document.workspace_id == workspace_id,
        Document.status == DocumentStatus.INDEXED,
        Document.approval_status == "approved",
    )

    if current_user.role != "Admin":
        stmt = stmt.where(
            or_(
                Document.visibility == "public",
                Document.department_id == current_user.department_id,
            )
        )

    result = await db.execute(stmt)
    return [row[0] for row in result.all()]


@router.get(
    "/recommend/{workspace_id}",
    response_model=ExpertRecommendResponse,
    summary="Đề xuất chuyên gia",
    description=(
        "Đề xuất top-K chuyên gia (users đã upload nhiều tài liệu liên quan nhất) "
        "dựa trên câu hỏi của người dùng trong workspace cụ thể. "
        "Sử dụng vector search để tìm documents liên quan, sau đó group theo uploader."
    ),
)
async def get_expert_recommendations(
    workspace_id: int,
    query: str = Query(..., min_length=1, max_length=1000, description="Câu hỏi của người dùng"),
    top_k: int = Query(default=3, ge=1, le=10, description="Số lượng chuyên gia cần trả về"),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """
    Đề xuất chuyên gia trong một workspace dựa trên câu hỏi.

    - **workspace_id**: ID của workspace
    - **query**: Câu hỏi của người dùng (required)
    - **top_k**: Số lượng chuyên gia (1-10, default 3)

    Returns danh sách ExpertRecommendation đã được sort theo:
    1. Số lượng document liên quan (desc)
    2. Avg relevance (desc)
    """
    # Verify workspace exists
    await _verify_workspace_access(workspace_id, db)

    # Get allowed document IDs for this user
    allowed_ids = await _get_allowed_document_ids(db, current_user, workspace_id)

    if not allowed_ids:
        return ExpertRecommendResponse(experts=[])

    # Get expert recommendations
    experts = await recommend_experts(
        workspace_id=workspace_id,
        query=query,
        top_k=top_k,
        db=db,
        allowed_document_ids=allowed_ids,
    )

    return ExpertRecommendResponse(experts=experts)
