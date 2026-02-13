# Technical Implementation Guide

**Project:** Social Media Sentiment Analysis for Product Reviews
**Version:** 1.0.0
**Date:** 2026-02-08

## 1. System Architecture

The system follows a modern **microservices-inspired monolithic architecture** (Modular Monolith) designed for scalability and real-time processing.

### High-Level Components
1.  **Frontend (SPA)**: React + TypeScript + Vite. Uses `Recharts` for visualization and `Axios` for API communication. Handles real-time updates via WebSockets.
2.  **Backend (API + Worker)**: FastAPI (Python). Handles REST requests, WebSocket connections, and background processing tasks.
3.  **Data Ingestion Layer**: Specialized scrapers for YouTube (API), Reddit (AsyncPRAW), and Twitter (Tweepy/Scraper).
4.  **AI/ML Pipeline**: Asynchronous processing pipeline using Hugging Face Transformers (DistilBERT), KeyBERT, and Gensim (LDA).
5.  **Database**: Supabase (PostgreSQL) for relational data storage.

## 2. Technology Stack

### Backend
-   **Framework**: FastAPI
-   **Server**: Uvicorn (ASGI)
-   **Language**: Python 3.9+
-   **AI Libraries**: 
    -   `transformers` (Hugging Face) - Sentiment Analysis
    -   `keybert` - Keyword Extraction
    -   `gensim` - Topic Modeling (LDA)
    -   `nrclex` - Emotion Detection
    -   `spacy` - Aspect-Based Sentiment Analysis (ABSA)
-   **Scraping**: `google-api-python-client`, `asyncpraw`, `tweepy`, `ntscraper`

### Frontend
-   **Framework**: React 18
-   **Build Tool**: Vite
-   **Styling**: TailwindCSS + Shadcn UI (Radix Primitives)
-   **State Management**: React Query (TanStack Query)
-   **Visualization**: Recharts, D3-cloud (WordCloud)

### Infrastructure
-   **Database**: Supabase (PostgreSQL 15+)
-   **Authentication**: Supabase Auth (RLS Policies enabled)

## 3. Database Schema (Supabase)

### Tables
1.  `products`
    -   `id` (UUID, PK): Unique product identifier.
    -   `name` (Text): Product name.
    -   `description` (Text): Optional description.
    -   `keywords` (Text[]): Array of keywords to track.
    -   `created_at` (Timestamp): Creation date.
    
2.  `reviews`
    -   `id` (UUID, PK): Unique review identifier.
    -   `product_id` (UUID, FK -> products.id): Associated product.
    -   `platform` (Text): Source platform (reddit, youtube, twitter).
    -   `content` (Text): The raw review text.
    -   `username` (Text): Author username.
    -   `rating` (Float): Optional normalized rating (0-5).
    -   `source_url` (Text): Link to original post.
    -   `created_at` (Timestamp): Date of the review.

3.  `sentiment_analysis`
    -   `id` (UUID, PK): Unique analysis identifier.
    -   `review_id` (UUID, FK -> reviews.id): Linked review.
    -   `score` (Float): Sentiment score (0.0 to 1.0).
    -   `label` (Text): POSITIVE, NEGATIVE, NEUTRAL.
    -   `emotions` (JSONB): Detected emotions (e.g., `[{"name": "Joy", "score": 0.8}]`).
    -   `aspects` (JSONB): Aspect-based sentiment (e.g., `[{"aspect": "battery", "sentiment": "negative"}]`).
    -   `credibility` (Float): Bot/spam probability score.

4.  `topic_analysis`
    -   `id` (UUID, PK): Unique topic identifier.
    -   `topic_name` (Text): Extracted topic/keyword.
    -   `size` (Integer): Frequency/Relevance score.
    -   `created_at` (Timestamp): generation date.

## 4. API Documentation

The backend automatically generates interactive API documentation.
-   **Swagger UI**: `http://localhost:8000/docs`
-   **ReDoc**: `http://localhost:8000/redoc`

### Key Endpoints
-   `GET /api/system/status`: Real-time system health check.
-   `POST /api/products`: Create a new product to track.
-   `POST /api/scrape/trigger`: Manually trigger the scraping pipeline for a product.
-   `GET /api/products/{id}/stats`: aggregate dashboard statistics.
-   `WS /ws/progress/{product_id}`: WebSocket for real-time scraping progress updates.
-   `GET /reports/export`: Generate PDF/CSV reports.

## 5. Setup for Developers

1.  **Clone Repo**: `git clone <repo_url>`
2.  **Backend**:
    ```bash
    cd backend
    python -m venv .venv
    .venv\Scripts\activate  # Windows
    pip install -r requirements.txt
    python -m spacy download en_core_web_sm
    ```
3.  **Environment Variables**:
    Create `.env` in `backend/`:
    ```env
    suppose_url=YOUR_SUPABASE_URL
    suppose_key=YOUR_SUPABASE_KEY
    YOUTUBE_API_KEY=optional
    REDDIT_CLIENT_ID=optional
    ```
4.  **Run Server**:
    ```bash
    python -m uvicorn main:app --reload
    ```

## 6. AI Pipeline Details

The implementation handles tasks asynchronously:
1.  **Ingestion**: Scrapers fetch raw text.
2.  **Preprocessing**: Cleaning (regex), deduplication (hashing).
3.  **Analysis (Async)**:
    -   **Sentiment**: Batched interference using `distilbert-base-uncased-finetuned-sst-2-english`.
    -   **Aspect Extraction**: Spacy dependency parsing to find Noun-Adjective pairs.
    -   **Topic Modeling**: LDA (Latent Dirichlet Allocation) on batched documents.
4.  **Storage**: Results are saved to Supabase with relational integrity.

For more details, refer to `backend/services/ai_service.py`.
