from datetime import datetime
from sqlalchemy import Column, Integer, String, DateTime, ForeignKey
from sqlalchemy.orm import relationship
from backend.app.core.database import Base


class FieldMapping(Base):
    __tablename__ = "field_mappings"

    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    task_id = Column(Integer, ForeignKey("crawler_tasks.id", ondelete="CASCADE"), nullable=False, index=True)
    json_field = Column(String(100), nullable=False)
    web_element = Column(String(200), nullable=False)
    display_name = Column(String(100), nullable=True)
    format_type = Column(String(50), nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)

    task = relationship("CrawlerTask", back_populates="field_mappings")

    def __repr__(self):
        return f"<FieldMapping(id={self.id}, task_id={self.task_id}, json_field='{self.json_field}')>"
