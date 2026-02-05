# Deployment Guide

This guide outlines the steps to deploy the Sentiment Beacon application to a production environment.

## 1. Backend Deployment (Render / Heroku / AWS)

The backend is a FastAPI application using Python.

### Option A: Render.com (Recommended for ease)

1.  **Create a new Web Service** on Render.
2.  **Connect your GitHub repository**.
3.  **Settings**:
    -   **Build Command**: `pip install -r backend/requirements.txt`
    -   **Start Command**: `cd backend && python -m uvicorn main:app --host 0.0.0.0 --port $PORT`
4.  **Environment Variables**:
    Add the following in the Render Dashboard:
    -   `SUPABASE_URL`: Your Supabase Project URL
    -   `SUPABASE_KEY`: Your Supabase Anon/Service Key
    -   `REDDIT_CLIENT_ID`: (Optional)
    -   `REDDIT_CLIENT_SECRET`: (Optional)
    -   `TWITTER_BEARER_TOKEN`: (Optional)
    -   `YOUTUBE_API_KEY`: (Optional)
    -   `PYTHON_VERSION`: `3.9.18` (or similar)

### Option B: Docker

1.  Build the image:
    ```bash
    docker build -t sentiment-backend ./backend
    ```
2.  Run the container:
    ```bash
    docker run -p 8000:8000 --env-file backend/.env sentiment-backend
    ```

## 2. Frontend Deployment (Vercel / Netlify)

The frontend is a React + Vite application.

### Option A: Vercel (Recommended)

1.  **Install Vercel CLI** or use the Dashboard.
2.  **Import Project** from GitHub.
3.  **Build Settings**:
    -   **Framework Preset**: Vite
    -   **Build Command**: `npm run build`
    -   **Output Directory**: `dist`
4.  **Environment Variables**:
    -   `VITE_API_URL`: The URL of your deployed backend (e.g., `https://sentiment-backend.onrender.com`).
    -   `VITE_SUPABASE_URL`: Your Supabase URL.
    -   `VITE_SUPABASE_ANON_KEY`: Your Supabase Anon Key.

## 3. Database (Supabase)

Since Supabase is a managed PostgreSQL service, no deployment is needed. Ensure:
1.  Your `products` and `reviews` tables are created (use `backend/sql/schema.sql` if provided).
2.  RLS (Row Level Security) policies allow your backend to read/write.

## 4. Verification

1.  Open your Vercel URL.
2.  Go to the **System Status** page to verify the frontend can reach the backend.
3.  Trigger a test scrape to ensure external APIs are reachable from the cloud server.
