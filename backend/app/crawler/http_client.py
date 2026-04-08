import asyncio
import time
from typing import Dict, Any, Optional, List, Callable
from dataclasses import dataclass, field
from urllib.parse import urlparse, urljoin
import logging
import re

import httpx


logger = logging.getLogger(__name__)


@dataclass
class RequestInfo:
    url: str
    method: str
    headers: Dict[str, str]
    timestamp: float
    retry_count: int = 0


@dataclass
class ResponseInfo:
    url: str
    status_code: int
    headers: Dict[str, str]
    text: str
    elapsed: float
    request_info: Optional[RequestInfo] = None


@dataclass
class RetryConfig:
    max_retries: int = 3
    retry_delay: float = 1.0
    retry_on_status: List[int] = field(default_factory=lambda: [429, 500, 502, 503, 504])
    exponential_backoff: bool = True
    max_delay: float = 30.0


class HTTPClient:
    def __init__(
        self,
        user_agent: str = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36",
        timeout: int = 30,
        max_retries: int = 3,
        retry_delay: float = 1.0,
        proxy: Optional[str] = None,
        headers: Optional[Dict[str, str]] = None,
        cookies: Optional[Dict[str, str]] = None,
        verify_ssl: bool = True,
        follow_redirects: bool = True,
    ):
        self.user_agent = user_agent
        self.timeout = timeout
        self.retry_config = RetryConfig(
            max_retries=max_retries,
            retry_delay=retry_delay,
        )
        self.proxy = proxy
        self.verify_ssl = verify_ssl
        self.follow_redirects = follow_redirects
        
        self._default_headers = {
            "User-Agent": user_agent,
            "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8",
            "Accept-Language": "zh-CN,zh;q=0.9,en;q=0.8",
            "Accept-Encoding": "gzip, deflate, br",
            "Connection": "keep-alive",
        }
        
        if headers:
            self._default_headers.update(headers)
        
        self._cookies = cookies or {}
        self._client: Optional[httpx.AsyncClient] = None
        self._sync_client: Optional[httpx.Client] = None
        self._request_interceptors: List[Callable] = []
        self._response_interceptors: List[Callable] = []
        self._request_history: List[RequestInfo] = []

    async def initialize(self) -> None:
        if self._client is not None:
            return
        
        proxies = None
        if self.proxy:
            proxies = {
                "http://": self.proxy,
                "https://": self.proxy,
            }
        
        self._client = httpx.AsyncClient(
            headers=self._default_headers,
            cookies=self._cookies,
            timeout=httpx.Timeout(self.timeout),
            verify=self.verify_ssl,
            follow_redirects=self.follow_redirects,
            proxies=proxies,
        )
        
        logger.info("HTTP client initialized successfully")

    def add_request_interceptor(self, interceptor: Callable) -> None:
        self._request_interceptors.append(interceptor)

    def add_response_interceptor(self, interceptor: Callable) -> None:
        self._response_interceptors.append(interceptor)

    async def _apply_request_interceptors(self, request_args: Dict[str, Any]) -> Dict[str, Any]:
        for interceptor in self._request_interceptors:
            request_args = await interceptor(request_args) if asyncio.iscoroutinefunction(interceptor) else interceptor(request_args)
        return request_args

    async def _apply_response_interceptors(self, response: httpx.Response) -> httpx.Response:
        for interceptor in self._response_interceptors:
            response = await interceptor(response) if asyncio.iscoroutinefunction(interceptor) else interceptor(response)
        return response

    def _record_request(self, url: str, method: str, headers: Dict[str, str], retry_count: int = 0) -> RequestInfo:
        request_info = RequestInfo(
            url=url,
            method=method,
            headers=headers,
            timestamp=time.time(),
            retry_count=retry_count,
        )
        self._request_history.append(request_info)
        return request_info

    async def _retry_request(
        self,
        method: str,
        url: str,
        retry_count: int = 0,
        **kwargs
    ) -> httpx.Response:
        if retry_count >= self.retry_config.max_retries:
            raise httpx.HTTPError(f"Max retries ({self.retry_config.max_retries}) exceeded for {url}")
        
        delay = self.retry_config.retry_delay
        if self.retry_config.exponential_backoff:
            delay = min(
                self.retry_config.retry_delay * (2 ** retry_count),
                self.retry_config.max_delay
            )
        
        if retry_count > 0:
            logger.warning(f"Retrying {url} (attempt {retry_count + 1}/{self.retry_config.max_retries}) after {delay}s")
            await asyncio.sleep(delay)
        
        try:
            response = await self._client.request(method, url, **kwargs)
            
            if response.status_code in self.retry_config.retry_on_status:
                return await self._retry_request(method, url, retry_count + 1, **kwargs)
            
            return response
        except (httpx.ConnectError, httpx.ReadTimeout, httpx.WriteTimeout) as e:
            logger.warning(f"Request failed for {url}: {str(e)}")
            return await self._retry_request(method, url, retry_count + 1, **kwargs)

    async def request(
        self,
        method: str,
        url: str,
        headers: Optional[Dict[str, str]] = None,
        cookies: Optional[Dict[str, str]] = None,
        params: Optional[Dict[str, Any]] = None,
        data: Optional[Any] = None,
        json: Optional[Any] = None,
        **kwargs
    ) -> ResponseInfo:
        if self._client is None:
            await self.initialize()
        
        request_headers = dict(self._default_headers)
        if headers:
            request_headers.update(headers)
        
        request_args = {
            "method": method,
            "url": url,
            "headers": request_headers,
            "cookies": cookies or self._cookies,
            "params": params,
            "data": data,
            "json": json,
            **kwargs
        }
        
        request_args = await self._apply_request_interceptors(request_args)
        
        start_time = time.time()
        request_info = self._record_request(url, method, request_headers)
        
        try:
            response = await self._retry_request(
                request_args.pop("method"),
                request_args.pop("url"),
                **request_args
            )
            
            response = await self._apply_response_interceptors(response)
            
            elapsed = time.time() - start_time
            
            return ResponseInfo(
                url=str(response.url),
                status_code=response.status_code,
                headers=dict(response.headers),
                text=response.text,
                elapsed=elapsed,
                request_info=request_info,
            )
        except Exception as e:
            logger.error(f"Request failed for {url}: {str(e)}")
            raise

    async def get(self, url: str, **kwargs) -> ResponseInfo:
        return await self.request("GET", url, **kwargs)

    async def post(self, url: str, **kwargs) -> ResponseInfo:
        return await self.request("POST", url, **kwargs)

    async def put(self, url: str, **kwargs) -> ResponseInfo:
        return await self.request("PUT", url, **kwargs)

    async def delete(self, url: str, **kwargs) -> ResponseInfo:
        return await self.request("DELETE", url, **kwargs)

    async def head(self, url: str, **kwargs) -> ResponseInfo:
        return await self.request("HEAD", url, **kwargs)

    async def download(self, url: str, save_path: str, chunk_size: int = 8192, **kwargs) -> str:
        if self._client is None:
            await self.initialize()
        
        async with self._client.stream("GET", url, **kwargs) as response:
            response.raise_for_status()
            
            with open(save_path, "wb") as f:
                async for chunk in response.aiter_bytes(chunk_size):
                    f.write(chunk)
        
        logger.info(f"Downloaded {url} to {save_path}")
        return save_path

    def get_request_history(self) -> List[RequestInfo]:
        return self._request_history.copy()

    def clear_request_history(self) -> None:
        self._request_history.clear()

    async def close(self) -> None:
        if self._client:
            await self._client.aclose()
            self._client = None
        
        if self._sync_client:
            self._sync_client.close()
            self._sync_client = None
        
        logger.info("HTTP client closed")

    async def __aenter__(self):
        await self.initialize()
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        await self.close()

    def _init_sync_client(self) -> None:
        if self._sync_client is not None:
            return
        
        proxies = None
        if self.proxy:
            proxies = {
                "http://": self.proxy,
                "https://": self.proxy,
            }
        
        self._sync_client = httpx.Client(
            headers=self._default_headers,
            cookies=self._cookies,
            timeout=httpx.Timeout(self.timeout),
            verify=self.verify_ssl,
            follow_redirects=self.follow_redirects,
            proxies=proxies,
        )

    def sync_get(self, url: str, **kwargs) -> ResponseInfo:
        self._init_sync_client()
        
        start_time = time.time()
        response = self._sync_client.get(url, **kwargs)
        elapsed = time.time() - start_time
        
        return ResponseInfo(
            url=str(response.url),
            status_code=response.status_code,
            headers=dict(response.headers),
            text=response.text,
            elapsed=elapsed,
        )

    def sync_post(self, url: str, **kwargs) -> ResponseInfo:
        self._init_sync_client()
        
        start_time = time.time()
        response = self._sync_client.post(url, **kwargs)
        elapsed = time.time() - start_time
        
        return ResponseInfo(
            url=str(response.url),
            status_code=response.status_code,
            headers=dict(response.headers),
            text=response.text,
            elapsed=elapsed,
        )
