from sqlalchemy import Column, Integer, String, Float, Text, DateTime, ForeignKey
from sqlalchemy.sql import func
from app.core.database import Base

class SystemChatLog(Base):
    """
    Detailed chat logs for system optimization and performance tracking.
    Stores IP addresses, response times, and RAG methods used.
    """
    __tablename__ = "system_chat_logs"

    id = Column(Integer, primary_key=True, index=True)
    workspace_id = Column(Integer, ForeignKey("knowledge_bases.id", ondelete="CASCADE"), nullable=False)
    ip_address = Column(String(50), nullable=True)
    timestamp = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    response_time = Column(Float, nullable=False)  # in seconds
    question = Column(Text, nullable=False)
    answer = Column(Text, nullable=False)
    method = Column(String(50), nullable=False)  # hybrid, vector_only, graph_only, etc.

    def __repr__(self):
        return f"<SystemChatLog(id={self.id}, workspace_id={self.workspace_id}, method={self.method})>"
