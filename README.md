# Social Media Sentiment Analysis for Product Reviews

## Project Overview
This project is a comprehensive **Real-Time Sentiment Analysis System** designed to scrape, analyze, and visualize customer feedback from multiple social platforms (Twitter, Reddit, YouTube) using advanced NLP (BERT, LDA).

## Key Features
- **Real-Time Scraping**: Live data collection from YouTube, Reddit, and Twitter.
- **Advanced NLP**: 
  - Sentiment Classification (DistilBERT)
  - Emotion Detection (Joy, Anger, Trust, etc.)
  - Topic Modeling (LDA)
  - Keyword Extraction (TF-IDF/KeyBERT)
- **Interactive Dashboard**: React-based UI with real-time charts, predictive trends, and "War Room" competitor analysis.
- **Reporting**: PDF and CSV export capabilities.

## Technical Stack
- **Frontend**: React, TypeScript, TailwindCSS, Recharts.
- **Backend**: FastAPI, Python 3.9+.
- **Database**: Supabase (PostgreSQL).
- **AI/ML**: Hugging Face Transformers, PyTorch, Scikit-learn, Gensim.

## Quick Start Guide

### Prerequisites
- Node.js 18+
- Python 3.9+
- Supabase Account
- (Optional) Twitter/Reddit API Keys

### Installation

1.  **Clone the Repository**
    ```bash
    git clone https://github.com/your-repo/sentiment-beacon.git
    cd sentiment-beacon
    ```

2.  **Backend Setup**
    ```bash
    cd backend
    python -m venv venv
    # Windows
    venv\Scripts\activate
    # Linux/Mac
    # source venv/bin/activate
    
    pip install -r requirements.txt
    ```

3.  **Frontend Setup**
    ```bash
    cd ../
    npm install
    ```

4.  **Environment Configuration**
    - Create a `.env` file in `backend/` and `root` based on the example.
    - Add your `SUPABASE_URL` and `SUPABASE_KEY`.
    - Add optional scraper keys (`REDDIT_CLIENT_ID`, `YOUTUBE_API_KEY`, etc.).

5.  **Running the App**
    - **Backend**:
      ```bash
      # In backend/ directory
      python -m uvicorn main:app --reload --port 8000
      ```
    - **Frontend**:
      ```bash
      # In root directory
      npm run dev
      ```
    - Access dashboard at `http://localhost:5173`.

## Model Training (Advanced)
To fine-tune the sentiment model on your own dataset:
```bash
python backend/scripts/train_model.py
```
This script demonstrates the training loop using Hugging Face Trainer API.

## Project Structure
- `src/`: Frontend React application.
- `backend/`: FastAPI server and services.
  - `services/`: Core logic for AI, scrapers, and pipeline.
  - `routers/`: API endpoints.
  - `scripts/`: Utility scripts (e.g., model training).

## Credits
Built for **Advanced Agentic Coding** - Google DeepMind.