from __future__ import annotations

import uuid

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.deps import get_db
from app.core.security import get_current_user
from app.models.user import User
from app.models.chat_message import ChatMessage as PersistedChatMessage
from app.schemas.rag import ChatRequest, ChatMessageSchema
from app.schemas.compat import LegacyChatMessageResponse, LegacyChatSendRequest
from app.api.rag import chat_with_documents
from app.api_compat.utils import get_or_create_default_workspace

router = APIRouter(prefix="/api/chat", tags=["Chat Assistant"])


def _map_sources_to_legacy_strings(sources) -> list[str]:
    labels = []
    for s in sources or []:
        idx = getattr(s, "index", None) or (s.get("index") if isinstance(s, dict) else None)
        doc_id = getattr(s, "document_id", None) or (s.get("document_id") if isinstance(s, dict) else None)
        page_no = getattr(s, "page_no", None) or (s.get("page_no") if isinstance(s, dict) else None)
        source_type = getattr(s, "source_type", None) or (s.get("source_type") if isinstance(s, dict) else None)

        chunk = f"[{idx}]" if idx else ""
        doc = f"doc:{doc_id}" if doc_id else "doc:unknown"
        page = f" p.{page_no}" if page_no else ""
        stype = f" ({source_type})" if source_type else ""
        labels.append(f"{doc}{page} {chunk}{stype}".strip())
    return labels


@router.post("/send", response_model=LegacyChatMessageResponse)
async def send_message(
    req: LegacyChatSendRequest,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    workspace = await get_or_create_default_workspace(db)

    history_stmt = (
        select(PersistedChatMessage)
        .where(PersistedChatMessage.workspace_id == workspace.id)
        .order_by(PersistedChatMessage.created_at.asc())
        .limit(30)
    )
    rows = (await db.execute(history_stmt)).scalars().all()
    history = [
        ChatMessageSchema(role="user" if m.role == "user" else "assistant", content=m.content)
        for m in rows
    ]

    chat_req = ChatRequest(
        message=req.message,
        history=history,
        document_ids=req.document_ids,
    )

    try:
        rag_resp = await chat_with_documents(workspace.id, chat_req, db)
    except HTTPException:
        raise
    except Exception as exc:  # pragma: no cover - fallback for runtime errors
        raise HTTPException(status_code=500, detail=f"Chat processing failed: {exc}")

    return LegacyChatMessageResponse(
        id=0,
        role="ai",
        content=rag_resp.answer,
        sources=_map_sources_to_legacy_strings(rag_resp.sources),
        graph_data=None,
    )


@router.get("/history", response_model=list[LegacyChatMessageResponse])
async def get_history(
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    workspace = await get_or_create_default_workspace(db)

    stmt = (
        select(PersistedChatMessage)
        .where(PersistedChatMessage.workspace_id == workspace.id)
        .order_by(PersistedChatMessage.created_at.asc())
    )
    rows = (await db.execute(stmt)).scalars().all()

    out: list[LegacyChatMessageResponse] = []
    for msg in rows:
        role = "user" if msg.role == "user" else "ai"
        out.append(
            LegacyChatMessageResponse(
                id=msg.id,
                role=role,
                content=msg.content,
                sources=_map_sources_to_legacy_strings(msg.sources or []),
                graph_data=None,
            )
        )

    return out
