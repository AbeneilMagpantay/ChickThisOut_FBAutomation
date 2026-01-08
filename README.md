# 🍗 ChickThisOut Facebook Automation Bot

An AI-powered automation bot that automatically responds to Facebook comments and Messenger messages for ChickThisOut restaurant.

## Features

- ✅ **Auto-reply to Comments** - Responds to customer comments on your Facebook posts
- ✅ **Auto-reply to Messages** - Responds to Messenger conversations
- ✅ **AI-Powered Responses** - Uses Google Gemini (free tier) for intelligent, contextual responses
- ✅ **Smart Duplicate Detection** - Never replies twice to the same comment/message
- ✅ **Conversation Context** - Considers previous messages for better responses
- ✅ **Activity Logging** - Tracks all bot activity in a local database
- ✅ **Customizable Personality** - Easy to modify AI behavior via prompt file

## Tech Stack

- **Python 3.10+**
- **Facebook Graph API** - Official Facebook API for page management
- **Google Gemini** - Free AI model for generating responses
- **SQLite** - Local database for tracking processed items
- **APScheduler** - Job scheduling for periodic checks

## Prerequisites

Before you start, you'll need:

1. **Python 3.10 or higher** installed
2. **A Facebook Page** that you manage
3. **Facebook Developer Account** (free)
4. **Google AI Studio account** for Gemini API (free)

---

## Setup Guide

### Step 1: Clone and Install Dependencies

```bash
# Navigate to the project folder
cd ChichThisOut_FBAutomation

# Create a virtual environment
python -m venv venv

# Activate it
# Windows:
venv\Scripts\activate
# Mac/Linux:
source venv/bin/activate

# Install dependencies
pip install -r requirements.txt
```

### Step 2: Get Your Facebook Credentials

1. Go to [Facebook Developers](https://developers.facebook.com/)
2. Click "My Apps" → "Create App"
3. Select "Business" type
4. Fill in app details and create

**Get Page Access Token:**

1. In your app, go to "Tools" → "Graph API Explorer"
2. Select your app from dropdown
3. Click "Add Permission" and add:
   - `pages_manage_posts`
   - `pages_read_engagement`
   - `pages_messaging`
   - `pages_manage_metadata`
4. Click "Generate Token"
5. Select your Facebook Page
6. Copy the token

**Get Page ID:**

1. Go to your Facebook Page
2. Click "About"
3. Scroll down to find "Page ID" or use Graph API Explorer:
   ```
   GET /me?fields=id,name (with page token selected)
   ```

### Step 3: Get Google Gemini API Key

1. Go to [Google AI Studio](https://makersuite.google.com/app/apikey)
2. Click "Create API Key"
3. Copy the API key

### Step 4: Configure Environment

```bash
# Copy the example env file
copy .env.example .env    # Windows
# or
cp .env.example .env      # Mac/Linux
```

Edit `.env` and fill in your values:

```env
FACEBOOK_PAGE_ID=your_page_id_here
FACEBOOK_PAGE_ACCESS_TOKEN=your_token_here
GEMINI_API_KEY=your_gemini_key_here
```

### Step 5: Customize AI Personality (Optional)

Edit `prompts/restaurant_prompt.txt` to customize:
- Restaurant information (menu items, delivery options, etc.)
- Response style and tone
- What the AI should/shouldn't say

### Step 6: Run the Bot

```bash
python src/main.py
```

You should see:

```
╔═══════════════════════════════════════════════════════════╗
║   🍗 ChickThisOut Facebook Automation Bot 🍗              ║
╚═══════════════════════════════════════════════════════════╝

✓ Facebook API connected
✓ Gemini AI connected
✓ Database ready
🚀 Bot is now running! Press Ctrl+C to stop.
```

---

## Configuration Options

| Variable | Description | Default |
|----------|-------------|---------|
| `CHECK_INTERVAL_SECONDS` | How often to check for new comments/messages | `60` |
| `TIMEZONE` | Your timezone | `America/Toronto` |
| `LOG_LEVEL` | Logging verbosity (DEBUG, INFO, WARNING, ERROR) | `INFO` |

---

## Project Structure

```
ChichThisOut_FBAutomation/
├── config/
│   └── settings.py          # Configuration and environment loading
├── src/
│   ├── facebook_api.py      # Facebook Graph API wrapper
│   ├── ai_responder.py      # Gemini AI integration
│   ├── comment_handler.py   # Comment processing logic
│   ├── message_handler.py   # Message processing logic
│   ├── database.py          # SQLite database models
│   └── main.py              # Application entry point
├── prompts/
│   └── restaurant_prompt.txt # AI personality and guidelines
├── .env.example             # Environment template
├── .gitignore               # Git ignore rules
├── requirements.txt         # Python dependencies
└── README.md                # This file
```

---

## How It Works

1. **Scheduler** runs every 60 seconds (configurable)
2. **Fetches** recent posts and their comments
3. **Checks** each comment against the database
4. **Generates** AI response for new comments
5. **Posts** reply and marks as processed
6. Same flow for **Messenger messages**

---

## Important Notes

### Facebook App Review

For production use, you'll need to submit your Facebook App for review to get permanent access tokens. The development tokens expire after ~60 days.

Required permissions for review:
- `pages_messaging` - For replying to messages
- `pages_read_engagement` - For reading comments
- `pages_manage_posts` - For replying to comments

### Rate Limits

- Facebook API: ~200 calls per hour per user
- Gemini Free Tier: 60 requests per minute

The bot is designed to stay well within these limits.

### Token Security

- **NEVER** commit your `.env` file
- Use environment variables in production
- Regenerate tokens if compromised

---

## Troubleshooting

### "Facebook token verification failed"
- Your token may have expired (regenerate in Graph API Explorer)
- Make sure you have the required permissions

### "AI failed to generate response"
- Check your GEMINI_API_KEY
- You may have hit rate limits (wait a few minutes)

### Bot not replying to comments
- Ensure the comment is not hidden
- Check if you already replied manually
- Look at bot_data.db for error details

---

## Contributing

Feel free to modify and improve! Key areas for enhancement:
- Add webhook support for real-time updates
- Implement sentiment analysis for urgent messages
- Add support for multiple pages

---

## License

MIT License - Use freely for your restaurant!

---

Made with ❤️ for ChickThisOut Restaurant 🍗
