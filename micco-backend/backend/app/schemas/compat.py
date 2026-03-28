from __future__ import annotations

from datetime import datetime
from pydantic import BaseModel


class RegisterRequest(BaseModel):
    name: str
    email: str
    password: str
    department_id: int | None = None


class LoginRequest(BaseModel):
    email: str
    password: str


class TokenResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"


class UserResponse(BaseModel):
    id: int
    name: str
    email: str
    role: str
    department_id: int | None = None
    department_name: str | None = None
    avatar: str | None = None


class UserUpdateRequest(BaseModel):
    name: str | None = None
    password: str | None = None


class DepartmentResponse(BaseModel):
    id: int
    name: str
    description: str | None = None


class LegacyChatSendRequest(BaseModel):
    message: str
    document_ids: list[int] = []


class LegacyChatMessageResponse(BaseModel):
    id: int
    role: str
    content: str
    sources: list[str] = []
    graph_data: dict | None = None


class KnowledgeCreateRequest(BaseModel):
    title: str
    content_html: str
    content_text: str
    category: str = "Chung"
    tags: list[str] = []
    visibility: str = "internal"
    status: str = "Active"


class KnowledgeUpdateRequest(BaseModel):
    title: str | None = None
    content_html: str | None = None
    content_text: str | None = None
    category: str | None = None
    tags: list[str] | None = None
    visibility: str | None = None
    status: str | None = None


class LegacyDocumentVersionResponse(BaseModel):
    id: int
    document_id: int
    version_number: int
    version_label: str
    size: str | None = None
    change_note: str | None = None
    created_by_name: str = "System"
    is_current: bool = True
    created_at: datetime
