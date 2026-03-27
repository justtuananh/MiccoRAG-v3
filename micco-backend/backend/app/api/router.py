"""
NexusRAG API router — aggregates workspace, document, and RAG endpoints.
"""
from fastapi import APIRouter

from app.api.workspaces import router as workspaces_router
from app.api.documents import router as documents_router
from app.api.rag import router as rag_router
from app.api.config import router as config_router

api_router = APIRouter()
api_router.include_router(workspaces_router)
api_router.include_router(documents_router)
api_router.include_router(rag_router)
api_router.include_router(config_router)
