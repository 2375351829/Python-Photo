from typing import List, Dict, Any, Optional
from dataclasses import dataclass, field
import re
import logging

from bs4 import BeautifulSoup, Tag, NavigableString
import lxml.html
from lxml.etree import XPath


logger = logging.getLogger(__name__)


@dataclass
class TextContent:
    text: str
    source_type: str
    position: Optional[int] = None
    tag: Optional[str] = None
    word_count: int = 0
    char_count: int = 0


@dataclass
class Paragraph:
    text: str
    html: str
    position: int
    word_count: int
    links: List[str] = field(default_factory=list)


class TextExtractor:
    def __init__(self):
        self._noise_selectors = [
            "script", "style", "nav", "footer", "header", "aside",
            ".sidebar", ".advertisement", ".ad", ".ads", ".comment",
            ".social-share", ".related-posts", ".navigation", ".menu",
        ]
        self._content_selectors = [
            "article", ".article", ".post", ".content", ".entry-content",
            ".post-content", ".article-content", "main", "#content",
            ".main-content", ".single-content", ".text-content",
        ]
        self._title_selectors = [
            "h1", ".title", ".post-title", ".article-title", ".entry-title",
            "header h1", "article h1", ".headline",
        ]

    def extract_title(self, html: str) -> Optional[str]:
        soup = BeautifulSoup(html, "lxml")
        
        for selector in self._title_selectors:
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
            return title
        
        og_title = soup.find("meta", property="og:title")
        if og_title and og_title.get("content"):
            return og_title["content"]
        
        return None

    def extract_content(self, html: str, min_paragraph_length: int = 50) -> str:
        soup = BeautifulSoup(html, "lxml")
        
        content_elem = None
        for selector in self._content_selectors:
            try:
                elem = soup.select_one(selector)
                if elem:
                    text = elem.get_text(strip=True)
                    if len(text) > min_paragraph_length * 3:
                        content_elem = elem
                        break
            except Exception:
                continue
        
        if not content_elem:
            content_elem = soup.find("body") or soup
        
        for selector in self._noise_selectors:
            for elem in content_elem.select(selector):
                elem.decompose()
        
        paragraphs = []
        for elem in content_elem.find_all(["p", "div"]):
            text = elem.get_text(strip=True)
            if len(text) >= min_paragraph_length:
                paragraphs.append(text)
        
        if not paragraphs:
            text = content_elem.get_text(separator="\n", strip=True)
            paragraphs = [p.strip() for p in text.split("\n") if len(p.strip()) >= min_paragraph_length]
        
        return "\n\n".join(paragraphs)

    def extract_paragraphs(self, html: str, min_length: int = 50) -> List[Paragraph]:
        soup = BeautifulSoup(html, "lxml")
        paragraphs = []
        
        for selector in self._noise_selectors:
            for elem in soup.select(selector):
                elem.decompose()
        
        position = 0
        for p in soup.find_all("p"):
            text = p.get_text(strip=True)
            
            if len(text) >= min_length:
                links = []
                for a in p.find_all("a", href=True):
                    links.append(a["href"])
                
                paragraph = Paragraph(
                    text=text,
                    html=str(p),
                    position=position,
                    word_count=len(text.split()),
                    links=links,
                )
                paragraphs.append(paragraph)
                position += 1
        
        return paragraphs

    def extract_headings(self, html: str) -> Dict[str, List[str]]:
        soup = BeautifulSoup(html, "lxml")
        headings = {}
        
        for level in range(1, 7):
            tag = f"h{level}"
            heading_list = []
            
            for h in soup.find_all(tag):
                text = h.get_text(strip=True)
                if text:
                    heading_list.append(text)
            
            if heading_list:
                headings[tag] = heading_list
        
        return headings

    def extract_meta_description(self, html: str) -> Optional[str]:
        soup = BeautifulSoup(html, "lxml")
        
        description = soup.find("meta", attrs={"name": "description"})
        if description and description.get("content"):
            return description["content"]
        
        og_description = soup.find("meta", property="og:description")
        if og_description and og_description.get("content"):
            return og_description["content"]
        
        return None

    def extract_keywords(self, html: str) -> List[str]:
        soup = BeautifulSoup(html, "lxml")
        
        keywords = soup.find("meta", attrs={"name": "keywords"})
        if keywords and keywords.get("content"):
            return [kw.strip() for kw in keywords["content"].split(",") if kw.strip()]
        
        return []

    def extract_author(self, html: str) -> Optional[str]:
        soup = BeautifulSoup(html, "lxml")
        
        author = soup.find("meta", attrs={"name": "author"})
        if author and author.get("content"):
            return author["content"]
        
        author = soup.find("span", class_="author")
        if author:
            return author.get_text(strip=True)
        
        author = soup.find("a", rel="author")
        if author:
            return author.get_text(strip=True)
        
        return None

    def extract_publish_date(self, html: str) -> Optional[str]:
        soup = BeautifulSoup(html, "lxml")
        
        date_selectors = [
            ("meta", {"property": "article:published_time"}),
            ("meta", {"itemprop": "datePublished"}),
            ("time", {"datetime": True}),
            ("span", {"class": "date"}),
            ("span", {"class": "published"}),
        ]
        
        for tag, attrs in date_selectors:
            elem = soup.find(tag, attrs)
            if elem:
                if tag == "time":
                    return elem.get("datetime") or elem.get_text(strip=True)
                elif tag == "meta":
                    return elem.get("content")
                else:
                    return elem.get_text(strip=True)
        
        return None

    def extract_text_by_selector(
        self,
        html: str,
        selector: str,
        extract_text: bool = True,
    ) -> List[str]:
        soup = BeautifulSoup(html, "lxml")
        
        elements = soup.select(selector)
        
        if extract_text:
            return [elem.get_text(strip=True) for elem in elements]
        
        return [str(elem) for elem in elements]

    def extract_clean_text(self, html: str) -> str:
        soup = BeautifulSoup(html, "lxml")
        
        for tag in soup.find_all(["script", "style", "nav", "footer", "header", "aside"]):
            tag.decompose()
        
        text = soup.get_text(separator=" ", strip=True)
        
        text = re.sub(r'\s+', ' ', text)
        
        return text.strip()

    def extract_word_count(self, html: str) -> int:
        text = self.extract_clean_text(html)
        return len(text.split())

    def extract_reading_time(self, html: str, words_per_minute: int = 200) -> int:
        word_count = self.extract_word_count(html)
        return max(1, word_count // words_per_minute)

    def detect_language(self, html: str) -> Optional[str]:
        soup = BeautifulSoup(html, "lxml")
        
        html_tag = soup.find("html")
        if html_tag and html_tag.get("lang"):
            return html_tag["lang"]
        
        meta = soup.find("meta", attrs={"http-equiv": "content-language"})
        if meta and meta.get("content"):
            return meta["content"]
        
        return None

    def extract_lists(self, html: str) -> Dict[str, List[List[str]]]:
        soup = BeautifulSoup(html, "lxml")
        lists = {"ul": [], "ol": []}
        
        for ul in soup.find_all("ul"):
            items = [li.get_text(strip=True) for li in ul.find_all("li")]
            if items:
                lists["ul"].append(items)
        
        for ol in soup.find_all("ol"):
            items = [li.get_text(strip=True) for li in ol.find_all("li")]
            if items:
                lists["ol"].append(items)
        
        return lists

    def extract_tables(self, html: str) -> List[Dict[str, Any]]:
        soup = BeautifulSoup(html, "lxml")
        tables = []
        
        for table in soup.find_all("table"):
            table_data = {
                "headers": [],
                "rows": [],
            }
            
            thead = table.find("thead")
            if thead:
                headers = thead.find_all("th")
                table_data["headers"] = [th.get_text(strip=True) for th in headers]
            
            tbody = table.find("tbody") or table
            for tr in tbody.find_all("tr"):
                cells = tr.find_all(["td", "th"])
                row = [cell.get_text(strip=True) for cell in cells]
                if row:
                    table_data["rows"].append(row)
            
            if table_data["rows"]:
                tables.append(table_data)
        
        return tables

    def extract_quotes(self, html: str) -> List[str]:
        soup = BeautifulSoup(html, "lxml")
        quotes = []
        
        for blockquote in soup.find_all("blockquote"):
            text = blockquote.get_text(strip=True)
            if text:
                quotes.append(text)
        
        for q in soup.find_all("q"):
            text = q.get_text(strip=True)
            if text:
                quotes.append(text)
        
        return quotes
