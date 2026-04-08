from fastapi import APIRouter, WebSocket, WebSocketDisconnect, Depends
from backend.app.core.websocket import manager, send_task_status, send_log_message
from backend.app.core.dependencies import get_current_active_user
from backend.app.models.user import User
import logging

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/ws", tags=["websocket"])


@router.websocket("/tasks/{task_id}")
async def task_status_websocket(websocket: WebSocket, task_id: int):
    channel = f"task_{task_id}"
    await manager.connect(websocket, channel)
    try:
        while True:
            data = await websocket.receive_text()
            logger.debug(f"Received from task {task_id}: {data}")
    except WebSocketDisconnect:
        manager.disconnect(websocket, channel)


@router.websocket("/logs")
async def logs_websocket(websocket: WebSocket):
    channel = "logs"
    await manager.connect(websocket, channel)
    try:
        while True:
            data = await websocket.receive_text()
            logger.debug(f"Received log message: {data}")
    except WebSocketDisconnect:
        manager.disconnect(websocket, channel)


@router.websocket("/dashboard")
async def dashboard_websocket(websocket: WebSocket):
    channel = "dashboard"
    await manager.connect(websocket, channel)
    try:
        while True:
            data = await websocket.receive_text()
            logger.debug(f"Received dashboard message: {data}")
    except WebSocketDisconnect:
        manager.disconnect(websocket, channel)
