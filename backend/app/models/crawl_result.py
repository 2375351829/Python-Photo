from datetime import datetime
from sqlalchemy import Column, Integer, String, DateTime, ForeignKey, JSON
from sqlalchemy.orm import relationship
from backend.app.core.database import Base


class CrawlResult(Base):
    __tablename__ = "crawl_results"

    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    task_id = Column(Integer, ForeignKey("crawler_tasks.id", ondelete="CASCADE"), nullable=False, index=True)
    resource_type = Column(String(20), nullable=False, index=True)
    data = Column(JSON, nullable=True)
    file_path = Column(String(500), nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)

    task = relationship("CrawlerTask", back_populates="results")

    def __repr__(self):
        return f"<CrawlResult(id={self.id}, task_id={self.task_id}, resource_type='{self.resource_type}')>"
