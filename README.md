# ChickThisOut Facebook Automation

A serverless automated responder for the ChickThisOut Facebook page. It handles comments and Messenger inquiries using Facebook Webhooks and Google Gemini AI.

## Overview

- **Real-time responses**: Uses webhooks to reply instantly to comments and messages.
- **AI Integration**: Generates context-aware replies using Google Gemini.
- **Cost**: $0/month (uses free tiers of Vercel and Google AI).
- **Architecture**: Python (Flask) backend deployed as a serverless function.

## Setup & Deployment

### 1. Prerequisites
- **Vercel Account** (for hosting)
- **Facebook Developer Account** (for the App & Page token)
- **Google AI Studio Key** (for Gemini)

### 2. Deployment
This project is designed to be deployed directly from GitHub to Vercel.

1. **Fork** or **Push** this code to your GitHub.
2. Import the project in Vercel.
3. Configure the **Environment Variables** in Vercel settings:

| Variable | Description |
|----------|-------------|
| `FACEBOOK_PAGE_ACCESS_TOKEN` | Token from Facebook Graph API (requires `pages_messaging`, `pages_manage_posts`, `pages_read_engagement`) |
| `FACEBOOK_PAGE_ID` | The numeric ID of the Facebook Page |
| `FACEBOOK_APP_SECRET` | Found in Facebook App Basic Settings |
| `FACEBOOK_VERIFY_TOKEN` | A random string you create (e.g., `my_secret_token_2024`) |
| `GEMINI_API_KEY` | API Key from Google AI Studio |

### 3. Facebook Configuration
Once deployed, you need to connect Facebook to your Vercel URL.

1. Go to the **Facebook Developers Portal** > Your App > **Webhooks**.
2. Select **Page** from the dropdown.
3. Click **Subscribe to this object**.
   - **Callback URL**: `https://your-project.vercel.app/api/webhook`
   - **Verify Token**: Must match the `FACEBOOK_VERIFY_TOKEN` you set in Vercel.
4. Under "Subscription Fields", subscribe to:
   - `feed` (for comments)
   - `messages` (for direct messages)

**Important**: You must also link the specific Page in the **Messenger API Settings** or **Webhooks** section by clicking "Add Subscriptions" next to the Page name.

## Customizing the AI

The bot's behavior is defined in `prompts/restaurant_prompt.txt`.
To update the bot's knowledge (e.g., new hours, menu items), simply edit this text file and push the changes to GitHub. Vercel will auto-deploy the update.

## Troubleshooting

- **Bot not replying?** Check Vercel logs. If you see successful webhook requests but no reply, check the permissions on your Facebook Page Access Token.
- **Verification Failed?** Ensure the `FACEBOOK_VERIFY_TOKEN` matches exactly in both Vercel and Facebook.

## Local Development (Optional)

You can run the Flask app locally for testing, but you will need a tool like `ngrok` to expose your local port to Facebook.

```bash
pip install -r requirements.txt
python src/webhook.py
```

