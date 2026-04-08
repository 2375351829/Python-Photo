import json
from typing import Dict, Set, Any
from fastapi import WebSocket, WebSocketDisconnect
import logging

logger = logging.getLogger(__name__)


class ConnectionManager:
    def __init__(self):
        self.active_connections: Dict[str, Set[WebSocket]] = {}
    
    async def connect(self, websocket: WebSocket, channel: str):
        await websocket.accept()
        if channel not in self.active_connections:
            self.active_connections[channel] = set()
        self.active_connections[channel].add(websocket)
        logger.info(f"WebSocket connected to channel: {channel}")
    
    def disconnect(self, websocket: WebSocket, channel: str):
        if channel in self.active_connections:
            self.active_connections[channel].discard(websocket)
            if not self.active_connections[channel]:
                del self.active_connections[channel]
        logger.info(f"WebSocket disconnected from channel: {channel}")
    
    async def send_personal_message(self, message: Dict[str, Any], websocket: WebSocket):
        await websocket.send_json(message)
    
    async def broadcast(self, channel: str, message: Dict[str, Any]):
        if channel in self.active_connections:
            for connection in self.active_connections[channel]:
                try:
                    await connection.send_json(message)
                except Exception as e:
                    logger.error(f"Error broadcasting to WebSocket: {e}")
    
    async def broadcast_to_all(self, message: Dict[str, Any]):
        for channel in self.active_connections:
            await self.broadcast(channel, message)


manager = ConnectionManager()


async def send_task_status(task_id: int, status: str, data: Dict[str, Any] = None):
    channel = f"task_{task_id}"
    message = {
        "type": "task_status",
        "task_id": task_id,
        "status": status,
        "data": data or {}
    }
    await manager.broadcast(channel, message)


async def send_task_progress(task_id: int, progress: int, message: str = ""):
    channel = f"task_{task_id}"
    data = {
        "type": "task_progress",
        "task_id": task_id,
        "progress": progress,
        "message": message
    }
    await manager.broadcast(channel, data)


async def send_log_message(level: str, message: str, task_id: int = None):
    channel = "logs"
    data = {
        "type": "log",
        "level": level,
        "message": message,
        "task_id": task_id
    }
    await manager.broadcast(channel, data)
