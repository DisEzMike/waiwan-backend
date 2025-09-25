import os
import hashlib
import shutil
from typing import Optional, List
from pathlib import Path
from fastapi import UploadFile, HTTPException, status
import aiofiles
from PIL import Image
import io

# Configuration
UPLOAD_DIR = Path("uploads")
MAX_FILE_SIZE = 10 * 1024 * 1024  # 10MB
ALLOWED_IMAGE_TYPES = {"image/jpeg", "image/png", "image/gif", "image/webp"}
ALLOWED_DOCUMENT_TYPES = {"application/pdf", "text/plain", "application/msword", 
                         "application/vnd.openxmlformats-officedocument.wordprocessingml.document"}
ALLOWED_TYPES = ALLOWED_IMAGE_TYPES | ALLOWED_DOCUMENT_TYPES

# Image settings
MAX_IMAGE_WIDTH = 1920
MAX_IMAGE_HEIGHT = 1920
THUMBNAIL_SIZE = (300, 300)

class FileUploadError(Exception):
    pass

def ensure_upload_directory():
    """Create upload directories if they don't exist"""
    directories = [
        UPLOAD_DIR / "images",
        UPLOAD_DIR / "documents", 
        UPLOAD_DIR / "profiles",
        UPLOAD_DIR / "temp"
    ]
    
    for directory in directories:
        directory.mkdir(parents=True, exist_ok=True)

def validate_file(file: UploadFile) -> None:
    """Validate uploaded file"""
    # Check file size
    if hasattr(file.file, 'seek') and hasattr(file.file, 'tell'):
        file.file.seek(0, 2)  # Seek to end
        file_size = file.file.tell()
        file.file.seek(0)  # Reset to beginning
        
        if file_size > MAX_FILE_SIZE:
            raise FileUploadError(f"File too large. Maximum size is {MAX_FILE_SIZE / (1024*1024):.1f}MB")
    
    # Check content type
    if file.content_type not in ALLOWED_TYPES:
        raise FileUploadError(f"File type {file.content_type} not allowed")
    
    # Check filename
    if not file.filename or len(file.filename) > 255:
        raise FileUploadError("Invalid filename")

def generate_unique_filename(original_filename: str, file_hash: str) -> str:
    """Generate unique filename using hash"""
    file_extension = Path(original_filename).suffix.lower()
    return f"{file_hash[:16]}{file_extension}"

def get_file_hash(file_content: bytes) -> str:
    """Generate SHA256 hash of file content"""
    return hashlib.sha256(file_content).hexdigest()

def get_file_category(content_type: str) -> str:
    """Determine file category based on content type"""
    if content_type in ALLOWED_IMAGE_TYPES:
        return "images"
    elif content_type in ALLOWED_DOCUMENT_TYPES:
        return "documents"
    else:
        return "other"

async def process_image(file_content: bytes, max_width: int = MAX_IMAGE_WIDTH, 
                       max_height: int = MAX_IMAGE_HEIGHT) -> bytes:
    """Resize and optimize image"""
    try:
        # Open image
        image = Image.open(io.BytesIO(file_content))
        
        # Convert RGBA to RGB if necessary
        if image.mode in ('RGBA', 'LA', 'P'):
            background = Image.new('RGB', image.size, (255, 255, 255))
            if image.mode == 'P':
                image = image.convert('RGBA')
            background.paste(image, mask=image.split()[-1] if image.mode == 'RGBA' else None)
            image = background
        
        # Resize if too large
        if image.width > max_width or image.height > max_height:
            image.thumbnail((max_width, max_height), Image.Resampling.LANCZOS)
        
        # Save optimized image
        output = io.BytesIO()
        image.save(output, format='JPEG', quality=85, optimize=True)
        return output.getvalue()
        
    except Exception as e:
        raise FileUploadError(f"Error processing image: {str(e)}")

async def save_uploaded_file(file: UploadFile, user_id: str) -> tuple[str, bytes, str]:
    """Save uploaded file and return path, content, and hash"""
    try:
        # Read file content
        content = await file.read()
        
        # Generate file hash
        file_hash = get_file_hash(content)
        
        # Process image if it's an image file
        if file.content_type in ALLOWED_IMAGE_TYPES:
            content = await process_image(content)
        
        # Generate filename and path
        filename = generate_unique_filename(file.filename, file_hash)
        category = get_file_category(file.content_type)
        file_path = UPLOAD_DIR / category / filename
        
        # Ensure directory exists
        file_path.parent.mkdir(parents=True, exist_ok=True)
        
        # Save file
        async with aiofiles.open(file_path, 'wb') as f:
            await f.write(content)
        
        return str(file_path), content, file_hash
        
    except Exception as e:
        raise FileUploadError(f"Error saving file: {str(e)}")

async def delete_file(file_path: str) -> bool:
    """Delete file from filesystem"""
    try:
        if os.path.exists(file_path):
            os.remove(file_path)
            return True
        return False
    except Exception:
        return False

def get_file_url(file_path: str, base_url: str = "") -> str:
    """Generate URL for accessing file"""
    # Convert absolute path to relative path from uploads directory
    relative_path = Path(file_path).relative_to(UPLOAD_DIR)
    return f"{base_url}/files/{relative_path}"

# Initialize upload directories on import
ensure_upload_directory()