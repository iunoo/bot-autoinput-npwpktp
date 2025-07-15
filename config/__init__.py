"""
Configuration package for the Telegram Bot.
Provides centralized configuration management with validation.
"""

from .settings import settings
from .constants import *

__all__ = [
    'settings',
    'FOLDER_MAP',
    'SHEET_NAME_MAP',
    'GOOGLE_SCOPES',
    'AI_MODELS',
    'DEFAULT_TIMEOUTS'
]