from celery import Celery
from celery.schedules import crontab
from backend.app.core.config import settings

celery_app = Celery(
    "crawler",
    broker=settings.REDIS_URL,
    backend=settings.REDIS_URL,
    include=["backend.app.tasks.crawler_tasks"]
)

celery_app.conf.update(
    task_serializer="json",
    accept_content=["json"],
    result_serializer="json",
    timezone="Asia/Shanghai",
    enable_utc=True,
    task_track_started=True,
    task_time_limit=30 * 60,
    task_soft_time_limit=25 * 60,
    worker_prefetch_multiplier=1,
    worker_max_tasks_per_child=100,
    broker_connection_retry_on_startup=True,
)

celery_app.conf.beat_schedule = {}

celery_app.conf.task_routes = {
    "backend.app.tasks.crawler_tasks.execute_crawler_task": {"queue": "crawler"},
    "backend.app.tasks.crawler_tasks.scheduled_crawler_task": {"queue": "scheduled"},
}
