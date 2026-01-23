import re
from collections import Counter
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

    def extract_topics(self, texts: List[str], top_k: int = 5) -> List[Dict[str, any]]:
        """
        Extract top topics using Frequency-Based Bigram Analysis (Lightweight TextRank approximation).
        Returns top 5 Bigrams with their sentiment polarity.
        """
        if not texts:
            return []

        # 1. Normalize and clean
        # Common stop words to remove
        stopwords = {
            "the", "is", "and", "to", "a", "of", "in", "it", "for", "on", "that", "this", "with", "i", "you",
            "but", "was", "my", "have", "as", "are", "not", "be", "so", "at", "if", "or", "just", "very", "can",
            "product", "item", "one", "get", "me", "all", "about", "out", "has", "more", "like", "when", "up",
            "what", "time", "would", "they", "from", "do", "will", "really", "good", "great", "review", "video",
            "video", "use", "had", "than", "been", "only", "also", "after", "which", "by", "there", "review",
            "bought", "buy", "price", "amazon"  # Added some more contextual stop words
        }
        
        normalized_texts = []
        for t in texts:
            if not t: continue
            # Lowercase and remove punctuation
            clean = re.sub(r'[^\w\s]', '', t.lower())
            normalized_texts.append(clean)

        # 2. Extract Bigrams & Track Sentiment context
        bigram_counts = Counter()
        bigram_sentiments = {} # Map bigram -> list of sentiments (from context)

        for text in normalized_texts:
            words = text.split()
            filtered = [w for w in words if w not in stopwords and len(w) > 2]
            
            if len(filtered) >= 2:
                # Calculate simple sentiment for this text snippet once
                # We use a very naive polarity check here for speed if model not used, 
                # or we could use self.analyze_text but that might be slow in loop.
                # Let's rely on self.analyze_text's cache if possible, or just use a simple lexicon here 
                # to keep "extract_topics" lightweight as requested.
                
                # However, the instruction says "with their sentiment polarity". 
                # Let's use a simplified lexicon approach for speed within this loop.
                pos_words = {"love", "amazing", "excellent", "best", "awesome", "perfect", "happy", "glad"}
                neg_words = {"hate", "worst", "terrible", "bad", "awful", "horrible", "refund", "waste", "slow"}
                
                score = 0
                for w in filtered:
                    if w in pos_words: score += 1
                    elif w in neg_words: score -= 1
                
                label = "neutral"
                if score > 0: label = "positive"
                elif score < 0: label = "negative"

                for i in range(len(filtered) - 1):
                    bigram = f"{filtered[i]} {filtered[i+1]}"
                    bigram_counts[bigram] += 1
                    
                    if bigram not in bigram_sentiments:
                        bigram_sentiments[bigram] = {"pos": 0, "neg": 0, "neu": 0}
                    
                    if label == "positive": bigram_sentiments[bigram]["pos"] += 1
                    elif label == "negative": bigram_sentiments[bigram]["neg"] += 1
                    else: bigram_sentiments[bigram]["neu"] += 1

        # 3. Get Top K
        most_common = bigram_counts.most_common(top_k)
        
        results = []
        for topic, count in most_common:
            # Determine dominant sentiment for this topic
            s_counts = bigram_sentiments[topic]
            dom_sentiment = "neutral"
            if s_counts["pos"] > s_counts["neg"] and s_counts["pos"] > s_counts["neu"]:
                dom_sentiment = "positive"
            elif s_counts["neg"] > s_counts["pos"] and s_counts["neg"] > s_counts["neu"]:
                dom_sentiment = "negative"
            
            results.append({
                "topic": topic,
                "sentiment": dom_sentiment,
                "count": count
            })
            
        return results


ai_service = AIService()

