import os
import json
import logging
import psutil
from typing import Dict, Any, Optional
from datetime import datetime
from pathlib import Path
from sqlalchemy.orm import Session
from backend.app.models.task import CrawlerTask
from backend.app.models.task_log import TaskLog

logger = logging.getLogger(__name__)

CHECKPOINT_DIR = Path("checkpoints")
CHECKPOINT_DIR.mkdir(exist_ok=True)


def monitor_memory() -> Dict[str, Any]:
    process = psutil.Process(os.getpid())
    memory_info = process.memory_info()
    
    return {
        "rss_mb": memory_info.rss / (1024 * 1024),
        "vms_mb": memory_info.vms / (1024 * 1024),
        "percent": process.memory_percent(),
        "available_mb": psutil.virtual_memory().available / (1024 * 1024),
        "total_mb": psutil.virtual_memory().total / (1024 * 1024)
    }


def cleanup_resources() -> Dict[str, Any]:
    import gc
    collected = gc.collect()
    
    memory_before = monitor_memory()
    gc.collect()
    memory_after = monitor_memory()
    
    return {
        "collected_objects": collected,
        "memory_before": memory_before,
        "memory_after": memory_after,
        "memory_freed_mb": memory_before["rss_mb"] - memory_after["rss_mb"]
    }


def save_checkpoint(task_id: int, state: Dict[str, Any], db: Session) -> str:
    checkpoint_file = CHECKPOINT_DIR / f"task_{task_id}_checkpoint.json"
    
    checkpoint_data = {
        "task_id": task_id,
        "state": state,
        "timestamp": datetime.utcnow().isoformat()
    }
    
    with open(checkpoint_file, "w", encoding="utf-8") as f:
        json.dump(checkpoint_data, f, ensure_ascii=False, indent=2)
    
    task = db.query(CrawlerTask).filter(CrawlerTask.id == task_id).first()
    if task:
        if not task.rules:
            task.rules = {}
        task.rules["checkpoint"] = str(checkpoint_file)
        db.commit()
    
    logger.info(f"Checkpoint saved for task {task_id}")
    return str(checkpoint_file)


def load_checkpoint(task_id: int, db: Session) -> Optional[Dict[str, Any]]:
    task = db.query(CrawlerTask).filter(CrawlerTask.id == task_id).first()
    if not task or not task.rules:
        return None
    
    checkpoint_file = task.rules.get("checkpoint")
    if not checkpoint_file or not os.path.exists(checkpoint_file):
        return None
    
    try:
        with open(checkpoint_file, "r", encoding="utf-8") as f:
            checkpoint_data = json.load(f)
        
        logger.info(f"Checkpoint loaded for task {task_id}")
        return checkpoint_data
    except Exception as e:
        logger.error(f"Failed to load checkpoint: {e}")
        return None


def delete_checkpoint(task_id: int) -> None:
    checkpoint_file = CHECKPOINT_DIR / f"task_{task_id}_checkpoint.json"
    if checkpoint_file.exists():
        checkpoint_file.unlink()
        logger.info(f"Checkpoint deleted for task {task_id}")


def get_resource_usage() -> Dict[str, Any]:
    cpu_percent = psutil.cpu_percent(interval=1)
    memory = psutil.virtual_memory()
    disk = psutil.disk_usage("/")
    
    return {
        "cpu_percent": cpu_percent,
        "memory_percent": memory.percent,
        "memory_available_gb": memory.available / (1024 * 1024 * 1024),
        "disk_percent": disk.percent,
        "disk_free_gb": disk.free / (1024 * 1024 * 1024)
    }
