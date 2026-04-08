from typing import Optional, List
from fastapi import APIRouter, Depends, HTTPException, status, Query
from fastapi.responses import StreamingResponse
from sqlalchemy.orm import Session
from sqlalchemy import and_, or_, desc
import csv
import json
import io
from datetime import datetime

from backend.app.core.database import get_db
from backend.app.core.dependencies import get_current_active_user
from backend.app.models.user import User
from backend.app.models.crawl_result import CrawlResult
from backend.app.models.task import CrawlerTask

router = APIRouter(prefix="/results", tags=["results"])


@router.get("")
def get_results(
    task_id: Optional[int] = Query(None, description="Filter by task ID"),
    resource_type: Optional[str] = Query(None, description="Filter by resource type"),
    search: Optional[str] = Query(None, description="Search in data"),
    skip: int = Query(0, ge=0),
    limit: int = Query(50, ge=1, le=200),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    query = db.query(CrawlResult)
    
    if task_id:
        query = query.filter(CrawlResult.task_id == task_id)
    
    if resource_type:
        query = query.filter(CrawlResult.resource_type == resource_type)
    
    if search:
        query = query.filter(CrawlResult.data.contains(search))
    
    query = query.order_by(desc(CrawlResult.created_at))
    total = query.count()
    results = query.offset(skip).limit(limit).all()
    
    return {
        "total": total,
        "skip": skip,
        "limit": limit,
        "results": [
            {
                "id": r.id,
                "task_id": r.task_id,
                "resource_type": r.resource_type,
                "data": r.data,
                "file_path": r.file_path,
                "created_at": r.created_at.isoformat() if r.created_at else None
            }
            for r in results
        ]
    }


@router.get("/{result_id}")
def get_result_detail(
    result_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    result = db.query(CrawlResult).filter(CrawlResult.id == result_id).first()
    if not result:
        raise HTTPException(status_code=404, detail="Result not found")
    
    return {
        "id": result.id,
        "task_id": result.task_id,
        "resource_type": result.resource_type,
        "data": result.data,
        "file_path": result.file_path,
        "created_at": result.created_at.isoformat() if result.created_at else None
    }


@router.get("/export/csv")
def export_csv(
    task_id: int = Query(..., description="Task ID to export"),
    resource_type: Optional[str] = Query(None, description="Filter by resource type"),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    query = db.query(CrawlResult).filter(CrawlResult.task_id == task_id)
    
    if resource_type:
        query = query.filter(CrawlResult.resource_type == resource_type)
    
    results = query.all()
    
    if not results:
        raise HTTPException(status_code=404, detail="No results found")
    
    output = io.StringIO()
    writer = csv.writer(output)
    
    all_keys = set()
    for r in results:
        if r.data:
            all_keys.update(r.data.keys())
    
    headers = ["id", "task_id", "resource_type", "created_at"] + sorted(list(all_keys))
    writer.writerow(headers)
    
    for r in results:
        row = [
            r.id,
            r.task_id,
            r.resource_type,
            r.created_at.isoformat() if r.created_at else ""
        ]
        for key in sorted(list(all_keys)):
            value = r.data.get(key, "") if r.data else ""
            if isinstance(value, (dict, list)):
                value = json.dumps(value, ensure_ascii=False)
            row.append(str(value))
        writer.writerow(row)
    
    output.seek(0)
    
    return StreamingResponse(
        io.BytesIO(output.getvalue().encode("utf-8-sig")),
        media_type="text/csv",
        headers={
            "Content-Disposition": f"attachment; filename=task_{task_id}_results.csv"
        }
    )


@router.get("/export/json")
def export_json(
    task_id: int = Query(..., description="Task ID to export"),
    resource_type: Optional[str] = Query(None, description="Filter by resource type"),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    query = db.query(CrawlResult).filter(CrawlResult.task_id == task_id)
    
    if resource_type:
        query = query.filter(CrawlResult.resource_type == resource_type)
    
    results = query.all()
    
    if not results:
        raise HTTPException(status_code=404, detail="No results found")
    
    data = [
        {
            "id": r.id,
            "task_id": r.task_id,
            "resource_type": r.resource_type,
            "data": r.data,
            "file_path": r.file_path,
            "created_at": r.created_at.isoformat() if r.created_at else None
        }
        for r in results
    ]
    
    output = io.BytesIO(
        json.dumps(data, ensure_ascii=False, indent=2).encode("utf-8")
    )
    
    return StreamingResponse(
        output,
        media_type="application/json",
        headers={
            "Content-Disposition": f"attachment; filename=task_{task_id}_results.json"
        }
    )


@router.delete("/{result_id}")
def delete_result(
    result_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    result = db.query(CrawlResult).filter(CrawlResult.id == result_id).first()
    if not result:
        raise HTTPException(status_code=404, detail="Result not found")
    
    db.delete(result)
    db.commit()
    
    return {"message": "Result deleted successfully"}


@router.delete("/task/{task_id}")
def delete_task_results(
    task_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    task = db.query(CrawlerTask).filter(CrawlerTask.id == task_id).first()
    if not task:
        raise HTTPException(status_code=404, detail="Task not found")
    
    deleted = db.query(CrawlResult).filter(CrawlResult.task_id == task_id).delete()
    db.commit()
    
    return {"message": f"Deleted {deleted} results"}
