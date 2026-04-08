from datetime import datetime
from typing import Optional, List, Any, Dict
from pydantic import BaseModel, Field, field_validator
import re


class TaskBase(BaseModel):
    name: str = Field(..., min_length=1, max_length=100, description="任务名称")
    url: str = Field(..., max_length=500, description="目标URL")
    target_types: Optional[List[str]] = Field(default=None, description="目标资源类型列表")
    rules: Optional[Dict[str, Any]] = Field(default=None, description="爬取规则配置")
    schedule: Optional[str] = Field(default=None, max_length=100, description="定时任务表达式")
    debug_mode: bool = Field(default=False, description="调试模式")

    @field_validator("url")
    @classmethod
    def validate_url(cls, v: str) -> str:
        url_pattern = re.compile(
            r"^https?://"
            r"(?:(?:[A-Z0-9](?:[A-Z0-9-]{0,61}[A-Z0-9])?\.)+[A-Z]{2,6}\.?|"
            r"localhost|"
            r"\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3})"
            r"(?::\d+)?"
            r"(?:/?|[/?]\S+)$",
            re.IGNORECASE,
        )
        if not url_pattern.match(v):
            raise ValueError("URL格式无效，必须是有效的HTTP/HTTPS URL")
        return v


class TaskCreate(TaskBase):
    pass


class TaskUpdate(BaseModel):
    name: Optional[str] = Field(None, min_length=1, max_length=100, description="任务名称")
    url: Optional[str] = Field(None, max_length=500, description="目标URL")
    target_types: Optional[List[str]] = Field(None, description="目标资源类型列表")
    rules: Optional[Dict[str, Any]] = Field(None, description="爬取规则配置")
    schedule: Optional[str] = Field(None, max_length=100, description="定时任务表达式")
    debug_mode: Optional[bool] = Field(None, description="调试模式")
    status: Optional[str] = Field(None, description="任务状态")

    @field_validator("url")
    @classmethod
    def validate_url(cls, v: Optional[str]) -> Optional[str]:
        if v is None:
            return v
        url_pattern = re.compile(
            r"^https?://"
            r"(?:(?:[A-Z0-9](?:[A-Z0-9-]{0,61}[A-Z0-9])?\.)+[A-Z]{2,6}\.?|"
            r"localhost|"
            r"\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3})"
            r"(?::\d+)?"
            r"(?:/?|[/?]\S+)$",
            re.IGNORECASE,
        )
        if not url_pattern.match(v):
            raise ValueError("URL格式无效，必须是有效的HTTP/HTTPS URL")
        return v

    @field_validator("status")
    @classmethod
    def validate_status(cls, v: Optional[str]) -> Optional[str]:
        if v is None:
            return v
        valid_statuses = ["pending", "running", "completed", "failed", "paused"]
        if v not in valid_statuses:
            raise ValueError(f"状态必须是以下之一: {', '.join(valid_statuses)}")
        return v


class UserInfo(BaseModel):
    id: int
    username: str
    email: str

    class Config:
        from_attributes = True


class TaskResponse(BaseModel):
    id: int
    name: str
    url: str
    target_types: Optional[List[str]] = None
    rules: Optional[Dict[str, Any]] = None
    schedule: Optional[str] = None
    status: str
    debug_mode: bool
    user_id: int
    user: Optional[UserInfo] = None
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


class TaskListResponse(BaseModel):
    items: List[TaskResponse]
    total: int
    page: int
    page_size: int
    pages: int


class TaskPreviewRequest(BaseModel):
    url: str = Field(..., max_length=500, description="目标URL")
    rules: Optional[Dict[str, Any]] = Field(default=None, description="爬取规则配置")
    target_types: Optional[List[str]] = Field(default=None, description="目标资源类型列表")

    @field_validator("url")
    @classmethod
    def validate_url(cls, v: str) -> str:
        url_pattern = re.compile(
            r"^https?://"
            r"(?:(?:[A-Z0-9](?:[A-Z0-9-]{0,61}[A-Z0-9])?\.)+[A-Z]{2,6}\.?|"
            r"localhost|"
            r"\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3})"
            r"(?::\d+)?"
            r"(?:/?|[/?]\S+)$",
            re.IGNORECASE,
        )
        if not url_pattern.match(v):
            raise ValueError("URL格式无效，必须是有效的HTTP/HTTPS URL")
        return v


class TaskPreviewResponse(BaseModel):
    url: str
    matched_resources: List[Dict[str, Any]] = Field(default_factory=list)
    total_matched: int = 0
    preview_time: datetime = Field(default_factory=datetime.utcnow)
