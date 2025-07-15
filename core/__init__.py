"""
Core package containing foundational components for the Telegram bot.
Includes exceptions, validators, and core business logic.
"""

from .exceptions import *
from .validators import DocumentValidator
from .bot import TelegramBot

__all__ = [
    # Exceptions
    'BotException',
    'AIProcessingError', 
    'GoogleServiceError',
    'ValidationError',
    'DuplicateDataError',
    'SessionExpiredError',
    'InvalidFileError',
    
    # Validators
    'DocumentValidator',
    
    # Core classes
    'TelegramBot'
]