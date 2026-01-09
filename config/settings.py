"""
ChickThisOut Facebook Automation - Configuration
"""
import os
from pathlib import Path
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Base directories
BASE_DIR = Path(__file__).resolve().parent.parent
PROMPTS_DIR = BASE_DIR / "prompts"

# Facebook API Configuration
FACEBOOK_PAGE_ID = os.getenv("FACEBOOK_PAGE_ID")
FACEBOOK_PAGE_ACCESS_TOKEN = os.getenv("FACEBOOK_PAGE_ACCESS_TOKEN")
FACEBOOK_APP_ID = os.getenv("FACEBOOK_APP_ID")
FACEBOOK_APP_SECRET = os.getenv("FACEBOOK_APP_SECRET")
FACEBOOK_VERIFY_TOKEN = os.getenv("FACEBOOK_VERIFY_TOKEN", "chickthisout_verify_2024")

# Facebook Graph API Base URL
FACEBOOK_GRAPH_API_URL = "https://graph.facebook.com/v18.0"

# Google Gemini Configuration
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")
GEMINI_MODEL = "gemini-2.0-flash"  # Free tier model

# Bot Settings
CHECK_INTERVAL_SECONDS = int(os.getenv("CHECK_INTERVAL_SECONDS", 60))
TIMEZONE = os.getenv("TIMEZONE", "America/Toronto")

# Logging
LOG_LEVEL = os.getenv("LOG_LEVEL", "INFO")

# Database
DATABASE_URL = os.getenv("DATABASE_URL", f"sqlite:///{BASE_DIR}/bot_data.db")

# Restaurant Information (used in AI prompts)
RESTAURANT_INFO = {
    "name": "ChickThisOut",
    "type": "Restaurant",
    "location": "Canada",
    "hours": {
        "monday": "11:00 AM - 8:00 PM",
        "tuesday": "11:00 AM - 8:00 PM",
        "wednesday": "11:00 AM - 8:00 PM",
        "thursday": "11:00 AM - 8:00 PM",
        "friday": "11:00 AM - 8:00 PM",
        "saturday": "11:00 AM - 8:00 PM",
        "sunday": "11:00 AM - 8:00 PM",
    },
    "timezone": "Canada (Eastern Time)",
}


def validate_config():
    """Validate that all required configuration is present."""
    errors = []
    
    if not FACEBOOK_PAGE_ID:
        errors.append("FACEBOOK_PAGE_ID is not set")
    if not FACEBOOK_PAGE_ACCESS_TOKEN:
        errors.append("FACEBOOK_PAGE_ACCESS_TOKEN is not set")
    if not GEMINI_API_KEY:
        errors.append("GEMINI_API_KEY is not set")
    
    if errors:
        raise ValueError(f"Configuration errors: {', '.join(errors)}")
    
    return True
