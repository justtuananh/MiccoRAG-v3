"""
Knowledge Base (Workspace) CRUD API endpoints.

Workspace 3 loại:
- Personal (visibility=private, owner_id=user_id): chỉ owner truy cập
- Department (visibility=department, department_id=dept_id): member trong dept truy cập
- Public (visibility=public): tất cả user đã đăng nhập truy cập
"""
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func, or_, and_
from sqlalchemy.orm import selectinload

from app.core.deps import get_db
from app.core.exceptions import NotFoundError
from app.core.security import get_current_user
from app.models.user import User
from app.models.knowledge_base import KnowledgeBase
from app.models.document import Document, DocumentStatus
from app.models.department import Department
from app.schemas.workspace import (
    WorkspaceCreate,
    WorkspaceUpdate,
    WorkspaceResponse,
    WorkspaceSummary,
)

router = APIRouter(prefix="/workspaces", tags=["workspaces"])


# ─── Access Helpers ────────────────────────────────────────────────

def _can_access_workspace(user: User, kb: KnowledgeBase) -> bool:
    """Check if user can access this workspace."""
    if user.role == "Admin":
        return True
    if kb.visibility == "public":
        return True
    if kb.visibility == "department" and kb.department_id == user.department_id:
        return True
    if kb.visibility == "private" and kb.owner_id == user.id:
        return True
    return False


def _can_modify_workspace(user: User, kb: KnowledgeBase) -> bool:
    """Check if user can modify this workspace."""
    if user.role == "Admin":
        return True
    # Chỉ owner mới sửa được personal workspace
    if kb.visibility == "private" and kb.owner_id == user.id:
        return True
    # Trưởng phòng sửa được workspace của phòng mình
    if kb.visibility == "department" and kb.department_id == user.department_id and user.role == "Trưởng phòng":
        return True
    return False


def _can_delete_workspace(user: User, kb: KnowledgeBase) -> bool:
    """Check if user can delete this workspace."""
    if user.role == "Admin":
        return True
    # Chỉ owner mới xóa được personal workspace
    if kb.visibility == "private" and kb.owner_id == user.id:
        return True
    # Trưởng phòng xóa được workspace của phòng mình
    if kb.visibility == "department" and kb.department_id == user.department_id and user.role == "Trưởng phòng":
        return True
    return False


# ─── Response Builder ────────────────────────────────────────────────

async def _enrich_response(db: AsyncSession, kb: KnowledgeBase) -> WorkspaceResponse:
    """Build WorkspaceResponse with computed counts."""
    from sqlalchemy import cast, String
    indexed = await db.execute(
        select(func.count(Document.id)).where(
            Document.workspace_id == kb.id,
            cast(Document.status, String).in_(["indexed", "INDEXED"]),
        )
    )
    return WorkspaceResponse(
        id=kb.id,
        name=kb.name,
        description=kb.description,
        visibility=kb.visibility,
        owner_id=kb.owner_id,
        system_prompt=kb.system_prompt,
        kg_language=kb.kg_language,
        kg_entity_types=kb.kg_entity_types,
        search_mode=kb.search_mode,
        indexed_count=indexed.scalar() or 0,
        suggested_questions=kb.suggested_questions,
        department_id=kb.department_id,
        department_name=kb.department.name if kb.department else None,
        created_at=kb.created_at,
        updated_at=kb.updated_at,
    )


# ─── Endpoints ──────────────────────────────────────────────────────

@router.get("", response_model=list[WorkspaceResponse])
async def list_workspaces(
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """
    List workspaces that user can access.
    - Admin: thấy tất cả workspaces
    - User: thấy personal (owner), department, và public workspaces
    """
    if current_user.role == "Admin":
        # Admin thấy tất cả workspaces
        result = await db.execute(
            select(KnowledgeBase)
            .options(selectinload(KnowledgeBase.department))
            .order_by(KnowledgeBase.visibility, KnowledgeBase.updated_at.desc())
        )
        kbs = result.scalars().all()
    else:
        # User: personal (owner) + department (same dept) + public
        result = await db.execute(
            select(KnowledgeBase)
            .options(selectinload(KnowledgeBase.department))
            .where(
                or_(
                    # Personal workspace của chính user
                    and_(
                        KnowledgeBase.visibility == "private",
                        KnowledgeBase.owner_id == current_user.id
                    ),
                    # Department workspace của phòng mình
                    and_(
                        KnowledgeBase.visibility == "department",
                        KnowledgeBase.department_id == current_user.department_id
                    ),
                    # Tất cả public workspaces
                    KnowledgeBase.visibility == "public"
                )
            )
            .order_by(KnowledgeBase.visibility, KnowledgeBase.updated_at.desc())
        )
        kbs = result.scalars().all()

    return [await _enrich_response(db, kb) for kb in kbs]


@router.post("", response_model=WorkspaceResponse, status_code=status.HTTP_201_CREATED)
async def create_workspace(
    body: WorkspaceCreate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """
    Create a new workspace.

    - visibility=private: mọi user đều có thể tạo personal workspace cho mình
    - visibility=department: chỉ Admin/Trưởng phòng mới tạo được
    - visibility=public: chỉ Admin mới tạo được
    """
    # RBAC: ai được tạo workspace loại nào
    # Personal workspace: ai cũng tạo được
    if body.visibility == "public" and current_user.role != "Admin":
        raise HTTPException(
            status_code=403,
            detail="Chỉ Admin mới được tạo workspace công khai",
        )
    if body.visibility == "department" and current_user.role not in ("Admin", "Trưởng phòng"):
        raise HTTPException(
            status_code=403,
            detail="Chỉ Admin hoặc Trưởng phòng mới được tạo workspace phòng ban",
        )

    # Personal workspace: gán owner = current_user
    # Department workspace: gán department_id = department của user
    # Public workspace: không gán department_id
    kb = KnowledgeBase(
        name=body.name,
        description=body.description,
        visibility=body.visibility,
        kg_language=body.kg_language,
        kg_entity_types=body.kg_entity_types,
        search_mode=body.search_mode or "hybrid",
    )

    if body.visibility == "private":
        kb.owner_id = current_user.id
        kb.department_id = None
    elif body.visibility == "department":
        if current_user.department_id is None:
            raise HTTPException(
                status_code=400,
                detail="Bạn không thuộc phòng ban nào để tạo workspace phòng ban",
            )
        kb.owner_id = None
        kb.department_id = current_user.department_id
    else:
        # public
        kb.owner_id = None
        kb.department_id = None

    db.add(kb)
    await db.commit()
    await db.refresh(kb)

    r2 = await db.execute(
        select(KnowledgeBase)
        .options(selectinload(KnowledgeBase.department))
        .where(KnowledgeBase.id == kb.id)
    )
    kb = r2.scalar_one()
    return await _enrich_response(db, kb)


@router.get("/summary", response_model=list[WorkspaceSummary])
async def list_workspace_summaries(
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """
    Compact list of accessible workspaces for dropdown selectors.
    """
    if current_user.role == "Admin":
        result = await db.execute(
            select(KnowledgeBase).order_by(KnowledgeBase.name)
        )
    else:
        result = await db.execute(
            select(KnowledgeBase)
            .where(
                or_(
                    and_(
                        KnowledgeBase.visibility == "private",
                        KnowledgeBase.owner_id == current_user.id
                    ),
                    and_(
                        KnowledgeBase.visibility == "department",
                        KnowledgeBase.department_id == current_user.department_id
                    ),
                    KnowledgeBase.visibility == "public"
                )
            )
            .order_by(KnowledgeBase.name)
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
    current_user: User = Depends(get_current_user),
):
    """Get a workspace by ID. User must have access."""
    result = await db.execute(
        select(KnowledgeBase)
        .options(selectinload(KnowledgeBase.department))
        .where(KnowledgeBase.id == workspace_id)
    )
    kb = result.scalar_one_or_none()
    if kb is None:
        raise NotFoundError("KnowledgeBase", workspace_id)

    if not _can_access_workspace(current_user, kb):
        raise HTTPException(status_code=403, detail="Bạn không có quyền truy cập workspace này")

    return await _enrich_response(db, kb)


@router.put("/{workspace_id}", response_model=WorkspaceResponse)
async def update_workspace(
    workspace_id: int,
    body: WorkspaceUpdate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Update a workspace. User must have modify permission."""
    result = await db.execute(
        select(KnowledgeBase)
        .options(selectinload(KnowledgeBase.department))
        .where(KnowledgeBase.id == workspace_id)
    )
    kb = result.scalar_one_or_none()
    if kb is None:
        raise NotFoundError("KnowledgeBase", workspace_id)

    if not _can_modify_workspace(current_user, kb):
        raise HTTPException(status_code=403, detail="Bạn không có quyền sửa workspace này")

    if body.name is not None:
        kb.name = body.name
    if body.description is not None:
        kb.description = body.description
    if body.visibility is not None:
        # Không cho đổi visibility qua API (phức tạp về RBAC)
        pass
    if body.system_prompt is not None:
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
    current_user: User = Depends(get_current_user),
):
    """Get or generate suggested questions for this workspace."""
    result = await db.execute(
        select(KnowledgeBase)
        .options(selectinload(KnowledgeBase.department))
        .where(KnowledgeBase.id == workspace_id)
    )
    kb = result.scalar_one_or_none()
    if kb is None:
        raise NotFoundError("KnowledgeBase", workspace_id)

    if not _can_access_workspace(current_user, kb):
        raise HTTPException(status_code=403, detail="Bạn không có quyền truy cập workspace này")

    if kb.suggested_questions:
        return kb.suggested_questions

    from app.services.suggested_questions_service import generate_suggested_questions
    return await generate_suggested_questions(db, workspace_id)


@router.delete("/{workspace_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_workspace(
    workspace_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Delete a workspace and all its data."""
    result = await db.execute(
        select(KnowledgeBase).where(KnowledgeBase.id == workspace_id)
    )
    kb = result.scalar_one_or_none()
    if kb is None:
        raise NotFoundError("KnowledgeBase", workspace_id)

    if not _can_delete_workspace(current_user, kb):
        raise HTTPException(status_code=403, detail="Bạn không có quyền xóa workspace này")

    # Clean up vector store
    try:
        from app.services.vector_store import get_vector_store
        vs = get_vector_store(workspace_id)
        vs.delete_collection()
    except Exception:
        pass

    # Clean up KG data
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
