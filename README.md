# 🍗 ChickThisOut Facebook Automation Bot

An AI-powered automation bot that automatically responds to Facebook comments and Messenger messages for ChickThisOut restaurant.
Run for free 24/7 on Vercel using webhooks!

## Features

- ✅ **Instant Replies** - Uses Facebook Webhooks for real-time responses
- ✅ **Auto-reply to Comments** - Responds to customer comments on your Facebook posts
- ✅ **Auto-reply to Messages** - Responds to Messenger conversations
- ✅ **AI-Powered Responses** - Uses Google Gemini (free tier) for intelligent, contextual responses
- ✅ **Run 24/7 for Free** - Serverless deployment via Vercel

## Tech Stack

- **Python 3.10+** (Flask)
- **Facebook Graph API**
- **Google Gemini 2.0 Flash**
- **Vercel** (Serverless Deployment)

## Prerequisites

1. **Facebook Page** that you manage
2. **Facebook Developer Account** (free)
3. **Google AI Studio account** for Gemini API (free)
4. **Vercel Account** (free)
5. **GitHub Account** (free)

---

## 🚀 Deployment Guide

### Step 1: Fork/Clone to GitHub

Make sure this code is in your own GitHub repository.

### Step 2: Deploy to Vercel

1. Go to [Vercel](https://vercel.com/new)
2. Import your GitHub repository
3. In **Environment Variables**, add the following:

| Name | Value | Description |
|------|-------|-------------|
| `FACEBOOK_PAGE_ACCESS_TOKEN` | (Your Page Token) | From Facebook Graph API Tool |
| `FACEBOOK_PAGE_ID` | `532393093294515` | Your Page ID |
| `FACEBOOK_APP_SECRET` | (Your App Secret) | From Facebook App Basic Settings |
| `FACEBOOK_VERIFY_TOKEN` | `chickthisout_secret_2024` | Any secret string you choose |
| `GEMINI_API_KEY` | (Your Gemini Key) | From Google AI Studio |

4. Click **Deploy**

### Step 3: Configure Facebook Webhook

1. Go to [Facebook Developers](https://developers.facebook.com/) → Your App
2. Click **Add Product** → **Webhooks**
3. Select **"Page"** (not User) from the dropdown
4. Click **"Subscribe to this object"**
5. Enter:
   - **Callback URL**: `https://your-project-name.vercel.app/api/webhook`
   - **Verify Token**: `chickthisout_secret_2024` (Must match Vercel env var)
6. Click **Verify and Save**

### Step 4: Subscribe to Events

In the Webhooks page:
1. Subscribe to **`feed`** (for comments)
2. Subscribe to **`messages`** (for Messenger)
3. **IMPORTANT**: Click **"Add Subscriptions"** under the "Pages" section and select your page ("Chick This Out")

### Step 5: Switch to Live

1. Go to **App Settings** → **Basic**
2. Add Privacy Policy URL: `https://your-project-name.vercel.app/privacy`
3. Switch **App Mode** toggle to **Live**

---

## Customizing AI Personality

Edit `prompts/restaurant_prompt.txt` to change how the bot behaves.
After editing, `git push` to GitHub and Vercel will automatically redeploy!

---

## Troubleshooting

### "Verification Failed"
- Ensure `FACEBOOK_VERIFY_TOKEN` in Vercel matches exactly what you type in Facebook.
- Did you redeploy Vercel after adding the environment variable?

### Bot not replying
1. Check **Vercel Logs**: Project → Logs
2. Did you subscribe the specific Page in Webhooks settings? (Step 4.3)
3. Is `FACEBOOK_PAGE_ACCESS_TOKEN` correct and does it have `pages_messaging` permission?

---

## License

MIT License - Use freely for your restaurant!

Made with ❤️ for ChickThisOut Restaurant 🍗
