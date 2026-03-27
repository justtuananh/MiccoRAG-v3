from app.api_compat.auth import router as auth_router
from app.api_compat.admin import router as admin_router
from app.api_compat.dashboard import router as dashboard_router
from app.api_compat.documents import router as documents_router
from app.api_compat.chat import router as chat_router
from app.api_compat.approvals import router as approvals_router
from app.api_compat.knowledge import router as knowledge_router

__all__ = [
    "auth_router",
    "admin_router",
    "dashboard_router",
    "documents_router",
    "chat_router",
    "approvals_router",
    "knowledge_router",
]
