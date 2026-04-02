from sqlalchemy import String, DateTime, Text, Integer, JSON, ForeignKey
from sqlalchemy.orm import Mapped, mapped_column, relationship
from datetime import datetime

from app.core.database import Base


class KnowledgeBase(Base):
    __tablename__ = "knowledge_bases"

    id: Mapped[int] = mapped_column(primary_key=True)
    name: Mapped[str] = mapped_column(String(255))
    description: Mapped[str | None] = mapped_column(Text, nullable=True)
    system_prompt: Mapped[str | None] = mapped_column(Text, nullable=True, default=None)
    kg_language: Mapped[str | None] = mapped_column(String(50), nullable=True, default=None)
    kg_entity_types: Mapped[list | None] = mapped_column(JSON, nullable=True, default=None)
    search_mode: Mapped[str | None] = mapped_column(String(50), nullable=True, default="hybrid")
    suggested_questions: Mapped[list | None] = mapped_column(JSON, nullable=True, default=None)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)

    updated_at: Mapped[datetime] = mapped_column(
        DateTime, default=datetime.utcnow, onupdate=datetime.utcnow
    )

    # Department relationship - mỗi department có 1 workspace duy nhất
    department_id: Mapped[int | None] = mapped_column(
        ForeignKey("departments.id", ondelete="SET NULL"),
        nullable=True,
        unique=True,  # 1:1 relationship - mỗi department chỉ có 1 workspace
        index=True
    )

    # Relationships
    documents: Mapped[list["Document"]] = relationship(
        back_populates="workspace", cascade="all, delete-orphan"
    )
    department: Mapped["Department | None"] = relationship(back_populates="workspace")
