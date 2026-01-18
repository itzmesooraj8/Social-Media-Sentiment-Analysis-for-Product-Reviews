"""
AIService

Provides a cached `analyze_text(text)` function that returns a dict:
  { label: "POSITIVE", score: 0.98, emotion: "joy", credibility: 0.12 }

Credibility: simple heuristic based on text length and duplication in DB.
"""

from functools import lru_cache
from typing import Dict
import os

try:
    from transformers import pipeline
    _TRANSFORMERS_AVAILABLE = True
except Exception:
    _TRANSFORMERS_AVAILABLE = False

from database import supabase


class AIService:
    def __init__(self, model_name: str = "distilbert-base-uncased-finetuned-sst-2-english"):
        self.model_name = model_name
        self._pipe = None
        if _TRANSFORMERS_AVAILABLE:
            try:
                self._pipe = pipeline("sentiment-analysis", model=self.model_name)
            except Exception as e:
                print(f"Warning: transformers pipeline init failed: {e}")

    def _normalize_label(self, raw_label: str) -> str:
        lbl = (raw_label or "").upper()
        if lbl in ("POSITIVE", "NEGATIVE"):
            return lbl
        if lbl.endswith("_0"):
            return "NEGATIVE"
        if lbl.endswith("_1"):
            return "POSITIVE"
        return "NEUTRAL"

    def _compute_credibility(self, text: str) -> float:
        """Simple credibility heuristic:
        - Very short texts (<10) -> low
        - Duplicate content already in DB -> low
        - Longer texts -> higher
        Returns value between 0.0 and 1.0
        """
        try:
            length = len(text.strip())
            if length < 10:
                base = 0.15
            elif length < 50:
                base = 0.45
            else:
                base = 0.75

            # Duplicate check
            try:
                q = supabase.table("reviews").select("id").eq("content", text).limit(1).execute()
                if q.data:
                    # duplicate -> low credibility
                    return 0.1
            except Exception:
                # ignore DB errors
                pass

            return float(min(1.0, max(0.0, base)))
        except Exception:
            return 0.5

    @lru_cache(maxsize=2048)
    def analyze_text(self, text: str) -> Dict[str, any]:
        """Synchronous analyze. Cached to avoid repeated work.

        Returns: { label, score, emotion, credibility }
        """
        if not text or not text.strip():
            return {"label": "NEUTRAL", "score": 0.5, "emotion": "neutral", "credibility": 0.1}

        # Try transformers pipeline first
        try:
            if self._pipe:
                out = self._pipe(text[:512])
                if isinstance(out, list) and out:
                    top = out[0]
                    label = self._normalize_label(top.get("label"))
                    score = float(top.get("score", 0.5))
                    emotion = "joy" if label == "POSITIVE" else ("anger" if label == "NEGATIVE" else "neutral")
                    credibility = self._compute_credibility(text)
                    return {"label": label, "score": round(score, 4), "emotion": emotion, "credibility": round(credibility, 3)}
        except Exception as e:
            print(f"AI pipeline error: {e}")

        # Heuristic fallback
        text_l = text.lower()
        pos = any(w in text_l for w in ["good", "great", "love", "excellent", "best", "awesome"])
        neg = any(w in text_l for w in ["bad", "terrible", "worst", "hate", "awful", "broken"])
        if pos and not neg:
            label = "POSITIVE"
            score = 0.65
            emotion = "joy"
        elif neg and not pos:
            label = "NEGATIVE"
            score = 0.65
            emotion = "anger"
        else:
            label = "NEUTRAL"
            score = 0.5
            emotion = "neutral"

        credibility = self._compute_credibility(text)
        return {"label": label, "score": round(score, 4), "emotion": emotion, "credibility": round(credibility, 3)}


ai_service = AIService()


            score = review.get("score") or review.get("sentiment_score")
            # If nested under 'analysis'
            if score is None and review.get("analysis"):
                score = review["analysis"].get("score")

        try:
            score = float(score) if score is not None else None
        except Exception:
            score = None

        if score is None:
            # Try to compute sentiment on review text if present
            text = review.get("text") or review.get("review_text") if isinstance(review, dict) else None
            if text:
                try:
                    analysis = await self.analyze_sentiment(text)
                    score = float(analysis.get("score") or 0.0)
                except Exception:
                    score = None

        if score is None:
            return None

        # Trigger alert when sentiment < 0.3
        if score < 0.3:
            alert_payload = {
                "type": "sentiment_drop",
                "severity": "high" if score < 0.15 else "medium",
                "title": "Negative sentiment detected",
                "message": review.get("text") or review.get("review_text") or "",
                "platform": review.get("platform") if isinstance(review, dict) else None,
                "is_read": False
            }
            if supabase:
                try:
                    supabase.table("alerts").insert(alert_payload).execute()
                except Exception as e:
                    print(f"Failed to insert alert: {e}")
            return alert_payload

        return None

    async def predict_trend(self, history: List[Dict[str, Any]]) -> Dict[str, Any]:
        """
        Predict future sentiment using Linear Regression on historical data.
        history: [{'date': '2025-10-01', 'sentiment_score': 0.8}, ...]
        """
        if len(history) < 3:
            return {"trend": "insufficient_data", "forecast": []}

        try:
            # Prepare data
            sorted_hist = sorted(history, key=lambda x: x['date'])
            dates = [datetime.fromisoformat(x['date']).timestamp() for x in sorted_hist]
            scores = [x['sentiment_score'] for x in sorted_hist]

            X = np.array(dates).reshape(-1, 1)
            y = np.array(scores)

            # Train simple Linear Regression
            from sklearn.linear_model import LinearRegression
            model = LinearRegression()
            model.fit(X, y)

            # Forecast next 7 days
            last_date = datetime.fromisoformat(sorted_hist[-1]['date'])
            forecast = []
            current_slope = model.coef_[0] # Positive = Upward trend, Negative = Downward

            for i in range(1, 8):
                future_date = last_date + timedelta(days=i)
                future_ts = future_date.timestamp()
                pred_score = model.predict([[future_ts]])[0]
                # Clamp score 0.0 to 1.0
                pred_score = max(0.0, min(1.0, pred_score))
                
                forecast.append({
                    "date": future_date.strftime("%Y-%m-%d"),
                    "predicted_score": round(pred_score, 2)
                })

            direction = "stable"
            if current_slope > 0.000001: direction = "improving"
            elif current_slope < -0.000001: direction = "declining"

            return {
                "trend": direction,
                "slope": current_slope,
                "forecast": forecast
            }
        except Exception as e:
            print(f"Prediction error: {e}")
            return {"trend": "error", "forecast": []}

ai_service = AIService()
