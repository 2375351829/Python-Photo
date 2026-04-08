import json
import logging
from typing import Dict, List, Any, Optional
from datetime import datetime
from sqlalchemy.orm import Session
from sqlalchemy import func
from backend.app.models.debug_report import DebugReport
from backend.app.models.intercepted_resource import InterceptedResource
from backend.app.models.task_log import TaskLog
from backend.app.services.debug_service import get_debug_session

logger = logging.getLogger(__name__)


def generate_report(task_id: int, db: Session) -> Dict[str, Any]:
    session = get_debug_session(task_id)
    if not session:
        return {'error': 'Debug session not found'}
    
    request_logs = summarize_requests(task_id)
    resource_stats = calculate_resource_stats(task_id, db)
    errors_warnings = collect_errors_warnings(task_id, db)
    
    report = DebugReport(
        task_id=task_id,
        request_logs=request_logs,
        resource_stats=resource_stats,
        errors=errors_warnings.get('errors', []),
        warnings=errors_warnings.get('warnings', [])
    )
    db.add(report)
    db.commit()
    db.refresh(report)
    
    return {
        'id': report.id,
        'task_id': task_id,
        'request_logs': request_logs,
        'resource_stats': resource_stats,
        'errors': errors_warnings.get('errors', []),
        'warnings': errors_warnings.get('warnings', []),
        'created_at': report.created_at.isoformat()
    }


def summarize_requests(task_id: int) -> Dict[str, Any]:
    session = get_debug_session(task_id)
    if not session:
        return {}
    
    requests = session.requests
    responses = session.responses
    
    total_requests = len(requests)
    successful_requests = sum(1 for r in responses if 200 <= r.get('status_code', 0) < 300)
    failed_requests = sum(1 for r in responses if r.get('status_code', 0) >= 400)
    
    total_size = sum(r.get('size', 0) for r in responses)
    total_duration = sum(r.get('duration', 0) for r in responses)
    avg_duration = total_duration / total_requests if total_requests > 0 else 0
    
    status_codes = {}
    for r in responses:
        code = r.get('status_code', 0)
        status_codes[str(code)] = status_codes.get(str(code), 0) + 1
    
    methods = {}
    for r in requests:
        method = r.get('method', 'GET')
        methods[method] = methods.get(method, 0) + 1
    
    return {
        'total_requests': total_requests,
        'successful_requests': successful_requests,
        'failed_requests': failed_requests,
        'success_rate': round(successful_requests / total_requests * 100, 2) if total_requests > 0 else 0,
        'total_size_bytes': total_size,
        'total_size_mb': round(total_size / (1024 * 1024), 2),
        'total_duration_seconds': round(total_duration, 2),
        'average_duration_seconds': round(avg_duration, 3),
        'status_codes': status_codes,
        'methods': methods,
        'requests': requests[:100],
        'responses': responses[:100]
    }


def calculate_resource_stats(task_id: int, db: Session) -> Dict[str, Any]:
    resources = db.query(InterceptedResource).filter(
        InterceptedResource.task_id == task_id
    ).all()
    
    if not resources:
        return {
            'total_resources': 0,
            'by_type': {},
            'by_domain': {},
            'total_size': 0,
            'average_duration': 0
        }
    
    by_type = {}
    by_domain = {}
    total_size = 0
    total_duration = 0
    
    for resource in resources:
        resource_type = resource.resource_type or 'unknown'
        by_type[resource_type] = by_type.get(resource_type, 0) + 1
        
        from urllib.parse import urlparse
        domain = urlparse(resource.url).netloc if resource.url else 'unknown'
        by_domain[domain] = by_domain.get(domain, 0) + 1
        
        total_size += resource.size or 0
        total_duration += resource.duration or 0
    
    return {
        'total_resources': len(resources),
        'by_type': by_type,
        'by_domain': dict(sorted(by_domain.items(), key=lambda x: x[1], reverse=True)[:10]),
        'total_size_bytes': total_size,
        'total_size_mb': round(total_size / (1024 * 1024), 2),
        'average_duration_seconds': round(total_duration / len(resources), 3) if resources else 0
    }


def collect_errors_warnings(task_id: int, db: Session) -> Dict[str, List[Dict[str, Any]]]:
    task_logs = db.query(TaskLog).filter(
        TaskLog.task_id == task_id
    ).all()
    
    errors = []
    warnings = []
    
    for log in task_logs:
        if log.error_message:
            errors.append({
                'timestamp': log.start_time.isoformat() if log.start_time else None,
                'message': log.error_message,
                'status': log.status
            })
        
        if log.debug_info:
            debug_data = log.debug_info if isinstance(log.debug_info, dict) else {}
            if debug_data.get('warnings'):
                for warning in debug_data.get('warnings', []):
                    warnings.append({
                        'timestamp': log.start_time.isoformat() if log.start_time else None,
                        'message': warning
                    })
    
    session = get_debug_session(task_id)
    if session:
        for log in session.logs:
            if log.get('type') == 'error':
                errors.append({
                    'timestamp': log.get('timestamp'),
                    'message': log.get('data', {}).get('message', 'Unknown error')
                })
            elif log.get('type') == 'warning':
                warnings.append({
                    'timestamp': log.get('timestamp'),
                    'message': log.get('data', {}).get('message', 'Unknown warning')
                })
    
    return {
        'errors': errors,
        'warnings': warnings,
        'error_count': len(errors),
        'warning_count': len(warnings)
    }


def export_report(task_id: int, format: str, db: Session) -> str:
    report_data = generate_report(task_id, db)
    
    if format == 'json':
        return json.dumps(report_data, indent=2, ensure_ascii=False)
    elif format == 'txt':
        lines = [
            f"Debug Report for Task {task_id}",
            "=" * 50,
            "",
            "Request Summary:",
            f"  Total Requests: {report_data['request_logs'].get('total_requests', 0)}",
            f"  Successful: {report_data['request_logs'].get('successful_requests', 0)}",
            f"  Failed: {report_data['request_logs'].get('failed_requests', 0)}",
            f"  Success Rate: {report_data['request_logs'].get('success_rate', 0)}%",
            "",
            "Resource Statistics:",
            f"  Total Resources: {report_data['resource_stats'].get('total_resources', 0)}",
            f"  Total Size: {report_data['resource_stats'].get('total_size_mb', 0)} MB",
            "",
            "Errors and Warnings:",
            f"  Errors: {report_data.get('errors', [])}",
            f"  Warnings: {report_data.get('warnings', [])}",
        ]
        return "\n".join(lines)
    else:
        return json.dumps(report_data, indent=2, ensure_ascii=False)


def get_saved_reports(task_id: int, db: Session) -> List[Dict[str, Any]]:
    reports = db.query(DebugReport).filter(
        DebugReport.task_id == task_id
    ).order_by(DebugReport.created_at.desc()).all()
    
    return [
        {
            'id': r.id,
            'task_id': r.task_id,
            'created_at': r.created_at.isoformat(),
            'error_count': len(r.errors) if r.errors else 0,
            'warning_count': len(r.warnings) if r.warnings else 0
        }
        for r in reports
    ]


def get_report_by_id(report_id: int, db: Session) -> Optional[Dict[str, Any]]:
    report = db.query(DebugReport).filter(DebugReport.id == report_id).first()
    if report:
        return {
            'id': report.id,
            'task_id': report.task_id,
            'request_logs': report.request_logs,
            'resource_stats': report.resource_stats,
            'errors': report.errors,
            'warnings': report.warnings,
            'created_at': report.created_at.isoformat()
        }
    return None
