import re
from typing import Dict, Any, Optional, List, Tuple
from dataclasses import dataclass, field
from urllib.parse import urljoin, urlparse
import logging
import json

from bs4 import BeautifulSoup, Tag, NavigableString
import lxml.html
from lxml.etree import XPath


logger = logging.getLogger(__name__)


@dataclass
class ContentArea:
    selector: str
    confidence: float
    text_length: int
    element_count: int
    position: Tuple[int, int]


@dataclass
class ExtractedContent:
    title: Optional[str] = None
    content: Optional[str] = None
    author: Optional[str] = None
    publish_date: Optional[str] = None
    summary: Optional[str] = None
    images: List[str] = field(default_factory=list)
    keywords: List[str] = field(default_factory=list)
    confidence: float = 0.0


class SmartExtractor:
    def __init__(self):
        self._noise_selectors = [
            "script", "style", "nav", "footer", "header", "aside",
            ".sidebar", ".advertisement", ".ad", ".ads", ".comment",
            ".social-share", ".related-posts", ".navigation", ".menu",
            ".breadcrumb", ".pagination", ".widget", "#sidebar",
            "#comments", "#footer", "#header", "#nav",
        ]
        
        self._content_indicators = [
            "article", ".article", ".post", ".content", ".entry-content",
            ".post-content", ".article-content", "main", "#content",
            ".main-content", ".single-content", ".text-content",
            ".story", ".story-content", "[itemprop='articleBody']",
            "[itemprop='article']", ".news-content", ".detail-content",
        ]
        
        self._title_indicators = [
            "h1", ".title", ".post-title", ".article-title", ".entry-title",
            "header h1", "article h1", ".headline", "[itemprop='headline']",
        ]
        
        self._negative_patterns = [
            r"cookie", r"privacy", r"policy", r"terms", r"subscribe",
            r"newsletter", r"advertisement", r"sponsored", r"share",
            r"follow", r"social", r"comment", r"login", r"sign up",
        ]
        
        self._positive_patterns = [
            r"article", r"post", r"story", r"news", r"content",
            r"entry", r"main", r"body",
        ]

    def auto_detect_content_area(self, html: str) -> Optional[ContentArea]:
        soup = BeautifulSoup(html, "lxml")
        
        body = soup.find("body")
        if not body:
            return None
        
        for selector in self._noise_selectors:
            for elem in body.select(selector):
                elem.decompose()
        
        candidates = []
        
        for selector in self._content_indicators:
            try:
                elements = body.select(selector)
                for elem in elements:
                    score = self._calculate_content_score(elem)
                    
                    if score > 0:
                        text = elem.get_text(strip=True)
                        candidates.append(ContentArea(
                            selector=selector,
                            confidence=score,
                            text_length=len(text),
                            element_count=len(elem.find_all()),
                            position=self._get_element_position(elem),
                        ))
            except Exception:
                continue
        
        if not candidates:
            main_elem = self._find_main_content(body)
            if main_elem:
                text = main_elem.get_text(strip=True)
                return ContentArea(
                    selector="auto-detected",
                    confidence=0.5,
                    text_length=len(text),
                    element_count=len(main_elem.find_all()),
                    position=(0, 0),
                )
        
        if candidates:
            return max(candidates, key=lambda x: x.confidence)
        
        return None

    def auto_extract_title(self, html: str) -> Optional[str]:
        soup = BeautifulSoup(html, "lxml")
        
        for selector in self._title_indicators:
            try:
                elem = soup.select_one(selector)
                if elem:
                    title = elem.get_text(strip=True)
                    if title and len(title) < 200:
                        return title
            except Exception:
                continue
        
        title_tag = soup.find("title")
        if title_tag:
            title = title_tag.get_text(strip=True)
            title = re.sub(r'\s*[-_|]\s*[^-_|]+$', '', title)
            title = re.sub(r'\s*[-_|]\s*', ' - ', title)
            return title
        
        og_title = soup.find("meta", property="og:title")
        if og_title and og_title.get("content"):
            return og_title["content"]
        
        h1 = soup.find("h1")
        if h1:
            return h1.get_text(strip=True)
        
        return None

    def auto_extract_content(self, html: str, min_paragraph_length: int = 50) -> Optional[str]:
        content_area = self.auto_detect_content_area(html)
        
        if content_area:
            soup = BeautifulSoup(html, "lxml")
            
            for selector in self._content_indicators:
                try:
                    elem = soup.select_one(selector)
                    if elem:
                        for noise in self._noise_selectors:
                            for noise_elem in elem.select(noise):
                                noise_elem.decompose()
                        
                        paragraphs = []
                        for p in elem.find_all(["p", "div"]):
                            text = p.get_text(strip=True)
                            if len(text) >= min_paragraph_length:
                                paragraphs.append(text)
                        
                        if paragraphs:
                            return "\n\n".join(paragraphs)
                except Exception:
                    continue
        
        soup = BeautifulSoup(html, "lxml")
        body = soup.find("body")
        
        if body:
            for selector in self._noise_selectors:
                for elem in body.select(selector):
                    elem.decompose()
            
            paragraphs = []
            for p in body.find_all("p"):
                text = p.get_text(strip=True)
                if len(text) >= min_paragraph_length:
                    paragraphs.append(text)
            
            if paragraphs:
                return "\n\n".join(paragraphs)
        
        return None

    def auto_extract_images(self, html: str, base_url: Optional[str] = None, min_width: int = 200) -> List[str]:
        soup = BeautifulSoup(html, "lxml")
        images = []
        
        content_area = self.auto_detect_content_area(html)
        
        search_area = soup
        if content_area:
            for selector in self._content_indicators:
                try:
                    elem = soup.select_one(selector)
                    if elem:
                        search_area = elem
                        break
                except Exception:
                    continue
        
        for img in search_area.find_all("img"):
            src = (
                img.get("src") or
                img.get("data-src") or
                img.get("data-original") or
                img.get("data-lazy-src")
            )
            
            if not src or src.startswith("data:"):
                continue
            
            if base_url:
                src = urljoin(base_url, src)
            
            width = img.get("width")
            if width:
                try:
                    if int(width) < min_width:
                        continue
                except ValueError:
                    pass
            
            images.append(src)
        
        return list(dict.fromkeys(images))

    def detect_json_response(self, text: str) -> bool:
        text = text.strip()
        
        if text.startswith("{") and text.endswith("}"):
            return True
        if text.startswith("[") and text.endswith("]"):
            return True
        
        return False

    def analyze_json_structure(self, json_data: Any, path: str = "") -> Dict[str, Any]:
        result = {
            "type": type(json_data).__name__,
            "path": path,
            "children": [],
        }
        
        if isinstance(json_data, dict):
            for key, value in json_data.items():
                child_path = f"{path}.{key}" if path else key
                child_result = self.analyze_json_structure(value, child_path)
                result["children"].append(child_result)
        
        elif isinstance(json_data, list):
            if json_data:
                first_item = json_data[0]
                child_path = f"{path}[0]"
                child_result = self.analyze_json_structure(first_item, child_path)
                result["children"].append(child_result)
                result["array_length"] = len(json_data)
        
        elif isinstance(json_data, str):
            result["value_type"] = "string"
            result["sample"] = json_data[:100] if len(json_data) > 100 else json_data
        
        elif isinstance(json_data, (int, float)):
            result["value_type"] = "number"
        
        elif isinstance(json_data, bool):
            result["value_type"] = "boolean"
        
        elif json_data is None:
            result["value_type"] = "null"
        
        return result

    def extract_json_data(self, text: str) -> Optional[Any]:
        if not self.detect_json_response(text):
            return None
        
        try:
            return json.loads(text)
        except json.JSONDecodeError:
            return self._extract_embedded_json(text)

    def _extract_embedded_json(self, html: str) -> Optional[Dict[str, Any]]:
        patterns = [
            r'<script[^>]*type=["\']application/ld\+json["\'][^>]*>(.*?)</script>',
            r'<script[^>]*type=["\']application/json["\'][^>]*>(.*?)</script>',
            r'window\.__INITIAL_STATE__\s*=\s*({.*?});',
            r'window\.__PRELOADED_STATE__\s*=\s*({.*?});',
            r'var\s+jsonData\s*=\s*({.*?});',
        ]
        
        for pattern in patterns:
            match = re.search(pattern, html, re.DOTALL)
            if match:
                try:
                    return json.loads(match.group(1))
                except json.JSONDecodeError:
                    continue
        
        return None

    def extract_full_content(self, html: str, base_url: Optional[str] = None) -> ExtractedContent:
        soup = BeautifulSoup(html, "lxml")
        
        title = self.auto_extract_title(html)
        content = self.auto_extract_content(html)
        images = self.auto_extract_images(html, base_url)
        
        author = self._extract_author(soup)
        publish_date = self._extract_publish_date(soup)
        keywords = self._extract_keywords(soup)
        summary = self._extract_summary(soup)
        
        confidence = self._calculate_extraction_confidence(
            title, content, author, publish_date
        )
        
        return ExtractedContent(
            title=title,
            content=content,
            author=author,
            publish_date=publish_date,
            summary=summary,
            images=images,
            keywords=keywords,
            confidence=confidence,
        )

    def _calculate_content_score(self, element: Tag) -> float:
        score = 0.0
        
        text = element.get_text(strip=True)
        text_length = len(text)
        
        if text_length > 500:
            score += 0.3
        elif text_length > 200:
            score += 0.2
        elif text_length > 100:
            score += 0.1
        
        p_count = len(element.find_all("p"))
        if p_count > 5:
            score += 0.2
        elif p_count > 2:
            score += 0.1
        
        class_names = " ".join(element.get("class", []))
        id_name = element.get("id", "")
        
        for pattern in self._positive_patterns:
            if re.search(pattern, class_names, re.IGNORECASE):
                score += 0.1
            if re.search(pattern, id_name, re.IGNORECASE):
                score += 0.1
        
        for pattern in self._negative_patterns:
            if re.search(pattern, class_names, re.IGNORECASE):
                score -= 0.1
            if re.search(pattern, id_name, re.IGNORECASE):
                score -= 0.1
        
        link_count = len(element.find_all("a"))
        text_link_ratio = link_count / (p_count + 1) if p_count > 0 else link_count
        
        if text_link_ratio > 0.5:
            score -= 0.2
        
        return max(0.0, min(1.0, score))

    def _find_main_content(self, body: Tag) -> Optional[Tag]:
        candidates = []
        
        for elem in body.find_all(["div", "section", "article", "main"]):
            score = self._calculate_content_score(elem)
            if score > 0.3:
                candidates.append((elem, score))
        
        if candidates:
            return max(candidates, key=lambda x: x[1])[0]
        
        return None

    def _get_element_position(self, element: Tag) -> Tuple[int, int]:
        try:
            body = element.find_parent("body")
            if body:
                all_elements = body.find_all(recursive=False)
                for i, elem in enumerate(all_elements):
                    if elem == element or element in elem.descendants:
                        return (i, len(all_elements))
        except Exception:
            pass
        
        return (0, 0)

    def _extract_author(self, soup: BeautifulSoup) -> Optional[str]:
        author = soup.find("meta", attrs={"name": "author"})
        if author and author.get("content"):
            return author["content"]
        
        author = soup.find("meta", property="article:author")
        if author and author.get("content"):
            return author["content"]
        
        author = soup.find(itemprop="author")
        if author:
            return author.get_text(strip=True)
        
        author = soup.find("span", class_=re.compile(r"author", re.I))
        if author:
            return author.get_text(strip=True)
        
        return None

    def _extract_publish_date(self, soup: BeautifulSoup) -> Optional[str]:
        date = soup.find("meta", property="article:published_time")
        if date and date.get("content"):
            return date["content"]
        
        date = soup.find("meta", itemprop="datePublished")
        if date and date.get("content"):
            return date["content"]
        
        date = soup.find("time")
        if date:
            return date.get("datetime") or date.get_text(strip=True)
        
        return None

    def _extract_keywords(self, soup: BeautifulSoup) -> List[str]:
        keywords = soup.find("meta", attrs={"name": "keywords"})
        if keywords and keywords.get("content"):
            return [kw.strip() for kw in keywords["content"].split(",") if kw.strip()]
        
        tags = soup.find_all("meta", property="article:tag")
        if tags:
            return [tag.get("content") for tag in tags if tag.get("content")]
        
        return []

    def _extract_summary(self, soup: BeautifulSoup) -> Optional[str]:
        summary = soup.find("meta", property="og:description")
        if summary and summary.get("content"):
            return summary["content"]
        
        summary = soup.find("meta", attrs={"name": "description"})
        if summary and summary.get("content"):
            return summary["content"]
        
        summary = soup.find(itemprop="description")
        if summary:
            return summary.get_text(strip=True)
        
        return None

    def _calculate_extraction_confidence(
        self,
        title: Optional[str],
        content: Optional[str],
        author: Optional[str],
        publish_date: Optional[str],
    ) -> float:
        confidence = 0.0
        
        if title:
            confidence += 0.25
        
        if content:
            content_length = len(content)
            if content_length > 1000:
                confidence += 0.35
            elif content_length > 500:
                confidence += 0.25
            elif content_length > 200:
                confidence += 0.15
        
        if author:
            confidence += 0.2
        
        if publish_date:
            confidence += 0.2
        
        return min(1.0, confidence)
