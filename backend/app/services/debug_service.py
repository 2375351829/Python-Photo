import logging
import json
from typing import Dict, List, Any, Optional
from datetime import datetime
from sqlalchemy.orm import Session
from backend.app.models.task_log import TaskLog
from backend.app.models.debug_report import DebugReport

logger = logging.getLogger(__name__)


class DebugSession:
    def __init__(self, task_id: int):
        self.task_id = task_id
        self.enabled = False
        self.breakpoints: List[int] = []
        self.current_step = 0
        self.paused = False
        self.variables: Dict[str, Any] = {}
        self.logs: List[Dict[str, Any]] = []
        self.requests: List[Dict[str, Any]] = []
        self.responses: List[Dict[str, Any]] = []
        self.match_results: List[Dict[str, Any]] = []


debug_sessions: Dict[int, DebugSession] = {}


def enable_debug_mode(task_id: int, db: Session) -> DebugSession:
    session = DebugSession(task_id)
    session.enabled = True
    debug_sessions[task_id] = session
    
    task_log = TaskLog(
        task_id=task_id,
        status='debug_started',
        start_time=datetime.utcnow(),
        debug_info={'enabled': True}
    )
    db.add(task_log)
    db.commit()
    
    logger.info(f"Debug mode enabled for task {task_id}")
    return session


def disable_debug_mode(task_id: int, db: Session) -> None:
    if task_id in debug_sessions:
        del debug_sessions[task_id]
        logger.info(f"Debug mode disabled for task {task_id}")


def get_debug_session(task_id: int) -> Optional[DebugSession]:
    return debug_sessions.get(task_id)


def log_request(task_id: int, request_info: Dict[str, Any]) -> None:
    session = get_debug_session(task_id)
    if session and session.enabled:
        request_info['timestamp'] = datetime.utcnow().isoformat()
        request_info['step'] = session.current_step
        session.requests.append(request_info)
        session.logs.append({
            'type': 'request',
            'data': request_info,
            'timestamp': request_info['timestamp']
        })
        logger.debug(f"[Task {task_id}] Request logged: {request_info.get('url', 'unknown')}")


def log_response(task_id: int, response_info: Dict[str, Any]) -> None:
    session = get_debug_session(task_id)
    if session and session.enabled:
        response_info['timestamp'] = datetime.utcnow().isoformat()
        response_info['step'] = session.current_step
        session.responses.append(response_info)
        session.logs.append({
            'type': 'response',
            'data': response_info,
            'timestamp': response_info['timestamp']
        })
        logger.debug(f"[Task {task_id}] Response logged: status={response_info.get('status_code', 'unknown')}")


def log_match_result(task_id: int, match_info: Dict[str, Any]) -> None:
    session = get_debug_session(task_id)
    if session and session.enabled:
        match_info['timestamp'] = datetime.utcnow().isoformat()
        match_info['step'] = session.current_step
        session.match_results.append(match_info)
        session.logs.append({
            'type': 'match_result',
            'data': match_info,
            'timestamp': match_info['timestamp']
        })
        logger.debug(f"[Task {task_id}] Match result logged: {len(match_info.get('results', []))} matches")


def set_breakpoint(task_id: int, step: int) -> None:
    session = get_debug_session(task_id)
    if session and session.enabled:
        if step not in session.breakpoints:
            session.breakpoints.append(step)
            session.breakpoints.sort()
            logger.info(f"[Task {task_id}] Breakpoint set at step {step}")


def remove_breakpoint(task_id: int, step: int) -> None:
    session = get_debug_session(task_id)
    if session and session.enabled:
        if step in session.breakpoints:
            session.breakpoints.remove(step)
            logger.info(f"[Task {task_id}] Breakpoint removed at step {step}")


def check_breakpoint(task_id: int, step: int) -> bool:
    session = get_debug_session(task_id)
    if session and session.enabled:
        if step in session.breakpoints:
            session.paused = True
            session.current_step = step
            logger.info(f"[Task {task_id}] Paused at breakpoint step {step}")
            return True
    return False


def step_execution(task_id: int) -> None:
    session = get_debug_session(task_id)
    if session and session.enabled and session.paused:
        session.paused = False
        session.current_step += 1
        logger.info(f"[Task {task_id}] Stepped to {session.current_step}")


def continue_execution(task_id: int) -> None:
    session = get_debug_session(task_id)
    if session and session.enabled:
        session.paused = False
        logger.info(f"[Task {task_id}] Execution continued")


def get_variable_state(task_id: int) -> Dict[str, Any]:
    session = get_debug_session(task_id)
    if session and session.enabled:
        return {
            'task_id': task_id,
            'current_step': session.current_step,
            'paused': session.paused,
            'variables': session.variables,
            'breakpoints': session.breakpoints,
            'request_count': len(session.requests),
            'response_count': len(session.responses),
            'match_count': len(session.match_results)
        }
    return {}


def set_variable(task_id: int, name: str, value: Any) -> None:
    session = get_debug_session(task_id)
    if session and session.enabled:
        session.variables[name] = value
        logger.debug(f"[Task {task_id}] Variable set: {name}={value}")


def increment_step(task_id: int) -> int:
    session = get_debug_session(task_id)
    if session and session.enabled:
        session.current_step += 1
        return session.current_step
    return 0


def get_debug_logs(task_id: int, log_type: Optional[str] = None) -> List[Dict[str, Any]]:
    session = get_debug_session(task_id)
    if session and session.enabled:
        if log_type:
            return [log for log in session.logs if log.get('type') == log_type]
        return session.logs
    return []
