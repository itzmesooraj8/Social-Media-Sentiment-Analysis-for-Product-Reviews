# Deployment Guide

**Project:** Sentiment Beacon  
**Author:** Sooraj S

---

## Overview

Sentiment Beacon uses a **split-hosting** deployment model:

| Layer | Platform | Config File |
| :--- | :--- | :--- |
| Frontend (React SPA) | [Vercel](https://vercel.com) | `vercel.json` |
| Backend (FastAPI) | [Render](https://render.com) | `render.yaml` |
| Database + Auth | [Supabase](https://supabase.com) | Managed via Supabase dashboard |

Both platforms integrate with GitHub and auto-deploy on every push to the `main` branch.

---

## Table of Contents

- [Prerequisites](#prerequisites)
- [Supabase Setup](#supabase-setup)
- [Backend Deployment (Render)](#backend-deployment-render)
- [Frontend Deployment (Vercel)](#frontend-deployment-vercel)
- [Environment Variables Reference](#environment-variables-reference)
- [Post-Deployment Verification](#post-deployment-verification)
- [Advanced: BERT Fine-Tuning on GPU](#advanced-bert-fine-tuning-on-gpu)
- [Redeployment](#redeployment)

---

## Prerequisites

Before deploying, ensure you have:

- A GitHub account with the repository pushed to a `main` branch
- A [Supabase](https://supabase.com) account with a new project created
- A [Render](https://render.com) account
- A [Vercel](https://vercel.com) account
- A Google Cloud project with the **YouTube Data API v3** enabled and an API key generated
- (Optional) Reddit OAuth app credentials
- (Optional) Twitter/X Developer app with a v2 Bearer Token

---

## Supabase Setup

### 1. Apply Database Migrations

Navigate to your Supabase project, open the **SQL Editor**, and run the migration files in the following order:

```
backend/sql/01_init_core.sql
backend/sql/02_security_hardening.sql
backend/sql/03_production_upgrade.sql
backend/sql/04_finalize_production.sql
backend/sql/05_add_youtube_comments.sql
backend/sql/06_add_roles.sql
backend/sql/07_add_engagement_metrics.sql
backend/sql/08_add_reports.sql
backend/sql/09_final_security_audit.sql
```

Run each file in sequence. Do not skip files or run them out of order, as each migration depends on the previous.

### 2. Retrieve API Keys

From the Supabase dashboard, go to **Project Settings -> API** and note the following:

- **Project URL** — used as `SUPABASE_URL`
- **anon / public key** — used as `SUPABASE_KEY`
- **service_role key** — used as `SUPABASE_SERVICE_ROLE_KEY`

> Keep the `service_role` key confidential. It bypasses Row-Level Security and must only be used server-side.

---

## Backend Deployment (Render)

### 1. Create a Web Service

1. Log in to Render and click **New -> Web Service**.
2. Connect your GitHub repository.
3. Configure the service as follows:

| Setting | Value |
| :--- | :--- |
| **Name** | `sentiment-beacon-backend` (or your preferred name) |
| **Region** | Closest to your primary user base |
| **Branch** | `main` |
| **Root Directory** | `backend` |
| **Runtime** | `Python 3` |
| **Build Command** | `pip install -r requirements.txt` |
| **Start Command** | `uvicorn main:app --host 0.0.0.0 --port $PORT` |

Render will automatically detect the Python version from `render.yaml` (`3.11.9`).

### 2. Set Environment Variables

In your Render service, go to **Environment** and add the following key-value pairs:

| Key | Value |
| :--- | :--- |
| `SUPABASE_URL` | Your Supabase project URL |
| `SUPABASE_KEY` | Your Supabase anon key |
| `SUPABASE_SERVICE_ROLE_KEY` | Your Supabase service role key |
| `YOUTUBE_API_KEY` | Your Google YouTube Data API v3 key |
| `REDDIT_CLIENT_ID` | (Optional) Reddit app client ID |
| `REDDIT_CLIENT_SECRET` | (Optional) Reddit app client secret |
| `TWITTER_BEARER_TOKEN` | (Optional) Twitter/X API v2 bearer token |

### 3. Deploy

Click **Create Web Service**. Render will pull the code, install dependencies, and start the server. The first build may take 3–5 minutes.

Once deployed, note the service URL (e.g., `https://sentiment-beacon-backend.onrender.com`). This becomes the value of `VITE_API_URL` in the frontend configuration.

---

## Frontend Deployment (Vercel)

### 1. Import the Project

1. Log in to Vercel and click **Add New -> Project**.
2. Import the GitHub repository.
3. Leave the **Framework Preset** as **Vite** (Vercel detects this automatically).
4. Leave the **Root Directory** as the repository root (`.`).

### 2. Set Environment Variables

In the Vercel project import screen (or later under **Settings -> Environment Variables**), add:

| Key | Value |
| :--- | :--- |
| `VITE_API_URL` | Full URL of your Render backend (e.g., `https://sentiment-beacon-backend.onrender.com`) |
| `VITE_SUPABASE_URL` | Your Supabase project URL |
| `VITE_SUPABASE_KEY` | Your Supabase anon key |

### 3. Deploy

Click **Deploy**. Vercel runs `npm install && npm run build` and publishes the output. The `vercel.json` file configures a catch-all rewrite rule so that all routes are served by `index.html`, enabling React Router's client-side navigation.

Once complete, Vercel provides a `.vercel.app` domain. You can optionally configure a custom domain under **Settings -> Domains**.

---

## Environment Variables Reference

### Backend (Render)

| Variable | Required | Description |
| :--- | :---: | :--- |
| `SUPABASE_URL` | Yes | Supabase project URL |
| `SUPABASE_KEY` | Yes | Supabase anon / public key |
| `SUPABASE_SERVICE_ROLE_KEY` | Yes | Service role key for server-side write access |
| `YOUTUBE_API_KEY` | Yes | Google YouTube Data API v3 key |
| `REDDIT_CLIENT_ID` | Optional | Reddit OAuth app client ID |
| `REDDIT_CLIENT_SECRET` | Optional | Reddit OAuth app client secret |
| `TWITTER_BEARER_TOKEN` | Optional | Twitter/X API v2 bearer token |
| `ENABLE_GPU_TRAINING` | Optional | Set `true` on GPU-enabled instances to activate real BERT fine-tuning |

### Frontend (Vercel)

| Variable | Required | Description |
| :--- | :---: | :--- |
| `VITE_API_URL` | Yes | Full base URL of the deployed backend |
| `VITE_SUPABASE_URL` | Yes | Supabase project URL |
| `VITE_SUPABASE_KEY` | Yes | Supabase anon / public key |

> Integrations that are missing their API keys are automatically disabled in the UI. No errors will be thrown for optional missing credentials.

---

## Post-Deployment Verification

After both services are live, perform the following checks:

1. **Backend health check** — Visit `https://<your-render-url>/` and confirm the JSON response:
   ```json
   { "message": "Sentiment Beacon AI Backend is Operational", "status": "online" }
   ```
2. **API docs** — Visit `https://<your-render-url>/docs` and confirm the Swagger UI loads.
3. **Frontend loads** — Open the Vercel URL and confirm the login page renders.
4. **Authentication** — Register a new account and confirm you are redirected to the dashboard.
5. **Add a product** — Create a test product and trigger a live analysis. Confirm reviews appear in the dashboard within 60–90 seconds.
6. **Report generation** — Generate a PDF report and confirm the download succeeds.

---

## Advanced: BERT Fine-Tuning on GPU

By default, the platform uses a pre-trained `distilbert-base-uncased-finetuned-sst-2-english` model for sentiment classification. For domain-specific fine-tuning on your own labelled dataset:

1. Deploy the backend to a GPU-enabled instance (e.g., a Render GPU instance, AWS `ec2-g4dn`, or Paperspace).
2. Set the environment variable `ENABLE_GPU_TRAINING=true`.
3. Use the **Model Training** interface in the Settings page to initiate a fine-tuning job.

> Standard free-tier deployments do not support GPU training. The training UI on standard instances will simulate the training process for demonstration purposes.

---

## Redeployment

To redeploy after pushing changes to the repository:

- **Vercel** — Automatically redeploys on every push to `main`. No action required.
- **Render** — Automatically redeploys on every push to `main`. No action required.

To trigger a manual redeploy without a code change:
- **Vercel**: Go to **Deployments** and click **Redeploy** on the latest deployment.
- **Render**: Go to the service dashboard and click **Manual Deploy -> Deploy latest commit**.

---

*For technical implementation details, see [TECHNICAL_GUIDE.md](TECHNICAL_GUIDE.md).*  
*For end-user feature documentation, see [USER_MANUAL.md](USER_MANUAL.md).*
