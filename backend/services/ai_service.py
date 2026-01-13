import os
import httpx
import asyncio
from typing import Dict, Any, List

# Using a robust sentiment model
HF_API_URL = "https://api-inference.huggingface.co/models/cardiffnlp/twitter-xlm-roberta-base-sentiment"

class AIService:
    def __init__(self):
        self.api_url = HF_API_URL

    async def _get_api_key(self) -> str:
        try:
            from database import supabase
            response = supabase.table("integrations").select("api_key").eq("platform", "huggingface").eq("active", True).limit(1).execute()
            if response.data:
                return response.data[0]["api_key"]
            return os.environ.get("HF_TOKEN", "")
        except:
            return os.environ.get("HF_TOKEN", "")


    async def analyze_sentiment(self, text: str) -> Dict[str, Any]:
        """
        Analyze sentiment, emotions, and credibility of a text string.
        """
        if not text or not text.strip():
            return {"label": "NEUTRAL", "score": 0.5, "emotions": [], "credibility": 0}

        token = await self._get_api_key()
        headers = {"Authorization": f"Bearer {token}"} if token else {}

        if not token:
             # Fallback to simple logic if no key provided
             print("Warning: No HF Token found. Using mock fallback.")
             # Simple heuristic for fallback
             sentiment = "POSITIVE" if "good" in text.lower() or "love" in text.lower() else "NEGATIVE" if "bad" in text.lower() else "NEUTRAL"
             return {
                "label": sentiment, 
                "score": 0.6, 
                "emotions": [{"name": "Neutral", "score": 70}], 
                "credibility": 50,
                "aspects": self._extract_aspects(text, sentiment)
             }


        async with httpx.AsyncClient() as client:
            try:
                # 1. Sentiment Analysis (Positive/Neutral/Negative)
                sentiment_task = self._query_hf(client, self.api_url, {"inputs": text[:512]}, headers)
                
                # 2. Emotion Analysis (Joy, Anger, etc.)
                EMOTION_API_URL = "https://api-inference.huggingface.co/models/j-hartmann/emotion-english-distilroberta-base"
                emotion_task = self._query_hf(client, EMOTION_API_URL, {"inputs": text[:512]}, headers)
                
                results = await asyncio.gather(sentiment_task, emotion_task, return_exceptions=True)
                
                sentiment_data = results[0] if not isinstance(results[0], Exception) else []
                emotion_data = results[1] if not isinstance(results[1], Exception) else []
                
                # Process Sentiment
                sentiment_res = self._process_sentiment(sentiment_data)
                
                # Process Emotions
                emotions = self._process_emotions(emotion_data)
                
                # Calculate Credibility (Heuristic)
                credibility = self._calculate_credibility(text)

                return {
                    "label": sentiment_res["label"],
                    "score": sentiment_res["score"],
                    "breakdown": sentiment_res["breakdown"],
                    "emotions": emotions,
                    "credibility": credibility,
                    "aspects": self._extract_aspects(text, sentiment_res["label"])
                }

            except Exception as e:
                print(f"AI Service Exception: {e}")
                return {"label": "NEUTRAL", "score": 0.5, "error": str(e)}

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

    def _process_sentiment(self, data) -> Dict[str, Any]:
        try:
            # Check for API Error first
            if isinstance(data, dict) and "error" in data:
                return {"label": "ERROR", "score": 0.0, "breakdown": [], "error": data["error"]}

            if isinstance(data, list) and len(data) > 0 and isinstance(data[0], list):
                scores = data[0]
                top_result = max(scores, key=lambda x: x['score'])
                return {
                    "label": top_result['label'].upper(),
                    "score": top_result['score'],
                    "breakdown": scores
                }
            return {"label": "NEUTRAL", "score": 0.5, "breakdown": []}
        except Exception as e:
            print(f"Sentiment Process Error: {e}")
            return {"label": "NEUTRAL", "score": 0.5, "breakdown": []}

    def _process_emotions(self, data) -> List[Dict[str, Any]]:
        # Expected format: [[{'label': 'joy', 'score': 0.9}, ...]]
        try:
            if isinstance(data, list) and len(data) > 0 and isinstance(data[0], list):
                # Sort by score desc
                sorted_emotions = sorted(data[0], key=lambda x: x['score'], reverse=True)
                return [{"name": e['label'].title(), "score": e['score'] * 100} for e in sorted_emotions]
            return []
        except:
            return []

    def _calculate_credibility(self, text: str) -> float:
        """
        Heuristic credibility score (0-100).
        """
        score = 80 # Start high
        
        # 1. Content Length
        if len(text) < 20: score -= 20
        if len(text) > 100: score += 10
        
        # 2. Capitalization Shouting
        caps_ratio = sum(1 for c in text if c.isupper()) / len(text) if text else 0
        if caps_ratio > 0.5: score -= 30
        
        # 3. Spam keywords
        spam_words = ["buy now", "click here", "subscribe", "winner", "crypto"]
        if any(w in text.lower() for w in spam_words): score -= 40
        
        return max(min(score, 100), 0)

    def _extract_aspects(self, text: str, global_sentiment: str) -> List[Dict[str, Any]]:
        """
        Heuristic aspect extraction since full ABSA models are heavy.
        """
        text_lower = text.lower()
        aspects = []
        
        keywords = {
            "Quality": ["quality", "build", "material", "durable", "broke", "solid"],
            "Price": ["price", "cost", "value", "expensive", "cheap", "worth"],
            "Shipping": ["shipping", "delivery", "arrived", "package", "packaging"],
            "Service": ["service", "support", "refund", "response", "staff"]
        }
        
        for category, terms in keywords.items():
            if any(term in text_lower for term in terms):
                aspects.append({
                    "name": category,
                    "sentiment": global_sentiment.lower() if global_sentiment else "neutral"
                })
                
        return aspects

    def extract_keywords(self, texts: List[str], top_n: int = 50) -> List[Dict[str, Any]]:
        """
        Extract frequent keywords/topics from a list of texts.
        Basic implementation: Tokenization + Stopword Removal + Frequency.
        """
        from collections import Counter
        import re

        stopwords = {
            "the", "a", "an", "and", "or", "but", "in", "on", "at", "to", "for", "of", "with",
            "is", "was", "are", "were", "be", "been", "this", "that", "these", "those",
            "it", "i", "you", "he", "she", "we", "they", "my", "your", "his", "her", "their",
            "what", "which", "who", "whom", "whose", "why", "how", "where", "when",
            "from", "as", "by", "about", "into", "through", "during", "before", "after",
            "above", "below", "up", "down", "out", "off", "over", "under", "again", "further",
            "then", "once", "here", "there", "all", "any", "both", "each", "few", "more",
            "most", "other", "some", "such", "no", "nor", "not", "only", "own", "same",
            "so", "than", "too", "very", "can", "will", "just", "don", "should", "now"
        }

        all_words = []
        for text in texts:
            # Simple normalization
            clean_text = re.sub(r'[^\w\s]', '', text.lower())
            words = clean_text.split()
            filtered = [w for w in words if w not in stopwords and len(w) > 2]
            all_words.extend(filtered)

        counter = Counter(all_words)
        most_common = counter.most_common(top_n)

        # Format for Word Cloud (text, value)
        return [{"text": word, "value": count} for word, count in most_common]

ai_service = AIService()
