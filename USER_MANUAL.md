# User Manual

**Project:** Social Media Sentiment Analysis for Product Reviews

## 1. Introduction
Sentiment Beacon is a real-time analytics platform that helps you understand customer perception across social media.

## 2. For Business Users (Marketing & Product Managers)

### **The Dashboard**
- **Overview**: Immediately see the "Sentiment Score" (0-100%). A score > 60% is generally positive.
- **Crisis Mode**: If sentiment drops rapidly, the interface will shift to "Crisis Mode" (red accents). Check the "Alerts" panel immediately.

### **The "War Room" (Competitor Analysis)**
1.  Navigate to the **War Room** tab.
2.  Select your product and a competitor's product.
3.  **Radar Chart**: Compare strengths. If your "Price" score is lower but "Quality" is higher, consider marketing on value-for-money.

### **Generating Reports**
1.  Go to the **Reports** page.
2.  Click **"Generate Deep Analysis PDF"**.
3.  Wait 5-10 seconds for the AI to process recent reviews, detect bot activity, and summarize topics.
4.  Download the PDF for your stakeholder meeting.

## 3. For Technical Users (Developers & Analysts)

### **Adding a New Product**
1.  Go to **Settings** > **Products**.
2.  Enter the Product Name.
3.  (Important) Enter precise **Keywords**. The scraper matches these in tweets and comments.
    -   *Good*: "iPhone 15 Pro", "iPhone 15 overheating"
    -   *Bad*: "iPhone", "phone"
4.  Toggle the platforms you want to track.

### **Manually Triggering a Scrape**
If you need immediate data:
-   Go to **Dashboard**.
-   Click the **"Scrape Now"** button (Lightning icon).
-   *Note*: This runs in the background. Results typically appear in 30-60 seconds.

### **Retraining the Model**
If the sentiment accuracy feels off:
1.  Ensure you have collected at least 100 new verified reviews.
2.  Run the training script (requires backend access):
    ```bash
    python backend/ml/train_transformer.py
    ```
3.  Reliability metrics will be logged to `backend.log`.

## 4. Troubleshooting

**"Configuration Missing" Alert**
-   This means the backend cannot find API keys for Twitter, Reddit, or YouTube.
-   **Fix**: Go to **Settings** > **Integrations** and enter your API keys.

**"No Data Available"**
-   Ensure you have added Keywords for the product.
-   Check if the platform (e.g., Reddit) is down or rate-limiting requests.
