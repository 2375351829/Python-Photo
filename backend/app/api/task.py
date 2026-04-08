from typing import Optional, Dict, Any
from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.orm import Session
from pydantic import BaseModel, Field

from backend.app.core.database import get_db
from backend.app.core.dependencies import get_current_active_user, get_current_admin_user
from backend.app.models.user import User
from backend.app.schemas.task import (
    TaskCreate,
    TaskUpdate,
    TaskResponse,
    TaskListResponse,
    TaskPreviewRequest,
    TaskPreviewResponse,
)
from backend.app.services import task_service

router = APIRouter(prefix="/tasks", tags=["任务管理"])


@router.get("", response_model=TaskListResponse)
def get_tasks(
    page: int = Query(1, ge=1, description="页码"),
    page_size: int = Query(10, ge=1, le=100, description="每页数量"),
    status: Optional[str] = Query(None, description="任务状态筛选"),
    search: Optional[str] = Query(None, description="搜索关键词"),
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db),
):
    skip = (page - 1) * page_size

    if current_user.role == "admin":
        return task_service.get_tasks(
            db=db,
            skip=skip,
            limit=page_size,
            status_filter=status,
            search=search,
        )
    else:
        return task_service.get_tasks(
            db=db,
            user_id=current_user.id,
            skip=skip,
            limit=page_size,
            status_filter=status,
            search=search,
        )


@router.get("/{task_id}", response_model=TaskResponse)
def get_task(
    task_id: int,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db),
):
    if current_user.role == "admin":
        task = task_service.get_task(db, task_id)
    else:
        task = task_service.get_task(db, task_id, current_user.id)

    return TaskResponse(
        id=task.id,
        name=task.name,
        url=task.url,
        target_types=task.target_types,
        rules=task.rules,
        schedule=task.schedule,
        status=task.status,
        debug_mode=task.debug_mode,
        user_id=task.user_id,
        user={
            "id": task.user.id,
            "username": task.user.username,
            "email": task.user.email,
        } if task.user else None,
        created_at=task.created_at,
        updated_at=task.updated_at,
    )


@router.post("", response_model=TaskResponse, status_code=status.HTTP_201_CREATED)
def create_task(
    task_data: TaskCreate,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db),
):
    task = task_service.create_task(db, task_data, current_user.id)

    return TaskResponse(
        id=task.id,
        name=task.name,
        url=task.url,
        target_types=task.target_types,
        rules=task.rules,
        schedule=task.schedule,
        status=task.status,
        debug_mode=task.debug_mode,
        user_id=task.user_id,
        user={
            "id": task.user.id,
            "username": task.user.username,
            "email": task.user.email,
        } if task.user else None,
        created_at=task.created_at,
        updated_at=task.updated_at,
    )


@router.put("/{task_id}", response_model=TaskResponse)
def update_task(
    task_id: int,
    task_data: TaskUpdate,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db),
):
    if current_user.role == "admin":
        task = task_service.update_task(db, task_id, task_data)
    else:
        task = task_service.update_task(db, task_id, task_data, current_user.id)

    return TaskResponse(
        id=task.id,
        name=task.name,
        url=task.url,
        target_types=task.target_types,
        rules=task.rules,
        schedule=task.schedule,
        status=task.status,
        debug_mode=task.debug_mode,
        user_id=task.user_id,
        user={
            "id": task.user.id,
            "username": task.user.username,
            "email": task.user.email,
        } if task.user else None,
        created_at=task.created_at,
        updated_at=task.updated_at,
    )


@router.delete("/{task_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_task(
    task_id: int,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db),
):
    if current_user.role == "admin":
        task_service.delete_task(db, task_id)
    else:
        task_service.delete_task(db, task_id, current_user.id)

    return None


@router.post("/{task_id}/execute", response_model=TaskResponse)
def execute_task(
    task_id: int,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db),
):
    if current_user.role == "admin":
        task = task_service.execute_task(db, task_id)
    else:
        task = task_service.execute_task(db, task_id, current_user.id)

    return TaskResponse(
        id=task.id,
        name=task.name,
        url=task.url,
        target_types=task.target_types,
        rules=task.rules,
        schedule=task.schedule,
        status=task.status,
        debug_mode=task.debug_mode,
        user_id=task.user_id,
        user={
            "id": task.user.id,
            "username": task.user.username,
            "email": task.user.email,
        } if task.user else None,
        created_at=task.created_at,
        updated_at=task.updated_at,
    )


@router.post("/preview", response_model=TaskPreviewResponse)
def preview_rules(
    preview_data: TaskPreviewRequest,
    current_user: User = Depends(get_current_active_user),
):
    result = task_service.preview_rules(
        url=preview_data.url,
        rules=preview_data.rules,
        target_types=preview_data.target_types,
    )

    return TaskPreviewResponse(**result)


class SmartExtractRequest(BaseModel):
    url: str = Field(..., max_length=500, description="目标URL")


class SmartExtractResponse(BaseModel):
    success: bool
    message: str
    content_area: Optional[Dict[str, Any]] = None
    title: Optional[str] = None
    content: Optional[str] = None
    images: list = []
    json_structure: Optional[Dict[str, Any]] = None
    is_json_response: bool = False
    confidence: float = 0.0
    suggested_rules: Dict[str, Any] = {}


@router.post("/smart-extract", response_model=SmartExtractResponse)
def smart_extract(
    extract_data: SmartExtractRequest,
    current_user: User = Depends(get_current_active_user),
):
    result = task_service.smart_extract(url=extract_data.url)
    return SmartExtractResponse(**result)
