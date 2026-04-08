from datetime import datetime
from sqlalchemy import Column, Integer, String, DateTime, ForeignKey, Float, JSON
from sqlalchemy.orm import relationship
from backend.app.core.database import Base


class InterceptedResource(Base):
    __tablename__ = "intercepted_resources"

    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    task_id = Column(Integer, ForeignKey("crawler_tasks.id", ondelete="CASCADE"), nullable=False, index=True)
    url = Column(String(1000), nullable=False)
    method = Column(String(10), nullable=False)
    status_code = Column(Integer, nullable=True)
    resource_type = Column(String(50), nullable=True, index=True)
    size = Column(Integer, nullable=True)
    duration = Column(Float, nullable=True)
    headers = Column(JSON, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)

    task = relationship("CrawlerTask", back_populates="intercepted_resources")

    def __repr__(self):
        return f"<InterceptedResource(id={self.id}, task_id={self.task_id}, url='{self.url[:50]}...')>"
