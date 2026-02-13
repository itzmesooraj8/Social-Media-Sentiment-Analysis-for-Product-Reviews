# User Manual: Real-Time Sentiment Analysis Dashboard

Welcome to the **Real-Time Sentiment Analysis** platform! This tool helps marketing and product teams understand customer perceptions across social media platforms like YouTube, Reddit, and Twitter.

## 1. Getting Started

### Access the Dashboard
Open your web browser and navigate to:
-   **URL**: `http://localhost:5173` (Local Development)

### Add a Product
1.  Click the **"Add Product"** button in the top-right corner.
2.  Enter the **Product Name** (e.g., "iPhone 15 Pro").
3.  Add relevant **Keywords** (e.g., "camera", "battery life", "overheating").
4.  Toggle **Platform Tracking** (YouTube/Reddit/Twitter) as needed.
5.  Click **Create Product**.

---

## 2. Dashboard Features

### The Overview Page
The main "Stat Cards" provide a snapshot of the current sentiment:
-   **Total Reviews**: Number of comments/reviews scraped.
-   **Sentiment Score (0-100)**: Higher is better. >75 is Excellent, <40 is Critical.
-   **Credibility Score**: Indicates data quality (filters out spam/bots).
-   **Active Platforms**: Status of active scrapers.

### Sentiment Trends Chart
Visualizes sentiment over time:
-   **Green Line**: Postive sentiment trend.
-   **Red Line**: Negative sentiment trend.
-   **Blue Bar**: Total review volume per day.

### Word Cloud
Displays frequent terms found in reviews. Larger words appear more often. Click on a word (if interactive) to drill down.

### Real-Time Alerts
Top-right bell icon. Notifies you of:
-   Sudden drops in sentiment score.
-   Completion of scraping tasks (e.g., "YouTube Scrape Finished").

---

## 3. Real-Time Scraping

### Watching the Progress
When you add a product or click "Refresh Data":
1.  A **Progress Bar** appears at the bottom or top of the dashboard.
2.  Status messages update in real-time:
    -   *Initializing Scrapers...*
    -   *Fetching Comments form YouTube (25/100)...*
    -   *Analyzing Sentiment (AI Model Running)...*
    -   *Completed Successfully!*

**Note**: YouTube scraping is fastest. Reddit may take longer due to API rate limits (proxies handle this automatically).

---

## 4. Reports & Exporting

### Generate a Report
1.  Navigate to the **"Reports"** tab in the sidebar.
2.  Select your **Product** from the dropdown.
3.  Choose a **Format**:
    -   **PDF**: Best for presentations/management. Include charts and summaries.
    -   **Excel**: Best for raw data analysis.
4.  Click **"Generate Report"**.

### Understanding Report Data
-   **Executive Summary**: AI-generated overview ("Generally positive, but users complain about battery life").
-   **Top Aspects**: Breakdown of specific features (e.g., "Camera: 90% Positive", "Price: 40% Negative").
-   **Emotion Analysis**: Distribution of emotions like "Joy", "Anger", "Surprise".

---

## 5. Troubleshooting (FAQ)

### Q: Why is the "Sentiment Score" 0?
**A**: Ensure scrapers have finished running. If no reviews are found for your keywords, the score defaults to 0. Try adding broader keywords.

### Q: Why are Reddit results missing?
**A**: Reddit scraping requires API keys or proxy configuration. Check with your technical administrator if these are set in the `.env` file.

### Q: The dashboard is not updating.
**A**: Hard refresh the page (`Ctrl + F5`). Ensure the backend server is running in the terminal.

---

**Need Technical Support?**
Contact the developer team or refer to the `TECHNICAL_GUIDE.md` for system details.
