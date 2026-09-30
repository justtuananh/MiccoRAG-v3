from sqlalchemy import String, ForeignKey, DateTime, Date, Integer, Text, Enum, Float, Index
from sqlalchemy.orm import Mapped, mapped_column, relationship
from datetime import datetime, date
import enum

from app.core.database import Base
from app.models.document_version import DocumentVersion  # noqa: F401


class DocumentStatus(str, enum.Enum):
    PENDING = "pending"
    PARSING = "parsing"
    PROCESSING = "processing"
    INDEXING = "indexing"
    INDEXED = "indexed"
    FAILED = "failed"
    REJECTED = "rejected"


class Document(Base):
    __tablename__ = "documents"
    __table_args__ = (Index('ix_documents_workspace_text_fingerprint', 'workspace_id', 'text_fingerprint'),)

    id: Mapped[int] = mapped_column(primary_key=True)
    workspace_id: Mapped[int] = mapped_column(ForeignKey("knowledge_bases.id", ondelete="CASCADE"))
    filename: Mapped[str] = mapped_column(String(255))
    original_filename: Mapped[str] = mapped_column(String(255))
    file_type: Mapped[str] = mapped_column(String(50))
    file_size: Mapped[int] = mapped_column(Integer)
    status: Mapped[DocumentStatus] = mapped_column(
        Enum(DocumentStatus), default=DocumentStatus.PENDING
    )
    chunk_count: Mapped[int] = mapped_column(Integer, default=0)
    error_message: Mapped[str | None] = mapped_column(String(500), nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    updated_at: Mapped[datetime] = mapped_column(
        DateTime, default=datetime.utcnow, onupdate=datetime.utcnow
    )

    # Approvals & Access Control
    uploader_id: Mapped[int | None] = mapped_column(ForeignKey("users.id", ondelete="SET NULL"), nullable=True)
    department_id: Mapped[int | None] = mapped_column(ForeignKey("departments.id", ondelete="SET NULL"), nullable=True)
    visibility: Mapped[str] = mapped_column(String(20), default="department") # "internal" | "department" | "public"
    # - "department": chỉ member trong department đọc
    # - "public": tất cả user đọc
    # - "internal": legacy — treated same as "department"
    approval_status: Mapped[str] = mapped_column(String(20), default="pending") # "pending", "approved", "rejected"
    approval_note: Mapped[str | None] = mapped_column(Text, nullable=True)
    effective_from: Mapped[date | None] = mapped_column(Date, nullable=True)
    effective_until: Mapped[date | None] = mapped_column(Date, nullable=True)
    approved_by: Mapped[int | None] = mapped_column(ForeignKey("users.id", ondelete="SET NULL"), nullable=True)
    approved_at: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)
    deleted_at: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)
    index_cleaned_at: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)
    index_cleanup_attempts: Mapped[int] = mapped_column(Integer, default=0, server_default="0")
    index_cleanup_error: Mapped[str | None] = mapped_column(String(200), nullable=True)
    content_hash: Mapped[str | None] = mapped_column(String(64), nullable=True)
    text_fingerprint: Mapped[str | None] = mapped_column(String(64), nullable=True)
    duplicate_of_document_id: Mapped[int | None] = mapped_column(ForeignKey("documents.id", ondelete="SET NULL"), nullable=True)
    near_duplicate_document_id: Mapped[int | None] = mapped_column(ForeignKey("documents.id", ondelete="SET NULL"), nullable=True)
    duplicate_similarity: Mapped[float | None] = mapped_column(Float, nullable=True)
    knowledge_entry_id: Mapped[int | None] = mapped_column(ForeignKey("knowledge_entries.id", ondelete="SET NULL"), nullable=True)
    supersedes_document_id: Mapped[int | None] = mapped_column(ForeignKey("documents.id", ondelete="SET NULL"), nullable=True)

    issuer: Mapped[str | None] = mapped_column(String(250), nullable=True)
    authority_scope: Mapped[str | None] = mapped_column(String(250), nullable=True)
    authority_rank: Mapped[int | None] = mapped_column(Integer, nullable=True)
    authority_verified_by: Mapped[int | None] = mapped_column(ForeignKey("users.id", ondelete="SET NULL"), nullable=True)
    authority_verified_at: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)

    # NexusRAG fields
    markdown_content: Mapped[str | None] = mapped_column(Text, nullable=True)
    page_count: Mapped[int] = mapped_column(Integer, default=0)
    image_count: Mapped[int] = mapped_column(Integer, default=0)
    table_count: Mapped[int] = mapped_column(Integer, default=0)
    parser_version: Mapped[str | None] = mapped_column(String(50), nullable=True)  # "docling" | "legacy"
    processing_time_ms: Mapped[int] = mapped_column(Integer, default=0)

    # Metadata
    category: Mapped[str | None] = mapped_column(String(100), nullable=True)
    tags: Mapped[str | None] = mapped_column(Text, nullable=True)  # comma-separated
    thumbnail: Mapped[str | None] = mapped_column(String(255), nullable=True)  # filename of thumbnail

    # Relationships
    workspace: Mapped["KnowledgeBase"] = relationship(back_populates="documents")
    images: Mapped[list["DocumentImage"]] = relationship(
        back_populates="document", cascade="all, delete-orphan"
    )
    tables: Mapped[list["DocumentTable"]] = relationship(
        back_populates="document", cascade="all, delete-orphan"
    )
    versions: Mapped[list["DocumentVersion"]] = relationship(
        back_populates="document",
        foreign_keys="DocumentVersion.document_id",
        cascade="all, delete-orphan",
        order_by="DocumentVersion.version_number.desc()",
    )


class DocumentImage(Base):
    __tablename__ = "document_images"

    id: Mapped[int] = mapped_column(primary_key=True)
    document_id: Mapped[int] = mapped_column(ForeignKey("documents.id", ondelete="CASCADE"))
    image_id: Mapped[str] = mapped_column(String(100), unique=True)  # UUID
    page_no: Mapped[int] = mapped_column(Integer, default=0)
    file_path: Mapped[str] = mapped_column(String(500))
    caption: Mapped[str] = mapped_column(Text, default="")
    width: Mapped[int] = mapped_column(Integer, default=0)
    height: Mapped[int] = mapped_column(Integer, default=0)
    mime_type: Mapped[str] = mapped_column(String(50), default="image/png")
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)

    # Relationships
    document: Mapped["Document"] = relationship(back_populates="images")


class DocumentTable(Base):
    __tablename__ = "document_tables"

    id: Mapped[int] = mapped_column(primary_key=True)
    document_id: Mapped[int] = mapped_column(ForeignKey("documents.id", ondelete="CASCADE"))
    table_id: Mapped[str] = mapped_column(String(100), unique=True)
    page_no: Mapped[int] = mapped_column(Integer, default=0)
    content_markdown: Mapped[str] = mapped_column(Text, default="")
    caption: Mapped[str] = mapped_column(Text, default="")
    num_rows: Mapped[int] = mapped_column(Integer, default=0)
    num_cols: Mapped[int] = mapped_column(Integer, default=0)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)

    # Relationships
    document: Mapped["Document"] = relationship(back_populates="tables")
