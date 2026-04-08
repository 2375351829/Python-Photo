from datetime import datetime
from sqlalchemy import Column, Integer, String, Boolean, DateTime, ForeignKey, JSON
from sqlalchemy.orm import relationship
from backend.app.core.database import Base


class CrawlerTask(Base):
    __tablename__ = "crawler_tasks"

    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    name = Column(String(100), nullable=False, index=True)
    url = Column(String(500), nullable=False)
    target_types = Column(JSON, nullable=True)
    rules = Column(JSON, nullable=True)
    schedule = Column(String(100), nullable=True)
    status = Column(String(20), default="pending", nullable=False, index=True)
    debug_mode = Column(Boolean, default=False, nullable=False)
    user_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)

    user = relationship("User", back_populates="tasks")
    logs = relationship("TaskLog", back_populates="task", cascade="all, delete-orphan")
    results = relationship("CrawlResult", back_populates="task", cascade="all, delete-orphan")
    intercepted_resources = relationship("InterceptedResource", back_populates="task", cascade="all, delete-orphan")
    debug_reports = relationship("DebugReport", back_populates="task", cascade="all, delete-orphan")
    field_mappings = relationship("FieldMapping", back_populates="task", cascade="all, delete-orphan")

    def __repr__(self):
        return f"<CrawlerTask(id={self.id}, name='{self.name}', status='{self.status}')>"
