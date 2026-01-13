# 🚀 Quick Start Guide - Reddit API Setup

## Get Reddit API Credentials (5 minutes)

1. **Go to Reddit Apps**: https://www.reddit.com/prefs/apps
2. **Click "create another app..." at the bottom**
3. **Fill in the form:**
   - Name: `Sentiment Beacon`
   - App type: Select **"script"**
   - Description: `Sentiment analysis for product reviews`
   - About URL: (leave blank)
   - Redirect URI: `http://localhost:8000`
4. **Click "create app"**
5. **Copy your credentials:**
   - **Client ID**: The string under "personal use script" (14 characters)
   - **Client Secret**: The "secret" field (27 characters)

## Update .env File

Open `.env` and replace:
```env
REDDIT_CLIENT_ID=your_reddit_client_id_here
REDDIT_CLIENT_SECRET=your_reddit_client_secret_here
```

With your actual credentials:
```env
REDDIT_CLIENT_ID=abc123xyz456
REDDIT_CLIENT_SECRET=abc123xyz456abc123xyz456abc
```

## Test It

1. Restart backend: `python backend/main.py`
2. Add a product in the UI
3. Click "Scrape Reddit Reviews"
4. Watch reviews appear in real-time!

**That's it!** 🎉
