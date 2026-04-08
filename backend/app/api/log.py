import logging
from typing import Optional, List
from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.orm import Session
from sqlalchemy import desc
from backend.app.core.database import get_db
from backend.app.core.dependencies import get_current_active_user
from backend.app.models.user import User
from backend.app.models.task_log import TaskLog
from datetime import datetime

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/logs", tags=["logs"])


@router.get("")
def get_logs(
    task_id: Optional[int] = Query(None, description="Filter by task ID"),
    status: Optional[str] = Query(None, description="Filter by status"),
    level: Optional[str] = Query(None, description="Filter by log level"),
    skip: int = Query(0, ge=0),
    limit: int = Query(50, ge=1, le=200),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    query = db.query(TaskLog)
    
    if task_id:
        query = query.filter(TaskLog.task_id == task_id)
    
    if status:
        query = query.filter(TaskLog.status == status)
    
    query = query.order_by(desc(TaskLog.start_time))
    total = query.count()
    logs = query.offset(skip).limit(limit).all()
    
    return {
        "total": total,
        "skip": skip,
        "limit": limit,
        "logs": [
            {
                "id": log.id,
                "task_id": log.task_id,
                "status": log.status,
                "start_time": log.start_time.isoformat() if log.start_time else None,
                "end_time": log.end_time.isoformat() if log.end_time else None,
                "error_message": log.error_message,
                "debug_info": log.debug_info
            }
            for log in logs
        ]
    }


@router.get("/{log_id}")
def get_log_detail(
    log_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    log = db.query(TaskLog).filter(TaskLog.id == log_id).first()
    if not log:
        raise HTTPException(status_code=404, detail="Log not found")
    
    return {
        "id": log.id,
        "task_id": log.task_id,
        "status": log.status,
        "start_time": log.start_time.isoformat() if log.start_time else None,
        "end_time": log.end_time.isoformat() if log.end_time else None,
        "error_message": log.error_message,
        "debug_info": log.debug_info
    }


@router.delete("")
def clear_logs(
    task_id: Optional[int] = Query(None, description="Clear logs for specific task"),
    before_days: Optional[int] = Query(None, description="Clear logs older than X days"),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    query = db.query(TaskLog)
    
    if task_id:
        query = query.filter(TaskLog.task_id == task_id)
    
    if before_days:
        from datetime import timedelta
        cutoff = datetime.utcnow() - timedelta(days=before_days)
        query = query.filter(TaskLog.start_time < cutoff)
    
    deleted = query.delete()
    db.commit()
    
    return {"message": f"Deleted {deleted} log entries"}
