import re
from typing import List, Dict, Any, Optional, Union
from dataclasses import dataclass, field
from urllib.parse import urljoin, urlparse
import logging

from bs4 import BeautifulSoup, Tag, NavigableString
from lxml import etree
import lxml.html


logger = logging.getLogger(__name__)


@dataclass
class LinkInfo:
    url: str
    text: str
    title: Optional[str] = None
    rel: Optional[str] = None
    target: Optional[str] = None


@dataclass
class ImageInfo:
    url: str
    alt: Optional[str] = None
    title: Optional[str] = None
    width: Optional[int] = None
    height: Optional[int] = None
    srcset: Optional[str] = None


@dataclass
class VideoInfo:
    url: str
    type: Optional[str] = None
    poster: Optional[str] = None
    width: Optional[int] = None
    height: Optional[int] = None


class HTMLParser:
    def __init__(self, parser: str = "lxml"):
        self.parser = parser
        self._soup: Optional[BeautifulSoup] = None
        self._lxml_tree: Optional[etree._Element] = None
        self._raw_html: Optional[str] = None
        self._base_url: Optional[str] = None

    def parse(self, html: str, base_url: Optional[str] = None) -> "HTMLParser":
        self._raw_html = html
        self._base_url = base_url
        self._soup = BeautifulSoup(html, self.parser)
        self._lxml_tree = lxml.html.fromstring(html)
        return self

    def _ensure_parsed(self) -> None:
        if self._soup is None or self._lxml_tree is None:
            raise ValueError("HTML not parsed. Call parse() first.")

    def css_select(self, selector: str, extract_text: bool = True) -> Union[List[str], List[Dict[str, Any]]]:
        self._ensure_parsed()
        
        elements = self._soup.select(selector)
        
        if not elements:
            return []
        
        if extract_text:
            return [elem.get_text(strip=True) for elem in elements]
        
        results = []
        for elem in elements:
            if isinstance(elem, Tag):
                elem_data = {
                    "tag": elem.name,
                    "text": elem.get_text(strip=True),
                    "attributes": dict(elem.attrs),
                }
                results.append(elem_data)
        
        return results

    def css_select_one(self, selector: str, extract_text: bool = True) -> Optional[Union[str, Dict[str, Any]]]:
        self._ensure_parsed()
        
        elem = self._soup.select_one(selector)
        
        if not elem:
            return None
        
        if extract_text:
            return elem.get_text(strip=True)
        
        if isinstance(elem, Tag):
            return {
                "tag": elem.name,
                "text": elem.get_text(strip=True),
                "attributes": dict(elem.attrs),
            }
        
        return None

    def xpath_select(self, xpath: str, extract_text: bool = True) -> Union[List[str], List[Dict[str, Any]]]:
        self._ensure_parsed()
        
        elements = self._lxml_tree.xpath(xpath)
        
        if not elements:
            return []
        
        results = []
        for elem in elements:
            if isinstance(elem, etree._Element):
                if extract_text:
                    text = elem.text_content().strip() if elem.text_content() else ""
                    results.append(text)
                else:
                    elem_data = {
                        "tag": elem.tag,
                        "text": elem.text_content().strip() if elem.text_content() else "",
                        "attributes": dict(elem.attrib),
                    }
                    results.append(elem_data)
            elif isinstance(elem, str):
                results.append(elem.strip())
        
        return results

    def xpath_select_one(self, xpath: str, extract_text: bool = True) -> Optional[Union[str, Dict[str, Any]]]:
        self._ensure_parsed()
        
        elements = self._lxml_tree.xpath(xpath)
        
        if not elements:
            return None
        
        elem = elements[0]
        
        if isinstance(elem, etree._Element):
            if extract_text:
                return elem.text_content().strip() if elem.text_content() else ""
            
            return {
                "tag": elem.tag,
                "text": elem.text_content().strip() if elem.text_content() else "",
                "attributes": dict(elem.attrib),
            }
        elif isinstance(elem, str):
            return elem.strip()
        
        return None

    def regex_match(self, pattern: str, flags: int = 0) -> List[str]:
        self._ensure_parsed()
        
        matches = re.findall(pattern, self._raw_html, flags)
        return list(matches) if matches else []

    def regex_search(self, pattern: str, flags: int = 0) -> Optional[str]:
        self._ensure_parsed()
        
        match = re.search(pattern, self._raw_html, flags)
        return match.group(0) if match else None

    def extract_text(self, selector: Optional[str] = None, strip: bool = True) -> str:
        self._ensure_parsed()
        
        if selector:
            elem = self._soup.select_one(selector)
            if elem:
                return elem.get_text(strip=strip)
            return ""
        
        return self._soup.get_text(strip=strip)

    def extract_paragraphs(self, min_length: int = 50) -> List[str]:
        self._ensure_parsed()
        
        paragraphs = []
        for p in self._soup.find_all("p"):
            text = p.get_text(strip=True)
            if len(text) >= min_length:
                paragraphs.append(text)
        
        return paragraphs

    def extract_links(self, base_url: Optional[str] = None) -> List[LinkInfo]:
        self._ensure_parsed()
        
        base = base_url or self._base_url
        links = []
        
        for a in self._soup.find_all("a", href=True):
            href = a["href"]
            
            if base:
                href = urljoin(base, href)
            
            link_info = LinkInfo(
                url=href,
                text=a.get_text(strip=True),
                title=a.get("title"),
                rel=a.get("rel", [None])[0] if a.get("rel") else None,
                target=a.get("target"),
            )
            links.append(link_info)
        
        return links

    def extract_internal_links(self, base_url: str) -> List[LinkInfo]:
        all_links = self.extract_links(base_url)
        base_domain = urlparse(base_url).netloc
        
        return [
            link for link in all_links
            if urlparse(link.url).netloc == base_domain
        ]

    def extract_external_links(self, base_url: str) -> List[LinkInfo]:
        all_links = self.extract_links(base_url)
        base_domain = urlparse(base_url).netloc
        
        return [
            link for link in all_links
            if link.url.startswith(("http://", "https://")) and urlparse(link.url).netloc != base_domain
        ]

    def extract_images(self, base_url: Optional[str] = None) -> List[ImageInfo]:
        self._ensure_parsed()
        
        base = base_url or self._base_url
        images = []
        
        for img in self._soup.find_all("img"):
            src = img.get("src") or img.get("data-src") or img.get("data-original")
            
            if not src:
                continue
            
            if base:
                src = urljoin(base, src)
            
            width = None
            height = None
            
            if img.get("width"):
                try:
                    width = int(img["width"])
                except ValueError:
                    pass
            
            if img.get("height"):
                try:
                    height = int(img["height"])
                except ValueError:
                    pass
            
            image_info = ImageInfo(
                url=src,
                alt=img.get("alt"),
                title=img.get("title"),
                width=width,
                height=height,
                srcset=img.get("srcset"),
            )
            images.append(image_info)
        
        return images

    def extract_videos(self, base_url: Optional[str] = None) -> List[VideoInfo]:
        self._ensure_parsed()
        
        base = base_url or self._base_url
        videos = []
        
        for video in self._soup.find_all("video"):
            src = video.get("src")
            
            if not src:
                source = video.find("source")
                if source:
                    src = source.get("src")
            
            if not src:
                continue
            
            if base:
                src = urljoin(base, src)
            
            width = None
            height = None
            
            if video.get("width"):
                try:
                    width = int(video["width"])
                except ValueError:
                    pass
            
            if video.get("height"):
                try:
                    height = int(video["height"])
                except ValueError:
                    pass
            
            video_info = VideoInfo(
                url=src,
                type=video.get("type"),
                poster=video.get("poster"),
                width=width,
                height=height,
            )
            videos.append(video_info)
        
        return videos

    def extract_meta_tags(self) -> Dict[str, str]:
        self._ensure_parsed()
        
        meta_tags = {}
        
        for meta in self._soup.find_all("meta"):
            name = meta.get("name") or meta.get("property") or meta.get("http-equiv")
            content = meta.get("content")
            
            if name and content:
                meta_tags[name] = content
        
        return meta_tags

    def extract_title(self) -> Optional[str]:
        self._ensure_parsed()
        
        title_tag = self._soup.find("title")
        if title_tag:
            return title_tag.get_text(strip=True)
        
        og_title = self._soup.find("meta", property="og:title")
        if og_title and og_title.get("content"):
            return og_title["content"]
        
        return None

    def extract_description(self) -> Optional[str]:
        self._ensure_parsed()
        
        description = self._soup.find("meta", attrs={"name": "description"})
        if description and description.get("content"):
            return description["content"]
        
        og_description = self._soup.find("meta", property="og:description")
        if og_description and og_description.get("content"):
            return og_description["content"]
        
        return None

    def extract_keywords(self) -> List[str]:
        self._ensure_parsed()
        
        keywords = self._soup.find("meta", attrs={"name": "keywords"})
        if keywords and keywords.get("content"):
            return [kw.strip() for kw in keywords["content"].split(",")]
        
        return []

    def extract_headings(self) -> Dict[str, List[str]]:
        self._ensure_parsed()
        
        headings = {}
        
        for level in range(1, 7):
            tag = f"h{level}"
            heading_list = []
            
            for h in self._soup.find_all(tag):
                text = h.get_text(strip=True)
                if text:
                    heading_list.append(text)
            
            if heading_list:
                headings[tag] = heading_list
        
        return headings

    def extract_forms(self) -> List[Dict[str, Any]]:
        self._ensure_parsed()
        
        forms = []
        
        for form in self._soup.find_all("form"):
            form_data = {
                "action": form.get("action"),
                "method": form.get("method", "get").upper(),
                "enctype": form.get("enctype"),
                "fields": [],
            }
            
            for input_tag in form.find_all(["input", "textarea", "select"]):
                field = {
                    "name": input_tag.get("name"),
                    "type": input_tag.get("type", "text"),
                    "value": input_tag.get("value", ""),
                    "required": input_tag.has_attr("required"),
                }
                form_data["fields"].append(field)
            
            forms.append(form_data)
        
        return forms

    def extract_scripts(self) -> List[Dict[str, str]]:
        self._ensure_parsed()
        
        scripts = []
        
        for script in self._soup.find_all("script"):
            script_data = {
                "src": script.get("src"),
                "type": script.get("type"),
                "content": script.string or "",
            }
            scripts.append(script_data)
        
        return scripts

    def extract_stylesheets(self) -> List[str]:
        self._ensure_parsed()
        
        stylesheets = []
        
        for link in self._soup.find_all("link", rel="stylesheet"):
            href = link.get("href")
            if href:
                stylesheets.append(href)
        
        return stylesheets

    def remove_elements(self, selectors: List[str]) -> "HTMLParser":
        self._ensure_parsed()
        
        for selector in selectors:
            for elem in self._soup.select(selector):
                elem.decompose()
        
        return self

    def get_clean_text(self) -> str:
        self._ensure_parsed()
        
        soup_copy = BeautifulSoup(str(self._soup), self.parser)
        
        for tag in soup_copy.find_all(["script", "style", "nav", "footer", "header", "aside"]):
            tag.decompose()
        
        return soup_copy.get_text(separator=" ", strip=True)

    def get_raw_html(self) -> Optional[str]:
        return self._raw_html

    def get_soup(self) -> Optional[BeautifulSoup]:
        return self._soup

    def get_lxml_tree(self) -> Optional[etree._Element]:
        return self._lxml_tree
