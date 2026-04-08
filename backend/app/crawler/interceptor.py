import time
from typing import Dict, Any, Optional, List, Callable, Set
from dataclasses import dataclass, field
from urllib.parse import urlparse
import logging
import json
import re


logger = logging.getLogger(__name__)


@dataclass
class ResourceInfo:
    url: str
    resource_type: str
    method: str
    status_code: Optional[int] = None
    headers: Dict[str, str] = field(default_factory=dict)
    size: Optional[int] = None
    content_type: Optional[str] = None
    response_time: Optional[float] = None
    timestamp: float = field(default_factory=time.time)
    error: Optional[str] = None
    domain: Optional[str] = None
    is_blocked: bool = False
    block_reason: Optional[str] = None


@dataclass
class InterceptRule:
    resource_types: List[str] = field(default_factory=list)
    domains: List[str] = field(default_factory=list)
    url_patterns: List[str] = field(default_factory=list)
    content_types: List[str] = field(default_factory=list)
    block: bool = False
    callback: Optional[Callable] = None


class RequestInterceptor:
    def __init__(self):
        self._resources: List[ResourceInfo] = []
        self._rules: List[InterceptRule] = []
        self._blocked_domains: Set[str] = set()
        self._blocked_resource_types: Set[str] = set()
        self._request_callbacks: List[Callable] = []
        self._response_callbacks: List[Callable] = []
        self._max_history: int = 10000

    def intercept_request(self, request: Dict[str, Any]) -> Dict[str, Any]:
        url = request.get("url", "")
        method = request.get("method", "GET")
        headers = request.get("headers", {})
        
        parsed = urlparse(url)
        domain = parsed.netloc
        
        resource_type = self._detect_resource_type(url, headers)
        
        resource_info = ResourceInfo(
            url=url,
            resource_type=resource_type,
            method=method,
            headers=headers,
            domain=domain,
        )
        
        is_blocked, block_reason = self._should_block(resource_info)
        
        if is_blocked:
            resource_info.is_blocked = True
            resource_info.block_reason = block_reason
            self._add_to_history(resource_info)
            logger.debug(f"Blocked request: {url} - {block_reason}")
            raise InterceptBlockedException(f"Request blocked: {block_reason}")
        
        for callback in self._request_callbacks:
            try:
                request = callback(request, resource_info)
            except Exception as e:
                logger.warning(f"Request callback error: {str(e)}")
        
        self._add_to_history(resource_info)
        
        return request

    def intercept_response(self, response: Dict[str, Any]) -> Dict[str, Any]:
        url = response.get("url", "")
        status_code = response.get("status_code")
        headers = response.get("headers", {})
        response_time = response.get("elapsed", 0)
        
        content_type = headers.get("content-type", "")
        if isinstance(content_type, list):
            content_type = content_type[0] if content_type else ""
        
        size = None
        content_length = headers.get("content-length")
        if content_length:
            try:
                size = int(content_length)
            except ValueError:
                pass
        
        for resource in reversed(self._resources):
            if resource.url == url and resource.status_code is None:
                resource.status_code = status_code
                resource.headers = headers
                resource.size = size
                resource.content_type = content_type
                resource.response_time = response_time
                break
        
        for callback in self._response_callbacks:
            try:
                response = callback(response, self._find_resource(url))
            except Exception as e:
                logger.warning(f"Response callback error: {str(e)}")
        
        return response

    def record_resource(self, resource_info: ResourceInfo) -> None:
        self._add_to_history(resource_info)

    def add_rule(self, rule: InterceptRule) -> None:
        self._rules.append(rule)
        logger.info(f"Added intercept rule: types={rule.resource_types}, domains={rule.domains}, block={rule.block}")

    def add_block_domain(self, domain: str) -> None:
        self._blocked_domains.add(domain.lower())
        logger.info(f"Added blocked domain: {domain}")

    def add_block_resource_type(self, resource_type: str) -> None:
        self._blocked_resource_types.add(resource_type.lower())
        logger.info(f"Added blocked resource type: {resource_type}")

    def add_request_callback(self, callback: Callable) -> None:
        self._request_callbacks.append(callback)

    def add_response_callback(self, callback: Callable) -> None:
        self._response_callbacks.append(callback)

    def filter_by_type(self, resource_type: str) -> List[ResourceInfo]:
        resource_type_lower = resource_type.lower()
        
        return [
            r for r in self._resources
            if r.resource_type == resource_type_lower
        ]

    def filter_by_domain(self, domain: str) -> List[ResourceInfo]:
        domain_lower = domain.lower()
        
        return [
            r for r in self._resources
            if r.domain and r.domain.lower() == domain_lower
        ]

    def filter_by_status(self, status_code: int) -> List[ResourceInfo]:
        return [
            r for r in self._resources
            if r.status_code == status_code
        ]

    def filter_by_content_type(self, content_type_pattern: str) -> List[ResourceInfo]:
        pattern = re.compile(content_type_pattern, re.IGNORECASE)
        
        return [
            r for r in self._resources
            if r.content_type and pattern.search(r.content_type)
        ]

    def get_all_resources(self) -> List[ResourceInfo]:
        return self._resources.copy()

    def get_blocked_resources(self) -> List[ResourceInfo]:
        return [r for r in self._resources if r.is_blocked]

    def get_successful_resources(self) -> List[ResourceInfo]:
        return [
            r for r in self._resources
            if r.status_code and 200 <= r.status_code < 300
        ]

    def get_failed_resources(self) -> List[ResourceInfo]:
        return [
            r for r in self._resources
            if r.status_code and r.status_code >= 400
        ]

    def get_statistics(self) -> Dict[str, Any]:
        total = len(self._resources)
        
        type_counts: Dict[str, int] = {}
        domain_counts: Dict[str, int] = {}
        status_counts: Dict[int, int] = {}
        
        total_size = 0
        total_time = 0.0
        blocked_count = 0
        
        for resource in self._resources:
            type_counts[resource.resource_type] = type_counts.get(resource.resource_type, 0) + 1
            
            if resource.domain:
                domain_counts[resource.domain] = domain_counts.get(resource.domain, 0) + 1
            
            if resource.status_code:
                status_counts[resource.status_code] = status_counts.get(resource.status_code, 0) + 1
            
            if resource.size:
                total_size += resource.size
            
            if resource.response_time:
                total_time += resource.response_time
            
            if resource.is_blocked:
                blocked_count += 1
        
        return {
            "total_requests": total,
            "blocked_requests": blocked_count,
            "successful_requests": len(self.get_successful_resources()),
            "failed_requests": len(self.get_failed_resources()),
            "total_size_bytes": total_size,
            "total_response_time": total_time,
            "average_response_time": total_time / total if total > 0 else 0,
            "resource_types": type_counts,
            "domains": domain_counts,
            "status_codes": status_counts,
        }

    def clear_history(self) -> None:
        self._resources.clear()
        logger.info("Cleared intercept history")

    def reset(self) -> None:
        self._resources.clear()
        self._rules.clear()
        self._blocked_domains.clear()
        self._blocked_resource_types.clear()
        self._request_callbacks.clear()
        self._response_callbacks.clear()
        logger.info("Reset request interceptor")

    def export_history(self, format: str = "json") -> str:
        if format == "json":
            data = []
            for resource in self._resources:
                data.append({
                    "url": resource.url,
                    "resource_type": resource.resource_type,
                    "method": resource.method,
                    "status_code": resource.status_code,
                    "content_type": resource.content_type,
                    "size": resource.size,
                    "response_time": resource.response_time,
                    "timestamp": resource.timestamp,
                    "domain": resource.domain,
                    "is_blocked": resource.is_blocked,
                    "block_reason": resource.block_reason,
                })
            return json.dumps(data, indent=2, ensure_ascii=False)
        
        raise ValueError(f"Unsupported format: {format}")

    def _detect_resource_type(self, url: str, headers: Dict[str, str]) -> str:
        parsed = urlparse(url)
        path = parsed.path.lower()
        
        image_extensions = {".jpg", ".jpeg", ".png", ".gif", ".webp", ".svg", ".bmp", ".ico"}
        video_extensions = {".mp4", ".webm", ".ogg", ".avi", ".mov", ".mkv"}
        audio_extensions = {".mp3", ".wav", ".ogg", ".flac", ".aac"}
        font_extensions = {".woff", ".woff2", ".ttf", ".otf", ".eot"}
        style_extensions = {".css"}
        script_extensions = {".js"}
        document_extensions = {".pdf", ".doc", ".docx", ".xls", ".xlsx"}
        
        for ext in image_extensions:
            if path.endswith(ext):
                return "image"
        
        for ext in video_extensions:
            if path.endswith(ext):
                return "video"
        
        for ext in audio_extensions:
            if path.endswith(ext):
                return "audio"
        
        for ext in font_extensions:
            if path.endswith(ext):
                return "font"
        
        for ext in style_extensions:
            if path.endswith(ext):
                return "stylesheet"
        
        for ext in script_extensions:
            if path.endswith(ext):
                return "script"
        
        for ext in document_extensions:
            if path.endswith(ext):
                return "document"
        
        content_type = headers.get("content-type", "")
        if isinstance(content_type, list):
            content_type = content_type[0] if content_type else ""
        
        content_type_lower = content_type.lower()
        
        if "image/" in content_type_lower:
            return "image"
        if "video/" in content_type_lower:
            return "video"
        if "audio/" in content_type_lower:
            return "audio"
        if "font" in content_type_lower:
            return "font"
        if "css" in content_type_lower:
            return "stylesheet"
        if "javascript" in content_type_lower:
            return "script"
        
        if any(x in path for x in ["/api/", "/ajax/", "/json"]):
            return "xhr"
        
        return "document"

    def _should_block(self, resource: ResourceInfo) -> tuple:
        if resource.domain and resource.domain.lower() in self._blocked_domains:
            return True, f"Domain blocked: {resource.domain}"
        
        if resource.resource_type.lower() in self._blocked_resource_types:
            return True, f"Resource type blocked: {resource.resource_type}"
        
        for rule in self._rules:
            if self._matches_rule(resource, rule):
                if rule.block:
                    return True, "Matched block rule"
                
                if rule.callback:
                    try:
                        result = rule.callback(resource)
                        if result is False:
                            return True, "Blocked by callback"
                    except Exception as e:
                        logger.warning(f"Rule callback error: {str(e)}")
        
        return False, None

    def _matches_rule(self, resource: ResourceInfo, rule: InterceptRule) -> bool:
        if rule.resource_types:
            if resource.resource_type not in rule.resource_types:
                return False
        
        if rule.domains:
            if not resource.domain or resource.domain not in rule.domains:
                return False
        
        if rule.url_patterns:
            matched = False
            for pattern in rule.url_patterns:
                if re.search(pattern, resource.url):
                    matched = True
                    break
            if not matched:
                return False
        
        if rule.content_types:
            if not resource.content_type:
                return False
            matched = False
            for ct in rule.content_types:
                if ct in resource.content_type:
                    matched = True
                    break
            if not matched:
                return False
        
        return True

    def _add_to_history(self, resource: ResourceInfo) -> None:
        self._resources.append(resource)
        
        if len(self._resources) > self._max_history:
            self._resources = self._resources[-self._max_history:]

    def _find_resource(self, url: str) -> Optional[ResourceInfo]:
        for resource in reversed(self._resources):
            if resource.url == url:
                return resource
        return None


class InterceptBlockedException(Exception):
    pass
