# Frontend Blank Screen - Troubleshooting Guide

## Issue
The frontend shows briefly then goes blank.

## Most Likely Causes

### 1. **Database Tables Not Created** ⚠️ **MOST COMMON**
The API is trying to query Supabase tables that don't exist yet.

**Solution**:
1. Open https://supabase.com
2. Go to SQL Editor
3. Copy ALL contents of `backend/schema.sql`
4. Paste and click **RUN**
5. Refresh the frontend

### 2. **API Connection Error**
Frontend can't reach the backend at http://localhost:8000

**Check**:
- Is backend running? Look for "Uvicorn running on http://0.0.0.0:8000"
- Test: Open http://localhost:8000/health in browser
- Should see: `{"status":"healthy",...}`

### 3. **JavaScript Error**
Check browser console (F12) for errors.

**Common errors**:
- "Failed to fetch" → Backend not running
- "Network Error" → CORS issue or backend down
- "Cannot read property" → Data structure mismatch

## Quick Fix Steps

### Step 1: Check Browser Console
1. Press **F12** in browser
2. Click **Console** tab
3. Look for red errors
4. Share the error message if you see one

### Step 2: Verify Backend is Running
```bash
# Should see "Uvicorn running on http://0.0.0.0:8000"
# In the terminal where you ran: python main.py
```

### Step 3: Test Backend Health
Open in browser: http://localhost:8000/health

Should see:
```json
{
  "status": "healthy",
  "database": "connected",
  "ai_service": "ready"
}
```

### Step 4: Run Database Schema
**This is REQUIRED before the app will work properly!**

1. Go to https://supabase.com
2. Click "SQL Editor"
3. Open `backend/schema.sql` file
4. Copy EVERYTHING
5. Paste into Supabase SQL Editor
6. Click "RUN"
7. Check "Table Editor" - should see 5 tables

### Step 5: Restart Frontend
```bash
# Stop the frontend (Ctrl+C)
# Then restart:
npm run dev
```

## Temporary Workaround

The app is designed to work with mock data if the backend fails. If you're seeing a blank screen, it means there's a JavaScript error preventing the app from loading at all.

**Check the browser console (F12) and share what error you see.**

## What Should Happen

Even without the database set up, the app should:
- ✅ Load the UI
- ✅ Show the dashboard with mock data
- ✅ Display charts and metrics (using generated data)
- ❌ Live Review Analyzer won't work (needs backend)
- ❌ Product management won't work (needs database)

## Next Steps

1. **Press F12** in your browser
2. **Click Console tab**
3. **Take a screenshot** of any red errors
4. **Share the error message**

This will help me identify the exact issue!
