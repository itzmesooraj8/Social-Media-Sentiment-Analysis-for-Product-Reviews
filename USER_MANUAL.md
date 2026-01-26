# User Manual & Implementation Guide

## 1. Introduction
Welcome to the Sentiment Beacon dashboard. This tool helps marketing teams and product managers understand real-time customer sentiment.

## 2. Navigating the Dashboard

### 2.1 Main Dashboard
- **Live Feed**: Shows the most recent reviews streaming in from connected sources.
- **Sentiment Word Cloud**: Visualizes the most common positive (green) and negative (red) terms.
- **Trend Chart**: A line graph showing sentiment evolution over the last 7 or 30 days.

### 2.2 Products Page
- **Add Product**: Click the "+" button to track a new product.
- **Scrape Actions**: Click the generic "Actions" menu on a product card to manually trigger a **YouTube** or **Reddit** scrape.
- **Deep Analysis**: Click a product card to enter the detailed product view.

### 2.3 Analytics Page
- **Predictive AI**: See a 7-day forecast of sentiment trends.
- **Visualizations**: Access deep-dive charts like specific attribute analysis (Price vs Quality vs Shipping).

## 3. Configuration & Roles

### 3.1 User Roles
- **Admins**: Can configure API keys in the `.env` file for Twitter/Reddit access.
- **Analysts**: Can view dashboards, export reports, and compare competitors.
- **Viewers**: Read-only access to dashboards (future implementation via Supabase RLS).

### 3.2 Setting Up Data Sources
- **YouTube**: Requires `YOUTUBE_API_KEY` in `.env`.
- **Reddit**: Requires `REDDIT_CLIENT_ID` and `SECRET`.
- **Twitter**: Requires Bearer Token. *Note: Wireless fallback to "Nitter" (no-code scraping) is enabled if keys are missing.*

## 4. Troubleshooting

| Issue | Solution |
|-------|----------|
| **No Data Showing** | Check if backend is running on port 8000. Ensure you have triggered a scrape. |
| **Login Failed** | Verify Supabase credentials in `.env`. |
| **Pending Scrape** | Scrapes are background tasks. Check the backend terminal logs for "Scraper started". |

## 5. Exporting Reports
1. Navigate to the **"Reports"** tab.
2. Select your date range.
3. Click **"Download PDF"** for a management-ready summary.
