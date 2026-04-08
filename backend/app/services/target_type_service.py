import re
import hashlib
import logging
from typing import Dict, List, Any, Optional
from urllib.parse import urljoin, urlparse
from bs4 import BeautifulSoup
import aiohttp
import asyncio

logger = logging.getLogger(__name__)

IMAGE_EXTENSIONS = {'.jpg', '.jpeg', '.png', '.gif', '.webp', '.svg', '.bmp', '.ico', '.tiff', '.avif'}
VIDEO_EXTENSIONS = {'.mp4', '.webm', '.avi', '.mkv', '.mov', '.wmv', '.flv', '.m4v'}
DOCUMENT_EXTENSIONS = {'.pdf', '.doc', '.docx', '.xls', '.xlsx', '.ppt', '.pptx', '.txt'}
ARCHIVE_EXTENSIONS = {'.zip', '.rar', '.7z', '.tar', '.gz'}


def get_extension_from_url(url: str) -> str:
    parsed = urlparse(url)
    path = parsed.path.lower()
    for ext in IMAGE_EXTENSIONS | VIDEO_EXTENSIONS | DOCUMENT_EXTENSIONS | ARCHIVE_EXTENSIONS:
        if path.endswith(ext):
            return ext
    return ''


def is_image_url(url: str) -> bool:
    ext = get_extension_from_url(url)
    return ext in IMAGE_EXTENSIONS


def is_video_url(url: str) -> bool:
    ext = get_extension_from_url(url)
    return ext in VIDEO_EXTENSIONS


def is_file_url(url: str) -> bool:
    ext = get_extension_from_url(url)
    return ext in (DOCUMENT_EXTENSIONS | ARCHIVE_EXTENSIONS)


async def fetch_html(url: str, timeout: int = 30) -> Optional[str]:
    try:
        async with aiohttp.ClientSession() as session:
            async with session.get(url, timeout=aiohttp.ClientTimeout(total=timeout)) as response:
                if response.status == 200:
                    return await response.text()
    except Exception as e:
        logger.error(f"Failed to fetch HTML from {url}: {e}")
    return None


def process_images(html: str, config: Dict[str, Any], base_url: str = '') -> List[Dict[str, Any]]:
    results = []
    soup = BeautifulSoup(html, 'html.parser')
    
    img_tags = soup.find_all('img')
    for img in img_tags:
        src = img.get('src') or img.get('data-src') or img.get('data-original')
        if not src:
            continue
        
        if src.startswith('//'):
            src = 'https:' + src
        elif src.startswith('/'):
            src = urljoin(base_url, src)
        elif not src.startswith('http'):
            src = urljoin(base_url, src)
        
        image_info = {
            'url': src,
            'alt': img.get('alt', ''),
            'title': img.get('title', ''),
            'width': img.get('width'),
            'height': img.get('height'),
            'type': 'image'
        }
        
        if config.get('download', True):
            image_info['should_download'] = True
        
        if config.get('keepOriginal', True):
            image_info['keep_original'] = True
        
        if config.get('convertFormat'):
            image_info['convert_to'] = config['convertFormat']
        
        if config.get('quality'):
            image_info['quality'] = config['quality']
        
        if config.get('watermark', {}).get('enabled'):
            image_info['watermark'] = {
                'enabled': True,
                'text': config['watermark'].get('text', '')
            }
        
        results.append(image_info)
    
    css_bg_pattern = re.compile(r'url\(["\']?([^"\'()]+)["\']?\)')
    for element in soup.find_all(style=True):
        style = element.get('style', '')
        matches = css_bg_pattern.findall(style)
        for match in matches:
            if match.startswith('//'):
                match = 'https:' + match
            elif match.startswith('/'):
                match = urljoin(base_url, match)
            elif not match.startswith('http'):
                match = urljoin(base_url, match)
            
            if is_image_url(match):
                results.append({
                    'url': match,
                    'type': 'image',
                    'source': 'css_background',
                    'should_download': config.get('download', True)
                })
    
    logger.info(f"Processed {len(results)} images from HTML")
    return results


def process_videos(html: str, config: Dict[str, Any], base_url: str = '') -> List[Dict[str, Any]]:
    results = []
    soup = BeautifulSoup(html, 'html.parser')
    
    video_tags = soup.find_all('video')
    for video in video_tags:
        src = video.get('src')
        poster = video.get('poster')
        
        if src:
            if src.startswith('//'):
                src = 'https:' + src
            elif src.startswith('/'):
                src = urljoin(base_url, src)
            elif not src.startswith('http'):
                src = urljoin(base_url, src)
            
            video_info = {
                'url': src,
                'type': 'video',
                'poster': poster,
                'should_download': config.get('download', True)
            }
            
            if config.get('extractAudio'):
                video_info['extract_audio'] = True
            
            if config.get('generateThumbnail'):
                video_info['generate_thumbnail'] = True
            
            if config.get('maxDuration', 0) > 0:
                video_info['max_duration'] = config['maxDuration']
            
            if config.get('maxResolution'):
                video_info['max_resolution'] = config['maxResolution']
            
            results.append(video_info)
    
    source_tags = soup.find_all('source')
    for source in source_tags:
        src = source.get('src')
        if src:
            if src.startswith('//'):
                src = 'https:' + src
            elif src.startswith('/'):
                src = urljoin(base_url, src)
            elif not src.startswith('http'):
                src = urljoin(base_url, src)
            
            if is_video_url(src) or source.get('type', '').startswith('video/'):
                results.append({
                    'url': src,
                    'type': 'video',
                    'mime_type': source.get('type'),
                    'should_download': config.get('download', True)
                })
    
    iframe_pattern = re.compile(r'(youtube\.com|vimeo\.com|bilibili\.com|youku\.com)')
    iframe_tags = soup.find_all('iframe')
    for iframe in iframe_tags:
        src = iframe.get('src', '')
        if iframe_pattern.search(src):
            if src.startswith('//'):
                src = 'https:' + src
            results.append({
                'url': src,
                'type': 'embedded_video',
                'platform': 'embedded',
                'should_download': False
            })
    
    logger.info(f"Processed {len(results)} videos from HTML")
    return results


def process_text(html: str, config: Dict[str, Any], base_url: str = '') -> List[Dict[str, Any]]:
    results = []
    soup = BeautifulSoup(html, 'html.parser')
    
    for script in soup(['script', 'style', 'nav', 'footer', 'header']):
        script.decompose()
    
    text_config = config or {}
    
    if text_config.get('extractMain', True):
        main_content = soup.find('main') or soup.find('article') or soup.find('div', class_=re.compile(r'content|article|post|entry'))
        if main_content:
            text_soup = main_content
        else:
            text_soup = soup
    else:
        text_soup = soup
    
    paragraphs = text_soup.find_all(['p', 'h1', 'h2', 'h3', 'h4', 'h5', 'h6'])
    for p in paragraphs:
        text = p.get_text(strip=True)
        
        if text_config.get('stripHtml', True):
            text = BeautifulSoup(text, 'html.parser').get_text()
        
        if text_config.get('stripWhitespace', True):
            text = ' '.join(text.split())
        
        min_length = text_config.get('minLength', 0)
        if min_length > 0 and len(text) < min_length:
            continue
        
        if text:
            text_info = {
                'content': text,
                'tag': p.name,
                'type': 'text',
                'length': len(text)
            }
            
            if p.name.startswith('h'):
                text_info['heading_level'] = int(p.name[1])
            
            results.append(text_info)
    
    full_text = text_soup.get_text(separator='\n', strip=True)
    if text_config.get('stripWhitespace', True):
        full_text = '\n'.join(' '.join(line.split()) for line in full_text.split('\n') if line.strip())
    
    results.append({
        'content': full_text,
        'type': 'full_text',
        'length': len(full_text),
        'save_format': text_config.get('saveFormat', 'txt')
    })
    
    logger.info(f"Processed {len(results)} text segments from HTML")
    return results


def process_links(html: str, config: Dict[str, Any], base_url: str = '') -> List[Dict[str, Any]]:
    results = []
    soup = BeautifulSoup(html, 'html.parser')
    base_domain = urlparse(base_url).netloc if base_url else ''
    
    link_config = config or {}
    
    a_tags = soup.find_all('a', href=True)
    for a in a_tags:
        href = a.get('href', '')
        
        if href.startswith('#') or href.startswith('javascript:') or href.startswith('mailto:'):
            continue
        
        if href.startswith('//'):
            href = 'https:' + href
        elif href.startswith('/'):
            href = urljoin(base_url, href)
        elif not href.startswith('http'):
            href = urljoin(base_url, href)
        
        href_domain = urlparse(href).netloc
        is_internal = href_domain == base_domain
        
        if is_internal and not link_config.get('includeInternal', True):
            continue
        if not is_internal and not link_config.get('includeExternal', True):
            continue
        
        link_info = {
            'url': href,
            'type': 'link',
            'is_internal': is_internal,
            'domain': href_domain
        }
        
        if link_config.get('extractAnchorText', True):
            link_info['anchor_text'] = a.get_text(strip=True)
        
        if a.get('title'):
            link_info['title'] = a.get('title')
        
        if a.get('rel'):
            link_info['rel'] = a.get('rel')
        
        results.append(link_info)
    
    seen_urls = set()
    unique_results = []
    for link in results:
        if link['url'] not in seen_urls:
            seen_urls.add(link['url'])
            unique_results.append(link)
    
    logger.info(f"Processed {len(unique_results)} unique links from HTML")
    return unique_results


def process_files(html: str, config: Dict[str, Any], base_url: str = '') -> List[Dict[str, Any]]:
    results = []
    soup = BeautifulSoup(html, 'html.parser')
    
    file_config = config or {}
    
    a_tags = soup.find_all('a', href=True)
    for a in a_tags:
        href = a.get('href', '')
        
        if href.startswith('//'):
            href = 'https:' + href
        elif href.startswith('/'):
            href = urljoin(base_url, href)
        elif not href.startswith('http'):
            href = urljoin(base_url, href)
        
        ext = get_extension_from_url(href)
        
        if ext in DOCUMENT_EXTENSIONS:
            file_type = 'document'
        elif ext in ARCHIVE_EXTENSIONS:
            file_type = 'archive'
        elif ext and ext not in IMAGE_EXTENSIONS and ext not in VIDEO_EXTENSIONS:
            file_type = 'other'
        else:
            continue
        
        file_info = {
            'url': href,
            'type': 'file',
            'file_type': file_type,
            'extension': ext,
            'filename': urlparse(href).path.split('/')[-1],
            'should_download': file_config.get('download', True)
        }
        
        if file_config.get('keepOriginalName', True):
            file_info['keep_original_name'] = True
        
        if file_config.get('renamePattern'):
            file_info['rename_pattern'] = file_config['renamePattern']
        
        if file_config.get('extractArchive', False) and file_type == 'archive':
            file_info['extract_archive'] = True
        
        if file_config.get('computeHash'):
            file_info['compute_hash'] = file_config['computeHash']
        
        results.append(file_info)
    
    seen_urls = set()
    unique_results = []
    for file in results:
        if file['url'] not in seen_urls:
            seen_urls.add(file['url'])
            unique_results.append(file)
    
    logger.info(f"Processed {len(unique_results)} files from HTML")
    return unique_results


async def process_all_types(
    html: str,
    target_types: List[str],
    configs: Dict[str, Any],
    base_url: str = ''
) -> Dict[str, List[Dict[str, Any]]]:
    results = {}
    
    if 'image' in target_types:
        results['images'] = process_images(html, configs.get('image', {}), base_url)
    
    if 'video' in target_types:
        results['videos'] = process_videos(html, configs.get('video', {}), base_url)
    
    if 'text' in target_types:
        results['texts'] = process_text(html, configs.get('text', {}), base_url)
    
    if 'link' in target_types:
        results['links'] = process_links(html, configs.get('link', {}), base_url)
    
    if 'file' in target_types:
        results['files'] = process_files(html, configs.get('file', {}), base_url)
    
    return results


def get_resource_summary(results: Dict[str, List[Dict[str, Any]]]) -> Dict[str, int]:
    return {
        'images': len(results.get('images', [])),
        'videos': len(results.get('videos', [])),
        'texts': len(results.get('texts', [])),
        'links': len(results.get('links', [])),
        'files': len(results.get('files', [])),
        'total': sum(len(v) for v in results.values())
    }
