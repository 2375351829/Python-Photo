from typing import Optional, List
from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.orm import Session
from backend.app.core.database import get_db
from backend.app.core.dependencies import get_current_active_user
from backend.app.models.user import User
from backend.app.services.debug_service import (
    enable_debug_mode, disable_debug_mode, get_debug_session,
    log_request, log_response, log_match_result,
    set_breakpoint, remove_breakpoint, check_breakpoint,
    step_execution, continue_execution, get_variable_state,
    set_variable, increment_step, get_debug_logs
)
from backend.app.services.debug_report_service import (
    generate_report, export_report, get_saved_reports, get_report_by_id
)
from pydantic import BaseModel
from typing import Dict, Any


router = APIRouter(prefix="/debug", tags=["debug"])


class BreakpointRequest(BaseModel):
    step: int


class VariableRequest(BaseModel):
    name: str
    value: Any


class LogRequest(BaseModel):
    request_info: Dict[str, Any]


class ResponseLogRequest(BaseModel):
    response_info: Dict[str, Any]


class MatchResultRequest(BaseModel):
    match_info: Dict[str, Any]


@router.post("/{task_id}/enable")
def enable_debug(
    task_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    session = enable_debug_mode(task_id, db)
    return {
        "message": "Debug mode enabled",
        "task_id": task_id,
        "session": {
            "enabled": session.enabled,
            "breakpoints": session.breakpoints,
            "current_step": session.current_step
        }
    }


@router.post("/{task_id}/disable")
def disable_debug(
    task_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    disable_debug_mode(task_id, db)
    return {"message": "Debug mode disabled", "task_id": task_id}


@router.get("/{task_id}/status")
def get_debug_status(
    task_id: int,
    current_user: User = Depends(get_current_active_user)
):
    session = get_debug_session(task_id)
    if not session:
        return {"enabled": False, "message": "Debug session not found"}
    
    return {
        "enabled": session.enabled,
        "paused": session.paused,
        "current_step": session.current_step,
        "breakpoints": session.breakpoints,
        "variables": session.variables,
        "request_count": len(session.requests),
        "response_count": len(session.responses),
        "match_count": len(session.match_results)
    }


@router.post("/{task_id}/breakpoint")
def add_breakpoint(
    task_id: int,
    request: BreakpointRequest,
    current_user: User = Depends(get_current_active_user)
):
    set_breakpoint(task_id, request.step)
    return {"message": f"Breakpoint set at step {request.step}", "task_id": task_id}


@router.delete("/{task_id}/breakpoint/{step}")
def delete_breakpoint(
    task_id: int,
    step: int,
    current_user: User = Depends(get_current_active_user)
):
    remove_breakpoint(task_id, step)
    return {"message": f"Breakpoint removed at step {step}", "task_id": task_id}


@router.post("/{task_id}/step")
def step(
    task_id: int,
    current_user: User = Depends(get_current_active_user)
):
    step_execution(task_id)
    return {"message": "Stepped to next step", "task_id": task_id}


@router.post("/{task_id}/continue")
def continue_exec(
    task_id: int,
    current_user: User = Depends(get_current_active_user)
):
    continue_execution(task_id)
    return {"message": "Execution continued", "task_id": task_id}


@router.get("/{task_id}/variables")
def get_variables(
    task_id: int,
    current_user: User = Depends(get_current_active_user)
):
    state = get_variable_state(task_id)
    return state


@router.post("/{task_id}/variables")
def set_var(
    task_id: int,
    request: VariableRequest,
    current_user: User = Depends(get_current_active_user)
):
    set_variable(task_id, request.name, request.value)
    return {"message": f"Variable {request.name} set", "task_id": task_id}


@router.post("/{task_id}/log/request")
def log_req(
    task_id: int,
    request: LogRequest,
    current_user: User = Depends(get_current_active_user)
):
    log_request(task_id, request.request_info)
    return {"message": "Request logged", "task_id": task_id}


@router.post("/{task_id}/log/response")
def log_resp(
    task_id: int,
    request: ResponseLogRequest,
    current_user: User = Depends(get_current_active_user)
):
    log_response(task_id, request.response_info)
    return {"message": "Response logged", "task_id": task_id}


@router.post("/{task_id}/log/match")
def log_match(
    task_id: int,
    request: MatchResultRequest,
    current_user: User = Depends(get_current_active_user)
):
    log_match_result(task_id, request.match_info)
    return {"message": "Match result logged", "task_id": task_id}


@router.get("/{task_id}/logs")
def get_logs(
    task_id: int,
    log_type: Optional[str] = Query(None, description="Filter by log type"),
    current_user: User = Depends(get_current_active_user)
):
    logs = get_debug_logs(task_id, log_type)
    return {"task_id": task_id, "logs": logs, "count": len(logs)}


@router.get("/{task_id}/report")
def get_report(
    task_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    report = generate_report(task_id, db)
    return report


@router.get("/{task_id}/reports")
def list_reports(
    task_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    reports = get_saved_reports(task_id, db)
    return {"task_id": task_id, "reports": reports}


@router.get("/report/{report_id}")
def get_report_detail(
    report_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    report = get_report_by_id(report_id, db)
    if not report:
        raise HTTPException(status_code=404, detail="Report not found")
    return report


@router.get("/{task_id}/export")
def export_debug_report(
    task_id: int,
    format: str = Query("json", description="Export format: json or txt"),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    content = export_report(task_id, format, db)
    return {"task_id": task_id, "format": format, "content": content}
