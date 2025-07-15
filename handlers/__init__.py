"""
Handlers package for Telegram bot.
Contains all message, command, and callback handlers with improved structure.
"""

# Import individual handler classes
try:
    from .commands import CommandHandlers
except ImportError as e:
    print(f"Warning: Could not import CommandHandlers: {e}")
    CommandHandlers = None

try:
    from .messages import MessageHandlers
except ImportError as e:
    print(f"Warning: Could not import MessageHandlers: {e}")
    MessageHandlers = None

try:
    from .callbacks import CallbackHandlers
except ImportError as e:
    print(f"Warning: Could not import CallbackHandlers: {e}")
    # Try alternative names
    try:
        from .callbacks import CallbackQueryHandlers as CallbackHandlers
    except ImportError:
        CallbackHandlers = None

try:
    from .base import BaseHandler
except ImportError as e:
    print(f"Warning: Could not import BaseHandler: {e}")
    BaseHandler = None

__all__ = [
    'BaseHandler',
    'CommandHandlers',
    'MessageHandlers', 
    'CallbackHandlers'
]