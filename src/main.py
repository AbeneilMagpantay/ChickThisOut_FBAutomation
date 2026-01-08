"""
ChickThisOut Facebook Automation Bot
Main entry point for the automation system.
"""
import sys
import logging
import time
from datetime import datetime

import colorlog
from apscheduler.schedulers.blocking import BlockingScheduler
import pytz

# Add project root to path
sys.path.insert(0, str(__file__).rsplit("\\", 2)[0].rsplit("/", 2)[0])

from config.settings import (
    CHECK_INTERVAL_SECONDS,
    TIMEZONE,
    LOG_LEVEL,
    validate_config,
    RESTAURANT_INFO,
)
from src.facebook_api import facebook_api
from src.ai_responder import ai_responder
from src.comment_handler import comment_handler
from src.message_handler import message_handler
from src.database import db_manager


def setup_logging():
    """Configure colorful logging."""
    handler = colorlog.StreamHandler()
    handler.setFormatter(colorlog.ColoredFormatter(
        "%(log_color)s%(asctime)s [%(levelname)s] %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S",
        log_colors={
            "DEBUG": "cyan",
            "INFO": "green",
            "WARNING": "yellow",
            "ERROR": "red",
            "CRITICAL": "red,bg_white",
        }
    ))
    
    root_logger = logging.getLogger()
    root_logger.addHandler(handler)
    root_logger.setLevel(getattr(logging, LOG_LEVEL.upper(), logging.INFO))
    
    # Reduce noise from other libraries
    logging.getLogger("urllib3").setLevel(logging.WARNING)
    logging.getLogger("requests").setLevel(logging.WARNING)
    logging.getLogger("apscheduler").setLevel(logging.WARNING)


def run_check_cycle():
    """Run a single check cycle for comments and messages."""
    tz = pytz.timezone(TIMEZONE)
    current_time = datetime.now(tz)
    
    logging.info(f"🔄 Starting check cycle at {current_time.strftime('%Y-%m-%d %H:%M:%S %Z')}")
    
    # Process comments
    try:
        comment_stats = comment_handler.process_all_comments()
        if comment_stats["replies_sent"] > 0:
            logging.info(f"💬 Replied to {comment_stats['replies_sent']} comment(s)")
    except Exception as e:
        logging.error(f"Error processing comments: {e}")
    
    # Process messages
    try:
        message_stats = message_handler.process_all_messages()
        if message_stats["replies_sent"] > 0:
            logging.info(f"📨 Replied to {message_stats['replies_sent']} message(s)")
    except Exception as e:
        logging.error(f"Error processing messages: {e}")
    
    logging.info("✅ Check cycle complete")


def print_banner():
    """Print startup banner."""
    banner = """
    ╔═══════════════════════════════════════════════════════════╗
    ║                                                           ║
    ║   🍗 ChickThisOut Facebook Automation Bot 🍗              ║
    ║                                                           ║
    ║   Automatically responding to comments and messages       ║
    ║   using AI-powered responses                              ║
    ║                                                           ║
    ╚═══════════════════════════════════════════════════════════╝
    """
    print(banner)


def print_config():
    """Print current configuration."""
    logging.info(f"Restaurant: {RESTAURANT_INFO['name']}")
    logging.info(f"Check interval: {CHECK_INTERVAL_SECONDS} seconds")
    logging.info(f"Timezone: {TIMEZONE}")


def verify_connections():
    """Verify all connections are working."""
    logging.info("Verifying connections...")
    
    # Verify Facebook token
    if not facebook_api.verify_token():
        logging.error("❌ Facebook token verification failed!")
        logging.error("Please check your FACEBOOK_PAGE_ACCESS_TOKEN in .env")
        return False
    logging.info("✓ Facebook API connected")
    
    # Verify AI
    if not ai_responder.test_connection():
        logging.error("❌ AI connection failed!")
        logging.error("Please check your GEMINI_API_KEY in .env")
        return False
    logging.info("✓ Gemini AI connected")
    
    # Database is initialized in import
    logging.info("✓ Database ready")
    
    return True


def main():
    """Main entry point."""
    setup_logging()
    print_banner()
    
    # Validate configuration
    try:
        validate_config()
    except ValueError as e:
        logging.error(f"Configuration error: {e}")
        logging.error("Please copy .env.example to .env and fill in your API keys")
        sys.exit(1)
    
    print_config()
    
    # Verify connections
    if not verify_connections():
        logging.error("Connection verification failed. Exiting.")
        sys.exit(1)
    
    # Get initial stats
    stats = db_manager.get_stats()
    logging.info(f"📊 Historical stats: {stats['comments_replied']} comments, {stats['messages_replied']} messages replied")
    
    # Run initial check
    logging.info("Running initial check...")
    run_check_cycle()
    
    # Set up scheduler
    logging.info(f"Starting scheduler (checking every {CHECK_INTERVAL_SECONDS} seconds)...")
    scheduler = BlockingScheduler(timezone=TIMEZONE)
    scheduler.add_job(
        run_check_cycle,
        "interval",
        seconds=CHECK_INTERVAL_SECONDS,
        id="check_cycle",
        name="Check for new comments and messages"
    )
    
    try:
        logging.info("🚀 Bot is now running! Press Ctrl+C to stop.")
        scheduler.start()
    except KeyboardInterrupt:
        logging.info("Shutting down...")
        scheduler.shutdown()
        logging.info("Bot stopped. Goodbye! 👋")


if __name__ == "__main__":
    main()
