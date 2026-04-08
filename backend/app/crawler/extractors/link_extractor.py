from typing import List, Dict, Any, Optional, Set
from dataclasses import dataclass, field
from urllib.parse import urljoin, urlparse, urlunparse
import re
import logging

from bs4 import BeautifulSoup, Tag


logger = logging.getLogger(__name__)


@dataclass
class LinkResource:
    url: str
    text: str
    source_type: str
    title: Optional[str] = None
    rel: Optional[str] = None
    target: Optional[str] = None
    is_internal: bool = False
    is_download: bool = False
    file_extension: Optional[str] = None


@dataclass
class AnchorInfo:
    text: str
    url: str
    position: int
    is_nofollow: bool = False
    is_sponsored: bool = False
    is_ugc: bool = False


class LinkExtractor:
    def __init__(self):
        self._file_extensions = {
            ".pdf", ".doc", ".docx", ".xls", ".xlsx", ".ppt", ".pptx",
            ".zip", ".rar", ".7z", ".tar", ".gz",
            ".mp3", ".mp4", ".avi", ".mov", ".wav",
            ".exe", ".dmg", ".apk", ".ipa",
        }

    def extract_internal_links(self, html: str, base_url: str) -> List[LinkResource]:
        soup = BeautifulSoup(html, "lxml")
        links = []
        
        base_domain = urlparse(base_url).netloc
        
        for a in soup.find_all("a", href=True):
            href = a["href"]
            
            if self._is_invalid_link(href):
                continue
            
            full_url = urljoin(base_url, href)
            normalized_url = self._normalize_url(full_url)
            
            parsed = urlparse(normalized_url)
            is_internal = parsed.netloc == base_domain or parsed.netloc == ""
            
            if is_internal:
                file_ext = self._get_file_extension(parsed.path)
                
                link_resource = LinkResource(
                    url=normalized_url,
                    text=a.get_text(strip=True),
                    source_type="internal",
                    title=a.get("title"),
                    rel=a.get("rel", [None])[0] if a.get("rel") else None,
                    target=a.get("target"),
                    is_internal=True,
                    is_download=file_ext in self._file_extensions if file_ext else False,
                    file_extension=file_ext,
                )
                links.append(link_resource)
        
        return links

    def extract_external_links(self, html: str, base_url: str) -> List[LinkResource]:
        soup = BeautifulSoup(html, "lxml")
        links = []
        
        base_domain = urlparse(base_url).netloc
        
        for a in soup.find_all("a", href=True):
            href = a["href"]
            
            if self._is_invalid_link(href):
                continue
            
            full_url = urljoin(base_url, href)
            normalized_url = self._normalize_url(full_url)
            
            parsed = urlparse(normalized_url)
            is_external = (
                parsed.scheme in ["http", "https"] and
                parsed.netloc != base_domain and
                parsed.netloc != ""
            )
            
            if is_external:
                file_ext = self._get_file_extension(parsed.path)
                
                link_resource = LinkResource(
                    url=normalized_url,
                    text=a.get_text(strip=True),
                    source_type="external",
                    title=a.get("title"),
                    rel=a.get("rel", [None])[0] if a.get("rel") else None,
                    target=a.get("target"),
                    is_internal=False,
                    is_download=file_ext in self._file_extensions if file_ext else False,
                    file_extension=file_ext,
                )
                links.append(link_resource)
        
        return links

    def extract_anchor_texts(self, html: str, base_url: Optional[str] = None) -> List[AnchorInfo]:
        soup = BeautifulSoup(html, "lxml")
        anchors = []
        
        position = 0
        for a in soup.find_all("a", href=True):
            href = a["href"]
            text = a.get_text(strip=True)
            
            if not text:
                continue
            
            if base_url:
                href = urljoin(base_url, href)
            
            rel = a.get("rel", [])
            rel_str = " ".join(rel) if isinstance(rel, list) else rel
            
            anchor_info = AnchorInfo(
                text=text,
                url=href,
                position=position,
                is_nofollow="nofollow" in rel_str,
                is_sponsored="sponsored" in rel_str,
                is_ugc="ugc" in rel_str,
            )
            anchors.append(anchor_info)
            position += 1
        
        return anchors

    def extract_all_links(self, html: str, base_url: str) -> List[LinkResource]:
        internal = self.extract_internal_links(html, base_url)
        external = self.extract_external_links(html, base_url)
        
        return internal + external

    def extract_links_by_domain(self, html: str, domain: str, base_url: str) -> List[LinkResource]:
        all_links = self.extract_all_links(html, base_url)
        
        return [
            link for link in all_links
            if domain in urlparse(link.url).netloc
        ]

    def extract_navigation_links(self, html: str, base_url: str) -> List[LinkResource]:
        soup = BeautifulSoup(html, "lxml")
        links = []
        
        nav_selectors = ["nav", ".nav", ".navigation", ".menu", "#menu", "header nav"]
        
        for selector in nav_selectors:
            try:
                nav = soup.select_one(selector)
                if nav:
                    for a in nav.find_all("a", href=True):
                        href = a["href"]
                        
                        if self._is_invalid_link(href):
                            continue
                        
                        full_url = urljoin(base_url, href)
                        normalized_url = self._normalize_url(full_url)
                        
                        link_resource = LinkResource(
                            url=normalized_url,
                            text=a.get_text(strip=True),
                            source_type="navigation",
                            title=a.get("title"),
                            target=a.get("target"),
                            is_internal=urlparse(normalized_url).netloc == urlparse(base_url).netloc,
                        )
                        links.append(link_resource)
            except Exception:
                continue
        
        return self._deduplicate_links(links)

    def extract_footer_links(self, html: str, base_url: str) -> List[LinkResource]:
        soup = BeautifulSoup(html, "lxml")
        links = []
        
        footer = soup.find("footer")
        if footer:
            for a in footer.find_all("a", href=True):
                href = a["href"]
                
                if self._is_invalid_link(href):
                    continue
                
                full_url = urljoin(base_url, href)
                normalized_url = self._normalize_url(full_url)
                
                link_resource = LinkResource(
                    url=normalized_url,
                    text=a.get_text(strip=True),
                    source_type="footer",
                    title=a.get("title"),
                    target=a.get("target"),
                    is_internal=urlparse(normalized_url).netloc == urlparse(base_url).netloc,
                )
                links.append(link_resource)
        
        return links

    def extract_social_links(self, html: str, base_url: str) -> Dict[str, List[str]]:
        soup = BeautifulSoup(html, "lxml")
        social_links = {}
        
        social_domains = {
            "facebook": ["facebook.com", "fb.com"],
            "twitter": ["twitter.com", "x.com"],
            "instagram": ["instagram.com"],
            "linkedin": ["linkedin.com"],
            "youtube": ["youtube.com", "youtu.be"],
            "github": ["github.com"],
            "weibo": ["weibo.com"],
            "weixin": ["weixin.qq.com", "wechat.com"],
            "douyin": ["douyin.com", "tiktok.com"],
            "zhihu": ["zhihu.com"],
        }
        
        for a in soup.find_all("a", href=True):
            href = a["href"]
            
            if base_url:
                href = urljoin(base_url, href)
            
            parsed = urlparse(href)
            
            for platform, domains in social_domains.items():
                if any(domain in parsed.netloc for domain in domains):
                    if platform not in social_links:
                        social_links[platform] = []
                    social_links[platform].append(href)
                    break
        
        return social_links

    def extract_sitemap_links(self, html: str, base_url: str) -> List[str]:
        soup = BeautifulSoup(html, "lxml")
        links = []
        
        for a in soup.find_all("a", href=True):
            href = a["href"]
            
            if self._is_invalid_link(href):
                continue
            
            full_url = urljoin(base_url, href)
            normalized_url = self._normalize_url(full_url)
            
            links.append(normalized_url)
        
        return list(set(links))

    def get_unique_domains(self, html: str, base_url: str) -> Set[str]:
        all_links = self.extract_all_links(html, base_url)
        
        domains = set()
        for link in all_links:
            if not link.is_internal:
                parsed = urlparse(link.url)
                domains.add(parsed.netloc)
        
        return domains

    def count_links(self, html: str, base_url: str) -> Dict[str, int]:
        internal = self.extract_internal_links(html, base_url)
        external = self.extract_external_links(html, base_url)
        
        return {
            "total": len(internal) + len(external),
            "internal": len(internal),
            "external": len(external),
            "unique_internal": len(set(link.url for link in internal)),
            "unique_external": len(set(link.url for link in external)),
        }

    def _is_invalid_link(self, href: str) -> bool:
        if not href:
            return True
        
        invalid_prefixes = ["javascript:", "mailto:", "tel:", "#", "data:"]
        
        href_lower = href.strip().lower()
        
        for prefix in invalid_prefixes:
            if href_lower.startswith(prefix):
                return True
        
        return False

    def _normalize_url(self, url: str) -> str:
        parsed = urlparse(url)
        
        parsed = parsed._replace(
            scheme=parsed.scheme.lower(),
            netloc=parsed.netloc.lower(),
        )
        
        if parsed.path.endswith("/"):
            parsed = parsed._replace(path=parsed.path[:-1])
        
        return urlunparse(parsed)

    def _get_file_extension(self, path: str) -> Optional[str]:
        path = path.lower()
        
        for ext in self._file_extensions:
            if path.endswith(ext):
                return ext
        
        return None

    def _deduplicate_links(self, links: List[LinkResource]) -> List[LinkResource]:
        seen = set()
        unique_links = []
        
        for link in links:
            if link.url not in seen:
                seen.add(link.url)
                unique_links.append(link)
        
        return unique_links
