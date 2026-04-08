import logging
import asyncio
from typing import Dict, Any, List, Optional
from datetime import datetime
from sqlalchemy.orm import Session
from backend.app.models.task import CrawlerTask
from backend.app.models.task_log import TaskLog
from backend.app.models.crawl_result import CrawlResult
from backend.app.models.intercepted_resource import InterceptedResource
from backend.app.crawler import BaseCrawler, HTTPClient, HTMLParser, SmartExtractor
from backend.app.services.debug_service import (
    log_request, log_response, log_match_result,
    get_debug_session
)
from backend.app.services.target_type_service import process_all_types
from backend.app.services.resource_filter_service import apply_all_filters

logger = logging.getLogger(__name__)


def execute_crawler_task_sync(task_id: int, log_id: int):
    import sys
    sys.path.insert(0, 'g:\\Python-xiangmu\\图片爬虫\\图片爬虫4.0')
    from backend.app.core.database import SessionLocal
    
    db = SessionLocal()
    try:
        task = db.query(CrawlerTask).filter(CrawlerTask.id == task_id).first()
        if not task:
            logger.error(f"Task {task_id} not found")
            return
        
        task_log = db.query(TaskLog).filter(TaskLog.id == log_id).first()
        if not task_log:
            task_log = TaskLog(task_id=task_id, status="running", start_time=datetime.utcnow())
            db.add(task_log)
            db.commit()
            db.refresh(task_log)
        
        task.status = "running"
        task_log.status = "running"
        db.commit()
        
        debug_session = get_debug_session(task_id)
        is_debug = debug_session and debug_session.enabled if debug_session else False
        
        try:
            client = HTTPClient(
                timeout=task.rules.get("timeout", 30) if task.rules else 30,
                delay=task.rules.get("delay", 1) if task.rules else 1
            )
            
            if is_debug:
                log_request(task_id, {
                    "url": task.url,
                    "method": "GET"
                })
            
            response = client.fetch(task.url)
            
            if is_debug:
                log_response(task_id, {
                    "status_code": response.get("status_code", 200),
                    "size": len(response.get("content", "")),
                    "duration": response.get("duration", 0)
                })
            
            content = response.get("content", "")
            
            parser = HTMLParser(content)
            smart_extractor = SmartExtractor(content)
            
            target_types = task.target_types if task.target_types else ["text"]
            rules = task.rules if task.rules else {}
            
            results = process_all_types(content, task.url, target_types, rules)
            
            if rules.get("filters"):
                for resource_type, resources in results.items():
                    if resources and isinstance(resources, list):
                        filtered = apply_all_filters(resources, rules["filters"])
                        results[resource_type] = filtered
            
            if is_debug:
                log_match_result(task_id, {
                    "rule_type": "all",
                    "results": results
                })
            
            saved_count = 0
            for resource_type, items in results.items():
                if items and isinstance(items, list):
                    for item in items:
                        result = CrawlResult(
                            task_id=task_id,
                            resource_type=resource_type,
                            data=item if isinstance(item, dict) else {"value": item}
                        )
                        db.add(result)
                        saved_count += 1
            
            db.commit()
            
            task.status = "completed"
            task_log.status = "completed"
            task_log.end_time = datetime.utcnow()
            task_log.debug_info = {
                "results_count": saved_count,
                "resource_types": list(results.keys())
            }
            db.commit()
            
            logger.info(f"Task {task_id} completed, saved {saved_count} results")
            
        except Exception as e:
            logger.error(f"Task {task_id} failed: {str(e)}")
            task.status = "failed"
            task_log.status = "failed"
            task_log.end_time = datetime.utcnow()
            task_log.error_message = str(e)
            db.commit()
            
    except Exception as e:
        logger.error(f"Task execution error: {str(e)}")
    finally:
        db.close()


@celery_app.task(bind=True, max_retries=3)
def execute_crawler_task(self, task_id: int, log_id: int):
    execute_crawler_task_sync(task_id, log_id)


@celery_app.task
def scheduled_crawler_task(task_id: int):
    import sys
    sys.path.insert(0, 'g:\\Python-xiangmu\\图片爬虫\\图片爬虫4.0')
    from backend.app.core.database import SessionLocal
    
    db = SessionLocal()
    try:
        task_log = TaskLog(
            task_id=task_id,
            status="started",
            start_time=datetime.utcnow()
        )
        db.add(task_log)
        db.commit()
        db.refresh(task_log)
        
        execute_crawler_task_sync(task_id, task_log.id)
    finally:
        db.close()
