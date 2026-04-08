from typing import List, Dict, Any, Optional, Set
from dataclasses import dataclass, field
from urllib.parse import urljoin, urlparse, unquote
import re
import logging
import mimetypes

from bs4 import BeautifulSoup, Tag


logger = logging.getLogger(__name__)


@dataclass
class FileResource:
    url: str
    file_type: str
    extension: str
    source_type: str
    file_name: Optional[str] = None
    mime_type: Optional[str] = None
    size: Optional[int] = None
    text: Optional[str] = None


class FileExtractor:
    def __init__(self):
        self._file_types = {
            "document": {
                ".pdf", ".doc", ".docx", ".txt", ".rtf", ".odt", ".xls", ".xlsx",
                ".ppt", ".pptx", ".csv", ".tsv",
            },
            "archive": {
                ".zip", ".rar", ".7z", ".tar", ".gz", ".bz2", ".xz",
            },
            "audio": {
                ".mp3", ".wav", ".ogg", ".flac", ".aac", ".m4a", ".wma",
            },
            "video": {
                ".mp4", ".avi", ".mkv", ".mov", ".wmv", ".flv", ".webm",
            },
            "image": {
                ".jpg", ".jpeg", ".png", ".gif", ".bmp", ".svg", ".webp", ".ico",
            },
            "executable": {
                ".exe", ".msi", ".dmg", ".apk", ".ipa", ".deb", ".rpm",
            },
            "code": {
                ".py", ".js", ".java", ".cpp", ".c", ".h", ".php", ".rb", ".go",
                ".rs", ".ts", ".jsx", ".tsx", ".vue", ".html", ".css", ".scss",
            },
            "data": {
                ".json", ".xml", ".yaml", ".yml", ".sql", ".db", ".sqlite",
            },
        }
        
        self._all_extensions: Set[str] = set()
        for extensions in self._file_types.values():
            self._all_extensions.update(extensions)

    def extract_download_links(self, html: str, base_url: Optional[str] = None) -> List[FileResource]:
        soup = BeautifulSoup(html, "lxml")
        files = []
        
        for a in soup.find_all("a", href=True):
            href = a["href"]
            
            if self._is_file_url(href):
                url = href
                
                if base_url:
                    url = urljoin(base_url, url)
                
                file_info = self._create_file_resource(url, "link", a.get_text(strip=True))
                
                if file_info:
                    files.append(file_info)
        
        return files

    def extract_by_type(self, html: str, file_type: str, base_url: Optional[str] = None) -> List[FileResource]:
        all_files = self.extract_download_links(html, base_url)
        
        file_type_lower = file_type.lower()
        
        return [
            f for f in all_files
            if f.file_type == file_type_lower
        ]

    def extract_documents(self, html: str, base_url: Optional[str] = None) -> List[FileResource]:
        return self.extract_by_type(html, "document", base_url)

    def extract_archives(self, html: str, base_url: Optional[str] = None) -> List[FileResource]:
        return self.extract_by_type(html, "archive", base_url)

    def extract_audio_files(self, html: str, base_url: Optional[str] = None) -> List[FileResource]:
        return self.extract_by_type(html, "audio", base_url)

    def extract_video_files(self, html: str, base_url: Optional[str] = None) -> List[FileResource]:
        return self.extract_by_type(html, "video", base_url)

    def extract_code_files(self, html: str, base_url: Optional[str] = None) -> List[FileResource]:
        return self.extract_by_type(html, "code", base_url)

    def extract_data_files(self, html: str, base_url: Optional[str] = None) -> List[FileResource]:
        return self.extract_by_type(html, "data", base_url)

    def detect_file_type(self, url: str) -> Optional[str]:
        parsed = urlparse(url)
        path = parsed.path.lower()
        
        for file_type, extensions in self._file_types.items():
            for ext in extensions:
                if path.endswith(ext):
                    return file_type
        
        return None

    def get_file_extension(self, url: str) -> Optional[str]:
        parsed = urlparse(url)
        path = parsed.path.lower()
        
        for ext in self._all_extensions:
            if path.endswith(ext):
                return ext
        
        return None

    def get_mime_type(self, url: str) -> Optional[str]:
        extension = self.get_file_extension(url)
        
        if extension:
            mime_type, _ = mimetypes.guess_type(f"file{extension}")
            return mime_type
        
        return None

    def extract_file_name(self, url: str) -> Optional[str]:
        parsed = urlparse(url)
        path = unquote(parsed.path)
        
        if "/" in path:
            file_name = path.rsplit("/", 1)[-1]
        else:
            file_name = path
        
        if file_name:
            return file_name
        
        return None

    def extract_from_srcset(self, html: str, base_url: Optional[str] = None) -> List[FileResource]:
        soup = BeautifulSoup(html, "lxml")
        files = []
        
        for elem in soup.find_all(srcset=True):
            srcset = elem.get("srcset")
            
            for part in srcset.split(","):
                part = part.strip()
                
                if not part:
                    continue
                
                url = part.split()[0]
                
                if base_url:
                    url = urljoin(base_url, url)
                
                file_info = self._create_file_resource(url, "srcset")
                
                if file_info:
                    files.append(file_info)
        
        return files

    def extract_from_object(self, html: str, base_url: Optional[str] = None) -> List[FileResource]:
        soup = BeautifulSoup(html, "lxml")
        files = []
        
        for obj in soup.find_all("object"):
            data = obj.get("data")
            
            if data:
                url = data
                
                if base_url:
                    url = urljoin(base_url, url)
                
                file_info = self._create_file_resource(url, "object")
                
                if file_info:
                    files.append(file_info)
        
        return files

    def extract_from_embed(self, html: str, base_url: Optional[str] = None) -> List[FileResource]:
        soup = BeautifulSoup(html, "lxml")
        files = []
        
        for embed in soup.find_all("embed"):
            src = embed.get("src")
            
            if src:
                url = src
                
                if base_url:
                    url = urljoin(base_url, url)
                
                file_info = self._create_file_resource(url, "embed")
                
                if file_info:
                    files.append(file_info)
        
        return files

    def extract_all_files(self, html: str, base_url: Optional[str] = None) -> List[FileResource]:
        all_files = []
        
        all_files.extend(self.extract_download_links(html, base_url))
        all_files.extend(self.extract_from_srcset(html, base_url))
        all_files.extend(self.extract_from_object(html, base_url))
        all_files.extend(self.extract_from_embed(html, base_url))
        
        unique_files = {}
        for file in all_files:
            if file.url not in unique_files:
                unique_files[file.url] = file
        
        return list(unique_files.values())

    def filter_by_extension(
        self,
        files: List[FileResource],
        extensions: List[str],
        include: bool = True,
    ) -> List[FileResource]:
        extensions_lower = [ext.lower() for ext in extensions]
        
        filtered = []
        for file in files:
            has_ext = file.extension in extensions_lower
            
            if include and has_ext:
                filtered.append(file)
            elif not include and not has_ext:
                filtered.append(file)
        
        return filtered

    def filter_by_type(
        self,
        files: List[FileResource],
        file_types: List[str],
        include: bool = True,
    ) -> List[FileResource]:
        types_lower = [t.lower() for t in file_types]
        
        filtered = []
        for file in files:
            has_type = file.file_type in types_lower
            
            if include and has_type:
                filtered.append(file)
            elif not include and not has_type:
                filtered.append(file)
        
        return filtered

    def get_file_statistics(self, html: str, base_url: Optional[str] = None) -> Dict[str, int]:
        all_files = self.extract_all_files(html, base_url)
        
        stats = {
            "total": len(all_files),
        }
        
        for file_type in self._file_types:
            stats[file_type] = 0
        
        for file in all_files:
            if file.file_type in stats:
                stats[file.file_type] += 1
        
        return stats

    def _is_file_url(self, url: str) -> bool:
        if not url:
            return False
        
        url_lower = url.lower()
        
        invalid_prefixes = ["javascript:", "mailto:", "tel:", "#", "data:"]
        for prefix in invalid_prefixes:
            if url_lower.startswith(prefix):
                return False
        
        parsed = urlparse(url)
        path = parsed.path.lower()
        
        for ext in self._all_extensions:
            if path.endswith(ext):
                return True
        
        return False

    def _create_file_resource(
        self,
        url: str,
        source_type: str,
        text: Optional[str] = None,
    ) -> Optional[FileResource]:
        file_type = self.detect_file_type(url)
        extension = self.get_file_extension(url)
        
        if not file_type or not extension:
            return None
        
        file_name = self.extract_file_name(url)
        mime_type = self.get_mime_type(url)
        
        return FileResource(
            url=url,
            file_type=file_type,
            extension=extension,
            source_type=source_type,
            file_name=file_name,
            mime_type=mime_type,
            text=text,
        )
