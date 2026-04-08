from typing import List, Dict, Any, Optional
from dataclasses import dataclass, field
from urllib.parse import urljoin, urlparse, parse_qs
import re
import logging

from bs4 import BeautifulSoup, Tag


logger = logging.getLogger(__name__)


@dataclass
class VideoResource:
    url: str
    source_type: str
    video_type: Optional[str] = None
    poster: Optional[str] = None
    width: Optional[int] = None
    height: Optional[int] = None
    duration: Optional[str] = None
    platform: Optional[str] = None
    embed_id: Optional[str] = None
    data_attributes: Dict[str, str] = field(default_factory=dict)


class VideoExtractor:
    def __init__(self):
        self._video_extensions = {
            ".mp4", ".webm", ".ogg", ".avi", ".mov", ".wmv", ".flv", ".mkv", ".m4v"
        }
        self._video_platforms = {
            "youtube": {
                "domains": ["youtube.com", "youtu.be", "www.youtube.com"],
                "patterns": [
                    r"(?:v=|embed/|youtu\.be/)([a-zA-Z0-9_-]{11})",
                ],
            },
            "bilibili": {
                "domains": ["bilibili.com", "www.bilibili.com", "b23.tv"],
                "patterns": [
                    r"video/(BV[a-zA-Z0-9]+)",
                    r"video/av(\d+)",
                ],
            },
            "youku": {
                "domains": ["youku.com", "v.youku.com"],
                "patterns": [
                    r"id_([a-zA-Z0-9=]+)",
                ],
            },
            "vimeo": {
                "domains": ["vimeo.com", "player.vimeo.com"],
                "patterns": [
                    r"vimeo\.com/(\d+)",
                    r"player\.vimeo\.com/video/(\d+)",
                ],
            },
            "dailymotion": {
                "domains": ["dailymotion.com", "www.dailymotion.com"],
                "patterns": [
                    r"dailymotion\.com/video/([a-zA-Z0-9]+)",
                ],
            },
        }

    def extract_video_tags(self, html: str, base_url: Optional[str] = None) -> List[VideoResource]:
        soup = BeautifulSoup(html, "lxml")
        videos = []
        
        for video in soup.find_all("video"):
            sources = []
            
            if video.get("src"):
                sources.append(video["src"])
            
            for source in video.find_all("source"):
                if source.get("src"):
                    sources.append(source["src"])
            
            for src in sources:
                url = src
                
                if base_url:
                    url = urljoin(base_url, url)
                
                width = self._parse_dimension(video.get("width"))
                height = self._parse_dimension(video.get("height"))
                
                video_resource = VideoResource(
                    url=url,
                    source_type="video_tag",
                    video_type=video.get("type"),
                    poster=video.get("poster"),
                    width=width,
                    height=height,
                    duration=video.get("duration"),
                )
                videos.append(video_resource)
        
        return videos

    def extract_video_links(self, html: str, base_url: Optional[str] = None) -> List[VideoResource]:
        soup = BeautifulSoup(html, "lxml")
        videos = []
        
        for a in soup.find_all("a", href=True):
            href = a["href"]
            
            if self.is_video_url(href):
                url = href
                
                if base_url:
                    url = urljoin(base_url, url)
                
                video_resource = VideoResource(
                    url=url,
                    source_type="link",
                )
                videos.append(video_resource)
        
        return videos

    def extract_iframe_videos(self, html: str, base_url: Optional[str] = None) -> List[VideoResource]:
        soup = BeautifulSoup(html, "lxml")
        videos = []
        
        for iframe in soup.find_all("iframe", src=True):
            src = iframe["src"]
            
            if base_url:
                src = urljoin(base_url, src)
            
            video_info = self._detect_embedded_video(src)
            
            if video_info:
                width = self._parse_dimension(iframe.get("width"))
                height = self._parse_dimension(iframe.get("height"))
                
                video_resource = VideoResource(
                    url=src,
                    source_type="iframe",
                    platform=video_info.get("platform"),
                    embed_id=video_info.get("video_id"),
                    width=width,
                    height=height,
                )
                videos.append(video_resource)
        
        return videos

    def extract_embed_videos(self, html: str, base_url: Optional[str] = None) -> List[VideoResource]:
        soup = BeautifulSoup(html, "lxml")
        videos = []
        
        for embed in soup.find_all("embed", src=True):
            src = embed["src"]
            
            if base_url:
                src = urljoin(base_url, src)
            
            if self.is_video_url(src):
                video_resource = VideoResource(
                    url=src,
                    source_type="embed",
                )
                videos.append(video_resource)
        
        return videos

    def extract_object_videos(self, html: str, base_url: Optional[str] = None) -> List[VideoResource]:
        soup = BeautifulSoup(html, "lxml")
        videos = []
        
        for obj in soup.find_all("object"):
            data = obj.get("data")
            
            if data:
                if base_url:
                    data = urljoin(base_url, data)
                
                if self.is_video_url(data):
                    video_resource = VideoResource(
                        url=data,
                        source_type="object",
                    )
                    videos.append(video_resource)
            
            for param in obj.find_all("param", attrs={"name": "movie"}):
                value = param.get("value")
                
                if value:
                    if base_url:
                        value = urljoin(base_url, value)
                    
                    if self.is_video_url(value):
                        video_resource = VideoResource(
                            url=value,
                            source_type="object_param",
                        )
                        videos.append(video_resource)
        
        return videos

    def extract_all_videos(self, html: str, base_url: Optional[str] = None) -> List[VideoResource]:
        all_videos = []
        
        all_videos.extend(self.extract_video_tags(html, base_url))
        all_videos.extend(self.extract_video_links(html, base_url))
        all_videos.extend(self.extract_iframe_videos(html, base_url))
        all_videos.extend(self.extract_embed_videos(html, base_url))
        all_videos.extend(self.extract_object_videos(html, base_url))
        
        unique_videos = {}
        for video in all_videos:
            if video.url not in unique_videos:
                unique_videos[video.url] = video
        
        return list(unique_videos.values())

    def extract_by_platform(self, html: str, platform: str, base_url: Optional[str] = None) -> List[VideoResource]:
        all_videos = self.extract_all_videos(html, base_url)
        
        platform_lower = platform.lower()
        
        return [
            video for video in all_videos
            if video.platform and video.platform.lower() == platform_lower
        ]

    def is_video_url(self, url: str) -> bool:
        parsed = urlparse(url)
        path = parsed.path.lower()
        
        if any(path.endswith(ext) for ext in self._video_extensions):
            return True
        
        if "video" in path:
            return True
        
        for platform_info in self._video_platforms.values():
            if parsed.netloc in platform_info["domains"]:
                return True
        
        return False

    def get_video_id(self, url: str, platform: str) -> Optional[str]:
        platform_lower = platform.lower()
        
        if platform_lower not in self._video_platforms:
            return None
        
        platform_info = self._video_platforms[platform_lower]
        parsed = urlparse(url)
        
        if parsed.netloc not in platform_info["domains"]:
            return None
        
        for pattern in platform_info["patterns"]:
            match = re.search(pattern, url)
            if match:
                return match.group(1)
        
        return None

    def _detect_embedded_video(self, url: str) -> Optional[Dict[str, Any]]:
        parsed = urlparse(url)
        
        for platform, info in self._video_platforms.items():
            if parsed.netloc in info["domains"]:
                video_id = None
                
                for pattern in info["patterns"]:
                    match = re.search(pattern, url)
                    if match:
                        video_id = match.group(1)
                        break
                
                return {
                    "platform": platform,
                    "video_id": video_id,
                }
        
        return None

    def _parse_dimension(self, value: Optional[str]) -> Optional[int]:
        if not value:
            return None
        
        try:
            value = value.strip().rstrip("px")
            return int(value)
        except (ValueError, AttributeError):
            return None
