"""
Constants and mappings used throughout the application.
Separated from settings for better organization.
"""

from typing import Dict, List

# Google Drive folder mappings
FOLDER_MAP: Dict[str, str] = {
    "BJ": "1B8-vxVXYjcG5m7aqnqFHjuShphvfjMo4",
    "BJM": "15rLbNaQ-_DvExm86HBlevGqcTLJYkT0v", 
    "SBY": "15pjmJNcr2bdxDKBwm6DZmGm4FebQfZ0W",
    "SMD-BPN": "1-DJINheeXhZT-ugOCAI0v8VnQOT4Zqo3",
    "SMG": "1-BbhmDkHanpCBgLyl46NeBXa-B_ByYBh",
}

# Google Sheets name mappings
SHEET_NAME_MAP: Dict[str, str] = {
    "BJ": "NPWPKTP BJ (NEW)",
    "SMG": "NPWPKTP BBN SMG (NEW)",
    "SBY": "NPWPKTP BBN SBY-BJM (NEW)",
    "BJM": "NPWPKTP BBN SBY-BJM (NEW)",
    "SMD-BPN": "NPWPKTP BBN SMD-BPP (NEW)",
}

# Google API scopes
GOOGLE_SCOPES: List[str] = [
    "https://www.googleapis.com/auth/drive",
    "https://www.googleapis.com/auth/spreadsheets"
]

# AI model configurations
AI_MODELS: Dict[str, Dict[str, str]] = {
    "openai": {
        "default": "gpt-4o-mini",
        "vision": "gpt-4o-mini",
        "fast": "gpt-3.5-turbo"
    },
    "deepseek": {
        "default": "deepseek-vision",
        "vision": "deepseek-vision"
    }
}

# Default timeout configurations (in seconds)
DEFAULT_TIMEOUTS: Dict[str, int] = {
    "ai_processing": 60,
    "google_api": 30,
    "file_upload": 120,
    "user_session": 1800  # 30 minutes
}

# File size limits (in MB)
FILE_SIZE_LIMITS: Dict[str, int] = {
    "image": 20,
    "pdf": 50
}

# Supported file types
SUPPORTED_IMAGE_TYPES: List[str] = [
    "image/jpeg", 
    "image/png", 
    "image/jpg"
]

SUPPORTED_DOCUMENT_TYPES: List[str] = [
    "application/pdf"
]

# Validation patterns
VALIDATION_PATTERNS: Dict[str, str] = {
    "nik": r"^\d{16}$",
    "npwp_15": r"^\d{15}$", 
    "npwp_16": r"^\d{16}$"
}

# Error messages
ERROR_MESSAGES: Dict[str, str] = {
    "invalid_file_type": "❌ Tipe file tidak didukung. Gunakan gambar (JPG/PNG) atau PDF.",
    "file_too_large": "❌ File terlalu besar. Maksimal {limit}MB.",
    "ai_processing_failed": "❌ AI tidak dapat memproses gambar. Pastikan gambar jelas dan berisi KTP/NPWP.",
    "google_service_error": "❌ Terjadi masalah dengan layanan Google. Coba lagi nanti.",
    "duplicate_data": "⚠️ Data sudah ada di database. Tetap simpan?",
    "invalid_branch": "❌ Cabang tidak valid. Pilih dari daftar yang tersedia.",
    "session_expired": "⏰ Sesi sudah berakhir. Silakan mulai ulang dengan /start"
}