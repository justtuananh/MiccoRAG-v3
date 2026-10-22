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


async def _verify_workspace_access(workspace_id: int, db: AsyncSession, current_user: User) -> KnowledgeBase:
    from app.api.rag import verify_workspace_access
    return await verify_workspace_access(workspace_id, db, current_user)


async def _get_allowed_document_ids(db: AsyncSession, current_user: User, workspace_id: int) -> list[int]:
    from app.api.rag import get_allowed_document_ids
    return await get_allowed_document_ids(db, current_user, workspace_id)


@router.get(
    "/recommend/{workspace_id}",
    response_model=ExpertRecommendResponse,
    summary="Đề xuất người liên hệ tài liệu",
    description=(
        "Đề xuất top-K người cung cấp tài liệu liên quan; chưa xác nhận chuyên môn "
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
    Đề xuất người liên hệ tài liệu trong một workspace dựa trên câu hỏi.

    - **workspace_id**: ID của workspace
    - **query**: Câu hỏi của người dùng (required)
    - **top_k**: Số lượng chuyên gia (1-10, default 3)

    Returns danh sách ExpertRecommendation đã được sort theo:
    1. Mức liên quan trung bình giảm dần
    2. Số tài liệu liên quan giảm dần
    3. ID người dùng tăng dần khi đồng điểm
    """
    # Verify workspace exists
    await _verify_workspace_access(workspace_id, db, current_user)

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
