import logging
from typing import Dict, Any, Optional, Callable
from functools import wraps
import time
import random
from datetime import datetime
from sqlalchemy.orm import Session
from backend.app.models.task_log import TaskLog

logger = logging.getLogger(__name__)


class CrawlerException(Exception):
    def __init__(self, message: str, task_id: Optional[int] = None, details: Optional[Dict[str, Any]] = None):
        self.message = message
        self.task_id = task_id
        self.details = details or {}
        super().__init__(self.message)


class NetworkException(CrawlerException):
    pass


class ParseException(CrawlerException):
    pass


class ValidationException(CrawlerException):
    pass


class RateLimitException(CrawlerException):
    pass


def exponential_backoff(retry_count: int, base_delay: float = 1.0, max_delay: float = 60.0) -> float:
    delay = min(base_delay * (2 ** retry_count), max_delay)
    jitter = random.uniform(0, 0.1) * delay
    return delay + jitter


def retry_on_failure(
    max_retries: int = 3,
    base_delay: float = 1.0,
    exceptions: tuple = (Exception,),
    on_retry: Optional[Callable] = None
):
    def decorator(func):
        @wraps(func)
        def wrapper(*args, **kwargs):
            last_exception = None
            
            for attempt in range(max_retries + 1):
                try:
                    return func(*args, **kwargs)
                except exceptions as e:
                    last_exception = e
                    
                    if attempt < max_retries:
                        delay = exponential_backoff(attempt, base_delay)
                        logger.warning(
                            f"Attempt {attempt + 1}/{max_retries + 1} failed: {str(e)}. "
                            f"Retrying in {delay:.2f}s..."
                        )
                        
                        if on_retry:
                            on_retry(attempt, e, delay)
                        
                        time.sleep(delay)
                    else:
                        logger.error(f"All {max_retries + 1} attempts failed")
                        raise
            
            raise last_exception
        
        return wrapper
    return decorator


def log_error(task_id: int, error: Exception, db: Session) -> None:
    error_info = {
        "type": type(error).__name__,
        "message": str(error),
        "timestamp": datetime.utcnow().isoformat()
    }
    
    if isinstance(error, CrawlerException):
        error_info["details"] = error.details
    
    task_log = db.query(TaskLog).filter(
        TaskLog.task_id == task_id,
        TaskLog.status == "running"
    ).order_by(TaskLog.start_time.desc()).first()
    
    if task_log:
        if not task_log.debug_info:
            task_log.debug_info = {}
        task_log.debug_info["error"] = error_info
        task_log.status = "failed"
        task_log.end_time = datetime.utcnow()
        task_log.error_message = str(error)
        db.commit()
    
    logger.error(f"Task {task_id} error: {error_info}")


def get_error_logs(task_id: int, db: Session) -> list:
    logs = db.query(TaskLog).filter(
        TaskLog.task_id == task_id,
        TaskLog.status == "failed"
    ).order_by(TaskLog.start_time.desc()).all()
    
    return [
        {
            "id": log.id,
            "error_message": log.error_message,
            "start_time": log.start_time.isoformat() if log.start_time else None,
            "end_time": log.end_time.isoformat() if log.end_time else None,
            "debug_info": log.debug_info
        }
        for log in logs
    ]


def send_notification(user_id: int, error: Exception, db: Session) -> None:
    logger.info(f"Notification sent to user {user_id}: {str(error)}")
