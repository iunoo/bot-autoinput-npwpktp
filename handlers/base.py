"""
Base handler class for all Telegram handlers.
Provides common functionality, error handling, and session management.
"""

import logging
from abc import ABC
from typing import Optional, Dict, Any
from datetime import datetime, timedelta
from telegram import Update
from telegram.ext import ContextTypes

from core.exceptions import (
    BotException, 
    SessionExpiredError, 
    get_user_error_message
)
from config.settings import settings


class BaseHandler(ABC):
    """
    Base class for all Telegram handlers.
    Provides common functionality and error handling.
    """
    
    def __init__(self):
        self.logger = logging.getLogger(self.__class__.__name__)
    
    async def handle_error(self, update: Update, context: ContextTypes.DEFAULT_TYPE, error: Exception) -> None:
        """
        Handle errors in a consistent way across all handlers.
        """
        # Log the error with context
        self.logger.error(f"Error in {self.__class__.__name__}: {error}", exc_info=True)
        
        # Add user context to logs
        user_id = self._get_user_id(update)
        if user_id:
            self.logger.error(f"User ID: {user_id}")
        
        # Get user-friendly error message
        error_message = get_user_error_message(error)
        
        try:
            # Send error message to user
            if update.callback_query:
                await update.callback_query.edit_message_text(
                    text=error_message,
                    parse_mode=None
                )
            elif update.message:
                await update.message.reply_text(
                    text=error_message,
                    parse_mode=None
                )
                
            # Clear session on critical errors
            if isinstance(error, (SessionExpiredError, BotException)):
                self._clear_user_session(context)
                
        except Exception as send_error:
            self.logger.error(f"Failed to send error message: {send_error}")
    
    def _get_user_id(self, update: Update) -> Optional[int]:
        """Get user ID from update."""
        if update.effective_user:
            return update.effective_user.id
        return None
    
    def _get_user_session(self, context: ContextTypes.DEFAULT_TYPE) -> Dict[str, Any]:
        """Get user session data with expiration check."""
        user_data = context.user_data
        
        # Check session expiration
        if self._is_session_expired(user_data):
            self._clear_user_session(context)
            raise SessionExpiredError()
        
        return user_data
    
    def _update_session_timestamp(self, context: ContextTypes.DEFAULT_TYPE) -> None:
        """Update session timestamp to current time."""
        context.user_data['last_activity'] = datetime.now()
    
    def _is_session_expired(self, user_data: Dict[str, Any]) -> bool:
        """Check if user session has expired."""
        if not user_data:
            return False
        
        last_activity = user_data.get('last_activity')
        if not last_activity:
            return False
        
        timeout = timedelta(minutes=settings.SESSION_TIMEOUT_MINUTES)
        return datetime.now() - last_activity > timeout
    
    def _clear_user_session(self, context: ContextTypes.DEFAULT_TYPE) -> None:
        """Clear user session data."""
        context.user_data.clear()
        self.logger.info("User session cleared")
    
    def _init_user_session(self, context: ContextTypes.DEFAULT_TYPE, workflow_type: str) -> None:
        """Initialize user session with basic data."""
        self._clear_user_session(context)
        context.user_data.update({
            'workflow_type': workflow_type,
            'state': 'initialized',
            'created_at': datetime.now(),
            'last_activity': datetime.now()
        })
    
    def _get_session_state(self, context: ContextTypes.DEFAULT_TYPE) -> Optional[str]:
        """Get current session state."""
        user_data = self._get_user_session(context)
        return user_data.get('state')
    
    def _set_session_state(self, context: ContextTypes.DEFAULT_TYPE, state: str) -> None:
        """Set session state and update timestamp."""
        user_data = self._get_user_session(context)
        user_data['state'] = state
        self._update_session_timestamp(context)
    
    def _get_session_data(self, context: ContextTypes.DEFAULT_TYPE, key: str, default: Any = None) -> Any:
        """Get data from user session."""
        user_data = self._get_user_session(context)
        return user_data.get(key, default)
    
    def _set_session_data(self, context: ContextTypes.DEFAULT_TYPE, key: str, value: Any) -> None:
        """Set data in user session."""
        user_data = self._get_user_session(context)
        user_data[key] = value
        self._update_session_timestamp(context)
    
    async def _send_typing_action(self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
        """Send typing action to indicate bot is processing."""
        try:
            await context.bot.send_chat_action(
                chat_id=update.effective_chat.id,
                action="typing"
            )
        except Exception as e:
            self.logger.debug(f"Failed to send typing action: {e}")
    
    async def _delete_message_safely(self, context: ContextTypes.DEFAULT_TYPE, 
                                   chat_id: int, message_id: int) -> bool:
        """Safely delete a message without raising exceptions."""
        try:
            await context.bot.delete_message(
                chat_id=chat_id, 
                message_id=message_id
            )
            return True
        except Exception as e:
            self.logger.debug(f"Failed to delete message {message_id}: {e}")
            return False
    
    def _log_user_action(self, update: Update, action: str, details: Optional[Dict] = None) -> None:
        """Log user actions for audit trail."""
        if not settings.ENABLE_AUDIT_LOG:
            return
        
        user_id = self._get_user_id(update)
        log_data = {
            'user_id': user_id,
            'action': action,
            'timestamp': datetime.now().isoformat(),
            'details': details or {}
        }
        
        # Add username if available
        if update.effective_user and update.effective_user.username:
            log_data['username'] = update.effective_user.username
        
        self.logger.info(f"User action: {log_data}")
    
    def _validate_file_size(self, file_size: Optional[int], max_size_mb: int) -> bool:
        """Validate file size against maximum allowed."""
        if file_size is None:
            return True
        
        max_size_bytes = max_size_mb * 1024 * 1024
        return file_size <= max_size_bytes
    
    def _format_file_size(self, size_bytes: int) -> str:
        """Format file size for display."""
        if size_bytes < 1024:
            return f"{size_bytes} B"
        elif size_bytes < 1024 * 1024:
            return f"{size_bytes / 1024:.1f} KB"
        else:
            return f"{size_bytes / 1024 / 1024:.1f} MB"
    
    def _is_admin_user(self, user_id: int) -> bool:
        """Check if user is an admin."""
        admin_ids = getattr(settings, 'ADMIN_USER_IDS', [])
        return user_id in admin_ids
    
    async def _require_admin(self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> bool:
        """Check if user is admin, send error if not."""
        user_id = self._get_user_id(update)
        
        if not user_id or not self._is_admin_user(user_id):
            await update.message.reply_text(
                "❌ Anda tidak memiliki akses untuk perintah ini."
            )
            return False
        
        return True
    
    def _get_user_display_name(self, update: Update) -> str:
        """Get user display name for logs and messages."""
        user = update.effective_user
        if not user:
            return "Unknown"
        
        if user.username:
            return f"@{user.username}"
        elif user.full_name:
            return user.full_name
        else:
            return f"User {user.id}"