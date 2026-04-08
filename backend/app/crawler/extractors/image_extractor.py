from typing import List, Dict, Any, Optional
from dataclasses import dataclass, field
from urllib.parse import urljoin, urlparse
import re
import logging

from bs4 import BeautifulSoup, Tag


logger = logging.getLogger(__name__)


@dataclass
class ImageResource:
    url: str
    source_type: str
    alt: Optional[str] = None
    title: Optional[str] = None
    width: Optional[int] = None
    height: Optional[int] = None
    srcset: Optional[List[Dict[str, str]]] = None
    data_attributes: Dict[str, str] = field(default_factory=dict)


class ImageExtractor:
    def __init__(self):
        self._image_extensions = {
            ".jpg", ".jpeg", ".png", ".gif", ".webp", ".bmp", ".svg", ".ico", ".tiff", ".tif"
        }
        self._lazy_load_attributes = [
            "data-src", "data-original", "data-lazy-src", "data-lazy",
            "data-srcset", "data-lazy-srcset", "data-image", "data-url"
        ]

    def extract_img_tags(self, html: str, base_url: Optional[str] = None) -> List[ImageResource]:
        soup = BeautifulSoup(html, "lxml")
        images = []
        
        for img in soup.find_all("img"):
            src = self._get_image_src(img)
            
            if not src:
                continue
            
            if base_url:
                src = urljoin(base_url, src)
            
            srcset_list = self._parse_srcset(img.get("srcset"), base_url)
            
            data_attrs = {}
            for attr in self._lazy_load_attributes:
                if img.get(attr):
                    data_attrs[attr] = img.get(attr)
            
            width = self._parse_dimension(img.get("width"))
            height = self._parse_dimension(img.get("height"))
            
            image_resource = ImageResource(
                url=src,
                source_type="img_tag",
                alt=img.get("alt"),
                title=img.get("title"),
                width=width,
                height=height,
                srcset=srcset_list if srcset_list else None,
                data_attributes=data_attrs,
            )
            images.append(image_resource)
        
        return images

    def extract_background_images(self, html: str, base_url: Optional[str] = None) -> List[ImageResource]:
        soup = BeautifulSoup(html, "lxml")
        images = []
        
        bg_pattern = re.compile(
            r'url\(\s*[\'"]?\s*([^\'"\)\s]+)\s*[\'"]?\s*\)',
            re.IGNORECASE
        )
        
        for element in soup.find_all(style=True):
            style = element.get("style", "")
            
            matches = bg_pattern.findall(style)
            
            for match in matches:
                url = match.strip()
                
                if base_url:
                    url = urljoin(base_url, url)
                
                image_resource = ImageResource(
                    url=url,
                    source_type="background_image",
                )
                images.append(image_resource)
        
        for style_tag in soup.find_all("style"):
            if style_tag.string:
                matches = bg_pattern.findall(style_tag.string)
                
                for match in matches:
                    url = match.strip()
                    
                    if base_url:
                        url = urljoin(base_url, url)
                    
                    image_resource = ImageResource(
                        url=url,
                        source_type="style_tag",
                    )
                    images.append(image_resource)
        
        return images

    def extract_srcset(self, html: str, base_url: Optional[str] = None) -> List[Dict[str, Any]]:
        soup = BeautifulSoup(html, "lxml")
        srcset_data = []
        
        for img in soup.find_all("img", srcset=True):
            srcset = img.get("srcset")
            parsed = self._parse_srcset(srcset, base_url)
            
            srcset_data.append({
                "element": "img",
                "srcset": parsed,
                "original_srcset": srcset,
            })
        
        for source in soup.find_all("source", srcset=True):
            srcset = source.get("srcset")
            parsed = self._parse_srcset(srcset, base_url)
            
            srcset_data.append({
                "element": "source",
                "srcset": parsed,
                "original_srcset": srcset,
                "media": source.get("media"),
                "type": source.get("type"),
            })
        
        return srcset_data

    def extract_picture_sources(self, html: str, base_url: Optional[str] = None) -> List[ImageResource]:
        soup = BeautifulSoup(html, "lxml")
        images = []
        
        for picture in soup.find_all("picture"):
            for source in picture.find_all("source"):
                srcset = source.get("srcset")
                
                if srcset:
                    parsed = self._parse_srcset(srcset, base_url)
                    
                    for item in parsed:
                        image_resource = ImageResource(
                            url=item.get("url", ""),
                            source_type="picture_source",
                            data_attributes={
                                "media": source.get("media", ""),
                                "type": source.get("type", ""),
                            }
                        )
                        images.append(image_resource)
        
        return images

    def extract_all_images(self, html: str, base_url: Optional[str] = None) -> List[ImageResource]:
        all_images = []
        
        all_images.extend(self.extract_img_tags(html, base_url))
        all_images.extend(self.extract_background_images(html, base_url))
        all_images.extend(self.extract_picture_sources(html, base_url))
        
        unique_images = {}
        for img in all_images:
            if img.url not in unique_images:
                unique_images[img.url] = img
        
        return list(unique_images.values())

    def filter_by_size(
        self,
        images: List[ImageResource],
        min_width: Optional[int] = None,
        min_height: Optional[int] = None,
        max_width: Optional[int] = None,
        max_height: Optional[int] = None,
    ) -> List[ImageResource]:
        filtered = []
        
        for img in images:
            if min_width and (img.width is None or img.width < min_width):
                continue
            if min_height and (img.height is None or img.height < min_height):
                continue
            if max_width and (img.width is None or img.width > max_width):
                continue
            if max_height and (img.height is None or img.height > max_height):
                continue
            
            filtered.append(img)
        
        return filtered

    def filter_by_extension(
        self,
        images: List[ImageResource],
        extensions: List[str],
        include: bool = True,
    ) -> List[ImageResource]:
        extensions = [ext.lower() for ext in extensions]
        filtered = []
        
        for img in images:
            parsed = urlparse(img.url)
            ext = parsed.path.lower()
            
            has_ext = any(ext.endswith(e) for e in extensions)
            
            if include and has_ext:
                filtered.append(img)
            elif not include and not has_ext:
                filtered.append(img)
        
        return filtered

    def is_image_url(self, url: str) -> bool:
        parsed = urlparse(url)
        path = parsed.path.lower()
        
        if any(path.endswith(ext) for ext in self._image_extensions):
            return True
        
        if "image" in parsed.query.lower():
            return True
        
        return False

    def _get_image_src(self, img: Tag) -> Optional[str]:
        src = img.get("src")
        
        if src and not src.startswith("data:"):
            return src
        
        for attr in self._lazy_load_attributes:
            value = img.get(attr)
            if value and not value.startswith("data:"):
                return value
        
        return None

    def _parse_srcset(self, srcset: Optional[str], base_url: Optional[str] = None) -> List[Dict[str, str]]:
        if not srcset:
            return []
        
        result = []
        parts = srcset.split(",")
        
        for part in parts:
            part = part.strip()
            if not part:
                continue
            
            items = part.split()
            
            if len(items) >= 1:
                url = items[0]
                
                if base_url:
                    url = urljoin(base_url, url)
                
                descriptor = items[1] if len(items) >= 2 else ""
                
                result.append({
                    "url": url,
                    "descriptor": descriptor,
                })
        
        return result

    def _parse_dimension(self, value: Optional[str]) -> Optional[int]:
        if not value:
            return None
        
        try:
            value = value.strip().rstrip("px")
            return int(value)
        except (ValueError, AttributeError):
            return None
