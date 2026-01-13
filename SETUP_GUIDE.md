# 🚀 Quick Setup Guide

## ⚡ You're Almost Ready!

Your Sentiment Beacon project is configured and ready to run. Follow these final steps:

---

## 📋 Step 1: Set Up Supabase Database

1. **Open Supabase**: Go to [https://supabase.com](https://supabase.com) and log in
2. **Navigate to SQL Editor**: Click on "SQL Editor" in the left sidebar
3. **Run Schema**: 
   - Open the file `backend/schema.sql` in your code editor
   - Copy ALL the contents
   - Paste into Supabase SQL Editor
   - Click **RUN** button
4. **Verify**: Check that tables were created:
   - Go to "Table Editor" in Supabase
   - You should see: `products`, `reviews`, `sentiment_analysis`, `integrations`, `alerts`

---

## 🖥️ Step 2: Start the Backend Server

**Option A: Using the script (Windows)**
\`\`\`bash
cd backend
start.bat
\`\`\`

**Option B: Manual start**
\`\`\`bash
cd backend
python main.py
\`\`\`

✅ Backend should start on **http://localhost:8000**

**Test it**: Open http://localhost:8000/health in your browser
- You should see: `{"status":"healthy","database":"connected","ai_service":"ready"}`

---

## 🎨 Step 3: Start the Frontend

**In a NEW terminal window:**

\`\`\`bash
npm run dev
\`\`\`

✅ Frontend should start on **http://localhost:5173**

---

## ✨ Step 4: Test the Application

### Test 1: Live Review Analyzer

1. Open http://localhost:5173
2. Find the **"Live Review Analyzer"** card on the dashboard
3. Paste this test review:
   \`\`\`
   This product is absolutely amazing! The quality is excellent and it exceeded all my expectations. Highly recommend!
   \`\`\`
4. Click **"Analyze Sentiment"**
5. You should see:
   - Sentiment: **Positive**
   - Confidence: ~85-95%
   - Emotions: Joy, Trust, etc.
   - Credibility Score: ~80-90%

### Test 2: Add a Product

1. Click **"Products"** in the sidebar
2. Click **"Add Product"** button
3. Fill in:
   - Name: `Test Wireless Headphones`
   - SKU: `TWH-001`
   - Category: `Electronics`
   - Description: `Premium wireless headphones for testing`
4. Click **"Add Product"**
5. Product should appear in the list

### Test 3: API Health Check

Open these URLs in your browser:
- **Health**: http://localhost:8000/health
- **API Docs**: http://localhost:8000/docs (Interactive Swagger UI)
- **Products API**: http://localhost:8000/api/products

---

## 🐛 Troubleshooting

### Backend won't start

**Error: "Supabase credentials not found"**
- Check your `.env` file has the correct Supabase URL and keys
- Make sure `.env` is in the ROOT directory (not in `backend/`)

**Error: "Module not found"**
- Run: `pip install -r requirements.txt` in the `backend/` directory

**Error: "Port 8000 already in use"**
- Stop any other process using port 8000
- Or change the port in `backend/main.py` (last line)

### Frontend won't connect to backend

**Error: "Network Error" or "Failed to fetch"**
- Make sure backend is running on http://localhost:8000
- Check `.env` has `VITE_API_URL=http://localhost:8000`
- Restart frontend: `npm run dev`

**Error: "CORS policy"**
- Backend should already have CORS configured
- If still issues, check `backend/main.py` CORS settings

### Database connection issues

**Error: "database: disconnected"**
- Verify Supabase credentials in `.env`
- Check you're using the **service_role_key** for backend
- Ensure you ran the `schema.sql` in Supabase

### Live Analyzer not working

**Shows "Analysis unavailable"**
- Check backend is running
- Check HuggingFace token is valid in `.env`
- HF models may take 20-30 seconds to load on first request (be patient!)
- Check browser console for errors (F12)

---

## 📊 What's Working Now

✅ **Backend API Server** - FastAPI running on port 8000  
✅ **Database Connection** - Supabase connected  
✅ **AI Sentiment Analysis** - HuggingFace models ready  
✅ **Frontend UI** - React app with beautiful design  
✅ **Live Review Analyzer** - Real-time sentiment analysis  
✅ **Product Management** - CRUD operations  
✅ **Dashboard Metrics** - Real data from database  

---

## 🎯 Next Steps (Optional Enhancements)

### 1. Add More Sample Data

Run this in Supabase SQL Editor to add more reviews:

\`\`\`sql
-- Add more sample reviews
INSERT INTO reviews (product_id, text, platform, author) 
SELECT 
    p.id,
    'The battery life is disappointing. Only lasts 3 hours.',
    'reddit',
    'user789'
FROM products p WHERE p.sku = 'UPHW-001'
LIMIT 1;

-- Analyze them
-- You can use the API or Live Analyzer
\`\`\`

### 2. Set Up Automated Scraping

- Add web scraping scripts in `backend/scrapers/`
- Use Twitter API, Reddit API, YouTube API
- Schedule with cron jobs or background tasks

### 3. Deploy to Production

**Frontend** (Vercel):
\`\`\`bash
npm run build
# Deploy dist/ folder to Vercel
\`\`\`

**Backend** (Railway/Render):
- Push to GitHub
- Connect repository
- Set environment variables
- Deploy!

### 4. Add Authentication

- Enable Supabase Auth
- Add login/signup pages
- Update RLS policies
- Protect API endpoints

---

## 📞 Need Help?

- **Check logs**: Backend terminal shows all API requests
- **Browser Console**: Press F12 to see frontend errors
- **API Docs**: http://localhost:8000/docs for interactive testing
- **Database**: Check Supabase Table Editor for data

---

## 🎉 You're All Set!

Your Sentiment Beacon is now running with:
- ✅ Real-time AI sentiment analysis
- ✅ Beautiful modern UI
- ✅ Working database
- ✅ Full API backend

**Enjoy analyzing sentiments!** 🚀
