"""
Main entry point for the Telegram KTP/NPWP Bot.
Updated with proper error handling for testing.
"""

import asyncio
import logging
import sys
from pathlib import Path

# Add project root to Python path
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

def setup_logging():
    """Setup basic logging for testing."""
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        handlers=[
            logging.StreamHandler(sys.stdout),
            logging.FileHandler('bot.log')
        ]
    )

async def main():
    """Main function with comprehensive error handling."""
    print("🤖 Starting Telegram KTP/NPWP Bot...")
    
    try:
        # Setup logging first
        setup_logging()
        logger = logging.getLogger(__name__)
        
        print("📁 Testing imports...")
        
        # Test imports one by one for better error tracking
        try:
            from config.settings import settings
            print("✅ Config imported")
        except Exception as e:
            print(f"❌ Config import error: {e}")
            return
        
        try:
            from core.bot import TelegramBot
            print("✅ Core bot imported")
        except Exception as e:
            print(f"❌ Core bot import error: {e}")
            return
        
        try:
            # Validate configuration
            print("⚙️ Validating configuration...")
            settings.validate()
            print("✅ Configuration valid")
        except Exception as e:
            print(f"❌ Configuration error: {e}")
            print("\n💡 Tips:")
            print("- Check your .env file")
            print("- Make sure TELEGRAM_BOT_TOKEN is set")
            print("- Make sure GOOGLE_SHEET_ID is set")
            print("- Check API keys")
            return
        
        try:
            # Initialize bot
            print("🚀 Initializing bot...")
            bot = TelegramBot()
            
            # Start bot
            print("▶️ Starting bot...")
            await bot.start()
            
        except KeyboardInterrupt:
            print("\n⏹️ Bot stopped by user")
        except Exception as e:
            logger.error(f"Bot error: {e}", exc_info=True)
            print(f"❌ Bot error: {e}")
            
            # Print detailed error info for debugging
            import traceback
            print("\n🔍 Detailed error traceback:")
            traceback.print_exc()
        
        finally:
            print("🧹 Cleaning up...")
            try:
                if 'bot' in locals():
                    await bot.stop()
            except Exception as e:
                print(f"Cleanup error: {e}")
    
    except Exception as e:
        print(f"❌ Fatal error: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("\n👋 Goodbye!")
    except Exception as e:
        print(f"❌ Failed to start: {e}")
        import traceback
        traceback.print_exc()