# Sentiment Beacon — User Manual

**Version:** 1.0.0  
**Author:** Sooraj S

---

## Table of Contents

- [Introduction](#introduction)
- [Getting Started](#getting-started)
- [Dashboard Overview](#dashboard-overview)
- [Managing Products](#managing-products)
- [Triggering a Live Analysis](#triggering-a-live-analysis)
- [Analytics Page](#analytics-page)
- [Competitor Intelligence (War Room)](#competitor-intelligence-war-room)
- [Reports](#reports)
- [Alerts](#alerts)
- [Settings and Integrations](#settings-and-integrations)
- [Troubleshooting](#troubleshooting)

---

## Introduction

**Sentiment Beacon** is a real-time sentiment intelligence platform designed for marketing teams, product managers, and brand analysts. It continuously monitors customer opinions across YouTube, Reddit, and Twitter/X, applies advanced AI analysis, and presents the results through an interactive, easy-to-navigate dashboard.

This manual covers all features available in the application and is intended for end users who do not require knowledge of the underlying technical implementation.

---

## Getting Started

### Accessing the Application

Open your web browser and navigate to the application URL provided by your administrator. For local development environments, the default address is `http://localhost:5173`.

### Logging In

1. On the login page, enter your registered **email address** and **password**.
2. Click **Sign In**.
3. If you do not have an account, click **Create an account** and complete the registration form.

---

## Dashboard Overview

The main dashboard is the default landing page after login. It provides a consolidated view of sentiment data across all tracked products.

### Metric Cards

The four headline stat cards at the top of the page give an at-a-glance summary:

| Card | Description |
| :--- | :--- |
| **Total Reviews** | Total number of comments and reviews collected across all platforms |
| **Sentiment Score** | Aggregate score from 0–100. Above 75 is Excellent; below 40 requires attention |
| **Credibility Score** | Data quality index; filters out spam, bots, and low-quality submissions |
| **Active Platforms** | Indicates which scrapers (YouTube, Reddit, Twitter) are currently enabled |

### Sentiment Trend Chart

Displays how positive and negative sentiment has changed over time. Use the date range filter to zoom in on specific periods, such as a product launch window or a news event.

### Emotion Wheel

A radar chart showing the distribution of eight primary emotions detected across all reviews — Joy, Anger, Sadness, Trust, Fear, Disgust, Anticipation, and Surprise. This provides deeper context beyond simple positive/negative scoring.

### Word Cloud

Visualises the most frequently mentioned terms in customer reviews. Larger words appear more often. The word cloud updates automatically after each scraping cycle.

### Topic Clusters

Groups related discussion themes extracted via AI topic modeling (LDA). Each cluster represents a recurring subject in the review data, such as "battery life" or "customer support".

### Aspect Radar Chart

Breaks down sentiment by product aspect (e.g., Price, Quality, Delivery, Support). This makes it easy to pinpoint which specific attributes customers are satisfied or dissatisfied with.

### Review Feed

A real-time, paginated feed of all ingested reviews. Each entry shows the source platform, review text, sentiment label, and publication date. Use the filter controls to narrow results by platform, sentiment, or date.

### Platform Breakdown Chart

A visual representation of the proportion of reviews coming from each integrated platform. Useful for understanding where your customers are most active.

### Credibility Report

Highlights reviews that have been flagged as potentially inauthentic. Low-credibility entries are weighted down in the overall sentiment calculations to ensure the scores reflect genuine customer opinion.

---

## Managing Products

### Adding a Product

1. Click **Add Product** in the top navigation or sidebar.
2. Enter the **Product Name** (e.g., "Samsung Galaxy S25").
3. Enter **Keywords** to guide the scrapers — include the product name, common abbreviations, and known pain points (e.g., "battery", "overheating").
4. Toggle the **Platform Tracking** switches to enable or disable specific channels.
5. Click **Create Product**.

The system will immediately begin its first data collection cycle.

### Selecting a Product

Use the **Product Selector** dropdown at the top of the dashboard to filter all charts and metrics to a single product, or leave it on the global view to see aggregated data across all products.

### Deleting a Product

Navigate to the **Products** page, locate the product, and click **Delete**. This action permanently removes the product and all associated review data. This action cannot be undone.

---

## Triggering a Live Analysis

To fetch the latest data from social platforms on demand:

1. Select the target product from the product selector.
2. Click the **Run Live Analysis** or **Refresh Data** button.
3. A progress notification will confirm that data collection has started.
4. The dashboard will automatically refresh once analysis is complete — typically within 30–90 seconds depending on review volume.

> **Note:** YouTube data is typically retrieved fastest. Reddit and Twitter results may take slightly longer depending on API rate limits.

---

## Analytics Page

The **Analytics** page provides deeper insights beyond the main dashboard.

- **Predictive Trend Forecast** — An AI-generated 7-day projection of where sentiment is likely to move based on historical trends.
- **Executive Summary** — A plain-language narrative generated by the AI that summarises the current state of customer opinion.
- **Comparative Bar Charts** — Side-by-side comparison of sentiment volume over custom time periods.
- **Word Cloud Panel** — Product-specific keyword frequency visualisation.

---

## Competitor Intelligence (War Room)

The **Competitors** page allows you to compare two products head-to-head across all sentiment dimensions.

### Running a Comparison

1. Navigate to **Competitors** in the sidebar.
2. Select **Product A** and **Product B** from the respective dropdowns.
3. The comparison charts will populate automatically.

### Interpreting the Results

| Chart | What It Shows |
| :--- | :--- |
| **Radar Chart** | Relative strength across aspects such as Quality, Price, and Support |
| **Bar Chart** | Positive, Negative, and Neutral review volumes side by side |
| **Metrics Table** | Direct numerical comparison of sentiment score, credibility, and review count |

---

## Reports

### Generating a Report

1. Navigate to **Reports** in the sidebar.
2. Select the **Product** you want to report on.
3. Choose a **format**: PDF (for presentations) or CSV (for further data analysis).
4. Click **Generate Report**.
5. The report will appear in the reports list when ready. Click **Download** to save it.

### Report Contents

- **Executive Summary** — An AI-authored narrative overview of the sentiment landscape.
- **Sentiment Breakdown** — Counts and percentages for positive, negative, and neutral reviews.
- **Top Aspects** — Ranked list of the most-discussed product attributes and their sentiment scores.
- **Emotion Analysis** — Distribution of all detected emotions.
- **Platform Breakdown** — Review counts segmented by source platform.

---

## Alerts

Alerts notify you when a tracked metric crosses a defined threshold.

### Creating an Alert

1. Navigate to **Alerts** in the sidebar.
2. Click **New Alert**.
3. Select the **Metric** to monitor (e.g., Sentiment Score).
4. Set the **Condition** (e.g., "drops below 50").
5. Click **Save**.

When the condition is triggered, a notification will appear in the application's notification panel.

---

## Settings and Integrations

### Platform Integrations

Navigate to **Integrations** to manage API credentials for each social platform:

| Platform | Credential Required |
| :--- | :--- |
| YouTube | Google YouTube Data API v3 key |
| Reddit | Reddit app Client ID and Client Secret |
| Twitter/X | Twitter/X API v2 Bearer Token |

Enter the credentials and click **Save**. Integrations without valid credentials are automatically disabled and will not affect the rest of the application.

### Application Settings

The **Settings** page allows you to:
- Update your email address and password
- Configure notification preferences
- Toggle the application theme (Dark / Light)

---

## Troubleshooting

### The Sentiment Score shows 0

The scraping cycle may not have completed yet, or no reviews were found matching the product keywords. Try broadening the keywords or waiting for the next scheduled collection cycle. Click **Run Live Analysis** to trigger an immediate refresh.

### Reddit or Twitter data is missing

These platforms require API credentials configured in the **Integrations** page. If credentials are not present or have expired, the corresponding scraper is automatically disabled. Contact your administrator to verify the API keys are valid and correctly set.

### The dashboard is not updating after a live analysis

Perform a hard page refresh (`Ctrl + F5` on Windows / `Cmd + Shift + R` on macOS). Ensure that the backend service is running. If you are on the hosted version, check the service status page.

### Data appears stale

Scheduled background jobs refresh data automatically every few hours. For immediate updates, use **Run Live Analysis**. If scheduled jobs have stopped, contact your administrator to restart the backend service.

---

*For deployment and infrastructure guidance, see [DEPLOYMENT_GUIDE.md](DEPLOYMENT_GUIDE.md).*  
*For technical implementation details, see [TECHNICAL_GUIDE.md](TECHNICAL_GUIDE.md).*
