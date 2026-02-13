# Deployment Guide (Vercel + Render)

This project is configured for a split deployment:
- **Frontend**: Vercel (serves React app)
- **Backend**: Render (serves Python FastAPI)

## 1. Environment Variables (CRITICAL)

The following environment variables **MUST** be set in your deployment dashboards for the app to function correctly.

### Backend (Render)
Go to your Render Service -> **Environment**.

| Key | Value / Description |
| :--- | :--- |
| `PYTHON_VERSION` | `3.11.0` (or `3.9+`) |
| `SUPABASE_URL` | Your Supabase Project URL |
| `SUPABASE_KEY` | Your Supabase Anon Key |
| `SUPABASE_SERVICE_ROLE_KEY` | Your Supabase Service Role Key (Required for writing data) |
| `YOUTUBE_API_KEY` | Your Google YouTube Data API Key |
| `REDDIT_CLIENT_ID` | (Optional) Reddit App ID |
| `REDDIT_CLIENT_SECRET` | (Optional) Reddit App Secret |
| `TWITTER_BEARER_TOKEN` | (Optional) Twitter Bearer Token |

> **Note:** If `REDDIT` or `TWITTER` keys are missing, those integrations will be **disabled** in the dashboard.

### Frontend (Vercel)
Go to your Vercel Project -> **Settings** -> **Environment Variables**.

| Key | Value |
| :--- | :--- |
| `VITE_API_URL` | The *full* URL of your Render Backend (e.g. `https://your-app.onrender.com`) |
| `VITE_SUPABASE_URL` | Your Supabase Project URL |
| `VITE_SUPABASE_KEY` | Your Supabase Anon Key |

---

## 2. Startup Optimization

The backend has been optimized to prevent timeouts on free-tier services.
- Heavy AI models (BERT, Spacy) are loaded **lazily** (only on first request).
- NLTK data is downloaded only on first use.
- **Startup Command**: `uvicorn backend.main:app --host 0.0.0.0 --port 10000` (Render detects this automatically).

## 3. "Model Training" Feature

The "Model Training" UI allows users to trigger training jobs. 
- On standard hosting, this simulates training logic for demonstration.
- To enable **Real BERT Fine-Tuning**, you must deploy to a GPU-enabled instance (e.g., paperspace, AWS ec2-g4dn) and set `ENABLE_GPU_TRAINING=true`.

## 4. Updates

To redeploy after changes:
1. Push to `main` branch.
2. Vercel and Render will auto-trigger builds.
