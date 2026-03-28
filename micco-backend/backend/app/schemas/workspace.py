"""
Knowledge Base (Workspace) schemas for request/response validation.
"""
from pydantic import BaseModel, Field
from datetime import datetime


class WorkspaceCreate(BaseModel):
    name: str = Field(..., min_length=1, max_length=255)
    description: str | None = None
    kg_language: str | None = None
    kg_entity_types: list[str] | None = None
    search_mode: str | None = "hybrid"


class WorkspaceUpdate(BaseModel):
    name: str | None = Field(default=None, min_length=1, max_length=255)
    description: str | None = None
    system_prompt: str | None = None
    kg_language: str | None = None
    kg_entity_types: list[str] | None = None
    search_mode: str | None = None


class WorkspaceResponse(BaseModel):
    id: int
    name: str
    description: str | None
    system_prompt: str | None = None
    kg_language: str | None = None
    kg_entity_types: list[str] | None = None
    search_mode: str | None = "hybrid"
    document_count: int = 0
    indexed_count: int = 0
    suggested_questions: list[str] | None = None
    created_at: datetime
    updated_at: datetime


    model_config = {"from_attributes": True}


class WorkspaceSummary(BaseModel):
    """Compact summary for dropdown selectors."""
    id: int
    name: str
    document_count: int = 0

    model_config = {"from_attributes": True}
