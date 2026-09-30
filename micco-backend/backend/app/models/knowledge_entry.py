from __future__ import annotations

from datetime import datetime, date

from sqlalchemy import String, Integer, DateTime, Date, ForeignKey, Text
from sqlalchemy.dialects.postgresql import JSON
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.database import Base


class KnowledgeEntry(Base):
    __tablename__ = "knowledge_entries"

    id: Mapped[int] = mapped_column(primary_key=True, index=True)
    title: Mapped[str] = mapped_column(String(500), nullable=False)
    content_html: Mapped[str] = mapped_column(Text, nullable=False)
    content_text: Mapped[str] = mapped_column(Text, nullable=False)
    category: Mapped[str] = mapped_column(String(100), nullable=False, default="Chung")
    tags: Mapped[list] = mapped_column(JSON, nullable=False, default=list)
    owner_id: Mapped[int] = mapped_column(Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    department_id: Mapped[int | None] = mapped_column(Integer, ForeignKey("departments.id", ondelete="SET NULL"), nullable=True)
    visibility: Mapped[str] = mapped_column(String(20), nullable=False, default="internal")
    approval_status: Mapped[str] = mapped_column(String(20), nullable=False, default="pending_dept")
    approval_note: Mapped[str | None] = mapped_column(Text, nullable=True)
    effective_from: Mapped[date | None] = mapped_column(Date, nullable=True)
    effective_until: Mapped[date | None] = mapped_column(Date, nullable=True)
    approved_by: Mapped[int | None] = mapped_column(ForeignKey("users.id", ondelete="SET NULL"), nullable=True)
    approved_at: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)
    deleted_at: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)
    supersedes_entry_id: Mapped[int | None] = mapped_column(ForeignKey("knowledge_entries.id", ondelete="SET NULL"), nullable=True)
    status: Mapped[str] = mapped_column(String(20), nullable=False, default="Active")
    ingest_status: Mapped[str | None] = mapped_column(String(20), nullable=True, default="pending")
    ingest_error: Mapped[str | None] = mapped_column(Text, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    updated_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    owner: Mapped["User"] = relationship(back_populates="knowledge_entries", foreign_keys=[owner_id])
    department: Mapped["Department | None"] = relationship()
