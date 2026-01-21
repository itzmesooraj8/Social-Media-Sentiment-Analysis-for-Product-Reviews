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

