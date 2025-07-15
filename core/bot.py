"""
Main Telegram bot class with improved architecture.
Handles bot initialization, middleware setup, and graceful shutdown.
"""

import logging
import signal
import asyncio
from typing import Optional
from telegram.ext import (
    Application, 
    CommandHandler, 
    MessageHandler, 
    CallbackQueryHandler,
    filters
)
from telegram.error import NetworkError, TelegramError

from config.settings import settings
from .exceptions import BotException, ConfigurationError, get_user_error_message


class TelegramBot:
    """
    Main Telegram bot class with improved error handling and lifecycle management.
    """
    
    def __init__(self):
        self.logger = logging.getLogger(__name__)
        self.application: Optional[Application] = None
        self._is_running = False
        self._shutdown_requested = False
        
        # Validate configuration before proceeding
        try:
            settings.validate()
        except Exception as e:
            raise ConfigurationError(f"Bot configuration is invalid: {e}")
    
    async def start(self) -> None:
        """
        Start the Telegram bot with proper error handling.
        """
        try:
            self.logger.info("Initializing Telegram bot...")
            await self._initialize_bot()
            
            self.logger.info("Registering handlers...")
            self._register_handlers()
            
            self.logger.info("Setting up shutdown handlers...")
            self._setup_shutdown_handlers()
            
            self.logger.info("Starting bot polling...")
            await self._start_polling()
            
        except Exception as e:
            self.logger.error(f"Failed to start bot: {e}", exc_info=True)
            await self.stop()
            raise
    
    async def stop(self) -> None:
        """
        Gracefully stop the bot.
        """
        if self._shutdown_requested:
            return
            
        self._shutdown_requested = True
        self.logger.info("Shutting down bot...")
        
        if self.application and self._is_running:
            try:
                await self.application.stop()
                await self.application.shutdown()
                self.logger.info("Bot stopped gracefully")
            except Exception as e:
                self.logger.error(f"Error during shutdown: {e}")
        
        self._is_running = False
    
    async def _initialize_bot(self) -> None:
        """
        Initialize the Telegram bot application.
        """
        try:
            # Create application with improved settings
            self.application = (
                Application.builder()
                .token(settings.TELEGRAM_BOT_TOKEN)
                .read_timeout(30)
                .write_timeout(30)
                .connect_timeout(30)
                .pool_timeout(30)
                .concurrent_updates(256)  # Handle multiple updates concurrently
                .build()
            )
            
            # Add error handler
            self.application.add_error_handler(self._error_handler)
            
            self.logger.info("Bot application initialized successfully")
            
        except Exception as e:
            raise BotException(f"Failed to initialize bot application: {e}")
    
    def _register_handlers(self) -> None:
        """
        Register all message and callback handlers.
        """
        try:
            # Import handlers locally to avoid circular imports
            from handlers.commands import CommandHandlers
            from handlers.messages import MessageHandlers
            from handlers.callbacks import CallbackHandlers
            
            # Initialize handlers
            command_handlers = CommandHandlers()
            message_handlers = MessageHandlers()
            callback_handlers = CallbackHandlers()
            
            # Register command handlers
            self.application.add_handler(
                CommandHandler("start", command_handlers.start_command)
            )
            self.application.add_handler(
                CommandHandler("help", command_handlers.help_command)
            )
            self.application.add_handler(
                CommandHandler("status", command_handlers.status_command)
            )
            self.application.add_handler(
                CommandHandler("cancel", command_handlers.cancel_command)
            )
            
            # Register message handlers (order matters!)
            # Photo messages
            self.application.add_handler(
                MessageHandler(
                    filters.PHOTO, 
                    message_handlers.handle_photo_message
                )
            )
            
            # PDF documents
            self.application.add_handler(
                MessageHandler(
                    filters.Document.PDF, 
                    message_handlers.handle_pdf_message
                )
            )
            
            # Text messages (should be last to catch all remaining text)
            self.application.add_handler(
                MessageHandler(
                    filters.TEXT & ~filters.COMMAND, 
                    message_handlers.handle_text_message
                )
            )
            
            # Callback query handler
            self.application.add_handler(
                CallbackQueryHandler(callback_handlers.handle_callback_query)
            )
            
            self.logger.info("All handlers registered successfully")
            
        except Exception as e:
            raise BotException(f"Failed to register handlers: {e}")
    
    async def _start_polling(self) -> None:
        """
        Start bot polling with error recovery.
        """
        max_retries = 5
        retry_delay = 5
        
        for attempt in range(max_retries):
            try:
                self.logger.info(f"Starting polling (attempt {attempt + 1}/{max_retries})...")
                self._is_running = True
                
                # Start polling
                await self.application.initialize()
                await self.application.start()
                await self.application.updater.start_polling(
                    allowed_updates=['message', 'callback_query'],
                    drop_pending_updates=True
                )
                
                self.logger.info("Bot is now running and polling for updates...")
                
                # Keep the bot running until shutdown is requested
                while not self._shutdown_requested:
                    await asyncio.sleep(1)
                
                break  # Exit retry loop if successful
                
            except NetworkError as e:
                self.logger.warning(f"Network error on attempt {attempt + 1}: {e}")
                if attempt < max_retries - 1:
                    self.logger.info(f"Retrying in {retry_delay} seconds...")
                    await asyncio.sleep(retry_delay)
                    retry_delay *= 2  # Exponential backoff
                else:
                    raise BotException(f"Failed to start polling after {max_retries} attempts: {e}")
                    
            except TelegramError as e:
                self.logger.error(f"Telegram API error: {e}")
                raise BotException(f"Telegram API error: {e}")
                
            except Exception as e:
                self.logger.error(f"Unexpected error during polling: {e}", exc_info=True)
                raise BotException(f"Unexpected error during polling: {e}")
    
    def _setup_shutdown_handlers(self) -> None:
        """
        Setup signal handlers for graceful shutdown.
        """
        def signal_handler(signum, frame):
            self.logger.info(f"Received signal {signum}, initiating shutdown...")
            asyncio.create_task(self.stop())
        
        # Register signal handlers
        signal.signal(signal.SIGINT, signal_handler)
        signal.signal(signal.SIGTERM, signal_handler)
    
    async def _error_handler(self, update, context) -> None:
        """
        Global error handler for the bot.
        """
        try:
            # Log the error with context
            error = context.error
            self.logger.error(f"Bot error: {error}", exc_info=True)
            
            # Add update context to logs
            if update:
                if update.message:
                    self.logger.error(f"Update info - Message: {update.message.text}, User: {update.message.from_user.id}")
                elif update.callback_query:
                    self.logger.error(f"Update info - Callback: {update.callback_query.data}, User: {update.callback_query.from_user.id}")
            
            # Try to send user-friendly error message
            user_message = get_user_error_message(error)
            
            try:
                if update and update.effective_chat:
                    if update.callback_query:
                        await update.callback_query.edit_message_text(
                            text=user_message,
                            parse_mode=None
                        )
                    elif update.message:
                        await update.message.reply_text(
                            text=user_message,
                            parse_mode=None
                        )
            except Exception as send_error:
                self.logger.error(f"Failed to send error message to user: {send_error}")
                
            # Clear user session on critical errors
            if isinstance(error, (BotException,)) and hasattr(context, 'user_data'):
                context.user_data.clear()
                self.logger.info("User session cleared due to error")
                
        except Exception as handler_error:
            self.logger.error(f"Error in error handler: {handler_error}", exc_info=True)
    
    def get_bot_info(self) -> dict:
        """
        Get current bot status and information.
        """
        return {
            "is_running": self._is_running,
            "shutdown_requested": self._shutdown_requested,
            "bot_username": self.application.bot.username if self.application else None,
            "handlers_count": len(self.application.handlers) if self.application else 0,
        }
    
    async def send_admin_notification(self, message: str) -> None:
        """
        Send notification to admin users (if configured).
        """
        admin_chat_ids = getattr(settings, 'ADMIN_CHAT_IDS', [])
        
        if not admin_chat_ids:
            self.logger.debug("No admin chat IDs configured")
            return
        
        for chat_id in admin_chat_ids:
            try:
                await self.application.bot.send_message(
                    chat_id=chat_id,
                    text=f"🤖 Bot Notification:\n{message}",
                    parse_mode=None
                )
            except Exception as e:
                self.logger.error(f"Failed to send admin notification to {chat_id}: {e}")
    
    async def health_check(self) -> bool:
        """
        Perform health check on the bot.
        """
        try:
            if not self.application or not self._is_running:
                return False
            
            # Try to get bot info to test connection
            await self.application.bot.get_me()
            return True
            
        except Exception as e:
            self.logger.error(f"Health check failed: {e}")
            return False