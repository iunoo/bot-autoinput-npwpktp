"""
Helper utilities for various common operations.
Provides validation, file operations, and other utility functions.
"""

import os
import re
import uuid
import hashlib
import mimetypes
import asyncio
import urllib.parse
import platform
from pathlib import Path
from typing import Optional, Union, List, Dict, Any, Tuple
from datetime import datetime, timedelta


def validate_file_size(file_size: int, max_size_mb: int) -> Tuple[bool, Optional[str]]:
    """
    Validate file size against maximum allowed size.
    
    Args:
        file_size: File size in bytes
        max_size_mb: Maximum size in MB
        
    Returns:
        Tuple of (is_valid, error_message)
    """
    if file_size <= 0:
        return False, "File kosong atau tidak valid"
    
    max_size_bytes = max_size_mb * 1024 * 1024
    
    if file_size > max_size_bytes:
        current_mb = file_size / 1024 / 1024
        return False, f"File terlalu besar ({current_mb:.1f}MB). Maksimal {max_size_mb}MB"
    
    return True, None


def validate_file_type(filename: str, allowed_extensions: List[str]) -> Tuple[bool, Optional[str]]:
    """
    Validate file type based on extension.
    
    Args:
        filename: Name of the file
        allowed_extensions: List of allowed extensions (e.g., ['.jpg', '.png'])
        
    Returns:
        Tuple of (is_valid, error_message)
    """
    if not filename:
        return False, "Nama file tidak valid"
    
    file_ext = Path(filename).suffix.lower()
    
    if not file_ext:
        return False, "File tidak memiliki ekstensi"
    
    if file_ext not in [ext.lower() for ext in allowed_extensions]:
        allowed_str = ", ".join(allowed_extensions)
        return False, f"Tipe file tidak didukung. Gunakan: {allowed_str}"
    
    return True, None


def sanitize_filename(filename: str, max_length: int = 255) -> str:
    """
    Sanitize filename for safe file system operations.
    
    Args:
        filename: Original filename
        max_length: Maximum filename length
        
    Returns:
        Sanitized filename
    """
    if not filename:
        return "untitled"
    
    # Remove path separators and invalid characters
    filename = os.path.basename(filename)
    invalid_chars = r'[<>:"/\\|?*]'
    sanitized = re.sub(invalid_chars, '_', filename)
    
    # Remove control characters
    sanitized = re.sub(r'[\x00-\x1f\x7f-\x9f]', '', sanitized)
    
    # Remove leading/trailing dots and spaces
    sanitized = sanitized.strip('. ')
    
    # Ensure not empty
    if not sanitized:
        sanitized = "untitled"
    
    # Limit length while preserving extension
    if len(sanitized) > max_length:
        name, ext = os.path.splitext(sanitized)
        max_name_len = max_length - len(ext)
        sanitized = name[:max_name_len] + ext
    
    return sanitized


def generate_random_id(length: int = 8) -> str:
    """
    Generate random alphanumeric ID.
    
    Args:
        length: Length of the ID
        
    Returns:
        Random ID string
    """
    return str(uuid.uuid4()).replace('-', '')[:length].upper()


def generate_hash(data: str, algorithm: str = 'sha256') -> str:
    """
    Generate hash of input data.
    
    Args:
        data: Data to hash
        algorithm: Hash algorithm ('md5', 'sha1', 'sha256')
        
    Returns:
        Hexadecimal hash string
    """
    if algorithm == 'md5':
        return hashlib.md5(data.encode()).hexdigest()
    elif algorithm == 'sha1':
        return hashlib.sha1(data.encode()).hexdigest()
    elif algorithm == 'sha256':
        return hashlib.sha256(data.encode()).hexdigest()
    else:
        raise ValueError(f"Unsupported hash algorithm: {algorithm}")


def get_mime_type(filename: str) -> str:
    """
    Get MIME type of file based on extension.
    
    Args:
        filename: Name of the file
        
    Returns:
        MIME type string
    """
    mime_type, _ = mimetypes.guess_type(filename)
    return mime_type or 'application/octet-stream'


def is_image_file(filename: str) -> bool:
    """
    Check if file is an image based on MIME type.
    
    Args:
        filename: Name of the file
        
    Returns:
        True if image file, False otherwise
    """
    mime_type = get_mime_type(filename)
    return mime_type.startswith('image/')


def is_document_file(filename: str) -> bool:
    """
    Check if file is a document (PDF, DOC, etc.).
    
    Args:
        filename: Name of the file
        
    Returns:
        True if document file, False otherwise
    """
    document_mimes = [
        'application/pdf',
        'application/msword',
        'application/vnd.openxmlformats-officedocument.wordprocessingml.document',
        'application/vnd.ms-excel',
        'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet',
        'text/plain'
    ]
    
    mime_type = get_mime_type(filename)
    return mime_type in document_mimes


def calculate_confidence_score(factors: Dict[str, float]) -> float:
    """
    Calculate confidence score based on various factors.
    
    Args:
        factors: Dictionary of factor names and their scores (0.0 to 1.0)
        
    Returns:
        Overall confidence score (0.0 to 1.0)
    """
    if not factors:
        return 0.0
    
    # Weight different factors
    weights = {
        'text_clarity': 0.3,
        'image_quality': 0.2,
        'field_completeness': 0.3,
        'validation_passed': 0.2
    }
    
    weighted_sum = 0.0
    total_weight = 0.0
    
    for factor, score in factors.items():
        weight = weights.get(factor, 0.1)  # Default weight for unknown factors
        weighted_sum += score * weight
        total_weight += weight
    
    return weighted_sum / total_weight if total_weight > 0 else 0.0


def parse_duration_string(duration_str: str) -> Optional[timedelta]:
    """
    Parse duration string like "5m", "1h30m", "2d" into timedelta.
    
    Args:
        duration_str: Duration string
        
    Returns:
        timedelta object or None if parsing fails
    """
    if not duration_str:
        return None
    
    # Pattern to match duration components
    pattern = r'(?:(\d+)d)?(?:(\d+)h)?(?:(\d+)m)?(?:(\d+)s)?'
    match = re.match(pattern, duration_str.strip().lower())
    
    if not match:
        return None
    
    days, hours, minutes, seconds = match.groups()
    
    return timedelta(
        days=int(days) if days else 0,
        hours=int(hours) if hours else 0,
        minutes=int(minutes) if minutes else 0,
        seconds=int(seconds) if seconds else 0
    )


def chunk_list(items: List[Any], chunk_size: int) -> List[List[Any]]:
    """
    Split list into chunks of specified size.
    
    Args:
        items: List to chunk
        chunk_size: Size of each chunk
        
    Returns:
        List of chunks
    """
    if chunk_size <= 0:
        return [items]
    
    return [items[i:i + chunk_size] for i in range(0, len(items), chunk_size)]


def deep_merge_dicts(dict1: Dict[str, Any], dict2: Dict[str, Any]) -> Dict[str, Any]:
    """
    Deep merge two dictionaries.
    
    Args:
        dict1: First dictionary
        dict2: Second dictionary (takes precedence)
        
    Returns:
        Merged dictionary
    """
    result = dict1.copy()
    
    for key, value in dict2.items():
        if key in result and isinstance(result[key], dict) and isinstance(value, dict):
            result[key] = deep_merge_dicts(result[key], value)
        else:
            result[key] = value
    
    return result


def flatten_dict(nested_dict: Dict[str, Any], separator: str = '.') -> Dict[str, Any]:
    """
    Flatten nested dictionary with dot notation keys.
    
    Args:
        nested_dict: Nested dictionary to flatten
        separator: Separator for nested keys
        
    Returns:
        Flattened dictionary
    """
    def _flatten(obj, parent_key=''):
        items = []
        
        if isinstance(obj, dict):
            for key, value in obj.items():
                new_key = f"{parent_key}{separator}{key}" if parent_key else key
                
                if isinstance(value, dict):
                    items.extend(_flatten(value, new_key).items())
                else:
                    items.append((new_key, value))
        else:
            items.append((parent_key, obj))
        
        return dict(items)
    
    return _flatten(nested_dict)


def retry_with_backoff(max_retries: int = 3, base_delay: float = 1.0, 
                      max_delay: float = 60.0, backoff_factor: float = 2.0):
    """
    Decorator for retry logic with exponential backoff.
    
    Args:
        max_retries: Maximum number of retry attempts
        base_delay: Base delay in seconds
        max_delay: Maximum delay in seconds
        backoff_factor: Multiplier for delay between retries
        
    Returns:
        Decorator function
    """
    def decorator(func):
        async def wrapper(*args, **kwargs):
            import random
            last_exception = None
            
            for attempt in range(max_retries + 1):
                try:
                    return await func(*args, **kwargs)
                except Exception as e:
                    last_exception = e
                    
                    if attempt == max_retries:
                        break
                    
                    # Calculate delay with exponential backoff
                    delay = min(base_delay * (backoff_factor ** attempt), max_delay)
                    
                    # Add some jitter to prevent thundering herd
                    jitter = random.uniform(0.1, 0.3) * delay
                    total_delay = delay + jitter
                    
                    await asyncio.sleep(total_delay)
            
            raise last_exception
        
        return wrapper
    return decorator


def validate_indonesian_phone(phone: str) -> Tuple[bool, Optional[str]]:
    """
    Validate Indonesian phone number format.
    
    Args:
        phone: Phone number string
        
    Returns:
        Tuple of (is_valid, normalized_number)
    """
    if not phone:
        return False, None
    
    # Remove all non-digit characters
    digits_only = re.sub(r'\D', '', phone)
    
    # Check if starts with country code
    if digits_only.startswith('62'):
        # Remove country code
        digits_only = digits_only[2:]
    elif digits_only.startswith('0'):
        # Remove leading zero
        digits_only = digits_only[1:]
    
    # Validate length (should be 9-12 digits after country code/leading zero removal)
    if len(digits_only) < 9 or len(digits_only) > 12:
        return False, None
    
    # Check if starts with valid operator codes
    valid_prefixes = ['8', '7', '9']  # Common Indonesian mobile prefixes
    if not any(digits_only.startswith(prefix) for prefix in valid_prefixes):
        return False, None
    
    # Return normalized format
    normalized = f"+62{digits_only}"
    return True, normalized


def validate_email(email: str) -> bool:
    """
    Simple email validation.
    
    Args:
        email: Email address to validate
        
    Returns:
        True if valid email format, False otherwise
    """
    if not email:
        return False
    
    # Simple regex for email validation
    email_pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
    return bool(re.match(email_pattern, email))


def generate_qr_code_url(data: str, size: int = 200) -> str:
    """
    Generate QR code URL using an online service.
    
    Args:
        data: Data to encode in QR code
        size: Size of QR code in pixels
        
    Returns:
        URL to QR code image
    """
    encoded_data = urllib.parse.quote(data)
    return f"https://api.qrserver.com/v1/create-qr-code/?size={size}x{size}&data={encoded_data}"


def extract_urls_from_text(text: str) -> List[str]:
    """
    Extract URLs from text.
    
    Args:
        text: Text to search for URLs
        
    Returns:
        List of found URLs
    """
    if not text:
        return []
    
    # URL regex pattern
    url_pattern = r'https?://(?:[-\w.])+(?:\:[0-9]+)?(?:/(?:[\w/_.])*(?:\?(?:[\w&=%.])*)?(?:\#(?:[\w.])*)?)?'
    
    return re.findall(url_pattern, text)


def create_backup_filename(original_filename: str, 
                          include_timestamp: bool = True) -> str:
    """
    Create backup filename with timestamp.
    
    Args:
        original_filename: Original filename
        include_timestamp: Whether to include timestamp
        
    Returns:
        Backup filename
    """
    path = Path(original_filename)
    name = path.stem
    extension = path.suffix
    
    if include_timestamp:
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        return f"{name}_backup_{timestamp}{extension}"
    else:
        return f"{name}_backup{extension}"


def get_system_info() -> Dict[str, Any]:
    """
    Get basic system information.
    
    Returns:
        Dictionary with system information
    """
    basic_info = {
        'platform': platform.platform(),
        'python_version': platform.python_version(),
        'cpu_count': os.cpu_count(),
        'memory_total': None,
        'memory_available': None,
        'disk_usage': None
    }
    
    # Try to get advanced info with psutil if available
    try:
        import psutil
        basic_info.update({
            'cpu_count': psutil.cpu_count(),
            'memory_total': psutil.virtual_memory().total,
            'memory_available': psutil.virtual_memory().available,
            'disk_usage': psutil.disk_usage('/').percent if os.name != 'nt' else psutil.disk_usage('C:').percent
        })
    except ImportError:
        # psutil not available, use basic info only
        pass
    
    return basic_info


def safe_cast(value: Any, target_type: type, default: Any = None) -> Any:
    """
    Safely cast value to target type with default fallback.
    
    Args:
        value: Value to cast
        target_type: Target type to cast to
        default: Default value if casting fails
        
    Returns:
        Casted value or default
    """
    try:
        if target_type == bool and isinstance(value, str):
            # Special handling for boolean strings
            return value.lower() in ('true', '1', 'yes', 'on')
        return target_type(value)
    except (ValueError, TypeError):
        return default


def mask_sensitive_data(data: str, mask_char: str = '*', 
                       visible_start: int = 2, visible_end: int = 2) -> str:
    """
    Mask sensitive data showing only start and end characters.
    
    Args:
        data: Data to mask
        mask_char: Character to use for masking
        visible_start: Number of visible characters at start
        visible_end: Number of visible characters at end
        
    Returns:
        Masked data string
    """
    if not data or len(data) <= visible_start + visible_end:
        return mask_char * len(data) if data else ""
    
    start = data[:visible_start]
    end = data[-visible_end:] if visible_end > 0 else ""
    middle_length = len(data) - visible_start - visible_end
    middle = mask_char * middle_length
    
    return f"{start}{middle}{end}"