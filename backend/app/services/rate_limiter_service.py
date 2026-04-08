import re
import logging
from typing import Dict, List, Any, Optional
from urllib.parse import urlparse, urljoin
import time
import requests
from backend.app.models.intercepted_resource import InterceptedResource
from sqlalchemy.orm import Session

logger = logging.getLogger(__name__)


class RateLimiter:
    def __init__(self):
        self.domains: Dict[str, float] = {}
        self.robots_cache: Dict[str, Dict[str, Any]] = {}
    
    def check_rate_limit(self, domain: str, delay: float = 1.0) -> bool:
        if domain in self.domains:
            elapsed = time.time() - self.domains[domain]
            if elapsed < delay:
                return False
        return True
    
    def wait_if_needed(self, domain: str, delay: float = 1.0) -> None:
        if domain in self.domains:
            elapsed = time.time() - self.domains[domain]
            if elapsed < delay:
                wait_time = delay - elapsed
                logger.debug(f"Waiting {wait_time:.2f}s for domain {domain}")
                time.sleep(wait_time)
        self.domains[domain] = time.time()
    
    def parse_robots_txt(self, base_url: str) -> Dict[str, Any]:
        parsed = urlparse(base_url)
        robots_url = f"{parsed.scheme}://{parsed.netloc}/robots.txt"
        
        if robots_url in self.robots_cache:
            return self.robots_cache[robots_url]
        
        try:
            response = requests.get(robots_url, timeout=10)
            if response.status_code == 200:
                content = response.text
                rules = self._parse_robots_content(content)
                self.robots_cache[robots_url] = rules
                return rules
        except Exception as e:
            logger.warning(f"Failed to fetch robots.txt: {e}")
        
        self.robots_cache[robots_url] = {"allowed": [], "disallowed": []}
        return {"allowed": [], "disallowed": []}
    
    def _parse_robots_content(self, content: str) -> Dict[str, Any]:
        rules = {"allowed": [], "disallowed": []}
        current_user_agent = "*"
        
        for line in content.split("\n"):
            line = line.strip().lower()
            if line.startswith("user-agent:"):
                current_user_agent = line.split(":", 1)[1].strip()
            elif line.startswith("disallow:"):
                if current_user_agent == "*":
                    path = line.split(":", 1)[1].strip()
                    if path:
                        rules["disallowed"].append(path)
            elif line.startswith("allow:"):
                if current_user_agent == "*":
                    path = line.split(":", 1)[1].strip()
                    if path:
                        rules["allowed"].append(path)
        
        return rules
    
    def check_robots_allowed(self, url: str, base_url: str) -> bool:
        rules = self.parse_robots_txt(base_url)
        parsed = urlparse(url)
        path = parsed.path
        
        for disallowed in rules.get("disallowed", []):
            if path.startswith(disallowed):
                for allowed in rules.get("allowed", []):
                    if path.startswith(allowed) and len(allowed) > len(disallowed):
                        return True
                return False
        
        return True


rate_limiter = RateLimiter()


def check_rate_limit(domain: str, delay: float = 1.0) -> bool:
    return rate_limiter.check_rate_limit(domain, delay)


def wait_if_needed(domain: str, delay: float = 1.0) -> None:
    rate_limiter.wait_if_needed(domain, delay)


def parse_robots_txt(url: str) -> Dict[str, Any]:
    return rate_limiter.parse_robots_txt(url)


def check_robots_allowed(url: str, base_url: str) -> bool:
    return rate_limiter.check_robots_allowed(url, base_url)
