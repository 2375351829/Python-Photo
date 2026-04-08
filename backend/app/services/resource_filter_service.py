import re
import logging
from typing import Dict, List, Any, Optional, Tuple
from urllib.parse import urlparse
from dataclasses import dataclass
from enum import Enum

logger = logging.getLogger(__name__)


class SizeUnit(Enum):
    B = 1
    KB = 1024
    MB = 1024 * 1024
    GB = 1024 * 1024 * 1024


@dataclass
class FilterConfig:
    formats: List[str] = None
    min_size: int = 0
    max_size: int = 0
    size_unit: str = 'KB'
    min_width: int = 0
    max_width: int = 0
    min_height: int = 0
    max_height: int = 0
    aspect_ratio: str = ''
    min_duration: int = 0
    max_duration: int = 0
    min_resolution: str = ''


RESOLUTION_MAP = {
    '240p': (240, 320),
    '360p': (360, 640),
    '480p': (480, 854),
    '720p': (720, 1280),
    '1080p': (1080, 1920),
    '1440p': (1440, 2560),
    '2160p': (2160, 3840),
}


def convert_size_to_bytes(size: float, unit: str) -> int:
    unit_map = {
        'B': SizeUnit.B,
        'KB': SizeUnit.KB,
        'MB': SizeUnit.MB,
        'GB': SizeUnit.GB,
    }
    return int(size * unit_map.get(unit, SizeUnit.KB).value)


def get_extension_from_url(url: str) -> str:
    parsed = urlparse(url)
    path = parsed.path.lower()
    if '.' in path.split('/')[-1]:
        return path.rsplit('.', 1)[-1]
    return ''


def filter_by_format(resources: List[Dict[str, Any]], formats: List[str]) -> List[Dict[str, Any]]:
    if not formats:
        return resources
    
    formats_lower = [f.lower().lstrip('.') for f in formats]
    
    filtered = []
    for resource in resources:
        url = resource.get('url', '')
        ext = get_extension_from_url(url)
        
        if not ext:
            mime_type = resource.get('mime_type', '')
            if mime_type:
                ext = mime_type.split('/')[-1] if '/' in mime_type else ''
        
        if ext and ext.lower() in formats_lower:
            filtered.append(resource)
        elif not ext:
            filtered.append(resource)
    
    logger.info(f"Format filter: {len(resources)} -> {len(filtered)} resources")
    return filtered


def filter_by_size(
    resources: List[Dict[str, Any]],
    min_size: int = 0,
    max_size: int = 0,
    size_unit: str = 'KB'
) -> List[Dict[str, Any]]:
    if min_size <= 0 and max_size <= 0:
        return resources
    
    min_bytes = convert_size_to_bytes(min_size, size_unit) if min_size > 0 else 0
    max_bytes = convert_size_to_bytes(max_size, size_unit) if max_size > 0 else float('inf')
    
    filtered = []
    for resource in resources:
        size = resource.get('size', 0) or resource.get('content_length', 0)
        
        if size == 0:
            filtered.append(resource)
        elif min_bytes <= size <= max_bytes:
            filtered.append(resource)
    
    logger.info(f"Size filter: {len(resources)} -> {len(filtered)} resources")
    return filtered


def filter_by_dimension(
    resources: List[Dict[str, Any]],
    min_width: int = 0,
    max_width: int = 0,
    min_height: int = 0,
    max_height: int = 0
) -> List[Dict[str, Any]]:
    if min_width <= 0 and max_width <= 0 and min_height <= 0 and max_height <= 0:
        return resources
    
    filtered = []
    for resource in resources:
        width = resource.get('width', 0) or resource.get('natural_width', 0)
        height = resource.get('height', 0) or resource.get('natural_height', 0)
        
        if width == 0 or height == 0:
            filtered.append(resource)
            continue
        
        if min_width > 0 and width < min_width:
            continue
        if max_width > 0 and width > max_width:
            continue
        if min_height > 0 and height < min_height:
            continue
        if max_height > 0 and height > max_height:
            continue
        
        filtered.append(resource)
    
    logger.info(f"Dimension filter: {len(resources)} -> {len(filtered)} resources")
    return filtered


def filter_by_aspect_ratio(
    resources: List[Dict[str, Any]],
    aspect_ratio: str
) -> List[Dict[str, Any]]:
    if not aspect_ratio:
        return resources
    
    filtered = []
    for resource in resources:
        width = resource.get('width', 0) or resource.get('natural_width', 0)
        height = resource.get('height', 0) or resource.get('natural_height', 0)
        
        if width == 0 or height == 0:
            filtered.append(resource)
            continue
        
        ratio = width / height
        
        if aspect_ratio == 'landscape' and ratio > 1:
            filtered.append(resource)
        elif aspect_ratio == 'portrait' and ratio < 1:
            filtered.append(resource)
        elif aspect_ratio == 'square' and abs(ratio - 1) < 0.1:
            filtered.append(resource)
        elif ':' in aspect_ratio:
            parts = aspect_ratio.split(':')
            if len(parts) == 2:
                try:
                    target_ratio = float(parts[0]) / float(parts[1])
                    if abs(ratio - target_ratio) < 0.1:
                        filtered.append(resource)
                except (ValueError, ZeroDivisionError):
                    filtered.append(resource)
        else:
            filtered.append(resource)
    
    logger.info(f"Aspect ratio filter: {len(resources)} -> {len(filtered)} resources")
    return filtered


def filter_by_duration(
    resources: List[Dict[str, Any]],
    min_duration: int = 0,
    max_duration: int = 0
) -> List[Dict[str, Any]]:
    if min_duration <= 0 and max_duration <= 0:
        return resources
    
    filtered = []
    for resource in resources:
        duration = resource.get('duration', 0) or 0
        
        if duration == 0:
            filtered.append(resource)
            continue
        
        if min_duration > 0 and duration < min_duration:
            continue
        if max_duration > 0 and duration > max_duration:
            continue
        
        filtered.append(resource)
    
    logger.info(f"Duration filter: {len(resources)} -> {len(filtered)} resources")
    return filtered


def filter_by_resolution(
    resources: List[Dict[str, Any]],
    min_resolution: str
) -> List[Dict[str, Any]]:
    if not min_resolution or min_resolution not in RESOLUTION_MAP:
        return resources
    
    min_height, min_width = RESOLUTION_MAP[min_resolution]
    
    filtered = []
    for resource in resources:
        width = resource.get('width', 0) or resource.get('natural_width', 0)
        height = resource.get('height', 0) or resource.get('natural_height', 0)
        
        if width == 0 or height == 0:
            filtered.append(resource)
            continue
        
        if width >= min_width and height >= min_height:
            filtered.append(resource)
    
    logger.info(f"Resolution filter: {len(resources)} -> {len(filtered)} resources")
    return filtered


def filter_by_url_keywords(
    resources: List[Dict[str, Any]],
    include_keywords: List[str] = None,
    exclude_keywords: List[str] = None,
    url_regex: str = ''
) -> List[Dict[str, Any]]:
    filtered = resources
    
    if include_keywords:
        new_filtered = []
        for resource in resources:
            url = resource.get('url', '').lower()
            if any(kw.lower() in url for kw in include_keywords):
                new_filtered.append(resource)
        filtered = new_filtered
    
    if exclude_keywords:
        new_filtered = []
        for resource in filtered:
            url = resource.get('url', '').lower()
            if not any(kw.lower() in url for kw in exclude_keywords):
                new_filtered.append(resource)
        filtered = new_filtered
    
    if url_regex:
        try:
            pattern = re.compile(url_regex, re.IGNORECASE)
            new_filtered = []
            for resource in filtered:
                url = resource.get('url', '')
                if pattern.search(url):
                    new_filtered.append(resource)
            filtered = new_filtered
        except re.error as e:
            logger.warning(f"Invalid URL regex pattern: {e}")
    
    logger.info(f"URL keyword filter: {len(resources)} -> {len(filtered)} resources")
    return filtered


def filter_by_filename_keywords(
    resources: List[Dict[str, Any]],
    include_keywords: List[str] = None,
    exclude_keywords: List[str] = None
) -> List[Dict[str, Any]]:
    filtered = resources
    
    if include_keywords:
        new_filtered = []
        for resource in resources:
            filename = resource.get('filename', '') or urlparse(resource.get('url', '')).path.split('/')[-1]
            if any(kw.lower() in filename.lower() for kw in include_keywords):
                new_filtered.append(resource)
        filtered = new_filtered
    
    if exclude_keywords:
        new_filtered = []
        for resource in filtered:
            filename = resource.get('filename', '') or urlparse(resource.get('url', '')).path.split('/')[-1]
            if not any(kw.lower() in filename.lower() for kw in exclude_keywords):
                new_filtered.append(resource)
        filtered = new_filtered
    
    logger.info(f"Filename keyword filter: {len(resources)} -> {len(filtered)} resources")
    return filtered


def remove_duplicates(resources: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    seen_urls = set()
    seen_hashes = set()
    filtered = []
    
    for resource in resources:
        url = resource.get('url', '')
        
        if url in seen_urls:
            continue
        
        resource_hash = resource.get('hash') or resource.get('md5')
        if resource_hash and resource_hash in seen_hashes:
            continue
        
        seen_urls.add(url)
        if resource_hash:
            seen_hashes.add(resource_hash)
        filtered.append(resource)
    
    logger.info(f"Duplicate removal: {len(resources)} -> {len(filtered)} resources")
    return filtered


def apply_image_filters(
    resources: List[Dict[str, Any]],
    config: Dict[str, Any]
) -> List[Dict[str, Any]]:
    filtered = resources
    
    if config.get('formats'):
        filtered = filter_by_format(filtered, config['formats'])
    
    if config.get('minWidth', 0) > 0 or config.get('maxWidth', 0) > 0 or \
       config.get('minHeight', 0) > 0 or config.get('maxHeight', 0) > 0:
        filtered = filter_by_dimension(
            filtered,
            config.get('minWidth', 0),
            config.get('maxWidth', 0),
            config.get('minHeight', 0),
            config.get('maxHeight', 0)
        )
    
    if config.get('aspectRatio'):
        filtered = filter_by_aspect_ratio(filtered, config['aspectRatio'])
    
    if config.get('minSize', 0) > 0 or config.get('maxSize', 0) > 0:
        filtered = filter_by_size(
            filtered,
            config.get('minSize', 0),
            config.get('maxSize', 0),
            config.get('minSizeUnit', 'KB')
        )
    
    return filtered


def apply_video_filters(
    resources: List[Dict[str, Any]],
    config: Dict[str, Any]
) -> List[Dict[str, Any]]:
    filtered = resources
    
    if config.get('formats'):
        filtered = filter_by_format(filtered, config['formats'])
    
    if config.get('minDuration', 0) > 0 or config.get('maxDuration', 0) > 0:
        filtered = filter_by_duration(
            filtered,
            config.get('minDuration', 0),
            config.get('maxDuration', 0)
        )
    
    if config.get('minResolution'):
        filtered = filter_by_resolution(filtered, config['minResolution'])
    
    if config.get('minSize', 0) > 0 or config.get('maxSize', 0) > 0:
        filtered = filter_by_size(
            filtered,
            config.get('minSize', 0),
            config.get('maxSize', 0),
            config.get('minSizeUnit', 'MB')
        )
    
    return filtered


def apply_file_filters(
    resources: List[Dict[str, Any]],
    config: Dict[str, Any]
) -> List[Dict[str, Any]]:
    filtered = resources
    
    all_formats = []
    if config.get('documentFormats'):
        all_formats.extend(config['documentFormats'])
    if config.get('archiveFormats'):
        all_formats.extend(config['archiveFormats'])
    if config.get('otherFormats'):
        all_formats.extend(config['otherFormats'])
    
    if all_formats:
        filtered = filter_by_format(filtered, all_formats)
    
    if config.get('minSize', 0) > 0 or config.get('maxSize', 0) > 0:
        filtered = filter_by_size(
            filtered,
            config.get('minSize', 0),
            config.get('maxSize', 0),
            config.get('minSizeUnit', 'KB')
        )
    
    return filtered


def apply_advanced_filters(
    resources: List[Dict[str, Any]],
    config: Dict[str, Any]
) -> List[Dict[str, Any]]:
    filtered = resources
    
    filtered = filter_by_url_keywords(
        filtered,
        config.get('urlIncludeKeywords'),
        config.get('urlExcludeKeywords'),
        config.get('urlRegex', '')
    )
    
    filtered = filter_by_filename_keywords(
        filtered,
        config.get('filenameIncludeKeywords'),
        config.get('filenameExcludeKeywords')
    )
    
    if config.get('skipDuplicates', True):
        filtered = remove_duplicates(filtered)
    
    return filtered


def apply_all_filters(
    resources: List[Dict[str, Any]],
    resource_type: str,
    filter_config: Dict[str, Any]
) -> List[Dict[str, Any]]:
    if not filter_config:
        return resources
    
    filtered = resources
    
    if resource_type == 'image':
        filtered = apply_image_filters(filtered, filter_config.get('image', {}))
    elif resource_type == 'video':
        filtered = apply_video_filters(filtered, filter_config.get('video', {}))
    elif resource_type == 'file':
        filtered = apply_file_filters(filtered, filter_config.get('file', {}))
    
    filtered = apply_advanced_filters(filtered, filter_config.get('advanced', {}))
    
    logger.info(f"Total filter result for {resource_type}: {len(resources)} -> {len(filtered)}")
    return filtered


def get_filter_statistics(
    original_count: int,
    filtered_count: int
) -> Dict[str, Any]:
    return {
        'original_count': original_count,
        'filtered_count': filtered_count,
        'removed_count': original_count - filtered_count,
        'retention_rate': round(filtered_count / original_count * 100, 2) if original_count > 0 else 0
    }


class ResourceFilterService:
    def calculate_statistics(self, resources: List[Any]) -> Dict[str, Any]:
        total = len(resources)
        by_type = {}
        by_domain = {}
        by_status = {}
        total_size = 0
        
        for r in resources:
            rtype = getattr(r, 'resource_type', 'unknown')
            by_type[rtype] = by_type.get(rtype, 0) + 1
            
            url = getattr(r, 'url', '')
            if url:
                try:
                    from urllib.parse import urlparse
                    domain = urlparse(url).netloc
                    by_domain[domain] = by_domain.get(domain, 0) + 1
                except:
                    pass
            
            status = getattr(r, 'status_code', 0)
            by_status[status] = by_status.get(status, 0) + 1
            
            size = getattr(r, 'size', 0) or 0
            total_size += size
        
        return {
            'total': total,
            'by_type': by_type,
            'by_domain': by_domain,
            'by_status': by_status,
            'total_size': total_size,
        }
    
    def apply_filters(
        self,
        resources: List[Any],
        url_pattern: str = None,
        resource_types: List[str] = None,
        domains: List[str] = None,
        domain_mode: str = "blacklist",
        status_codes: List[int] = None,
        min_size: int = 0,
        max_size: int = 0,
    ) -> List[Any]:
        filtered = resources
        
        if resource_types:
            filtered = [r for r in filtered if getattr(r, 'resource_type', None) in resource_types]
        
        if url_pattern:
            import re
            try:
                pattern = re.compile(url_pattern, re.IGNORECASE)
                filtered = [r for r in filtered if pattern.search(getattr(r, 'url', ''))]
            except re.error:
                pass
        
        if domains:
            from urllib.parse import urlparse
            if domain_mode == "whitelist":
                filtered = [r for r in filtered if urlparse(getattr(r, 'url', '')).netloc in domains]
            else:
                filtered = [r for r in filtered if urlparse(getattr(r, 'url', '')).netloc not in domains]
        
        if status_codes:
            filtered = [r for r in filtered if getattr(r, 'status_code', None) in status_codes]
        
        if min_size > 0:
            filtered = [r for r in filtered if getattr(r, 'size', 0) >= min_size]
        
        if max_size > 0:
            filtered = [r for r in filtered if getattr(r, 'size', 0) <= max_size]
        
        return filtered
    
    def replay_request(
        self,
        url: str,
        method: str = "GET",
        headers: Dict[str, str] = None,
        body: str = None,
    ) -> Dict[str, Any]:
        import httpx
        import time
        
        try:
            start_time = time.time()
            
            with httpx.Client() as client:
                response = client.request(
                    method=method,
                    url=url,
                    headers=headers or {},
                    content=body,
                    timeout=30,
                )
            
            duration = time.time() - start_time
            
            return {
                'success': True,
                'status_code': response.status_code,
                'headers': dict(response.headers),
                'body': response.text[:10000],
                'duration': round(duration, 3),
                'size': len(response.content),
            }
        except Exception as e:
            return {
                'success': False,
                'error': str(e),
            }
    
    def capture_api_requests(self, html: str) -> List[Dict[str, Any]]:
        import re
        from urllib.parse import urljoin
        
        api_requests = []
        
        patterns = [
            r'(fetch|axios|http\.get|http\.post|\.ajax)\s*\(\s*["\']([^"\']+)["\']',
            r'(fetch|axios|http\.get|http\.post|\.ajax)\s*\(\s*\{[^}]*url\s*:\s*["\']([^"\']+)["\']',
            r'["\']https?://[^"\']+api[^"\']*["\']',
        ]
        
        for pattern in patterns:
            matches = re.findall(pattern, html, re.IGNORECASE)
            for match in matches:
                if isinstance(match, tuple):
                    url = match[-1]
                else:
                    url = match
                
                if url and not url.startswith('data:'):
                    api_requests.append({
                        'url': url,
                        'method': 'GET',
                    })
        
        return api_requests


resource_filter_service = ResourceFilterService()
