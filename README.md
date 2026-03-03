# Sentiment Beacon

> **Real-Time Social Media Sentiment Analysis Platform**  
> Multi-platform intelligence for product reputation monitoring, powered by transformer-based NLP and an interactive React dashboard.

---

## Table of Contents

- [Overview](#overview)
- [Key Features](#key-features)
- [Tech Stack](#tech-stack)
- [Architecture](#architecture)
- [Project Structure](#project-structure)
- [Prerequisites](#prerequisites)
- [Local Development Setup](#local-development-setup)
- [Environment Variables Reference](#environment-variables-reference)
- [Deployment](#deployment)
- [API Reference](#api-reference)
- [Contributing](#contributing)
- [Author](#author)
- [License](#license)

---

## Overview

**Sentiment Beacon** is a full-stack, production-ready sentiment intelligence platform that aggregates customer opinions from **YouTube**, **Reddit**, and **Twitter/X** in real time. It applies a multi-layered NLP pipeline — sentiment classification, emotion detection, topic modeling, and predictive forecasting — and surfaces actionable insights through a richly interactive dashboard.

Whether you are tracking a product launch, monitoring brand health, or benchmarking against competitors, Sentiment Beacon gives you a single pane of glass across all major social channels.

---

## Key Features

### Data Ingestion
- **Multi-Platform Scraping** — Live collection from YouTube comments, Reddit threads, and Twitter/X posts via dedicated scraper services
- **CSV Import** — Bulk upload of historical review data
- **Scheduled Pipelines** — Background APScheduler jobs keep data continuously fresh without manual intervention

### AI / NLP Pipeline
- **Transformer Sentiment Classification** — DistilBERT-based positive / negative / neutral scoring
- **Emotion Detection** — Eight primary emotions (Joy, Anger, Sadness, Trust, Fear, Disgust, Anticipation, Surprise) powered by NRCLex
- **VADER Sentiment** — Fast lexicon-based fallback for high-throughput scenarios
- **Topic Modeling** — Latent Dirichlet Allocation (LDA via Gensim) to surface dominant discussion themes
- **Keyword Extraction** — TF-IDF and KeyBERT to identify the most impactful terms per product
- **Predictive Forecasting** — Time-series trend projection for future sentiment trajectories
- **Word Cloud Generation** — Visual frequency maps of key terms per product

### Dashboard & Visualisations
- **Sentiment Trend Charts** — Time-series area and line charts powered by Recharts
- **Emotion Wheel** — Radar-based emotion breakdown per product
- **Aspect Radar Chart** — Multi-dimensional aspect sentiment comparison
- **Topic Clusters** — Visual LDA topic groupings
- **Platform Breakdown Chart** — Source distribution across YouTube, Reddit, and Twitter
- **Live Review Analyzer** — Real-time sentiment scoring of any arbitrary input text
- **Review Feed** — Paginated, filterable stream of ingested reviews
- **Credibility Report** — Review authenticity and quality scoring

### Competitor Intelligence (War Room)
- **Side-by-Side Radar Chart** — Compare two products across all sentiment dimensions simultaneously
- **Head-to-Head Metrics** — Sentiment score, credibility index, and review volume benchmarks
- **Aspect-Level Bar Chart** — Granular breakdown of strengths and weaknesses per product

### Reporting & Alerts
- **PDF / CSV Export** — One-click report generation via ReportLab
- **Configurable Alerts** — Threshold-based notifications for sentiment drops or spikes
- **Executive Summary Cards** — Auto-generated narrative insights surfaced on the dashboard

### Platform
- **JWT Authentication** — Secure login and registration with role-based access control
- **Dark / Light Theme** — Full system-preference-aware theming via `next-themes`
- **Responsive Layout** — Mobile-first design built on TailwindCSS and Radix UI

---

## Tech Stack

| Layer | Technology |
| :--- | :--- |
| **Frontend Framework** | React 18, TypeScript, Vite |
| **Styling** | TailwindCSS, Radix UI (shadcn/ui) |
| **State & Data Fetching** | TanStack React Query v5, React Hook Form, Zod |
| **Charts & Animation** | Recharts, Framer Motion |
| **Routing** | React Router v7 |
| **Backend** | FastAPI, Python 3.11, Uvicorn |
| **Database & Auth** | Supabase (PostgreSQL + Auth) |
| **Backend Auth** | python-jose, passlib (bcrypt) |
| **NLP / ML** | HuggingFace Transformers (DistilBERT), VADER, TextBlob, NRCLex, KeyBERT, Gensim, NLTK, Scikit-learn |
| **Scraping** | google-api-python-client, youtube-comment-downloader, asyncpraw, ntscraper, Tweepy |
| **Task Scheduling** | APScheduler |
| **Reporting** | ReportLab, Matplotlib, WordCloud |
| **Deployment** | Vercel (Frontend) · Render (Backend) |

---

## Architecture

```
+-------------------------------------------------------------+
|                   React Frontend  (Vite)                    |
|  Dashboard | Analytics | Competitors | Reports | Alerts     |
+---------------------------+---------------------------------+
                            |  REST / JSON  (Axios)
+---------------------------v---------------------------------+
|                 FastAPI Backend  (Python 3.11)              |
|                                                             |
|  Routers: /products  /reviews  /scrape  /alerts             |
|           /reports   /settings  /auth   /analytics          |
|                                                             |
|  Services:                                                  |
|   +-- ai_service.py          DistilBERT · emotion · LDA    |
|   +-- nlp_service.py         TF-IDF · topic modeling       |
|   +-- prediction_service.py  trend forecasting             |
|   +-- youtube_scraper.py     YouTube Data API v3           |
|   +-- reddit_scraper.py      asyncpraw                     |
|   +-- twitter_scraper.py     ntscraper / Tweepy            |
|   +-- data_pipeline.py       orchestration layer           |
|   +-- report_service.py      PDF / CSV generation          |
|   +-- scheduler.py           APScheduler background jobs   |
|   +-- wordcloud_service.py   image word-cloud rendering    |
+---------------------------+---------------------------------+
                            |  Supabase JS SDK / REST
+---------------------------v---------------------------------+
|              Supabase  (PostgreSQL + Auth)                   |
|   products | reviews | alerts | reports | users             |
+-------------------------------------------------------------+
```

---

## Project Structure

```
sentiment-beacon/
+-- backend/                        # FastAPI application root
|   +-- main.py                     # App entry point, CORS, startup hooks
|   +-- database.py                 # Supabase client and query helpers
|   +-- auth/
|   |   +-- dependencies.py         # JWT bearer dependency injection
|   |   +-- utils.py                # Password hashing utilities
|   +-- routers/                    # Feature-scoped API route modules
|   |   +-- alerts.py
|   |   +-- auth.py
|   |   +-- reports.py
|   |   +-- settings.py
|   +-- services/                   # All business logic and integrations
|   |   +-- ai_service.py           # Core NLP/ML inference (DistilBERT, NRCLex, LDA)
|   |   +-- nlp_service.py          # TF-IDF, LDA, keyword extraction
|   |   +-- prediction_service.py   # Sentiment trend forecasting
|   |   +-- youtube_scraper.py      # YouTube Data API v3 + comment downloader
|   |   +-- reddit_scraper.py       # Reddit via asyncpraw
|   |   +-- twitter_scraper.py      # Twitter/X via ntscraper / Tweepy
|   |   +-- data_pipeline.py        # Scraper orchestration and processing
|   |   +-- report_service.py       # PDF and CSV report generation
|   |   +-- scheduler.py            # APScheduler periodic job definitions
|   |   +-- wordcloud_service.py    # Word cloud image rendering
|   |   +-- csv_import_service.py   # Bulk CSV review ingestion
|   |   +-- batch_processor.py      # Background batch NLP processing
|   |   +-- insights_service.py     # AI-generated narrative insight cards
|   +-- scripts/                    # DB initialisation and seed scripts
|   |   +-- init_db.py
|   |   +-- setup_reports.py
|   +-- sql/                        # Ordered SQL migration files (01 to 09)
|   +-- requirements.txt            # Lightweight production dependencies
|   +-- requirements-full.txt       # Full dependency set (incl. torch, transformers)
|
+-- src/                            # React frontend (Vite + TypeScript)
|   +-- pages/
|   |   +-- Index.tsx               # Main dashboard
|   |   +-- Analytics.tsx           # Advanced analytics and predictions
|   |   +-- Competitors.tsx         # War Room competitor comparison
|   |   +-- Products.tsx            # Product management
|   |   +-- ProductDetails.tsx      # Single product deep-dive
|   |   +-- Reports.tsx             # Report listing and generation
|   |   +-- Alerts.tsx              # Alert configuration and history
|   |   +-- Settings.tsx            # User and app settings
|   |   +-- Integrations.tsx        # API key and platform configuration
|   |   +-- Help.tsx                # Documentation and onboarding
|   +-- components/
|   |   +-- dashboard/              # Chart and data visualisation widgets
|   |   +-- layout/                 # App shell, sidebar, header
|   |   +-- auth/                   # ProtectedRoute wrapper
|   |   +-- ui/                     # shadcn/ui primitive components
|   +-- hooks/                      # Custom React hooks
|   +-- lib/
|   |   +-- api.ts                  # Centralised Axios API client
|   |   +-- supabase.ts             # Supabase browser client
|   |   +-- utils.ts                # Shared utility functions
|   +-- context/
|   |   +-- AuthContext.tsx         # Authentication React context
|   +-- types/
|       +-- sentinel.ts             # Shared TypeScript type definitions
|
+-- public/
+-- vercel.json                     # Vercel SPA rewrite configuration
+-- render.yaml                     # Render backend service definition
+-- vite.config.ts
+-- tailwind.config.ts
+-- package.json
```

---

## Prerequisites

| Requirement | Version |
| :--- | :--- |
| Node.js | 18 or later |
| Python | 3.11 or later |
| npm | 9 or later |
| Supabase account | - |
| YouTube Data API v3 key | Strongly recommended |
| Reddit API credentials | Optional |
| Twitter/X Bearer Token | Optional |

---

## Local Development Setup

### 1. Clone the Repository

```bash
git clone https://github.com/your-username/sentiment-beacon.git
cd sentiment-beacon
```

### 2. Backend Setup

```bash
cd backend

# Create and activate a virtual environment
python -m venv .venv

# Windows
.venv\Scripts\activate

# macOS / Linux
source .venv/bin/activate

# Install dependencies
pip install -r requirements.txt
```

Create a `.env` file inside `backend/`:

```env
SUPABASE_URL=https://<your-project-ref>.supabase.co
SUPABASE_KEY=<your-anon-key>
SUPABASE_SERVICE_ROLE_KEY=<your-service-role-key>
YOUTUBE_API_KEY=<your-youtube-data-api-v3-key>
REDDIT_CLIENT_ID=<optional>
REDDIT_CLIENT_SECRET=<optional>
TWITTER_BEARER_TOKEN=<optional>
```

Apply the database migrations by running the SQL files in `backend/sql/` in numerical order (01 through 09) against your Supabase project via the Supabase SQL Editor or `psql`.

Start the development server:

```bash
uvicorn main:app --reload --port 8000
```

Interactive API documentation is available at `http://localhost:8000/docs`.

### 3. Frontend Setup

```bash
# From the project root
npm install
```

Create a `.env` file in the project root:

```env
VITE_API_URL=http://localhost:8000
VITE_SUPABASE_URL=https://<your-project-ref>.supabase.co
VITE_SUPABASE_KEY=<your-anon-key>
```

Start the Vite development server:

```bash
npm run dev
```

The application will be available at `http://localhost:5173`.

---

## Environment Variables Reference

### Backend (`backend/.env`)

| Variable | Required | Description |
| :--- | :---: | :--- |
| `SUPABASE_URL` | Yes | Supabase project URL |
| `SUPABASE_KEY` | Yes | Supabase anon / public key |
| `SUPABASE_SERVICE_ROLE_KEY` | Yes | Service role key for authenticated write operations |
| `YOUTUBE_API_KEY` | Yes | Google YouTube Data API v3 key |
| `REDDIT_CLIENT_ID` | Optional | Reddit OAuth app client ID |
| `REDDIT_CLIENT_SECRET` | Optional | Reddit OAuth app client secret |
| `TWITTER_BEARER_TOKEN` | Optional | Twitter/X API v2 bearer token |
| `ENABLE_GPU_TRAINING` | Optional | Set to `true` to enable real BERT fine-tuning on GPU instances |

### Frontend (`.env`)

| Variable | Required | Description |
| :--- | :---: | :--- |
| `VITE_API_URL` | Yes | Full base URL of the backend API |
| `VITE_SUPABASE_URL` | Yes | Supabase project URL |
| `VITE_SUPABASE_KEY` | Yes | Supabase anon / public key |

> Integrations without API keys are **gracefully disabled** in the UI — missing credentials will not cause application errors.

---

## Deployment

Sentiment Beacon uses a split-hosting model with continuous deployment on both platforms.

| Layer | Platform | Config File |
| :--- | :--- | :--- |
| Frontend | Vercel | `vercel.json` |
| Backend | Render | `render.yaml` |

### Frontend → Vercel

1. Push the repository to GitHub.
2. Import the project into Vercel and select the repository root as the project directory.
3. Add the three `VITE_*` environment variables under **Project → Settings → Environment Variables**.
4. Vercel uses `vercel.json` to rewrite all routes to `index.html`, enabling client-side routing.
5. Every push to `main` automatically triggers a new deployment.

### Backend → Render

1. Create a new **Web Service** on Render pointing to the same GitHub repository.
2. Set **Root Directory** to `backend`.
3. Render reads `render.yaml` automatically and configures:
   - **Build Command:** `pip install -r requirements.txt`
   - **Start Command:** `uvicorn main:app --host 0.0.0.0 --port $PORT`
   - **Python Version:** `3.11.9`
4. Add all backend environment variables under **Service → Environment**.
5. Every push to `main` automatically triggers a new build and deploy.

> **Cold-start optimisation:** Heavy AI models (DistilBERT, spaCy) are loaded **lazily** on first request, keeping startup time well within free-tier limits. NLTK corpora are downloaded on first use rather than at startup.

---

## API Reference

Full interactive documentation is auto-generated by FastAPI and available at runtime:

```
http://localhost:8000/docs       # Swagger UI
http://localhost:8000/redoc      # ReDoc
```

### Core Endpoint Summary

| Method | Path | Description |
| :--- | :--- | :--- |
| `GET` | `/api/products` | List all tracked products |
| `POST` | `/api/products` | Add a new product for monitoring |
| `DELETE` | `/api/products/{id}` | Remove a product and its associated data |
| `GET` | `/api/reviews` | Fetch paginated, filterable reviews |
| `POST` | `/api/scrape/trigger` | Trigger a live multi-platform scrape |
| `GET` | `/api/dashboard` | Aggregated sentiment dashboard metrics |
| `GET` | `/api/analytics` | Extended analytics and trend data |
| `GET` | `/api/alerts` | Fetch all configured alert rules |
| `POST` | `/api/alerts` | Create a new alert rule |
| `GET` | `/api/reports` | List previously generated reports |
| `POST` | `/api/reports/generate` | Generate and store a new PDF/CSV report |
| `POST` | `/api/integrations/config` | Save or update platform API credentials |
| `DELETE` | `/api/integrations/{platform}` | Remove saved credentials for a platform |
| `POST` | `/api/auth/register` | Register a new user account |
| `POST` | `/api/auth/login` | Authenticate and receive a JWT |

---

## Contributing

Contributions, bug reports, and feature requests are welcome.

1. Fork the repository
2. Create a feature branch: `git checkout -b feature/your-feature-name`
3. Commit with a descriptive message: `git commit -m 'feat: add your feature'`
4. Push to your fork: `git push origin feature/your-feature-name`
5. Open a Pull Request against the `main` branch

Please ensure all ESLint checks pass (`npm run lint`) before submitting a pull request.

---

## Author

**Sooraj S**  
Full-Stack Developer | AI/ML Engineer

---

## License

This project is licensed under the terms specified in the [LICENSE](LICENSE) file.
