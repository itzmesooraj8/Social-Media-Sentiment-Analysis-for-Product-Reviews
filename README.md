# Sentiment Beacon 🎯

**Real-time Social Media Sentiment Analysis for Product Reviews**

A powerful, AI-driven sentiment analysis platform that monitors and analyzes product reviews across multiple social media platforms in real-time. Built with React, TypeScript, FastAPI, and Supabase.

![License](https://img.shields.io/badge/license-MIT-blue.svg)
![React](https://img.shields.io/badge/React-18.3-61DAFB?logo=react)
![TypeScript](https://img.shields.io/badge/TypeScript-5.8-3178C6?logo=typescript)
![FastAPI](https://img.shields.io/badge/FastAPI-0.115-009688?logo=fastapi)

---

## 🚀 Key Differentiators (Why this Project Wins)

Unlike standard sentiment analyzers, this platform features:

1.  **⚡ Real-Time Ingestion Engine:**
    - Live scraping of YouTube & Reddit via direct URL.
    - Zero-latency analysis using `AsyncIO` and FastAPI.

2.  **🛡️ "Credibility" & Bot Detection:**
    - Proprietary algorithm to filter out spam, bots, and duplicate reviews before analysis.
    - Ensures insights are based on *real* human feedback.

3.  **⚔️ Competitor War Room:**
    - Head-to-head Aspect-Based Sentiment Analysis (ABSA).
    - Visualizes gaps in specific features (Battery, Price, Service) using Radar Charts.

4.  **🚨 Automated Crisis Monitoring:**
    - Background workers scan for PR threats (keywords: "fire", "scam", "lawsuit").
    - instant Alerts system for high-severity negative spikes.

## ✨ Features

### 🎨 **Beautiful Modern UI**
- Glassmorphism design with smooth animations
- Dark mode support
- Fully responsive layout
- Real-time data visualization with Recharts

### 🤖 **AI-Powered Analysis**
- **Sentiment Detection**: Positive, Negative, Neutral classification
- **Emotion Analysis**: Joy, Anger, Fear, Surprise, Trust, Anticipation
- **Credibility Scoring**: Detect fake reviews and bot patterns
- **Aspect-Based Analysis**: Quality, Price, Service, Shipping insights
- **Keyword Extraction**: Identify trending topics and phrases

### 📊 **Comprehensive Dashboard**
- Live review analyzer with instant feedback
- Sentiment trend charts (30-day history)
- Platform breakdown (Twitter, Reddit, YouTube, Forums)
- Emotion wheel visualization
- Credibility reports with bot detection
- Real-time alerts for sentiment shifts

### 🔧 **Product Management**
- Add and track multiple products
- SKU-based organization
- Category management
- Keyword tracking
- Platform-specific monitoring

### 📈 **Advanced Analytics**
- Year-over-year comparisons
- Hourly engagement patterns
- Sentiment vs. Engagement correlation
- Platform performance metrics
- Custom date range filtering

---

## 🚀 Quick Start

### Prerequisites

- **Node.js** 18+ and npm
- **Python** 3.9+
- **Supabase** account (free tier works)
- **HuggingFace** account (free)

### 1. Clone the Repository

\`\`\`bash
git clone https://github.com/itzmesooraj8/Social-Media-Sentiment-Analysis-for-Product-Reviews.git
cd sentiment-beacon-main
\`\`\`

### 2. Set Up Environment Variables

Create a \`.env\` file in the root directory:

\`\`\`env
# Backend Environment Variables
SUPABASE_URL=your_supabase_url_here
SUPABASE_KEY=your_supabase_anon_key_here
SUPABASE_SERVICE_ROLE_KEY=your_service_role_key_here
HF_TOKEN=your_huggingface_token_here
YOUTUBE_API_KEY=your_youtube_api_key_here

# Frontend Environment Variables (VITE_ prefix required)
VITE_SUPABASE_URL=your_supabase_url_here
VITE_SUPABASE_KEY=your_supabase_anon_key_here
VITE_API_URL=http://localhost:8000
\`\`\`

**Get Your API Keys:**
- **Supabase**: [supabase.com](https://supabase.com) → Create Project → Settings → API
- **HuggingFace**: [huggingface.co](https://huggingface.co) → Settings → Access Tokens
- **YouTube** (optional): [Google Cloud Console](https://console.cloud.google.com) → Enable YouTube Data API v3

### 3. Set Up Database

1. Go to your Supabase project
2. Navigate to **SQL Editor**
3. Copy and paste the contents of `backend/schema.sql`
4. Click **Run** to create all tables and seed data

### 4. Install Dependencies

**Frontend:**
\`\`\`bash
npm install
\`\`\`

**Backend:**
\`\`\`bash
cd backend
pip install -r requirements.txt
cd ..
\`\`\`

### 5. Run the Application

**Terminal 1 - Backend API:**
\`\`\`bash
cd backend
python main.py
\`\`\`
Backend will run on `http://localhost:8000`

**Terminal 2 - Frontend:**
\`\`\`bash
npm run dev
\`\`\`
Frontend will run on `http://localhost:5173`

### 6. Access the Application

Open your browser and navigate to:
- **Frontend**: http://localhost:5173
- **API Docs**: http://localhost:8000/docs (Swagger UI)
- **Health Check**: http://localhost:8000/health

---

## 📁 Project Structure

\`\`\`
sentiment-beacon-main/
├── backend/
│   ├── services/
│   │   └── ai_service.py          # AI sentiment analysis service
│   ├── database.py                 # Supabase database client
│   ├── main.py                     # FastAPI server
│   ├── schema.sql                  # Database schema
│   ├── seed_keys.py                # API key seeding script
│   └── requirements.txt            # Python dependencies
├── src/
│   ├── components/
│   │   ├── dashboard/              # Dashboard components
│   │   ├── layout/                 # Layout components
│   │   └── ui/                     # shadcn-ui components
│   ├── hooks/
│   │   └── useDashboardData.ts     # Data fetching hooks
│   ├── lib/
│   │   ├── api.ts                  # API client
│   │   ├── mockData.ts             # Mock data generators
│   │   └── utils.ts                # Utility functions
│   ├── pages/
│   │   ├── Index.tsx               # Dashboard page
│   │   ├── Analytics.tsx           # Analytics page
│   │   ├── Products.tsx            # Products management
│   │   ├── Reports.tsx             # Reports page
│   │   ├── Alerts.tsx              # Alerts page
│   │   ├── Settings.tsx            # Settings page
│   │   ├── Integrations.tsx        # API integrations
│   │   └── Help.tsx                # Help & documentation
│   ├── types/
│   │   └── sentinel.ts             # TypeScript type definitions
│   └── App.tsx                     # Main app component
├── .env                            # Environment variables
├── package.json                    # Node dependencies
├── vite.config.ts                  # Vite configuration
└── README.md                       # This file
\`\`\`

---

## 🔌 API Endpoints

### Sentiment Analysis
- `POST /api/analyze` - Analyze sentiment of text
  \`\`\`json
  {
    "text": "This product is amazing! Great quality."
  }
  \`\`\`

### Products
- `GET /api/products` - List all products
- `POST /api/products` - Create new product
- `DELETE /api/products/{id}` - Delete product

### Reviews
- `GET /api/reviews` - List reviews (optional: ?product_id=xxx)
- `POST /api/reviews` - Create review with auto-analysis

### Dashboard
- `GET /api/dashboard` - Get dashboard metrics and data

### Analytics
- `GET /api/analytics` - Get analytics data

### Health
- `GET /health` - Health check endpoint

**Full API Documentation**: http://localhost:8000/docs

---

## 🗄️ Database Schema

### Tables

**products**
- Product information (name, SKU, category, keywords)
- Status tracking (active, paused, archived)

**reviews**
- Review text and metadata
- Platform and source URL
- Linked to products

**sentiment_analysis**
- Sentiment labels (POSITIVE, NEGATIVE, NEUTRAL)
- Confidence scores
- Emotions (JSONB)
- Credibility scores
- Aspect analysis (JSONB)

**integrations**
- API keys storage
- Platform configurations

**alerts**
- Real-time alerts
- Severity levels
- Alert types (bot_detected, spam_cluster, etc.)

---

## 🎯 Usage Guide

### 1. Add a Product

1. Navigate to **Products** page
2. Click **Add Product**
3. Fill in product details:
   - Name
   - SKU (unique identifier)
   - Category
   - Description
   - Keywords to track
4. Click **Add Product**

### 2. Analyze Reviews

**Option A: Live Analyzer (Manual)**
1. Go to **Dashboard**
2. Find the **Live Review Analyzer** card
3. Paste any review text
4. Click **Analyze Sentiment**
5. View instant results with emotions and credibility

**Option B: API Integration (Automated)**
\`\`\`bash
curl -X POST http://localhost:8000/api/reviews \\
  -H "Content-Type: application/json" \\
  -d '{
    "product_id": "your-product-id",
    "text": "Great product, highly recommend!",
    "platform": "twitter"
  }'
\`\`\`

### 3. View Analytics

- **Dashboard**: Real-time metrics and trends
- **Analytics**: Deep dive with advanced charts
- **Reports**: Exportable reports (PDF, CSV)
- **Alerts**: Monitor for unusual patterns

---

## 🔧 Configuration

### AI Models

The system uses HuggingFace Inference API with these models:

- **Sentiment**: `cardiffnlp/twitter-xlm-roberta-base-sentiment`
- **Emotions**: `j-hartmann/emotion-english-distilroberta-base`

You can customize models in `backend/services/ai_service.py`

### Database Policies

Row Level Security (RLS) is enabled. Current policies allow public access for development. For production:

1. Enable authentication
2. Update RLS policies in Supabase
3. Add user management

---

## 🚢 Deployment

### Frontend (Vercel/Netlify)

\`\`\`bash
npm run build
\`\`\`

Deploy the `dist` folder. Set environment variables in your hosting platform.

### Backend (Railway/Render/Heroku)

1. Create new service
2. Connect GitHub repository
3. Set environment variables
4. Deploy from `backend/main.py`

**Important**: Update `VITE_API_URL` in frontend to your deployed backend URL.

---

## 🤝 Contributing

Contributions are welcome! Please feel free to submit a Pull Request.

1. Fork the repository
2. Create your feature branch (`git checkout -b feature/AmazingFeature`)
3. Commit your changes (`git commit -m 'Add some AmazingFeature'`)
4. Push to the branch (`git push origin feature/AmazingFeature`)
5. Open a Pull Request

---

## 📝 License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

---

## 🙏 Acknowledgments

- **shadcn/ui** for beautiful UI components
- **HuggingFace** for AI models
- **Supabase** for database and backend
- **Recharts** for data visualization
- **Framer Motion** for animations

---

## 📧 Support

For issues, questions, or suggestions:
- **GitHub Issues**: [Create an issue](https://github.com/itzmesooraj8/Social-Media-Sentiment-Analysis-for-Product-Reviews/issues)
- **Email**: your-email@example.com

---

## 🎓 Learn More

- [FastAPI Documentation](https://fastapi.tiangolo.com/)
- [React Documentation](https://react.dev/)
- [Supabase Documentation](https://supabase.com/docs)
- [HuggingFace Models](https://huggingface.co/models)

---

**Built with ❤️ for better product insights**
