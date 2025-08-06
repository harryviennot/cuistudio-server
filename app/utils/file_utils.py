import os
import tempfile
import requests
from typing import Optional
from urllib.parse import urlparse
import mimetypes

def is_valid_url(url: str) -> bool:
    """Check if a string is a valid URL"""
    try:
        result = urlparse(url)
        return all([result.scheme, result.netloc])
    except:
        return False

def get_file_extension(url: str) -> Optional[str]:
    """Get file extension from URL"""
    try:
        parsed = urlparse(url)
        path = parsed.path
        return os.path.splitext(path)[1].lower()
    except:
        return None

def is_image_file(url: str) -> bool:
    """Check if URL points to an image file"""
    image_extensions = {'.jpg', '.jpeg', '.png', '.gif', '.bmp', '.webp'}
    ext = get_file_extension(url)
    return ext in image_extensions

def is_video_file(url: str) -> bool:
    """Check if URL points to a video file"""
    video_extensions = {'.mp4', '.avi', '.mov', '.wmv', '.flv', '.webm', '.mkv'}
    ext = get_file_extension(url)
    return ext in video_extensions

async def download_file(url: str) -> Optional[bytes]:
    """Download file from URL"""
    try:
        response = requests.get(url, timeout=30)
        response.raise_for_status()
        return response.content
    except Exception as e:
        print(f"Error downloading file from {url}: {e}")
        return None

def save_temp_file(content: bytes, suffix: str = "") -> Optional[str]:
    """Save content to a temporary file and return the path"""
    try:
        with tempfile.NamedTemporaryFile(suffix=suffix, delete=False) as temp_file:
            temp_file.write(content)
            return temp_file.name
    except Exception as e:
        print(f"Error saving temporary file: {e}")
        return None

def cleanup_temp_file(file_path: str):
    """Delete a temporary file"""
    try:
        if os.path.exists(file_path):
            os.unlink(file_path)
    except Exception as e:
        print(f"Error cleaning up temporary file {file_path}: {e}") 