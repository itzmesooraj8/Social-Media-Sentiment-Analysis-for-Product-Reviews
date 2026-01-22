"""
AIService

Provides a cached `analyze_text(text)` function that returns a dict:
  { label: "POSITIVE", score: 0.98, emotion: "joy", credibility: 0.12 }

Uses 'distilbert-base-uncased-finetuned-sst-2-english' for sentiment
and 'j-hartmann/emotion-english-distilroberta-base' for emotion detection.
"""

from functools import lru_cache
from typing import Dict, List
import os
import asyncio

try:
    from transformers import pipeline
    _TRANSFORMERS_AVAILABLE = True
except ImportError:
    _TRANSFORMERS_AVAILABLE = False
    print("⚠️ Transformers not found. AI features will be limited.")

from database import supabase


class AIService:
    def __init__(self):
        self.sentiment_model = "distilbert-base-uncased-finetuned-sst-2-english"
        self.emotion_model = "j-hartmann/emotion-english-distilroberta-base"
        self._sentiment_pipe = None
        self._emotion_pipe = None

        if _TRANSFORMERS_AVAILABLE:
            try:
                print("[Loading] Sentiment Model...")
                self._sentiment_pipe = pipeline("sentiment-analysis", model=self.sentiment_model)
                print("[Loading] Emotion Model...")
                self._emotion_pipe = pipeline("text-classification", model=self.emotion_model, top_k=1)
                print("[OK] AI Models Loaded.")
            except Exception as e:
                print(f"[ERROR] AI Init Error: {e}")

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
        """Simple credibility heuristic."""
        try:
            length = len(text.strip())
            if length < 10:
                base = 0.15
            elif length < 50:
                base = 0.45
            else:
                base = 0.75

            # Duplicate check (simple cache check could go here, but DB check is expensive in loop)
            # For high-performance, we skip the DB check in this synchronous part or use a local bloom filter.
            # We will stick to length-based for now to ensure speed.
            return float(min(1.0, max(0.0, base)))
        except Exception:
            return 0.5

    @lru_cache(maxsize=2048)
    def analyze_text(self, text: str) -> Dict[str, any]:
        """Synchronous analyze. Cached to avoid repeated work."""
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
            except Exception as e:
                print(f"Emotion error: {e}")
        else:
            # Fallback heuristic if model failed to load
            text_l = text.lower()
            if label == "POSITIVE":
                emotion = "joy"
            elif label == "NEGATIVE":
                emotion = "anger"

        credibility = self._compute_credibility(text)
        
        return {
            "label": label,
            "score": round(score, 4),
            "emotion": emotion,
            "credibility": round(credibility, 3)
        }
    
    async def analyze_sentiment(self, text: str):
        """Async wrapper for the sync lru_cache method"""
        return await asyncio.to_thread(self.analyze_text, text)


ai_service = AIService()

