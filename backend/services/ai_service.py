try:
    import spacy
    try:
        nlp = spacy.load("en_core_web_sm")
    except OSError:
        # Fallback if model not downloaded
        nlp = None
        print("Warning: Spacy model 'en_core_web_sm' not found. Run 'python -m spacy download en_core_web_sm'")
except ImportError:
    nlp = None
    print("Warning: Spacy not installed.")

    print("Warning: Spacy not installed.")

import hashlib
import json
import httpx
import asyncio
import os
import pickle
import numpy as np
from datetime import datetime, timedelta
from typing import Dict, Any, List, Optional
from dotenv import load_dotenv
from pathlib import Path

# Load env
env_path = Path(__file__).resolve().parent.parent / ".env"
load_dotenv(dotenv_path=env_path)

HF_API_URL = "https://router.huggingface.co/models/distilbert-base-uncased-finetuned-sst-2-english"

class AIService:
    def __init__(self):
        self.api_url = HF_API_URL
        self.local_model = None
        self.model_path = Path(__file__).resolve().parent.parent / "models" / "sentiment_baseline_v1.pkl"
        self._load_local_model()

    def _load_local_model(self):
        """Load the local Sklearn pipeline for fallback inference."""
        try:
            if self.model_path.exists():
                with open(self.model_path, "rb") as f:
                    self.local_model = pickle.load(f)
                print(f"✅ Local AI Model loaded from {self.model_path}")
            else:
                print("⚠️ Local model not found. Run 'python backend/ml/train_model.py'")
        except Exception as e:
            print(f"❌ Failed to load local model: {e}")

    async def generate_executive_summary(self, reviews: List[str], product_name: str) -> str:
        """
        Generate a business executive summary using LLM.
        """
        if not reviews:
            return "Insufficient data to generate summary."
            
        # Prepare context (Text Blob)
        # Limit to 10-15 short reviews to fit in context
        joined_reviews = "\n- ".join([r[:200] for r in reviews[:15]])
        prompt = f"Summarize these reviews for {product_name} into 3 short, actionable takeaways for the product manager:\n\n{joined_reviews}\n\nSummary:"
        
        API_URL = "https://api-inference.huggingface.co/models/google/flan-t5-large"
        
        token = await self._get_api_key()
        headers = {"Authorization": f"Bearer {token}"} if token else {}
        
        async with httpx.AsyncClient() as client:
            try:
                response = await self._query_hf(client, API_URL, {
                    "inputs": prompt, 
                    "parameters": {"max_length": 150, "temperature": 0.7}
                }, headers)
                
                if isinstance(response, dict) and "error" in response:
                    return "AI Summary unavailable (Model loading or API limit)."
                    
                if isinstance(response, list) and len(response) > 0:
                    return response[0].get("generated_text", "No summary generated.")
                    
                return "Analysis complete, but summary generation failed."
            except Exception as e:
                print(f"Summary Gen Error: {e}")
                return "AI Summary service currently unavailable."

    async def _get_api_key(self) -> str:
        try:
            from database import supabase
            response = supabase.table("integrations").select("api_key").eq("platform", "huggingface").eq("active", True).limit(1).execute()
            if response.data:
                return response.data[0]["api_key"]
            return os.environ.get("HF_TOKEN", "")
        except:
            return os.environ.get("HF_TOKEN", "")
            
    def _compute_hash(self, text: str) -> str:
        return hashlib.md5(text.encode('utf-8')).hexdigest()

    async def _check_cache(self, text_hash: str) -> Dict[str, Any]:
        """Check if we have analyzed this exact text before."""
        try:
            from database import supabase
            pass
        except:
            pass
        return None

    async def analyze_sentiment(self, text: str) -> Dict[str, Any]:
        """
        Analyze sentiment using Hybrid approach (Cloud API -> Local Model -> Fallback).
        """
        if not text or not text.strip():
            return {"label": "NEUTRAL", "score": 0.5, "emotions": [], "credibility": 0}

        # 1. Cloud API (Hugging Face)
        token = os.environ.get("HF_TOKEN")
        if token:
            try:
                headers = {"Authorization": f"Bearer {token}"}
                async with httpx.AsyncClient() as client:
                    response = await client.post(self.api_url, headers=headers, json={"inputs": text[:512]})
                    if response.status_code == 200:
                        data = response.json()
                        # Process HF format [[{'label': 'POSITIVE', 'score': 0.9}]]
                        if isinstance(data, list) and len(data) > 0:
                            top = max(data[0], key=lambda x: x['score'])
                            return self._enrich_analysis(text, top['label'].upper(), top['score'])
            except Exception as e:
                print(f"⚠️ Cloud AI failed ({e}), switching to Local Model...")

        # 2. Local Model (Fallback)
        if self.local_model:
            try:
                # Predict returns ['positive'] or ['negative']
                prediction = self.local_model.predict([text])[0]
                # Probability for score
                probs = self.local_model.predict_proba([text])[0]
                score = max(probs)
                return self._enrich_analysis(text, prediction.upper(), float(score))
            except Exception as e:
                print(f"❌ Local AI failed: {e}")

        # 3. Simple Fallback (Keyword heuristic)
        return self._heuristic_fallback(text)

    def _enrich_analysis(self, text: str, label: str, score: float) -> Dict[str, Any]:
        """Add emotions, credibility, and aspects to the base sentiment."""
        credibility_data = self._calculate_credibility(text)
        return {
            "label": label,
            "score": score,
            "emotions": self._extract_emotions_local(text, label), # Local heuristic for speed
            "credibility": credibility_data["score"],
            "credibility_reasons": credibility_data["reasons"],
            "aspects": self._extract_aspects(text, label)
        }

    def _heuristic_fallback(self, text: str) -> Dict[str, Any]:
        """If everything fails, use keywords."""
        text_lower = text.lower()
        pos_words = ["good", "great", "love", "best", "excellent", "fast"]
        neg_words = ["bad", "hate", "worst", "slow", "broken", "terrible"]
        
        pos_count = sum(1 for w in pos_words if w in text_lower)
        neg_count = sum(1 for w in neg_words if w in text_lower)
        
        if pos_count > neg_count:
            return self._enrich_analysis(text, "POSITIVE", 0.6 + (0.1 * pos_count))
        elif neg_count > pos_count:
            return self._enrich_analysis(text, "NEGATIVE", 0.6 + (0.1 * neg_count))
        return self._enrich_analysis(text, "NEUTRAL", 0.5)

    def _extract_emotions_local(self, text: str, label: str) -> List[Dict[str, Any]]:
        """Fast rule-based emotion tagging to avoid 2nd API call latency."""
        text_lower = text.lower()
        emotions = []
        if "anger" in text_lower or "stupid" in text_lower or "waste" in text_lower:
            emotions.append({"name": "Anger", "score": 0.9})
        if "love" in text_lower or "happy" in text_lower or "great" in text_lower:
            emotions.append({"name": "Joy", "score": 0.9})
        if "scam" in text_lower or "fake" in text_lower:
            emotions.append({"name": "Disgust", "score": 0.8})
        
        if not emotions:
            emotions.append({"name": "Neutral", "score": 0.5})
        return emotions

    async def _query_hf(self, client, url, payload, headers):
        response = await client.post(url, headers=headers, json=payload)
        if response.status_code != 200:
            # Propagate error details
            try:
                err_json = response.json()
                error_msg = err_json.get("error", f"HTTP {response.status_code}")
                # Handling model loading specifically
                if "estimated_time" in err_json:
                    error_msg = f"Model Loading ({err_json['estimated_time']}s)"
                print(f"HF Error {url}: {error_msg}")
                return {"error": error_msg}
            except:
                print(f"HF Error {url}: {response.text}")
                return {"error": f"HTTP {response.status_code}"}
        return response.json()

    def _calculate_credibility(self, text: str) -> Dict[str, Any]:
        """Forensic Credibility Analysis."""
        score = 100
        reasons = []
        text_lower = text.lower()
        
        # 1. Length Check
        if len(text) < 15:
            score -= 20
            reasons.append("Too short to be meaningful")
        
        # 2. Stylometric: All Caps
        if text.isupper() and len(text) > 10:
            score -= 30
            reasons.append("Excessive shouting (All Caps)")
            
        # 3. Marketing Speak / Bot Patterns
        bot_triggers = ["click here", "buy now", "100% free", "giveaway", "limited time"]
        if any(t in text_lower for t in bot_triggers):
            score -= 50
            reasons.append("Contains promotional/bot triggers")

        # 4. Repetition (Stammering Bot)
        words = text_lower.split()
        if len(words) > 10 and len(set(words)) < len(words) * 0.5:
            score -= 30
            reasons.append("High lexical repetition (Bot-like)")

        return {"score": max(0, score), "reasons": reasons}

    def _extract_aspects(self, text: str, sentiment: str) -> List[Dict[str, Any]]:
        """Extract product aspects (Camera, Battery, Price)."""
        aspects = []
        keywords = {
            "Quality": ["quality", "build", "solid", "cheap", "plastic"],
            "Price": ["price", "cost", "value", "expensive", "cheap", "worth"],
            "Service": ["service", "support", "refund", "shipping"],
            "Performance": ["fast", "slow", "lag", "smooth", "crash"]
        }
        
        text_lower = text.lower()
        for aspect, terms in keywords.items():
            if any(term in text_lower for term in terms):
                aspects.append({
                    "name": aspect,
                    "sentiment": sentiment.lower()
                })
        return aspects

    def extract_keywords(self, texts: List[str], top_n: int = 50) -> List[Dict[str, Any]]:
        """
        Extract frequent keywords/topics from a list of texts using Scikit-Learn.
        Removes stopwords and extracts top N meaningful terms (unigrams/bigrams).
        """
        if not texts:
            return []

        try:
            from sklearn.feature_extraction.text import CountVectorizer
            
            # Custom stop words + standar English list
            stop_words = 'english'
            
            # Use CountVectorizer to extract top words
            # ngram_range=(1, 2) lets us capture "battery life" or "screen"
            vectorizer = CountVectorizer(stop_words=stop_words, max_features=top_n, ngram_range=(1, 2))
            X = vectorizer.fit_transform(texts)
            
            # Sum word counts
            word_counts = X.toarray().sum(axis=0)
            words = vectorizer.get_feature_names_out()
            
            # Zip and sort
            freqs = sorted(zip(words, word_counts), key=lambda x: x[1], reverse=True)
            
            return [{"text": word, "value": int(count)} for word, count in freqs[:top_n]]
            
        except ImportError:
            # Fallback if scikit-learn is missing
            print("Warning: scikit-learn not found, using simple fallback.")
            from collections import Counter
            import re
            all_text = " ".join(texts).lower()
            words = re.findall(r'\w+', all_text)
            common = Counter(words).most_common(top_n)
            return [{"text": w, "value": c} for w, c in common]
        except Exception as e:
            print(f"Keyword Extraction Error: {e}")
            return []

    async def generate_topic_clusters(self, reviews: List[str], top_n: int = 10) -> List[Dict[str, Any]]:
        """
        Generate topic clusters from a list of reviews.
        - Extract most common nouns (using Spacy if available, else fallback to word frequency)
        - For each topic, compute average sentiment score from reviews that mention the topic
        - Persist a row to `topic_analysis` for each topic
        Returns a list of topic dicts: {topic_name, sentiment, size, keywords}
        """
        if not reviews:
            return []

        from collections import Counter
        import re
        try:
            from database import supabase
        except Exception:
            supabase = None

        # 1) Extract candidate topic tokens
        candidate_tokens = []
        if nlp:
            for r in reviews:
                try:
                    doc = nlp(r)
                    for token in doc:
                        if token.pos_ in ("NOUN", "PROPN") and len(token.text) > 2 and not token.is_stop:
                            candidate_tokens.append(token.lemma_.lower())
                except Exception:
                    continue
        else:
            # Fallback: use extract_keywords which already removes stopwords
            kw = self.extract_keywords(reviews, top_n=200)
            candidate_tokens = [k["text"] for k in kw]

        if not candidate_tokens:
            return []

        counts = Counter(candidate_tokens)
        top_topics = [t for t, _ in counts.most_common(top_n)]

        topics_output = []

        # Normalize reviews for matching
        normalized_reviews = [r.lower() for r in reviews]

        # We'll reuse analyze_sentiment to compute a numeric score (0-1)
        for topic in top_topics:
            # Find reviews mentioning the topic token (simple substring match)
            related_indices = [i for i, r in enumerate(normalized_reviews) if re.search(r"\b" + re.escape(topic) + r"\b", r)]
            if not related_indices:
                continue

            # Compute sentiment scores for related reviews
            sentiment_scores = []
            for idx in related_indices:
                try:
                    sentiment = await self.analyze_sentiment(reviews[idx])
                    score = float(sentiment.get("score") or 0.0)
                    sentiment_scores.append(score)
                except Exception:
                    continue

            avg_sentiment = sum(sentiment_scores) / len(sentiment_scores) if sentiment_scores else 0.0

            # Extract keywords from related reviews (top 5)
            related_texts = [reviews[i] for i in related_indices]
            keywords_objs = self.extract_keywords(related_texts, top_n=10)
            keywords = [k["text"] for k in keywords_objs[:5]]

            topic_entry = {
                "topic_name": topic,
                "sentiment": avg_sentiment,
                "size": len(related_indices),
                "keywords": keywords,
            }

            # Persist to DB if supabase available
            if supabase:
                try:
                    supabase.table("topic_analysis").insert({
                        "topic_name": topic,
                        "sentiment": avg_sentiment,
                        "size": len(related_indices),
                        "keywords": keywords,
                    }).execute()
                except Exception as e:
                    print(f"Failed saving topic_analysis for {topic}: {e}")

            topics_output.append(topic_entry)

        return topics_output

    async def check_for_alerts(self, review: Dict[str, Any]):
        """
        Create an alert in the `alerts` table if sentiment score below threshold.
        Expects review dict that may contain 'score' or 'sentiment_score'.
        """
        try:
            from database import supabase
        except Exception:
            supabase = None

        # Extract score
        score = None
        if isinstance(review, dict):
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
