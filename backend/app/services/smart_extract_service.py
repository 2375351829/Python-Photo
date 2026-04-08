import re
import json
import logging
from typing import Dict, Any, Optional, List, Tuple
from dataclasses import dataclass, field, asdict
from urllib.parse import urljoin, urlparse

import httpx
from bs4 import BeautifulSoup, Tag

from backend.app.crawler.smart_extractor import SmartExtractor, ContentArea, ExtractedContent


logger = logging.getLogger(__name__)


@dataclass
class SmartExtractResult:
    success: bool
    message: str
    content_area: Optional[Dict[str, Any]] = None
    title: Optional[str] = None
    content: Optional[str] = None
    images: List[str] = field(default_factory=list)
    json_structure: Optional[Dict[str, Any]] = None
    is_json_response: bool = False
    confidence: float = 0.0
    suggested_rules: Dict[str, Any] = field(default_factory=dict)


@dataclass
class PreviewResult:
    url: str
    matched_items: List[Dict[str, Any]] = field(default_factory=list)
    total_count: int = 0
    preview_time: str = ""
    error: Optional[str] = None


class SmartExtractService:
    def __init__(self):
        self.extractor = SmartExtractor()
        self._http_timeout = 30.0
        self._default_headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
            "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8",
            "Accept-Language": "zh-CN,zh;q=0.9,en;q=0.8",
        }

    async def fetch_url(self, url: str, headers: Optional[Dict[str, str]] = None) -> Tuple[Optional[str], Optional[str], int]:
        request_headers = {**self._default_headers, **(headers or {})}
        
        try:
            async with httpx.AsyncClient(timeout=self._http_timeout, follow_redirects=True) as client:
                response = await client.get(url, headers=request_headers)
                response.raise_for_status()
                
                content_type = response.headers.get("content-type", "")
                return response.text, content_type, response.status_code
                
        except httpx.TimeoutException:
            logger.error(f"请求超时: {url}")
            return None, None, 408
        except httpx.HTTPStatusError as e:
            logger.error(f"HTTP错误: {e}")
            return None, None, e.response.status_code
        except Exception as e:
            logger.error(f"请求失败: {e}")
            return None, None, 500

    def auto_detect_content_area(self, html: str) -> Optional[Dict[str, Any]]:
        if not html:
            return None
            
        try:
            content_area = self.extractor.auto_detect_content_area(html)
            if content_area:
                return {
                    "selector": content_area.selector,
                    "confidence": content_area.confidence,
                    "text_length": content_area.text_length,
                    "element_count": content_area.element_count,
                    "position": content_area.position,
                }
        except Exception as e:
            logger.error(f"自动检测内容区域失败: {e}")
            
        return None

    def auto_extract_title(self, html: str) -> Optional[str]:
        if not html:
            return None
            
        try:
            return self.extractor.auto_extract_title(html)
        except Exception as e:
            logger.error(f"自动提取标题失败: {e}")
            return None

    def auto_extract_content(self, html: str, min_paragraph_length: int = 50) -> Optional[str]:
        if not html:
            return None
            
        try:
            return self.extractor.auto_extract_content(html, min_paragraph_length)
        except Exception as e:
            logger.error(f"自动提取正文失败: {e}")
            return None

    def auto_extract_images(self, html: str, base_url: Optional[str] = None, min_width: int = 200) -> List[str]:
        if not html:
            return []
            
        try:
            return self.extractor.auto_extract_images(html, base_url, min_width)
        except Exception as e:
            logger.error(f"自动提取图片失败: {e}")
            return []

    def detect_json_response(self, response_text: str) -> bool:
        if not response_text:
            return False
            
        return self.extractor.detect_json_response(response_text)

    def analyze_json_structure(self, json_data: Any) -> Dict[str, Any]:
        if json_data is None:
            return {"type": "null", "children": []}
            
        try:
            return self.extractor.analyze_json_structure(json_data)
        except Exception as e:
            logger.error(f"分析JSON结构失败: {e}")
            return {"type": "unknown", "error": str(e)}

    async def smart_extract(self, url: str) -> SmartExtractResult:
        html, content_type, status_code = await self.fetch_url(url)
        
        if not html:
            return SmartExtractResult(
                success=False,
                message=f"获取页面失败，状态码: {status_code}",
            )
        
        is_json = self.detect_json_response(html)
        json_structure = None
        suggested_rules = {}
        
        if is_json:
            try:
                json_data = json.loads(html)
                json_structure = self.analyze_json_structure(json_data)
                suggested_rules = self._suggest_json_rules(json_data)
                
                return SmartExtractResult(
                    success=True,
                    message="成功识别JSON响应",
                    is_json_response=True,
                    json_structure=json_structure,
                    suggested_rules=suggested_rules,
                    confidence=0.9,
                )
            except json.JSONDecodeError:
                pass
        
        content_area = self.auto_detect_content_area(html)
        title = self.auto_extract_title(html)
        content = self.auto_extract_content(html)
        images = self.auto_extract_images(html, url)
        
        suggested_rules = self._suggest_html_rules(html, content_area)
        
        confidence = self._calculate_confidence(title, content, images, content_area)
        
        return SmartExtractResult(
            success=True,
            message="成功提取页面内容",
            content_area=content_area,
            title=title,
            content=content[:500] + "..." if content and len(content) > 500 else content,
            images=images[:20],
            suggested_rules=suggested_rules,
            confidence=confidence,
        )

    async def preview_rules(
        self,
        url: str,
        rules: Dict[str, Any],
        target_types: Optional[List[str]] = None,
    ) -> PreviewResult:
        from datetime import datetime
        
        html, content_type, status_code = await self.fetch_url(url)
        
        if not html:
            return PreviewResult(
                url=url,
                error=f"获取页面失败，状态码: {status_code}",
                preview_time=datetime.utcnow().isoformat(),
            )
        
        matched_items = []
        
        if self.detect_json_response(html):
            matched_items = self._apply_json_rules(html, rules)
        else:
            matched_items = self._apply_html_rules(html, rules, url, target_types)
        
        return PreviewResult(
            url=url,
            matched_items=matched_items,
            total_count=len(matched_items),
            preview_time=datetime.utcnow().isoformat(),
        )

    def _apply_html_rules(
        self,
        html: str,
        rules: Dict[str, Any],
        base_url: str,
        target_types: Optional[List[str]] = None,
    ) -> List[Dict[str, Any]]:
        results = []
        soup = BeautifulSoup(html, "lxml")
        
        css_rules = rules.get("css", [])
        for rule in css_rules:
            if not rule.get("selector"):
                continue
                
            try:
                elements = soup.select(rule["selector"])
                for elem in elements:
                    item = self._extract_element_data(elem, base_url, rule)
                    if item:
                        results.append(item)
            except Exception as e:
                logger.warning(f"CSS选择器执行失败: {rule['selector']}, 错误: {e}")
        
        xpath_rules = rules.get("xpath", [])
        for rule in xpath_rules:
            if not rule.get("selector"):
                continue
                
            try:
                import lxml.html
                tree = lxml.html.fromstring(html)
                elements = tree.xpath(rule["selector"])
                
                for elem in elements:
                    if isinstance(elem, str):
                        results.append({
                            "type": "text",
                            "value": elem.strip(),
                            "rule_name": rule.get("name", ""),
                        })
                    elif hasattr(elem, "get"):
                        item = self._extract_lxml_element_data(elem, base_url, rule)
                        if item:
                            results.append(item)
            except Exception as e:
                logger.warning(f"XPath执行失败: {rule['selector']}, 错误: {e}")
        
        regex_rules = rules.get("regex", [])
        for rule in regex_rules:
            if not rule.get("pattern"):
                continue
                
            try:
                pattern = re.compile(rule["pattern"], re.IGNORECASE)
                matches = pattern.findall(html)
                
                for match in matches:
                    if isinstance(match, tuple):
                        match = match[0] if match else ""
                    
                    results.append({
                        "type": "regex_match",
                        "value": match.strip() if isinstance(match, str) else str(match),
                        "rule_name": rule.get("name", ""),
                    })
            except Exception as e:
                logger.warning(f"正则表达式执行失败: {rule['pattern']}, 错误: {e}")
        
        if target_types:
            results = self._filter_by_target_types(results, target_types)
        
        return results[:100]

    def _apply_json_rules(self, html: str, rules: Dict[str, Any]) -> List[Dict[str, Any]]:
        results = []
        
        try:
            json_data = json.loads(html)
        except json.JSONDecodeError:
            return results
        
        json_rules = rules.get("json", [])
        
        for rule in json_rules:
            if not rule.get("path"):
                continue
                
            try:
                values = self._extract_json_path(json_data, rule["path"])
                for value in values:
                    results.append({
                        "type": "json_value",
                        "value": str(value),
                        "rule_name": rule.get("name", ""),
                        "path": rule["path"],
                    })
            except Exception as e:
                logger.warning(f"JSON路径提取失败: {rule['path']}, 错误: {e}")
        
        return results[:100]

    def _extract_json_path(self, data: Any, path: str) -> List[Any]:
        results = []
        parts = path.split(".")
        current = [data]
        
        for part in parts:
            next_current = []
            for item in current:
                if isinstance(item, dict):
                    if part in item:
                        next_current.append(item[part])
                elif isinstance(item, list):
                    try:
                        idx = int(part.replace("[", "").replace("]", ""))
                        if 0 <= idx < len(item):
                            next_current.append(item[idx])
                    except ValueError:
                        for sub_item in item:
                            if isinstance(sub_item, dict) and part in sub_item:
                                next_current.append(sub_item[part])
            
            current = next_current
        
        return current

    def _extract_element_data(self, elem: Tag, base_url: str, rule: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        tag_name = elem.name.lower()
        
        if tag_name == "img":
            src = elem.get("src") or elem.get("data-src") or elem.get("data-original")
            if src:
                return {
                    "type": "image",
                    "value": urljoin(base_url, src),
                    "alt": elem.get("alt", ""),
                    "rule_name": rule.get("name", ""),
                }
        
        elif tag_name == "a":
            href = elem.get("href")
            if href:
                return {
                    "type": "link",
                    "value": urljoin(base_url, href),
                    "text": elem.get_text(strip=True),
                    "rule_name": rule.get("name", ""),
                }
        
        elif tag_name == "video":
            src = elem.get("src")
            if src:
                return {
                    "type": "video",
                    "value": urljoin(base_url, src),
                    "rule_name": rule.get("name", ""),
                }
        
        else:
            text = elem.get_text(strip=True)
            if text:
                return {
                    "type": "text",
                    "value": text,
                    "tag": tag_name,
                    "rule_name": rule.get("name", ""),
                }
        
        return None

    def _extract_lxml_element_data(self, elem, base_url: str, rule: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        try:
            tag = elem.tag
            if tag == "img":
                src = elem.get("src") or elem.get("data-src")
                if src:
                    return {
                        "type": "image",
                        "value": urljoin(base_url, src),
                        "rule_name": rule.get("name", ""),
                    }
            elif tag == "a":
                href = elem.get("href")
                if href:
                    return {
                        "type": "link",
                        "value": urljoin(base_url, href),
                        "text": elem.text_content().strip() if hasattr(elem, "text_content") else "",
                        "rule_name": rule.get("name", ""),
                    }
            else:
                text = elem.text_content().strip() if hasattr(elem, "text_content") else ""
                if text:
                    return {
                        "type": "text",
                        "value": text,
                        "tag": tag,
                        "rule_name": rule.get("name", ""),
                    }
        except Exception:
            pass
        
        return None

    def _filter_by_target_types(self, items: List[Dict[str, Any]], target_types: List[str]) -> List[Dict[str, Any]]:
        type_mapping = {
            "image": ["image", "img"],
            "video": ["video"],
            "text": ["text"],
            "link": ["link", "url"],
            "file": ["file", "download"],
        }
        
        allowed_types = set()
        for t in target_types:
            allowed_types.update(type_mapping.get(t, [t]))
        
        return [item for item in items if item.get("type") in allowed_types]

    def _suggest_html_rules(self, html: str, content_area: Optional[Dict[str, Any]]) -> Dict[str, Any]:
        suggestions = {
            "css": [],
            "xpath": [],
            "regex": [],
        }
        
        soup = BeautifulSoup(html, "lxml")
        
        images = soup.find_all("img", src=True)
        if images:
            img_selectors = set()
            for img in images[:5]:
                classes = img.get("class", [])
                if classes:
                    img_selectors.add(f".{'.'.join(classes)}")
                parent = img.parent
                if parent and parent.get("class"):
                    parent_classes = parent.get("class", [])
                    img_selectors.add(f".{'.'.join(parent_classes)} img")
            
            for selector in list(img_selectors)[:3]:
                suggestions["css"].append({
                    "name": "图片提取",
                    "selector": selector,
                    "description": "自动检测的图片选择器",
                })
        
        links = soup.find_all("a", href=True)
        if links:
            link_selectors = set()
            for link in links[:5]:
                classes = link.get("class", [])
                if classes:
                    link_selectors.add(f".{'.'.join(classes)}")
            
            for selector in list(link_selectors)[:3]:
                suggestions["css"].append({
                    "name": "链接提取",
                    "selector": selector,
                    "description": "自动检测的链接选择器",
                })
        
        if content_area and content_area.get("selector"):
            suggestions["css"].append({
                "name": "内容区域",
                "selector": content_area["selector"],
                "description": f"自动检测的内容区域 (置信度: {content_area['confidence']:.2f})",
            })
        
        return suggestions

    def _suggest_json_rules(self, json_data: Any) -> Dict[str, Any]:
        suggestions = {
            "json": [],
        }
        
        def find_image_paths(data: Any, path: str = "") -> List[str]:
            paths = []
            
            if isinstance(data, dict):
                for key, value in data.items():
                    current_path = f"{path}.{key}" if path else key
                    
                    if key.lower() in ["image", "img", "url", "src", "thumb", "thumbnail", "picture", "photo"]:
                        if isinstance(value, str) and (value.startswith("http") or any(ext in value.lower() for ext in [".jpg", ".png", ".gif", ".webp"])):
                            paths.append(current_path)
                    
                    paths.extend(find_image_paths(value, current_path))
            
            elif isinstance(data, list):
                for i, item in enumerate(data[:3]):
                    current_path = f"{path}[{i}]"
                    paths.extend(find_image_paths(item, current_path))
            
            return paths
        
        image_paths = find_image_paths(json_data)
        for img_path in image_paths[:5]:
            suggestions["json"].append({
                "name": "图片URL",
                "path": img_path,
                "description": "自动检测的图片路径",
            })
        
        return suggestions

    def _calculate_confidence(
        self,
        title: Optional[str],
        content: Optional[str],
        images: List[str],
        content_area: Optional[Dict[str, Any]],
    ) -> float:
        confidence = 0.0
        
        if title:
            confidence += 0.2
        
        if content:
            content_len = len(content)
            if content_len > 1000:
                confidence += 0.3
            elif content_len > 500:
                confidence += 0.2
            elif content_len > 100:
                confidence += 0.1
        
        if images:
            if len(images) > 10:
                confidence += 0.3
            elif len(images) > 5:
                confidence += 0.2
            else:
                confidence += 0.1
        
        if content_area:
            confidence += content_area.get("confidence", 0) * 0.2
        
        return min(1.0, confidence)


smart_extract_service = SmartExtractService()
