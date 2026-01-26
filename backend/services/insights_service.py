
from typing import List, Dict, Any
from database import supabase
from datetime import datetime, timedelta
import logging

logger = logging.getLogger(__name__)

class InsightsService:
    def generate_insights(self, product_id: str = None) -> List[str]:
        """
        Generate bullet-point insights based on recent data.
        """
        insights = []
        try:
            # 1. Fetch recent stats (last 30 days)
            days = 30
            start_date = datetime.now() - timedelta(days=days)
            
            # Base query
            query = supabase.table("reviews").select("sentiment_analysis(label, score), created_at").gte("created_at", start_date.isoformat())
            if product_id:
                query = query.eq("product_id", product_id)
            
            resp = query.execute()
            reviews = resp.data or []
            
            if not reviews:
                return ["No enough data to generate insights yet."]

            total = len(reviews)
            positive = 0
            negative = 0
            
            for r in reviews:
                sa = r.get("sentiment_analysis")
                label = "NEUTRAL"
                if isinstance(sa, list) and sa: label = sa[0].get("label")
                elif isinstance(sa, dict): label = sa.get("label")
                
                if label == "POSITIVE": positive += 1
                elif label == "NEGATIVE": negative += 1
            
            pos_pct = int((positive / total) * 100)
            neg_pct = int((negative / total) * 100)
            
            # Insight 1: Sentiment Overview
            sentiment_trend_arrow = "↑" if pos_pct > 50 else "↓"
            insights.append(f"{pos_pct}% positive reviews in the last 30 days {sentiment_trend_arrow} (based on {total} reviews).")
            
            # Insight 2: Concern Alert
            if neg_pct > 20:
                insights.append(f"⚠️ High volume of negative feedback ({neg_pct}%). Immediate attention recommended.")
            else:
                 insights.append("✅ Negative sentiment is within healthy limits.")
                 
            # Insight 3: Topic suggestions (Stub - ideally fetch from topic_analysis)
            # Fetch top topic from DB
            try:
                topic_query = supabase.table("topic_analysis").select("topic_name").order("size", desc=True).limit(1).execute()
                if topic_query.data:
                    top_topic = topic_query.data[0]["topic_name"]
                    insights.append(f"Top trending discussion topic: '{top_topic}'.")
            except:
                pass

        except Exception as e:
            logger.error(f"Insights generation failed: {e}")
            insights.append("Could not generate AI insights at this time.")
            
        return insights

insights_service = InsightsService()
