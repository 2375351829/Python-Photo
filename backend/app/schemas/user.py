from datetime import datetime
from typing import Optional
from pydantic import BaseModel, Field, EmailStr


class UserBase(BaseModel):
    username: str = Field(..., min_length=3, max_length=50, description="用户名")
    email: str = Field(..., max_length=100, description="邮箱地址")


class UserCreate(UserBase):
    password: str = Field(..., min_length=6, max_length=100, description="密码")


class UserUpdate(BaseModel):
    username: Optional[str] = Field(None, min_length=3, max_length=50, description="用户名")
    email: Optional[str] = Field(None, max_length=100, description="邮箱地址")
    password: Optional[str] = Field(None, min_length=6, max_length=100, description="新密码")
    role: Optional[str] = Field(None, description="用户角色")
    is_active: Optional[bool] = Field(None, description="是否激活")


class UserResponse(BaseModel):
    id: int
    username: str
    email: str
    role: str
    is_active: bool
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True
