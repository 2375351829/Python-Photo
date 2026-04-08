import re
import math
import asyncio
from datetime import datetime
from typing import Optional, List, Dict, Any

from sqlalchemy.orm import Session
from fastapi import HTTPException, status

from backend.app.models.task import CrawlerTask
from backend.app.models.user import User
from backend.app.schemas.task import TaskCreate, TaskUpdate, TaskListResponse, TaskResponse
from backend.app.services.smart_extract_service import smart_extract_service


def validate_url(url: str) -> bool:
    url_pattern = re.compile(
        r"^https?://"
        r"(?:(?:[A-Z0-9](?:[A-Z0-9-]{0,61}[A-Z0-9])?\.)+[A-Z]{2,6}\.?|"
        r"localhost|"
        r"\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3})"
        r"(?::\d+)?"
        r"(?:/?|[/?]\S+)$",
        re.IGNORECASE,
    )
    return bool(url_pattern.match(url))


def create_task(db: Session, task_data: TaskCreate, user_id: int) -> CrawlerTask:
    if not validate_url(task_data.url):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="URL格式无效",
        )

    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="用户不存在",
        )

    new_task = CrawlerTask(
        name=task_data.name,
        url=task_data.url,
        target_types=task_data.target_types,
        rules=task_data.rules,
        schedule=task_data.schedule,
        debug_mode=task_data.debug_mode,
        user_id=user_id,
        status="pending",
    )

    db.add(new_task)
    db.commit()
    db.refresh(new_task)

    return new_task


def get_task(db: Session, task_id: int, user_id: Optional[int] = None) -> CrawlerTask:
    query = db.query(CrawlerTask).filter(CrawlerTask.id == task_id)

    if user_id is not None:
        query = query.filter(CrawlerTask.user_id == user_id)

    task = query.first()

    if not task:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="任务不存在",
        )

    return task


def get_tasks(
    db: Session,
    user_id: Optional[int] = None,
    skip: int = 0,
    limit: int = 10,
    status_filter: Optional[str] = None,
    search: Optional[str] = None,
) -> TaskListResponse:
    query = db.query(CrawlerTask)

    if user_id is not None:
        query = query.filter(CrawlerTask.user_id == user_id)

    if status_filter:
        query = query.filter(CrawlerTask.status == status_filter)

    if search:
        search_pattern = f"%{search}%"
        query = query.filter(
            (CrawlerTask.name.ilike(search_pattern)) |
            (CrawlerTask.url.ilike(search_pattern))
        )

    total = query.count()

    tasks = query.order_by(CrawlerTask.created_at.desc()).offset(skip).limit(limit).all()

    task_responses = []
    for task in tasks:
        task_dict = {
            "id": task.id,
            "name": task.name,
            "url": task.url,
            "target_types": task.target_types,
            "rules": task.rules,
            "schedule": task.schedule,
            "status": task.status,
            "debug_mode": task.debug_mode,
            "user_id": task.user_id,
            "user": {
                "id": task.user.id,
                "username": task.user.username,
                "email": task.user.email,
            } if task.user else None,
            "created_at": task.created_at,
            "updated_at": task.updated_at,
        }
        task_responses.append(TaskResponse(**task_dict))

    pages = math.ceil(total / limit) if limit > 0 else 0
    page = (skip // limit) + 1 if limit > 0 else 1

    return TaskListResponse(
        items=task_responses,
        total=total,
        page=page,
        page_size=limit,
        pages=pages,
    )


def update_task(db: Session, task_id: int, task_data: TaskUpdate, user_id: Optional[int] = None) -> CrawlerTask:
    task = get_task(db, task_id, user_id)

    update_data = task_data.model_dump(exclude_unset=True)

    if "url" in update_data and update_data["url"]:
        if not validate_url(update_data["url"]):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="URL格式无效",
            )

    for field, value in update_data.items():
        setattr(task, field, value)

    task.updated_at = datetime.utcnow()

    db.commit()
    db.refresh(task)

    return task


def delete_task(db: Session, task_id: int, user_id: Optional[int] = None) -> bool:
    task = get_task(db, task_id, user_id)

    db.delete(task)
    db.commit()

    return True


def execute_task(db: Session, task_id: int, user_id: Optional[int] = None) -> CrawlerTask:
    task = get_task(db, task_id, user_id)

    if task.status == "running":
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="任务正在运行中",
        )

    task.status = "running"
    task.updated_at = datetime.utcnow()

    db.commit()
    db.refresh(task)

    return task


def preview_rules(url: str, rules: Optional[Dict[str, Any]], target_types: Optional[List[str]]) -> Dict[str, Any]:
    try:
        loop = asyncio.get_event_loop()
    except RuntimeError:
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
    
    result = loop.run_until_complete(
        smart_extract_service.preview_rules(url, rules or {}, target_types)
    )
    
    return {
        "url": result.url,
        "matched_resources": result.matched_items,
        "total_matched": result.total_count,
        "preview_time": result.preview_time,
        "error": result.error,
    }


async def smart_extract_async(url: str) -> Dict[str, Any]:
    result = await smart_extract_service.smart_extract(url)
    
    return {
        "success": result.success,
        "message": result.message,
        "content_area": result.content_area,
        "title": result.title,
        "content": result.content,
        "images": result.images,
        "json_structure": result.json_structure,
        "is_json_response": result.is_json_response,
        "confidence": result.confidence,
        "suggested_rules": result.suggested_rules,
    }


def smart_extract(url: str) -> Dict[str, Any]:
    try:
        loop = asyncio.get_event_loop()
    except RuntimeError:
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
    
    return loop.run_until_complete(smart_extract_async(url))
