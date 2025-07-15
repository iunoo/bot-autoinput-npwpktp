"""
Application settings management with validation.
Loads configuration from environment variables with proper defaults.
"""

import os
from pathlib import Path
from typing import Optional, List
from dotenv import load_dotenv

from .constants import (
    FOLDER_MAP, 
    SHEET_NAME_MAP, 
    GOOGLE_SCOPES, 
    AI_MODELS,
    DEFAULT_TIMEOUTS
)

# Load environment variables
load_dotenv()

class Settings:
    """Centralized configuration management with validation."""
    
    def __init__(self):
        self._validate_on_init = True
        self._setup_paths()
        self._load_basic_config()
        self._load_telegram_config()
        self._load_google_config()
        self._load_ai_config()
        self._load_app_config()
        
        if self._validate_on_init:
            self.validate()
    
    def _setup_paths(self):
        """Setup base paths."""
        self.BASE_DIR = Path(__file__).parent.parent
        self.CREDENTIALS_DIR = self.BASE_DIR / "credentials"
        self.LOGS_DIR = self.BASE_DIR / "logs"
        
        # Create directories if they don't exist
        self.CREDENTIALS_DIR.mkdir(exist_ok=True)
        self.LOGS_DIR.mkdir(exist_ok=True)
    
    def _load_basic_config(self):
        """Load basic application configuration."""
        self.DEBUG = os.getenv("DEBUG", "false").lower() == "true"
        self.ENVIRONMENT = os.getenv("ENVIRONMENT", "development")
        self.LOG_LEVEL = os.getenv("LOG_LEVEL", "INFO").upper()
    
    def _load_telegram_config(self):
        """Load Telegram bot configuration."""
        self.TELEGRAM_BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")
        self.TELEGRAM_WEBHOOK_URL = os.getenv("TELEGRAM_WEBHOOK_URL")
        self.TELEGRAM_WEBHOOK_PORT = int(os.getenv("TELEGRAM_WEBHOOK_PORT", "8443"))
    
    def _load_google_config(self):
        """Load Google services configuration."""
        self.GOOGLE_SHEET_ID = os.getenv("GOOGLE_SHEET_ID")
        
        # Credential files
        self.GOOGLE_CREDENTIALS_FILE = self.CREDENTIALS_DIR / "credentials.json"
        self.GOOGLE_TOKEN_FILE = self.CREDENTIALS_DIR / "token.json"
        
        # Alternative: service account
        self.GOOGLE_SERVICE_ACCOUNT_FILE = self.CREDENTIALS_DIR / "service_account.json"
        
        # Use service account if available, otherwise OAuth2
        self.USE_SERVICE_ACCOUNT = self.GOOGLE_SERVICE_ACCOUNT_FILE.exists()
        
        # Google API settings
        self.GOOGLE_SCOPES = GOOGLE_SCOPES
        self.GOOGLE_API_TIMEOUT = DEFAULT_TIMEOUTS["google_api"]
    
    def _load_ai_config(self):
        """Load AI service configuration."""
        self.ACTIVE_AI_SERVICE = os.getenv("ACTIVE_AI_SERVICE", "openai").lower()
        
        # OpenAI config
        self.OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
        self.OPENAI_MODEL = os.getenv("OPENAI_MODEL", AI_MODELS["openai"]["default"])
        self.OPENAI_TIMEOUT = int(os.getenv("OPENAI_TIMEOUT", str(DEFAULT_TIMEOUTS["ai_processing"])))
        
        # DeepSeek config  
        self.DEEPSEEK_API_KEY = os.getenv("DEEPSEEK_API_KEY")
        self.DEEPSEEK_MODEL = os.getenv("DEEPSEEK_MODEL", AI_MODELS["deepseek"]["default"])
        self.DEEPSEEK_TIMEOUT = int(os.getenv("DEEPSEEK_TIMEOUT", str(DEFAULT_TIMEOUTS["ai_processing"])))
    
    def _load_app_config(self):
        """Load application-specific configuration."""
        # File handling
        self.MAX_IMAGE_SIZE_MB = int(os.getenv("MAX_IMAGE_SIZE_MB", "20"))
        self.MAX_PDF_SIZE_MB = int(os.getenv("MAX_PDF_SIZE_MB", "50"))
        
        # Session management
        self.SESSION_TIMEOUT_MINUTES = int(os.getenv("SESSION_TIMEOUT_MINUTES", "30"))
        self.MAX_CONCURRENT_SESSIONS = int(os.getenv("MAX_CONCURRENT_SESSIONS", "100"))
        
        # Feature flags
        self.ENABLE_DUPLICATE_CHECK = os.getenv("ENABLE_DUPLICATE_CHECK", "true").lower() == "true"
        self.ENABLE_DATA_VALIDATION = os.getenv("ENABLE_DATA_VALIDATION", "true").lower() == "true"
        self.ENABLE_AUDIT_LOG = os.getenv("ENABLE_AUDIT_LOG", "true").lower() == "true"
        
        # Performance settings
        self.CONCURRENT_AI_REQUESTS = int(os.getenv("CONCURRENT_AI_REQUESTS", "5"))
        self.GOOGLE_API_RETRY_COUNT = int(os.getenv("GOOGLE_API_RETRY_COUNT", "3"))
        
        # Folder and sheet mappings
        self.FOLDER_MAP = FOLDER_MAP
        self.SHEET_NAME_MAP = SHEET_NAME_MAP
    
    def validate(self) -> None:
        """Validate all configuration settings."""
        errors = []
        
        # Required settings
        if not self.TELEGRAM_BOT_TOKEN:
            errors.append("TELEGRAM_BOT_TOKEN is required")
        
        if not self.GOOGLE_SHEET_ID:
            errors.append("GOOGLE_SHEET_ID is required")
        
        # AI service validation
        if self.ACTIVE_AI_SERVICE not in ["openai", "deepseek"]:
            errors.append(f"ACTIVE_AI_SERVICE must be 'openai' or 'deepseek', got '{self.ACTIVE_AI_SERVICE}'")
        
        if self.ACTIVE_AI_SERVICE == "openai" and not self.OPENAI_API_KEY:
            errors.append("OPENAI_API_KEY is required when using OpenAI")
        
        if self.ACTIVE_AI_SERVICE == "deepseek" and not self.DEEPSEEK_API_KEY:
            errors.append("DEEPSEEK_API_KEY is required when using DeepSeek")
        
        # Google credentials validation
        if not self.USE_SERVICE_ACCOUNT:
            if not self.GOOGLE_CREDENTIALS_FILE.exists():
                errors.append(f"Google credentials file not found: {self.GOOGLE_CREDENTIALS_FILE}")
        
        # Folder mappings validation
        if not self.FOLDER_MAP:
            errors.append("FOLDER_MAP cannot be empty")
        
        if not self.SHEET_NAME_MAP:
            errors.append("SHEET_NAME_MAP cannot be empty")
        
        # Check if all branches have both folder and sheet mappings
        folder_branches = set(self.FOLDER_MAP.keys())
        sheet_branches = set(self.SHEET_NAME_MAP.keys())
        
        missing_folders = sheet_branches - folder_branches
        missing_sheets = folder_branches - sheet_branches
        
        if missing_folders:
            errors.append(f"Missing folder mappings for branches: {missing_folders}")
        
        if missing_sheets:
            errors.append(f"Missing sheet mappings for branches: {missing_sheets}")
        
        # Value range validation
        if self.MAX_IMAGE_SIZE_MB <= 0 or self.MAX_IMAGE_SIZE_MB > 100:
            errors.append("MAX_IMAGE_SIZE_MB must be between 1 and 100")
        
        if self.SESSION_TIMEOUT_MINUTES <= 0:
            errors.append("SESSION_TIMEOUT_MINUTES must be positive")
        
        if errors:
            raise ValueError("Configuration validation failed:\n" + "\n".join(f"- {error}" for error in errors))
    
    def get_ai_config(self) -> dict:
        """Get configuration for the active AI service."""
        if self.ACTIVE_AI_SERVICE == "openai":
            return {
                "api_key": self.OPENAI_API_KEY,
                "model": self.OPENAI_MODEL,
                "timeout": self.OPENAI_TIMEOUT
            }
        elif self.ACTIVE_AI_SERVICE == "deepseek":
            return {
                "api_key": self.DEEPSEEK_API_KEY,
                "model": self.DEEPSEEK_MODEL,
                "timeout": self.DEEPSEEK_TIMEOUT
            }
        else:
            raise ValueError(f"Unknown AI service: {self.ACTIVE_AI_SERVICE}")
    
    def get_google_credentials_path(self) -> Path:
        """Get the appropriate Google credentials file path."""
        if self.USE_SERVICE_ACCOUNT:
            return self.GOOGLE_SERVICE_ACCOUNT_FILE
        return self.GOOGLE_CREDENTIALS_FILE
    
    def is_valid_branch(self, branch: str) -> bool:
        """Check if branch code is valid."""
        return branch in self.FOLDER_MAP and branch in self.SHEET_NAME_MAP
    
    def get_branch_list(self) -> List[str]:
        """Get list of available branch codes."""
        return list(self.FOLDER_MAP.keys())
    
    def __repr__(self) -> str:
        """String representation for debugging."""
        return f"Settings(environment={self.ENVIRONMENT}, ai_service={self.ACTIVE_AI_SERVICE})"


# Create global settings instance
settings = Settings()