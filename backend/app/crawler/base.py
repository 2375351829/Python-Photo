from typing import Dict, Any, Optional, List
from dataclasses import dataclass, field
from abc import ABC, abstractmethod
import logging

from backend.app.crawler.http_client import HTTPClient
from backend.app.crawler.parser import HTMLParser


logger = logging.getLogger(__name__)


@dataclass
class CrawlerConfig:
    user_agent: str = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"
    timeout: int = 30
    max_retries: int = 3
    retry_delay: float = 1.0
    proxy: Optional[str] = None
    headers: Dict[str, str] = field(default_factory=dict)
    cookies: Dict[str, str] = field(default_factory=dict)
    max_concurrent: int = 10
    request_delay: float = 0.5
    follow_redirects: bool = True
    verify_ssl: bool = True


@dataclass
class ParseRule:
    selector: str
    selector_type: str = "css"
    attribute: Optional[str] = None
    multiple: bool = False
    default: Any = None
    transform: Optional[str] = None


@dataclass
class CrawlResult:
    url: str
    status_code: int
    content: Optional[str] = None
    data: Dict[str, Any] = field(default_factory=dict)
    links: List[str] = field(default_factory=list)
    images: List[str] = field(default_factory=list)
    videos: List[str] = field(default_factory=list)
    files: List[str] = field(default_factory=list)
    error: Optional[str] = None
    response_time: float = 0.0
    headers: Dict[str, str] = field(default_factory=dict)


class BaseCrawler(ABC):
    def __init__(self, config: Optional[CrawlerConfig] = None):
        self.config = config or CrawlerConfig()
        self.http_client: Optional[HTTPClient] = None
        self.parser: Optional[HTMLParser] = None
        self._is_initialized = False

    async def initialize(self) -> None:
        if self._is_initialized:
            return
        
        self.http_client = HTTPClient(
            user_agent=self.config.user_agent,
            timeout=self.config.timeout,
            max_retries=self.config.max_retries,
            retry_delay=self.config.retry_delay,
            proxy=self.config.proxy,
            headers=self.config.headers,
            cookies=self.config.cookies,
            verify_ssl=self.config.verify_ssl,
        )
        await self.http_client.initialize()
        self.parser = HTMLParser()
        self._is_initialized = True
        logger.info("Crawler initialized successfully")

    async def fetch(self, url: str, **kwargs) -> CrawlResult:
        if not self._is_initialized:
            await self.initialize()
        
        try:
            response = await self.http_client.get(url, **kwargs)
            
            result = CrawlResult(
                url=url,
                status_code=response.status_code,
                content=response.text,
                response_time=response.elapsed,
                headers=dict(response.headers),
            )
            
            return result
        except Exception as e:
            logger.error(f"Failed to fetch {url}: {str(e)}")
            return CrawlResult(
                url=url,
                status_code=0,
                error=str(e),
            )

    async def parse(self, html: str, rules: Dict[str, ParseRule]) -> Dict[str, Any]:
        if not self.parser:
            self.parser = HTMLParser()
        
        self.parser.parse(html)
        result = {}
        
        for field_name, rule in rules.items():
            try:
                extracted = self.extract(html, rule.selector, rule.selector_type)
                
                if rule.attribute and extracted:
                    if isinstance(extracted, list):
                        extracted = [item.get(rule.attribute, item) if isinstance(item, dict) else item for item in extracted]
                    elif isinstance(extracted, dict):
                        extracted = extracted.get(rule.attribute, extracted)
                
                if rule.transform:
                    extracted = self._apply_transform(extracted, rule.transform)
                
                result[field_name] = extracted if extracted is not None else rule.default
            except Exception as e:
                logger.warning(f"Failed to extract field '{field_name}': {str(e)}")
                result[field_name] = rule.default
        
        return result

    def extract(self, html: str, selector: str, selector_type: str = "css") -> Any:
        if not self.parser:
            self.parser = HTMLParser()
        
        self.parser.parse(html)
        
        if selector_type == "css":
            return self.parser.css_select(selector)
        elif selector_type == "xpath":
            return self.parser.xpath_select(selector)
        elif selector_type == "regex":
            return self.parser.regex_match(selector)
        else:
            raise ValueError(f"Unsupported selector type: {selector_type}")

    def _apply_transform(self, value: Any, transform: str) -> Any:
        if not value:
            return value
        
        transforms = {
            "strip": lambda x: x.strip() if isinstance(x, str) else x,
            "lower": lambda x: x.lower() if isinstance(x, str) else x,
            "upper": lambda x: x.upper() if isinstance(x, str) else x,
            "int": lambda x: int(x) if x else 0,
            "float": lambda x: float(x) if x else 0.0,
            "list": lambda x: [x] if not isinstance(x, list) else x,
        }
        
        if transform in transforms:
            return transforms[transform](value)
        
        return value

    async def close(self) -> None:
        if self.http_client:
            await self.http_client.close()
            self.http_client = None
        
        self.parser = None
        self._is_initialized = False
        logger.info("Crawler closed successfully")

    async def __aenter__(self):
        await self.initialize()
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        await self.close()

    @abstractmethod
    async def crawl(self, url: str, **kwargs) -> CrawlResult:
        pass
