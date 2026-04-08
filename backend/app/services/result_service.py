import csv
import json
import io
from typing import Dict, Any, List, Optional
from datetime import datetime
from sqlalchemy.orm import Session
from sqlalchemy import and_, or_, desc
from backend.app.models.crawl_result import CrawlResult
from backend.app.models.task import CrawlerTask


def get_results(
    db: Session,
    task_id: Optional[int] = None,
    resource_type: Optional[str] = None,
    skip: int = 0,
    limit: int = 20,
    search: Optional[str] = None
) -> Dict[str, Any]:
    query = db.query(CrawlResult)
    
    if task_id:
        query = query.filter(CrawlResult.task_id == task_id)
    
    if resource_type:
        query = query.filter(CrawlResult.resource_type == resource_type)
    
    if search:
        query = query.filter(CrawlResult.data.contains(search))
    
    total = query.count()
    results = query.order_by(desc(CrawlResult.created_at)).offset(skip).limit(limit).all()
    
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


def get_result(db: Session, result_id: int) -> Optional[Dict[str, Any]]:
    result = db.query(CrawlResult).filter(CrawlResult.id == result_id).first()
    if result:
        return {
            "id": result.id,
            "task_id": result.task_id,
            "resource_type": result.resource_type,
            "data": result.data,
            "file_path": result.file_path,
            "created_at": result.created_at.isoformat() if result.created_at else None
        }
    return None


def delete_result(db: Session, result_id: int) -> bool:
    result = db.query(CrawlResult).filter(CrawlResult.id == result_id).first()
    if result:
        db.delete(result)
        db.commit()
        return True
    return False


def export_csv(
    db: Session,
    task_id: Optional[int] = None,
    resource_type: Optional[str] = None
) -> str:
    query = db.query(CrawlResult)
    
    if task_id:
        query = query.filter(CrawlResult.task_id == task_id)
    
    if resource_type:
        query = query.filter(CrawlResult.resource_type == resource_type)
    
    results = query.order_by(desc(CrawlResult.created_at)).all()
    
    if not results:
        return ""
    
    all_keys = set()
    for r in results:
        if r.data and isinstance(r.data, dict):
            all_keys.update(r.data.keys())
    
    all_keys = sorted(list(all_keys))
    fieldnames = ["id", "task_id", "resource_type", "created_at"] + all_keys
    
    output = io.StringIO()
    writer = csv.DictWriter(output, fieldnames=fieldnames)
    writer.writeheader()
    
    for r in results:
        row = {
            "id": r.id,
            "task_id": r.task_id,
            "resource_type": r.resource_type,
            "created_at": r.created_at.isoformat() if r.created_at else ""
        }
        if r.data and isinstance(r.data, dict):
            for key in all_keys:
                value = r.data.get(key, "")
                if isinstance(value, (dict, list)):
                    value = json.dumps(value, ensure_ascii=False)
                row[key] = value
        writer.writerow(row)
    
    return output.getvalue()


def export_json(
    db: Session,
    task_id: Optional[int] = None,
    resource_type: Optional[str] = None
) -> str:
    query = db.query(CrawlResult)
    
    if task_id:
        query = query.filter(CrawlResult.task_id == task_id)
    
    if resource_type:
        query = query.filter(CrawlResult.resource_type == resource_type)
    
    results = query.order_by(desc(CrawlResult.created_at)).all()
    
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
    
    return json.dumps(data, ensure_ascii=False, indent=2)


def get_result_stats(db: Session, task_id: Optional[int] = None) -> Dict[str, Any]:
    query = db.query(CrawlResult)
    
    if task_id:
        query = query.filter(CrawlResult.task_id == task_id)
    
    results = query.all()
    
    total = len(results)
    by_type = {}
    by_task = {}
    
    for r in results:
        rt = r.resource_type or "unknown"
        by_type[rt] = by_type.get(rt, 0) + 1
        
        tid = r.task_id
        by_task[tid] = by_task.get(tid, 0) + 1
    
    return {
        "total": total,
        "by_type": by_type,
        "by_task": by_task
    }
