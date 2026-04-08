import logging
from typing import Dict, Any, Optional
from datetime import datetime
from croniter import croniter
from sqlalchemy.orm import Session
from backend.app.models.task import CrawlerTask
from backend.app.models.task_log import TaskLog
from backend.app.core.celery_app import celery_app

logger = logging.getLogger(__name__)


def parse_cron_expression(cron_expression: str) -> Dict[str, Any]:
    try:
        cron = croniter(cron_expression)
        next_run = cron.get_next(datetime)
        prev_run = cron.get_prev(datetime)
        
        parts = cron_expression.split()
        if len(parts) != 5:
            return {"valid": False, "error": "Invalid cron format"}
        
        return {
            "valid": True,
            "expression": cron_expression,
            "next_run": next_run.isoformat(),
            "prev_run": prev_run.isoformat(),
            "minute": parts[0],
            "hour": parts[1],
            "day_of_month": parts[2],
            "month": parts[3],
            "day_of_week": parts[4]
        }
    except Exception as e:
        return {"valid": False, "error": str(e)}


def create_scheduled_task(task_id: int, cron_expression: str, db: Session) -> Dict[str, Any]:
    parsed = parse_cron_expression(cron_expression)
    if not parsed["valid"]:
        return {"success": False, "error": parsed["error"]}
    
    task = db.query(CrawlerTask).filter(CrawlerTask.id == task_id).first()
    if not task:
        return {"success": False, "error": "Task not found"}
    
    task.schedule = cron_expression
    db.commit()
    
    schedule_name = f"task_{task_id}"
    celery_app.conf.beat_schedule[schedule_name] = {
        "task": "backend.app.tasks.crawler_tasks.scheduled_crawler_task",
        "schedule": crontab(
            minute=parsed["minute"],
            hour=parsed["hour"],
            day_of_month=parsed["day_of_month"],
            month_of_month=parsed["month"],
            day_of_week=parsed["day_of_week"]
        ),
        "args": (task_id,)
    }
    
    logger.info(f"Scheduled task {task_id} with cron: {cron_expression}")
    return {
        "success": True,
        "task_id": task_id,
        "schedule": cron_expression,
        "next_run": parsed["next_run"]
    }


def update_scheduled_task(task_id: int, cron_expression: str, db: Session) -> Dict[str, Any]:
    delete_scheduled_task(task_id, db)
    return create_scheduled_task(task_id, cron_expression, db)


def delete_scheduled_task(task_id: int, db: Session) -> Dict[str, Any]:
    task = db.query(CrawlerTask).filter(CrawlerTask.id == task_id).first()
    if task:
        task.schedule = None
        db.commit()
    
    schedule_name = f"task_{task_id}"
    if schedule_name in celery_app.conf.beat_schedule:
        del celery_app.conf.beat_schedule[schedule_name]
        logger.info(f"Removed scheduled task {task_id}")
    
    return {"success": True, "task_id": task_id}


def trigger_task(task_id: int, db: Session) -> Dict[str, Any]:
    task = db.query(CrawlerTask).filter(CrawlerTask.id == task_id).first()
    if not task:
        return {"success": False, "error": "Task not found"}
    
    task.status = "running"
    db.commit()
    
    task_log = TaskLog(
        task_id=task_id,
        status="started",
        start_time=datetime.utcnow()
    )
    db.add(task_log)
    db.commit()
    db.refresh(task_log)
    
    from backend.app.tasks.crawler_tasks import execute_crawler_task
    result = execute_crawler_task.delay(task_id, task_log.id)
    
    logger.info(f"Triggered task {task_id}, execution_id: {result.id}")
    return {
        "success": True,
        "task_id": task_id,
        "execution_id": result.id,
        "log_id": task_log.id
    }


def stop_task(task_id: int, db: Session) -> Dict[str, Any]:
    task = db.query(CrawlerTask).filter(CrawlerTask.id == task_id).first()
    if not task:
        return {"success": False, "error": "Task not found"}
    
    task.status = "stopped"
    db.commit()
    
    task_log = db.query(TaskLog).filter(
        TaskLog.task_id == task_id,
        TaskLog.status == "started"
    ).order_by(TaskLog.start_time.desc()).first()
    
    if task_log:
        task_log.status = "stopped"
        task_log.end_time = datetime.utcnow()
        db.commit()
    
    logger.info(f"Stopped task {task_id}")
    return {"success": True, "task_id": task_id}


def get_task_status(task_id: int, db: Session) -> Dict[str, Any]:
    task = db.query(CrawlerTask).filter(CrawlerTask.id == task_id).first()
    if not task:
        return {"error": "Task not found"}
    
    latest_log = db.query(TaskLog).filter(
        TaskLog.task_id == task_id
    ).order_by(TaskLog.start_time.desc()).first()
    
    return {
        "task_id": task_id,
        "status": task.status,
        "schedule": task.schedule,
        "latest_execution": {
            "log_id": latest_log.id if latest_log else None,
            "status": latest_log.status if latest_log else None,
            "start_time": latest_log.start_time.isoformat() if latest_log and latest_log.start_time else None,
            "end_time": latest_log.end_time.isoformat() if latest_log and latest_log.end_time else None,
            "error": latest_log.error_message if latest_log else None
        } if latest_log else None
    }
