"""
Text formatting utilities for Telegram messages.
Provides various formatting functions for consistent message display.
"""

import re
import html
from datetime import datetime, timedelta
from typing import Optional, Union, List, Dict, Any


def format_npwp_15(npwp: str) -> str:
    """
    Format NPWP 15 digit with proper separators.
    Format: xx.xxx.xxx.x-xxx.xxx
    
    Args:
        npwp: NPWP 15 digit string
        
    Returns:
        Formatted NPWP string
    """
    if not npwp or len(npwp) != 15:
        return npwp or ""
    
    return f"{npwp[0:2]}.{npwp[2:5]}.{npwp[5:8]}.{npwp[8:9]}-{npwp[9:12]}.{npwp[12:15]}"


def format_id_16_digit(id_number: str) -> str:
    """
    Format 16-digit ID (NIK/NPWP) with spaces.
    Format: xxxx xxxx xxxx xxxx
    
    Args:
        id_number: 16 digit ID string
        
    Returns:
        Formatted ID string
    """
    if not id_number or len(id_number) != 16:
        return id_number or ""
    
    return f"{id_number[0:4]} {id_number[4:8]} {id_number[8:12]} {id_number[12:16]}"


def escape_markdown_v2(text: str) -> str:
    """
    Escape special characters for Telegram MarkdownV2.
    
    Args:
        text: Text to escape
        
    Returns:
        Escaped text safe for MarkdownV2
    """
    if not isinstance(text, str):
        text = str(text)
    
    # Characters that need escaping in MarkdownV2
    escape_chars = r'_*[]()~`>#+-=|{}.!'
    
    return re.sub(f'([{re.escape(escape_chars)}])', r'\\\1', text)


def escape_html(text: str) -> str:
    """
    Escape HTML special characters.
    
    Args:
        text: Text to escape
        
    Returns:
        HTML-escaped text
    """
    if not isinstance(text, str):
        text = str(text)
    
    return html.escape(text)


def format_file_size(size_bytes: int) -> str:
    """
    Format file size in human-readable format.
    
    Args:
        size_bytes: File size in bytes
        
    Returns:
        Formatted file size string
    """
    if size_bytes == 0:
        return "0 B"
    
    size_names = ["B", "KB", "MB", "GB"]
    size_bytes = float(size_bytes)
    
    i = 0
    while size_bytes >= 1024.0 and i < len(size_names) - 1:
        size_bytes /= 1024.0
        i += 1
    
    return f"{size_bytes:.1f} {size_names[i]}"


def format_duration(seconds: Union[int, float]) -> str:
    """
    Format duration in human-readable format.
    
    Args:
        seconds: Duration in seconds
        
    Returns:
        Formatted duration string
    """
    if seconds < 60:
        return f"{int(seconds)} detik"
    elif seconds < 3600:
        minutes = int(seconds // 60)
        remaining_seconds = int(seconds % 60)
        if remaining_seconds > 0:
            return f"{minutes} menit {remaining_seconds} detik"
        return f"{minutes} menit"
    else:
        hours = int(seconds // 3600)
        remaining_minutes = int((seconds % 3600) // 60)
        if remaining_minutes > 0:
            return f"{hours} jam {remaining_minutes} menit"
        return f"{hours} jam"


def format_timestamp(timestamp: datetime, 
                    format_type: str = "full") -> str:
    """
    Format timestamp in various formats.
    
    Args:
        timestamp: Datetime object to format
        format_type: Type of format ("full", "date", "time", "relative")
        
    Returns:
        Formatted timestamp string
    """
    if not isinstance(timestamp, datetime):
        return str(timestamp)
    
    if format_type == "full":
        return timestamp.strftime("%Y-%m-%d %H:%M:%S")
    elif format_type == "date":
        return timestamp.strftime("%Y-%m-%d")
    elif format_type == "time":
        return timestamp.strftime("%H:%M:%S")
    elif format_type == "relative":
        now = datetime.now()
        diff = now - timestamp
        
        if diff.days > 0:
            return f"{diff.days} hari lalu"
        elif diff.seconds > 3600:
            hours = diff.seconds // 3600
            return f"{hours} jam lalu"
        elif diff.seconds > 60:
            minutes = diff.seconds // 60
            return f"{minutes} menit lalu"
        else:
            return "Baru saja"
    else:
        return timestamp.strftime("%Y-%m-%d %H:%M:%S")


def format_percentage(value: float, decimals: int = 1) -> str:
    """
    Format number as percentage.
    
    Args:
        value: Value to format (0.0 to 1.0)
        decimals: Number of decimal places
        
    Returns:
        Formatted percentage string
    """
    return f"{value * 100:.{decimals}f}%"


def format_currency(amount: float, currency: str = "IDR") -> str:
    """
    Format amount as currency.
    
    Args:
        amount: Amount to format
        currency: Currency code
        
    Returns:
        Formatted currency string
    """
    if currency == "IDR":
        # Indonesian Rupiah formatting
        formatted = f"Rp {amount:,.0f}".replace(",", ".")
        return formatted
    else:
        return f"{currency} {amount:,.2f}"


def truncate_text(text: str, max_length: int = 100, 
                 suffix: str = "...") -> str:
    """
    Truncate text to specified length with suffix.
    
    Args:
        text: Text to truncate
        max_length: Maximum length including suffix
        suffix: Suffix to add when truncating
        
    Returns:
        Truncated text
    """
    if not text or len(text) <= max_length:
        return text
    
    return text[:max_length - len(suffix)] + suffix


def format_list(items: List[str], 
               style: str = "bullet",
               max_items: Optional[int] = None) -> str:
    """
    Format list of items with various styles.
    
    Args:
        items: List of items to format
        style: Format style ("bullet", "numbered", "comma")
        max_items: Maximum number of items to show
        
    Returns:
        Formatted list string
    """
    if not items:
        return ""
    
    # Limit items if specified
    display_items = items[:max_items] if max_items else items
    remaining_count = len(items) - len(display_items) if max_items else 0
    
    if style == "bullet":
        formatted = "\n".join(f"• {item}" for item in display_items)
    elif style == "numbered":
        formatted = "\n".join(f"{i+1}. {item}" for i, item in enumerate(display_items))
    elif style == "comma":
        formatted = ", ".join(display_items)
    else:
        formatted = "\n".join(display_items)
    
    # Add remaining count if items were truncated
    if remaining_count > 0:
        if style == "comma":
            formatted += f", dan {remaining_count} lainnya"
        else:
            formatted += f"\n... dan {remaining_count} item lainnya"
    
    return formatted


def format_table(data: List[Dict[str, Any]], 
                headers: Optional[List[str]] = None) -> str:
    """
    Format data as simple text table.
    
    Args:
        data: List of dictionaries with table data
        headers: Optional custom headers
        
    Returns:
        Formatted table string
    """
    if not data:
        return "Tidak ada data"
    
    # Get headers
    if headers:
        table_headers = headers
    else:
        table_headers = list(data[0].keys()) if data else []
    
    # Calculate column widths
    col_widths = {}
    for header in table_headers:
        col_widths[header] = max(
            len(str(header)),
            max(len(str(row.get(header, ""))) for row in data)
        )
    
    # Build table
    lines = []
    
    # Header row
    header_row = " | ".join(
        str(header).ljust(col_widths[header]) 
        for header in table_headers
    )
    lines.append(header_row)
    
    # Separator
    separator = "-+-".join("-" * col_widths[header] for header in table_headers)
    lines.append(separator)
    
    # Data rows
    for row in data:
        data_row = " | ".join(
            str(row.get(header, "")).ljust(col_widths[header])
            for header in table_headers
        )
        lines.append(data_row)
    
    return "\n".join(lines)


def format_progress_bar(current: int, total: int, 
                       width: int = 20, 
                       filled_char: str = "█",
                       empty_char: str = "░") -> str:
    """
    Create text-based progress bar.
    
    Args:
        current: Current progress value
        total: Total/maximum value
        width: Width of progress bar in characters
        filled_char: Character for filled portion
        empty_char: Character for empty portion
        
    Returns:
        Progress bar string
    """
    if total == 0:
        return empty_char * width
    
    progress = min(current / total, 1.0)
    filled_width = int(progress * width)
    empty_width = width - filled_width
    
    bar = filled_char * filled_width + empty_char * empty_width
    percentage = f"{progress * 100:.1f}%"
    
    return f"{bar} {percentage}"


def clean_filename(filename: str) -> str:
    """
    Clean filename by removing invalid characters.
    
    Args:
        filename: Original filename
        
    Returns:
        Cleaned filename safe for file systems
    """
    # Remove invalid characters for most file systems
    invalid_chars = r'<>:"/\\|?*'
    cleaned = filename
    
    for char in invalid_chars:
        cleaned = cleaned.replace(char, "_")
    
    # Remove multiple underscores and trim
    cleaned = re.sub(r'_+', '_', cleaned).strip('_')
    
    # Ensure filename is not empty and not too long
    if not cleaned:
        cleaned = "untitled"
    
    if len(cleaned) > 255:
        name, ext = cleaned.rsplit('.', 1) if '.' in cleaned else (cleaned, '')
        max_name_len = 255 - len(ext) - 1 if ext else 255
        cleaned = name[:max_name_len] + ('.' + ext if ext else '')
    
    return cleaned


def format_error_message(error: Exception, 
                        user_friendly: bool = True) -> str:
    """
    Format error message for display.
    
    Args:
        error: Exception object
        user_friendly: Whether to show user-friendly message
        
    Returns:
        Formatted error message
    """
    if user_friendly:
        # Map common errors to user-friendly messages
        error_type = type(error).__name__
        error_msg = str(error)
        
        if "timeout" in error_msg.lower():
            return "⏰ Operasi timeout. Silakan coba lagi."
        elif "network" in error_msg.lower() or "connection" in error_msg.lower():
            return "🌐 Masalah koneksi. Periksa internet Anda."
        elif "permission" in error_msg.lower() or "forbidden" in error_msg.lower():
            return "🔒 Akses ditolak. Hubungi administrator."
        elif "not found" in error_msg.lower():
            return "🔍 Data tidak ditemukan."
        else:
            return f"❌ Terjadi kesalahan: {error_type}"
    else:
        return f"{type(error).__name__}: {str(error)}"