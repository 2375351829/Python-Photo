from datetime import datetime
from sqlalchemy import Column, Integer, DateTime, ForeignKey, JSON
from sqlalchemy.orm import relationship
from backend.app.core.database import Base


class DebugReport(Base):
    __tablename__ = "debug_reports"

    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    task_id = Column(Integer, ForeignKey("crawler_tasks.id", ondelete="CASCADE"), nullable=False, index=True)
    request_logs = Column(JSON, nullable=True)
    resource_stats = Column(JSON, nullable=True)
    errors = Column(JSON, nullable=True)
    warnings = Column(JSON, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)

    task = relationship("CrawlerTask", back_populates="debug_reports")

    def __repr__(self):
        return f"<DebugReport(id={self.id}, task_id={self.task_id})>"
