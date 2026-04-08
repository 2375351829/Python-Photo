from typing import Optional, List
from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.orm import Session
from sqlalchemy import and_, or_

from backend.app.core.database import get_db
from backend.app.core.dependencies import get_current_active_user
from backend.app.models.user import User
from backend.app.models.intercepted_resource import InterceptedResource
from backend.app.models.task import CrawlerTask
from backend.app.schemas.resource import (
    ResourceResponse,
    ResourceListResponse,
    ResourceStatsResponse,
    ResourceFilterRequest,
    ReplayRequest,
    ReplayResponse,
)
from backend.app.services.resource_filter_service import resource_filter_service


router = APIRouter(prefix="/resources", tags=["资源拦截"])


@router.get("", response_model=ResourceListResponse)
def get_resources(
    page: int = Query(1, ge=1, description="页码"),
    page_size: int = Query(20, ge=1, le=100, description="每页数量"),
    task_id: Optional[int] = Query(None, description="任务ID"),
    resource_type: Optional[str] = Query(None, description="资源类型"),
    domain: Optional[str] = Query(None, description="域名"),
    status_code: Optional[int] = Query(None, description="状态码"),
    search: Optional[str] = Query(None, description="搜索关键词"),
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db),
):
    query = db.query(InterceptedResource)
    
    if current_user.role != "admin":
        query = query.join(CrawlerTask).filter(CrawlerTask.user_id == current_user.id)
    
    if task_id:
        query = query.filter(InterceptedResource.task_id == task_id)
    
    if resource_type:
        query = query.filter(InterceptedResource.resource_type == resource_type)
    
    if domain:
        query = query.filter(InterceptedResource.url.contains(domain))
    
    if status_code:
        query = query.filter(InterceptedResource.status_code == status_code)
    
    if search:
        query = query.filter(InterceptedResource.url.contains(search))
    
    total = query.count()
    
    skip = (page - 1) * page_size
    resources = query.order_by(InterceptedResource.created_at.desc()).offset(skip).limit(page_size).all()
    
    pages = (total + page_size - 1) // page_size
    
    return ResourceListResponse(
        items=[ResourceResponse.from_orm(r) for r in resources],
        total=total,
        page=page,
        page_size=page_size,
        pages=pages,
    )


@router.get("/stats", response_model=ResourceStatsResponse)
def get_resource_stats(
    task_id: Optional[int] = Query(None, description="任务ID"),
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db),
):
    query = db.query(InterceptedResource)
    
    if current_user.role != "admin":
        query = query.join(CrawlerTask).filter(CrawlerTask.user_id == current_user.id)
    
    if task_id:
        query = query.filter(InterceptedResource.task_id == task_id)
    
    resources = query.all()
    
    stats = resource_filter_service.calculate_statistics(resources)
    
    return ResourceStatsResponse(**stats)


@router.get("/types")
def get_resource_types(
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db),
):
    query = db.query(InterceptedResource.resource_type).distinct()
    
    if current_user.role != "admin":
        query = query.join(CrawlerTask).filter(CrawlerTask.user_id == current_user.id)
    
    types = [t[0] for t in query.all() if t[0]]
    
    return {"types": types}


@router.get("/domains")
def get_resource_domains(
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db),
):
    from urllib.parse import urlparse
    
    query = db.query(InterceptedResource.url)
    
    if current_user.role != "admin":
        query = query.join(CrawlerTask).filter(CrawlerTask.user_id == current_user.id)
    
    urls = [u[0] for u in query.all()]
    
    domains = set()
    for url in urls:
        try:
            parsed = urlparse(url)
            if parsed.netloc:
                domains.add(parsed.netloc)
        except:
            pass
    
    return {"domains": sorted(list(domains))}


@router.post("/filter", response_model=ResourceListResponse)
def filter_resources(
    filter_data: ResourceFilterRequest,
    page: int = Query(1, ge=1, description="页码"),
    page_size: int = Query(20, ge=1, le=100, description="每页数量"),
    task_id: Optional[int] = Query(None, description="任务ID"),
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db),
):
    query = db.query(InterceptedResource)
    
    if current_user.role != "admin":
        query = query.join(CrawlerTask).filter(CrawlerTask.user_id == current_user.id)
    
    if task_id:
        query = query.filter(InterceptedResource.task_id == task_id)
    
    resources = query.all()
    
    filtered = resource_filter_service.apply_filters(
        resources=resources,
        url_pattern=filter_data.url_pattern,
        resource_types=filter_data.resource_types,
        domains=filter_data.domains,
        domain_mode=filter_data.domain_mode or "blacklist",
        status_codes=filter_data.status_codes,
        min_size=filter_data.min_size,
        max_size=filter_data.max_size,
    )
    
    total = len(filtered)
    
    skip = (page - 1) * page_size
    paged_resources = filtered[skip:skip + page_size]
    
    pages = (total + page_size - 1) // page_size
    
    return ResourceListResponse(
        items=[ResourceResponse.from_orm(r) for r in paged_resources],
        total=total,
        page=page,
        page_size=page_size,
        pages=pages,
    )


@router.post("/replay", response_model=ReplayResponse)
def replay_request(
    replay_data: ReplayRequest,
    current_user: User = Depends(get_current_active_user),
):
    if current_user.role != "admin":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="只有管理员可以重放请求"
        )
    
    result = resource_filter_service.replay_request(
        url=replay_data.url,
        method=replay_data.method,
        headers=replay_data.headers,
        body=replay_data.body,
    )
    
    if not result.get('success'):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=result.get('error', '请求失败')
        )
    
    return ReplayResponse(
        status_code=result['status_code'],
        headers=result['headers'],
        body=result['body'],
        duration=result['duration'],
        size=result['size'],
    )


@router.post("/capture-api")
def capture_api_requests(
    html: str,
    current_user: User = Depends(get_current_active_user),
):
    api_requests = resource_filter_service.capture_api_requests(html)
    
    return {
        "total": len(api_requests),
        "requests": api_requests,
    }


@router.get("/{resource_id}", response_model=ResourceResponse)
def get_resource(
    resource_id: int,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db),
):
    query = db.query(InterceptedResource).filter(InterceptedResource.id == resource_id)
    
    if current_user.role != "admin":
        query = query.join(CrawlerTask).filter(CrawlerTask.user_id == current_user.id)
    
    resource = query.first()
    
    if not resource:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="资源不存在"
        )
    
    return ResourceResponse.from_orm(resource)


@router.delete("/{resource_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_resource(
    resource_id: int,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db),
):
    query = db.query(InterceptedResource).filter(InterceptedResource.id == resource_id)
    
    if current_user.role != "admin":
        query = query.join(CrawlerTask).filter(CrawlerTask.user_id == current_user.id)
    
    resource = query.first()
    
    if not resource:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="资源不存在"
        )
    
    db.delete(resource)
    db.commit()
    
    return None


@router.delete("/task/{task_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_task_resources(
    task_id: int,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db),
):
    task_query = db.query(CrawlerTask).filter(CrawlerTask.id == task_id)
    
    if current_user.role != "admin":
        task_query = task_query.filter(CrawlerTask.user_id == current_user.id)
    
    task = task_query.first()
    
    if not task:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="任务不存在"
        )
    
    db.query(InterceptedResource).filter(InterceptedResource.task_id == task_id).delete()
    db.commit()
    
    return None
