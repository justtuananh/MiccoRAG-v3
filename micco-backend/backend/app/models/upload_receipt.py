from datetime import datetime
from sqlalchemy import String, Integer, DateTime, JSON, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column
from app.core.database import Base


class UploadReceipt(Base):
    __tablename__='upload_receipts'
    __table_args__=(UniqueConstraint('actor_id','route','request_key',name='uq_upload_receipt_request'),)
    id: Mapped[int]=mapped_column(primary_key=True)
    actor_id: Mapped[int]=mapped_column(Integer,nullable=False)
    route: Mapped[str]=mapped_column(String(100),nullable=False)
    request_key: Mapped[str]=mapped_column(String(128),nullable=False)
    payload_hash: Mapped[str]=mapped_column(String(64),nullable=False)
    response: Mapped[dict | list]=mapped_column(JSON,nullable=False)
    created_at: Mapped[datetime]=mapped_column(DateTime,default=datetime.utcnow)
