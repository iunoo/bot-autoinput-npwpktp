"""
Custom exceptions for the Telegram bot application.
Provides specific exception types for better error handling and debugging.
"""

from typing import Optional, Dict, Any


class BotException(Exception):
    """
    Base exception for all bot-related errors.
    All custom exceptions should inherit from this class.
    """
    
    def __init__(self, message: str, error_code: Optional[str] = None, details: Optional[Dict[str, Any]] = None):
        super().__init__(message)
        self.message = message
        self.error_code = error_code
        self.details = details or {}
    
    def __str__(self) -> str:
        if self.error_code:
            return f"[{self.error_code}] {self.message}"
        return self.message


class AIProcessingError(BotException):
    """
    Raised when AI processing fails.
    This includes API errors, invalid responses, or processing timeouts.
    """
    
    def __init__(self, message: str, ai_service: Optional[str] = None, model: Optional[str] = None):
        super().__init__(message, "AI_ERROR")
        self.ai_service = ai_service
        self.model = model
        self.details.update({
            "ai_service": ai_service,
            "model": model
        })


class GoogleServiceError(BotException):
    """
    Raised when Google service operations fail.
    This includes Drive API, Sheets API, or authentication errors.
    """
    
    def __init__(self, message: str, service: Optional[str] = None, operation: Optional[str] = None):
        super().__init__(message, "GOOGLE_ERROR")
        self.service = service  # 'drive', 'sheets', 'auth'
        self.operation = operation  # 'upload', 'append', 'read', etc.
        self.details.update({
            "service": service,
            "operation": operation
        })


class ValidationError(BotException):
    """
    Raised when data validation fails.
    Contains detailed validation errors for user feedback.
    """
    
    def __init__(self, message: str, field: Optional[str] = None, validation_errors: Optional[list] = None):
        super().__init__(message, "VALIDATION_ERROR")
        self.field = field
        self.validation_errors = validation_errors or []
        self.details.update({
            "field": field,
            "validation_errors": validation_errors
        })
    
    def get_user_friendly_message(self) -> str:
        """Get a user-friendly validation error message."""
        if self.validation_errors:
            errors = "\n".join(f"• {error}" for error in self.validation_errors)
            return f"Data tidak valid:\n{errors}"
        return self.message


class DuplicateDataError(BotException):
    """
    Raised when duplicate data is detected in the system.
    """
    
    def __init__(self, message: str, duplicate_field: Optional[str] = None, existing_value: Optional[str] = None):
        super().__init__(message, "DUPLICATE_ERROR")
        self.duplicate_field = duplicate_field
        self.existing_value = existing_value
        self.details.update({
            "duplicate_field": duplicate_field,
            "existing_value": existing_value
        })


class SessionExpiredError(BotException):
    """
    Raised when user session has expired.
    """
    
    def __init__(self, message: str = "Sesi sudah berakhir. Silakan mulai ulang dengan /start"):
        super().__init__(message, "SESSION_EXPIRED")


class InvalidFileError(BotException):
    """
    Raised when uploaded file is invalid or unsupported.
    """
    
    def __init__(self, message: str, file_type: Optional[str] = None, file_size: Optional[int] = None):
        super().__init__(message, "INVALID_FILE")
        self.file_type = file_type
        self.file_size = file_size
        self.details.update({
            "file_type": file_type,
            "file_size": file_size
        })


class ConfigurationError(BotException):
    """
    Raised when there's a configuration error.
    """
    
    def __init__(self, message: str, config_key: Optional[str] = None):
        super().__init__(message, "CONFIG_ERROR")
        self.config_key = config_key
        self.details.update({
            "config_key": config_key
        })


class RateLimitError(BotException):
    """
    Raised when rate limit is exceeded.
    """
    
    def __init__(self, message: str, service: Optional[str] = None, retry_after: Optional[int] = None):
        super().__init__(message, "RATE_LIMIT")
        self.service = service
        self.retry_after = retry_after
        self.details.update({
            "service": service,
            "retry_after": retry_after
        })


class AuthenticationError(BotException):
    """
    Raised when authentication fails.
    """
    
    def __init__(self, message: str, auth_type: Optional[str] = None):
        super().__init__(message, "AUTH_ERROR")
        self.auth_type = auth_type  # 'google', 'telegram', 'ai_service'
        self.details.update({
            "auth_type": auth_type
        })


# Utility functions for exception handling

def handle_api_error(func):
    """
    Decorator to handle common API errors and convert them to custom exceptions.
    """
    def wrapper(*args, **kwargs):
        try:
            return func(*args, **kwargs)
        except Exception as e:
            # Convert common errors to custom exceptions
            error_msg = str(e).lower()
            
            if "rate limit" in error_msg or "quota" in error_msg:
                raise RateLimitError(f"Rate limit exceeded: {str(e)}")
            elif "authentication" in error_msg or "unauthorized" in error_msg:
                raise AuthenticationError(f"Authentication failed: {str(e)}")
            elif "timeout" in error_msg:
                raise BotException(f"Operation timed out: {str(e)}", "TIMEOUT_ERROR")
            else:
                # Re-raise as generic bot exception
                raise BotException(f"Unexpected error: {str(e)}", "UNKNOWN_ERROR")
    
    return wrapper


def get_user_error_message(exception: Exception) -> str:
    """
    Convert any exception to a user-friendly error message.
    """
    if isinstance(exception, ValidationError):
        return exception.get_user_friendly_message()
    elif isinstance(exception, DuplicateDataError):
        return "⚠️ Data sudah ada di database. Tetap simpan?"
    elif isinstance(exception, SessionExpiredError):
        return "⏰ Sesi sudah berakhir. Silakan mulai ulang dengan /start"
    elif isinstance(exception, InvalidFileError):
        return f"❌ File tidak valid: {exception.message}"
    elif isinstance(exception, AIProcessingError):
        return "❌ AI tidak dapat memproses gambar. Pastikan gambar jelas dan berisi KTP/NPWP."
    elif isinstance(exception, GoogleServiceError):
        return "❌ Terjadi masalah dengan layanan Google. Coba lagi nanti."
    elif isinstance(exception, RateLimitError):
        return "⏳ Terlalu banyak permintaan. Silakan tunggu sebentar."
    elif isinstance(exception, BotException):
        return f"❌ {exception.message}"
    else:
        return "❌ Terjadi kesalahan tidak terduga. Silakan coba lagi."