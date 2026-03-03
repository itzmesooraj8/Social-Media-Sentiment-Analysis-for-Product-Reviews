# Technical Implementation Guide

**Project:** Sentiment Beacon
**Version:** 1.0.0
**Author:** Sooraj S

---

## Table of Contents

- [System Architecture](#system-architecture)
- [Technology Stack](#technology-stack)
- [Database Schema](#database-schema)
- [AI / NLP Pipeline](#ai--nlp-pipeline)
- [API Documentation](#api-documentation)
- [Developer Setup](#developer-setup)

---

## System Architecture

Sentiment Beacon follows a **Modular Monolith** pattern — a single deployable backend unit with clearly separated, independently testable service modules. This approach provides the simplicity of a monolith with the code organisation benefits of microservices, which is appropriate for this scale.

### Component Overview

```
+---------------------+        REST/JSON (Axios)        +------------------------+
|  React SPA (Vite)   | <-----------------------------> |   FastAPI Backend       |
|                     |                                  |   (Python 3.11)         |
|  - Dashboard        |                                  |                         |
|  - Analytics        |                                  |  Routers (feature APIs) |
|  - Competitors      |                                  |  Services (business     |
|  - Reports          |                                  |    logic + ML)          |
|  - Alerts           |                                  |  Schedulers (background)|
+---------------------+                                  +----------+--------------+
                                                                     |
                                                         Supabase SDK / REST
                                                                     |
                                                         +-----------v--------------+
                                                         |  Supabase (PostgreSQL)   |
                                                         |  + Row-Level Security    |
                                                         |  + Supabase Auth         |
                                                         +--------------------------+
```

### Request Lifecycle

1. The React frontend issues an authenticated REST request via Axios.
2. FastAPI validates the JWT, routes the request to the appropriate router module.
3. The router delegates business logic to the relevant service (e.g., `ai_service`, `data_pipeline`).
4. Data is read from or written to Supabase via the Python Supabase SDK.
5. The response is serialised with Pydantic and returned as JSON.

Background scraping and scheduled jobs run on a separate APScheduler thread pool, completely decoupled from the request-response cycle.

---

## Technology Stack

### Backend

| Component | Library / Version |
| :--- | :--- |
| Framework | FastAPI |
| ASGI Server | Uvicorn with standard extras |
| Language | Python 3.11 |
| Auth | python-jose (JWT), passlib (bcrypt) |
| Database | supabase-py |
| Configuration | python-dotenv |

#### AI / NLP Libraries

| Purpose | Library |
| :--- | :--- |
| Sentiment Classification | HuggingFace Transformers — `distilbert-base-uncased-finetuned-sst-2-english` |
| Emotion Detection | NRCLex |
| Lexicon Sentiment (fallback) | vaderSentiment |
| Keyword Extraction | KeyBERT, Scikit-learn TF-IDF |
| Topic Modeling | Gensim (LDA) |
| Text Preprocessing | NLTK (tokenisation, stop-words) |
| Readability Scoring | textstat |
| General NLP helpers | TextBlob |

#### Scraping Libraries

| Platform | Library |
| :--- | :--- |
| YouTube | google-api-python-client, youtube-comment-downloader |
| Reddit | asyncpraw |
| Twitter/X | ntscraper, Tweepy |

#### Supporting Libraries

| Purpose | Library |
| :--- | :--- |
| Task Scheduling | APScheduler |
| PDF Generation | ReportLab |
| Word Cloud Rendering | wordcloud, Matplotlib |
| CSV Handling | pandas |

### Frontend

| Component | Library / Version |
| :--- | :--- |
| Framework | React 18 |
| Build Tool | Vite |
| Language | TypeScript |
| Styling | TailwindCSS, Radix UI (shadcn/ui) |
| State / Fetching | TanStack React Query v5 |
| Forms | React Hook Form, Zod |
| Charts | Recharts |
| Animation | Framer Motion |
| Routing | React Router v7 |
| HTTP Client | Axios |
| Auth Client | @supabase/supabase-js |

---

## Database Schema

The database is hosted on **Supabase (PostgreSQL 15+)** with Row-Level Security (RLS) enabled. Migrations are applied in order via the numbered SQL files in `backend/sql/`.

### Core Tables

#### `products`

| Column | Type | Notes |
| :--- | :--- | :--- |
| `id` | UUID (PK) | Auto-generated |
| `name` | TEXT | Product display name |
| `description` | TEXT | Optional description |
| `keywords` | TEXT[] | Keywords used to drive scraper queries |
| `platforms` | TEXT[] | Active platforms: youtube, reddit, twitter |
| `created_at` | TIMESTAMPTZ | Auto-set on insert |

#### `reviews`

| Column | Type | Notes |
| :--- | :--- | :--- |
| `id` | UUID (PK) | Auto-generated |
| `product_id` | UUID (FK) | References `products.id` |
| `platform` | TEXT | Source platform |
| `content` | TEXT | Raw review or comment text |
| `username` | TEXT | Author handle |
| `rating` | FLOAT | Normalised rating (0–5), if available |
| `source_url` | TEXT | Direct link to original post |
| `content_hash` | TEXT | SHA-256 hash for deduplication |
| `created_at` | TIMESTAMPTZ | Date of the original post |

#### `sentiment_analysis`

| Column | Type | Notes |
| :--- | :--- | :--- |
| `id` | UUID (PK) | Auto-generated |
| `review_id` | UUID (FK) | References `reviews.id` |
| `score` | FLOAT | Confidence score (0.0–1.0) |
| `label` | TEXT | POSITIVE, NEGATIVE, or NEUTRAL |
| `emotions` | JSONB | Array of `{name, score}` objects |
| `aspects` | JSONB | Array of `{aspect, sentiment}` objects |
| `credibility` | FLOAT | Spam/bot probability score (0–1) |

#### `topic_analysis`

| Column | Type | Notes |
| :--- | :--- | :--- |
| `id` | UUID (PK) | Auto-generated |
| `product_id` | UUID (FK) | References `products.id` |
| `topic_name` | TEXT | LDA-extracted topic label |
| `keywords` | TEXT[] | Associated keywords for this topic |
| `size` | INTEGER | Relative frequency / relevance weight |
| `created_at` | TIMESTAMPTZ | Generation timestamp |

---

## AI / NLP Pipeline

Data flows through a structured, sequential pipeline after ingestion. Each step is implemented as an independent service module to support unit testing and future replacement.

```
Raw Text Input
      |
      v
[1] Preprocessing     -- regex cleaning, HTML stripping, length filtering,
      |                  SHA-256 deduplication
      v
[2] Sentiment         -- DistilBERT batch inference (primary)
      |                  VADER lexicon scoring (fallback / validation)
      v
[3] Emotion Detection -- NRCLex emotion mapping (Joy, Anger, Sadness,
      |                  Trust, Fear, Disgust, Anticipation, Surprise)
      v
[4] Keyword Extraction -- TF-IDF vectorisation + KeyBERT semantic extraction
      |
      v
[5] Topic Modeling    -- LDA (Gensim) over batched document corpus
      |
      v
[6] Credibility Score -- heuristics: account age, review length, repetition
      |
      v
[7] Persistence       -- Results written to Supabase with relational integrity
```

### Key Implementation Notes

- **Lazy Loading:** Transformer models and spaCy pipelines are instantiated on first use, not at application startup. This prevents cold-start timeouts on free-tier hosting.
- **Batch Inference:** Reviews are grouped into batches before being passed to the transformer pipeline, significantly reducing GPU/CPU overhead.
- **Deduplication:** A SHA-256 hash of the review content is stored on insert. Duplicate hashes are skipped at the pipeline level.
- **Fallback Strategy:** If the transformer model is unavailable (e.g., memory constraints), the pipeline falls back gracefully to VADER for all scoring.

---

## API Documentation

FastAPI auto-generates OpenAPI documentation from route decorators and Pydantic schemas.

| UI | URL |
| :--- | :--- |
| Swagger UI | `http://localhost:8000/docs` |
| ReDoc | `http://localhost:8000/redoc` |

### Key Endpoints

| Method | Path | Description |
| :--- | :--- | :--- |
| `GET` | `/` | Health check — confirms API is operational |
| `GET` | `/api/products` | List all tracked products |
| `POST` | `/api/products` | Create a new product |
| `DELETE` | `/api/products/{id}` | Delete a product and its data |
| `GET` | `/api/reviews` | Paginated review feed with filters |
| `POST` | `/api/scrape/trigger` | Trigger a live scrape for a product |
| `GET` | `/api/dashboard` | Aggregated metrics for the dashboard |
| `GET` | `/api/analytics` | Extended analytics and trend data |
| `GET` | `/api/predictions/{product_id}` | Time-series sentiment forecast |
| `POST` | `/api/reports/generate` | Generate a PDF or CSV report |
| `GET` | `/api/alerts` | Retrieve all alert rules |
| `POST` | `/api/integrations/config` | Save platform API credentials |
| `POST` | `/api/auth/register` | Register a user account |
| `POST` | `/api/auth/login` | Authenticate and receive a JWT |

---

## Developer Setup

### Prerequisites

- Python 3.11+
- pip
- A Supabase project (free tier is sufficient for development)

### Steps

```bash
# 1. Navigate to the backend directory
cd backend

# 2. Create and activate a virtual environment
python -m venv .venv

# Windows
.venv\Scripts\activate
# macOS / Linux
source .venv/bin/activate

# 3. Install all dependencies
pip install -r requirements.txt

# 4. Create the environment configuration file
```

Create `backend/.env` with the following variables:

```env
SUPABASE_URL=https://<your-project-ref>.supabase.co
SUPABASE_KEY=<your-anon-key>
SUPABASE_SERVICE_ROLE_KEY=<your-service-role-key>
YOUTUBE_API_KEY=<your-google-api-key>
REDDIT_CLIENT_ID=<optional>
REDDIT_CLIENT_SECRET=<optional>
TWITTER_BEARER_TOKEN=<optional>
```

```bash
# 5. Apply database migrations (run these in order in the Supabase SQL Editor)
#    backend/sql/01_init_core.sql
#    backend/sql/02_security_hardening.sql
#    ...through...
#    backend/sql/09_final_security_audit.sql

# 6. Start the development server
uvicorn main:app --reload --port 8000
```

The API will be available at `http://localhost:8000`.  
Interactive documentation is at `http://localhost:8000/docs`.

---

*For deployment instructions, see [DEPLOYMENT_GUIDE.md](DEPLOYMENT_GUIDE.md).*  
*For end-user feature documentation, see [USER_MANUAL.md](USER_MANUAL.md).*
