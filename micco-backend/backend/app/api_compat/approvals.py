from __future__ import annotations

from fastapi import APIRouter, Depends
from app.core.security import get_current_user
from app.models.user import User

router = APIRouter(prefix="/api/approvals", tags=["Approvals"])


@router.get("/count")
async def pending_count(current_user: User = Depends(get_current_user)):
    if current_user.role not in ("Admin", "Trưởng phòng"):
        return {"count": 0}
    return {"count": 0}


@router.get("/pending")
async def list_pending(current_user: User = Depends(get_current_user)):
    _ = current_user
    return {"documents": [], "knowledge": []}


@router.post("/documents/{doc_id}/approve")
async def approve_document(doc_id: int, current_user: User = Depends(get_current_user)):
    _ = current_user
    return {"message": "Đã phê duyệt", "id": doc_id}


@router.post("/documents/{doc_id}/reject")
async def reject_document(doc_id: int, current_user: User = Depends(get_current_user)):
    _ = current_user
    return {"message": "Đã từ chối", "id": doc_id}


@router.post("/knowledge/{entry_id}/approve")
async def approve_knowledge(entry_id: int, current_user: User = Depends(get_current_user)):
    _ = current_user
    return {"message": "Đã phê duyệt", "id": entry_id}


@router.post("/knowledge/{entry_id}/reject")
async def reject_knowledge(entry_id: int, current_user: User = Depends(get_current_user)):
    _ = current_user
    return {"message": "Đã từ chối", "id": entry_id}
