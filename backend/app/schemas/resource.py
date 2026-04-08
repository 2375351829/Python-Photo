from datetime import datetime
from typing import Optional, List, Dict, Any
from pydantic import BaseModel, Field


class ResourceBase(BaseModel):
    url: str = Field(..., max_length=1000, description="资源URL")
    method: str = Field(default="GET", max_length=10, description="请求方法")
    resource_type: Optional[str] = Field(None, max_length=50, description="资源类型")
    status_code: Optional[int] = Field(None, description="HTTP状态码")
    size: Optional[int] = Field(None, description="资源大小（字节）")
    duration: Optional[float] = Field(None, description="请求耗时（秒）")
    headers: Optional[Dict[str, Any]] = Field(None, description="请求/响应头")


class ResourceCreate(ResourceBase):
    task_id: int = Field(..., description="任务ID")


class ResourceResponse(ResourceBase):
    id: int
    task_id: int
    created_at: datetime

    class Config:
        from_attributes = True


class ResourceListResponse(BaseModel):
    items: List[ResourceResponse]
    total: int
    page: int
    page_size: int
    pages: int


class ResourceStatsResponse(BaseModel):
    total_requests: int = Field(..., description="总请求数")
    blocked_requests: int = Field(..., description="被拦截的请求数")
    successful_requests: int = Field(..., description="成功的请求数")
    failed_requests: int = Field(..., description="失败的请求数")
    total_size_bytes: int = Field(..., description="总大小（字节）")
    total_response_time: float = Field(..., description="总响应时间（秒）")
    average_response_time: float = Field(..., description="平均响应时间（秒）")
    resource_types: Dict[str, int] = Field(..., description="资源类型分布")
    domains: Dict[str, int] = Field(..., description="域名分布")
    status_codes: Dict[int, int] = Field(..., description="状态码分布")


class ResourceFilterRequest(BaseModel):
    url_pattern: Optional[str] = Field(None, description="URL模式（正则表达式）")
    resource_types: Optional[List[str]] = Field(None, description="资源类型列表")
    domains: Optional[List[str]] = Field(None, description="域名列表")
    domain_mode: Optional[str] = Field("blacklist", description="域名过滤模式：blacklist/whitelist")
    status_codes: Optional[List[int]] = Field(None, description="状态码列表")
    min_size: Optional[int] = Field(None, description="最小大小（字节）")
    max_size: Optional[int] = Field(None, description="最大大小（字节）")


class ReplayRequest(BaseModel):
    url: str = Field(..., max_length=1000, description="请求URL")
    method: str = Field(default="GET", max_length=10, description="请求方法")
    headers: Optional[Dict[str, str]] = Field(None, description="请求头")
    body: Optional[str] = Field(None, description="请求体")


class ReplayResponse(BaseModel):
    status_code: int = Field(..., description="响应状态码")
    headers: Dict[str, str] = Field(..., description="响应头")
    body: Optional[str] = Field(None, description="响应体")
    duration: float = Field(..., description="请求耗时（秒）")
    size: int = Field(..., description="响应大小（字节）")
