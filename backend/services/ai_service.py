import re
import asyncio
from functools import lru_cache
from typing import Dict, List, Any
import logging

try:
    from transformers import pipeline
    _TRANSFORMERS_AVAILABLE = True
except ImportError:
    _TRANSFORMERS_AVAILABLE = False
    print("⚠️ Transformers not found. AI features will be limited.")

try:
    import textstat
    _TEXTSTAT_AVAILABLE = True
except ImportError:
    _TEXTSTAT_AVAILABLE = False
    print("⚠️ textstat not found. Credibility scoring will be limited.")

try:
    from keybert import KeyBERT
    _KEYBERT_AVAILABLE = True
except ImportError:
    _KEYBERT_AVAILABLE = False
    print("⚠️ KeyBERT not found. Topic extraction will be limited.")

from database import supabase

logger = logging.getLogger(__name__)

class AIService:
    def __init__(self):
        self.sentiment_model = "distilbert-base-uncased-finetuned-sst-2-english"
        self.emotion_model = "j-hartmann/emotion-english-distilroberta-base"
        self._sentiment_pipe = None
        self._emotion_pipe = None
        self._keybert_model = None
        self._models_loaded = False

    def _ensure_models_loaded(self):
        if self._models_loaded or not _TRANSFORMERS_AVAILABLE:
            return

        try:
            print("[Loading] Sentiment Model (Lazy Load)...")
            self._sentiment_pipe = pipeline("sentiment-analysis", model=self.sentiment_model)
            print("[Loading] Emotion Model (Lazy Load)...")
            self._emotion_pipe = pipeline("text-classification", model=self.emotion_model, top_k=1)
            
            if _KEYBERT_AVAILABLE:
                 print("[Loading] KeyBERT Model (Lazy Load)...")
                 self._keybert_model = KeyBERT()

            print("[OK] AI Models Loaded.")
            self._models_loaded = True
        except Exception as e:
            print(f"[ERROR] AI Init Error: {e}")
            self._models_loaded = True # Prevent retry loop on failure

    def _normalize_label(self, raw_label: str) -> str:
        lbl = (raw_label or "").upper()
        if lbl in ("POSITIVE", "NEGATIVE"):
            return lbl
        if lbl.endswith("_0"):
            return "NEGATIVE"
        if lbl.endswith("_1"):
            return "POSITIVE"
        return "NEUTRAL"

    def _compute_credibility(self, text: str, confidence: float, metadata: Dict[str, Any] = None) -> float:
        """
        Multi-Factor Credibility Score:
        Formula = (0.4 * Sentiment_Confidence) + (0.3 * Readability_Score) + (0.3 * Metadata_Impact)
        """
        if not text or not text.strip():
            return 0.1

        # 1. Sentiment Confidence (0.4 weight) - passed in from model
        conf_score = confidence if confidence else 0.5
        
        # 2. Readability Score (0.3 weight)
        readability_val = 0.5
        if _TEXTSTAT_AVAILABLE:
            try:
                # Flesch Reading Ease: 0-100 (higher is easier). We normalize to 0-1.
                # A good review is usually readable but not too simple.
                # Let's say 30-70 is "credible" (complex but readable). 
                # Actually, standard interpretation: 60-70 is standard. 
                # Let's just normalize 0-100 to 0-1.
                ease = textstat.flesch_reading_ease(text)
                readability_val = max(0.0, min(1.0, ease / 100.0))
            except Exception:
                readability_val = 0.5
        
        # 3. Metadata Impact (0.3 weight)
        meta_val = 0.0
        if metadata:
            # Normalize likes/replies/retweets. 
            # Simple heuristic: presence of engagement increases credibility (social proof).
            likes = metadata.get("like_count", 0)
            replies = metadata.get("reply_count", 0)
            retweets = metadata.get("retweet_count", 0)
            total_engagement = likes + replies + retweets
            
            # Logarithmic scale or simple threshold
            if total_engagement > 100: meta_val = 1.0
            elif total_engagement > 10: meta_val = 0.7
            elif total_engagement > 0: meta_val = 0.4
            else: meta_val = 0.1 # No engagement
        else:
             meta_val = 0.3 # default if no metadata available (e.g. direct text analysis)

        final_score = (0.4 * conf_score) + (0.3 * readability_val) + (0.3 * meta_val)
        return round(final_score, 3)

    # Note: lru_cache removed for analyze_text because metadata changes per call, making caching less effective/correct
    # or we need to exclude metadata from cache key. For now, we prioritize correctness.
    def analyze_text(self, text: str, metadata: Dict[str, Any] = None) -> Dict[str, any]:
        """Synchronous analyze."""
        self._ensure_models_loaded()

        if not text or not text.strip():
            return {"label": "NEUTRAL", "score": 0.5, "emotion": "neutral", "credibility": 0.1}

        label = "NEUTRAL"
        score = 0.5
        emotion = "neutral"

        # 1. Sentiment Analysis
        if self._sentiment_pipe:
            try:
                out = self._sentiment_pipe(text[:512])
                if out and isinstance(out, list):
                    top = out[0]
                    label = self._normalize_label(top.get("label"))
                    score = float(top.get("score", 0.5))
            except Exception as e:
                print(f"Sentiment error: {e}")

        # 2. Emotion Analysis (Real Model)
        emotion_score = 0.0
        if self._emotion_pipe:
            try:
                e_out = self._emotion_pipe(text[:512])
                # e_out structure with top_k=1: [{'label': 'joy', 'score': 0.9}]
                if e_out and isinstance(e_out, list):
                    if isinstance(e_out[0], list): # Handle batch output edge case
                        top_e = e_out[0][0]
                    else:
                        top_e = e_out[0]
                    
                    emotion = top_e.get("label", "neutral")
                    emotion_score = float(top_e.get("score", 0.0))
            except Exception as e:
                print(f"Emotion error: {e}")
        else:
            # Fallback heuristic if model failed to load
            text_l = text.lower()
            if label == "POSITIVE":
                emotion = "joy"
                emotion_score = 0.8
            elif label == "NEGATIVE":
                emotion = "anger"
                emotion_score = 0.8

        credibility = self._compute_credibility(text, score, metadata)
        
        return {
            "label": label,
            "score": round(score, 4),
            "emotions": [{"name": emotion, "score": int(emotion_score * 100)}] if emotion != "neutral" else [],
            "credibility": credibility
        }
    
    async def analyze_sentiment(self, text: str, metadata: Dict[str, Any] = None):
        """Async wrapper."""
        return await asyncio.to_thread(self.analyze_text, text, metadata)

    def extract_topics(self, texts: List[str], top_k: int = 5) -> List[Dict[str, any]]:
        """
        Extract topics using Bigram Frequency (Client PDF Requirement).
        """
        if not texts:
            return []

        # 1. Normalize
        stop_words = {"the", "a", "an", "and", "or", "but", "in", "on", "at", "to", "for", "of", "with", "is", "was", "are", "were", "it", "this", "that", "i", "my", "we", "our", "you", "your", "good", "bad", "great", "product", "review", "phone", "app", "very", "so", "really", "video", "just", "like", "have", "has", "had", "not", "dont", "cant", "wont"}
        
        normalized_texts = []
        for t in texts:
            # Lowercase, remove punctuation (basic), split
            cleaned = re.sub(r'[^\w\s]', '', t.lower())
            words = [w for w in cleaned.split() if w not in stop_words and len(w) > 2]
            normalized_texts.append(words)

        # 2. Create Bigrams & Count
        bigram_counts = {}
        
        for words in normalized_texts:
            if len(words) < 2:
                continue
            for i in range(len(words) - 1):
                bigram = f"{words[i]} {words[i+1]}"
                bigram_counts[bigram] = bigram_counts.get(bigram, 0) + 1

        # 3. Sort and Return Top K
        sorted_bigrams = sorted(bigram_counts.items(), key=lambda x: x[1], reverse=True)
        top_bigrams = sorted_bigrams[:top_k]
        
        results = []
        for bg, count in top_bigrams:
            results.append({
                "topic": bg,
                "sentiment": "neutral", 
                "count": count
            })
            
        return results


ai_service = AIService()

